#!/usr/bin/env python3
"""
Simple startup script with better error handling
"""

import sys
import os

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

print("=" * 80)
print("STARTING MONETA SERVER")
print("=" * 80)
print(f"Working directory: {os.getcwd()}")
print()

try:
    # Import and run
    from run import app
    
    port = 4000
    print(f"Starting server on http://localhost:{port}")
    print("=" * 80)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
    
except Exception as e:
    print(f"\n\n{'='*80}")
    print("ERROR STARTING SERVER")
    print("=" * 80)
    print(f"Error: {e}")
    print()
    import traceback
    traceback.print_exc()
    print("=" * 80)
    sys.exit(1)

