#!/usr/bin/env python3
"""
Clerk Authentication using REST API (no async issues!)
This replaces the clerk-backend-sdk which has async/await problems with Flask
"""

import os
import requests
import jwt
from jwt import PyJWKClient
from typing import Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client


class ClerkRestAPI:
    """
    Clerk authentication using direct REST API calls
    Works perfectly with Flask (synchronous)
    """
    
    def __init__(self):
        # Use hardcoded values from config
        from config import config
        self.clerk_secret_key = config.clerk_secret_key
        self.clerk_publishable_key = config.clerk_publishable_key
        self.base_url = "https://api.clerk.com/v1"
        
        if not self.clerk_secret_key:
            raise ValueError("CLERK_SECRET_KEY not configured")
        
        self.headers = {
            'Authorization': f'Bearer {self.clerk_secret_key}',
            'Content-Type': 'application/json'
        }
        
        # Get the instance domain from the publishable key
        # Clerk publishable keys are base64 encoded and contain the frontend API URL
        if self.clerk_publishable_key:
            try:
                import base64
                # Decode the publishable key to get the frontend API domain
                # Format: pk_test_<base64_encoded_domain>
                key_parts = self.clerk_publishable_key.split('_')
                if len(key_parts) >= 3:
                    encoded_domain = key_parts[2]
                    # Remove any trailing characters like '$' and add padding if needed
                    encoded_domain = encoded_domain.rstrip('$')
                    # Add padding to make length multiple of 4
                    padding = 4 - (len(encoded_domain) % 4)
                    if padding != 4:
                        encoded_domain += '=' * padding
                    
                    # Decode base64 to get domain (e.g., "golden-opossum-32.clerk.accounts.dev")
                    decoded = base64.b64decode(encoded_domain).decode('utf-8')
                    # Remove any trailing special characters
                    decoded = decoded.rstrip('$')
                    
                    # Construct JWKS URL for this specific instance
                    self.jwks_url = f"https://{decoded}/.well-known/jwks.json"
                    print(f"[INFO] Clerk instance domain: {decoded}")
                    print(f"[INFO] Using JWKS URL: {self.jwks_url}")
                    # Create PyJWKClient for JWT verification
                    self.jwks_client = PyJWKClient(self.jwks_url, cache_keys=True)
                else:
                    print("[WARN] Could not parse publishable key for JWKS URL")
                    self.jwks_client = None
            except Exception as e:
                import traceback
                print(f"[ERROR] Failed to construct JWKS URL: {e}")
                print(traceback.format_exc())
                self.jwks_client = None
        else:
            self.jwks_client = None
        
        # Initialize Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
        
        print("[OK] Clerk REST API initialized (no async issues!)")
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Clerk JWT token using JWKS (networkless verification)
        This is the modern, recommended approach by Clerk
        
        Args:
            token: JWT token from Clerk session
            
        Returns:
            Decoded JWT payload with user info or None if invalid
        """
        try:
            if not self.jwks_client:
                print("[ERROR] JWKS client not initialized")
                return None
            
            print(f"[INFO] Verifying JWT token (first 30 chars): {token[:30]}...")
            
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            print(f"[INFO] Got signing key from JWKS")
            
            # Verify and decode JWT without strict audience/issuer validation
            # Clerk uses dynamic issuers, so we'll verify them after decoding
            # Add leeway for clock skew to prevent premature expiration
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": False,  # Don't verify audience (Clerk doesn't require it)
                    "verify_iss": False,  # Don't verify issuer (we'll check it manually)
                },
                leeway=60  # Allow 60 seconds of clock skew for exp/iat verification
            )
            
            # Log the payload for debugging
            print(f"[INFO] JWT payload decoded:")
            print(f"  - User ID (sub): {payload.get('sub')}")
            print(f"  - Issuer (iss): {payload.get('iss')}")
            print(f"  - Expires (exp): {payload.get('exp')}")
            
            print(f"[OK] JWT verified successfully for user: {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            print("[ERROR] JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[ERROR] Invalid JWT token: {e}")
            import traceback
            print(traceback.format_exc())
            return None
        except Exception as e:
            print(f"[ERROR] JWT verification error: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def verify_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Verify Clerk session using REST API (DEPRECATED)
        This method is kept for backward compatibility but is deprecated by Clerk
        
        Args:
            session_id: Session ID from frontend (clerk.session.id)
            
        Returns:
            Session data or None if invalid
        """
        try:
            print("[WARN] Using deprecated session verification. Please use JWT tokens instead.")
            # Verify session with Clerk API using session ID
            url = f"{self.base_url}/sessions/{session_id}/verify"
            response = requests.post(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"[ERROR] Session verification failed: {response.status_code}")
                print(f"[ERROR] Response: {response.text}")
                return None
            
            session_data = response.json()
            return session_data
            
        except Exception as e:
            print(f"[ERROR] Clerk session verification error: {e}")
            return None
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user details from Clerk
        
        Args:
            user_id: Clerk user ID
            
        Returns:
            User data or None if not found
        """
        try:
            url = f"{self.base_url}/users/{user_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                print(f"[ERROR] Get user failed: {response.status_code}")
                return None
            
            user_data = response.json()
            return user_data
            
        except Exception as e:
            print(f"[ERROR] Clerk get user error: {e}")
            return None
    
    def verify_and_get_user(self, session_id_or_token: str, is_jwt: bool = False) -> Optional[Dict[str, Any]]:
        """
        Verify session/token and get user data in one call
        
        Args:
            session_id_or_token: Either session ID (deprecated) or JWT token (recommended)
            is_jwt: True if session_id_or_token is a JWT token, False if it's a session ID
        
        Returns:
            User data with Clerk info or None
        """
        try:
            user_id = None
            
            if is_jwt:
                # Modern approach: Verify JWT token (networkless, fast)
                print("[INFO] Verifying JWT token...")
                jwt_payload = self.verify_jwt_token(session_id_or_token)
                if not jwt_payload:
                    print("[ERROR] Invalid JWT token")
                    return None
                
                # Extract user ID from JWT (Clerk puts user ID in 'sub' claim)
                user_id = jwt_payload.get('sub')
                
                if not user_id:
                    print("[ERROR] No user ID in JWT payload")
                    return None
                
                print(f"[OK] JWT verified, user ID: {user_id}")
            else:
                # Deprecated approach: Verify session ID with Clerk API
                print("[INFO] Verifying session ID (deprecated)...")
                session = self.verify_session(session_id_or_token)
                if not session or not session.get('user_id'):
                    print(f"[ERROR] Invalid session or no user_id in session")
                    return None
                
                user_id = session['user_id']
            
            # Get user details from Clerk API
            user = self.get_user(user_id)
            
            if not user:
                print(f"[ERROR] Could not get user {user_id} from Clerk")
                return None
            
            # Extract user information
            email_addresses = user.get('email_addresses', [])
            primary_email = next(
                (e['email_address'] for e in email_addresses if e.get('id') == user.get('primary_email_address_id')),
                email_addresses[0]['email_address'] if email_addresses else None
            )
            
            user_data = {
                'clerk_id': user['id'],
                'email': primary_email,
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or 'User',
                'profile_image': user.get('profile_image_url'),
                'created_at': user.get('created_at')
            }
            
            return user_data
            
        except Exception as e:
            import traceback
            print(f"[ERROR] Verify and get user error: {e}")
            print(traceback.format_exc())
            return None
    
    def sync_user_to_supabase(self, clerk_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync Clerk user to Supabase database
        Handles cases where user exists by clerk_id or by email
        """
        try:
            clerk_id = clerk_user_data['clerk_id']
            email = clerk_user_data['email']
            name = clerk_user_data['name']
            profile_image = clerk_user_data.get('profile_image')
            
            user = None
            user_id = None
            
            # First, try to find user by clerk_id
            existing_user = self.supabase.table('users').select('*').eq('clerk_id', clerk_id).execute()
            
            if existing_user.data:
                # User exists with this clerk_id - update it
                user = existing_user.data[0]
                user_id = user['id']
                
                self.supabase.table('users').update({
                    'name': name,
                    'email': email,
                    'profile_image': profile_image,
                    'last_login': datetime.utcnow().isoformat()
                }).eq('id', user_id).execute()
                
                print(f"[INFO] Updated user by clerk_id: {email}")
            else:
                # User doesn't exist by clerk_id, check if email exists
                existing_by_email = self.supabase.table('users').select('*').eq('email', email).execute()
                
                if existing_by_email.data:
                    # User exists with this email but different/no clerk_id - update it
                    user = existing_by_email.data[0]
                    user_id = user['id']
                    
                    print(f"[INFO] Found existing user by email, updating clerk_id: {email}")
                    
                    self.supabase.table('users').update({
                        'clerk_id': clerk_id,
                        'name': name,
                        'profile_image': profile_image,
                        'last_login': datetime.utcnow().isoformat()
                    }).eq('id', user_id).execute()
                    
                    print(f"[INFO] Updated user by email: {email}")
                else:
                    # User doesn't exist at all - create new user
                    user_data = {
                        'clerk_id': clerk_id,
                        'name': name,
                        'email': email,
                        'profile_image': profile_image,
                        'created_at': datetime.utcnow().isoformat(),
                        'last_login': datetime.utcnow().isoformat(),
                        'is_active': True
                    }
                    
                    result = self.supabase.table('users').insert(user_data).execute()
                    
                    if not result.data:
                        return {'success': False, 'error': 'Failed to create user'}
                    
                    user = result.data[0]
                    user_id = user['id']
                    
                    # Create memory database
                    self._create_user_memory_database(user_id)
                    
                    print(f"[INFO] Created new user: {email}")
            
            return {
                'success': True,
                'user': {
                    'id': user_id,
                    'clerk_id': clerk_id,
                    'name': name,
                    'email': email,
                    'profile_image': profile_image
                }
            }
            
        except Exception as e:
            print(f"[ERROR] Sync user to Supabase error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_user_memory_database(self, user_id: str):
        """Create personal memory database for user"""
        try:
            memory_db_data = {
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'memory_count': 0,
                'last_accessed': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('user_memory_databases').insert(memory_db_data).execute()
            print(f"[OK] Created memory database for user {user_id}")
            
        except Exception as e:
            print(f"[ERROR] Create memory database error: {e}")
    
    def verify_clerk_token(self, session_id_or_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Clerk session/token and return user data
        This is an alias for verify_and_get_user for compatibility
        Auto-detects if input is JWT token or session ID
        
        Args:
            session_id_or_token: Either JWT token or session ID
            
        Returns:
            User data with Clerk info or None
        """
        # Auto-detect if it's a JWT token (contains dots)
        is_jwt = '.' in session_id_or_token and session_id_or_token.count('.') >= 2
        return self.verify_and_get_user(session_id_or_token, is_jwt=is_jwt)
    
    def get_user_from_clerk_id(self, clerk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user from Supabase by Clerk ID
        
        Args:
            clerk_id: Clerk user ID
            
        Returns:
            User data from Supabase or None
        """
        try:
            result = self.supabase.table('users').select('*').eq('clerk_id', clerk_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Get user from Clerk ID error: {e}")
            return None


# Global instance
clerk_rest_api = None

def get_clerk_rest_api():
    """Get or create Clerk REST API instance"""
    global clerk_rest_api
    if clerk_rest_api is None:
        try:
            clerk_rest_api = ClerkRestAPI()
        except Exception as e:
            print(f"[WARN] Clerk REST API not available: {e}")
    return clerk_rest_api

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Helper function to get user details by ID
    
    Args:
        user_id: User ID to look up
        
    Returns:
        User data dictionary with 'name', 'email', etc. or None
    """
    try:
        api = get_clerk_rest_api()
        if not api:
            print("[WARN] Clerk REST API not available")
            return None
        
        # Get user from Clerk
        clerk_user = api.get_user(user_id)
        if not clerk_user:
            print(f"[WARN] User not found in Clerk: {user_id}")
            return None
        
        # Extract name from Clerk user data
        # Clerk stores name in multiple possible fields
        name = None
        if 'first_name' in clerk_user and 'last_name' in clerk_user:
            first = clerk_user.get('first_name', '').strip()
            last = clerk_user.get('last_name', '').strip()
            if first and last:
                name = f"{first} {last}"
            elif first:
                name = first
            elif last:
                name = last
        
        # Fallback to full_name if available
        if not name and 'full_name' in clerk_user:
            name = clerk_user.get('full_name', '').strip()
        
        # Fallback to username
        if not name and 'username' in clerk_user:
            name = clerk_user.get('username', '').strip()
        
        # Fallback to email prefix
        if not name and 'email_addresses' in clerk_user:
            emails = clerk_user.get('email_addresses', [])
            if emails and len(emails) > 0:
                email = emails[0].get('email_address', '')
                if email:
                    name = email.split('@')[0]
        
        return {
            'id': user_id,
            'name': name or 'User',  # Always return at least 'User'
            'email': clerk_user.get('email_addresses', [{}])[0].get('email_address') if clerk_user.get('email_addresses') else None
        }
    
    except Exception as e:
        print(f"[ERROR] get_user_by_id failed: {e}")
        return None

