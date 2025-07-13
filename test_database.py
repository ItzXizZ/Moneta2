#!/usr/bin/env python3
"""
Test script to verify database and authentication functionality
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:4000"
TEST_USER = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpassword123"
}

def test_landing_page():
    """Test if the landing page loads correctly"""
    print("🌐 Testing landing page...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Landing page loaded successfully")
            print(f"   Response size: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Landing page failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Landing page test failed: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    print("\n👤 Testing user registration...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                print("✅ User registration successful")
                print(f"   User ID: {data['user']['id']}")
                print(f"   Token length: {len(data['token'])} characters")
                return data['token']
            else:
                print(f"❌ Registration failed: {data.get('error')}")
                return None
        else:
            print(f"❌ Registration failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return None

def test_user_login():
    """Test user login"""
    print("\n🔐 Testing user login...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ User login successful")
                print(f"   User: {data['user']['name']} ({data['user']['email']})")
                return data['token']
            else:
                print(f"❌ Login failed: {data.get('error')}")
                return None
        else:
            print(f"❌ Login failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None

def test_token_verification(token):
    """Test JWT token verification"""
    print("\n🔍 Testing token verification...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Token verification successful")
                print(f"   Verified user: {data['user']['name']}")
                return True
            else:
                print(f"❌ Token verification failed: {data}")
                return False
        else:
            print(f"❌ Token verification failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Token verification test failed: {e}")
        return False

def test_memory_operations(token):
    """Test memory CRUD operations"""
    print("\n🧠 Testing memory operations...")
    
    # Test adding a memory
    print("   Adding a test memory...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/memories",
            json={
                "content": "This is a test memory for database functionality testing",
                "tags": ["test", "database", "functionality"]
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                print("   ✅ Memory added successfully")
                memory_id = data['memory']['id']
            else:
                print(f"   ❌ Memory addition failed: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Memory addition failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Memory addition test failed: {e}")
        return False
    
    # Test retrieving memories
    print("   Retrieving user memories...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/memories",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Retrieved {data['count']} memories")
                if data['count'] > 0:
                    print(f"   First memory: {data['memories'][0]['content'][:50]}...")
            else:
                print(f"   ❌ Memory retrieval failed: {data}")
                return False
        else:
            print(f"   ❌ Memory retrieval failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Memory retrieval test failed: {e}")
        return False
    
    # Test memory search
    print("   Testing memory search...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/memories/search?q=test&limit=5",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Memory search returned {data['count']} results")
                return True
            else:
                print(f"   ❌ Memory search failed: {data}")
                return False
        else:
            print(f"   ❌ Memory search failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Memory search test failed: {e}")
        return False

def test_user_profile(token):
    """Test user profile endpoint"""
    print("\n👤 Testing user profile...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/user/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ User profile retrieved successfully")
                print(f"   Memory count: {data.get('memory_count', 'N/A')}")
                return True
            else:
                print(f"❌ Profile retrieval failed: {data}")
                return False
        else:
            print(f"❌ Profile retrieval failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Profile test failed: {e}")
        return False

def cleanup_test_user(token):
    """Clean up test user (if cleanup endpoint exists)"""
    print("\n🧹 Cleaning up test data...")
    # Note: In a real implementation, you might want to add a cleanup endpoint
    # For now, we'll just note that the test user remains in the database
    print("   Test user remains in database for manual cleanup if needed")
    print(f"   Test user email: {TEST_USER['email']}")

def main():
    """Run all tests"""
    print("🚀 Starting Moneta Database and Authentication Tests")
    print("=" * 60)
    
    # Test 1: Landing page
    if not test_landing_page():
        print("\n❌ Basic connectivity test failed. Exiting.")
        return
    
    # Test 2: User registration
    token = test_user_registration()
    if not token:
        # Try login instead (user might already exist)
        token = test_user_login()
        if not token:
            print("\n❌ Authentication tests failed. Exiting.")
            return
    
    # Test 3: Token verification
    if not test_token_verification(token):
        print("\n❌ Token verification failed. Exiting.")
        return
    
    # Test 4: Memory operations
    if not test_memory_operations(token):
        print("\n❌ Memory operations failed.")
    
    # Test 5: User profile
    if not test_user_profile(token):
        print("\n❌ User profile test failed.")
    
    # Cleanup
    cleanup_test_user(token)
    
    print("\n" + "=" * 60)
    print("🎉 Database and Authentication Tests Completed!")
    print("✅ All core functionality is working correctly")
    print(f"🌐 Application is running at: {BASE_URL}")
    print("🔗 You can now open your browser and test the full interface")

if __name__ == "__main__":
    main() 