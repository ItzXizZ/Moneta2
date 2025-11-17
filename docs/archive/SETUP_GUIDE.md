# Moneta Setup and Usage Guide

## Quick Start Guide

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the Moneta2 directory with the following variables:

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration (Required for production)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# JWT Secret (Required for authentication)
JWT_SECRET=your_secret_key_here_change_this

# Flask Configuration
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=4000

# Optional: Force UTF-8 encoding (for Windows)
PYTHONIOENCODING=utf-8
```

### 3. Database Setup

Run the Supabase table creation scripts:

```bash
# Create authentication and user tables
python scripts/setup_cloud.py

# Create chat tables
python scripts/setup_chat_tables.py
```

### 4. Running the Application

**Option A: Using the fixed launcher (Recommended for Windows)**
```bash
python run_fixed.py
```

**Option B: Using the standard launcher**
```bash
python run.py
```

The application will be available at: `http://localhost:4000`

## Authentication System

### How to Login/Logout

1. **Sign Up**
   - Go to `http://localhost:4000/`
   - Click "Get Started" or "Sign Up"
   - Fill in your name, email, and password (minimum 6 characters)
   - Click "Start Remembering"
   - You'll be automatically logged in and redirected to the dashboard

2. **Login**
   - Go to `http://localhost:4000/`
   - Click "Sign In"
   - Enter your email and password
   - Click "Sign In"
   - You'll be redirected to the dashboard

3. **Logout**
   - Click the "Sign Out" button in the top right corner of the dashboard
   - Or click "Sign Out" in the chat interface (Dashboard button → Sign Out)

### Authentication Flow

- **JWT Tokens**: The system uses JSON Web Tokens stored in localStorage
- **Protected Routes**: `/dashboard`, `/chat`, `/subscription` require authentication
- **Public Routes**: `/` (landing page) is accessible without authentication
- **Token Verification**: Every API request checks the `Authorization: Bearer <token>` header

## Chat System

### Starting a Chat

1. Login to your account
2. Click "Enter Memory Universe" from the dashboard
3. Type your message in the input box at the bottom
4. Press Enter or click "Send"

### Chat Features

- **Thread Management**: 
  - Create new threads with the "New" button
  - View previous threads in the left sidebar
  - Delete threads with the trash icon
  - Save memories from conversations with the "💾 Save" button

- **Memory Integration**:
  - The AI automatically searches your personal memory database
  - Relevant memories are injected into responses
  - You can see which memories were used (expandable section below AI responses)

- **Memory Extraction**:
  - Click "💾 Save" to extract important information from the conversation
  - The system uses OpenAI to identify personal facts, preferences, and information
  - Extracted memories are saved to your personal database

### Troubleshooting

**Problem: Chats don't send or save**
- Check that your OpenAI API key is set in `.env`
- Verify Supabase connection (URL and KEY in `.env`)
- Check the browser console (F12) for errors
- Look at server logs for error messages

**Problem: 500 Internal Server Error**
- This was caused by Unicode encoding issues (now fixed)
- Make sure you're using `run_fixed.py` on Windows
- Check that PYTHONIOENCODING=utf-8 is set in your environment

**Problem: Login doesn't work**
- Verify JWT_SECRET is set in `.env`
- Check Supabase tables are created (`users` table)
- Clear browser localStorage and try again
- Check browser console for API errors

**Problem: Memory network doesn't load**
- Check that vis-network.js is loading (check browser console)
- Verify you have memories in your database
- Try clicking the "Refresh" button in the memory network

## Architecture Overview

### Backend Structure

```
Moneta2/
├── app/
│   ├── blueprints/          # API route handlers
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── chat.py         # Chat endpoints
│   │   ├── memory.py       # Memory management endpoints
│   │   └── main.py         # UI routes
│   ├── core/               # Core system components
│   │   ├── auth_system.py  # Authentication logic
│   │   ├── chat_interface.py
│   │   └── lightweight_memory_manager.py
│   └── services/           # Business logic services
│       ├── openai_service.py
│       ├── user_conversation_service.py
│       └── memory_search_service.py
├── templates/              # HTML templates
├── config.py               # Configuration management
└── run_fixed.py           # Application entry point (UTF-8 fixed)
```

### Key Components

1. **Authentication System** (`app/core/auth_system.py`)
   - Handles user registration and login
   - JWT token generation and validation
   - User-specific memory isolation

2. **Chat System** (`app/services/user_conversation_service.py`)
   - Manages conversation threads
   - Integrates with OpenAI for responses
   - Handles message persistence

3. **Memory System** (`app/core/lightweight_memory_manager.py`)
   - User-specific memory storage
   - Semantic search and retrieval
   - Memory scoring and relevance

4. **OpenAI Integration** (`app/services/openai_service.py`)
   - Chat completions with memory context
   - Memory extraction from conversations
   - Subscription-based model selection

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/verify` - Verify JWT token
- `POST /api/auth/logout` - Logout (client-side)
- `GET /api/auth/profile` - Get user profile

### Chat
- `POST /api/chat/send` - Send message and get AI response
- `POST /api/chat/thread/new` - Create new thread
- `GET /api/chat/thread/<id>` - Get thread messages
- `DELETE /api/chat/thread/<id>` - Delete thread
- `POST /api/chat/thread/end` - Extract memories from thread
- `GET /api/chat/threads` - Get all user threads

### Memory
- `GET /api/memory/user` - Get user memories
- `POST /api/memory/add` - Add memory
- `DELETE /api/memory/<id>` - Delete memory
- `GET /api/memory/search` - Search memories

## Security Best Practices

1. **Never commit `.env` files** - They contain sensitive API keys
2. **Change JWT_SECRET** - Use a strong, unique secret key
3. **Use HTTPS in production** - Protect authentication tokens
4. **Rotate API keys** - Regularly update OpenAI and Supabase keys
5. **Validate user input** - All inputs are validated server-side

## Deployment

### Render.com Deployment

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Use `render.yaml` configuration
4. Deploy and monitor logs

### Manual Deployment

1. Set up a server (Ubuntu/Debian recommended)
2. Install Python 3.8+
3. Clone repository
4. Install dependencies
5. Set environment variables
6. Use gunicorn or similar WSGI server
7. Set up reverse proxy (nginx/Apache)
8. Enable HTTPS with Let's Encrypt

## Support

For issues or questions:
1. Check this guide first
2. Review the logs (server console output)
3. Check browser console (F12)
4. Verify all environment variables are set
5. Ensure database tables are created
6. Test OpenAI API key independently

## Recent Fixes (November 2025)

### Unicode Encoding Fix
- **Problem**: Emoji characters in print statements caused 500 errors on Windows
- **Solution**: Created `run_fixed.py` with UTF-8 encoding configuration
- **Impact**: All console output now works correctly on Windows

### Authentication Improvements
- Clarified login/logout flow
- Added better error messages
- Improved token handling

### Chat System Enhancements
- Fixed message persistence
- Improved thread management
- Better error handling



