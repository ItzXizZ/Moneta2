#!/usr/bin/env python3
"""
Login test user and get authentication token for testing the memory network.
"""

import requests
import json

def login_test_user():
    """Login test user and get authentication token"""
    
    base_url = "http://localhost:4000"
    
    print("🔑 LOGIN TEST USER")
    print("=" * 50)
    
    # Test user credentials
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        print(f"📧 Logging in with: {login_data['email']}")
        
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                token = result.get('token')
                user = result.get('user')
                
                print("✅ Login successful!")
                print(f"👤 User: {user.get('name')} ({user.get('email')})")
                print(f"🆔 User ID: {user.get('id')}")
                print(f"🔑 Token: {token[:50]}...")
                
                print("\n" + "=" * 50)
                print("🔧 TO SET UP AUTHENTICATION IN BROWSER:")
                print("1. Open your browser's Developer Tools (F12)")
                print("2. Go to the Console tab")
                print("3. Run these commands:")
                print(f"   localStorage.setItem('authToken', '{token}');")
                print(f"   localStorage.setItem('user', '{json.dumps(user)}');")
                print("4. Refresh the page")
                print("5. The memory network should now show 11 memories!")
                
                print("\n" + "=" * 50)
                print("🧪 TESTING MEMORY NETWORK WITH AUTH...")
                
                # Test memory network with the token
                headers = {'Authorization': f'Bearer {token}'}
                network_response = requests.get(f"{base_url}/memory-network", headers=headers)
                
                if network_response.status_code == 200:
                    network_data = network_response.json()
                    print(f"✅ Memory network working!")
                    print(f"📊 Found {len(network_data.get('nodes', []))} nodes")
                    print(f"📊 Found {len(network_data.get('edges', []))} edges")
                    print(f"📊 Total memories: {network_data.get('total_memories', 0)}")
                else:
                    print(f"❌ Memory network test failed: {network_response.status_code}")
                    
            else:
                print(f"❌ Login failed: {result.get('error')}")
        else:
            print(f"❌ Login request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    login_test_user() 