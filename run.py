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
    
    # Get debug mode from environment (force True for development)
    debug = True  # Force debug mode for development
    
    print("=" * 60)
    print("   MONETA - AI Memory Management System")
    print("=" * 60)
    print(f"   Server: http://localhost:{port}")
    print(f"   Debug Mode: {debug}")
    print("=" * 60)
    
    # Run the application
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port
    )

