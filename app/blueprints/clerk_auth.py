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
        
        print(f"[INFO] Getting user profile for session: {session_id[:20]}...")
        
        # Verify session with Clerk
        clerk_user_data = clerk_auth_system.verify_clerk_token(session_id)
        
        if not clerk_user_data:
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Get user from Supabase with memory statistics
        user = clerk_auth_system.get_user_from_clerk_id(clerk_user_data['clerk_id'])
        
        if not user:
            # Try to sync user if not found in database
            print(f"[INFO] User not found in database, syncing from Clerk...")
            sync_result = clerk_auth_system.sync_user_to_supabase(clerk_user_data)
            if sync_result['success']:
                user = sync_result['user']
            else:
                return jsonify({'error': 'Failed to sync user data'}), 500
        
        # Get memory statistics safely
        try:
            if clerk_user_memory_manager:
                memories = clerk_user_memory_manager.get_user_memories(user['id'], 1000)
            else:
                memories = []
        except Exception as mem_error:
            print(f"[WARN] Failed to get memories: {mem_error}")
            memories = []
        
        # Get conversation count
        total_conversations = 0
        try:
            threads_result = clerk_auth_system.supabase.table('user_chat_threads').select('id').eq('user_id', user['id']).execute()
            total_conversations = len(threads_result.data) if threads_result.data else 0
            print(f"[INFO] User has {total_conversations} conversations")
        except Exception as conv_error:
            print(f"[WARN] Failed to get conversation count: {conv_error}")
            total_conversations = 0
        
        user_profile = {
            'user': user,
            'stats': {
                'total_memories': len(memories),
                'total_conversations': total_conversations,
                'average_score': sum(m.get('score', 0) for m in memories) / len(memories) if memories else 0,
                'most_recent_memory': max(memories, key=lambda x: x.get('created_at', ''))['created_at'] if memories else None
            }
        }
        
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

