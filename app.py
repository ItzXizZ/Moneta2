#!/usr/bin/env python3

from flask import Flask, render_template_string, render_template, redirect, url_for
from config import config
from api.chat_routes import register_chat_routes
from api.memory_routes import register_memory_routes
from api.auth_routes import register_auth_routes
from api.subscription_routes import register_subscription_routes
from ui.chat_interface import CHAT_INTERFACE_TEMPLATE
from ui.memory_network_ui import MEMORY_NETWORK_UI_TEMPLATE, MEMORY_NETWORK_CSS
from ui.chat_javascript import CHAT_JAVASCRIPT
from ui.memory_network_javascript import MEMORY_NETWORK_JAVASCRIPT
from utils.file_watcher import setup_file_watcher

app = Flask(__name__)
app.secret_key = config.jwt_secret if hasattr(config, 'jwt_secret') else 'your-secret-key-here'

# Combine all UI components into the complete template
COMPLETE_TEMPLATE = CHAT_INTERFACE_TEMPLATE.replace(
    '''            <div id="memory-network-container">
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

@app.route('/chat')
def chat_interface():
    """Chat interface route (requires authentication)"""
    from auth_system import auth_system, get_auth_system
    
    # Ensure auth system is initialized
    if auth_system is None:
        auth_system, _ = get_auth_system()
    
    # Check authentication via JavaScript (client-side redirect)
    # The template includes auth check that redirects to / if no token
    return render_template_string(COMPLETE_TEMPLATE)

@app.route('/debug')
def debug_auth():
    """Debug authentication page"""
    import os
    debug_file_path = os.path.join(os.path.dirname(__file__), 'debug_auth.html')
    with open(debug_file_path, 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/subscription')
def subscription_page():
    """Subscription management page"""
    return render_template('subscription.html')

# Register all API routes
register_auth_routes(app)  # Authentication routes (includes landing page at /)
register_chat_routes(app)
register_memory_routes(app)
register_subscription_routes(app)

# Setup file watcher for memory changes
if config.memory_available and config.memory_manager:
    setup_file_watcher(config.memory_manager, config.memory_json_path)

if __name__ == '__main__':
    print("🤖 Starting ChatGPT Clone with OpenAI API and Memory Search...")
    print("📱 Open your browser and go to: http://localhost:4000")
    print("💜 Enjoy your purple-themed chat experience!")
    
    if config.memory_available:
        print("🧠 Memory search system is available!")
    else:
        print("⚠️  Memory search system is not available")
    
    app.run(
        debug=config.debug, 
        host=config.host, 
        port=config.port
    ) 