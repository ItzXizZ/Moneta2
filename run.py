#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moneta - AI Memory Management System
Application Entry Point
"""

import os
import sys

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    # Set console code page to UTF-8
    try:
        import subprocess
        subprocess.run(['chcp', '65001'], shell=True, check=False, capture_output=True)
    except:
        pass
    
    # Force UTF-8 for stdin/stdout/stderr
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    if sys.stdin.encoding != 'utf-8':
        sys.stdin.reconfigure(encoding='utf-8', errors='replace')

# Set environment variable for Python
os.environ['PYTHONIOENCODING'] = 'utf-8'

from app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Get port from environment variable (for cloud deployment) or use default
    port = int(os.environ.get('PORT', 4000))
    
    # Get debug mode from environment (defaults to False for production safety)
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Check if we're in production
    is_production = os.environ.get('ENVIRONMENT', 'development').lower() == 'production'
    
    print("=" * 60)
    print("   MONETA - AI Memory Management System")
    print("=" * 60)
    print(f"   Server: http://localhost:{port}")
    print(f"   Debug Mode: {debug}")
    print(f"   Environment: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")
    print("=" * 60)
    
    if is_production:
        print("\n⚠️  WARNING: Running Flask dev server in production!")
        print("   For production, use: gunicorn --bind 0.0.0.0:4000 run:app")
        print("=" * 60 + "\n")
    
    # Run the application
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port
    )

