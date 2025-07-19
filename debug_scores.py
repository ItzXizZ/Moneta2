#!/usr/bin/env python3
"""
Debug the scoring system by making a direct request to the memory network endpoint.
"""

import requests
import json

def debug_scoring():
    """Debug the scoring system"""
    
    base_url = "http://localhost:4000"
    
    print("🔍 DEBUGGING SCORING SYSTEM")
    print("=" * 50)
    
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
            return
        
        login_result = login_response.json()
        if not login_result.get('success'):
            print(f"❌ Login failed: {login_result.get('error')}")
            return
        
        token = login_result.get('token')
        print("✅ Login successful")
        
        # Test memory network endpoint
        print("\n📊 Testing memory network endpoint...")
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{base_url}/memory-network?threshold=0.4", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            
            print(f"✅ Got response: {len(nodes)} nodes, {len(edges)} edges")
            
            # Check the first few nodes for scores
            print(f"\n📈 Checking node scores:")
            for i, node in enumerate(nodes[:5]):
                score = node.get('score', 0)
                label = node.get('label', 'No label')
                print(f"   Node {i+1}: Score = {score}, Label = {label[:50]}...")
            
            # Check if any nodes have non-zero scores
            non_zero_scores = [node for node in nodes if node.get('score', 0) > 0]
            print(f"\n📊 Score Analysis:")
            print(f"   Total nodes: {len(nodes)}")
            print(f"   Nodes with non-zero scores: {len(non_zero_scores)}")
            
            if non_zero_scores:
                print(f"   ✅ Scoring system is working!")
                for node in non_zero_scores[:3]:
                    print(f"     - Score: {node.get('score')}, Content: {node.get('label')[:40]}...")
            else:
                print(f"   ❌ All scores are zero - there's an issue with the scoring system")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_scoring() 