#!/usr/bin/env python3
"""
Memory Network Diagnostic Tool
Tests whether the memory network loads correctly for authenticated users.
"""

import requests
import json

def test_memory_network_endpoints():
    """Test the memory network related endpoints"""
    
    base_url = "http://localhost:5000"
    
    print("🔍 MEMORY NETWORK DIAGNOSTIC")
    print("=" * 50)
    
    # Test 1: Check if memory network endpoint is accessible
    print("\n1. Testing /memory-network endpoint...")
    try:
        response = requests.get(f"{base_url}/memory-network")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Correctly requires authentication")
        elif response.status_code == 200:
            data = response.json()
            print(f"   📊 Found {len(data.get('memories', []))} memories")
            print(f"   📊 Found {len(data.get('connections', []))} connections")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Check memory availability
    print("\n2. Testing /check_memory_availability endpoint...")
    try:
        response = requests.get(f"{base_url}/check_memory_availability")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Available: {data.get('available', False)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check if authentication routes work
    print("\n3. Testing authentication endpoints...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   Landing page status: {response.status_code}")
        
        response = requests.get(f"{base_url}/dashboard")
        print(f"   Dashboard status: {response.status_code}")
        
        response = requests.get(f"{base_url}/chat")
        print(f"   Chat interface status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("DIAGNOSIS COMPLETE")
    print("\nIf you see 401 errors, that's normal - it means authentication is working.")
    print("The memory network should load automatically when you're logged in.")
    print("Check the browser console for memory network initialization logs.")

if __name__ == "__main__":
    test_memory_network_endpoints() 