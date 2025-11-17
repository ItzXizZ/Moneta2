#!/usr/bin/env python3

import os
import threading
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Moneta application"""
    
    def __init__(self):
        # OpenAI Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                print("[OK] OpenAI client initialized successfully")
            except Exception as e:
                print(f"[ERROR] Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            print("[WARN] OPENAI_API_KEY not found in environment variables")
            print("[INFO] Please add OPENAI_API_KEY to your .env file to enable AI chat")
            self.openai_client = None
        
        # Flask Configuration
        self.debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'  # Default to False for production
        self.host = os.getenv('FLASK_HOST', '0.0.0.0')
        # Use Render's PORT environment variable if available, otherwise default to 4000
        self.port = int(os.getenv('PORT', os.getenv('FLASK_PORT', '4000')))
        
        # Authentication Configuration
        self.jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key-here')
        
        # Clerk Configuration
        self.clerk_secret_key = os.getenv('CLERK_SECRET_KEY')
        self.clerk_publishable_key = os.getenv('CLERK_PUBLISHABLE_KEY')
        
        # Validate Clerk configuration
        if not self.clerk_secret_key or not self.clerk_publishable_key:
            print("[WARN] Clerk authentication keys not found in environment variables")
            print("[INFO] Please add CLERK_SECRET_KEY and CLERK_PUBLISHABLE_KEY to your .env file")
            print("[INFO] Clerk authentication will not be available")
        else:
            # Check if using test or production keys
            if self.clerk_secret_key.startswith('sk_test_'):
                print("[INFO] Using Clerk TEST keys (development mode)")
            elif self.clerk_secret_key.startswith('sk_live_'):
                print("[OK] Using Clerk PRODUCTION keys")
            else:
                print("[WARN] Unrecognized Clerk key format")
            print("[OK] Clerk authentication configured")
        
        # Memory system configuration
        self.memory_available = False
        self.memory_manager = None
        self.memory_json_path = 'memory_data.json'
        
        # Session memory queue for real-time updates
        self.session_new_memories = []
        self.session_new_memories_lock = threading.Lock()
        
        # Memory search configuration (optimized for full ML version)
        self.min_relevance_threshold = 0.7  # Higher threshold for better quality with ML
        self.max_search_results = 15        # More results with powerful ML search
        self.max_injected_memories = 5      # More memories can be injected with better relevance
        
        # Initialize memory system
        self._initialize_memory_system()
    
    def _initialize_memory_system(self):
        """Initialize the memory management system (prioritizing full version)"""
        try:
            # Try to import the full memory manager with ML capabilities
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'memory-app', 'backend'))
            from memory_manager import MemoryManager
            
            self.memory_manager = MemoryManager()
            self.memory_available = True
            print("[INFO] Full ML-powered memory system initialized successfully!")
            print("   - Semantic search with sentence-transformers")
            print("   - Advanced similarity calculations with scikit-learn")
            print("   - High-performance memory retrieval")
        except ImportError as e:
            print(f"[WARN] Full memory system not available: {e}")
            print("   Falling back to lightweight version...")
            # Fallback to lightweight memory manager
            try:
                from app.core.lightweight_memory_manager import LightweightMemoryManager
                self.memory_manager = LightweightMemoryManager()
                self.memory_available = True
                print("[OK] Lightweight memory system initialized (fallback)")
            except Exception as e2:
                print(f"[ERROR] Error initializing lightweight memory system: {e2}")
                self.memory_available = False
        except Exception as e:
            print(f"[ERROR] Error initializing memory system: {e}")
            # Try lightweight as last resort
            try:
                from app.core.lightweight_memory_manager import LightweightMemoryManager
                self.memory_manager = LightweightMemoryManager()
                self.memory_available = True
                print("[OK] Lightweight memory system initialized (last resort)")
            except Exception as e3:
                print(f"[ERROR] All memory systems failed: {e3}")
                self.memory_available = False

# Create global config instance
config = Config() 