#!/usr/bin/env python3

import datetime
import uuid
import time
import requests
import os
import json
from config import config
from services.openai_service import openai_service

class ConversationService:
    """Service for managing conversations and threads"""
    
    CHAT_HISTORY_FILE = os.path.join(os.path.dirname(__file__), '../chat_history.json')
    
    def __init__(self):
        # In-memory storage for chat threads and messages
        self.chat_threads = {}
        
        # Track processed request IDs to prevent duplicates
        self.processed_requests = set()
        self.last_cleanup = time.time()
        self.load_history_from_disk()
    
    def save_history_to_disk(self):
        try:
            with open(self.CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.chat_threads, f, indent=2)
        except Exception as e:
            print(f'[WARN] Failed to save chat history: {e}')

    def load_history_from_disk(self):
        try:
            if os.path.exists(self.CHAT_HISTORY_FILE):
                with open(self.CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.chat_threads = json.load(f)
        except Exception as e:
            print(f'[WARN] Failed to load chat history: {e}')
    
    def cleanup_old_requests(self):
        """Clean up old request IDs every 5 minutes"""
        current_time = time.time()
        if current_time - self.last_cleanup > 300:  # 5 minutes
            self.processed_requests.clear()
            self.last_cleanup = current_time
            print("[INFO] Cleaned up old request IDs")
    
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
    
    def create_or_get_thread(self, thread_id=None):
        """Create a new thread or get existing one"""
        if not thread_id:
            thread_id = str(uuid.uuid4())
            self.chat_threads[thread_id] = []
        
        if thread_id not in self.chat_threads:
            self.chat_threads[thread_id] = []
        
        return thread_id
    
    def create_new_thread(self):
        """Create a new empty thread and return its ID"""
        thread_id = str(uuid.uuid4())
        self.chat_threads[thread_id] = []
        self.save_history_to_disk()
        return thread_id
    
    def add_message_to_thread(self, thread_id, content, sender):
        """Add a message to a thread"""
        timestamp = datetime.datetime.now().isoformat()
        message = {
            'id': str(uuid.uuid4()),
            'content': content,
            'sender': sender,
            'timestamp': timestamp
        }
        
        if thread_id not in self.chat_threads:
            self.chat_threads[thread_id] = []
        
        self.chat_threads[thread_id].append(message)
        self.save_history_to_disk()
        return message
    
    def get_thread_messages(self, thread_id):
        """Get all messages from a thread"""
        return self.chat_threads.get(thread_id, [])
    
    def process_message(self, message, thread_id, request_id=None, user_id=None):
        """Process a user message and generate AI response"""
        # Clean up old requests
        self.cleanup_old_requests()
        
        # Check for duplicate request
        if self.is_duplicate_request(request_id):
            return None, None, None, "Duplicate request detected"
        
        if not message.strip():
            return None, None, None, "Message cannot be empty"
        
        # Create or get thread
        thread_id = self.create_or_get_thread(thread_id)
        
        # Add user message to thread
        user_message = self.add_message_to_thread(thread_id, message, 'user')
        
        # Generate AI response using OpenAI API with user-specific memory context
        ai_response, memory_context, created_memories = openai_service.generate_response_with_memory(
            message, 
            self.chat_threads[thread_id],
            user_id
        )
        
        # Add AI response to thread
        ai_message = self.add_message_to_thread(thread_id, ai_response, 'assistant')
        
        # Log created memories for debugging
        if created_memories:
            print(f"[INFO] Created {len(created_memories)} new memories during chat:")
            for mem in created_memories:
                print(f"   - {mem.get('content', '')[:50]}...")
        
        return thread_id, ai_response, memory_context, None
    
    def end_thread_and_extract_memories(self, thread_id, user_id=None):
        """Extract memories from a conversation thread when it ends"""
        print(f"🔧 DEBUG: end_thread_and_extract_memories called for thread: {thread_id}")
        
        if not thread_id or thread_id not in self.chat_threads:
            print(f"🔧 DEBUG: Thread not found - thread_id: {thread_id}, exists: {thread_id in self.chat_threads if thread_id else False}")
            return False, [], "Thread not found"
        
        conversation = self.chat_threads[thread_id]
        print(f"🔧 DEBUG: Found conversation with {len(conversation)} messages")
        
        # Extract memories with error handling
        try:
            print("🔧 DEBUG: Calling extract_memories_from_conversation...")
            extracted_memories = openai_service.extract_memories_from_conversation(conversation, user_id)
            print(f"🔧 DEBUG: Memory extraction completed, got {len(extracted_memories)} memories")
        except Exception as e:
            print(f"❌ Error during memory extraction: {e}")
            print(f"🔧 DEBUG: Memory extraction exception: {type(e).__name__}: {e}")
            extracted_memories = []
        
        # Add extracted memories to user-specific database
        successful_adds = 0
        if extracted_memories and user_id:
            print(f"💾 Extracting {len(extracted_memories)} memories for user {user_id}...")
            
            # Add memories to user's personal database
            from auth_system import user_memory_manager
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
        elif not user_id:
            print("🔧 DEBUG: No user_id provided, cannot save user-specific memories")
        
        # DON'T clean up the thread - keep it active so user can continue chatting
        # if thread_id in self.chat_threads:
        #     del self.chat_threads[thread_id]
        print(f"🔧 DEBUG: Thread {thread_id} preserved for continued conversation")
        
        return True, extracted_memories, f'Successfully extracted and saved {len(extracted_memories)} memories!'
    
    def clear_thread(self, thread_id):
        """Clear a specific thread"""
        if thread_id in self.chat_threads:
            del self.chat_threads[thread_id]
            self.save_history_to_disk()
            return True
        return False

# Global service instance
conversation_service = ConversationService() 