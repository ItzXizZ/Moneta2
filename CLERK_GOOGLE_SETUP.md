# Clerk Google Sign-In Setup Guide

## ✅ What's Been Fixed

Your Moneta application has been updated to properly work with Clerk authentication:

1. **Landing Page**: Updated `landing_clerk.html` to dynamically load Clerk SDK with your publishable key
2. **Authentication Flow**: Fixed sign-in, sign-out, and session management
3. **Backend Integration**: Clerk REST API is properly configured and running

## 🔑 Step 1: Verify Environment Variables

Make sure your `.env` file has these keys (they should already be set based on your terminal output):

```bash
CLERK_SECRET_KEY=sk_test_your_actual_secret_key
CLERK_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
OPENAI_API_KEY=sk-proj-your_openai_key
```

## 🔐 Step 2: Enable Google OAuth in Clerk Dashboard

**This is the most critical step!** You need to enable Google as a sign-in method in your Clerk Dashboard:

1. **Go to Clerk Dashboard**: https://dashboard.clerk.com/
2. **Select your application** (or create one if you haven't)
3. **Navigate to**: `User & Authentication` → `Social Connections` (or `Social Login`)
4. **Enable Google**:
   - Click on **Google** 
   - Toggle it **ON**
   - You can use Clerk's default OAuth credentials for testing, or add your own Google OAuth credentials for production

5. **Configure Redirect URLs** (if needed):
   - In your Clerk Dashboard, go to `Paths`
   - Make sure the redirect URLs include:
     - `http://localhost:4000`
     - `http://localhost:4000/dashboard`

## 🌐 Step 3: Test the Authentication

1. **Restart your server** if it's already running:
   ```bash
   python run.py
   ```

2. **Open your browser** and go to:
   ```
   http://localhost:4000
   ```

3. **Click "Sign in with Google"** button

4. **You should see**:
   - A Clerk modal popup appear
   - Google sign-in option available
   - After signing in, you'll be redirected to the dashboard

## 🐛 Troubleshooting

### Issue: "Authentication not configured" error

**Solution**: Check that your environment variables are loaded:
- Make sure the `.env` file is in the `Moneta2` directory
- Restart the Flask server after changing `.env`
- Check the terminal for `[OK] Clerk REST API initialized` message

### Issue: No Google sign-in option in Clerk modal

**Solution**: 
- Go to Clerk Dashboard → Social Connections
- Make sure Google is **enabled** and **toggled ON**
- It can take a minute for changes to propagate

### Issue: "Redirect URL mismatch" error

**Solution**:
- In Clerk Dashboard → Paths
- Add `http://localhost:4000/dashboard` to allowed redirect URLs
- Save changes

### Issue: User signed in but can't access dashboard

**Solution**: 
- Check browser console (F12) for errors
- Make sure Supabase is properly configured
- Verify that the `users` table exists in Supabase

## 📊 Check Server Logs

Your server should show these messages on startup:

```
[OK] OpenAI client initialized successfully
[OK] Clerk REST API initialized (no async issues!)
[OK] Clerk REST API initialized (no async issues!)
[INFO] Starting Moneta - AI Memory Management System...
[INFO] Open your browser and go to: http://localhost:4000
```

## 🎯 What Happens When You Sign In

1. **Frontend**: Clerk handles Google OAuth
2. **Session Created**: Clerk creates a secure session
3. **Backend Sync**: Your app syncs user data to Supabase
4. **User Record Created**: New user record in `users` table
5. **Memory Database**: Personal memory database created
6. **Redirect**: User redirected to dashboard

## 🚀 Next Steps

After Google sign-in works:

1. **Test the Dashboard**: Navigate to `/dashboard`
2. **Test the Chat**: Navigate to `/chat` 
3. **Create Memories**: Chat with the AI and watch memories form
4. **View Memory Network**: See your memories visualized

## 💡 Pro Tips

- **Development**: Use Clerk's built-in Google OAuth (no Google Cloud setup needed)
- **Production**: Add your own Google OAuth credentials in Clerk for better branding
- **Testing**: Use incognito mode to test sign-in flow from scratch
- **Debugging**: Open browser DevTools (F12) to see console logs

## 📱 Production Deployment

When deploying to production (Render, Heroku, etc.):

1. **Add your production domain** to Clerk Dashboard:
   - Go to `Domains` in Clerk Dashboard
   - Add your production URL (e.g., `https://your-app.onrender.com`)

2. **Update environment variables** on your hosting platform

3. **Update redirect URLs** in Clerk to include production domain

---

## ✨ Your Authentication is Now Ready!

The code has been updated and should work once you **enable Google OAuth in the Clerk Dashboard**. This is a one-time configuration step that takes about 30 seconds.

**Need help?** Check the browser console (F12) and server logs for detailed error messages.


