#!/usr/bin/env python3

import os
from auth_system import auth_system, user_memory_manager

def debug_user_memory():
    print("🔍 Debugging user memory system...")
    
    # Test user login
    email = 'ethan8eight@gmail.com'
    password = 'Mydragon100'
    
    result = auth_system.login_user(email, password)
    if result['success']:
        user_id = result['user']['id']
        print(f"✅ User login successful: {user_id}")
        
        # Check user memories
        memories = user_memory_manager.get_user_memories(user_id, 20)
        print(f"📊 User has {len(memories)} memories")
        
        if memories:
            print("📝 User memories:")
            for i, memory in enumerate(memories[:5]):
                print(f"  {i+1}. {memory.get('content', 'No content')[:50]}...")
        else:
            print("❌ No user memories found - this explains why you're seeing default memories!")
            
        # Check memory network data (simplified)
        try:
            # Create a simple network representation from user memories
            nodes = []
            for memory in memories:
                nodes.append({
                    'id': memory['id'],
                    'content': memory['content'][:50] + '...' if len(memory['content']) > 50 else memory['content'],
                    'score': memory.get('score', 0)
                })
            print(f"🕸️  Memory network would have: {len(nodes)} nodes")
        except Exception as e:
            print(f"❌ Error creating memory network: {e}")
            
        # Check if user has any conversations
        try:
            conversations = auth_system.supabase.table('user_memories').select('*').eq('user_id', user_id).limit(5).execute()
            print(f"💬 User has {len(conversations.data)} conversation memories in database")
        except Exception as e:
            print(f"❌ Error checking conversations: {e}")
            
    else:
        print(f"❌ Login failed: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    debug_user_memory() 