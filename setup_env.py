#!/usr/bin/env python3
"""
Interactive script to set up your .env file with Clerk and other credentials
"""

import os
import sys

def create_env_file():
    print("="*70)
    print("  MONETA - Environment Setup")
    print("="*70)
    print("\nThis script will help you create your .env file.")
    print("\nYou'll need:")
    print("  1. Clerk account (https://clerk.com) - FREE")
    print("  2. Supabase account (https://supabase.com) - FREE")
    print("  3. OpenAI API key (https://platform.openai.com) - PAID")
    print("\n" + "="*70 + "\n")
    
    # Check if .env already exists
    if os.path.exists('.env'):
        response = input(".env file already exists. Overwrite? (y/n): ").lower()
        if response != 'y':
            print("Setup cancelled.")
            return
    
    env_content = """# ============================================
# CLERK AUTHENTICATION
# ============================================
# Get these from https://dashboard.clerk.com/
# 1. Create an account at https://clerk.com
# 2. Create a new application
# 3. Enable Google OAuth in the "Social Connections" section
# 4. Copy your keys from the API Keys section
"""
    
    print("\n[1/7] CLERK SECRET KEY")
    print("   Go to: https://dashboard.clerk.com/")
    print("   Navigate to: API Keys")
    print("   Copy your 'Secret Key' (starts with 'sk_test_' or 'sk_live_')")
    clerk_secret = input("   Paste here (or press Enter to skip): ").strip()
    env_content += f"CLERK_SECRET_KEY={clerk_secret}\n"
    
    print("\n[2/7] CLERK PUBLISHABLE KEY")
    print("   Copy your 'Publishable Key' (starts with 'pk_test_' or 'pk_live_')")
    clerk_pub = input("   Paste here (or press Enter to skip): ").strip()
    env_content += f"CLERK_PUBLISHABLE_KEY={clerk_pub}\n"
    
    env_content += """
# ============================================
# SUPABASE DATABASE
# ============================================
# Get these from https://app.supabase.com/
"""
    
    print("\n[3/7] SUPABASE URL")
    print("   Go to: https://app.supabase.com/")
    print("   Select your project → Settings → API")
    print("   Copy 'Project URL' (starts with 'https://')")
    supabase_url = input("   Paste here (or press Enter to skip): ").strip()
    env_content += f"SUPABASE_URL={supabase_url}\n"
    
    print("\n[4/7] SUPABASE ANON KEY")
    print("   Copy 'anon public' key (long string starting with 'eyJ')")
    supabase_key = input("   Paste here (or press Enter to skip): ").strip()
    env_content += f"SUPABASE_KEY={supabase_key}\n"
    
    print("\n[5/7] SUPABASE SERVICE KEY")
    print("   Copy 'service_role' key (long string starting with 'eyJ')")
    supabase_service = input("   Paste here (or press Enter to skip): ").strip()
    env_content += f"SUPABASE_SERVICE_KEY={supabase_service}\n"
    
    env_content += """
# ============================================
# OPENAI API
# ============================================
# Get this from https://platform.openai.com/api-keys
"""
    
    print("\n[6/7] OPENAI API KEY")
    print("   Go to: https://platform.openai.com/api-keys")
    print("   Click 'Create new secret key'")
    print("   Copy the key (starts with 'sk-' or 'sk-proj-')")
    openai_key = input("   Paste here (or press Enter to skip): ").strip()
    env_content += f"OPENAI_API_KEY={openai_key}\n"
    
    env_content += """
# ============================================
# FLASK CONFIGURATION
# ============================================
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=4000
"""
    
    print("\n[7/7] JWT SECRET")
    print("   Generate a random secret key for JWT tokens")
    import secrets
    jwt_secret = secrets.token_urlsafe(32)
    print(f"   Generated: {jwt_secret[:20]}...")
    env_content += f"JWT_SECRET={jwt_secret}\n"
    
    # Write the file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("\n" + "="*70)
        print("  ✅ SUCCESS! .env file created")
        print("="*70)
        print("\nYour .env file has been created with the following keys:")
        if clerk_secret:
            print("  ✅ Clerk Secret Key")
        else:
            print("  ⚠️  Clerk Secret Key (EMPTY - add this later!)")
        if clerk_pub:
            print("  ✅ Clerk Publishable Key")
        else:
            print("  ⚠️  Clerk Publishable Key (EMPTY - add this later!)")
        if supabase_url:
            print("  ✅ Supabase URL")
        else:
            print("  ⚠️  Supabase URL (EMPTY - add this later!)")
        if supabase_key:
            print("  ✅ Supabase Anon Key")
        else:
            print("  ⚠️  Supabase Anon Key (EMPTY - add this later!)")
        if supabase_service:
            print("  ✅ Supabase Service Key")
        else:
            print("  ⚠️  Supabase Service Key (EMPTY - add this later!)")
        if openai_key:
            print("  ✅ OpenAI API Key")
        else:
            print("  ⚠️  OpenAI API Key (EMPTY - add this later!)")
        print("  ✅ JWT Secret (auto-generated)")
        
        print("\n" + "="*70)
        print("\nNext steps:")
        print("  1. If you skipped any keys, edit .env and add them")
        print("  2. Run the database setup: docs/CLERK_SUPABASE_SCHEMA.sql")
        print("  3. Test the routes: python test_routes.py")
        print("  4. Start the server: python run.py")
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to create .env file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)


