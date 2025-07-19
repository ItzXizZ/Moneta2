#!/usr/bin/env python3
"""
Dashboard Authentication Debug Tool
Tests every step of the dashboard authentication flow to identify issues.
"""

import requests
import json
import time

def test_dashboard_auth_flow():
    """Test the complete dashboard authentication flow step by step"""
    
    base_url = "http://localhost:4000"
    
    print("🔍 DASHBOARD AUTHENTICATION DEBUG")
    print("=" * 60)
    
    # Step 1: Test login
    print("\n1️⃣ TESTING LOGIN...")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('token')
            print(f"   ✅ Login successful")
            print(f"   Token length: {len(token) if token else 0}")
            print(f"   Token preview: {token[:20] if token else 'None'}...")
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return
    
    # Step 2: Test user profile endpoint
    print("\n2️⃣ TESTING USER PROFILE ENDPOINT...")
    try:
        profile_response = requests.get(f"{base_url}/api/user/profile", 
                                      headers={'Authorization': f'Bearer {token}'})
        print(f"   Profile status: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print(f"   ✅ Profile request successful")
            print(f"   Success: {profile_data.get('success', False)}")
            
            if profile_data.get('success'):
                profile = profile_data.get('profile', {})
                user = profile.get('user', {})
                stats = profile.get('stats', {})
                
                print(f"   User: {user.get('name', 'N/A')}")
                print(f"   Email: {user.get('email', 'N/A')}")
                print(f"   Total memories: {stats.get('total_memories', 0)}")
                print(f"   Average score: {stats.get('average_score', 0)}")
            else:
                print(f"   ❌ Profile data indicates failure")
                print(f"   Error: {profile_data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ Profile request failed: {profile_response.text}")
    except Exception as e:
        print(f"   ❌ Profile error: {e}")
    
    # Step 3: Test memories endpoint
    print("\n3️⃣ TESTING MEMORIES ENDPOINT...")
    try:
        memories_response = requests.get(f"{base_url}/api/memories?limit=5", 
                                       headers={'Authorization': f'Bearer {token}'})
        print(f"   Memories status: {memories_response.status_code}")
        
        if memories_response.status_code == 200:
            memories_data = memories_response.json()
            print(f"   ✅ Memories request successful")
            print(f"   Success: {memories_data.get('success', False)}")
            
            if memories_data.get('success'):
                memories = memories_data.get('memories', [])
                print(f"   Found {len(memories)} memories")
                
                if memories:
                    print(f"   First memory: {memories[0].get('content', 'N/A')[:50]}...")
                    print(f"   First memory score: {memories[0].get('score', 0)}")
            else:
                print(f"   ❌ Memories data indicates failure")
                print(f"   Error: {memories_data.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ Memories request failed: {memories_response.text}")
    except Exception as e:
        print(f"   ❌ Memories error: {e}")
    
    # Step 4: Test dashboard route directly
    print("\n4️⃣ TESTING DASHBOARD ROUTE...")
    try:
        dashboard_response = requests.get(f"{base_url}/dashboard")
        print(f"   Dashboard route status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            print(f"   ✅ Dashboard route accessible")
            content = dashboard_response.text
            
            # Check if dashboard contains authentication-related content
            if "Demo User" in content:
                print(f"   ⚠️ Dashboard contains 'Demo User' - likely showing demo mode")
            if "test@example.com" in content:
                print(f"   ✅ Dashboard contains test email - likely showing real data")
            if "⚠️ Dashboard not available without authentication" in content:
                print(f"   ❌ Dashboard shows authentication error message")
            if "loadDashboard()" in content:
                print(f"   ✅ Dashboard contains loadDashboard function")
        else:
            print(f"   ❌ Dashboard route failed: {dashboard_response.text}")
    except Exception as e:
        print(f"   ❌ Dashboard route error: {e}")
    
    # Step 5: Test browser simulation
    print("\n5️⃣ SIMULATING BROWSER BEHAVIOR...")
    print("   This simulates what the browser JavaScript would do:")
    
    # Simulate localStorage token check
    print(f"   📋 localStorage token exists: {'Yes' if token else 'No'}")
    print(f"   📋 Token length: {len(token) if token else 0}")
    
    # Simulate profile fetch
    if token:
        try:
            profile_sim = requests.get(f"{base_url}/api/user/profile", 
                                     headers={'Authorization': f'Bearer {token}'})
            if profile_sim.status_code == 200:
                profile_sim_data = profile_sim.json()
                if profile_sim_data.get('success'):
                    print(f"   ✅ Profile fetch would succeed")
                    stats = profile_sim_data.get('profile', {}).get('stats', {})
                    total_memories = stats.get('total_memories', 0)
                    print(f"   📊 Total memories: {total_memories}")
                    
                    if total_memories == 0:
                        print(f"   ⚠️ WARNING: 0 memories found - this would trigger demo mode!")
                    else:
                        print(f"   ✅ Sufficient memories found - should show real data")
                else:
                    print(f"   ❌ Profile fetch would fail: {profile_sim_data.get('error')}")
            else:
                print(f"   ❌ Profile fetch would fail with status: {profile_sim.status_code}")
        except Exception as e:
            print(f"   ❌ Profile fetch simulation error: {e}")
    
    # Step 6: Test memory network endpoint
    print("\n6️⃣ TESTING MEMORY NETWORK ENDPOINT...")
    try:
        network_response = requests.get(f"{base_url}/memory-network?threshold=0.4", 
                                      headers={'Authorization': f'Bearer {token}'})
        print(f"   Memory network status: {network_response.status_code}")
        
        if network_response.status_code == 200:
            network_data = network_response.json()
            nodes = network_data.get('nodes', [])
            edges = network_data.get('edges', [])
            print(f"   ✅ Memory network accessible")
            print(f"   📊 Nodes: {len(nodes)}")
            print(f"   📊 Edges: {len(edges)}")
            
            if nodes:
                print(f"   📊 First node score: {nodes[0].get('score', 0)}")
        else:
            print(f"   ❌ Memory network failed: {network_response.text}")
    except Exception as e:
        print(f"   ❌ Memory network error: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 DIAGNOSIS SUMMARY")
    print("=" * 60)
    
    # Provide diagnosis based on results
    print("\n💡 LIKELY ISSUES:")
    print("1. If profile shows 0 memories → Dashboard falls back to demo mode")
    print("2. If token is invalid → Dashboard shows auth error")
    print("3. If API endpoints fail → Dashboard shows demo mode")
    print("4. If browser cache issue → Hard refresh needed")
    
    print("\n🔧 RECOMMENDED FIXES:")
    print("1. Check if memories are actually in the database")
    print("2. Verify user ID consistency across endpoints")
    print("3. Clear browser cache and localStorage")
    print("4. Check browser console for JavaScript errors")
    
    print("\n📋 NEXT STEPS:")
    print("1. Open browser developer tools (F12)")
    print("2. Go to Console tab")
    print("3. Navigate to dashboard")
    print("4. Look for authentication/logging messages")
    print("5. Check Network tab for failed API calls")

if __name__ == "__main__":
    test_dashboard_auth_flow() 