#!/usr/bin/env python3

import os
import time
import threading
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def start_memory_file_watcher(memory_manager, path):
    """Start watching memory files for changes and reload when needed"""
    
    class MemoryFileHandler(FileSystemEventHandler):
        def __init__(self):
            super().__init__()
            self.last_reload_time = 0
            self.last_file_size = 0
            self.last_file_hash = None
            
        def on_modified(self, event):
            # Only process memories.json files
            if not str(event.src_path).endswith('memories.json'):
                return
                
            # Skip temporary, backup, and lock files
            if str(event.src_path).endswith(('.tmp', '.backup', '.lock')):
                return
                
            current_time = time.time()
            
            # Avoid duplicate reloads within 10 seconds to reduce position resets
            if current_time - self.last_reload_time < 10.0:
                return
            
            try:
                # Check if file actually changed (avoid reloading on same content)
                if os.path.exists(event.src_path):
                    current_size = os.path.getsize(event.src_path)
                    
                    # Skip if file is empty or being written
                    if current_size == 0:
                        return
                    
                    # Wait a bit for file write to complete
                    time.sleep(0.2)
                    
                    # Calculate file hash to detect actual content changes
                    try:
                        with open(event.src_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        
                        # Skip if content hasn't actually changed
                        if file_hash == self.last_file_hash:
                            return
                            
                        self.last_file_hash = file_hash
                        self.last_file_size = current_size
                    except (IOError, OSError):
                        # File might be locked, skip this reload
                        print(f"[Watcher] File locked, skipping reload")
                        return
                
                print(f"[Watcher] Detected memories.json change, reloading...")
                
                # Add delay before reloading to let file operations complete
                time.sleep(0.5)
                memory_manager.reload_from_disk()
                self.last_reload_time = current_time
                
            except Exception as e:
                print(f"[Watcher] Error during reload: {e}")
                    
    try:
        observer = Observer()
        handler = MemoryFileHandler()
        watch_dir = os.path.dirname(path)
        
        # Check if directory exists before watching
        if not os.path.exists(watch_dir):
            print(f"[Watcher] Directory {watch_dir} does not exist, skipping file watcher")
            return None
            
        observer.schedule(handler, path=watch_dir, recursive=False)
        observer.daemon = True
        observer.start()
        print(f"[Watcher] Watching {path} for changes...")
        
        return observer
    except Exception as e:
        print(f"[Watcher] Failed to start file watcher: {e}")
        return None

def setup_file_watcher(memory_manager, memory_json_path):
    """Setup file watcher if memory manager is available"""
    if not memory_manager:
        print("[WARN] Memory manager not available, skipping file watcher")
        return None
    
    # Skip file watcher in production/cloud environments
    if os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('HEROKU_APP_NAME'):
        print("[WARN] Running in cloud environment, skipping file watcher")
        return None
    
    try:
        watcher_thread = threading.Thread(
            target=start_memory_file_watcher, 
            args=(memory_manager, memory_json_path), 
            daemon=True
        )
        watcher_thread.start()
        print("[INFO] Memory file watcher started successfully")
        return watcher_thread
    except Exception as e:
        print(f"[WARN] Warning: Could not start memory file watcher: {e}")
        return None 