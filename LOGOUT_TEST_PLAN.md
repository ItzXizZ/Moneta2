# Logout Fix - Test Plan

## Quick Test Steps

### 1. Test Normal Logout
1. Start your Flask server: `python run.py` or `python start_server.py`
2. Navigate to `http://localhost:5000/`
3. Sign in with Google
4. Verify you're redirected to `/dashboard`
5. Click the "Sign Out" button (top-right)
6. **Expected Result**: 
   - You should be redirected to landing page
   - Landing page should show "Sign in with Google" button
   - Should NOT auto-redirect back to dashboard

### 2. Test Re-login After Logout
1. After completing Test #1 (you're logged out on landing page)
2. Click "Sign in with Google"
3. Complete Google sign-in
4. **Expected Result**:
   - Should successfully sign in
   - Should redirect to `/dashboard`
   - Dashboard should load with your user info

### 3. Test Multiple Logout/Login Cycles
1. Repeat Tests #1 and #2 three times in a row
2. **Expected Result**:
   - Each logout should work correctly
   - Each login should work correctly
   - No "stuck" states or infinite redirects

### 4. Check Console Logs

#### During Logout (Dashboard Console):
Open browser DevTools (F12) and watch the console during logout. You should see:

```
[Dashboard] 🚪 Starting logout process...
[Dashboard] ✅ Set logging_out flag in sessionStorage
[Dashboard] ✅ Cleared all localStorage data
[Dashboard] Signing out from Clerk and WAITING...
[Dashboard] ✅ Clerk sign out complete
[Dashboard] 🏠 Redirecting to home with logout flag...
```

#### After Redirect (Landing Page Console):
After redirect to landing page, you should see:

```
[Landing] 🚪🚪🚪 LOGOUT DETECTED FROM URL PARAMETER 🚪🚪🚪
[Landing] User just logged out - preventing auto-login
[Landing] Clerk loaded, signing out any active sessions...
[Landing] Found active Clerk session, signing out...
  OR
[Landing] No active Clerk session found
[Landing] ✅ Logout complete - ready for new sign-in
```

### 5. Check Storage (Optional Debug)

During/after logout, check browser storage (DevTools → Application tab):

**localStorage** should be empty:
- No `moneta_user`
- No `moneta_session_token`
- No `moneta_session_id`

**sessionStorage** should be cleared after landing page loads:
- `logging_out` flag should be present briefly, then removed

## What Was Fixed

### Before the Fix:
```
Dashboard → Click Logout → Landing Page → 
  Clerk still has session → Auto-generate JWT → 
  Redirect to Dashboard → Still logged in! ❌
```

### After the Fix:
```
Dashboard → Click Logout → 
  Set flags → Clear storage → Sign out Clerk → 
  Landing Page → Detect logout flag → 
  Force Clerk sign out → Show sign-in button ✅
```

## Troubleshooting

### Issue: Still auto-redirecting to dashboard after logout

**Check:**
1. Make sure you saved both files:
   - `Moneta2/templates/dashboard.html`
   - `Moneta2/templates/landing_clerk.html`

2. Hard refresh the pages (Ctrl+Shift+R or Cmd+Shift+R) to clear browser cache

3. Restart your Flask server to ensure latest templates are loaded

4. Check console logs - you should see the emoji indicators (`🚪🚪🚪`, `🛑`, etc.)

### Issue: Get an error during logout

**Check:**
1. Console logs for specific error messages
2. Make sure Clerk SDK is loading properly
3. Check network tab for failed requests

### Issue: Can't sign back in after logout

**Check:**
1. Console logs for error messages
2. Make sure `/api/clerk/session` endpoint is working
3. Verify Clerk keys are configured properly

## Success Criteria

✅ Logout redirects to landing page with sign-in button  
✅ No auto-redirect back to dashboard after logout  
✅ Can sign back in after logout  
✅ Multiple logout/login cycles work correctly  
✅ Console logs show proper flow messages  
✅ Storage is cleared after logout

## If You Find Issues

If the logout still doesn't work after these changes:

1. Check browser console for error messages
2. Check Flask server logs
3. Verify both template files were saved with the changes
4. Try in an incognito/private browser window to rule out cached data
5. Share the console logs with me for debugging

## Questions?

If you encounter any issues or need clarification, let me know:
- What step failed?
- What error messages do you see?
- What browser are you using?
- Can you share console logs?

