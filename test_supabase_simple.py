#!/usr/bin/env python3
"""
Simple test to verify Supabase connection
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase connection...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    print(f"   URL: {supabase_url}")
    print(f"   Key: {supabase_key[:20]}..." if supabase_key else "   Key: None")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test connection by trying to query users table
        result = supabase.table('users').select('id').limit(1).execute()
        print("✅ Supabase connection successful")
        print(f"   Users table accessible: {len(result.data) if result.data else 0} records found")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    test_supabase_connection() 