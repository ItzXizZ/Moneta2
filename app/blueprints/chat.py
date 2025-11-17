#!/usr/bin/env python3
"""
Chat API Blueprint
Handles chat messages, conversation threads, and chat history.
"""

from flask import Blueprint, request, jsonify

chat_bp = Blueprint('chat', __name__)

# These will be initialized lazily
auth_system = None
clerk_auth_system = None
user_conversation_service = None


def _get_services():
    """Lazy initialization of services"""
    global auth_system, clerk_auth_system, user_conversation_service
    if user_conversation_service is None:
        from app.services.user_conversation_service import user_conversation_service as ucs
        user_conversation_service = ucs
    if auth_system is None:
        try:
            from app.core.auth_system import get_auth_system
            auth_system, _ = get_auth_system()
        except Exception:
            pass
    if clerk_auth_system is None:
        try:
            from app.core.clerk_auth_system import get_clerk_auth_system
            clerk_auth_system, _ = get_clerk_auth_system()
        except Exception:
            pass
    return auth_system, clerk_auth_system, user_conversation_service


def _get_user_id():
    """Get user ID from request (authenticated or anonymous) - supports both legacy and Clerk auth"""
    auth, clerk_auth, _ = _get_services()
    user_id = 'anonymous'
    
    auth_header = request.headers.get('Authorization')
    print(f"[DEBUG] _get_user_id called - Authorization header present: {bool(auth_header)}")
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        print(f"[DEBUG] Token extracted (first 20 chars): {token[:20]}...")
        
        # Check if token is a JWT (contains dots)
        is_jwt_token = '.' in token and token.count('.') >= 2
        print(f"[DEBUG] Is JWT token: {is_jwt_token} (dots count: {token.count('.')})")
        
        # Try Clerk REST API first for JWT tokens
        if is_jwt_token:
            try:
                from app.core.clerk_rest_api import get_clerk_rest_api
                clerk_rest = get_clerk_rest_api()
                if clerk_rest:
                    print(f"[DEBUG] Verifying Clerk JWT token...")
                    clerk_user_data = clerk_rest.verify_and_get_user(token, is_jwt=True)
                    if clerk_user_data:
                        # Sync user to Supabase
                        sync_result = clerk_rest.sync_user_to_supabase(clerk_user_data)
                        if sync_result['success']:
                            user = sync_result['user']
                            user_id = user['id']
                            request.current_user = user
                            print(f"[OK] Clerk user authenticated: {user_id}")
                            return user_id
            except Exception as e:
                print(f"[DEBUG] Clerk JWT verification failed, trying legacy: {e}")
        
        # Try legacy Clerk auth with session token
        if clerk_auth is not None and not is_jwt_token:
            try:
                clerk_user_data = clerk_auth.verify_clerk_token(token)
                if clerk_user_data:
                    # Sync user to Supabase
                    sync_result = clerk_auth.sync_user_to_supabase(clerk_user_data)
                    if sync_result['success']:
                        user = sync_result['user']
                        user_id = user['id']
                        request.current_user = user
                        print(f"[OK] Clerk user authenticated (legacy): {user_id}")
                        return user_id
            except Exception as e:
                print(f"[DEBUG] Clerk session auth failed: {e}")
        
        # Fallback to legacy JWT auth
        if auth is not None:
            user = auth.get_user_from_token(token)
            if user:
                user_id = user['id']
                request.current_user = user
                print(f"[OK] Legacy user authenticated: {user_id}")
    else:
        print(f"[WARN] No Authorization header found - defaulting to anonymous")
    
    print(f"[DEBUG] _get_user_id returning: '{user_id}'")
    return user_id


@chat_bp.route('/send', methods=['POST'])
def send_message():
    """Handle sending a message and generating AI response"""
    try:
        _, _, conv_service = _get_services()
        
        data = request.get_json()
        message = data.get('message', '').strip()
        thread_id = data.get('thread_id')
        request_id = data.get('request_id')
        
        user_id = _get_user_id()
        
        # Process the message
        thread_id, ai_response, memory_context, error = conv_service.process_message(
            message, thread_id, user_id, request_id
        )
        
        if error:
            if error == "Duplicate request detected":
                return jsonify({'success': False, 'error': error}), 409
            else:
                return jsonify({'success': False, 'error': error}), 400
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'thread_id': thread_id,
            'memory_context': memory_context
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/thread/end', methods=['POST'])
def end_thread():
    """Extract memories from a conversation thread when it ends"""
    try:
        _, _, conv_service = _get_services()
        
        data = request.get_json()
        thread_id = data.get('thread_id')
        
        user_id = _get_user_id()
        
        success, extracted_memories, message = conv_service.end_thread_and_extract_memories(
            thread_id, user_id
        )
        
        if not success:
            return jsonify({'success': False, 'error': message}), 400
        
        return jsonify({
            'success': True,
            'extracted_memories': extracted_memories,
            'count': len(extracted_memories),
            'message': message
        })
        
    except Exception as e:
        print(f"Exception in /end_thread endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/thread/new', methods=['POST'])
def create_new_thread():
    """Create a new empty chat thread"""
    try:
        _, _, conv_service = _get_services()
        user_id = _get_user_id()
        
        thread_id = conv_service.create_new_thread(user_id)
        
        return jsonify({
            'success': True,
            'thread_id': thread_id,
            'message': 'New thread created successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/thread/<thread_id>', methods=['GET'])
def get_chat_history(thread_id):
    """Get chat history for a specific thread"""
    try:
        _, _, conv_service = _get_services()
        user_id = _get_user_id()
        
        messages = conv_service.get_thread_messages(thread_id, user_id)
        return jsonify({'thread_id': thread_id, 'messages': messages})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/thread/<thread_id>', methods=['DELETE'])
def delete_chat_history(thread_id):
    """Delete a specific chat thread"""
    try:
        _, _, conv_service = _get_services()
        user_id = _get_user_id()
        
        success = conv_service.clear_thread(thread_id, user_id)
        if success:
            return jsonify({'success': True, 'message': 'Thread deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Thread not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/thread/last', methods=['GET'])
def get_last_chat_history():
    """Get the last chat history for the user"""
    try:
        _, _, conv_service = _get_services()
        user_id = _get_user_id()
        
        threads = conv_service.get_user_threads(user_id)
        if not threads:
            return jsonify({'thread_id': None, 'messages': []})
        
        last_thread = threads[-1]
        messages = conv_service.get_thread_messages(last_thread, user_id)
        return jsonify({'thread_id': last_thread, 'messages': messages})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@chat_bp.route('/threads', methods=['GET'])
def get_all_thread_ids():
    """Get all thread IDs for the user"""
    try:
        _, _, conv_service = _get_services()
        user_id = _get_user_id()
        
        threads = conv_service.get_user_threads(user_id)
        return jsonify({'threads': threads})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



