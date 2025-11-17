# 🔍 Diagnosing Chat & Memory Issues

## Current Status

Based on your logs:
- ✅ Chat is working (getting responses)
- ❌ No tool calls happening (no memories created)
- ❌ No memory nodes showing
- ❌ Chat history not loading on refresh

## Root Cause

**The user_id is 'anonymous'** - which means:
1. Tool calling is disabled (only works for authenticated users)
2. Memories can't be created
3. Chat history saved under wrong user_id

## Immediate Steps to Debug

### Step 1: Restart the Server

**IMPORTANT:** You MUST restart the Python server for the code changes to take effect!

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python run.py
```

### Step 2: Check Server Logs When You Chat

After restarting, send a message like "I love pizza" and watch for these logs:

**Expected logs (if working):**
```
[DEBUG] _get_user_id called - Authorization header present: True
[DEBUG] Token extracted (first 20 chars): eyJhbGciOiJSUzI1NiIs...
[DEBUG] Is JWT token: True (dots count: 2)
[DEBUG] Verifying Clerk JWT token...
[INFO] Verifying JWT token (first 30 chars): eyJhbGci...
[OK] JWT verified successfully for user: user_2abc123xyz
[INFO] Updated user by clerk_id: info@amcacademy.ca
[OK] Clerk user authenticated: 550e8400-e29b-41d4-a716-446655440000
[DEBUG] _get_user_id returning: '550e8400-e29b-41d4-a716-446655440000'
[INFO] Using OpenAI model: gpt-4o-mini
[DEBUG] USER_ID for tool calling: '550e8400-e29b-41d4-a716-446655440000'
[INFO] ✅ Tool calling ENABLED for user: 550e8400-e29b-41d4-a716-446655440000
[INFO] AI requested 1 tool call(s)
[INFO] Tool call: create_memory with args: {"content": "I love pizza", "tags": ["preference", "food"]}
[OK] Created memory via Clerk: I love pizza
[OK] Final response generated after tool calls
```

**If you see this instead (problem):**
```
[WARN] No Authorization header found - defaulting to anonymous
[DEBUG] _get_user_id returning: 'anonymous'
[WARN] ❌ Tool calling DISABLED - user_id is: 'anonymous'
[OK] Response generated without tool calls
```

### Step 3: If Still Anonymous

The token isn't being sent or recognized. Check:

#### A. Verify Token in Browser

1. Open DevTools (F12)
2. Go to Application tab
3. Local Storage → http://localhost:4000
4. Check for `authToken` key
5. Should contain a long JWT string starting with `eyJ`

**If no authToken:**
- Sign out completely
- Clear browser storage: `localStorage.clear()`
- Sign in again with Clerk

#### B. Verify Token is Being Sent

1. Open DevTools → Network tab
2. Send a chat message
3. Find the `/api/chat/send` request
4. Click it → Headers tab
5. Scroll to "Request Headers"
6. Should see: `Authorization: Bearer eyJhbGci...`

**If Authorization header is missing:**
- The frontend isn't sending the token
- Check browser console for JavaScript errors

### Step 4: If JWT Verification Fails

If you see:
```
[DEBUG] Clerk JWT verification failed, trying legacy: ...
```

**Possible causes:**
1. **CLERK_SECRET_KEY wrong** - Check your `.env` file
2. **JWKS URL wrong** - Check server startup logs for JWKS URL
3. **Token expired** - Sign out and sign in again
4. **Wrong Clerk instance** - Verify publishable key matches

## Quick Fix Checklist

- [ ] **Restart server** (python run.py)
- [ ] **Check browser has authToken** in localStorage
- [ ] **Clear browser storage** if no token
- [ ] **Sign out and sign in again**
- [ ] **Send test message** ("I love pizza")
- [ ] **Check server logs** for authentication flow
- [ ] **Verify user_id is NOT 'anonymous'**
- [ ] **Look for tool calling enabled message**

## Expected Flow (When Working)

### Frontend:
```javascript
1. User types "I love pizza"
2. JavaScript gets token: localStorage.getItem('authToken')
3. Sends to: POST /api/chat/send
4. Headers: Authorization: Bearer {token}
```

### Backend:
```python
1. chat.py receives request
2. _get_user_id() extracts token
3. Detects JWT (has dots)
4. clerk_rest_api verifies JWT
5. Gets user_id from Supabase
6. Passes to openai_service
7. Tool calling enabled for user
8. AI calls create_memory
9. Memory saved to Supabase
10. Response returned
```

### Result:
- ✅ Memory created in `user_memories` table
- ✅ Memory node appears on frontend
- ✅ AI acknowledges memory creation
- ✅ Chat history saved under correct user_id

## Still Not Working?

### Provide These Logs:

1. **Server startup logs** (first 50 lines)
2. **Logs when sending a message** (complete flow)
3. **Browser console errors** (if any)
4. **Network tab** showing the /api/chat/send request headers

### Quick Test Command:

```bash
# In browser console:
console.log('Token:', localStorage.getItem('authToken') ? 'Present' : 'Missing');
console.log('User:', localStorage.getItem('user'));

# Should show:
# Token: Present
# User: {"id":"...","email":"info@amcacademy.ca",...}
```

## Nuclear Option: Complete Reset

If nothing works:

```bash
# 1. Stop server
# 2. Clear browser completely
localStorage.clear()
sessionStorage.clear()
# 3. Close browser
# 4. Restart server
python run.py
# 5. Open new incognito window
# 6. Sign in fresh
# 7. Try again
```

---

**Next:** After restart, paste the server logs here so I can see what's happening!

