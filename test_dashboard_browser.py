#!/usr/bin/env python3
"""
Browser Dashboard Authentication Test
This script helps you test the dashboard authentication in your browser.
"""

import requests
import json

def get_auth_token():
    """Get an authentication token for testing"""
    
    base_url = "http://localhost:4000"
    
    print("🔍 GETTING AUTHENTICATION TOKEN FOR BROWSER TESTING")
    print("=" * 60)
    
    # Login with test user
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        print("🔑 Logging in...")
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return None
        
        login_result = login_response.json()
        if not login_result.get('success'):
            print(f"❌ Login failed: {login_result.get('error')}")
            return None
        
        token = login_result.get('token')
        user = login_result.get('user')
        
        print(f"✅ Login successful!")
        print(f"👤 User: {user.get('name')} ({user.get('email')})")
        print(f"🆔 User ID: {user.get('id')}")
        print(f"🔑 Token: {token[:50]}...")
        
        return token, user
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main function to run the browser test"""
    
    result = get_auth_token()
    if not result:
        print("❌ Failed to get authentication token")
        return
    
    token, user = result
    
    print("\n" + "=" * 60)
    print("🌐 BROWSER TESTING INSTRUCTIONS")
    print("=" * 60)
    
    print("\n📋 STEP 1: Open Browser Developer Tools")
    print("   1. Open your browser and go to: http://localhost:4000")
    print("   2. Press F12 to open Developer Tools")
    print("   3. Go to the 'Console' tab")
    
    print("\n📋 STEP 2: Set Authentication Token")
    print("   Copy and paste this command into the console:")
    print(f"   localStorage.setItem('authToken', '{token}');")
    print(f"   localStorage.setItem('user', '{json.dumps(user)}');")
    
    print("\n📋 STEP 3: Verify Token is Set")
    print("   Run this command to verify:")
    print("   console.log('Token:', localStorage.getItem('authToken'));")
    print("   console.log('User:', JSON.parse(localStorage.getItem('user')));")
    
    print("\n📋 STEP 4: Test Dashboard")
    print("   1. Navigate to: http://localhost:4000/dashboard")
    print("   2. Check the console for any error messages")
    print("   3. The dashboard should show real user data, not demo mode")
    
    print("\n📋 STEP 5: Test Dashboard Button from Chat")
    print("   1. Go to: http://localhost:4000/chat")
    print("   2. Click the '🏠 Dashboard' button in the sidebar")
    print("   3. It should redirect to the dashboard with real data")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("   - If you see 'Demo User', the token is not being read properly")
    print("   - Check the Network tab in Developer Tools for failed API calls")
    print("   - Look for 401 errors which indicate authentication issues")
    print("   - Try hard refresh (Ctrl+F5) to clear any cached content")
    
    print("\n💡 EXPECTED BEHAVIOR:")
    print("   - Dashboard should show: Test User (test@example.com)")
    print("   - Memory count should be: 10")
    print("   - Recent memories should show actual memory content")
    print("   - No 'Demo User' or demo mode messages")

if __name__ == "__main__":
    main() 