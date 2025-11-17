#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clerk Configuration Diagnostic Tool
Run this to check if your Clerk setup is correct
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass

def diagnose_clerk():
    print("=" * 60)
    print("   CLERK CONFIGURATION DIAGNOSTIC")
    print("=" * 60)
    print()
    
    # Load environment variables
    load_dotenv()
    
    # Check for Clerk keys
    clerk_secret = os.getenv('CLERK_SECRET_KEY')
    clerk_pub = os.getenv('CLERK_PUBLISHABLE_KEY')
    
    print("1. ENVIRONMENT VARIABLES CHECK")
    print("-" * 60)
    
    if clerk_secret:
        print(f"[OK] CLERK_SECRET_KEY: Present (starts with: {clerk_secret[:15]}...)")
        if not clerk_secret.startswith('sk_'):
            print("   [WARN] Secret key should start with 'sk_test_' or 'sk_live_'")
    else:
        print("[X] CLERK_SECRET_KEY: Missing")
        print("   Add this to your .env file from Clerk Dashboard > API Keys")
    
    print()
    
    if clerk_pub:
        print(f"[OK] CLERK_PUBLISHABLE_KEY: Present (starts with: {clerk_pub[:15]}...)")
        if not clerk_pub.startswith('pk_'):
            print("   [WARN] Publishable key should start with 'pk_test_' or 'pk_live_'")
    else:
        print("[X] CLERK_PUBLISHABLE_KEY: Missing")
        print("   Add this to your .env file from Clerk Dashboard > API Keys")
    
    print()
    print("2. CLERK REST API CHECK")
    print("-" * 60)
    
    if clerk_secret:
        try:
            from app.core.clerk_rest_api import get_clerk_rest_api
            clerk_api = get_clerk_rest_api()
            print("[OK] Clerk REST API initialized successfully")
            print(f"   Backend URL: {clerk_api.base_url}")
        except Exception as e:
            print(f"[X] Failed to initialize Clerk REST API")
            print(f"   Error: {e}")
    else:
        print("[SKIP] Skipped (no secret key)")
    
    print()
    print("3. FRONTEND CLERK SDK CHECK")
    print("-" * 60)
    
    # Check if landing_clerk.html exists
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'landing_clerk.html')
    
    if os.path.exists(template_path):
        print("[OK] landing_clerk.html template exists")
        
        # Check if it loads Clerk script
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '@clerk/clerk-js' in content or 'clerk.browser.js' in content:
            print("[OK] Clerk JavaScript SDK is loaded in template")
        else:
            print("[X] Clerk JavaScript SDK not found in template")
            
        if '/api/clerk/config' in content:
            print("[OK] Template fetches Clerk config from backend")
        else:
            print("[WARN] Template doesn't fetch config from backend")
    else:
        print(f"[X] Template not found at: {template_path}")
    
    print()
    print("4. ROUTES CHECK")
    print("-" * 60)
    
    try:
        from app import create_app
        app = create_app()
        
        clerk_routes = [rule for rule in app.url_map.iter_rules() if 'clerk' in rule.rule]
        
        if clerk_routes:
            print(f"[OK] Found {len(clerk_routes)} Clerk routes:")
            for route in clerk_routes:
                print(f"   - {route.rule} ({', '.join(route.methods - {'HEAD', 'OPTIONS'})})")
        else:
            print("[X] No Clerk routes found")
    except Exception as e:
        print(f"[X] Error checking routes: {e}")
    
    print()
    print("5. RECOMMENDATION")
    print("=" * 60)
    
    if clerk_secret and clerk_pub:
        print("[OK] Your Clerk configuration looks good!")
        print()
        print("Next steps:")
        print("1. Run: python run.py")
        print("2. Open: http://localhost:4000")
        print("3. Click 'Sign in with Google'")
        print("4. Check browser console (F12) for any errors")
        print()
        print("Common issues:")
        print("- Make sure your Clerk dashboard has:")
        print("  * Google OAuth enabled")
        print("  * Authorized domain: http://localhost:4000")
        print("  * Application URL set correctly")
    else:
        print("[X] Missing Clerk configuration")
        print()
        print("To fix:")
        print("1. Go to https://dashboard.clerk.com/")
        print("2. Navigate to API Keys")
        print("3. Copy your Publishable Key and Secret Key")
        print("4. Add them to your .env file:")
        print()
        print("   CLERK_SECRET_KEY=sk_test_...")
        print("   CLERK_PUBLISHABLE_KEY=pk_test_...")
        print()
        print("5. Re-run this diagnostic script")
    
    print("=" * 60)

if __name__ == '__main__':
    diagnose_clerk()

