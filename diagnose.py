#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script to identify routing and Clerk configuration issues
"""

import os
import sys

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, check=False, capture_output=True)
    except:
        pass
    
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("="*70)
print("  MONETA - System Diagnostic")
print("="*70)

# Check 1: Working Directory
print("\n[1] Working Directory")
cwd = os.getcwd()
print(f"    Current: {cwd}")
if cwd.endswith('Moneta2'):
    print("    ✅ Correct directory")
else:
    print("    ⚠️  WARNING: You might be in the wrong directory")
    print("       Expected to end with 'Moneta2'")

# Check 2: Required Files
print("\n[2] Required Files")
required_files = {
    'run.py': 'Main application entry point',
    'config.py': 'Configuration file',
    'app/__init__.py': 'Flask app factory',
    'templates/landing_clerk.html': 'Clerk landing page',
    'templates/landing.html': 'Legacy landing page',
}

all_files_exist = True
for file, desc in required_files.items():
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    print(f"    {status} {file:30s} - {desc}")
    if not exists:
        all_files_exist = False

# Check 3: Environment Variables
print("\n[3] Environment Variables")
env_exists = os.path.exists('.env')
print(f"    .env file exists: {'✅' if env_exists else '❌'}")

if env_exists:
    from dotenv import load_dotenv
    load_dotenv()
    
    env_vars = {
        'CLERK_SECRET_KEY': 'Clerk authentication',
        'CLERK_PUBLISHABLE_KEY': 'Clerk frontend',
        'SUPABASE_URL': 'Database connection',
        'SUPABASE_KEY': 'Database access',
        'OPENAI_API_KEY': 'AI chat',
        'JWT_SECRET': 'Session security',
    }
    
    for var, desc in env_vars.items():
        value = os.getenv(var)
        has_value = bool(value and value.strip())
        status = "✅" if has_value else "⚠️ "
        print(f"    {status} {var:25s} - {desc}")
        if has_value:
            # Show preview of key
            if len(value) > 10:
                print(f"        Preview: {value[:15]}...{value[-5:]}")
else:
    print("    ❌ .env file not found!")
    print("    → Run: python setup_env.py")

# Check 4: Can Import Flask App
print("\n[4] Flask App Import")
try:
    from app import create_app
    print("    ✅ Successfully imported create_app")
    
    print("\n[5] Flask App Creation")
    app = create_app()
    print("    ✅ Successfully created app instance")
    
    print("\n[6] Registered Routes")
    routes = list(app.url_map.iter_rules())
    print(f"    Total routes: {len(routes)}")
    
    # Check for key routes
    key_routes = {
        '/': 'Landing page',
        '/hello': 'Test route',
        '/debug': 'Debug info',
        '/dashboard': 'User dashboard',
        '/api/clerk/config': 'Clerk config endpoint',
    }
    
    route_paths = [rule.rule for rule in routes]
    for route, desc in key_routes.items():
        exists = route in route_paths
        status = "✅" if exists else "❌"
        print(f"    {status} {route:25s} - {desc}")
    
except Exception as e:
    print(f"    ❌ Error: {e}")
    print(f"    Error type: {type(e).__name__}")
    import traceback
    print(f"\n    Traceback:")
    traceback.print_exc()

# Check 7: Clerk Configuration
print("\n[7] Clerk Configuration")
try:
    from dotenv import load_dotenv
    load_dotenv()
    clerk_secret = os.getenv('CLERK_SECRET_KEY')
    clerk_pub = os.getenv('CLERK_PUBLISHABLE_KEY')
    
    if clerk_secret and clerk_pub:
        print("    ✅ Clerk keys are configured")
        print(f"    Secret key starts with: {clerk_secret[:10] if clerk_secret else 'N/A'}")
        print(f"    Pub key starts with: {clerk_pub[:10] if clerk_pub else 'N/A'}")
        
        # Validate key formats
        valid_secret = clerk_secret.startswith(('sk_test_', 'sk_live_'))
        valid_pub = clerk_pub.startswith(('pk_test_', 'pk_live_'))
        
        if valid_secret and valid_pub:
            print("    ✅ Key formats look correct")
        else:
            if not valid_secret:
                print("    ⚠️  Secret key format looks wrong (should start with sk_test_ or sk_live_)")
            if not valid_pub:
                print("    ⚠️  Publishable key format looks wrong (should start with pk_test_ or pk_live_)")
    else:
        print("    ⚠️  Clerk keys not configured")
        print("    → Run: python setup_env.py")
except Exception as e:
    print(f"    ❌ Error checking Clerk: {e}")

# Summary
print("\n" + "="*70)
print("  SUMMARY")
print("="*70)

issues = []
if not all_files_exist:
    issues.append("Missing required files")
if not env_exists:
    issues.append("Missing .env file")
if not (os.getenv('CLERK_SECRET_KEY') and os.getenv('CLERK_PUBLISHABLE_KEY')):
    issues.append("Clerk not configured")

if issues:
    print("\n⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"    - {issue}")
    print("\n📝 RECOMMENDED ACTIONS:")
    print("    1. Run: python setup_env.py")
    print("    2. Add your Clerk keys from https://dashboard.clerk.com/")
    print("    3. Run: python test_routes.py")
    print("    4. If test passes, run: python run.py")
else:
    print("\n✅ ALL CHECKS PASSED!")
    print("\n🚀 READY TO RUN:")
    print("    python test_routes.py    # Test routes first")
    print("    python run.py            # Run main server")

print("\n" + "="*70 + "\n")

