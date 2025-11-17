#!/usr/bin/env python3
"""
Moneta - AI Memory Management System
Flask Application Factory
"""

import os
from flask import Flask
from config import config


def create_app():
    """Create and configure the Flask application"""
    # Get the base directory (Moneta2 folder)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'app', 'static')
    
    print(f"[DEBUG] Base directory: {base_dir}")
    print(f"[DEBUG] Template directory: {template_dir}")
    print(f"[DEBUG] Static directory: {static_dir}")
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path='/static')
    app.secret_key = config.jwt_secret
    
    # Register blueprints
    print("[DEBUG] Importing blueprints...")
    from app.blueprints.auth import auth_bp
    from app.blueprints.clerk_auth import clerk_auth_bp
    from app.blueprints.chat import chat_bp
    from app.blueprints.memory import memory_bp
    from app.blueprints.subscription import subscription_bp
    from app.blueprints.main import main_bp
    
    print("[DEBUG] Registering main_bp...")
    app.register_blueprint(main_bp)
    print(f"[DEBUG] main_bp routes: {[rule.rule for rule in app.url_map.iter_rules() if 'main' in rule.endpoint]}")
    
    print("[DEBUG] Registering other blueprints...")
    app.register_blueprint(auth_bp, url_prefix='/api/auth')  # Legacy auth (backward compatibility)
    app.register_blueprint(clerk_auth_bp, url_prefix='/api/clerk')  # New Clerk auth
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(memory_bp, url_prefix='/api/memory')
    app.register_blueprint(subscription_bp, url_prefix='/api/subscription')
    
    print(f"[DEBUG] Total routes registered: {len(list(app.url_map.iter_rules()))}")
    print("[DEBUG] All routes:")
    for rule in app.url_map.iter_rules():
        print(f"  - {rule.rule} -> {rule.endpoint}")
    
    print("[INFO] Starting Moneta - AI Memory Management System...")
    print("[INFO] Open your browser and go to: http://localhost:4000")
    
    # Initialize memory system if available
    if config.memory_available:
        print("[OK] Memory search system is ready!")
        from app.utils.file_watcher import setup_file_watcher
        setup_file_watcher(config.memory_manager, config.memory_json_path)
    else:
        print("[WARN] Memory search system is not available")
    
    return app

