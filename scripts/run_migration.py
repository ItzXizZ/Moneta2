#!/usr/bin/env python3
"""
Run migration with hardcoded credentials
"""

import os
import sys

# Set environment variables
os.environ['SUPABASE_URL'] = "https://pquleppdqequfjwlcmbn.supabase.co"
os.environ['SUPABASE_ANON_KEY'] = os.getenv('SUPABASE_ANON_KEY', '')

# Add the backend directory to the path
sys.path.append('memory-app/backend')

def run_migration():
    """Run the migration process."""
    print("🚀 Starting migration with hardcoded credentials...")
    
    try:
        from cloud_memory_manager import CloudMemoryManager
        
        # Initialize memory manager
        memory_manager = CloudMemoryManager()
        
        if not memory_manager.client:
            print("❌ Failed to initialize Supabase client")
            return False
        
        # Find JSON files
        possible_files = [
            "memory-app/backend/data/memories.json",
            "memories.json",
            "chat_history.json"
        ]
        
        json_file_path = None
        for file_path in possible_files:
            if os.path.exists(file_path):
                json_file_path = file_path
                print(f"✅ Found JSON file: {file_path}")
                break
        
        if not json_file_path:
            print("❌ No JSON memory files found!")
            return False
        
        # Perform migration
        print(f"📦 Migrating from: {json_file_path}")
        migrated_count = memory_manager.migrate_from_json(json_file_path)
        
        print(f"✅ Migration completed! Migrated {migrated_count} memories")
        
        # Get stats
        stats = memory_manager.get_stats()
        print(f"📊 Database stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 