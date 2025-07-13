#!/usr/bin/env python3

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from auth_system import auth_system, get_auth_system
from services.user_conversation_service import user_conversation_service

def test_database_setup():
    """Test database connection and table setup"""
    print("🔧 Testing database setup...")
    
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
    
    # Test database connection
    try:
        result = auth_sys.supabase.table('users').select('id').limit(1).execute()
        print("✅ Database connection successful")
        
        # Test chat tables exist
        result = auth_sys.supabase.table('user_chat_threads').select('id').limit(1).execute()
        result = auth_sys.supabase.table('user_chat_messages').select('id').limit(1).execute()
        print("✅ Chat tables exist and accessible")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_authentication():
    """Test user authentication system"""
    print("\n🔧 Testing user authentication...")
    
    auth_sys = auth_system
    if not auth_sys:
        auth_sys, _ = get_auth_system()
    
    try:
        # Test user login
        result = auth_sys.login_user('ethan8eight@gmail.com', 'Mydragon100')
        if not result['success']:
            print(f"❌ Login failed: {result.get('message', 'Unknown error')}")
            return False, None
        
        user_id = result['user']['id']
        print(f"✅ User authentication successful: {user_id}")
        return True, user_id
        
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False, None

def test_chat_functionality(user_id):
    """Test core chat functionality"""
    print("\n🔧 Testing chat functionality...")
    
    try:
        # Test 1: Create new thread
        thread_id = user_conversation_service.create_new_thread(user_id)
        if not thread_id:
            print("❌ Failed to create new thread")
            return False
        print(f"✅ Created new thread: {thread_id}")
        
        # Test 2: Process user message
        message = "This is a test message for the chat system"
        result = user_conversation_service.process_message(message, thread_id, user_id, f"test_{int(time.time())}")
        
        if result[3]:  # error field
            print(f"❌ Message processing failed: {result[3]}")
            return False
        
        print("✅ Message processed successfully")
        print(f"   AI Response: {result[1][:100] if result[1] else 'None'}...")
        
        # Test 3: Retrieve messages
        messages = user_conversation_service.get_thread_messages(thread_id, user_id)
        if len(messages) < 2:
            print("❌ Expected at least 2 messages (user + assistant)")
            return False
        
        print(f"✅ Retrieved {len(messages)} messages from thread")
        
        # Test 4: Get user threads
        threads = user_conversation_service.get_user_threads(user_id)
        if not threads:
            print("❌ No threads found for user")
            return False
        
        print(f"✅ User has {len(threads)} total threads")
        
        return True
        
    except Exception as e:
        print(f"❌ Chat functionality error: {e}")
        return False

def test_memory_system(user_id):
    """Test memory extraction and saving"""
    print("\n🔧 Testing memory system...")
    
    try:
        # Create a conversation for memory extraction
        thread_id = user_conversation_service.create_new_thread(user_id)
        
        # Add some messages to create a meaningful conversation
        messages = [
            "I love programming in Python",
            "My favorite hobby is reading science fiction books",
            "I'm particularly interested in artificial intelligence"
        ]
        
        for i, msg in enumerate(messages):
            result = user_conversation_service.process_message(msg, thread_id, user_id, f"memory_test_{i}")
            if result[3]:
                print(f"❌ Failed to process message {i+1}: {result[3]}")
                return False
        
        print("✅ Created conversation for memory extraction")
        
        # Extract memories
        success, extracted_memories, message = user_conversation_service.end_thread_and_extract_memories(thread_id, user_id)
        
        if not success:
            print(f"❌ Memory extraction failed: {message}")
            return False
        
        print(f"✅ Memory extraction successful: {len(extracted_memories)} memories")
        print(f"   Message: {message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory system error: {e}")
        return False

def test_duplicate_prevention():
    """Test duplicate request prevention"""
    print("\n🔧 Testing duplicate request prevention...")
    
    try:
        auth_sys = auth_system
        if not auth_sys:
            auth_sys, _ = get_auth_system()
        
        result = auth_sys.login_user('ethan8eight@gmail.com', 'Mydragon100')
        user_id = result['user']['id']
        
        # Test duplicate request
        request_id = f"duplicate_test_{int(time.time())}"
        
        # First request
        result1 = user_conversation_service.process_message("Test message", None, user_id, request_id)
        if result1[3]:
            print(f"❌ First request failed: {result1[3]}")
            return False
        
        # Second request with same ID (should be blocked)
        result2 = user_conversation_service.process_message("Test message", None, user_id, request_id)
        if result2[3] != "Duplicate request detected":
            print(f"❌ Duplicate request not detected: {result2[3]}")
            return False
        
        print("✅ Duplicate request prevention working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Duplicate prevention error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🧪 Running comprehensive user-specific chat system test...")
    print("=" * 60)
    
    # Test results
    results = {
        'database_setup': False,
        'user_authentication': False,
        'chat_functionality': False,
        'memory_system': False,
        'duplicate_prevention': False
    }
    
    # Run tests
    results['database_setup'] = test_database_setup()
    
    if results['database_setup']:
        success, user_id = test_user_authentication()
        results['user_authentication'] = success
        
        if success and user_id:
            results['chat_functionality'] = test_chat_functionality(user_id)
            results['memory_system'] = test_memory_system(user_id)
            results['duplicate_prevention'] = test_duplicate_prevention()
    
    # Print results
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! User-specific chat system is fully functional.")
        print("\n✅ The system is ready for use:")
        print("   - Database connection working")
        print("   - User authentication working")
        print("   - Chat functionality working")
        print("   - Memory extraction working")
        print("   - Duplicate request prevention working")
        
        print("\n🚀 To start the application:")
        print("   1. Run: python app.py")
        print("   2. Open: http://localhost:4000")
        print("   3. Login with your credentials")
        print("   4. Start chatting!")
        
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        print("   Make sure all dependencies are installed and database is properly configured.")
    
    return all_passed

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1) 