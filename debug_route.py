#!/usr/bin/env python3
"""Debug script to check what landing page is being served"""

import os
from dotenv import load_dotenv

load_dotenv()

# Check environment variable
clerk_secret = os.getenv('CLERK_SECRET_KEY')
clerk_pub = os.getenv('CLERK_PUBLISHABLE_KEY')

print("=" * 60)
print("DEBUG: Landing Page Route Logic")
print("=" * 60)

print(f"\nCLERK_SECRET_KEY found: {bool(clerk_secret)}")
print(f"CLERK_PUBLISHABLE_KEY found: {bool(clerk_pub)}")

if clerk_secret:
    print(f"Value: {clerk_secret[:20]}...")

print("\n" + "=" * 60)
print("Route logic in main.py:")
print("=" * 60)

if os.getenv('CLERK_SECRET_KEY'):
    print("✓ Condition TRUE: Should serve 'landing_clerk.html'")
else:
    print("✗ Condition FALSE: Will serve 'landing.html' (legacy)")

print("=" * 60)

# Check if templates exist
import os.path
clerk_template = os.path.join('templates', 'landing_clerk.html')
legacy_template = os.path.join('templates', 'landing.html')

print(f"\nTemplate files:")
print(f"  landing_clerk.html exists: {os.path.exists(clerk_template)}")
print(f"  landing.html exists: {os.path.exists(legacy_template)}")


