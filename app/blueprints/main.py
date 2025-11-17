#!/usr/bin/env python3
"""
Main routes blueprint - Landing pages, dashboard, and core UI routes
"""

from flask import Blueprint, render_template, render_template_string

main_bp = Blueprint('main', __name__)


@main_bp.route('/hello')
def hello():
    """Simple test route to verify routes are loading"""
    return "Hello! Routes are working!"


@main_bp.route('/')
def index():
    """Main page route - Landing page with Clerk authentication"""
    # Check if Clerk is configured
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    from flask import jsonify
    
    # Get the absolute path to .env file
    # Go up from app/blueprints/main.py to the Moneta2 directory
    base_dir = Path(__file__).resolve().parent.parent.parent
    env_file = base_dir / '.env'
    
    # Force reload environment variables with explicit path
    load_dotenv(env_file, override=True)
    
    clerk_key = os.getenv('CLERK_SECRET_KEY')
    clerk_pub = os.getenv('CLERK_PUBLISHABLE_KEY')
    
    print(f"[DEBUG] Route '/' called")
    print(f"[DEBUG] .env file path: {env_file}")
    print(f"[DEBUG] .env file exists: {env_file.exists()}")
    print(f"[DEBUG] CLERK_SECRET_KEY present: {bool(clerk_key)}")
    print(f"[DEBUG] CLERK_SECRET_KEY preview: {clerk_key[:20] if clerk_key else 'None'}...")
    print(f"[DEBUG] CLERK_PUBLISHABLE_KEY present: {bool(clerk_pub)}")
    print(f"[DEBUG] CLERK_PUBLISHABLE_KEY preview: {clerk_pub[:20] if clerk_pub else 'None'}...")
    
    # Validate Clerk keys
    if clerk_key and clerk_pub:
        # Check if keys look valid
        if not clerk_key.startswith('sk_'):
            print(f"[ERROR] CLERK_SECRET_KEY is invalid - should start with 'sk_test_' or 'sk_live_'")
            return f"""
            <html>
            <body style="background: #1a1a1a; color: white; font-family: Arial; padding: 50px; text-align: center;">
                <h1>⚠️ Clerk Configuration Error</h1>
                <p style="font-size: 18px;">CLERK_SECRET_KEY is invalid</p>
                <p>Secret key should start with <code>sk_test_</code> or <code>sk_live_</code></p>
                <p>Current value starts with: <code>{clerk_key[:20]}...</code></p>
                <hr style="margin: 30px 0;">
                <p>Fix your .env file and restart the server</p>
            </body>
            </html>
            """, 500
        
        if not clerk_pub.startswith('pk_'):
            print(f"[ERROR] CLERK_PUBLISHABLE_KEY is invalid - should start with 'pk_test_' or 'pk_live_'")
            return f"""
            <html>
            <body style="background: #1a1a1a; color: white; font-family: Arial; padding: 50px; text-align: center;">
                <h1>⚠️ Clerk Configuration Error</h1>
                <p style="font-size: 18px;">CLERK_PUBLISHABLE_KEY is invalid</p>
                <p>Publishable key should start with <code>pk_test_</code> or <code>pk_live_</code></p>
                <p>Current value starts with: <code>{clerk_pub[:20]}...</code></p>
                <hr style="margin: 30px 0;">
                <p>Fix your .env file and restart the server</p>
            </body>
            </html>
            """, 500
        
        print(f"[DEBUG] ✓ Serving: landing_clerk.html (Clerk authentication)")
        return render_template('landing_clerk.html')
    
    elif clerk_key or clerk_pub:
        # Only one key is present
        print(f"[ERROR] Incomplete Clerk configuration")
        return f"""
        <html>
        <body style="background: #1a1a1a; color: white; font-family: Arial; padding: 50px; text-align: center;">
            <h1>⚠️ Incomplete Clerk Configuration</h1>
            <p style="font-size: 18px;">You need BOTH keys in your .env file:</p>
            <ul style="text-align: left; max-width: 500px; margin: 30px auto;">
                <li>CLERK_SECRET_KEY: {'✓ Present' if clerk_key else '✗ Missing'}</li>
                <li>CLERK_PUBLISHABLE_KEY: {'✓ Present' if clerk_pub else '✗ Missing'}</li>
            </ul>
            <hr style="margin: 30px 0;">
            <p>Add both keys to .env and restart the server</p>
        </body>
        </html>
        """, 500
    
    else:
        print(f"[DEBUG] ✗ No Clerk keys found, serving: landing.html (legacy authentication)")
        # Fallback to legacy landing page
        return render_template('landing.html')


@main_bp.route('/dashboard')
def dashboard():
    """Dashboard route - User dashboard (requires authentication)"""
    try:
        from app.core.auth_system import get_auth_system
        auth_system, _ = get_auth_system()
        return render_template('dashboard.html')
    except Exception as e:
        print(f"Error in dashboard: {e}")
        return render_template('dashboard.html')


@main_bp.route('/chat')
def chat_interface():
    """Chat interface route (requires authentication)"""
    try:
        from app.core.auth_system import get_auth_system
        from app.core.chat_interface import CHAT_INTERFACE_TEMPLATE
        from app.core.memory_network_ui import MEMORY_NETWORK_UI_TEMPLATE, MEMORY_NETWORK_CSS
        from app.core.chat_javascript import CHAT_JAVASCRIPT
        from app.core.memory_network_javascript import MEMORY_NETWORK_JAVASCRIPT
        from config import config
        
        auth_system, _ = get_auth_system()
        
        # Inject Clerk publishable key from config (don't hardcode it in template)
        template_with_key = CHAT_INTERFACE_TEMPLATE.replace(
            'data-clerk-publishable-key="pk_test_Z29sZGVuLW9wb3NzdW0tMzIuY2xlcmsuYWNjb3VudHMuZGV2JA"',
            f'data-clerk-publishable-key="{config.clerk_publishable_key}"'
        )
        
        # Create complete template
        complete_template = template_with_key.replace(
            '''            <!-- Memory Network Section -->
            <div id="memory-network-container">
                <!-- This will be populated by the memory network UI component -->
            </div>''',
            MEMORY_NETWORK_UI_TEMPLATE
        ).replace(
            '</head>',
            f'<style>{MEMORY_NETWORK_CSS}</style></head>'
        ).replace(
            '</body>',
            f'{CHAT_JAVASCRIPT}{MEMORY_NETWORK_JAVASCRIPT}</body>'
        )
        
        print("[Chat Route] Serving chat interface with Clerk authentication")
        print(f"[Chat Route] Clerk key: {config.clerk_publishable_key[:20]}...")
        
        return render_template_string(complete_template)
    except Exception as e:
        import traceback
        print(f"[ERROR] Error in chat interface: {e}")
        print(traceback.format_exc())
        # Return a basic error template
        return "Error loading chat interface. Check server logs.", 500


@main_bp.route('/subscription')
def subscription_page():
    """Subscription page route"""
    return render_template('subscription.html')


@main_bp.route('/debug')
def debug_auth():
    """Debug authentication route"""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    from flask import jsonify
    
    # Get the absolute path to .env file
    base_dir = Path(__file__).resolve().parent.parent.parent
    env_file = base_dir / '.env'
    
    # Force reload environment variables
    load_dotenv(env_file, override=True)
    
    clerk_secret = os.getenv('CLERK_SECRET_KEY')
    clerk_pub = os.getenv('CLERK_PUBLISHABLE_KEY')
    
    return jsonify({
        'env_file_path': str(env_file),
        'env_file_exists': env_file.exists(),
        'clerk_secret_present': bool(clerk_secret),
        'clerk_secret_preview': clerk_secret[:20] if clerk_secret else None,
        'clerk_pub_present': bool(clerk_pub),
        'clerk_pub_preview': clerk_pub[:20] if clerk_pub else None,
        'which_template_should_serve': 'landing_clerk.html' if (clerk_secret and clerk_pub) else 'landing.html',
        'message': 'Check this at /debug to see what Flask sees'
    })


@main_bp.route('/test-clerk')
def test_clerk_page():
    """Force serve the Clerk landing page for testing"""
    return render_template('landing_clerk.html')


@main_bp.route('/test-legacy')
def test_legacy_page():
    """Force serve the legacy landing page for testing"""
    return render_template('landing.html')



