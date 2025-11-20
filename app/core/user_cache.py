#!/usr/bin/env python3
"""
User cache to avoid redundant Clerk API calls and database queries
"""

import time
from typing import Optional, Dict, Any
from threading import Lock

class UserCache:
    """
    In-memory cache for user data to avoid repeated API calls
    Cache expires after 5 minutes to ensure data stays relatively fresh
    """
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
        self.ttl = ttl_seconds
    
    def get(self, clerk_id: str) -> Optional[Dict[str, Any]]:
        """Get user from cache if not expired"""
        with self.lock:
            if clerk_id in self.cache:
                entry = self.cache[clerk_id]
                if time.time() - entry['cached_at'] < self.ttl:
                    print(f"[CACHE HIT] User {clerk_id[:10]}... from cache")
                    return entry['data']
                else:
                    # Expired, remove it
                    print(f"[CACHE MISS] User {clerk_id[:10]}... expired")
                    del self.cache[clerk_id]
            return None
    
    def set(self, clerk_id: str, user_data: Dict[str, Any]):
        """Cache user data"""
        with self.lock:
            self.cache[clerk_id] = {
                'data': user_data,
                'cached_at': time.time()
            }
            print(f"[CACHE SET] User {clerk_id[:10]}... cached for {self.ttl}s")
    
    def invalidate(self, clerk_id: str):
        """Invalidate cache for a specific user"""
        with self.lock:
            if clerk_id in self.cache:
                del self.cache[clerk_id]
                print(f"[CACHE INVALIDATE] User {clerk_id[:10]}...")
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            print("[CACHE CLEAR] All cache cleared")

# Global cache instance
_user_cache = UserCache(ttl_seconds=300)  # 5 minutes

def get_user_cache() -> UserCache:
    """Get the global user cache instance"""
    return _user_cache



