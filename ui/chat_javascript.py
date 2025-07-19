#!/usr/bin/env python3

# Chat JavaScript Component with all functionality
CHAT_JAVASCRIPT = '''
<script>
let currentThreadId = null;
let isTyping = false;
let sendingMessage = false;

// Handle authentication errors
function handleAuthError(response) {
    if (response.status === 401) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        // Don't redirect for now - just log the error
        console.log('⚠️ Authentication error - continuing without auth');
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
        const token = localStorage.getItem('authToken');
        console.log('🔧 DEBUG: Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'NULL');
        
        if (!token) {
            console.error('❌ No token found in localStorage!');
            addMessage('⚠️ Running without authentication - some features may be limited.', 'assistant');
            // Continue without token for now
        }
        
        const response = await fetch('/send_message', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
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
            console.error('❌ 401 Unauthorized - Token may be expired or invalid');
            console.log('🔧 DEBUG: Clearing invalid token and continuing without auth...');
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
            addMessage('⚠️ Authentication error - continuing without user-specific features.', 'assistant');
            // Continue without redirect
            return;
        }
        
        if (handleAuthError(response)) return;
        
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
                
                // Trigger memory animation
                const activatedMemoryIds = data.memory_context.map(ctx => ctx.id || ctx.memory?.id).filter(id => id);
                setTimeout(() => {
                    if (memoryNetwork && networkData.nodes.length > 0) {
                        animateMemoryActivation(activatedMemoryIds);
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
    
    // Create a new empty thread
    const token = localStorage.getItem('authToken');
    const response = await fetch('/chat_history/new', {
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
        const response = await fetch(`/chat_history/${threadId}`, {
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
        
        console.log('🔧 DEBUG: 📡 Making request to /end_thread endpoint');
        console.log('🔧 DEBUG: 📦 Request payload:', JSON.stringify({ thread_id: currentThreadId }));
        
        const token = localStorage.getItem('authToken');
        const response = await fetch('/end_thread', {
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

// Auto-hide sidebar when clicking chat area
window.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.addEventListener('click', function() {
        const sidebar = document.getElementById('thread-sidebar');
        if (!sidebar.classList.contains('hidden')) {
            toggleSidebar(true);
        }
    });
});

// --- Thread Sidebar Logic ---
async function loadThreadListAndLast(selectLast = false) {
    // Fetch all thread IDs
    const token = localStorage.getItem('authToken');
    const threadsRes = await fetch('/chat_history/threads', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
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
}

async function loadThread(threadId, threadIds) {
    const token = localStorage.getItem('authToken');
    const res = await fetch(`/chat_history/${threadId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
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

// Call focusChatInput on page load
window.addEventListener('DOMContentLoaded', function() {
    // Check if user is authenticated
    const token = localStorage.getItem('authToken');
    if (!token) {
        console.log('⚠️ No authentication token found - running without user-specific features');
        // Don't redirect, just continue without auth
    } else {
        loadThreadListAndLast();
    }
    
    focusChatInput();
    
    // Initialize memory network on page load
    if (typeof window.refreshMemoryNetwork === 'function') {
        console.log('🧠 Initial memory network load...');
        window.refreshMemoryNetwork();
    }
    
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.addEventListener('click', function() {
        const sidebar = document.getElementById('thread-sidebar');
        if (!sidebar.classList.contains('hidden')) {
            toggleSidebar(true);
        }
    });
});
</script>
''' 