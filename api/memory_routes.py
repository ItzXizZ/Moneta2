#!/usr/bin/env python3

from flask import request, jsonify
from config import config
from services.memory_search_service import memory_search_service
from auth_system import auth_system, user_memory_manager, get_auth_system

def register_memory_routes(app):
    """Register all memory-related routes with the Flask app"""
    # Ensure auth system is initialized
    global auth_system, user_memory_manager
    if auth_system is None:
        auth_system, user_memory_manager = get_auth_system()
    
    @app.route('/check_memory_availability')
    def check_memory_availability():
        """Check if the memory system is available"""
        return jsonify({'available': config.memory_available})
    
    @app.route('/new-memories')
    def get_new_memories():
        """Get and clear the queue of new memories for real-time network updates"""
        print(f"🔧 DEBUG: /new-memories endpoint called")
        
        with config.session_new_memories_lock:
            print(f"🔧 DEBUG: Session queue size before copy: {len(config.session_new_memories)}")
            new_memories = config.session_new_memories.copy()
            config.session_new_memories.clear()
            print(f"🔧 DEBUG: Session queue size after clear: {len(config.session_new_memories)}")
        
        print(f"🔧 DEBUG: Returning {len(new_memories)} new memories")
        if new_memories:
            for i, memory in enumerate(new_memories):
                print(f"🔧 DEBUG: Memory {i+1}: {memory.get('content', 'N/A')[:30]}...")
        
        return jsonify({
            'memories': new_memories,
            'count': len(new_memories)
        })
    
    @app.route('/memory-network')
    @auth_system.require_auth
    def memory_network():
        """Get memory network data for visualization (user-specific)"""
        try:
            # Get threshold from query param, default 0.35
            threshold = float(request.args.get('threshold', config.min_relevance_threshold))
            
            # Get user ID from authenticated request
            user_id = request.current_user['id']
            
            # Get user-specific memories
            user_memories = user_memory_manager.get_user_memories(user_id, 1000)
            
            # Create nodes for the network
            nodes = []
            edges = []
            
            for memory in user_memories:
                nodes.append({
                    'id': memory['id'],
                    'label': memory['content'][:50] + ('...' if len(memory['content']) > 50 else ''),
                    'title': memory['content'],
                    'score': memory.get('score', 0),
                    'created': memory.get('created_at', ''),
                    'tags': memory.get('tags', []),
                    'size': 20 + min(memory.get('score', 0), 100) * 0.5,
                })
            
            # Calculate connections between memories
            print(f"🔧 DEBUG: Calculating connections for {len(user_memories)} memories...")
            
            # Simple connection calculation based on shared tags and content similarity
            for i, memory1 in enumerate(user_memories):
                for j, memory2 in enumerate(user_memories):
                    if i >= j:  # Avoid duplicate connections and self-connections
                        continue
                    
                    # Calculate similarity based on shared tags
                    tags1 = set(memory1.get('tags', []))
                    tags2 = set(memory2.get('tags', []))
                    tag_similarity = len(tags1 & tags2) / len(tags1 | tags2) if tags1 | tags2 else 0
                    
                    # Calculate content similarity (basic word overlap)
                    words1 = set(memory1['content'].lower().split())
                    words2 = set(memory2['content'].lower().split())
                    content_similarity = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0
                    
                    # Combined similarity score
                    similarity = (tag_similarity * 0.6) + (content_similarity * 0.4)
                    
                    # Create edge if similarity is above threshold
                    if similarity > 0.15:  # Adjusted threshold for better connections
                        edges.append({
                            'from': memory1['id'],
                            'to': memory2['id'],
                            'value': similarity,
                            'label': f'{similarity:.2f}',
                            'color': {'color': '#4CAF50' if similarity > 0.3 else '#FFC107'}
                        })
            
            print(f"🔧 DEBUG: Created {len(edges)} connections")
            
            return jsonify({
                'nodes': nodes,
                'edges': edges,
                'user_specific': True,
                'total_memories': len(user_memories),
                'connections': len(edges)
            })
            
        except Exception as e:
            print(f"❌ Error in memory-network route: {e}")
            return jsonify({'nodes': [], 'edges': []}) 