# Clerk Chat Authentication Fix

## Problem
The chat interface at `/chat` was showing "Please log in to use the chat" alert and redirecting users to the home page, even after they were authenticated through the dashboard.

## Root Cause
1. **Strict Authentication Check**: The `initializeChat()` function was too strict - if Clerk failed to initialize or restore the session, it would immediately redirect without checking for cached tokens
2. **Token Template Issues**: The `getToken({ template: 'supabase' })` call was failing in some cases without a fallback
3. **Session Restoration Timing**: Clerk needs time to restore sessions from cookies, but the timeout was too short
4. **Inconsistent Token Storage**: Different parts of the app were looking for tokens in different localStorage keys

## Fixes Applied

### 1. **Improved Token Retrieval** (`chat_javascript.py`)
```javascript
// Added fallback for token template
let token = null;
try {
    token = await clerk.session.getToken({ 
        skipCache: true,
        template: 'supabase'
    });
} catch (templateError) {
    console.warn('[Chat] Template token failed, trying default:', templateError);
    // Fallback to default token
    token = await clerk.session.getToken({ skipCache: true });
}
```

### 2. **Graceful Fallback to Cached Token** (`chat_javascript.py`)
```javascript
// If Clerk fails, try to use cached token
if (!clerkInitialized) {
    if (existingToken) {
        // Verify cached token with backend
        const response = await fetch('/api/clerk/user', {
            headers: { 'Authorization': `Bearer ${existingToken}` }
        });
        
        if (response.ok) {
            // Token is valid, proceed with chat
            currentToken = existingToken;
            // Initialize chat features...
            return;
        }
    }
    // Only redirect if no valid token found
    alert('⚠️ Your session has expired. Please log in again.');
    window.location.href = '/';
}
```

### 3. **Increased Session Restoration Time** (`chat_javascript.py`)
```javascript
// Give Clerk more time to restore session from cookies
await new Promise(resolve => setTimeout(resolve, 1000)); // Increased from 500ms
```

### 4. **Better Error Logging** (`chat_javascript.py`)
Added comprehensive error logging to help debug authentication issues:
```javascript
console.error('[Chat] Token error details:', error.message, error.stack);
console.log('[Chat] Session:', clerk.session);
console.log('[Chat] User:', clerk.user);
```

### 5. **Unified Token Storage** (`chat_javascript.py`, `memory_network_javascript.py`)
```javascript
// Check both possible token locations
const token = localStorage.getItem('authToken') || localStorage.getItem('moneta_session_token');
```

### 6. **Dynamic Clerk Key Injection** (`main.py`)
```python
# Inject Clerk key from config instead of hardcoding
template_with_key = CHAT_INTERFACE_TEMPLATE.replace(
    'data-clerk-publishable-key="pk_test_..."',
    f'data-clerk-publishable-key="{config.clerk_publishable_key}"'
)
```

## How It Works Now

### Authentication Flow
1. **User logs in** via landing page → Clerk session created
2. **User navigates to dashboard** → Session restored, token refreshed
3. **User clicks "Start Chatting"** to go to `/chat`:
   - Chat page loads with Clerk SDK
   - JavaScript attempts to restore Clerk session (with 1000ms timeout)
   - **If Clerk succeeds**: Get fresh token and proceed
   - **If Clerk fails**: Check for cached token in localStorage
   - **If cached token valid**: Verify with backend and proceed
   - **If no valid token**: Show alert and redirect to home

### Token Management
- Tokens are stored in both `authToken` and `moneta_session_token` for compatibility
- Chat checks both locations before giving up
- Memory network also checks both locations
- Token is verified with backend before proceeding

## Testing Instructions

1. **Fresh Login Test**:
   - Clear browser cache and localStorage
   - Go to `http://localhost:4000`
   - Log in with Google via Clerk
   - Navigate to dashboard
   - Click "Enter Memory Universe" or "Start Chatting"
   - ✅ Should load chat interface without "Please log in" alert

2. **Refresh Test**:
   - After logging in and using chat
   - Refresh the `/chat` page (F5)
   - ✅ Should stay authenticated using cached token

3. **Session Expiry Test**:
   - Log in and use chat
   - Clear localStorage manually: `localStorage.clear()`
   - Refresh page
   - ✅ Should show "session expired" alert and redirect to login

## Files Modified
- `app/core/chat_javascript.py` - Improved authentication logic
- `app/core/memory_network_javascript.py` - Unified token storage keys
- `app/blueprints/main.py` - Dynamic Clerk key injection

## Benefits
- ✅ More robust authentication that handles Clerk SDK issues
- ✅ Better user experience - no unnecessary logouts
- ✅ Graceful fallbacks when Clerk is slow or fails
- ✅ Comprehensive error logging for debugging
- ✅ Consistent token management across the app

## Notes
- The fix maintains security by always verifying tokens with the backend
- Cached tokens are only used if they pass backend verification
- Users are only redirected to login if truly unauthenticated
- All authentication errors are logged for debugging

