# JWT Token Expiration Fix Summary

## Problem
JWT tokens from Clerk were expiring every ~60 seconds, causing:
- 401 authentication errors in the chat interface
- User being logged out or getting "anonymous" mode errors
- Having to manually refresh/reclick dashboard to get a new token
- Database errors: `invalid input syntax for type uuid: "anonymous"`

## Root Causes
1. **No Token Refresh**: Frontend was not automatically refreshing JWT tokens before expiration
2. **Anonymous Mode Fallback**: Backend was falling back to 'anonymous' user when tokens expired
3. **No Retry Logic**: Failed API calls with 401 errors were not being retried with fresh tokens

## Solutions Implemented

### 1. Backend Changes

#### `Moneta2/app/blueprints/memory.py`
**Removed anonymous mode** - All memory endpoints now require authentication:
- `_get_user_id()` function now returns `None` instead of `'anonymous'` when auth fails
- All endpoints (`/network`, `/user`, `/add`, `/search`) now return 401 errors when `user_id` is `None`
- Removed fallback to anonymous mode entirely

**Changes:**
```python
# Before: Returned 'anonymous' when auth failed
user_id = 'anonymous'

# After: Returns None when auth fails
return None

# All endpoints now check:
if not user_id:
    return jsonify({
        'error': 'Authentication required',
        'message': 'Please sign in to access...'
    }), 401
```

### 2. Frontend Changes

#### `Moneta2/templates/dashboard.html`
**Added automatic token refresh system:**

1. **Token Refresh Function** (lines 570-595):
   - Automatically refreshes JWT tokens using Clerk
   - Updates localStorage with new token
   - Called every 50 seconds (tokens expire after ~60 seconds)

2. **Auto-Refresh Interval** (lines 598-619):
   - `startTokenRefresh()` - Starts automatic refresh every 50 seconds
   - `stopTokenRefresh()` - Stops refresh on logout
   - Runs automatically when user is authenticated

3. **Smart Fetch Wrapper** (lines 622-665):
   - `fetchWithAuth()` - Wraps all API calls with automatic token management
   - Automatically includes Authorization header
   - Detects 401 errors and refreshes token
   - Retries failed requests once with new token
   - Redirects to login if refresh fails

4. **Updated API Calls**:
   - All API calls now use `fetchWithAuth()` instead of raw `fetch()`
   - Automatic retry on 401 errors
   - Token stored in `currentToken` variable for immediate access

#### `Moneta2/app/core/chat_javascript.py`
**Added same token refresh system to chat interface:**

1. **Clerk Initialization** (lines 14-34):
   - `initChatClerk()` - Initializes Clerk in chat interface
   - Called on page load
   - Starts automatic token refresh

2. **Token Refresh Functions** (lines 37-82):
   - Same refresh logic as dashboard
   - Refreshes every 50 seconds
   - Updates localStorage automatically

3. **Smart Fetch Wrapper** (lines 85-126):
   - `fetchWithAuth()` with same retry logic
   - Handles 401 errors gracefully
   - Shows user-friendly error messages

4. **Updated API Calls**:
   - `sendMessage()` - Uses `fetchWithAuth()`
   - `loadThreadListAndLast()` - Uses `fetchWithAuth()`
   - `loadThread()` - Uses `fetchWithAuth()`
   - All wrapped in try-catch for error handling

5. **Page Load Initialization** (lines 584-607):
   - Automatically initializes Clerk on page load
   - Sets up token refresh
   - Loads current token from localStorage

## How It Works Now

### Token Lifecycle
```
1. User logs in via Clerk
   ↓
2. JWT token obtained (valid for ~60 seconds)
   ↓
3. Token stored in:
   - localStorage.authToken
   - localStorage.moneta_session_token
   - currentToken variable
   ↓
4. Auto-refresh starts (every 50 seconds)
   ↓
5. Before token expires (at 50s):
   - Clerk refreshes token automatically
   - New token stored in all locations
   ↓
6. If API call gets 401:
   - Token refresh triggered immediately
   - Request retried with new token
   - If still fails → redirect to login
```

### API Call Flow
```
API Call Made
   ↓
fetchWithAuth() wrapper
   ↓
Add Authorization header
   ↓
Send request
   ↓
Got 401? 
   ├─ No → Return response
   └─ Yes → Refresh token
         ↓
      Got new token?
         ├─ Yes → Retry request
         └─ No → Redirect to login
```

## Benefits

1. **Seamless UX**: Users never experience token expiration
2. **No Manual Refresh**: No need to click dashboard to re-authenticate
3. **Error-Free**: No more "anonymous" UUID errors
4. **Automatic Recovery**: Failed requests retry automatically
5. **Secure**: Tokens still expire regularly but refresh transparently

## Testing

### What to Test:
1. **Dashboard**:
   - Load dashboard → Should see auto-refresh in console every 50s
   - Stay on dashboard for 2+ minutes → Should not get logged out
   - Check memory stats → Should load without errors

2. **Chat Interface**:
   - Start chatting
   - Continue conversation for 2+ minutes
   - Memory network should load correctly
   - No 401 errors or "anonymous" errors

3. **Token Expiration**:
   - Watch console logs
   - Should see: `[Token Refresh] ✅ Token refreshed successfully` every 50s
   - No 401 errors in network tab

4. **Error Recovery**:
   - If internet drops and reconnects
   - Should automatically recover
   - May need to refresh page if session fully expired

## Console Logs to Look For

### Success:
```
[Chat Token Refresh] Auto-refresh enabled (every 50s)
[Token Refresh] Refreshing JWT token...
[Token Refresh] ✅ Token refreshed successfully
```

### Failure (Expected when token truly expires):
```
[Token Refresh] ❌ Failed to get new token
[Fetch] Got 401, refreshing token and retrying...
[Fetch] Still getting 401 after token refresh - session expired
```

## Files Changed

1. `Moneta2/app/blueprints/memory.py` - Removed anonymous mode
2. `Moneta2/templates/dashboard.html` - Added token refresh
3. `Moneta2/app/core/chat_javascript.py` - Added token refresh

## Migration Notes

- No database changes required
- No environment variable changes required
- Backward compatible with existing tokens
- Users currently logged in will need to refresh once

## Future Improvements

1. Add visual indicator when token is being refreshed
2. Add "Session expiring" warning at 5 minutes
3. Store refresh timestamp to avoid unnecessary refreshes
4. Add token refresh retry with exponential backoff
5. Implement refresh token (currently using short-lived JWT only)

---

**Date**: November 17, 2025  
**Issue**: JWT Token Expiration Every Few Seconds  
**Status**: ✅ Fixed

