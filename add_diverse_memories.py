#!/usr/bin/env python3
"""
Add diverse memories with better tags to test the improved scoring and connection system.
"""

import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(__file__))

def add_diverse_memories():
    """Add diverse memories with better tags to test the improved system"""
    
    try:
        from auth_system import get_auth_system
        
        # Get the auth system and user memory manager
        auth_system, user_memory_manager = get_auth_system()
        
        if user_memory_manager is None:
            print("❌ User memory manager not available")
            return
        
        # Use test user
        test_email = "test@example.com"
        test_password = "testpassword123"
        
        # Login to get user ID
        login_result = auth_system.login_user(test_email, test_password)
        if not login_result['success']:
            print("❌ Failed to login test user")
            return
        
        user_id = login_result['user']['id']
        print(f"✅ Logged in as: {login_result['user']['name']}")
        
        # Diverse memories with better tags and content
        diverse_memories = [
            {
                "content": "I love working with Python for data analysis and machine learning projects. The pandas library makes data manipulation so much easier.",
                "tags": ["python", "data analysis", "machine learning", "pandas", "programming"]
            },
            {
                "content": "Building web applications with Flask and React is incredibly satisfying. The combination of Python backend and JavaScript frontend is powerful.",
                "tags": ["flask", "react", "web development", "python", "javascript", "programming"]
            },
            {
                "content": "Natural language processing fascinates me. Understanding how machines can process and understand human language opens up so many possibilities.",
                "tags": ["nlp", "machine learning", "ai", "language processing", "technology"]
            },
            {
                "content": "Docker containers have revolutionized how I deploy applications. The consistency across different environments is amazing.",
                "tags": ["docker", "containers", "devops", "deployment", "technology"]
            },
            {
                "content": "Git version control is essential for any development project. Being able to track changes and collaborate effectively is crucial.",
                "tags": ["git", "version control", "programming", "collaboration", "development"]
            },
            {
                "content": "I enjoy exploring different programming languages. Each has its strengths - Python for data science, JavaScript for web development, and Rust for systems programming.",
                "tags": ["programming", "python", "javascript", "rust", "languages", "technology"]
            },
            {
                "content": "Machine learning algorithms are fascinating. Understanding how neural networks can learn patterns from data is mind-blowing.",
                "tags": ["machine learning", "neural networks", "algorithms", "ai", "technology"]
            },
            {
                "content": "Database design and optimization are crucial skills. Understanding how to structure data efficiently makes all the difference.",
                "tags": ["database", "design", "optimization", "data", "programming"]
            },
            {
                "content": "I love building chatbots and conversational AI systems. The challenge of making machines understand and respond naturally is exciting.",
                "tags": ["chatbots", "conversational ai", "nlp", "ai", "programming"]
            },
            {
                "content": "Data science combines statistics, programming, and domain expertise. It's amazing how we can extract insights from raw data.",
                "tags": ["data science", "statistics", "programming", "analytics", "insights"]
            }
        ]
        
        print("🧠 Adding diverse memories with improved tags...")
        print(f"📝 Using user ID: {user_id}")
        
        for i, memory in enumerate(diverse_memories, 1):
            try:
                print(f"📝 Adding memory {i}: {memory['content'][:50]}...")
                
                result = user_memory_manager.add_memory_for_user(
                    user_id, 
                    memory['content'], 
                    memory['tags']
                )
                
                if result['success']:
                    print(f"✅ Memory {i} added successfully")
                else:
                    print(f"❌ Failed to add memory {i}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error adding memory {i}: {e}")
        
        # Check final count
        memories = user_memory_manager.get_user_memories(user_id, 50)
        print(f"🎉 User now has {len(memories)} total memories!")
        
        print("\n📊 Memory breakdown:")
        tag_counts = {}
        for memory in memories:
            for tag in memory.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        print("   Tags by frequency:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"     {tag}: {count}")
        
        print("\n💡 Now test the improved memory network with better scoring and connections!")
        
    except Exception as e:
        print(f"❌ Error initializing system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_diverse_memories() 