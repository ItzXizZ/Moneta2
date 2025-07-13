#!/usr/bin/env python3

from auth_system import auth_system, user_memory_manager

def add_test_memories():
    print("🧪 Adding test memories to user account...")
    
    # Login user
    result = auth_system.login_user('ethan8eight@gmail.com', 'Mydragon100')
    if not result['success']:
        print(f"❌ Login failed: {result.get('message', 'Unknown error')}")
        return
    
    user_id = result['user']['id']
    print(f"✅ User login successful: {user_id}")
    
    # Test memories to add
    test_memories = [
        {
            'content': 'I enjoy working with Python and building AI applications',
            'tags': ['python', 'ai', 'programming']
        },
        {
            'content': 'Machine learning and neural networks fascinate me',
            'tags': ['ml', 'neural networks', 'ai']
        },
        {
            'content': 'I like to build web applications using Flask and React',
            'tags': ['flask', 'react', 'web development']
        },
        {
            'content': 'Data science and analytics are important skills',
            'tags': ['data science', 'analytics', 'python']
        },
        {
            'content': 'I am interested in natural language processing',
            'tags': ['nlp', 'ai', 'language']
        },
        {
            'content': 'Building chatbots and conversational AI is exciting',
            'tags': ['chatbots', 'conversational ai', 'nlp']
        },
        {
            'content': 'I like to experiment with different programming languages',
            'tags': ['programming', 'languages', 'learning']
        },
        {
            'content': 'Database design and optimization are crucial for applications',
            'tags': ['database', 'sql', 'optimization']
        }
    ]
    
    print(f"📝 Adding {len(test_memories)} test memories...")
    
    for i, memory_data in enumerate(test_memories):
        result = user_memory_manager.add_memory_for_user(
            user_id, 
            memory_data['content'], 
            memory_data['tags']
        )
        
        if result['success']:
            print(f"✅ Added memory {i+1}: {memory_data['content'][:50]}...")
        else:
            print(f"❌ Failed to add memory {i+1}: {result.get('error', 'Unknown error')}")
    
    # Check final count
    memories = user_memory_manager.get_user_memories(user_id, 50)
    print(f"🎉 User now has {len(memories)} total memories!")
    
    print("\n📊 User memories:")
    for i, memory in enumerate(memories):
        print(f"  {i+1}. {memory['content'][:60]}...")

if __name__ == "__main__":
    add_test_memories() 