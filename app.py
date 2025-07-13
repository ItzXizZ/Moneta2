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

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.secret_key = config.jwt_secret

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
        try:
            from auth_system import get_auth_system
            auth_system, _ = get_auth_system()
            # Your chat interface logic here
            return render_template_string(COMPLETE_TEMPLATE)
        except Exception as e:
            print(f"Error in chat interface: {e}")
            return render_template_string(COMPLETE_TEMPLATE)

    @app.route('/debug')
    def debug_auth():
        """Debug authentication route"""
        with open('debug_auth.html', 'r', encoding='utf-8') as f:
            return f.read()

    @app.route('/subscription')
    def subscription_page():
        """Subscription page route"""
        return render_template('subscription.html')

    @app.route('/')
    def index():
        """Main page route"""
        return redirect(url_for('chat_interface'))

    # Register API routes
    register_auth_routes(app)
    register_chat_routes(app)
    register_memory_routes(app)
    register_subscription_routes(app)

    print("🤖 Starting ChatGPT Clone with OpenAI API and Memory Search...")
    print("📱 Open your browser and go to: http://localhost:4000")
    
    # Initialize memory system if available
    if config.memory_available:
        print("✅ Memory search system is ready!")
        setup_file_watcher(config.memory_manager, config.memory_json_path)
    else:
        print("⚠️  Memory search system is not available")
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    # For Render deployment, we need to bind to 0.0.0.0 and use PORT from environment
    import os
    port = int(os.environ.get('PORT', config.port))
    app.run(
        debug=config.debug, 
        host='0.0.0.0', 
        port=port
    ) 