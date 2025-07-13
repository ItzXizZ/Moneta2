#!/usr/bin/env python3
"""
Test to verify database schema is properly set up
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def test_database_schema():
    """Test if all required tables exist and have proper structure"""
    print("🗄️ Testing database schema...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test each table
        tables_to_test = [
            'users',
            'user_memory_databases', 
            'user_memories',
            'memory_connections'
        ]
        
        for table_name in tables_to_test:
            try:
                print(f"   Testing table: {table_name}")
                result = supabase.table(table_name).select('*').limit(1).execute()
                print(f"   ✅ {table_name} table exists and is accessible")
            except Exception as e:
                print(f"   ❌ {table_name} table error: {e}")
                return False
        
        print("✅ All required tables exist and are accessible")
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

def test_user_registration_direct():
    """Test user registration directly with Supabase"""
    print("\n👤 Testing direct user registration...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test user data
        test_user = {
            'name': 'Direct Test User',
            'email': 'direct_test@example.com',
            'password_hash': 'test_hash_123',
            'is_active': True
        }
        
        # Try to insert a test user
        result = supabase.table('users').insert(test_user).execute()
        
        if result.data:
            print("✅ Direct user registration successful")
            print(f"   User ID: {result.data[0]['id']}")
            
            # Clean up test user
            user_id = result.data[0]['id']
            supabase.table('users').delete().eq('id', user_id).execute()
            print("   ✅ Test user cleaned up")
            return True
        else:
            print("❌ Direct user registration failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Direct user registration failed: {e}")
        return False

if __name__ == "__main__":
    schema_ok = test_database_schema()
    if schema_ok:
        test_user_registration_direct()
    else:
        print("\n❌ Database schema issues detected.")
        print("🔧 Please run the SQL script provided earlier in your Supabase SQL editor.")
        print("   The script creates all required tables, indexes, and security policies.") 