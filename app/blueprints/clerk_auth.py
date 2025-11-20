#!/usr/bin/env python3
"""
Clerk Authentication API Blueprint
Handles user authentication via Clerk OAuth (Google sign-in)
and syncs with Supabase database
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import os

clerk_auth_bp = Blueprint('clerk_auth', __name__)

# These will be initialized when the blueprint is registered
clerk_auth_system = None
clerk_user_memory_manager = None


def init_clerk_auth_blueprint():
    """Initialize Clerk auth system for the blueprint"""
    global clerk_auth_system, clerk_user_memory_manager
    try:
        # Try REST API first (no async issues!)
        from app.core.clerk_rest_api import get_clerk_rest_api
        clerk_auth_system = get_clerk_rest_api()
        print("[OK] Clerk REST API initialized (no async issues!)")
        
        # Initialize memory manager for Clerk users
        if clerk_auth_system:
            try:
                from app.core.clerk_auth_system import ClerkUserMemoryManager
                clerk_user_memory_manager = ClerkUserMemoryManager(clerk_auth_system)
                print("[OK] Clerk User Memory Manager initialized")
            except Exception as mem_error:
                print(f"[WARN] Clerk memory manager not available: {mem_error}")
                clerk_user_memory_manager = None
    except Exception as e:
        print(f"[WARN] Clerk REST API not available: {e}")
        print("[INFO] Using legacy auth system")
        clerk_auth_system = None
        clerk_user_memory_manager = None


@clerk_auth_bp.route('/session', methods=['POST'])
def verify_session():
    """
    Verify Clerk session and sync user to Supabase
    Frontend should call this after Clerk authentication
    Supports both JWT tokens (recommended) and session IDs (deprecated)
    """
    try:
        if not clerk_auth_system:
            return jsonify({
                'error': 'Clerk authentication not configured',
                'message': 'Please set CLERK_SECRET_KEY in environment variables'
            }), 503
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Get token/session_id from request
        # Prefer JWT token (session_token) over session_id
        token = data.get('session_token')
        session_id = data.get('session_id')
        
        # Use token if provided, otherwise fall back to session_id
        auth_value = token or session_id
        
        if not auth_value:
            return jsonify({'error': 'Session token or ID is required'}), 400
        
        # Auto-detect if it's a JWT token (contains dots) or session ID
        is_jwt = '.' in auth_value and auth_value.count('.') >= 2
        
        if is_jwt:
            print(f"[INFO] Verifying JWT token: {auth_value[:20]}...")
        else:
            print(f"[INFO] Verifying session ID: {auth_value[:20]}...")
        
        # Verify token/session and get user with REST API
        clerk_user_data = clerk_auth_system.verify_and_get_user(auth_value, is_jwt=is_jwt)
        
        if not clerk_user_data:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Sync user to Supabase
        sync_result = clerk_auth_system.sync_user_to_supabase(clerk_user_data)
        
        if not sync_result['success']:
            return jsonify({'error': sync_result.get('error', 'Failed to sync user')}), 500
        
        print(f"[INFO] User synced successfully: {sync_result['user']['email']}")
        
        return jsonify({
            'success': True,
            'user': sync_result['user'],
            'message': 'Authentication successful'
        }), 200
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Session verification error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Session verification failed', 'details': str(e)}), 500


@clerk_auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """
    Verify current session from Authorization header
    Returns user info if valid
    Expects: Authorization: Bearer <session_id>
    """
    try:
        if not clerk_auth_system:
            return jsonify({
                'error': 'Clerk authentication not configured',
                'message': 'Please set CLERK_SECRET_KEY in environment variables'
            }), 503
        
        # Get session ID from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        session_id = auth_header.split(' ')[1]
        
        print(f"[INFO] Verifying session via header: {session_id[:20]}...")
        
        # Verify session with Clerk
        clerk_user_data = clerk_auth_system.verify_clerk_token(session_id)
        
        if not clerk_user_data:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Get user from Supabase
        user = clerk_auth_system.get_user_from_clerk_id(clerk_user_data['clerk_id'])
        
        if not user:
            # Sync user if not in database
            print(f"[INFO] User not in database, syncing...")
            sync_result = clerk_auth_system.sync_user_to_supabase(clerk_user_data)
            if sync_result['success']:
                user = sync_result['user']
            else:
                return jsonify({'error': 'Failed to sync user'}), 500
        
        return jsonify({
            'success': True,
            'user': user
        }), 200
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Token verification error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Token verification failed', 'details': str(e)}), 500


@clerk_auth_bp.route('/signout', methods=['POST'])
def signout():
    """
    Sign out user (handled by Clerk on client-side)
    This endpoint just confirms the action
    """
    return jsonify({
        'success': True,
        'message': 'Signed out successfully'
    }), 200


@clerk_auth_bp.route('/user', methods=['GET'])
def get_current_user():
    """
    Get current authenticated user's information
    Requires valid session token in Authorization header
    """
    import time
    start_time = time.time()
    
    try:
        if not clerk_auth_system:
            return jsonify({
                'error': 'Clerk authentication not configured'
            }), 503
        
        # Get session token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        session_id = auth_header.split(' ')[1]
        
        print(f"[PERF] /user endpoint called")
        
        # Verify session with Clerk
        verify_start = time.time()
        clerk_user_data = clerk_auth_system.verify_clerk_token(session_id)
        print(f"[PERF] Token verification took: {(time.time() - verify_start)*1000:.0f}ms")
        
        if not clerk_user_data:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Get user from Supabase with memory statistics
        db_start = time.time()
        user = clerk_auth_system.get_user_from_clerk_id(clerk_user_data['clerk_id'])
        print(f"[PERF] Get user from DB took: {(time.time() - db_start)*1000:.0f}ms")
        
        if not user:
            # Try to sync user if not found in database
            print(f"[INFO] User not found in database, syncing from Clerk...")
            sync_result = clerk_auth_system.sync_user_to_supabase(clerk_user_data)
            if sync_result['success']:
                user = sync_result['user']
            else:
                return jsonify({'error': 'Failed to sync user data'}), 500
        
        # Get memory statistics efficiently (use COUNT instead of loading all memories)
        total_memories = 0
        most_recent_memory = None
        try:
            if clerk_user_memory_manager:
                # Use COUNT query instead of loading all memories
                mem_start = time.time()
                count_result = clerk_auth_system.supabase.table('user_memories').select('id', count='exact').eq('user_id', user['id']).execute()
                total_memories = count_result.count if count_result.count else 0
                print(f"[PERF] Memory COUNT query took: {(time.time() - mem_start)*1000:.0f}ms")
                
                # Get only the most recent memory for timestamp
                if total_memories > 0:
                    recent_start = time.time()
                    recent_result = clerk_auth_system.supabase.table('user_memories').select('created_at').eq('user_id', user['id']).order('created_at', desc=True).limit(1).execute()
                    if recent_result.data:
                        most_recent_memory = recent_result.data[0].get('created_at')
                    print(f"[PERF] Recent memory query took: {(time.time() - recent_start)*1000:.0f}ms")
                
                print(f"[PERFORMANCE] Memory count: {total_memories} (efficient query)")
        except Exception as mem_error:
            print(f"[WARN] Failed to get memory count: {mem_error}")
            total_memories = 0
        
        # Get conversation count efficiently
        total_conversations = 0
        try:
            conv_start = time.time()
            threads_result = clerk_auth_system.supabase.table('user_chat_threads').select('id', count='exact').eq('user_id', user['id']).execute()
            total_conversations = threads_result.count if threads_result.count else 0
            print(f"[PERF] Conversation COUNT query took: {(time.time() - conv_start)*1000:.0f}ms")
            print(f"[PERFORMANCE] Conversation count: {total_conversations} (efficient query)")
        except Exception as conv_error:
            print(f"[WARN] Failed to get conversation count: {conv_error}")
            total_conversations = 0
        
        user_profile = {
            'user': user,
            'stats': {
                'total_memories': total_memories,
                'total_conversations': total_conversations,
                'most_recent_memory': most_recent_memory
            }
        }
        
        total_time = (time.time() - start_time) * 1000
        print(f"[PERF] ✅ /user endpoint total time: {total_time:.0f}ms")
        
        return jsonify({
            'success': True,
            'profile': user_profile
        }), 200
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error getting user profile: {e}")
        print(traceback.format_exc())
        return jsonify({'error': 'Failed to get user profile', 'details': str(e)}), 500


@clerk_auth_bp.route('/config', methods=['GET'])
def get_clerk_config():
    """
    Get Clerk publishable key for frontend configuration
    This is safe to expose publicly
    """
    # Use hardcoded value from config
    from config import config
    clerk_publishable_key = config.clerk_publishable_key
    
    return jsonify({
        'publishable_key': clerk_publishable_key
    }), 200


# Initialize auth system when module is loaded
init_clerk_auth_blueprint()

