#!/usr/bin/env python3
"""
Check what user IDs are associated with memories in the database.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(__file__))

def check_memory_user_ids():
    """Check memory user IDs in the database"""
    
    try:
        from auth_system import get_auth_system
        
        # Get the auth system and user memory manager
        auth_system, user_memory_manager = get_auth_system()
        
        if user_memory_manager is None:
            print("❌ User memory manager not available")
            return
        
        print("🔍 CHECKING MEMORY USER IDS IN DATABASE")
        print("=" * 50)
        
        # Get all memories from the database (without user filter)
        try:
            result = auth_system.supabase.table('user_memories').select('*').execute()
            all_memories = result.data if result.data else []
            
            print(f"📊 Found {len(all_memories)} total memories in database")
            
            if all_memories:
                print(f"\n📝 Memory breakdown by user_id:")
                user_memory_counts = {}
                
                for memory in all_memories:
                    user_id = memory.get('user_id', 'NO_USER_ID')
                    user_memory_counts[user_id] = user_memory_counts.get(user_id, 0) + 1
                
                for user_id, count in user_memory_counts.items():
                    print(f"   User ID: {user_id} - {count} memories")
                
                # Show first few memories
                print(f"\n📋 First 3 memories:")
                for i, memory in enumerate(all_memories[:3]):
                    print(f"   {i+1}. User ID: {memory.get('user_id', 'NO_USER_ID')}")
                    print(f"      Content: {memory.get('content', 'NO CONTENT')[:50]}...")
                    print(f"      Tags: {memory.get('tags', 'NO TAGS')}")
                    print(f"      Created: {memory.get('created_at', 'NO DATE')}")
                    print()
                
                # Check if there are memories for the test user
                test_user_id = "c07a0b77-96b9-474b-8908-9275e48e6a6d"
                test_user_memories = [m for m in all_memories if m.get('user_id') == test_user_id]
                
                print(f"🔍 Checking test user memories:")
                print(f"   Test user ID: {test_user_id}")
                print(f"   Memories for test user: {len(test_user_memories)}")
                
                if test_user_memories:
                    print(f"   ✅ Test user has memories!")
                else:
                    print(f"   ❌ Test user has no memories!")
                    print(f"   💡 This explains why the dashboard shows 0 memories")
                    
                    # Check if there are memories with different user IDs
                    other_user_memories = [m for m in all_memories if m.get('user_id') != test_user_id]
                    if other_user_memories:
                        print(f"   📝 Found {len(other_user_memories)} memories with different user IDs")
                        print(f"   💡 The memories were added with a different user ID")
                        
                        # Show the user IDs that have memories
                        other_user_ids = set(m.get('user_id') for m in other_user_memories)
                        print(f"   Other user IDs with memories: {list(other_user_ids)}")
                
            else:
                print(f"❌ No memories found in database")
                
        except Exception as e:
            print(f"❌ Error querying database: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_memory_user_ids() 