#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

import datetime
import uuid
import time
import json
from typing import Dict, List, Optional, Tuple
from auth_system import auth_system, user_memory_manager, get_auth_system
from services.openai_service import openai_service

class UserConversationService:
    """Service for managing user-specific conversations and threads in Supabase"""
    
    def __init__(self):
        # Ensure auth system is initialized
        if not auth_system or not auth_system.supabase:
            print("⚠️ Auth system not initialized. Attempting to initialize...")
            try:
                auth_sys, _ = get_auth_system()
                if not auth_sys or not auth_sys.supabase:
                    print("❌ Failed to initialize auth system")
                    raise Exception("Auth system initialization failed")
                self.supabase = auth_sys.supabase
            except Exception as e:
                print(f"❌ Error initializing auth system: {e}")
                raise
        else:
            self.supabase = auth_system.supabase
        
        # Track processed request IDs to prevent duplicates
        self.processed_requests = set()
        self.last_cleanup = time.time()
    
    def cleanup_old_requests(self):
        """Clean up old request IDs every 5 minutes"""
        current_time = time.time()
        if current_time - self.last_cleanup > 300:  # 5 minutes
            self.processed_requests.clear()
            self.last_cleanup = current_time
            print("🧹 Cleaned up old request IDs")
    
    def is_duplicate_request(self, request_id):
        """Check if this is a duplicate request"""
        if not request_id:
            return False
        
        if request_id in self.processed_requests:
            print(f"⚠️ Duplicate request detected: {request_id}")
            return True
        
        self.processed_requests.add(request_id)
        print(f"✅ Processing request: {request_id}")
        return False
    
    def create_or_get_thread(self, user_id: str, thread_id: Optional[str] = None) -> str:
        """Create a new thread or get existing one for a user"""
        if not thread_id:
            thread_id = str(uuid.uuid4())
            
            # Create thread in database
            thread_data = {
                'user_id': user_id,
                'thread_id': thread_id,
                'title': f'Conversation {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}',
                'created_at': datetime.datetime.utcnow().isoformat(),
                'updated_at': datetime.datetime.utcnow().isoformat(),
                'is_active': True
            }
            
            try:
                # Try to use Supabase if available
                if hasattr(self, 'supabase') and self.supabase:
                    result = self.supabase.table('user_chat_threads').insert(thread_data).execute()
                    print(f"✅ Created new thread: {thread_id} for user: {user_id}")
                else:
                    print(f"⚠️ Supabase not available, using fallback thread: {thread_id}")
            except Exception as e:
                print(f"❌ Error creating thread: {e}")
                print(f"⚠️ Using fallback thread: {thread_id}")
        else:
            # Check if thread exists and belongs to user
            try:
                if hasattr(self, 'supabase') and self.supabase:
                    result = self.supabase.table('user_chat_threads').select('*').eq('thread_id', thread_id).eq('user_id', user_id).execute()
                    if not result.data:
                        print(f"⚠️ Thread {thread_id} not found for user {user_id}, creating new one")
                        return self.create_or_get_thread(user_id, None)
                else:
                    print(f"⚠️ Supabase not available, using existing thread: {thread_id}")
            except Exception as e:
                print(f"❌ Error checking thread: {e}")
                print(f"⚠️ Using existing thread: {thread_id}")
        
        return thread_id
    
    def create_new_thread(self, user_id: str) -> str:
        """Create a new empty thread for a user"""
        return self.create_or_get_thread(user_id, None)
    
    def add_message_to_thread(self, thread_id: str, user_id: str, content: str, sender: str, memory_context: Optional[List] = None) -> Optional[Dict]:
        """Add a message to a thread"""
        message_id = str(uuid.uuid4())
        timestamp = datetime.datetime.utcnow().isoformat()
        
        message_data = {
            'thread_id': thread_id,
            'user_id': user_id,
            'message_id': message_id,
            'content': content,
            'sender': sender,
            'timestamp': timestamp,
            'memory_context': json.dumps(memory_context) if memory_context else None,
            'created_at': timestamp
        }
        
        try:
            # Try to use Supabase if available
            if hasattr(self, 'supabase') and self.supabase:
                result = self.supabase.table('user_chat_messages').insert(message_data).execute()
                
                if result.data:
                    print(f"✅ Added {sender} message to thread {thread_id}")
                    return {
                        'id': message_id,
                        'content': content,
                        'sender': sender,
                        'timestamp': timestamp,
                        'memory_context': memory_context
                    }
                else:
                    print(f"❌ Failed to add message to database")
                    return None
            else:
                # Fallback: just return the message data without saving to database
                print(f"⚠️ Supabase not available, using fallback for {sender} message")
                return {
                    'id': message_id,
                    'content': content,
                    'sender': sender,
                    'timestamp': timestamp,
                    'memory_context': memory_context
                }
                
        except Exception as e:
            print(f"❌ Error adding message: {e}")
            # Fallback: return message data anyway
            print(f"⚠️ Using fallback for {sender} message due to error")
            return {
                'id': message_id,
                'content': content,
                'sender': sender,
                'timestamp': timestamp,
                'memory_context': memory_context
            }
    
    def get_thread_messages(self, thread_id: str, user_id: str) -> List[Dict]:
        """Get all messages from a thread for a specific user"""
        try:
            result = self.supabase.table('user_chat_messages').select('*').eq('thread_id', thread_id).eq('user_id', user_id).order('timestamp', desc=False).execute()
            
            if result.data:
                messages = []
                for msg in result.data:
                    # Parse memory_context if it exists
                    memory_context = None
                    if msg.get('memory_context'):
                        try:
                            memory_context = json.loads(msg['memory_context'])
                        except:
                            pass
                    
                    messages.append({
                        'id': msg['message_id'],
                        'content': msg['content'],
                        'sender': msg['sender'],
                        'timestamp': msg['timestamp'],
                        'memory_context': memory_context
                    })
                
                return messages
            else:
                return []
                
        except Exception as e:
            print(f"❌ Error getting thread messages: {e}")
            return []
    
    def get_user_threads(self, user_id: str) -> List[str]:
        """Get all thread IDs for a user"""
        try:
            result = self.supabase.table('user_chat_threads').select('thread_id').eq('user_id', user_id).eq('is_active', True).order('updated_at', desc=True).execute()
            
            if result.data:
                return [thread['thread_id'] for thread in result.data]
            else:
                return []
                
        except Exception as e:
            print(f"❌ Error getting user threads: {e}")
            return []
    
    def process_message(self, message: str, thread_id: Optional[str], user_id: str, request_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[List], Optional[str]]:
        """Process a user message and generate AI response"""
        # Clean up old requests
        self.cleanup_old_requests()
        
        # Check for duplicate request
        if self.is_duplicate_request(request_id):
            return None, None, None, "Duplicate request detected"
        
        if not message.strip():
            return None, None, None, "Message cannot be empty"
        
        # Create or get thread
        thread_id = self.create_or_get_thread(user_id, thread_id)
        
        # Add user message to thread
        user_message = self.add_message_to_thread(thread_id, user_id, message, 'user')
        if not user_message:
            return None, None, None, "Failed to save user message"
        
        # Get conversation history for context
        conversation_history = self.get_thread_messages(thread_id, user_id)
        
        # Generate AI response using OpenAI API with user-specific memory context
        ai_response, memory_context = openai_service.generate_response_with_memory(
            message, 
            conversation_history,
            user_id
        )
        
        # Add AI response to thread
        ai_message = self.add_message_to_thread(thread_id, user_id, ai_response, 'assistant', memory_context)
        if not ai_message:
            return thread_id, ai_response, memory_context, "AI response generated but failed to save"
        
        return thread_id, ai_response, memory_context, None
    
    def end_thread_and_extract_memories(self, thread_id: str, user_id: str) -> Tuple[bool, List[str], str]:
        """Extract memories from a conversation thread when it ends"""
        print(f"🔧 DEBUG: end_thread_and_extract_memories called for thread: {thread_id}, user: {user_id}")
        
        if not thread_id or not user_id:
            return False, [], "Thread ID and User ID are required"
        
        # Get conversation messages
        conversation = self.get_thread_messages(thread_id, user_id)
        print(f"🔧 DEBUG: Found conversation with {len(conversation)} messages")
        
        if len(conversation) < 2:
            return False, [], "Conversation too short to extract memories"
        
        # Extract memories with error handling
        try:
            print("🔧 DEBUG: Calling extract_memories_from_conversation...")
            extracted_memories = openai_service.extract_memories_from_conversation(conversation)
            print(f"🔧 DEBUG: Memory extraction completed, got {len(extracted_memories)} memories")
        except Exception as e:
            print(f"❌ Error during memory extraction: {e}")
            extracted_memories = []
        
        # Add extracted memories to user's personal database
        successful_adds = 0
        if extracted_memories:
            print(f"💾 Extracting {len(extracted_memories)} memories for user {user_id}...")
            
            for memory_text in extracted_memories:
                try:
                    print(f"🔧 DEBUG: Adding user memory: {memory_text[:50]}...")
                    result = user_memory_manager.add_memory_for_user(user_id, memory_text, ["conversation", "auto-extracted"])
                    if result['success']:
                        print(f"   ✅ Added to user database: {memory_text}")
                        successful_adds += 1
                    else:
                        print(f"   ❌ Failed to add to user database: {memory_text} - {result.get('error')}")
                except Exception as e:
                    print(f"   ❌ Exception adding user memory: {memory_text} - {e}")
        
        # Keep the thread active - don't delete it
        print(f"🔧 DEBUG: Thread {thread_id} preserved for continued conversation")
        
        return True, extracted_memories, f'Successfully extracted and saved {successful_adds} memories to your personal database!'
    
    def clear_thread(self, thread_id: str, user_id: str) -> bool:
        """Mark a thread as inactive (soft delete)"""
        try:
            result = self.supabase.table('user_chat_threads').update({'is_active': False}).eq('thread_id', thread_id).eq('user_id', user_id).execute()
            
            if result.data:
                print(f"✅ Thread {thread_id} marked as inactive for user {user_id}")
                return True
            else:
                print(f"❌ Failed to deactivate thread {thread_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error deactivating thread: {e}")
            return False

# Create global instance with proper initialization
try:
    user_conversation_service = UserConversationService()
    print("✅ UserConversationService initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize UserConversationService: {e}")
    user_conversation_service = None 