#!/usr/bin/env python3
"""
Debug the user ID mismatch issue between profile endpoint and memory network.
"""

import requests
import json

def debug_user_ids():
    """Debug user ID mismatch"""
    
    base_url = "http://localhost:4000"
    
    print("🔍 DEBUGGING USER ID MISMATCH")
    print("=" * 50)
    
    # Login with test user
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        print("🔑 Step 1: Login and get token...")
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
        
        login_result = login_response.json()
        token = login_result.get('token')
        user = login_result.get('user', {})
        
        print(f"✅ Login successful")
        print(f"   User ID from login: {user.get('id')}")
        print(f"   User name: {user.get('name')}")
        print(f"   User email: {user.get('email')}")
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test profile endpoint
        print(f"\n👤 Step 2: Test profile endpoint...")
        profile_response = requests.get(f"{base_url}/api/user/profile", headers=headers)
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            profile_user = profile_data.get('profile', {}).get('user', {})
            stats = profile_data.get('profile', {}).get('stats', {})
            
            print(f"   ✅ Profile endpoint successful")
            print(f"   Profile user ID: {profile_user.get('id')}")
            print(f"   Total memories: {stats.get('total_memories', 0)}")
            print(f"   Average score: {stats.get('average_score', 0)}")
        else:
            print(f"   ❌ Profile endpoint failed: {profile_response.status_code}")
        
        # Test memories endpoint
        print(f"\n📝 Step 3: Test memories endpoint...")
        memories_response = requests.get(f"{base_url}/api/memories?limit=10", headers=headers)
        
        if memories_response.status_code == 200:
            memories_data = memories_response.json()
            memories = memories_data.get('memories', [])
            
            print(f"   ✅ Memories endpoint successful")
            print(f"   Found {len(memories)} memories")
            
            if memories:
                print(f"   First memory user_id: {memories[0].get('user_id', 'NO USER_ID')}")
                print(f"   First memory content: {memories[0].get('content', 'NO CONTENT')[:50]}...")
        else:
            print(f"   ❌ Memories endpoint failed: {memories_response.status_code}")
        
        # Test memory network endpoint
        print(f"\n🕸️ Step 4: Test memory network endpoint...")
        network_response = requests.get(f"{base_url}/memory-network?threshold=0.4", headers=headers)
        
        if network_response.status_code == 200:
            network_data = network_response.json()
            nodes = network_data.get('nodes', [])
            edges = network_data.get('edges', [])
            
            print(f"   ✅ Memory network endpoint successful")
            print(f"   Found {len(nodes)} nodes")
            print(f"   Found {len(edges)} edges")
            
            if nodes:
                print(f"   First node score: {nodes[0].get('score', 0)}")
        else:
            print(f"   ❌ Memory network endpoint failed: {network_response.status_code}")
        
        # Check if there's a user ID mismatch
        print(f"\n🔍 ANALYSIS:")
        if profile_user.get('id') == user.get('id'):
            print(f"   ✅ User IDs match between login and profile")
        else:
            print(f"   ❌ User ID mismatch!")
            print(f"      Login user ID: {user.get('id')}")
            print(f"      Profile user ID: {profile_user.get('id')}")
        
        print(f"\n💡 POSSIBLE ISSUES:")
        print(f"   1. Memories were added with different user ID")
        print(f"   2. Token contains wrong user ID")
        print(f"   3. Database query issue")
        print(f"   4. Authentication decorator issue")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_user_ids() 