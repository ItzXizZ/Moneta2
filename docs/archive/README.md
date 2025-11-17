# Moneta - AI Memory Management System

Moneta is a sophisticated Flask-based AI memory management system that combines conversational AI with intelligent memory storage, retrieval, and visualization.

## 🚀 Features

- **AI Chat Interface**: OpenAI-powered conversational AI with context-aware responses
- **Memory Management**: Intelligent memory storage with semantic search capabilities
- **Memory Network Visualization**: Interactive graph visualization of memory connections
- **User Authentication**: Secure JWT-based authentication system with Supabase
- **Subscription Management**: Tiered subscription plans with usage tracking
- **Real-time Updates**: Live memory network updates during conversations

## 📁 Project Structure

Following Flask best practices, the application is organized as follows:

```
Moneta2/
├── app/                          # Main application package
│   ├── __init__.py              # Application factory
│   ├── blueprints/              # Flask blueprints (API routes)
│   │   ├── __init__.py
│   │   ├── main.py             # Main page routes
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── chat.py             # Chat/conversation endpoints
│   │   ├── memory.py           # Memory management endpoints
│   │   └── subscription.py    # Subscription/billing endpoints
│   ├── core/                    # Core system components
│   │   ├── __init__.py
│   │   ├── auth_system.py      # Authentication system
│   │   ├── lightweight_memory_manager.py
│   │   ├── chatgpt_openai.py   # OpenAI integration
│   │   ├── chat_interface.py   # Chat UI template
│   │   ├── chat_javascript.py  # Chat JavaScript
│   │   ├── memory_network_ui.py # Memory network UI
│   │   ├── memory_network_javascript.py
│   │   └── node_animation.py   # Network visualization
│   ├── models/                  # Data models (future use)
│   │   └── __init__.py
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── conversation_service.py
│   │   ├── user_conversation_service.py
│   │   ├── memory_search_service.py
│   │   ├── openai_service.py
│   │   └── subscription_service.py
│   ├── static/                  # Static files
│   │   ├── css/
│   │   ├── js/
│   │   └── media/              # Images and videos
│   ├── templates/               # HTML templates (symlinked)
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       └── file_watcher.py
├── templates/                   # HTML templates
│   ├── landing.html
│   ├── dashboard.html
│   └── subscription.html
├── memory-app/                  # Full ML-powered memory system
│   ├── backend/
│   │   ├── memory_manager.py
│   │   ├── cloud_memory_manager.py
│   │   └── data/
│   └── frontend/
├── scripts/                     # Utility scripts
│   ├── setup_cloud.py
│   ├── setup_chat_tables.py
│   ├── migrate_to_cloud.py
│   └── *.sql
├── docs/                        # Documentation
│   ├── HOW_TO_USE.md
│   ├── MEMORY_SYSTEM_OVERVIEW.md
│   ├── SUPABASE_SETUP.md
│   └── *.md
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── render.yaml                  # Render deployment config
└── .env                         # Environment variables (not tracked)
```

## 🛠️ Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- Supabase account (for authentication and storage)

### Installation

1. **Clone the repository**
   ```bash
   cd Moneta2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   
   # Flask Configuration
   FLASK_DEBUG=True
   FLASK_HOST=0.0.0.0
   FLASK_PORT=4000
   
   # JWT Secret
   JWT_SECRET=your_secure_jwt_secret_here
   ```

4. **Setup database tables**
   
   Run the setup scripts to create necessary tables:
   ```bash
   python scripts/setup_chat_tables.py
   python scripts/setup_cloud.py
   ```

## 🚀 Running the Application

### Development Mode

```bash
python run.py
```

The application will be available at `http://localhost:4000`

### Production Mode

```bash
gunicorn -w 4 -b 0.0.0.0:4000 run:app
```

## 📚 API Endpoints

### Authentication (`/api/auth/`)
- `POST /register` - Register new user
- `POST /login` - User login
- `GET /verify` - Verify JWT token
- `POST /logout` - User logout
- `GET /profile` - Get user profile

### Chat (`/api/chat/`)
- `POST /send` - Send message and get AI response
- `POST /thread/new` - Create new conversation thread
- `POST /thread/end` - End thread and extract memories
- `GET /thread/<id>` - Get thread messages
- `DELETE /thread/<id>` - Delete thread
- `GET /threads` - Get all user threads

### Memory (`/api/memory/`)
- `GET /availability` - Check memory system availability
- `GET /network` - Get memory network data
- `GET /new` - Get new memories (real-time updates)
- `GET /user` - Get user memories
- `POST /add` - Add new memory
- `GET /search` - Search memories

### Subscription (`/api/subscription/`)
- `GET /plans` - Get available plans
- `GET /dashboard` - Get user dashboard data
- `POST /subscribe` - Subscribe to plan
- `POST /cancel` - Cancel subscription
- `GET /usage` - Get usage information
- `GET /can-chat` - Check if user can chat

## 🏗️ Architecture

### Application Factory Pattern

The application uses Flask's application factory pattern for better modularity and testing:

```python
from app import create_app

app = create_app()
```

### Blueprint Structure

Routes are organized into blueprints by functionality:
- **main**: Landing pages and core UI routes
- **auth**: Authentication and user management
- **chat**: Conversation and thread management
- **memory**: Memory storage and retrieval
- **subscription**: Billing and subscription management

### Service Layer

Business logic is separated into service classes:
- `OpenAIService`: AI response generation
- `UserConversationService`: Conversation management
- `MemorySearchService`: Memory search and filtering
- `SubscriptionService`: Subscription and usage tracking

## 🔧 Configuration

Configuration is managed through `config.py` with environment variables:

- **Memory System**: Automatically selects full ML-powered system or lightweight fallback
- **Debug Mode**: Controlled via `FLASK_DEBUG` environment variable
- **Port**: Configurable via `PORT` or `FLASK_PORT` environment variables

## 📦 Deployment

### Render

The application is configured for Render deployment with `render.yaml`:

```yaml
services:
  - type: web
    name: moneta
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn run:app
```

### Environment Variables

Set the following in your deployment platform:
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `JWT_SECRET`
- `PORT` (automatically set by most platforms)

## 🧪 Development

### Adding New Features

1. **New API Endpoint**: Create or modify blueprints in `app/blueprints/`
2. **Business Logic**: Add services in `app/services/`
3. **Core Components**: Add to `app/core/`
4. **Static Assets**: Place in `app/static/`

### Code Organization

- Follow Flask best practices
- Use blueprints for route organization
- Keep business logic in services
- Separate core system components
- Use configuration management for settings

## 📝 Documentation

Comprehensive documentation is available in the `docs/` folder:

- `HOW_TO_USE.md` - User guide
- `MEMORY_SYSTEM_OVERVIEW.md` - Memory system architecture
- `SUPABASE_SETUP.md` - Database setup guide
- `CHAT_INTEGRATION_GUIDE.md` - Chat system integration
- `START_MEMORYOS.md` - Getting started guide

## 🤝 Contributing

When contributing to this project:

1. Follow the existing code structure
2. Use meaningful commit messages
3. Update documentation as needed
4. Test thoroughly before submitting

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Built with Flask, OpenAI, and Supabase
- Uses sentence-transformers for semantic search
- Vis.js for network visualization

---

**Happy coding! 🚀**



