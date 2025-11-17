#!/usr/bin/env python3
"""
Memory API Blueprint
Handles memory operations, network visualization, and memory search.
"""

from flask import Blueprint, request, jsonify
from config import config

memory_bp = Blueprint('memory', __name__)

# These will be initialized lazily
auth_system = None
user_memory_manager = None


def _get_services():
    """Lazy initialization of services"""
    global auth_system, user_memory_manager
    if auth_system is None:
        from app.core.auth_system import get_auth_system
        auth_system, user_memory_manager = get_auth_system()
    return auth_system, user_memory_manager


def _get_user_id():
    """Get user ID from request - requires authentication (no anonymous mode)"""
    auth_header = request.headers.get('Authorization')
    print(f"[MEMORY] _get_user_id called - Authorization header present: {bool(auth_header)}")
    
    if not auth_header or not auth_header.startswith('Bearer '):
        print(f"[MEMORY] No Authorization header found")
        return None
    
    token = auth_header.split(' ')[1]
    print(f"[MEMORY] Token extracted (first 20 chars): {token[:20]}...")
    
    # Check if token is a JWT (contains dots)
    is_jwt_token = '.' in token and token.count('.') >= 2
    print(f"[MEMORY] Is JWT token: {is_jwt_token} (dots count: {token.count('.')})")
    
    # Try Clerk REST API first for JWT tokens
    if is_jwt_token:
        try:
            from app.core.clerk_rest_api import get_clerk_rest_api
            clerk_rest = get_clerk_rest_api()
            if clerk_rest:
                print(f"[MEMORY] Verifying Clerk JWT token...")
                clerk_user_data = clerk_rest.verify_and_get_user(token, is_jwt=True)
                if clerk_user_data:
                    # Sync user to Supabase
                    sync_result = clerk_rest.sync_user_to_supabase(clerk_user_data)
                    if sync_result['success']:
                        user = sync_result['user']
                        user_id = user['id']
                        request.current_user = user
                        print(f"[MEMORY] Clerk user authenticated: {user_id}")
                        return user_id
                else:
                    print(f"[MEMORY] JWT token verification failed (likely expired)")
                    return None
        except Exception as e:
            print(f"[MEMORY] Clerk JWT verification failed: {e}")
            return None
    
    # Fallback to legacy JWT auth
    auth, _ = _get_services()
    if auth is not None:
        user = auth.get_user_from_token(token)
        if user:
            user_id = user['id']
            request.current_user = user
            print(f"[MEMORY] Legacy user authenticated: {user_id}")
            return user_id
    
    print(f"[MEMORY] Authentication failed - no valid token")
    return None


@memory_bp.route('/availability', methods=['GET'])
def check_memory_availability():
    """Check if the memory system is available"""
    return jsonify({'available': config.memory_available})


@memory_bp.route('/new', methods=['GET'])
def get_new_memories():
    """Get and clear the queue of new memories for real-time network updates"""
    with config.session_new_memories_lock:
        new_memories = config.session_new_memories.copy()
        config.session_new_memories.clear()
    
    return jsonify({
        'memories': new_memories,
        'count': len(new_memories)
    })


@memory_bp.route('/network', methods=['GET'])
def memory_network():
    """Get memory network data for visualization (user-specific)"""
    try:
        user_id = _get_user_id()
        
        # Require authentication - no anonymous mode
        if not user_id:
            print(f"[MEMORY] /network endpoint - authentication required")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please sign in to access your memory network'
            }), 401
        
        print(f"[MEMORY] /network endpoint called for user: '{user_id}'")
        
        threshold = float(request.args.get('threshold', 0.4))
        _, mem_manager = _get_services()
        
        if mem_manager is None:
            print(f"[MEMORY] Memory manager not available!")
            return jsonify({
                'nodes': [],
                'edges': [],
                'user_specific': True,
                'total_memories': 0,
                'connections': 0,
                'error': 'Memory system not available'
            })
        
        user_memories = mem_manager.get_user_memories(user_id, 1000)
        print(f"[MEMORY] Found {len(user_memories)} memories for user '{user_id}'")
        
        # Calculate scores and create nodes
        nodes = []
        edges = []
        
        for memory in user_memories:
            score = _calculate_memory_score(memory, user_memories)
            nodes.append({
                'id': memory['id'],
                'label': memory['content'][:50] + ('...' if len(memory['content']) > 50 else ''),
                'title': memory['content'],
                'score': score,
                'created': memory.get('created_at', ''),
                'tags': memory.get('tags', []),
                'size': 20 + min(score, 100) * 0.5,
            })
        
        # Calculate connections
        for i, memory1 in enumerate(user_memories):
            for j, memory2 in enumerate(user_memories):
                if i >= j:
                    continue
                
                similarity = _calculate_similarity(memory1, memory2)
                
                if similarity > threshold:
                    edges.append({
                        'from': memory1['id'],
                        'to': memory2['id'],
                        'value': similarity,
                        'label': f'{similarity:.2f}',
                        'color': {
                            'color': '#4CAF50' if similarity > 0.6 else 
                                    '#FFC107' if similarity > 0.4 else 
                                    '#FF9800'
                        }
                    })
        
        return jsonify({
            'nodes': nodes,
            'edges': edges,
            'user_specific': True,
            'total_memories': len(user_memories),
            'connections': len(edges)
        })
        
    except Exception as e:
        print(f"Error in memory-network route: {e}")
        return jsonify({'nodes': [], 'edges': [], 'error': str(e)})


@memory_bp.route('/user', methods=['GET'])
def get_user_memories():
    """Get all memories for the authenticated user"""
    try:
        user_id = _get_user_id()
        
        # Require authentication
        if not user_id:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please sign in to access your memories'
            }), 401
        
        limit = request.args.get('limit', 50, type=int)
        _, mem_manager = _get_services()
        memories = mem_manager.get_user_memories(user_id, limit)
        
        return jsonify({
            'success': True,
            'memories': memories,
            'count': len(memories)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve memories'}), 500


@memory_bp.route('/add', methods=['POST'])
def add_user_memory():
    """Add a new memory for the authenticated user"""
    try:
        user_id = _get_user_id()
        
        # Require authentication
        if not user_id:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please sign in to add memories'
            }), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content', '').strip()
        tags = data.get('tags', [])
        
        if not content:
            return jsonify({'error': 'Memory content is required'}), 400
        
        _, mem_manager = _get_services()
        
        result = mem_manager.add_memory_for_user(user_id, content, tags)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Memory added successfully',
                'memory': result['memory']
            }), 201
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to add memory'}), 500


@memory_bp.route('/search', methods=['GET'])
def search_user_memories():
    """Search memories for the authenticated user"""
    try:
        user_id = _get_user_id()
        
        # Require authentication
        if not user_id:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please sign in to search memories'
            }), 401
        
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        _, mem_manager = _get_services()
        
        memories = mem_manager.search_user_memories(user_id, query, limit)
        
        return jsonify({
            'success': True,
            'query': query,
            'memories': memories,
            'count': len(memories)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to search memories'}), 500


def _calculate_memory_score(memory, all_memories):
    """Calculate a meaningful score based on content quality, tags, and connections"""
    score = 0
    
    content = memory.get('content', '')
    score += min(len(content) * 0.1, 20)
    
    tags = memory.get('tags', [])
    score += len(tags) * 2
    
    if any(keyword in content.lower() for keyword in ['python', 'machine learning', 'ai', 'programming']):
        score += 15
    
    if len(content.split()) > 10:
        score += 10
    
    connection_count = 0
    for other_memory in all_memories:
        if other_memory['id'] != memory['id']:
            other_tags = set(other_memory.get('tags', []))
            shared_tags = len(set(tags) & other_tags)
            if shared_tags > 0:
                connection_count += 1
    
    score += min(connection_count * 3, 30)
    return max(score, 5)


def _calculate_similarity(memory1, memory2):
    """Calculate similarity between two memories"""
    # Tag similarity
    tags1 = set(memory1.get('tags', []))
    tags2 = set(memory2.get('tags', []))
    
    if not tags1 or not tags2:
        tag_similarity = 0
    else:
        shared_tags = len(tags1 & tags2)
        total_unique_tags = len(tags1 | tags2)
        tag_similarity = (shared_tags / total_unique_tags) * 2
    
    # Content similarity
    content1 = memory1['content'].lower()
    content2 = memory2['content'].lower()
    
    common_words = {'i', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    words1 = set(word.strip('.,!?;:') for word in content1.split() if word.lower() not in common_words and len(word) > 2)
    words2 = set(word.strip('.,!?;:') for word in content2.split() if word.lower() not in common_words and len(word) > 2)
    
    if not words1 or not words2:
        content_similarity = 0
    else:
        shared_words = len(words1 & words2)
        total_unique_words = len(words1 | words2)
        content_similarity = shared_words / total_unique_words
    
    return (tag_similarity * 0.5) + (content_similarity * 0.5)




