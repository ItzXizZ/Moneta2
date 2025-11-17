# Quick Test Guide - JWT Token Fix

## What Was Fixed
✅ JWT tokens no longer expire every few seconds  
✅ Removed anonymous mode - proper authentication required  
✅ Automatic token refresh every 50 seconds  
✅ Auto-retry on 401 errors with fresh token  

## Quick Test Steps

### 1. Start the Server
```bash
cd Moneta2
python start_server.py
```

### 2. Open Browser Console
- Press F12 (Chrome/Edge) or Cmd+Option+I (Mac)
- Go to Console tab
- Keep it open while testing

### 3. Test Dashboard
1. Navigate to `http://localhost:5000`
2. Sign in with Clerk
3. Watch console - should see:
   ```
   [Token Refresh] Auto-refresh enabled (every 50s)
   ```
4. Wait 60+ seconds
5. Should see:
   ```
   [Token Refresh] Refreshing JWT token...
   [Token Refresh] ✅ Token refreshed successfully
   ```
6. Check memory stats still load - no errors

### 4. Test Chat Interface
1. Click "Enter Memory Universe" or go to `/chat`
2. Watch console - should see:
   ```
   [Chat] Page loaded, initializing...
   [Chat Token Refresh] Auto-refresh enabled (every 50s)
   ```
3. Send a few messages
4. Wait 60+ seconds (watch console for token refresh)
5. Send another message - should work fine
6. Memory network should load without errors

### 5. Test Memory Network
1. In chat interface, check right side panel
2. Memory network should be visible
3. Should show your memories as nodes
4. No "anonymous" UUID errors in console
5. Network should update after sending messages

## Expected Console Output

### Good (Success):
```
[Dashboard] Initializing Clerk...
[Dashboard] Clerk initialized successfully
[Token Refresh] Auto-refresh enabled (every 50s)
[Dashboard] Using token for API requests
[Dashboard] Fetching user profile...
[Dashboard] Profile loaded successfully
[Token Refresh] Refreshing JWT token...
[Token Refresh] ✅ Token refreshed successfully
[MEMORY] Clerk user authenticated: 71a57793-...
[MEMORY] Found 3 memories for user '71a57793-...'
```

### Bad (Old Behavior - Should NOT see):
```
❌ [ERROR] JWT token has expired
❌ [ERROR] Invalid JWT token
❌ [MEMORY] _get_user_id returning: 'anonymous'
❌ Error getting memories for user anonymous: invalid input syntax for type uuid
```

## Network Tab Check

1. Open Network tab in DevTools
2. Filter by "api"
3. Watch for API calls to `/api/memory/network`
4. Should NOT see any with status 401
5. If you do see 401, should see immediate retry with status 200

## What If Something Goes Wrong?

### Tokens Still Expiring?
- Check if Clerk is properly initialized
- Look for: `[Token Refresh] Auto-refresh enabled`
- If not present, Clerk SDK may not be loaded

### Still Seeing Anonymous Errors?
- Clear localStorage: `localStorage.clear()`
- Refresh page
- Sign in again

### 401 Errors Not Recovering?
- Check console for: `[Fetch] Got 401, refreshing token and retrying...`
- If missing, token refresh may not be working
- Try refreshing the page

### Memory Network Not Loading?
- Check Network tab for 401 errors on `/api/memory/network`
- Should auto-retry with new token
- If still failing, check if signed in properly

## Success Criteria

✅ Dashboard loads without errors  
✅ Can chat for 5+ minutes without re-authenticating  
✅ Memory network displays correctly  
✅ Token refresh happens automatically every 50s  
✅ No "anonymous" errors in console  
✅ No 401 errors (or they auto-recover)  
✅ No need to click dashboard to re-authenticate  

## Troubleshooting

### Clear Everything and Start Fresh
```javascript
// In browser console:
localStorage.clear();
sessionStorage.clear();
location.reload();
```

### Check Token
```javascript
// In browser console:
console.log('Auth Token:', localStorage.getItem('authToken')?.substring(0, 50));
console.log('Session Token:', localStorage.getItem('moneta_session_token')?.substring(0, 50));
```

### Force Token Refresh
```javascript
// In browser console (while on dashboard or chat):
refreshToken();
```

---

**Need Help?**  
Check `JWT_TOKEN_FIX_SUMMARY.md` for detailed technical explanation.

