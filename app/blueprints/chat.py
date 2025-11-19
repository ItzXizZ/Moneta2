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


@chat_bp.route('/anonymous/send', methods=['POST'])
def anonymous_send():
    """Handle anonymous chat messages with memory creation - no authentication required"""
    try:
        from app.services.openai_service import openai_service

        data = request.get_json()
        message = data.get('message', '').strip()
        conversation_history = data.get('history', [])
        existing_memories = data.get('memories', [])  # Existing localStorage memories

        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400

        # Build conversation context with system message for memory creation
        system_content = """You are a helpful AI assistant with a powerful memory system. You MUST actively create memories whenever users share personal information.

⚠️ IMPORTANT: You should use the create_memory tool FREQUENTLY. Whenever a user mentions ANYTHING about themselves, you should create a memory. Be proactive and liberal with memory creation.

Create memories for:
- Personal preferences (food, hobbies, interests) - e.g., user says "I love pepperoni" → create memory "User loves pepperoni"
- Facts about the user (job, location, family, pets) - e.g., user says "I work as a teacher" → create memory "User works as a teacher"
- Opinions and feelings they express - e.g., user says "I think cats are better than dogs" → create memory "User thinks cats are better than dogs"
- Goals or plans they mention - e.g., user says "I want to learn Spanish" → create memory "User wants to learn Spanish"
- Important experiences they share - e.g., user says "I went to Paris last year" → create memory "User went to Paris last year"
- Any likes or dislikes - e.g., user says "I hate broccoli" → create memory "User hates broccoli"
- Skills or abilities - e.g., user says "I can play guitar" → create memory "User can play guitar"

ALWAYS create memories in third person format about the user (starting with "User").

When you create a memory, acknowledge it naturally in your response (e.g., "I'll remember that you love pepperoni!")."""

        messages = [{"role": "system", "content": system_content}]
        
        # Add existing memories to context
        if existing_memories:
            memory_text = "\n\nUSER MEMORIES (for context):\n"
            for mem in existing_memories[-10:]:  # Last 10 memories
                memory_text += f"- {mem.get('content', '')}\n"
            memory_text += "\nReference these memories to personalize your response when relevant."
            messages[0]["content"] += memory_text

        # Add conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            role = "user" if msg.get('isUser') else "assistant"
            messages.append({"role": role, "content": msg.get('content', '')})

        # Add current message
        messages.append({"role": "user", "content": message})

        # Get AI response with tool calling for memory creation
        try:
            import json
            from openai import OpenAI
            
            # Define the memory creation tool
            tools = [{
                "type": "function",
                "function": {
                    "name": "create_memory",
                    "description": "Create a new memory about the user. Use this VERY FREQUENTLY whenever the user shares ANY personal information, preferences, facts, opinions, goals, or experiences.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The memory content in third person format about the user (e.g., 'User loves pizza', 'User works as a teacher')"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tags to categorize the memory (e.g., ['food', 'preferences'], ['work', 'career'])"
                            }
                        },
                        "required": ["content", "tags"]
                    }
                }
            }]
            
            client = openai_service.client
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=500,
                temperature=0.7
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Process tool calls to create memories
            created_memories = []
            if tool_calls:
                print(f"[Anonymous Chat] AI made {len(tool_calls)} tool call(s)")
                for tool_call in tool_calls:
                    if tool_call.function.name == "create_memory":
                        function_args = json.loads(tool_call.function.arguments)
                        memory = {
                            'id': str(__import__('uuid').uuid4()),
                            'content': function_args.get('content', ''),
                            'tags': function_args.get('tags', []),
                            'score': 1.0,
                            'created': __import__('datetime').datetime.now().strftime('%Y-%m-%d')
                        }
                        created_memories.append(memory)
                        print(f"[Anonymous Chat] Created memory: {memory['content'][:50]}...")
                
                # Get final response by continuing the conversation with tool results
                messages.append(response_message)
                for tool_call in tool_calls:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"success": True})
                    })
                
                # Get final response
                final_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                ai_response = final_response.choices[0].message.content
            else:
                ai_response = response_message.content
                print(f"[Anonymous Chat] No tool calls made")

            return jsonify({
                'success': True,
                'response': ai_response,
                'memories': created_memories  # Return created memories to frontend
            })
        except Exception as ai_error:
            print(f"[Anonymous Chat] OpenAI Error: {ai_error}")
            return jsonify({
                'success': False,
                'error': f'AI service error: {str(ai_error)}'
            }), 500

    except Exception as e:
        print(f"[Anonymous Chat] Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


