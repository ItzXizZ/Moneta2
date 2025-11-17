#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

from app.core.auth_system import auth_system, get_auth_system

def setup_chat_tables():
    """Set up the chat tables in Supabase"""
    print("[SETUP] Setting up chat tables in Supabase...")
    
    # Ensure auth system is initialized
    if not auth_system or not auth_system.supabase:
        print("[ERROR] Auth system not initialized. Attempting to initialize...")
        try:
            auth_sys, _ = get_auth_system()
            if not auth_sys or not auth_sys.supabase:
                print("[ERROR] Failed to initialize auth system")
                return False
        except Exception as e:
            print(f"[ERROR] Error initializing auth system: {e}")
            return False
    
    # Read the SQL script
    with open('create_chat_tables.sql', 'r') as f:
        sql_script = f.read()
    
    try:
        # Execute the SQL script using direct SQL execution
        result = auth_system.supabase.rpc('exec_sql', {'sql': sql_script})
        print("[OK] Chat tables created successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Error creating chat tables: {e}")
        
        # Try alternative approach - execute statements one by one
        print("[INFO] Trying alternative approach...")
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
        
        success_count = 0
        for i, statement in enumerate(statements):
            try:
                if statement.upper().startswith('CREATE TABLE'):
                    print(f"Creating table {i+1}/{len(statements)}...")
                elif statement.upper().startswith('CREATE INDEX'):
                    print(f"Creating index {i+1}/{len(statements)}...")
                elif statement.upper().startswith('CREATE FUNCTION'):
                    print(f"Creating function {i+1}/{len(statements)}...")
                elif statement.upper().startswith('CREATE TRIGGER'):
                    print(f"Creating trigger {i+1}/{len(statements)}...")
                else:
                    print(f"Executing statement {i+1}/{len(statements)}...")
                
                # Try to execute directly
                auth_system.supabase.rpc('exec_sql', {'sql': statement})
                success_count += 1
                
            except Exception as stmt_error:
                print(f"[WARN] Statement {i+1} failed: {stmt_error}")
                # Continue with other statements
        
        print(f"[INFO] Manual table creation completed. {success_count}/{len(statements)} statements succeeded.")
        return success_count > 0

if __name__ == "__main__":
    setup_chat_tables() 