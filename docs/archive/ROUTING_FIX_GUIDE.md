# 🔧 Routing Fix Guide - Get Your Routes Working!

## The Problem

You're seeing routes registered in the terminal output, but getting **404 errors** when accessing them. This is caused by:
1. Flask's debug mode reloader creating multiple app instances
2. Template folder path issues

## ✅ What I Fixed

### 1. Updated `app/__init__.py`
- ✅ Changed template folder to use **absolute paths** instead of relative paths
- ✅ Added debug output to show directory paths
- ✅ Fixed static folder configuration

### 2. Created Test Scripts
- ✅ `test_routes.py` - Simple server to test routes without reloader
- ✅ `setup_env.py` - Interactive script to create your .env file

---

## 🚀 Step-by-Step Fix

### Step 1: Stop the Current Server
Press `CTRL+C` in your terminal to stop the running server.

### Step 2: Set Up Your .env File

**Option A: Interactive Setup (Recommended)**
```bash
python setup_env.py
```

**Option B: Manual Setup**
```bash
copy ENV_TEMPLATE.txt .env
```
Then edit `.env` and add your keys:
- Clerk: https://dashboard.clerk.com/ → API Keys
- Supabase: https://app.supabase.com/ → Settings → API
- OpenAI: https://platform.openai.com/api-keys

### Step 3: Test Routes (Without Debug Reloader)
```bash
python test_routes.py
```

This will:
- Show all registered routes
- Start a simple server on http://localhost:5000
- **No reloader issues!**

Try accessing:
- http://localhost:5000/hello
- http://localhost:5000/
- http://localhost:5000/debug

If these work, your routes are fine! The issue was the debug reloader.

### Step 4: Fix the Main run.py (if test_routes.py works)

If `test_routes.py` works but `run.py` doesn't, here's the fix:

**Edit `run.py` and change line 51-55 from:**
```python
app.run(
    debug=debug,
    host='0.0.0.0',
    port=port
)
```

**To:**
```python
app.run(
    debug=False,  # Turn off debug mode temporarily
    host='0.0.0.0',
    port=port,
    use_reloader=False  # Disable reloader
)
```

Then run:
```bash
python run.py
```

### Step 5: Set Up Database Tables

1. Go to https://app.supabase.com/
2. Select your project
3. Go to SQL Editor
4. Copy the content from `docs/CLERK_SUPABASE_SCHEMA.sql`
5. Paste and execute

---

## 🔍 Verify Clerk Setup

### Test 1: Check Environment Variables
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Clerk Secret:', bool(os.getenv('CLERK_SECRET_KEY'))); print('Clerk Pub:', bool(os.getenv('CLERK_PUBLISHABLE_KEY')))"
```

### Test 2: Access Debug Route
Go to: http://localhost:4000/debug

You should see JSON showing your Clerk configuration.

### Test 3: Access Landing Page
Go to: http://localhost:4000/

You should see:
- The landing page loads (not 404)
- Clerk buttons appear (if keys are configured)
- Google Sign In button is visible

---

## 🎯 Expected Behavior

### With Clerk Keys Configured:
✅ `/` → Shows `landing_clerk.html` with Google Sign In button
✅ `/hello` → Shows "Hello! Routes are working!"
✅ `/debug` → Shows JSON with Clerk config
✅ `/test-clerk` → Force loads Clerk landing page
✅ `/test-legacy` → Force loads legacy landing page

### Without Clerk Keys:
✅ `/` → Shows `landing.html` with traditional login forms
✅ All other routes still work

---

## 🐛 Troubleshooting

### Issue: Still Getting 404 Errors
**Solution 1: Check your working directory**
```bash
cd Moneta2/Moneta2
python run.py
```
Make sure you're in the inner `Moneta2` folder (the one with `run.py`).

**Solution 2: Verify template folder**
When you run the server, look for these debug messages:
```
[DEBUG] Base directory: C:\Users\...\Moneta2\Moneta2
[DEBUG] Template directory: C:\Users\...\Moneta2\Moneta2\templates
[DEBUG] Static directory: C:\Users\...\Moneta2\Moneta2\app\static
```

If these paths are wrong, there's a directory structure issue.

### Issue: Clerk Not Loading
1. ✅ Check `.env` file exists in the same folder as `run.py`
2. ✅ Check `CLERK_SECRET_KEY` and `CLERK_PUBLISHABLE_KEY` are set
3. ✅ Visit `/debug` to see what Flask sees
4. ✅ Check browser console for JavaScript errors (F12)

### Issue: Google Sign In Button Not Showing
1. ✅ Enable Google OAuth in Clerk Dashboard:
   - Go to https://dashboard.clerk.com/
   - Click your application
   - Go to "Social Connections"
   - Enable Google
   - Save changes

2. ✅ Check Clerk script is loading:
   - Open browser console (F12)
   - Look for Clerk-related errors
   - Try `/test-clerk` to force load Clerk page

---

## 📝 Quick Reference

### Files Changed
- ✅ `app/__init__.py` - Fixed template/static folder paths
- ✅ `test_routes.py` - NEW: Test server without reloader
- ✅ `setup_env.py` - NEW: Interactive .env setup

### Files You Need to Create
- ⚠️  `.env` - Your API keys (use `setup_env.py` to create)

### Commands to Run
```bash
# Step 1: Set up environment
python setup_env.py

# Step 2: Test routes
python test_routes.py

# Step 3: Run main server
python run.py
```

---

## 🎉 Success Checklist

After following this guide, you should have:

- [x] `.env` file with all keys
- [x] Routes working (tested with `test_routes.py`)
- [x] Landing page showing Clerk interface
- [x] Google Sign In button visible
- [x] No 404 errors on `/hello`, `/`, `/debug`
- [x] Database tables created in Supabase

---

## 🆘 Still Having Issues?

If you're still seeing problems:

1. **Show me the output** of:
   ```bash
   python test_routes.py
   ```

2. **Show me your directory structure**:
   ```bash
   dir
   ```

3. **Show me the debug output** when accessing `/`:
   - Look in the terminal where you ran `python run.py`
   - Copy the `[DEBUG]` lines

4. **Check if `.env` exists**:
   ```bash
   dir .env
   ```

Then I can help you debug further!

