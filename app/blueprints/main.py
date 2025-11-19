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
        return render_template('landing_clerk.html', clerk_publishable_key=clerk_pub)
    
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


@main_bp.route('/privacy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('privacy.html')


@main_bp.route('/terms')
def terms_of_service():
    """Terms of Service page"""
    return render_template('terms.html')


@main_bp.route('/anonymous')
def anonymous_mode():
    """Anonymous mode - No authentication required, uses localStorage"""
    from flask import render_template_string
    from app.core.memory_network_ui import MEMORY_NETWORK_UI_TEMPLATE, MEMORY_NETWORK_CSS
    from app.core.memory_network_javascript import MEMORY_NETWORK_JAVASCRIPT
    
    # Create anonymous chat template with real memory network
    ANONYMOUS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moneta - Anonymous Mode</title>
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        /* Include all the chat interface styles from authenticated version */
        :root {
            --primary-50: #faf5ff;
            --primary-100: #f3e8ff;
            --primary-200: #e9d5ff;
            --primary-300: #d8b4fe;
            --primary-400: #c084fc;
            --primary-500: #a855f7;
            --primary-600: #9333ea;
            --primary-700: #7c3aed;
            --primary-800: #6b21a8;
            --primary-900: #581c87;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            --gray-950: #0a0a0a;
            --glass-bg: rgba(255, 255, 255, 0.08);
            --glass-bg-strong: rgba(255, 255, 255, 0.12);
            --glass-bg-subtle: rgba(255, 255, 255, 0.04);
            --glass-border: rgba(255, 255, 255, 0.15);
            --glass-border-strong: rgba(255, 255, 255, 0.25);
            --glass-blur: blur(24px);
            --glass-blur-strong: blur(32px);
            --glow-primary: 0 0 32px rgba(168, 85, 247, 0.25);
            --glow-secondary: 0 0 64px rgba(168, 85, 247, 0.12);
            --shadow-glass: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05);
            --shadow-floating: 0 20px 40px -12px rgba(0, 0, 0, 0.4);
            --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
            --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
            --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        * { box-sizing: border-box; }
        body {
            background: radial-gradient(ellipse at center, rgba(10, 10, 10, 0.98) 0%, rgba(17, 24, 39, 0.95) 60%, rgba(5, 5, 5, 0.99) 100%),
                radial-gradient(circle at 20% 20%, rgba(255, 215, 0, 0.02) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(168, 85, 247, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 40% 70%, rgba(255, 215, 0, 0.01) 0%, transparent 30%),
                radial-gradient(circle at 60% 30%, rgba(168, 85, 247, 0.02) 0%, transparent 40%);
            background-attachment: fixed;
            color: var(--gray-100);
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
            font-weight: 400;
            line-height: 1.5;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 10% 90%, rgba(168, 85, 247, 0.015) 0%, transparent 40%),
                radial-gradient(circle at 90% 10%, rgba(255, 215, 0, 0.01) 0%, transparent 30%);
            pointer-events: none;
            z-index: -1;
        }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: var(--glass-bg-strong); border-radius: 4px; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: var(--glass-blur); }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.15); border-color: rgba(255, 255, 255, 0.2); }
        .container { position: relative; width: 100vw; height: 100vh; padding: 0; margin: 0; overflow: visible; display: flex; flex-direction: row; }
        .main-content { position: relative; width: 100%; height: 100%; display: flex; pointer-events: none; }
        .chat-container {
            position: fixed; top: 20px; left: 20px; bottom: 20px; width: 500px; height: calc(100vh - 40px);
            display: flex; flex-direction: column; background: transparent; border: none; border-radius: 0;
            overflow: hidden; box-shadow: none; pointer-events: auto; z-index: 1000;
            transition: left 0.3s cubic-bezier(0.4,0,0.2,1), width 0.3s cubic-bezier(0.4,0,0.2,1); margin-right: 12px;
        }
        .chat-header { background: transparent; backdrop-filter: none; padding: 0 0 10px 0; border-bottom: none;
            position: relative; text-align: center; flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
        .chat-header h2 { margin: 0; color: rgba(255, 255, 255, 0.5); font-size: 0.875rem; font-weight: 400;
            letter-spacing: 0.1em; text-transform: uppercase; position: relative; flex: 1; text-align: center; }
        .header-buttons { display: flex; gap: 8px; align-items: center; }
        .home-btn { background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px; padding: 10px 12px; color: rgba(255, 255, 255, 0.7); font-weight: 400; font-size: 0.75rem;
            letter-spacing: 0.02em; cursor: pointer; transition: all 0.2s ease; text-decoration: none; display: inline-block; }
        .home-btn:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); color: rgba(255, 255, 255, 1); }
        .reset-btn { background: rgba(239, 68, 68, 0.1); backdrop-filter: blur(20px); border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 6px; padding: 10px 12px; color: rgba(239, 68, 68, 0.9); font-weight: 400; font-size: 0.75rem;
            letter-spacing: 0.02em; cursor: pointer; transition: all 0.2s ease; text-decoration: none; display: inline-block; }
        .reset-btn:hover { background: rgba(239, 68, 68, 0.2); border-color: rgba(239, 68, 68, 0.5); color: rgba(255, 255, 255, 1); transform: scale(1.05); }
        .chat-messages { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 10px; height: calc(100vh - 160px);
            scroll-behavior: smooth; -webkit-overflow-scrolling: touch; scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, 0.2) transparent; }
        .message { background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px; padding: 20px 24px; max-width: 85%; position: relative; transition: all 0.4s var(--ease-smooth);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 4px 16px rgba(168, 85, 247, 0.1);
            overflow: hidden; margin: 15px 0; opacity: 0; transform: scale(0.8) translateY(20px); animation: messagePopIn 0.3s ease-out forwards; width: fit-content; }
        @keyframes messagePopIn { 0% { opacity: 0; transform: scale(0.8) translateY(20px); } 100% { opacity: 1; transform: scale(1) translateY(0); } }
        .message::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 50%, transparent 100%);
            pointer-events: none; border-radius: 20px; }
        .message:hover { transform: translateY(-2px) scale(1.02); box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.25),
            inset 0 1px 0 rgba(255, 255, 255, 0.3), 0 8px 32px rgba(168, 85, 247, 0.2); border-color: rgba(255, 255, 255, 0.3); backdrop-filter: blur(24px); }
        .message.user { float: right; clear: both; background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(147, 51, 234, 0.1));
            backdrop-filter: blur(20px); border-color: rgba(168, 85, 247, 0.3); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 0 1px rgba(168, 85, 247, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.25), 0 4px 20px rgba(168, 85, 247, 0.15);
            animation: messagePopIn 0.2s ease-out forwards; }
        .message.user::before { background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(168, 85, 247, 0.05) 50%, transparent 100%); }
        .message.user:hover { box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(168, 85, 247, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 8px 40px rgba(168, 85, 247, 0.3); border-color: rgba(168, 85, 247, 0.5); }
        .message.assistant { float: left; clear: both; background: rgba(255, 255, 255, 0.08); animation: messagePopIn 0.3s ease-out forwards; animation-delay: 0.1s; }
        .message-content { margin: 0; word-wrap: break-word; white-space: pre-wrap; }
        .chat-input-container { padding: 5px 16px 10px 0; border-top: none; background: transparent; backdrop-filter: none;
            width: 92%; margin-top: auto; flex-shrink: 0; position: sticky; bottom: 0; z-index: 100; }
        .chat-input-form { display: flex; gap: 12px; padding-right: 16px; justify-content: center; }
        .chat-input { width: 75%; flex: none; max-width: 420px; background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 20px; padding: 18px 24px; color: rgba(255, 255, 255, 0.95);
            font-size: 1rem; transition: all 0.4s var(--ease-smooth); resize: none; min-height: 60px; max-height: 150px;
            font-family: inherit; line-height: 1.5; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.2), inset 0 2px 8px rgba(0, 0, 0, 0.1); }
        .chat-input::placeholder { color: rgba(255, 255, 255, 0.4); }
        .chat-input:focus { outline: none; border-color: rgba(168, 85, 247, 0.4); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 0 2px rgba(168, 85, 247, 0.2), 0 0 0 1px rgba(168, 85, 247, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.25),
            inset 0 2px 8px rgba(0, 0, 0, 0.15); background: rgba(255, 255, 255, 0.12); transform: translateY(-1px) scale(1.01); backdrop-filter: blur(24px); }
        .send-button { background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px; padding: 18px 20px; color: rgba(255, 255, 255, 0.9); font-size: 0.8rem; font-weight: 500;
            cursor: pointer; transition: all 0.4s var(--ease-smooth); box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2),
            0 0 0 1px rgba(255, 255, 255, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.2); position: relative; overflow: hidden;
            white-space: nowrap; max-width: 8vw; min-width: 70px; flex-shrink: 0; }
        .send-button::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(168, 85, 247, 0.05) 50%, transparent 100%);
            opacity: 0; transition: opacity 0.4s var(--ease-smooth); pointer-events: none; border-radius: 20px; }
        .send-button:hover { background: rgba(168, 85, 247, 0.12); border-color: rgba(168, 85, 247, 0.3);
            color: rgba(255, 255, 255, 1); transform: translateY(-2px) scale(1.02); box-shadow: 0 8px 32px rgba(168, 85, 247, 0.3),
            0 0 0 1px rgba(168, 85, 247, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.25); backdrop-filter: blur(24px); }
        .send-button:hover::before { opacity: 1; }
        .send-button:active { transform: translateY(-1px); }
        .send-button:disabled { opacity: 0.5; cursor: not-allowed; }
        .empty-state { text-align: center; color: var(--gray-400); font-style: italic; padding: 40px; clear: both; width: 100%; }
        .chat-messages::after { content: ""; display: table; clear: both; }
        ''' + MEMORY_NETWORK_CSS + '''
    </style>
</head>
<body>
    <div class="container">
        <div class="main-content">
            ''' + MEMORY_NETWORK_UI_TEMPLATE + '''
            <div class="chat-container">
                <div class="chat-header">
                    <h2 id="thread-title">Anonymous Chat</h2>
                    <div class="header-buttons">
                        <button class="reset-btn" onclick="resetAnonymousMode()">Reset</button>
                        <a href="/" class="home-btn">Home</a>
                    </div>
                </div>
                <div class="chat-messages" id="chat-messages">
                    <div class="empty-state">Start a conversation... (AI powered, localStorage persistence)</div>
                </div>
                <div class="chat-input-container">
                    <div class="chat-input-form" id="chat-form">
                        <textarea class="chat-input" id="chat-input" placeholder="Type your message here..." rows="1"></textarea>
                        <button type="button" class="send-button" id="send-button">Send</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        // Override authentication check for anonymous mode but enable memory network
        function isAuthenticated() { return false; }
        
        // Keep reference to actual memory network from included script
        let actualMemoryNetwork = null;
        let actualNetworkData = { nodes: [], edges: [] };
        let anonNodeGlowLevels = {};
        let anonGlowDecayInterval = null;
        
        // Anonymous chat with AI backend and memory network
        const STORAGE_KEY = 'moneta_anonymous_chat';
        const MEMORY_KEY = 'moneta_anonymous_memories';
        let isSending = false;
        let anonymousMemories = [];
        
        function loadChatHistory() {
            const history = localStorage.getItem(STORAGE_KEY);
            if (history) {
                try {
                    const messages = JSON.parse(history);
                    const chatMessages = document.getElementById('chat-messages');
                    chatMessages.innerHTML = '';
                    messages.forEach(msg => appendMessage(msg.content, msg.isUser, false));
                    scrollToBottom();
                } catch (e) { console.error('Error loading chat history:', e); }
            }
        }
        
        function saveChatHistory() {
            const messages = [];
            document.querySelectorAll('.message').forEach(el => {
                messages.push({
                    content: el.querySelector('.message-content').textContent,
                    isUser: el.classList.contains('user')
                });
            });
            localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
        }
        
        function loadMemories() {
            const stored = localStorage.getItem(MEMORY_KEY);
            if (stored) {
                try {
                    anonymousMemories = JSON.parse(stored);
                    console.log(`Loaded ${anonymousMemories.length} memories from localStorage`);
                    initializeAnonymousNetwork();
                } catch (e) { console.error('Error loading memories:', e); }
            }
        }
        
        function saveMemories() {
            localStorage.setItem(MEMORY_KEY, JSON.stringify(anonymousMemories));
        }
        
        function addMemoriesToNetwork(memories) {
            if (!memories || memories.length === 0) return;
            
            memories.forEach(memory => {
                anonymousMemories.push(memory);
                console.log(`Added memory to network: ${memory.content}`);
            });
            
            saveMemories();
            initializeAnonymousNetwork();
        }
        
        function appendMessage(content, isUser, save = true) {
            const chatMessages = document.getElementById('chat-messages');
            const emptyState = chatMessages.querySelector('.empty-state');
            if (emptyState) emptyState.remove();
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            messageDiv.appendChild(contentDiv);
            chatMessages.appendChild(messageDiv);
            scrollToBottom();
            if (save) saveChatHistory();
        }
        
        function scrollToBottom() {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function getConversationHistory() {
            const messages = [];
            document.querySelectorAll('.message').forEach(el => {
                messages.push({
                    content: el.querySelector('.message-content').textContent,
                    isUser: el.classList.contains('user')
                });
            });
            return messages;
        }
        
        function initializeAnonymousNetwork() {
            const container = document.getElementById('memory-network');
            if (!container) return;
            
            if (anonymousMemories.length === 0) {
                console.log('No memories to display yet');
                return;
            }
            
            // Build network data from memories with production-level styling
            const allScores = anonymousMemories.map(m => m.score || 1.0);
            const nodes = anonymousMemories.map((mem, index) => {
                const intensity = Math.max(0.7, Math.min(1, (mem.score || 1.0) / 100));
                const size = calculateProportionalNodeSize(mem.score || 1.0, allScores);
                
                return {
                    id: mem.id,
                    label: mem.content.length > 25 ? mem.content.substring(0, 25) + '…' : mem.content,
                    title: mem.content,
                    size: size,
                    color: {
                        background: `rgba(35,4,55,${intensity})`,
                        border: `rgba(255,255,255,${Math.min(0.4, intensity * 0.5)})`,
                        highlight: {
                            background: `rgba(70,9,107,${intensity})`,
                            border: 'rgba(255,255,255,0.8)'
                        },
                        hover: {
                            background: `rgba(50,6,80,${intensity})`,
                            border: 'rgba(255,255,255,0.6)'
                        }
                    },
                    font: {
                        size: Math.max(10, Math.min(14, 8 + size * 0.08)),
                        color: '#ffffff',
                        face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                        strokeWidth: 0,
                        strokeColor: 'transparent',
                        align: 'center'
                    },
                    borderWidth: 1,
                    borderWidthSelected: 2,
                    shadow: {
                        enabled: true,
                        color: 'rgba(17,24,39,0.6)',
                        size: 12,
                        x: 0,
                        y: 3
                    },
                    score: mem.score || 1.0,
                    tags: mem.tags || [],
                    content: mem.content,
                    created: mem.created || ''
                };
            });
            
            // Calculate simple similarity between memories for edges
            const edges = [];
            for (let i = 0; i < anonymousMemories.length; i++) {
                for (let j = i + 1; j < anonymousMemories.length; j++) {
                    const similarity = calculateSimpleSimilarity(
                        anonymousMemories[i].content,
                        anonymousMemories[j].content
                    );
                    if (similarity > 0.3) {
                        edges.push({
                            from: anonymousMemories[i].id,
                            to: anonymousMemories[j].id,
                            value: similarity,
                            width: Math.max(1, similarity * 6),
                            color: {
                                color: `rgba(168,85,247,${Math.max(0.2, similarity * 0.8)})`,
                                highlight: 'rgba(255,215,0,1)',
                                hover: 'rgba(255,215,0,0.8)'
                            },
                            smooth: {
                                type: 'curvedCW',
                                roundness: 0.2
                            },
                            title: `Similarity: ${similarity.toFixed(3)}`
                        });
                    }
                }
            }
            
            actualNetworkData = { nodes: nodes, edges: edges };
            
            // Use production-level options
            const options = {
                nodes: {
                    shape: 'dot',
                    scaling: { min: 20, max: 85 },
                    font: {
                        size: 11,
                        color: '#ffffff',
                        face: '-apple-system, SF Pro Display, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif',
                        strokeWidth: 0,
                        strokeColor: 'transparent',
                        align: 'center',
                        vadjust: 0,
                        multi: false
                    },
                    borderWidth: 1,
                    borderWidthSelected: 2,
                    shadow: {
                        enabled: true,
                        color: 'rgba(17,24,39,0.6)',
                        size: 12,
                        x: 0,
                        y: 3
                    },
                    margin: { top: 12, right: 12, bottom: 12, left: 12 },
                    chosen: {
                        node: function(values, id, selected, hovering) {
                            if (hovering) {
                                values.shadowSize = 12;
                                values.shadowColor = 'rgba(168,85,247,0.6)';
                                values.borderWidth = 2;
                            }
                        }
                    }
                },
                edges: {
                    width: 1.5,
                    color: { 
                        color: 'rgba(168,85,247,0.15)',
                        highlight: 'rgba(255,215,0,0.9)',
                        hover: 'rgba(255,215,0,0.7)'
                    },
                    smooth: {
                        type: 'curvedCW',
                        roundness: 0.2,
                        forceDirection: 'none'
                    },
                    shadow: {
                        enabled: true,
                        color: 'rgba(17,24,39,0.3)',
                        size: 6,
                        x: 0,
                        y: 2
                    },
                    length: 200,
                    scaling: { min: 1, max: 6 },
                    selectionWidth: 2,
                    hoverWidth: 2
                },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -1200,
                        centralGravity: 0.15,
                        springLength: 150,
                        springConstant: 0.02,
                        damping: 0.12,
                        avoidOverlap: 0.2
                    },
                    maxVelocity: 100,
                    minVelocity: 0.1,
                    solver: 'barnesHut',
                    stabilization: {
                        enabled: true,
                        iterations: 1500,
                        updateInterval: 35,
                        fit: true
                    },
                    adaptiveTimestep: false,
                    timestep: 0.3
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 150,
                    zoomView: true,
                    dragView: true,
                    dragNodes: true,
                    selectConnectedEdges: false,
                    hoverConnectedEdges: false,
                    keyboard: {
                        enabled: true,
                        speed: { x: 10, y: 10, zoom: 0.02 },
                        bindToWindow: false
                    },
                    multiselect: false,
                    navigationButtons: false,
                    zoomSpeed: 1.0
                },
                layout: {
                    improvedLayout: true,
                    clusterThreshold: 150,
                    hierarchical: false,
                    randomSeed: 2
                }
            };
            
            if (!actualMemoryNetwork) {
                actualMemoryNetwork = new vis.Network(container, actualNetworkData, options);
                console.log(`Initialized anonymous network with ${nodes.length} nodes (production styling)`);
                
                // Initialize glow levels for animation system
                nodes.forEach(node => {
                    anonNodeGlowLevels[node.id] = 0;
                });
                
                // Animate new nodes
                const newNodeIds = nodes.map(n => n.id);
                setTimeout(() => animateNewMemoryNodes(newNodeIds), 100);
            } else {
                actualMemoryNetwork.setData(actualNetworkData);
                console.log(`Updated anonymous network with ${nodes.length} nodes`);
                
                // Animate only truly new nodes
                const existingIds = new Set(Object.keys(anonNodeGlowLevels));
                const newNodeIds = nodes.filter(n => !existingIds.has(n.id)).map(n => n.id);
                
                // Initialize glow for new nodes
                newNodeIds.forEach(id => {
                    anonNodeGlowLevels[id] = 0;
                });
                
                if (newNodeIds.length > 0) {
                    setTimeout(() => animateNewMemoryNodes(newNodeIds), 100);
                }
            }
        }
        
        function calculateProportionalNodeSize(score, allScores) {
            if (!allScores || allScores.length === 0 || score === undefined || score === null) {
                return 35;
            }
            
            const validScores = allScores.filter(s => typeof s === 'number' && !isNaN(s) && s >= 0);
            if (validScores.length === 0) {
                return 35;
            }
            
            const minScore = Math.min(...validScores);
            const maxScore = Math.max(...validScores);
            
            if (minScore === maxScore) {
                return 35;
            }
            
            const logMin = Math.log(minScore + 1);
            const logMax = Math.log(maxScore + 1);
            const logScore = Math.log(score + 1);
            
            const relativePosition = (logScore - logMin) / (logMax - logMin);
            const sigmoid = 1 / (1 + Math.exp(-10 * (relativePosition - 0.5)));
            
            const minSize = 25;
            const maxSize = 80;
            const sizeRange = maxSize - minSize;
            
            const calculatedSize = minSize + (sigmoid * sizeRange);
            return Math.max(minSize, Math.min(maxSize, calculatedSize));
        }
        
        let globalVisitedNodes = new Set();
        let activeSignals = 0;
        
        function animateNewMemoryNodes(nodeIds) {
            nodeIds.forEach((nodeId, index) => {
                setTimeout(() => {
                    addNodeGlow(nodeId, 1.0);
                    createNodePulse(nodeId, 1.0);
                    createNodeVibration(nodeId, 1.0);
                    
                    const node = actualNetworkData.nodes.find(n => n.id === nodeId);
                    if (node) {
                        console.log(`✨ Animated new memory: ${node.label}`);
                    }
                }, index * 200);
            });
            
            // Start neural propagation after initial animations
            setTimeout(() => {
                createNeuralPropagationEffect(nodeIds);
            }, nodeIds.length * 200 + 300);
        }
        
        function createNeuralPropagationEffect(activatedMemoryIds) {
            globalVisitedNodes.clear();
            
            activatedMemoryIds.forEach((startNodeId, index) => {
                addNodeGlow(startNodeId, 1.0);
                createNodePulse(startNodeId, 1.0);
                createNodeVibration(startNodeId, 1.0);
            });
            
            activatedMemoryIds.forEach((startNodeId, index) => {
                setTimeout(() => {
                    propagateSignalFromNode(startNodeId, 0, new Set(), 1.0);
                }, index * 150);
            });
        }
        
        async function propagateSignalFromNode(currentNodeId, hopCount, visitedNodes, signalStrength) {
            if (hopCount >= 3 || signalStrength < 0.15 || globalVisitedNodes.has(currentNodeId)) {
                return;
            }
            
            const newVisited = new Set(visitedNodes);
            newVisited.add(currentNodeId);
            globalVisitedNodes.add(currentNodeId);
            
            addNodeGlow(currentNodeId, signalStrength);
            
            const neighbors = getConnectedNeighbors(currentNodeId);
            const unvisitedNeighbors = neighbors.filter(neighborId => !globalVisitedNodes.has(neighborId));
            
            if (unvisitedNeighbors.length === 0) {
                return;
            }
            
            const propagationPromises = unvisitedNeighbors.map((neighborId, index) => {
                return new Promise(resolve => {
                    setTimeout(async () => {
                        const newStrength = signalStrength * 0.85;
                        await animateSignalToNeighbor(currentNodeId, neighborId, newStrength, `hop-${hopCount}-${index}`, hopCount);
                        setTimeout(() => {
                            propagateSignalFromNode(neighborId, hopCount + 1, newVisited, newStrength);
                            resolve();
                        }, 50);
                    }, index * 75);
                });
            });
            
            await Promise.all(propagationPromises);
        }
        
        function getConnectedNeighbors(nodeId) {
            const neighbors = [];
            actualNetworkData.edges.forEach(edge => {
                if (edge.from === nodeId) {
                    neighbors.push(edge.to);
                } else if (edge.to === nodeId) {
                    neighbors.push(edge.from);
                }
            });
            return neighbors;
        }
        
        async function animateSignalToNeighbor(fromId, toId, strength, signalId, hopCount = 0) {
            return new Promise(resolve => {
                activeSignals++;
                
                const fadedStrength = strength * Math.pow(0.8, hopCount);
                const particle = createSignalParticle(fadedStrength, signalId);
                const container = document.getElementById('memory-network');
                const containerRect = container.getBoundingClientRect();
                
                const animationDuration = 100;
                const startTime = Date.now();
                const trail = [];
                
                const animate = () => {
                    const elapsed = Date.now() - startTime;
                    const progress = Math.min(elapsed / animationDuration, 1);
                    
                    const positions = actualMemoryNetwork.getPositions([fromId, toId]);
                    const fromPos = actualMemoryNetwork.canvasToDOM(positions[fromId]);
                    const toPos = actualMemoryNetwork.canvasToDOM(positions[toId]);
                    
                    const eased = easeInOutCubic(progress);
                    const { currentX, currentY } = getCurvedPathPosition(fromPos, toPos, eased, fromId, toId);
                    
                    particle.style.left = (containerRect.left + currentX) + 'px';
                    particle.style.top = (containerRect.top + currentY) + 'px';
                    
                    trail.push({ x: currentX, y: currentY, time: elapsed });
                    if (trail.length > 15) {
                        trail.shift();
                    }
                    
                    if (trail.length > 1) {
                        drawContinuousTrail(trail, fadedStrength, containerRect, signalId);
                    }
                    
                    const scale = fadedStrength * (1 + Math.sin(progress * Math.PI * 2) * 0.2);
                    particle.style.transform = `translate(-50%, -50%) scale(${scale})`;
                    particle.style.opacity = Math.max(0.2, fadedStrength * (Math.sin(progress * Math.PI) * 0.7 + 0.3));
                    
                    if (progress < 1) {
                        requestAnimationFrame(animate);
                    } else {
                        addNodeGlow(toId, fadedStrength);
                        createNodePulse(toId, fadedStrength);
                        createNodeVibration(toId, fadedStrength);
                        
                        particle.style.transition = 'all 0.4s ease-out';
                        particle.style.opacity = '0';
                        particle.style.transform = 'translate(-50%, -50%) scale(0)';
                        
                        setTimeout(() => {
                            particle.remove();
                            const trailElement = document.querySelector(`.continuous-trail-${signalId}`);
                            if (trailElement) {
                                trailElement.style.transition = 'opacity 0.3s ease-out';
                                trailElement.style.opacity = '0';
                                setTimeout(() => trailElement.remove(), 300);
                            }
                            activeSignals--;
                            resolve();
                        }, 400);
                    }
                };
                
                requestAnimationFrame(animate);
            });
        }
        
        function createSignalParticle(strength, signalId) {
            const particle = document.createElement('div');
            const size = Math.max(16, 32 * strength);
            const intensity = Math.max(0.7, strength);
            
            particle.className = `signal-particle-${signalId}`;
            particle.style.position = 'fixed';
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';
            particle.style.borderRadius = '50%';
            particle.style.background = `radial-gradient(circle, rgba(255, 255, 255, ${intensity}) 0%, rgba(255, 215, 0, ${intensity * 0.9}) 30%, rgba(255, 152, 0, ${intensity * 0.7}) 100%)`;
            particle.style.boxShadow = `0 0 ${size * 2}px rgba(255, 215, 0, ${intensity}), 0 0 ${size * 4}px rgba(255, 152, 0, ${intensity * 0.8}), 0 0 ${size * 6}px rgba(255, 215, 0, ${intensity * 0.4})`;
            particle.style.zIndex = '995';
            particle.style.pointerEvents = 'none';
            particle.style.transform = 'translate(-50%, -50%)';
            document.body.appendChild(particle);
            return particle;
        }
        
        function drawContinuousTrail(trail, strength, containerRect, signalId = 'default') {
            const existingTrail = document.querySelector(`.continuous-trail-${signalId}`);
            if (existingTrail) {
                existingTrail.remove();
            }
            
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.className = `continuous-trail continuous-trail-${signalId}`;
            svg.style.position = 'fixed';
            svg.style.top = '0';
            svg.style.left = '0';
            svg.style.width = '100vw';
            svg.style.height = '100vh';
            svg.style.pointerEvents = 'none';
            svg.style.zIndex = '990';
            document.body.appendChild(svg);
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            
            let pathData = '';
            trail.forEach((point, index) => {
                const x = containerRect.left + point.x;
                const y = containerRect.top + point.y;
                
                if (index === 0) {
                    pathData += `M ${x} ${y}`;
                } else {
                    pathData += ` L ${x} ${y}`;
                }
            });
            
            path.setAttribute('d', pathData);
            path.setAttribute('stroke', `rgba(255, 215, 0, ${strength * 0.8})`);
            path.setAttribute('stroke-width', Math.max(3, strength * 6));
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.style.filter = `drop-shadow(0 0 ${strength * 8}px rgba(255, 215, 0, ${strength * 0.6}))`;
            
            svg.appendChild(path);
            
            setTimeout(() => {
                if (svg.parentNode) {
                    svg.remove();
                }
            }, 150);
        }
        
        function createNodeVibration(nodeId, strength) {
            if (!actualMemoryNetwork) return;
            
            const positions = actualMemoryNetwork.getPositions([nodeId]);
            if (!positions[nodeId]) return;
            
            const nodePos = actualMemoryNetwork.canvasToDOM(positions[nodeId]);
            const container = document.getElementById('memory-network');
            const containerRect = container.getBoundingClientRect();
            
            const vibration = document.createElement('div');
            const node = actualNetworkData.nodes.find(n => n.id === nodeId);
            const nodeSize = node ? node.size : 35;
            
            const vibrationMultiplier = 1.0 + (strength * 0.8);
            const size = Math.max(nodeSize * vibrationMultiplier, 40);
            
            vibration.style.position = 'fixed';
            vibration.style.left = (containerRect.left + nodePos.x - size/2) + 'px';
            vibration.style.top = (containerRect.top + nodePos.y - size/2) + 'px';
            vibration.style.width = size + 'px';
            vibration.style.height = size + 'px';
            vibration.style.borderRadius = '50%';
            vibration.style.background = `radial-gradient(circle, rgba(255,255,255,${strength * 0.8}) 0%, rgba(255,215,0,${strength * 0.6}) 50%, transparent 100%)`;
            vibration.style.pointerEvents = 'none';
            vibration.style.zIndex = '994';
            vibration.style.opacity = Math.min(0.9, strength * 1.2);
            document.body.appendChild(vibration);

            const vibrationIntensity = Math.max(2, strength * 8);
            const vibrationDuration = Math.max(200, strength * 400);
            const vibrationSteps = 12;
            
            let step = 0;
            const vibrateInterval = setInterval(() => {
                if (step >= vibrationSteps) {
                    clearInterval(vibrateInterval);
                    vibration.style.transition = 'all 0.2s ease-out';
                    vibration.style.opacity = '0';
                    vibration.style.transform = 'scale(0.5)';
                    setTimeout(() => vibration.remove(), 200);
                    return;
                }
                
                const offsetX = (Math.random() - 0.5) * vibrationIntensity;
                const offsetY = (Math.random() - 0.5) * vibrationIntensity;
                const scale = 1 + (Math.random() - 0.5) * 0.3 * strength;
                
                vibration.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
                step++;
            }, vibrationDuration / vibrationSteps);
        }
        
        function easeInOutCubic(t) {
            return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        }
        
        function getCurvedPathPosition(fromPos, toPos, progress, fromId, toId) {
            const edge = actualNetworkData.edges.find(e => 
                (e.from === fromId && e.to === toId) || 
                (e.from === toId && e.to === fromId)
            );
            
            if (!edge) {
                const currentX = fromPos.x + (toPos.x - fromPos.x) * progress;
                const currentY = fromPos.y + (toPos.y - fromPos.y) * progress;
                return { currentX, currentY };
            }
            
            const dx = toPos.x - fromPos.x;
            const dy = toPos.y - fromPos.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            let curveDirection = -1;
            const isReversed = edge.from === toId;
            if (isReversed) {
                curveDirection = 1;
            }
            
            const roundness = 0.25;
            const curveOffset = distance * roundness * curveDirection;
            
            const perpX = -dy / distance;
            const perpY = dx / distance;
            
            const midX = (fromPos.x + toPos.x) / 2 + perpX * curveOffset;
            const midY = (fromPos.y + toPos.y) / 2 + perpY * curveOffset;
            
            const t = progress;
            const currentX = (1 - t) * (1 - t) * fromPos.x + 
                        2 * (1 - t) * t * midX + 
                        t * t * toPos.x;
            const currentY = (1 - t) * (1 - t) * fromPos.y + 
                        2 * (1 - t) * t * midY + 
                        t * t * toPos.y;
            
            return { currentX, currentY };
        }
        
        function addNodeGlow(nodeId, strength) {
            anonNodeGlowLevels[nodeId] = Math.min(1.0, strength);
            updateNodeGlow(nodeId);
            
            if (!anonGlowDecayInterval) {
                startGlowDecay();
            }
        }
        
        function updateNodeGlow(nodeId) {
            const glowLevel = anonNodeGlowLevels[nodeId];
            if (glowLevel <= 0.01) {
                const existingGlow = document.getElementById(`node-glow-${nodeId}`);
                if (existingGlow) existingGlow.remove();
                return;
            }
            
            let glow = document.getElementById(`node-glow-${nodeId}`);
            
            if (!glow) {
                glow = document.createElement('div');
                glow.id = `node-glow-${nodeId}`;
                glow.style.position = 'fixed';
                glow.style.borderRadius = '50%';
                glow.style.pointerEvents = 'none';
                glow.style.zIndex = '992';
                glow.style.transition = 'opacity 0.3s ease-out';
                document.body.appendChild(glow);
            }

            if (!actualMemoryNetwork) return;
            
            const positions = actualMemoryNetwork.getPositions([nodeId]);
            if (!positions[nodeId]) return;
            
            const nodePos = actualMemoryNetwork.canvasToDOM(positions[nodeId]);
            const container = document.getElementById('memory-network');
            const containerRect = container.getBoundingClientRect();
            
            const node = actualNetworkData.nodes.find(n => n.id === nodeId);
            const nodeSize = node ? node.size : 35;
            
            const glowMultiplier = 1.5 + (glowLevel * 1.0);
            const size = Math.max(nodeSize * glowMultiplier, 60);
            
            const x = containerRect.left + nodePos.x - size/2;
            const y = containerRect.top + nodePos.y - size/2;
            
            glow.style.transform = `translate(${x}px, ${y}px)`;
            glow.style.width = size + 'px';
            glow.style.height = size + 'px';
            glow.style.background = `radial-gradient(circle, rgba(168,85,247,${glowLevel * 0.7}) 0%, rgba(168,85,247,${glowLevel * 0.4}) 40%, transparent 70%)`;
            glow.style.opacity = Math.min(0.8, glowLevel * 1.1);
            glow.style.filter = `blur(${Math.max(2, 6 * glowLevel)}px)`;
        }
        
        function createNodePulse(nodeId, strength) {
            if (!actualMemoryNetwork) return;
            
            const positions = actualMemoryNetwork.getPositions([nodeId]);
            if (!positions[nodeId]) return;
            
            const nodePos = actualMemoryNetwork.canvasToDOM(positions[nodeId]);
            const container = document.getElementById('memory-network');
            const containerRect = container.getBoundingClientRect();
            
            for (let i = 0; i < Math.ceil(strength * 2); i++) {
                setTimeout(() => {
                    const pulse = document.createElement('div');
                    const node = actualNetworkData.nodes.find(n => n.id === nodeId);
                    const nodeSize = node ? node.size : 35;
                    
                    const pulseMultiplier = 1.2 + (strength * 0.8);
                    const size = Math.max(nodeSize * pulseMultiplier, 50);
                    
                    pulse.style.position = 'fixed';
                    pulse.style.left = (containerRect.left + nodePos.x - size/2) + 'px';
                    pulse.style.top = (containerRect.top + nodePos.y - size/2) + 'px';
                    pulse.style.width = size + 'px';
                    pulse.style.height = size + 'px';
                    pulse.style.borderRadius = '50%';
                    pulse.style.border = '3px solid rgba(168,85,247,0.8)';
                    pulse.style.pointerEvents = 'none';
                    pulse.style.zIndex = '993';
                    pulse.style.opacity = strength;
                    document.body.appendChild(pulse);

                    pulse.style.transition = 'all 0.8s ease-out';
                    pulse.style.transform = 'scale(2.5)';
                    pulse.style.opacity = '0';

                    setTimeout(() => pulse.remove(), 800);
                }, i * 150);
            }
        }
        
        function startGlowDecay() {
            if (anonGlowDecayInterval) {
                clearInterval(anonGlowDecayInterval);
            }
            
            anonGlowDecayInterval = setInterval(() => {
                let hasActiveGlows = false;
                
                for (const nodeId in anonNodeGlowLevels) {
                    if (anonNodeGlowLevels[nodeId] > 0.001) {
                        anonNodeGlowLevels[nodeId] *= 0.85;
                        updateNodeGlow(nodeId);
                        hasActiveGlows = true;
                    } else if (anonNodeGlowLevels[nodeId] > 0) {
                        anonNodeGlowLevels[nodeId] = 0;
                        const existingGlow = document.getElementById(`node-glow-${nodeId}`);
                        if (existingGlow) {
                            existingGlow.style.transition = 'opacity 0.2s ease-out';
                            existingGlow.style.opacity = '0';
                            setTimeout(() => existingGlow.remove(), 200);
                        }
                    }
                }
                
                if (!hasActiveGlows) {
                    clearInterval(anonGlowDecayInterval);
                    anonGlowDecayInterval = null;
                }
            }, 100);
        }
        
        function calculateSimpleSimilarity(text1, text2) {
            const words1 = text1.toLowerCase().split(/\s+/);
            const words2 = text2.toLowerCase().split(/\s+/);
            const set1 = new Set(words1);
            const set2 = new Set(words2);
            const intersection = new Set([...set1].filter(x => set2.has(x)));
            const union = new Set([...set1, ...set2]);
            return union.size > 0 ? intersection.size / union.size : 0;
        }
        
        function resetAnonymousMode() {
            if (confirm('Are you sure you want to reset? This will clear all chat history and memory nodes.')) {
                localStorage.removeItem(STORAGE_KEY);
                localStorage.removeItem(MEMORY_KEY);
                console.log('🗑️ Reset: Cleared chat history and memories');
                location.reload();
            }
        }
        
        async function sendMessage() {
            if (isSending) return;
            const input = document.getElementById('chat-input');
            const sendButton = document.getElementById('send-button');
            const message = input.value.trim();
            if (!message) return;
            
            isSending = true;
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';
            appendMessage(message, true);
            input.value = '';
            input.style.height = 'auto';
            
            const history = getConversationHistory();
            try {
                const response = await fetch('/api/chat/anonymous/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: message, 
                        history: history,
                        memories: anonymousMemories  // Send existing memories for context
                    })
                });
                const data = await response.json();
                if (data.success && data.response) {
                    setTimeout(() => {
                        appendMessage(data.response, false);
                        // Add newly created memories to the network
                        if (data.memories && data.memories.length > 0) {
                            console.log(`Received ${data.memories.length} new memories from AI`);
                            addMemoriesToNetwork(data.memories);
                        }
                    }, 500);
                } else {
                    appendMessage(`Error: ${data.error || 'Failed to get response'}`, false);
                }
            } catch (error) {
                console.error('Error sending message:', error);
                appendMessage(`Error: ${error.message}`, false);
            } finally {
                isSending = false;
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
            }
        }
        
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function setupEventListeners() {
            const input = document.getElementById('chat-input');
            const sendButton = document.getElementById('send-button');
            sendButton.addEventListener('click', sendMessage);
            input.addEventListener('keydown', handleKeyDown);
            input.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 150) + 'px';
            });
        }
        
        window.addEventListener('load', function() {
            loadChatHistory();
            loadMemories();  // Load memories and initialize network
            setupEventListeners();
        });
    </script>
    ''' + MEMORY_NETWORK_JAVASCRIPT + '''
</body>
</html>
'''
    
    return render_template_string(ANONYMOUS_TEMPLATE)


