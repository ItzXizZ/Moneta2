#!/usr/bin/env python3
"""
Add test memories to the system for testing the memory network visualization.
"""

import sys
import os
import uuid

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(__file__))

def add_test_memories():
    """Add test memories to the system"""
    
    try:
        from auth_system import get_auth_system
        
        # Get the auth system and user memory manager
        auth_system, user_memory_manager = get_auth_system()
        
        if user_memory_manager is None:
            print("❌ User memory manager not available")
            return
        
        # Try to register a test user first
        print("🔧 Attempting to register test user...")
        
        test_email = "test@example.com"
        test_password = "testpassword123"
        test_name = "Test User"
        
        # Check if user already exists
        try:
            login_result = auth_system.login_user(test_email, test_password)
            if login_result['success']:
                user_id = login_result['user']['id']
                print(f"✅ Test user already exists: {user_id}")
            else:
                # Register new user
                register_result = auth_system.register_user(test_name, test_email, test_password)
                if register_result['success']:
                    user_id = register_result['user']['id']
                    print(f"✅ Test user registered: {user_id}")
                else:
                    print(f"❌ Failed to register test user: {register_result.get('error')}")
                    return
        except Exception as e:
            print(f"❌ Error with user registration/login: {e}")
            return
        
        # Test memories with different topics and connections
        test_memories = [
            {
                "content": "Python is a high-level programming language known for its simplicity and readability.",
                "tags": ["programming", "python", "coding"]
            },
            {
                "content": "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.",
                "tags": ["AI", "machine learning", "technology"]
            },
            {
                "content": "Flask is a lightweight web framework for Python that makes it easy to build web applications.",
                "tags": ["programming", "python", "web development", "flask"]
            },
            {
                "content": "Neural networks are computing systems inspired by biological neural networks in animal brains.",
                "tags": ["AI", "machine learning", "neural networks", "technology"]
            },
            {
                "content": "JavaScript is a programming language that enables interactive web pages and is essential for modern web development.",
                "tags": ["programming", "javascript", "web development"]
            },
            {
                "content": "Data science combines statistics, programming, and domain expertise to extract insights from data.",
                "tags": ["data science", "statistics", "programming", "analytics"]
            },
            {
                "content": "React is a JavaScript library for building user interfaces, particularly single-page applications.",
                "tags": ["programming", "javascript", "web development", "react"]
            },
            {
                "content": "Natural language processing (NLP) is a field of AI that focuses on the interaction between computers and human language.",
                "tags": ["AI", "NLP", "machine learning", "language"]
            },
            {
                "content": "Docker is a platform for developing, shipping, and running applications in containers.",
                "tags": ["programming", "docker", "containers", "devops"]
            },
            {
                "content": "Git is a distributed version control system for tracking changes in source code during software development.",
                "tags": ["programming", "git", "version control", "software development"]
            }
        ]
        
        print("🧠 Adding test memories to the system...")
        print(f"📝 Using user ID: {user_id}")
        
        for i, memory in enumerate(test_memories, 1):
            try:
                print(f"📝 Adding memory {i}: {memory['content'][:50]}...")
                
                result = user_memory_manager.add_memory_for_user(
                    user_id, 
                    memory['content'], 
                    memory['tags']
                )
                
                if result['success']:
                    print(f"✅ Memory {i} added successfully")
                else:
                    print(f"❌ Failed to add memory {i}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error adding memory {i}: {e}")
        
        # Check final count
        memories = user_memory_manager.get_user_memories(user_id, 50)
        print(f"🎉 User now has {len(memories)} total memories!")
        
        print("\n📊 User memories:")
        for i, memory in enumerate(memories):
            print(f"  {i+1}. {memory['content'][:60]}...")
        
        print(f"\n🔑 Test user credentials:")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        print(f"   User ID: {user_id}")
        
        print("\n💡 Now try refreshing the memory network to see the new memories.")
        
    except Exception as e:
        print(f"❌ Error initializing system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_memories() 