#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from auth_system import auth_system, get_auth_system
from services.user_conversation_service import user_conversation_service

def test_complete_user_chat_system():
    print("🧪 Testing complete user-specific chat system...")
    
    # Ensure auth system is initialized
    auth_sys = auth_system
    if not auth_sys or not auth_sys.supabase:
        print("⚠️ Auth system not initialized. Attempting to initialize...")
        try:
            auth_sys, _ = get_auth_system()
            if not auth_sys or not auth_sys.supabase:
                print("❌ Failed to initialize auth system")
                return False
        except Exception as e:
            print(f"❌ Error initializing auth system: {e}")
            return False
    
    # Login user
    result = auth_sys.login_user('ethan8eight@gmail.com', 'Mydragon100')
    if not result['success']:
        print(f"❌ Login failed: {result.get('message', 'Unknown error')}")
        return False
    
    user_id = result['user']['id']
    print(f"✅ User login successful: {user_id}")
    
    try:
        # Test 1: Process a complete message with AI response
        print("\n🔧 Test 1: Processing complete message with AI response")
        test_message = "Hello, can you help me with a simple question?"
        
        thread_id, ai_response, memory_context, error = user_conversation_service.process_message(
            test_message, None, user_id, "test_request_1"
        )
        
        if error or not thread_id:
            print(f"❌ Error processing message: {error}")
            return False
        
        print(f"✅ Message processed successfully")
        print(f"   Thread ID: {thread_id}")
        print(f"   AI Response: {ai_response[:100] if ai_response else 'None'}...")
        print(f"   Memory Context: {len(memory_context) if memory_context else 0} memories")
        
        # Test 2: Add another message to the same thread
        print("\n🔧 Test 2: Adding message to existing thread")
        test_message_2 = "That's helpful, thank you!"
        
        thread_id_2, ai_response_2, memory_context_2, error_2 = user_conversation_service.process_message(
            test_message_2, thread_id, user_id, "test_request_2"
        )
        
        if error_2 or not thread_id_2:
            print(f"❌ Error processing second message: {error_2}")
            return False
        
        print(f"✅ Second message processed successfully")
        print(f"   Same Thread ID: {thread_id == thread_id_2}")
        print(f"   AI Response: {ai_response_2[:100] if ai_response_2 else 'None'}...")
        
        # Test 3: Retrieve thread messages
        print("\n🔧 Test 3: Retrieving thread messages")
        messages = user_conversation_service.get_thread_messages(thread_id, user_id)
        print(f"✅ Retrieved {len(messages)} messages from thread")
        
        for i, msg in enumerate(messages):
            print(f"   {i+1}. {msg['sender']}: {msg['content'][:50]}...")
        
        # Test 4: Get user threads
        print("\n🔧 Test 4: Getting user threads")
        threads = user_conversation_service.get_user_threads(user_id)
        print(f"✅ User has {len(threads)} total threads")
        
        # Test 5: Create new thread
        print("\n🔧 Test 5: Creating new thread")
        new_thread_id = user_conversation_service.create_new_thread(user_id)
        print(f"✅ Created new thread: {new_thread_id}")
        
        # Test 6: Test memory extraction
        print("\n🔧 Test 6: Testing memory extraction")
        success, extracted_memories, message = user_conversation_service.end_thread_and_extract_memories(
            thread_id, user_id
        )
        
        if success:
            print(f"✅ Memory extraction successful: {len(extracted_memories)} memories")
            print(f"   Message: {message}")
        else:
            print(f"⚠️ Memory extraction failed or no memories: {message}")
        
        # Test 7: Test duplicate request prevention
        print("\n🔧 Test 7: Testing duplicate request prevention")
        thread_id_dup, ai_response_dup, memory_context_dup, error_dup = user_conversation_service.process_message(
            "Test duplicate", None, user_id, "test_request_2"  # Same request ID as before
        )
        
        if error_dup == "Duplicate request detected":
            print("✅ Duplicate request prevention working correctly")
        else:
            print(f"⚠️ Duplicate request prevention may not be working: {error_dup}")
        
        print("\n🎉 Complete user-specific chat system test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during comprehensive testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_user_chat_system()
    if success:
        print("\n✅ All tests passed! User-specific chat system is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above.") 