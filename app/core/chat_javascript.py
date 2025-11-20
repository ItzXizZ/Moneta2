#!/usr/bin/env python3

# Chat JavaScript Component with all functionality
CHAT_JAVASCRIPT = '''
<script>
let currentThreadId = null;
let isTyping = false;
let sendingMessage = false;
let clerk = null;
let currentToken = null;
let tokenRefreshInterval = null;

// Wait for Clerk SDK to load
async function waitForClerk(maxWaitMs = 5000) {
    const startTime = Date.now();
    while (!window.Clerk) {
        if (Date.now() - startTime > maxWaitMs) {
            console.error('[Chat] Timeout waiting for Clerk SDK to load');
            return false;
        }
        console.log('[Chat] Waiting for Clerk SDK to load...');
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    console.log('[Chat] ✅ Clerk SDK loaded');
    return true;
}

// Initialize Clerk (if available)
async function initChatClerk() {
    try {
        // Wait for Clerk SDK to be available
        const clerkAvailable = await waitForClerk();
        if (!clerkAvailable) {
            console.error('[Chat] Clerk SDK not available - cannot authenticate');
            return null;
        }
        
        clerk = window.Clerk;
        console.log('[Chat] Loading Clerk session...');
        await clerk.load();
        
        // PERFORMANCE FIX: Removed artificial 1000ms delay
        // Clerk.load() already waits for session restoration
        // await new Promise(resolve => setTimeout(resolve, 1000));
        
        if (clerk.session && clerk.user) {
            console.log('[Chat] ✅ Clerk session restored');
            console.log('[Chat] User:', clerk.user.id);
            
            // Get fresh token from Clerk with 30-minute expiration
            try {
                // Request token that lasts 30 minutes (1800 seconds)
                // Try without template first (more compatible)
                let token = null;
                try {
                    token = await clerk.session.getToken({ 
                        skipCache: true,
                        template: 'supabase' // Use template for longer-lived tokens
                    });
                } catch (templateError) {
                    console.warn('[Chat] Template token failed, trying default:', templateError);
                    // Fallback to default token
                    token = await clerk.session.getToken({ skipCache: true });
                }
                
                if (token) {
                    currentToken = token;
                    localStorage.setItem('moneta_session_token', token);
                    localStorage.setItem('authToken', token);
                    console.log('[Chat] ✅ Fresh token obtained from Clerk session');
                    console.log('[Chat] Token preview:', token.substring(0, 20) + '...');
                } else {
                    console.error('[Chat] Failed to get token from session');
                    return null;
                }
            } catch (error) {
                console.error('[Chat] Error getting token:', error);
                console.error('[Chat] Token error details:', error.message, error.stack);
                return null;
            }
            
            // Start aggressive token refresh
            startTokenRefresh();
            return clerk;
        } else {
            console.log('[Chat] ⚠️ No active Clerk session found');
            console.log('[Chat] Session:', clerk.session);
            console.log('[Chat] User:', clerk.user);
            return null;
        }
    } catch (error) {
        console.error('[Chat] Clerk initialization error:', error);
        console.error('[Chat] Error details:', error.message, error.stack);
        return null;
    }
}

// Automatic token refresh
async function refreshToken() {
    try {
        if (!clerk || !clerk.session) {
            console.log('[Chat Token Refresh] ❌ No active Clerk session');
            
            // Check if we have a cached token that might still be valid
            const cachedToken = localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
            if (cachedToken) {
                console.log('[Chat Token Refresh] ⚠️ No session but found cached token, attempting to use it');
                // Don't redirect immediately - let the API call fail gracefully if token is invalid
                return cachedToken;
            }
            
            console.log('[Chat Token Refresh] ❌ No session and no cached token - redirecting to login');
            alert('⚠️ Your session has expired. Please log in again.');
            window.location.href = '/';
            return null;
        }
        
        console.log('[Chat Token Refresh] 🔄 Refreshing JWT token...');
        
        // Try template first (if configured), then fallback to default token
        let newToken = null;
        try {
            // Try with template first (for longer-lived tokens if configured)
            newToken = await clerk.session.getToken({ 
                skipCache: true,
                template: 'supabase' // Use template for longer-lived tokens
            });
            console.log('[Chat Token Refresh] ✅ Got token using supabase template');
        } catch (templateError) {
            console.warn('[Chat Token Refresh] Template token failed, trying default:', templateError.message);
            // Fallback to default token (this always works if session is valid)
            try {
                newToken = await clerk.session.getToken({ skipCache: true });
                console.log('[Chat Token Refresh] ✅ Got token using default method');
            } catch (defaultError) {
                console.error('[Chat Token Refresh] ❌ Both template and default token failed:', defaultError);
                // Check if we have a cached token to use as fallback
                const cachedToken = localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
                if (cachedToken) {
                    console.log('[Chat Token Refresh] ⚠️ Using cached token as fallback');
                    return cachedToken;
                }
                throw defaultError; // Re-throw if no fallback available
            }
        }
        
        if (newToken) {
            currentToken = newToken;
            localStorage.setItem('moneta_session_token', newToken);
            localStorage.setItem('authToken', newToken);
            console.log('[Chat Token Refresh] ✅ Token refreshed successfully');
            console.log('[Chat Token Refresh] New token (first 20 chars):', newToken.substring(0, 20) + '...');
            return newToken;
        } else {
            console.log('[Chat Token Refresh] ⚠️ Got null token, checking cached token...');
            // Fallback to cached token if available
            const cachedToken = localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
            if (cachedToken) {
                console.log('[Chat Token Refresh] ⚠️ Using cached token');
                return cachedToken;
            }
            console.log('[Chat Token Refresh] ❌ No token available');
            return null;
        }
    } catch (error) {
        console.error('[Chat Token Refresh] Error:', error);
        
        // Don't immediately redirect - try to use cached token first
        const cachedToken = localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
        if (cachedToken) {
            console.log('[Chat Token Refresh] ⚠️ Error occurred but using cached token as fallback');
            return cachedToken;
        }
        
        // Only redirect if we truly have no way to authenticate
        console.log('[Chat Token Refresh] ❌ No fallback available - redirecting to login');
        alert('⚠️ Authentication error. Please log in again.');
        window.location.href = '/';
        return null;
    }
}

// Start automatic token refresh
function startTokenRefresh() {
    if (tokenRefreshInterval) {
        clearInterval(tokenRefreshInterval);
    }
    
    // Show authentication status
    updateAuthStatus('✅ Authenticated');
    
    // Refresh token every 2 minutes to prevent any expiration issues
    // Clerk tokens typically last 5-60 minutes depending on configuration
    // Refreshing every 2 minutes ensures we always have a fresh token without being too aggressive
    tokenRefreshInterval = setInterval(async () => {
        console.log('[Chat Token Refresh] ⏰ Scheduled refresh (every 2 minutes)');
        updateAuthStatus('🔄 Refreshing...');
        try {
            const newToken = await refreshToken();
            if (newToken) {
                updateAuthStatus('✅ Authenticated');
                console.log('[Chat Token Refresh] ✅ Scheduled refresh successful');
            } else {
                // Don't update status if refresh failed - might be temporary
                console.warn('[Chat Token Refresh] ⚠️ Scheduled refresh returned null, but continuing...');
                updateAuthStatus('✅ Authenticated (using cached token)');
            }
        } catch (error) {
            // Don't let refresh errors break the interval
            console.error('[Chat Token Refresh] ⚠️ Scheduled refresh error (non-fatal):', error);
            updateAuthStatus('✅ Authenticated (refresh error, using cached token)');
        }
    }, 120000); // 2 minutes - balanced between freshness and not being too aggressive
    
    console.log('[Chat Token Refresh] ✅ Auto-refresh enabled (every 2 minutes)');
    console.log('[Chat Token Refresh] 📅 Frequent refresh prevents session expiration issues');
}

// Update authentication status indicator (HIDDEN - per user request)
function updateAuthStatus(message) {
    // Authentication status indicator hidden per user request
    console.log('[Auth Status]', message);
    // No visual indicator shown
}

// Stop token refresh
function stopTokenRefresh() {
    if (tokenRefreshInterval) {
        clearInterval(tokenRefreshInterval);
        tokenRefreshInterval = null;
    }
}

// Enhanced fetch with automatic token refresh on 401
async function fetchWithAuth(url, options = {}) {
    // Ensure headers object exists
    options.headers = options.headers || {};
    
    // Get current token
    let token = currentToken || localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
    
    // Try to refresh token proactively if we have a Clerk session
    if (!token && clerk && clerk.session) {
        console.log('[Chat Fetch] No token found, attempting to get fresh token...');
        try {
            token = await clerk.session.getToken({ skipCache: true });
            if (token) {
                currentToken = token;
                localStorage.setItem('moneta_session_token', token);
                localStorage.setItem('authToken', token);
                console.log('[Chat Fetch] ✅ Got fresh token from Clerk');
            }
        } catch (e) {
            console.warn('[Chat Fetch] Failed to get token from Clerk:', e.message);
        }
    }
    
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    } else {
        console.warn('[Chat Fetch] No authentication token available - request may fail');
    }
    
    try {
        let response = await fetch(url, options);
        
        // If we get a 401, try refreshing the token and retry once
        if (response.status === 401 && token) {
            console.log('[Chat Fetch] Got 401, refreshing token and retrying...');
            const newToken = await refreshToken();
            
            if (newToken && newToken !== token) {
                // Retry with new token
                options.headers['Authorization'] = `Bearer ${newToken}`;
                console.log('[Chat Fetch] Retrying request with refreshed token...');
                response = await fetch(url, options);
                
                if (response.status === 401) {
                    console.error('[Chat Fetch] Still getting 401 after token refresh');
                    // Don't clear tokens immediately - might be a temporary issue
                    // Let the user continue and they can refresh manually if needed
                } else {
                    console.log('[Chat Fetch] ✅ Retry successful after token refresh');
                }
            } else if (!newToken) {
                console.warn('[Chat Fetch] Token refresh returned null, but keeping original token for potential retry');
            }
        }
        
        return response;
    } catch (error) {
        console.error('[Chat Fetch] Request failed:', error);
        // Don't throw immediately - might be network error, not auth error
        throw error;
    }
}

// Handle authentication errors (DEPRECATED - use fetchWithAuth instead)
function handleAuthError(response) {
    if (response.status === 401) {
        console.log('⚠️ Authentication error - token may be expired');
        return true;
    }
    return false;
}

// Utility function to scroll chat to bottom with proper timing
function scrollChatToBottom() {
    const messagesContainer = document.getElementById('chat-messages');
    if (!messagesContainer) return;
    
    // Use double requestAnimationFrame to ensure DOM is fully rendered
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    });
}

// Auto-resize textarea
const textarea = document.getElementById('chat-input');
if (textarea) {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });
}

// Handle Enter key (Send on Enter, new line on Shift+Enter)
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        console.log('🔥 ENTER KEY PRESSED - calling sendMessage()');
        event.preventDefault();
        event.stopPropagation();
        sendMessage();
        return false;
    }
}

// Send message function
async function sendMessage() {
    console.log('🔥 === SENDMESSAGE FUNCTION CALLED ===');
    
    const input = document.getElementById('chat-input');
    const sendButton = document.querySelector('.send-button');
    const message = input.value.trim();
    
    if (!message || isTyping || sendingMessage) {
        return;
    }
    
    // Set flags and disable UI
    isTyping = true;
    sendingMessage = true;
    input.disabled = true;
    sendButton.disabled = true;
    sendButton.style.opacity = '0.5';
    
    // Generate unique request ID
    const requestId = 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // Clear input and add user message
    input.value = '';
    input.style.height = 'auto';
    addMessage(message, 'user');
    
    try {
        // Refresh token on user activity to ensure it's always fresh
        // Don't fail if refresh doesn't work - we'll try with existing token
        console.log('[Chat] Refreshing token before sending message (activity-based refresh)...');
        const refreshedToken = await refreshToken();
        if (refreshedToken) {
            console.log('[Chat] ✅ Token refreshed successfully before sending');
        } else {
            console.warn('[Chat] ⚠️ Token refresh returned null, will try with existing token');
        }
        
        const token = currentToken || localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
        console.log('🔧 DEBUG: Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'NULL');
        
        if (!token) {
            console.error('❌ No token found! Attempting to get fresh token from Clerk...');
            // Try one more time to get token directly from Clerk
            if (clerk && clerk.session) {
                try {
                    const directToken = await clerk.session.getToken({ skipCache: true });
                    if (directToken) {
                        currentToken = directToken;
                        localStorage.setItem('moneta_session_token', directToken);
                        localStorage.setItem('authToken', directToken);
                        console.log('[Chat] ✅ Got token directly from Clerk session');
                    }
                } catch (e) {
                    console.error('[Chat] ❌ Failed to get token from Clerk:', e);
                }
            }
            
            const finalToken = currentToken || localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
            if (!finalToken) {
                console.error('❌ No token available after all attempts');
                addMessage('⚠️ Authentication error. Please refresh the page and try again.', 'assistant');
                return;
            }
        }
        
        const response = await fetchWithAuth('/api/chat/send', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                thread_id: currentThreadId,
                use_memory_search: true,
                request_id: requestId
            })
        });
        
        console.log('🔧 DEBUG: Response status:', response.status);
        console.log('🔧 DEBUG: Response headers:', [...response.headers.entries()]);
        
        // Add comprehensive response debugging
        console.log('🔧 DEBUG: Response ok:', response.ok);
        console.log('🔧 DEBUG: Response statusText:', response.statusText);
        
        if (response.status === 401) {
            console.error('❌ 401 Unauthorized - Token expired and refresh failed');
            // Try one more aggressive refresh attempt
            console.log('[Chat] Attempting aggressive token refresh after 401...');
            const aggressiveRefresh = await refreshToken();
            if (aggressiveRefresh) {
                console.log('[Chat] ✅ Got new token after 401, but request already failed');
            }
            addMessage('⚠️ Authentication expired. Please refresh the page to continue.', 'assistant');
            return;
        }
        
        const data = await response.json();
        
        // Add comprehensive data debugging
        console.log('🔧 DEBUG: Response data parsed successfully:', data);
        console.log('🔧 DEBUG: data.success:', data.success);
        console.log('🔧 DEBUG: data.response:', data.response);
        console.log('🔧 DEBUG: data.thread_id:', data.thread_id);
        console.log('🔧 DEBUG: data.memory_context:', data.memory_context);
        console.log('🔧 DEBUG: data.error:', data.error);
        
        if (data.success) {
            console.log('🔧 DEBUG: ✅ Data success is true, processing response...');
            currentThreadId = data.thread_id;
            updateThreadTitle();
            
            if (data.memory_context && data.memory_context.length > 0) {
                console.log('🔧 DEBUG: 🧠 Adding message with memories injected:', data.memory_context.length, 'memories');
                addMessageWithMemoriesInjected(data.response, 'assistant', data.memory_context);
                
                // Trigger memory animation with 3 degrees of ancestry
                const activatedMemoryIds = data.memory_context.map(ctx => ctx.id || ctx.memory?.id).filter(id => id);
                console.log('[Memory Animation] Activating', activatedMemoryIds.length, 'memories with 3-degree propagation');
                setTimeout(() => {
                    if (typeof window.animateMemoryActivation === 'function') {
                        window.animateMemoryActivation(activatedMemoryIds);
                        console.log('[Memory Animation] Animation triggered for', activatedMemoryIds);
                    } else {
                        console.warn('[Memory Animation] animateMemoryActivation function not available');
                    }
                }, 200);
            } else {
                console.log('🔧 DEBUG: 💬 Adding regular message (no memories):', data.response);
                addMessage(data.response, 'assistant');
            }
        } else if (response.status !== 409) {
            console.log('🔧 DEBUG: ❌ Data success is false, adding error message');
            addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
        }
    } catch (error) {
        console.error('🔧 DEBUG: ❌ Exception in sendMessage:', error);
        console.error('🔧 DEBUG: ❌ Stack trace:', error.stack);
        addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    } finally {
        // Re-enable UI
        input.disabled = false;
        sendButton.disabled = false;
        sendButton.style.opacity = '1';
        sendButton.style.cursor = 'pointer';
        
        // Reset flags
        isTyping = false;
        sendingMessage = false;
        focusChatInput();
    }
}

// Add message to chat with standard chatbot protocol
function addMessage(content, sender) {
    console.log('🔧 DEBUG: 📝 addMessage called with:', { content, sender });
    
    const messagesContainer = document.getElementById('chat-messages');
    console.log('🔧 DEBUG: 📋 messagesContainer found:', messagesContainer ? 'YES' : 'NO');
    
    const emptyState = messagesContainer.querySelector('.empty-state');
    if (emptyState) {
        console.log('🔧 DEBUG: 🗑️ Removing empty state');
        emptyState.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    messageDiv.innerHTML = `
        <p class="message-content">${content}</p>
    `;
    
    console.log('🔧 DEBUG: 📱 Adding message to container');
    
    // Standard chat protocol: all messages go to the bottom
    messagesContainer.appendChild(messageDiv);
    scrollChatToBottom();
    
    console.log('🔧 DEBUG: ✅ Message added successfully');
}

// Add message with memories injected info
function addMessageWithMemoriesInjected(content, sender, memoryContext) {
    console.log('🔧 DEBUG: 🧠 addMessageWithMemoriesInjected called with:', { content, sender, memoryContext });
    
    const messagesContainer = document.getElementById('chat-messages');
    console.log('🔧 DEBUG: 📋 messagesContainer found:', messagesContainer ? 'YES' : 'NO');
    
    const emptyState = messagesContainer.querySelector('.empty-state');
    if (emptyState) {
        console.log('🔧 DEBUG: 🗑️ Removing empty state');
        emptyState.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    // Build memories injected HTML with collapsible design
    const memoryId = 'memory-' + Date.now();
    let memoriesHtml = '<div class="memories-injected-box">';
    memoriesHtml += `<div class="memories-injected-header" onclick="toggleMemoryInjection('${memoryId}')">`;
    memoriesHtml += '<h4>🧠 Memories Injected <span class="memory-count">(' + (memoryContext ? memoryContext.length : 0) + ')</span></h4>';
    memoriesHtml += '<span class="memories-injected-toggle" id="toggle-' + memoryId + '">▼ Click to view</span>';
    memoriesHtml += '</div>';
    memoriesHtml += `<div class="memories-injected-content" id="${memoryId}">`;
    if (memoryContext && memoryContext.length > 0) {
        memoryContext.forEach(memory => {
            // Skip if memory is null or undefined
            if (!memory) {
                console.log('🔧 DEBUG: ⚠️ Skipping null/undefined memory');
                return;
            }
            
            // Handle both user-specific memories (direct) and global memories (nested)
            const content = memory.content || memory.memory?.content || 'Unknown memory content';
            const score = memory.relevance_score || memory.score || 0;
            memoriesHtml += `<div class="memories-injected-item">${content}<span class="memories-injected-score">(Score: ${score.toFixed ? score.toFixed(2) : score})</span></div>`;
        });
    } else {
        memoriesHtml += '<div class="memories-injected-item">No relevant memories were injected for this prompt.</div>';
    }
    memoriesHtml += '</div></div>';
    
    messageDiv.innerHTML = `
        <p class="message-content">${content}</p>
        ${memoriesHtml}
    `;
    
    // Standard chat protocol: all messages go to the bottom
    messagesContainer.appendChild(messageDiv);
    scrollChatToBottom();
    
    console.log('🔧 DEBUG: ✅ Message with memories added successfully');
}

// Thread management functions
async function newThread() {
    console.log('🔥 Creating new thread...');
    
    // Refresh token on activity
    await refreshToken();
    
    // Create a new empty thread
    const token = localStorage.getItem('authToken');
    const response = await fetch('/api/chat/thread/new', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    });
    
    if (response.ok) {
        const data = await response.json();
        if (data.success) {
            currentThreadId = data.thread_id;
            
            // Clear the chat messages and show new conversation state
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = '<div class="empty-state">Start a new conversation by typing a message below...</div>';
            
            // Update thread title
            updateThreadTitle();
            
            // Reload the thread list to include the new thread
            await loadThreadListAndLast();
            
            focusChatInput();
            console.log('🔥 New thread created:', currentThreadId);
            
            // Ensure memory network stays loaded when switching threads
            if (typeof window.refreshMemoryNetwork === 'function') {
                console.log('🧠 Refreshing memory network for new thread...');
                window.refreshMemoryNetwork();
            }
        }
    } else {
        console.error('Failed to create new thread');
    }
}

async function deleteThread(threadId, event) {
    event.stopPropagation(); // Prevent thread selection
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`/api/chat/thread/${threadId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.ok) {
            await loadThreadListAndLast(true);
        } else {
            console.error('Failed to delete thread');
        }
    } catch (error) {
        console.error('Error deleting thread:', error);
    }
    focusChatInput();
}

async function endThread() {
    console.log('🔧 DEBUG: ========== SAVE MEMORIES CLICKED ==========');
    console.log('🔧 DEBUG: endThread() called');
    
    if (!currentThreadId) {
        console.log('🔧 DEBUG: ❌ No active thread to end');
        addMessage('❌ No active conversation to save memories from.', 'assistant');
        return;
    }

    console.log('🔧 DEBUG: ✅ Current thread ID:', currentThreadId);

    // No confirmation needed - just save memories
    
    console.log('🔧 DEBUG: 🚀 Starting memory extraction process...');
    
    try {
        addMessage('🧠 Extracting memories from conversation...', 'assistant');
        
        console.log('🔧 DEBUG: 📡 Making request to /api/chat/thread/end endpoint');
        console.log('🔧 DEBUG: 📦 Request payload:', JSON.stringify({ thread_id: currentThreadId }));
        
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/chat/thread/end', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ thread_id: currentThreadId })
        });

        console.log('🔧 DEBUG: 📥 Response status:', response.status);
        console.log('🔧 DEBUG: 📥 Response headers:', [...response.headers.entries()]);
        
        const data = await response.json();
        console.log('🔧 DEBUG: 📥 Response data:', JSON.stringify(data, null, 2));

        if (data.success) {
            console.log('🔧 DEBUG: Memory extraction successful!');
            console.log('🔧 DEBUG: Extracted memories count:', data.extracted_memories?.length || 0);
            console.log('🔧 DEBUG: Successful adds:', data.successful_adds || 0);
            
            // Keep the current thread active - DON'T clear it
            // const oldThreadId = currentThreadId;
            // currentThreadId = null;  // REMOVED - keep thread active
            
            if (data.extracted_memories && data.extracted_memories.length > 0) {
                const memoriesText = data.extracted_memories.join('\\n• ');
                addMessage(`✅ ${data.message}\\n\\n📚 Extracted Memories:\\n• ${memoriesText}\\n\\n💡 You can continue this chat or click "New Chat" to start fresh.`, 'assistant');
                console.log('🔧 DEBUG: Added success message with extracted memories');
                
                // Create temporary local nodes immediately for instant feedback
                console.log('🔧 DEBUG: Creating temporary local nodes for extracted memories...');
                data.extracted_memories.forEach((memoryText, index) => {
                    const tempMemory = {
                        id: 'temp_' + Date.now() + '_' + index,
                        content: memoryText,
                        score: 1.0,
                        tags: ['conversation', 'auto-extracted', 'temp'],
                        created: new Date().toISOString()
                    };
                    
                    console.log('🔧 DEBUG: Creating temp node:', tempMemory);
                    
                    // Add to memory network if available
                    if (typeof addMemoryToNetworkRealtime === 'function') {
                        addMemoryToNetworkRealtime(tempMemory);
                        console.log('🔧 DEBUG: Added temp memory to network:', tempMemory.id);
                    } else {
                        console.log('🔧 DEBUG: addMemoryToNetworkRealtime not available');
                    }
                });
                
                // Show success notification
                if (typeof showNewMemoryNotification === 'function') {
                    showNewMemoryNotification(`Added ${data.extracted_memories.length} new memories to network`);
                }
            } else {
                addMessage('✅ Memory extraction completed! No new personal information was found to remember.\\n\\n💡 You can continue this chat or click "New Chat" to start fresh.', 'assistant');
                console.log('🔧 DEBUG: Added success message - no memories extracted');
            }
            
            // DON'T auto-clear the chat - let user continue or start new manually
            console.log('🔧 DEBUG: Chat preserved - user can continue or start new');
            
        } else {
            console.log('🔧 DEBUG: Memory extraction failed:', data.error);
            addMessage(`❌ ${data.error || 'Failed to extract memories from conversation.'}`, 'assistant');
        }
    } catch (error) {
        console.error('🔧 DEBUG: Exception in endThread:', error);
        addMessage('❌ Error extracting memories. Please try again.', 'assistant');
    }
}

function updateThreadTitle(threadIds) {
    const titleElement = document.getElementById('thread-title');
    if (currentThreadId && Array.isArray(threadIds)) {
        const idx = threadIds.indexOf(currentThreadId);
        if (idx !== -1) {
            titleElement.textContent = `Moneta Conversation ${idx + 1}`;
            return;
        }
    }
    titleElement.textContent = 'New Conversation';
}

// Toggle memory injection visibility
function toggleMemoryInjection(memoryId) {
    const content = document.getElementById(memoryId);
    const toggle = document.getElementById('toggle-' + memoryId);
    
    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        toggle.textContent = '▼ Click to view';
        toggle.style.transform = 'rotate(0deg)';
    } else {
        content.classList.add('expanded');
        toggle.textContent = '▲ Click to hide';
        toggle.style.transform = 'rotate(180deg)';
    }
}

// Show notification for newly created memories (HIDDEN - per user request)
function showMemoriesCreatedNotification(memoryCount, memories) {
    console.log('[Memory Created] Notification hidden - ', memoryCount, 'memories created');
    
    // Just trigger the memory animation without showing the yellow box
    if (memories && memories.length > 0) {
        const memoryIds = memories.map(m => m.id).filter(id => id);
        if (memoryIds.length > 0 && typeof window.animateMemoryActivation === 'function') {
            setTimeout(() => {
                window.animateMemoryActivation(memoryIds);
            }, 500);
        }
    }
    // No visual notification shown
}

// Start memory polling to detect newly created memories
let memoryPollingInterval = null;
let lastMemoryPollTime = Date.now();

function startMemoryPolling() {
    if (memoryPollingInterval) {
        clearInterval(memoryPollingInterval);
    }
    
    memoryPollingInterval = setInterval(async () => {
        try {
            const response = await fetchWithAuth('/api/memory/new');
            if (response.ok) {
                const data = await response.json();
                if (data.memories && data.memories.length > 0) {
                    console.log('[Memory Polling] Found', data.count, 'new memories');
                    
                    // Show notification in chat
                    showMemoriesCreatedNotification(data.count, data.memories);
                    
                    // Add to memory network
                    data.memories.forEach(memory => {
                        if (typeof window.addNewMemoryToNetwork === 'function') {
                            window.addNewMemoryToNetwork(memory);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('[Memory Polling] Error:', error);
        }
    }, 2000); // Poll every 2 seconds
    
    console.log('[Memory Polling] Started - checking for new memories every 2 seconds');
}

function stopMemoryPolling() {
    if (memoryPollingInterval) {
        clearInterval(memoryPollingInterval);
        memoryPollingInterval = null;
        console.log('[Memory Polling] Stopped');
    }
}

// Navigate to dashboard
function goToDashboard() {
    console.log('🏠 Navigating to dashboard...');
    const token = localStorage.getItem('authToken');
    if (token) {
        console.log('✅ User is authenticated, redirecting to dashboard');
        window.location.href = '/dashboard';
    } else {
        console.log('⚠️ No authentication token found, redirecting to login');
        window.location.href = '/';
    }
}



function toggleSidebar(forceHide) {
    const sidebar = document.getElementById('thread-sidebar');
    const container = document.querySelector('.container');
    if (forceHide === true) {
        sidebar.classList.add('hidden');
        container.classList.add('sidebar-hidden');
        return;
    }
    const isHidden = sidebar.classList.toggle('hidden');
    container.classList.toggle('sidebar-hidden', isHidden);
}

// --- Thread Sidebar Logic ---
async function loadThreadListAndLast(selectLast = false) {
    // Fetch all thread IDs
    try {
        const threadsRes = await fetchWithAuth('/api/chat/threads');
        
        if (!threadsRes.ok) {
            console.error('Failed to load threads:', threadsRes.status);
            return;
        }
        
        const threadsData = await threadsRes.json();
        const threadIds = threadsData.threads || [];
        renderThreadList(threadIds);
        // If there are threads, select the last or keep current
        if (threadIds.length > 0) {
            if (selectLast || !currentThreadId || !threadIds.includes(currentThreadId)) {
                currentThreadId = threadIds[threadIds.length - 1];
            }
            await loadThread(currentThreadId, threadIds);
        } else {
            // No threads left, clear chat area
            const messagesContainer = document.getElementById('chat-messages');
            if (messagesContainer) {
                messagesContainer.innerHTML = '<div class="empty-state">Start a new conversation by typing a message below...</div>';
            }
            updateThreadTitle(threadIds);
        }
    } catch (error) {
        console.error('Error loading threads:', error);
    }
}

async function loadThread(threadId, threadIds) {
    try {
        const res = await fetchWithAuth(`/api/chat/thread/${threadId}`);
        const data = await res.json();
        currentThreadId = threadId;
        renderThreadList(threadIds); // re-render to highlight
        renderMessages(data.messages);
        updateThreadTitle(threadIds);
        focusChatInput();
        
        // Ensure memory network stays loaded when switching threads
        if (typeof window.refreshMemoryNetwork === 'function') {
            console.log('🧠 Refreshing memory network for thread switch...');
            window.refreshMemoryNetwork();
        }
    } catch (error) {
        console.error('Error loading thread:', error);
    }
}

function renderThreadList(threadIds) {
    const sidebar = document.getElementById('thread-sidebar');
    let list = sidebar.querySelector('.thread-list');
    if (!list) {
        list = document.createElement('div');
        list.className = 'thread-list';
        sidebar.appendChild(list);
    }
    list.innerHTML = '';
    (threadIds || []).forEach((threadId, idx) => {
        const item = document.createElement('div');
        item.className = 'thread-list-item' + (threadId === currentThreadId ? ' active' : '');
        item.dataset.threadId = threadId;
        item.onclick = () => loadThread(threadId, threadIds);
        
        // Create thread title
        const titleSpan = document.createElement('span');
        titleSpan.className = 'thread-title';
        titleSpan.textContent = 'Conversation ' + (idx + 1);
        
        // Create delete button
        const deleteBtn = document.createElement('div');
        deleteBtn.className = 'thread-delete-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.onclick = (event) => deleteThread(threadId, event);
        
        // Add title and delete button to item
        item.appendChild(titleSpan);
        item.appendChild(deleteBtn);
        
        list.appendChild(item);
    });
}

function renderMessages(messages) {
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML = '';
    (messages || []).forEach(msg => {
        if (msg.sender === 'assistant' && msg.memory_context) {
            addMessageWithMemoriesInjected(msg.content, msg.sender, msg.memory_context);
        } else {
            addMessage(msg.content, msg.sender);
        }
    });
    scrollChatToBottom();
}

function focusChatInput() {
    setTimeout(() => {
        const input = document.getElementById('chat-input');
        if (input) input.focus();
    }, 50);
}

// Initialize chat after Clerk authentication
async function initializeChat() {
    console.log('[Chat Init] Starting chat initialization...');
    console.log('[Chat Init] Checking for existing token in localStorage...');
    const existingToken = localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
    console.log('[Chat Init] Existing token:', existingToken ? 'FOUND' : 'NOT FOUND');
    
    // Wait for Clerk to initialize first
    console.log('[Chat Init] Waiting for Clerk to load and restore session...');
    const clerkInitialized = await initChatClerk();
    
    if (!clerkInitialized) {
        console.log('[Chat Init] ⚠️ Clerk initialization failed');
        console.log('[Chat Init] This means either:');
        console.log('[Chat Init]   1. Clerk SDK is not loaded');
        console.log('[Chat Init]   2. No active Clerk session exists');
        console.log('[Chat Init]   3. Session cookies expired or were cleared');
        
        // Check if we have a cached token from previous session
        if (existingToken) {
            console.log('[Chat Init] 🔑 Found cached token, attempting to verify...');
            
            try {
                // Try to verify the cached token with backend
                const response = await fetch('/api/clerk/user', {
                    headers: {
                        'Authorization': `Bearer ${existingToken}`
                    }
                });
                
                if (response.ok) {
                    console.log('[Chat Init] ✅ Cached token is valid! Proceeding with chat...');
                    currentToken = existingToken;
                    
                    // Initialize chat features
                    loadThreadListAndLast();
                    startMemoryPolling();
                    focusChatInput();
                    
                    if (typeof window.refreshMemoryNetwork === 'function') {
                        console.log('🧠 Initial memory network load...');
                        window.refreshMemoryNetwork();
                    }
                    
                    const chatContainer = document.querySelector('.chat-container');
                    if (chatContainer) {
                        chatContainer.addEventListener('click', function() {
                            const sidebar = document.getElementById('thread-sidebar');
                            if (!sidebar.classList.contains('hidden')) {
                                toggleSidebar(true);
                            }
                        });
                    }
                    
                    return; // Success!
                } else {
                    console.log('[Chat Init] ❌ Cached token is invalid or expired');
                }
            } catch (error) {
                console.error('[Chat Init] Error verifying cached token:', error);
            }
        }
        
        // No valid authentication found
        console.log('[Chat Init] ❌ No valid authentication - redirecting to login');
        alert('⚠️ Your session has expired. Please log in again.');
        window.location.href = '/';
        return;
    }
    
    console.log('[Chat Init] ✅ Clerk authenticated - initializing chat features');
    
    // Now that we're authenticated, load chat features
    loadThreadListAndLast();
    
    // Start memory polling for authenticated users
    startMemoryPolling();
    
    focusChatInput();
    
    // Initialize memory network on page load
    if (typeof window.refreshMemoryNetwork === 'function') {
        console.log('🧠 Initial memory network load...');
        window.refreshMemoryNetwork();
    }
    
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.addEventListener('click', function() {
            const sidebar = document.getElementById('thread-sidebar');
            if (!sidebar.classList.contains('hidden')) {
                toggleSidebar(true);
            }
        });
    }
    
    // Add page visibility handler to refresh token when user returns to page
    document.addEventListener('visibilitychange', async () => {
        if (!document.hidden && clerk && clerk.session) {
            console.log('[Chat] Page became visible - refreshing token...');
            await refreshToken();
        }
    });
}

// Call initialization on page load
window.addEventListener('DOMContentLoaded', async function() {
    console.log('[Chat] Page loaded - waiting for Clerk initialization...');
    console.log('[Chat] ⚠️ Anonymous mode is DISABLED - authentication required');
    
    // Initialize chat after Clerk is ready
    await initializeChat();
});
</script>
''' 