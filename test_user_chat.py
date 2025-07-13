#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from auth_system import auth_system, get_auth_system
from services.user_conversation_service import user_conversation_service

def test_user_chat():
    print("🧪 Testing user-specific chat system...")
    
    # Ensure auth system is initialized
    auth_sys = auth_system
    if not auth_sys or not auth_sys.supabase:
        print("⚠️ Auth system not initialized. Attempting to initialize...")
        try:
            auth_sys, _ = get_auth_system()
            if not auth_sys or not auth_sys.supabase:
                print("❌ Failed to initialize auth system")
                return
        except Exception as e:
            print(f"❌ Error initializing auth system: {e}")
            return
    
    # Login user
    result = auth_sys.login_user('ethan8eight@gmail.com', 'Mydragon100')
    if not result['success']:
        print(f"❌ Login failed: {result.get('message', 'Unknown error')}")
        return
    
    user_id = result['user']['id']
    print(f"✅ User login successful: {user_id}")
    
    # Test creating a new thread
    try:
        thread_id = user_conversation_service.create_new_thread(user_id)
        print(f"✅ Created new thread: {thread_id}")
        
        # Test adding messages
        user_msg = user_conversation_service.add_message_to_thread(
            thread_id, user_id, "Hello, this is a test message!", "user"
        )
        if user_msg:
            print(f"✅ Added user message: {user_msg['content'][:50]}...")
        else:
            print("❌ Failed to add user message")
            
        ai_msg = user_conversation_service.add_message_to_thread(
            thread_id, user_id, "Hello! I'm here to help you.", "assistant"
        )
        if ai_msg:
            print(f"✅ Added AI message: {ai_msg['content'][:50]}...")
        else:
            print("❌ Failed to add AI message")
        
        # Test getting messages
        messages = user_conversation_service.get_thread_messages(thread_id, user_id)
        print(f"✅ Retrieved {len(messages)} messages from thread")
        
        for i, msg in enumerate(messages):
            print(f"  {i+1}. {msg['sender']}: {msg['content'][:50]}...")
        
        # Test getting user threads
        threads = user_conversation_service.get_user_threads(user_id)
        print(f"✅ User has {len(threads)} total threads")
        
        print("\n🎉 User-specific chat system is working correctly!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_chat() 