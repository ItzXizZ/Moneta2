#!/usr/bin/env python3
"""
Clerk Authentication System for Moneta
Integrates Clerk OAuth (Google sign-in) with Supabase database
"""

import os
import json
from datetime import datetime
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Any
from supabase import create_client, Client

try:
    from clerk_backend_sdk import Configuration, ApiClient
    from clerk_backend_sdk import UsersApi, SessionsApi
    CLERK_AVAILABLE = True
except ImportError:
    CLERK_AVAILABLE = False
    print("[WARN] Clerk SDK not installed. Run: pip install clerk-backend-sdk")


class ClerkAuthSystem:
    """
    Authentication system using Clerk for OAuth (Google sign-in)
    and Supabase for user data storage
    """
    
    def __init__(self):
        # Initialize Clerk
        from config import config as app_config
        self.clerk_secret_key = app_config.clerk_secret_key
        self.clerk_publishable_key = app_config.clerk_publishable_key
        
        if not CLERK_AVAILABLE:
            print("[WARN] Clerk SDK not available - using legacy auth")
            raise ImportError("Clerk SDK not installed")
        
        if not self.clerk_secret_key:
            print("[WARN] CLERK_SECRET_KEY not set - Clerk auth disabled")
            raise ValueError("CLERK_SECRET_KEY not configured")
        
        # Configure Clerk API client
        config = Configuration()
        config.api_key['BearerAuth'] = self.clerk_secret_key
        api_client = ApiClient(configuration=config)
        
        # Initialize API endpoints
        self.users_api = UsersApi(api_client)
        self.sessions_api = SessionsApi(api_client)
        
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_service_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required")
        
        # Use service key for admin operations (creating users)
        self.supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
        
        print("[INFO] Clerk Authentication System initialized")
        print(f"[INFO] Clerk Publishable Key: {self.clerk_publishable_key[:20]}...")
    
    def verify_clerk_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Clerk session token and return user data
        
        Args:
            session_token: Clerk session token from frontend
            
        Returns:
            Dictionary with user info or None if invalid
        """
        try:
            # Verify the session token with Clerk
            session = self.sessions_api.verify_session(
                session_id=session_token
            )
            
            if not session:
                print("[ERROR] Invalid Clerk session")
                return None
            
            # Get user ID from session
            user_id = session.user_id
            if not user_id:
                print("[ERROR] No user_id in Clerk session")
                return None
            
            # Get full user details from Clerk
            user = self.users_api.get_user(user_id=user_id)
            
            if not user:
                print("[ERROR] Could not fetch user from Clerk")
                return None
            
            # Extract user information
            user_data = {
                'clerk_id': user.id,
                'email': user.email_addresses[0].email_address if user.email_addresses else None,
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or 'User',
                'profile_image': user.profile_image_url,
                'created_at': str(user.created_at) if user.created_at else None
            }
            
            return user_data
            
        except Exception as e:
            print(f"[ERROR] Clerk token verification failed: {e}")
            return None
    
    def sync_user_to_supabase(self, clerk_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync Clerk user to Supabase database
        Creates or updates user record in Supabase
        
        Args:
            clerk_user_data: User data from Clerk
            
        Returns:
            Dictionary with success status and user info
        """
        try:
            clerk_id = clerk_user_data['clerk_id']
            email = clerk_user_data['email']
            name = clerk_user_data['name']
            profile_image = clerk_user_data.get('profile_image')
            
            # Check if user exists in Supabase
            existing_user = self.supabase.table('users').select('*').eq('clerk_id', clerk_id).execute()
            
            if existing_user.data:
                # Update existing user
                user = existing_user.data[0]
                user_id = user['id']
                
                # Update user info
                self.supabase.table('users').update({
                    'name': name,
                    'email': email,
                    'profile_image': profile_image,
                    'last_login': datetime.utcnow().isoformat()
                }).eq('id', user_id).execute()
                
                print(f"[INFO] Updated existing user: {email}")
                
            else:
                # Create new user in Supabase
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
                    return {
                        'success': False,
                        'error': 'Failed to create user in database'
                    }
                
                user = result.data[0]
                user_id = user['id']
                
                # Create personal memory database for the user
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
            print(f"[ERROR] Error syncing user to Supabase: {e}")
            return {
                'success': False,
                'error': f'Failed to sync user: {str(e)}'
            }
    
    def _create_user_memory_database(self, user_id: str):
        """
        Create personal memory database for user using Row Level Security.
        Each user gets their own isolated memory space.
        """
        try:
            # Create initial memory database entry for user
            memory_db_data = {
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'memory_count': 0,
                'last_accessed': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('user_memory_databases').insert(memory_db_data).execute()
            
            print(f"[OK] Created personal memory database for user {user_id}")
            
        except Exception as e:
            print(f"[ERROR] Error creating user memory database: {e}")
    
    def get_user_from_clerk_id(self, clerk_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from Supabase using Clerk ID"""
        try:
            result = self.supabase.table('users').select('*').eq('clerk_id', clerk_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"[ERROR] Error getting user: {e}")
            return None
    
    def require_auth(self, f):
        """Decorator to require Clerk authentication for routes"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get session token from Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Authentication required'}), 401
            
            session_token = auth_header.split(' ')[1]
            
            # Verify token with Clerk
            clerk_user_data = self.verify_clerk_token(session_token)
            
            if not clerk_user_data:
                return jsonify({'error': 'Invalid or expired session'}), 401
            
            # Sync user to Supabase
            sync_result = self.sync_user_to_supabase(clerk_user_data)
            
            if not sync_result['success']:
                return jsonify({'error': 'Failed to sync user data'}), 500
            
            # Add user to request context
            request.current_user = sync_result['user']
            return f(*args, **kwargs)
        
        return decorated_function


class ClerkUserMemoryManager:
    """
    Memory manager that operates on user-specific memory databases.
    Integrates with Clerk authentication.
    """
    
    def __init__(self, auth_system: ClerkAuthSystem):
        self.auth_system = auth_system
        self.supabase = auth_system.supabase
    
    def add_memory_for_user(self, user_id: str, content: str, tags: list = None) -> Dict[str, Any]:
        """Add a memory to user's personal database."""
        try:
            from app.core.memory_math import initial_memory_state
            encoded = initial_memory_state(content, tags)
            memory_data = {
                'user_id': user_id,
                'content': content,
                'tags': encoded['tags'],
                'score': encoded['score'],
                'created_at': datetime.utcnow().isoformat(),
                'last_accessed': encoded['last_accessed'],
                'access_count': encoded['access_count'],
            }
            
            result = self.supabase.table('user_memories').insert(memory_data).execute()
            
            if result.data:
                # Update memory count for user
                self._update_user_memory_count(user_id)
                return {
                    'success': True,
                    'memory': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to add memory'
                }
                
        except Exception as e:
            print(f"Error adding memory for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Failed to add memory'
            }
    
    def get_user_memories(self, user_id: str, limit: int = 50) -> list:
        """Get all memories for a specific user with forgetting/sleep strength applied."""
        try:
            from app.core.memory_math import (
                compute_effective_strength,
                needs_sleep_consolidation,
                apply_consolidation_update,
            )
            result = self.supabase.table('user_memories').select('*').eq('user_id', user_id).order('score', desc=True).limit(limit).execute()
            memories = result.data if result.data else []
            updated = []
            for memory in memories:
                if needs_sleep_consolidation(memory.get('last_accessed')):
                    consolidated = apply_consolidation_update(memory)
                    self._persist_memory_strength(user_id, consolidated)
                    memory = consolidated
                memory = dict(memory)
                memory['effective_strength'] = round(compute_effective_strength(memory), 4)
                updated.append(memory)
            updated.sort(key=lambda m: m.get('effective_strength', m.get('score', 0)), reverse=True)
            return updated
        except Exception as e:
            print(f"Error getting memories for user {user_id}: {e}")
            return []
    
    def search_user_memories(self, user_id: str, query: str, limit: int = 10) -> list:
        """Search memories using recall probability P(recall) = S_target / ΣS."""
        try:
            from app.core.memory_math import rank_memories_for_recall, apply_recall_update
            print(f"[SEARCH] Searching user memories for: '{query}'")

            all_memories = self.get_user_memories(user_id, 1000)
            if not all_memories:
                return []

            results = rank_memories_for_recall(all_memories, query, limit)
            reinforced = []
            for memory in results:
                updated = apply_recall_update(memory)
                self._persist_memory_strength(user_id, updated)
                reinforced.append(updated)

            return reinforced

        except Exception as e:
            print(f"Error searching memories for user {user_id}: {e}")
            return []

    def _persist_memory_strength(self, user_id: str, memory: Dict[str, Any]):
        """Persist strength updates after recall or sleep consolidation."""
        try:
            memory_id = memory.get('id')
            if not memory_id:
                return
            update_data = {
                'score': memory.get('score'),
                'access_count': memory.get('access_count'),
                'last_accessed': memory.get('last_accessed'),
            }
            self.supabase.table('user_memories').update(update_data).eq('id', memory_id).eq('user_id', user_id).execute()
        except Exception as e:
            print(f"Error persisting memory strength for {memory.get('id')}: {e}")
    
    def _update_user_memory_count(self, user_id: str):
        """Update the memory count for a user."""
        try:
            # Get current count
            count_result = self.supabase.table('user_memories').select('id', count='exact').eq('user_id', user_id).execute()
            memory_count = count_result.count if count_result.count else 0
            
            # Update user's memory database record
            self.supabase.table('user_memory_databases').update({
                'memory_count': memory_count,
                'last_accessed': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
        except Exception as e:
            print(f"Error updating memory count for user {user_id}: {e}")


# Global instances (lazy initialization)
clerk_auth_system = None
clerk_user_memory_manager = None


def get_clerk_auth_system():
    """Get or create the global Clerk auth system instance"""
    global clerk_auth_system, clerk_user_memory_manager
    
    if clerk_auth_system is None:
        try:
            clerk_auth_system = ClerkAuthSystem()
            clerk_user_memory_manager = ClerkUserMemoryManager(clerk_auth_system)
            print("[OK] Clerk authentication system ready")
        except Exception as e:
            print(f"[ERROR] Failed to initialize Clerk auth system: {e}")
            raise
    
    return clerk_auth_system, clerk_user_memory_manager


# Try to initialize at import time
try:
    if CLERK_AVAILABLE and os.getenv('CLERK_SECRET_KEY'):
        clerk_auth_system, clerk_user_memory_manager = get_clerk_auth_system()
except Exception as e:
    print(f"[WARN] Clerk auth system will be initialized on first use: {e}")

