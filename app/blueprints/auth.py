#!/usr/bin/env python3
"""
Authentication API Blueprint
Handles user registration, login, and authentication verification.
"""

from flask import Blueprint, request, jsonify
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# These will be initialized when the blueprint is registered
auth_system = None
user_memory_manager = None


def init_auth_blueprint():
    """Initialize auth system for the blueprint"""
    global auth_system, user_memory_manager
    from app.core.auth_system import get_auth_system
    auth_system, user_memory_manager = get_auth_system()


def require_auth_if_available(f):
    """Decorator that requires auth if auth_system is available, otherwise allows access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if auth_system is None:
            request.current_user = {'id': 'anonymous', 'email': 'anonymous@example.com'}
            return f(*args, **kwargs)
        else:
            return auth_system.require_auth(f)(*args, **kwargs)
    return decorated_function


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not password or len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Register user
        result = auth_system.register_user(name, email, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'user': result['user'],
                'token': result['token']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Authenticate user
        result = auth_system.login_user(email, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': result['user'],
                'token': result['token']
            }), 200
        else:
            return jsonify({'error': result['error']}), 401
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/verify', methods=['GET'])
@require_auth_if_available
def verify_token():
    """Verify JWT token and return user info"""
    return jsonify({
        'success': True,
        'user': request.current_user
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@require_auth_if_available
def logout():
    """Logout user (client-side token removal)"""
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@require_auth_if_available
def get_user_profile():
    """Get user profile information"""
    try:
        user_id = request.current_user['id']
        
        # Get user's memory statistics
        memories = user_memory_manager.get_user_memories(user_id, 1000)
        
        # Get user's conversation count
        total_conversations = 0
        try:
            threads_result = auth_system.supabase.table('user_chat_threads').select('id').eq('user_id', user_id).execute()
            total_conversations = len(threads_result.data) if threads_result.data else 0
        except Exception as e:
            print(f"Error getting conversation count: {e}")
            total_conversations = 0
        
        profile_data = {
            'user': request.current_user,
            'stats': {
                'total_memories': len(memories),
                'total_conversations': total_conversations,
                'average_score': sum(m.get('score', 0) for m in memories) / len(memories) if memories else 0,
                'most_recent_memory': max(memories, key=lambda x: x['created_at'])['created_at'] if memories else None
            }
        }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        }), 200
        
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500


# Initialize auth system when module is loaded
init_auth_blueprint()




