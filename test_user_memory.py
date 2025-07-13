#!/usr/bin/env python3

from auth_system import user_memory_manager, auth_system

def test_user_memory():
    print("Testing user-specific memory system...")
    
    # Test user login to get user ID
    result = auth_system.login_user('ethan8eight@gmail.com', 'Mydragon100')
    if result['success']:
        user_id = result['user']['id']
        print(f'User ID: {user_id}')
        
        # Get user memories
        memories = user_memory_manager.get_user_memories(user_id, 10)
        print(f'User has {len(memories)} memories')
        
        # Add a test memory if none exist
        if len(memories) == 0:
            test_result = user_memory_manager.add_memory_for_user(
                user_id, 
                'I love programming and building AI systems', 
                ['programming', 'AI', 'interests']
            )
            if test_result['success']:
                print('Added test memory successfully')
            else:
                print(f'Failed to add test memory: {test_result.get("error")}')
        else:
            print('User already has memories:')
            for i, memory in enumerate(memories):
                print(f'  {i+1}. {memory["content"][:50]}...')
    else:
        print(f'Login failed: {result.get("error")}')

if __name__ == "__main__":
    test_user_memory() 