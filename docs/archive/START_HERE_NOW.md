# 🚀 START HERE NOW - Quick Fix for Routing & Clerk

## What Was Wrong
1. ❌ Routes showing as registered but returning 404 errors
2. ❌ Clerk not showing on landing page
3. ❌ Template folder using relative paths (causing issues)
4. ❌ Flask debug reloader creating duplicate app instances

## What I Fixed
1. ✅ Fixed `app/__init__.py` - Now uses absolute paths for templates and static files
2. ✅ Created `test_routes.py` - Test server without reloader issues
3. ✅ Created `setup_env.py` - Interactive script to set up your Clerk and API keys
4. ✅ Created `ROUTING_FIX_GUIDE.md` - Complete troubleshooting guide

---

## 🎯 Do This Now (3 Steps - 5 minutes)

### Step 1: Stop Your Server
Press `CTRL+C` in your terminal.

### Step 2: Set Up Your .env File
```bash
python setup_env.py
```

Follow the prompts and paste your:
- **Clerk Secret Key** (from https://dashboard.clerk.com/ → API Keys)
- **Clerk Publishable Key** (from same place)
- Skip the others for now if you want to test Clerk first

### Step 3: Test Your Routes
```bash
python test_routes.py
```

Then open your browser to:
- http://localhost:5000/hello ← Should say "Hello! Routes are working!"
- http://localhost:5000/ ← Should show the landing page

---

## ✅ If test_routes.py Works

Great! Your routes are fine. The issue was the debug reloader.

Now run the main server:
```bash
python run.py
```

Go to: http://localhost:4000/

You should now see:
- ✅ Landing page loads (not 404!)
- ✅ Clerk is attempting to load
- ✅ Google Sign In button appears (if Clerk keys are set)

---

## 🔧 If You Still Get 404 Errors

### Check 1: Are You in the Right Directory?
```bash
cd Moneta2
dir
```

You should see:
- `run.py`
- `app/` folder
- `templates/` folder
- `config.py`

### Check 2: Does .env Exist?
```bash
dir .env
```

If not found, run:
```bash
python setup_env.py
```

### Check 3: What Does the Debug Output Say?
When you run `python test_routes.py`, look for:
```
[DEBUG] Base directory: ...
[DEBUG] Template directory: ...
[DEBUG] Static directory: ...
```

Are these paths correct?

---

## 🎯 Enable Google Sign In

Once routes are working:

### 1. Get Clerk Keys
1. Go to https://dashboard.clerk.com/
2. Create a free account
3. Create a new application
4. Go to **"Social Connections"** → Enable **Google**
5. Go to **"API Keys"** → Copy both keys
6. Run `python setup_env.py` again or edit `.env` manually

### 2. Set Up Database
1. Go to https://app.supabase.com/
2. Create a project (free tier)
3. Go to SQL Editor
4. Open `docs/CLERK_SUPABASE_SCHEMA.sql`
5. Copy & paste the SQL, then execute

### 3. Test Clerk
```bash
python run.py
```

Go to: http://localhost:4000/

You should see:
- Google Sign In button
- Click it to test authentication

---

## 📚 More Information

- **`ROUTING_FIX_GUIDE.md`** - Complete troubleshooting guide
- **`setup_env.py`** - Interactive .env setup
- **`test_routes.py`** - Simple test server
- **`docs/CLERK_SUPABASE_SCHEMA.sql`** - Database schema

---

## 🆘 Quick Troubleshooting

### Problem: "Clerk is not configured"
**Solution:** Run `python setup_env.py` and add your Clerk keys

### Problem: Routes still 404
**Solution:** Run `python test_routes.py` first to isolate the issue

### Problem: Google Sign In button not showing
**Solution:** 
1. Check `.env` has `CLERK_SECRET_KEY` and `CLERK_PUBLISHABLE_KEY`
2. Enable Google in Clerk Dashboard → Social Connections
3. Check browser console (F12) for errors

### Problem: Database errors
**Solution:** Run the SQL schema from `docs/CLERK_SUPABASE_SCHEMA.sql` in Supabase

---

## 🎉 You're Done When...

- ✅ `python test_routes.py` works
- ✅ http://localhost:5000/hello shows "Hello!"
- ✅ `python run.py` starts without errors
- ✅ http://localhost:4000/ shows landing page (not 404)
- ✅ Google Sign In button appears
- ✅ You can click it and sign in

---

**Need help? Check `ROUTING_FIX_GUIDE.md` for detailed troubleshooting!**

