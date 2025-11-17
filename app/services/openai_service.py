#!/usr/bin/env python3

import json
from config import config
from app.services.memory_search_service import memory_search_service
from app.services.subscription_service import get_subscription_service

class OpenAIService:
    """Service for OpenAI API interactions"""
    
    def __init__(self):
        self.client = config.openai_client
        
        # Define the tool for creating memories
        self.memory_tool = {
            "type": "function",
            "function": {
                "name": "create_memory",
                "description": "IMPORTANT: Use this tool EVERY TIME the user mentions ANY personal information, preferences, likes/dislikes, facts, experiences, or anything about themselves. Be very liberal with creating memories - it's better to create too many than too few. Always use first person format (starting with 'I'). Examples: 'I love pepperoni pizza', 'I work as a software engineer', 'I have a dog named Max', 'I hate broccoli', 'I went to Paris', 'I want to learn Spanish'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The memory content in first person format. Must start with 'I'. Be specific and include details. Example: 'I love pepperoni pizza' NOT just 'I like pizza'"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags to categorize the memory. Use relevant tags like ['preference', 'food'], ['personal', 'work'], ['family', 'pet'], ['hobby'], ['goal'], etc."
                        }
                    },
                    "required": ["content"]
                }
            }
        }
    
    def _create_memory_for_user(self, user_id, content, tags=None):
        """Create a memory for the user using the appropriate memory manager"""
        if not user_id or user_id == 'anonymous':
            print("[ERROR] Authentication required - cannot create memories without valid user")
            return {"success": False, "error": "Authentication required to create memories"}
        
        # Clean up content
        content = content.strip()
        if not content:
            return {"success": False, "error": "Memory content cannot be empty"}
        
        # Ensure content starts with "I" for first person
        if not content.lower().startswith('i '):
            content = f"I {content.lower()}"
        
        tags = tags or ["conversation"]
        
        # Try Clerk auth system first
        try:
            from app.core.clerk_auth_system import clerk_user_memory_manager
            if clerk_user_memory_manager:
                result = clerk_user_memory_manager.add_memory_for_user(user_id, content, tags)
                if result.get('success'):
                    print(f"[OK] Created memory via Clerk: {content}")
                    # Add to session queue for real-time updates
                    self._add_to_session_queue(result.get('memory'))
                    return result
        except Exception as e:
            print(f"[DEBUG] Clerk memory creation failed, trying legacy: {e}")
        
        # Fallback to legacy auth system
        try:
            from app.core.auth_system import user_memory_manager
            if user_memory_manager:
                result = user_memory_manager.add_memory_for_user(user_id, content, tags)
                if result.get('success'):
                    print(f"[OK] Created memory via legacy: {content}")
                    # Add to session queue for real-time updates
                    self._add_to_session_queue(result.get('memory'))
                    return result
        except Exception as e:
            print(f"[ERROR] Legacy memory creation failed: {e}")
        
        return {"success": False, "error": "Failed to create memory"}
    
    def _add_to_session_queue(self, memory):
        """Add a newly created memory to the session queue for real-time updates"""
        if not memory:
            return
        
        try:
            memory_data = {
                'id': memory.get('id'),
                'content': memory.get('content'),
                'score': memory.get('score', 0),
                'tags': memory.get('tags', []),
                'created': memory.get('created_at', '')
            }
            
            with config.session_new_memories_lock:
                config.session_new_memories.append(memory_data)
                print(f"[OK] Added memory to session queue: {memory_data['content'][:50]}...")
                print(f"[DEBUG] Session queue now contains {len(config.session_new_memories)} memories")
        except Exception as e:
            print(f"[ERROR] Failed to add memory to session queue: {e}")
    
    def generate_response_with_memory(self, message, conversation_history, user_id=None):
        """Generate AI response using OpenAI API with tool calling for memory creation"""
        # Check if OpenAI client is available
        if not self.client:
            error_msg = "⚠️ OpenAI API is not configured. Please add your OPENAI_API_KEY to the .env file."
            print(f"[ERROR] {error_msg}")
            return error_msg, []
        
        # Check user's subscription and usage limits
        if user_id and user_id != 'anonymous':
            try:
                usage_check = get_subscription_service().can_user_chat(user_id)
                if not usage_check['can_chat']:
                    return f"I apologize, but you've reached your monthly message limit ({usage_check['messages_limit']} messages). Please upgrade to Premium for unlimited messages.", []
            except Exception as e:
                print(f"[WARN] Subscription check failed: {e}")
        
        try:
            # Build system message with memory context
            system_content = """You are a helpful AI assistant with a powerful memory system. You MUST actively create memories whenever users share personal information.

⚠️ IMPORTANT: You should use the create_memory tool FREQUENTLY. Whenever a user mentions ANYTHING about themselves, you should create a memory. Be proactive and liberal with memory creation.

Create memories for:
- Personal preferences (food, hobbies, interests) - e.g., "I love pepperoni" → create memory
- Facts about the user (job, location, family, pets) - e.g., "I work as a teacher" → create memory
- Opinions and feelings they express - e.g., "I think cats are better than dogs" → create memory
- Goals or plans they mention - e.g., "I want to learn Spanish" → create memory
- Important experiences they share - e.g., "I went to Paris last year" → create memory
- Any likes or dislikes - e.g., "I hate broccoli" → create memory
- Skills or abilities - e.g., "I can play guitar" → create memory

ALWAYS create memories in first person format (starting with "I").

When you create a memory, acknowledge it naturally in your response (e.g., "I'll remember that you love pepperoni!").

Use existing memories to personalize your responses when relevant."""

            messages = [
                {"role": "system", "content": system_content}
            ]
            
            memory_context = []
            
            # Search for relevant user-specific memories
            if user_id and user_id != 'anonymous':
                # Try Clerk auth system first
                try:
                    from app.core.clerk_auth_system import clerk_user_memory_manager
                    if clerk_user_memory_manager:
                        user_memories = clerk_user_memory_manager.search_user_memories(user_id, message, 5)
                        if user_memories:
                            memory_context = user_memories
                except Exception as e:
                    print(f"[DEBUG] Clerk memory search failed, trying legacy: {e}")
                    # Fallback to legacy auth system
                    try:
                        from app.core.auth_system import user_memory_manager
                        if user_memory_manager:
                            user_memories = user_memory_manager.search_user_memories(user_id, message, 5)
                            if user_memories:
                                memory_context = user_memories
                    except Exception as e2:
                        print(f"[DEBUG] Legacy memory search failed: {e2}")
                
                # Format user memories for injection
                if memory_context:
                    memory_text = "\n\nUSER MEMORIES (for context):\n"
                    for memory in memory_context:
                        memory_text += f"- {memory['content']}\n"
                    memory_text += "\nReference these memories to personalize your response when relevant."
                    messages[0]["content"] += memory_text
            else:
                # Fallback to global memory search for anonymous users
                try:
                    memory_context = memory_search_service.search_memories_with_strict_filtering(message)
                    
                    # Inject memories into system prompt if found
                    if memory_context:
                        memory_text = memory_search_service.format_memories_for_injection(memory_context)
                        messages[0]["content"] += memory_text
                except Exception as e:
                    print(f"[DEBUG] Global memory search failed: {e}")
            
            # Add conversation history (excluding the current message to avoid duplication)
            for msg in conversation_history[:-1]:  # Exclude the last message (current user message)
                role = "user" if msg['sender'] == 'user' else "assistant"
                messages.append({"role": role, "content": msg['content']})
            
            # Add the current user message
            messages.append({"role": "user", "content": message})
            
            # Get AI model based on user's subscription
            # Using gpt-4o-mini as default - it's better at tool calling than gpt-3.5-turbo
            ai_model = "gpt-4o-mini"  # Default for all users - excellent tool calling support
            if user_id and user_id != 'anonymous':
                try:
                    subscription_model = get_subscription_service().get_ai_model_for_user(user_id)
                    if subscription_model:
                        ai_model = subscription_model
                except Exception as e:
                    print(f"[WARN] Could not get AI model from subscription: {e}, using default: {ai_model}")
            
            print(f"[INFO] Using OpenAI model: {ai_model}")
            print(f"[DEBUG] USER_ID for tool calling: '{user_id}'")
            print(f"[DEBUG] User message: '{message[:100]}...'")
            
            # Require authentication - no anonymous mode
            if not user_id or user_id == 'anonymous':
                print(f"[ERROR] ❌ AUTHENTICATION REQUIRED - user_id is: '{user_id}'")
                print(f"[ERROR] Cannot proceed without valid authentication")
                return "⚠️ Your session has expired. Please refresh the page to continue.", [], []
            
            # Enable tool calling for authenticated users
            tools = [self.memory_tool]
            print(f"[INFO] ✅ Tool calling ENABLED for user: {user_id}")
            print(f"[INFO] 🧠 Memory creation tool is available - AI can create memories")
            
            # Generate response with tool calling
            response = self.client.chat.completions.create(
                model=ai_model,
                messages=messages,
                tools=tools,
                tool_choice="auto" if tools else None,
                max_tokens=500,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Track newly created memories for this request
            created_memories = []
            
            # Log whether AI decided to use tools or not
            if tool_calls:
                print(f"[INFO] ✅ AI MADE {len(tool_calls)} TOOL CALL(S) - Creating memories!")
            else:
                print(f"[WARN] ⚠️ AI DID NOT CALL ANY TOOLS - No memories will be created")
                print(f"[DEBUG] This might be because:")
                print(f"[DEBUG]   - The message didn't contain personal information")
                print(f"[DEBUG]   - The AI didn't recognize it as memory-worthy")
                print(f"[DEBUG]   - User message was: '{message[:150]}...'")
            
            # Handle tool calls if present
            if tool_calls:
                
                # Add assistant's response with tool calls to messages
                messages.append(response_message)
                
                # Process each tool call
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"[INFO] Tool call: {function_name} with args: {function_args}")
                    
                    if function_name == "create_memory":
                        # Create the memory
                        result = self._create_memory_for_user(
                            user_id,
                            function_args.get("content"),
                            function_args.get("tags")
                        )
                        
                        # Track the newly created memory
                        if result.get('success') and result.get('memory'):
                            created_memories.append({
                                'id': result['memory'].get('id'),
                                'content': result['memory'].get('content'),
                                'tags': result['memory'].get('tags', [])
                            })
                        
                        # Add tool response to messages
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        }
                        messages.append(tool_message)
                
                # Get final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=ai_model,
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                
                final_content = final_response.choices[0].message.content.strip()
                print(f"[OK] Final response generated after tool calls")
            else:
                # No tool calls, use the original response
                final_content = response_message.content.strip()
                print(f"[OK] Response generated without tool calls")
            
            # Track usage for the user
            if user_id and user_id != 'anonymous':
                try:
                    get_subscription_service().track_usage(user_id, messages_increment=1, api_calls_increment=1)
                except Exception as e:
                    print(f"[WARN] Could not track usage: {e}")
            
            # Return response with memory context and created memories
            return final_content, memory_context, created_memories
            
        except Exception as e:
            error_type = type(e).__name__
            print(f"[ERROR] OpenAI API Error ({error_type}): {e}")
            
            # More helpful error messages
            if "api_key" in str(e).lower() or "authentication" in str(e).lower():
                return "⚠️ OpenAI API authentication failed. Please check your OPENAI_API_KEY in the .env file.", [], []
            elif "quota" in str(e).lower() or "insufficient" in str(e).lower():
                return "⚠️ OpenAI API quota exceeded. Please check your OpenAI account billing.", [], []
            elif "rate_limit" in str(e).lower():
                return "⚠️ OpenAI API rate limit reached. Please wait a moment and try again.", [], []
            else:
                return f"⚠️ An error occurred: {str(e)}. Please try again.", [], []
    
    def extract_memories_from_conversation(self, conversation):
        """Extract up to 5 meaningful memories from a conversation using OpenAI"""
        print(f"[DEBUG] extract_memories_from_conversation called with {len(conversation) if conversation else 0} messages")
        
        # Check if OpenAI client is available
        if not self.client:
            print("[DEBUG] OpenAI client not available, cannot extract memories")
            return []
        
        if not conversation or len(conversation) < 2:
            print("[DEBUG] Conversation too short, returning empty list")
            return []
        
        # Build conversation text
        conversation_text = ""
        for msg in conversation:
            role = "User" if msg['sender'] == 'user' else "Assistant"
            conversation_text += f"{role}: {msg['content']}\n"
        
        print(f"[DEBUG] Built conversation text, length: {len(conversation_text)}")
        
        # Use OpenAI to extract memories
        try:
            extraction_prompt = f"""Analyze this conversation and extract up to 5 meaningful personal facts, preferences, or information about the user that should be remembered for future conversations.

Focus on:
- Personal preferences (food, hobbies, interests)
- Facts about the user (job, location, family, etc.)
- Opinions and feelings they expressed
- Goals or plans they mentioned
- Important experiences they shared

Return ONLY the extracted memories, one per line, in first person format (starting with "I").
If no meaningful personal information is found, return "NONE".

Conversation:
{conversation_text}

Extracted memories:"""

            print("🔧 DEBUG: Calling OpenAI API for memory extraction...")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=300,
                temperature=0.3,
                timeout=30  # Add timeout to prevent hanging
            )
            
            result = response.choices[0].message.content.strip()
            print(f"🔧 DEBUG: OpenAI response: {result}")
            
            if result == "NONE" or not result:
                print("🔧 DEBUG: No memories extracted (NONE or empty result)")
                return []
            
            # Parse the memories
            memories = []
            for line in result.split('\n'):
                line = line.strip()
                if line and not line.startswith('-') and len(line) > 10:
                    # Clean up the memory text
                    if line.startswith('- '):
                        line = line[2:]
                    if not line.lower().startswith('i '):
                        line = f"I {line.lower()}"
                    memories.append(line)
                    print(f"[DEBUG] Parsed memory: {line}")
            
            print(f"[DEBUG] Extracted {len(memories)} memories total")
            return memories[:5]  # Limit to 5 memories
            
        except Exception as e:
            print(f"[ERROR] Error extracting memories: {e}")
            print(f"[DEBUG] Exception type: {type(e).__name__}")
            return []

# Global service instance
openai_service = OpenAIService() 