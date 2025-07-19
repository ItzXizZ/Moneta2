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
    def memory_network():
        """Get memory network data for visualization (user-specific)"""
        try:
            # Get threshold from query param, default 0.35
            threshold = float(request.args.get('threshold', 0.4))  # Increased default threshold
            
            # Use anonymous user ID for now
            user_id = 'anonymous'
            
            # Check if auth system is available
            if auth_system is not None:
                # Try to get user from token if available
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    user = auth_system.get_user_from_token(token)
                    if user:
                        user_id = user['id']
                        request.current_user = user
                        print(f"🔧 DEBUG: Authenticated user: {user_id}")
                    else:
                        print(f"🔧 DEBUG: Invalid token, using anonymous user")
                else:
                    print(f"🔧 DEBUG: No auth header, using anonymous user")
            else:
                print(f"🔧 DEBUG: Auth system not available, using anonymous user")
            
            # Get user-specific memories
            if user_memory_manager is None:
                print(f"🔧 DEBUG: User memory manager not available, returning empty network")
                return jsonify({
                    'nodes': [],
                    'edges': [],
                    'user_specific': True,
                    'total_memories': 0,
                    'connections': 0,
                    'error': 'Memory system not available'
                })
            
            user_memories = user_memory_manager.get_user_memories(user_id, 1000)
            print(f"🔧 DEBUG: Retrieved {len(user_memories)} memories for user {user_id}")
            
            # Debug: Check the structure of the first memory
            if user_memories:
                first_memory = user_memories[0]
                print(f"🔧 DEBUG: First memory structure: {list(first_memory.keys())}")
                print(f"🔧 DEBUG: First memory content: {first_memory.get('content', 'NO CONTENT')[:50]}...")
                print(f"🔧 DEBUG: First memory tags: {first_memory.get('tags', 'NO TAGS')}")
                print(f"🔧 DEBUG: First memory score: {first_memory.get('score', 'NO SCORE')}")
            
            # Calculate meaningful scores for each memory
            def calculate_memory_score(memory, all_memories):
                """Calculate a meaningful score based on content quality, tags, and connections"""
                score = 0
                
                # Base score from content length and quality
                content = memory.get('content', '')
                score += min(len(content) * 0.1, 20)  # Length bonus, max 20
                
                # Tag bonus
                tags = memory.get('tags', [])
                score += len(tags) * 2  # 2 points per tag
                
                # Content quality indicators
                if any(keyword in content.lower() for keyword in ['python', 'machine learning', 'ai', 'programming', 'data science']):
                    score += 15  # Technical content bonus
                
                if len(content.split()) > 10:
                    score += 10  # Detailed content bonus
                
                # Connection potential bonus (memories that connect to many others get higher scores)
                connection_count = 0
                for other_memory in all_memories:
                    if other_memory['id'] != memory['id']:
                        # Check for shared tags
                        other_tags = set(other_memory.get('tags', []))
                        shared_tags = len(set(tags) & other_tags)
                        if shared_tags > 0:
                            connection_count += 1
                
                score += min(connection_count * 3, 30)  # Connection bonus, max 30
                
                # Ensure minimum score
                return max(score, 5)
            
            # Calculate scores for all memories
            for memory in user_memories:
                memory['calculated_score'] = calculate_memory_score(memory, user_memories)
                print(f"🔧 DEBUG: Memory '{memory['content'][:30]}...' - Calculated score: {memory['calculated_score']}")
            
            # Create nodes for the network with calculated scores
            nodes = []
            edges = []
            
            for memory in user_memories:
                score = memory.get('calculated_score', 5)
                print(f"🔧 DEBUG: Creating node for '{memory['content'][:30]}...' - Score: {score}")
                nodes.append({
                    'id': memory['id'],
                    'label': memory['content'][:50] + ('...' if len(memory['content']) > 50 else ''),
                    'title': memory['content'],
                    'score': score,
                    'created': memory.get('created_at', ''),
                    'tags': memory.get('tags', []),
                    'size': 20 + min(score, 100) * 0.5,
                })
            
            # Improved connection calculation with higher threshold and better algorithm
            print(f"🔧 DEBUG: Calculating connections for {len(user_memories)} memories...")
            
            # Calculate connections with improved algorithm
            for i, memory1 in enumerate(user_memories):
                for j, memory2 in enumerate(user_memories):
                    if i >= j:  # Avoid duplicate connections and self-connections
                        continue
                    
                    # Calculate tag similarity (weighted more heavily)
                    tags1 = set(memory1.get('tags', []))
                    tags2 = set(memory2.get('tags', []))
                    
                    if not tags1 or not tags2:
                        tag_similarity = 0
                    else:
                        shared_tags = len(tags1 & tags2)
                        total_unique_tags = len(tags1 | tags2)
                        tag_similarity = (shared_tags / total_unique_tags) * 2  # Boost tag importance
                    
                    # Calculate content similarity with improved algorithm
                    content1 = memory1['content'].lower()
                    content2 = memory2['content'].lower()
                    
                    # Split into meaningful words (filter out common words)
                    common_words = {'i', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'love', 'like', 'enjoy', 'interested', 'am', 'my', 'me', 'you', 'he', 'she', 'it', 'we', 'they'}
                    
                    words1 = set(word.strip('.,!?;:') for word in content1.split() if word.lower() not in common_words and len(word) > 2)
                    words2 = set(word.strip('.,!?;:') for word in content2.split() if word.lower() not in common_words and len(word) > 2)
                    
                    if not words1 or not words2:
                        content_similarity = 0
                    else:
                        shared_words = len(words1 & words2)
                        total_unique_words = len(words1 | words2)
                        content_similarity = shared_words / total_unique_words
                    
                    # Calculate technical similarity (bonus for technical content)
                    technical_keywords = {'python', 'programming', 'machine learning', 'ai', 'data science', 'web development', 'flask', 'react', 'javascript', 'docker', 'git', 'database', 'nlp', 'neural networks'}
                    
                    tech_words1 = words1 & technical_keywords
                    tech_words2 = words2 & technical_keywords
                    tech_similarity = len(tech_words1 & tech_words2) / max(len(tech_words1 | tech_words2), 1)
                    
                    # Combined similarity score with better weighting
                    similarity = (tag_similarity * 0.5) + (content_similarity * 0.3) + (tech_similarity * 0.2)
                    
                    # Higher threshold and additional criteria for connections
                    if similarity > threshold and (
                        tag_similarity > 0.1 or  # Must have some tag similarity
                        content_similarity > 0.15 or  # Or significant content similarity
                        tech_similarity > 0.3  # Or strong technical similarity
                    ):
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
            
            print(f"🔧 DEBUG: Created {len(edges)} connections with threshold {threshold}")
            
            return jsonify({
                'nodes': nodes,
                'edges': edges,
                'user_specific': True,
                'total_memories': len(user_memories),
                'connections': len(edges)
            })
            
        except Exception as e:
            print(f"❌ Error in memory-network route: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'nodes': [], 'edges': [], 'error': str(e)}) 