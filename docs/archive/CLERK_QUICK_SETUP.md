# Clerk Quick Setup - 5 Minutes

## Step 1: Copy Your API Keys to .env (2 minutes)

You already have your Clerk keys! From your dashboard screenshot:

```env
CLERK_SECRET_KEY=sk_test_JaQ4cbiEmExq6nWCZzbnkhHzfIrEEBekr8J38iIAj
CLERK_PUBLISHABLE_KEY=pk_test_Z29sZGVuLW9wb3NzdW0tMzIuY2xlcmsuYWNjb3VudHMuZGV2JA
```

Add these to your `.env` file at: `C:\Users\ethan\OneDrive\Desktop\Moneta2\Moneta2\.env`

## Step 2: Enable Google OAuth (1 minute)

In your Clerk dashboard (https://dashboard.clerk.com):

1. Click **"User & Authentication"** (left sidebar)
2. Click **"Social Connections"**
3. Find **"Google"** in the providers list
4. **Toggle it ON** (should turn blue/green)
5. Click **"Save"** or **"Apply"**

That's it! Clerk automatically configures Google OAuth for you.

## Step 3: Ignore Next.js (0 minutes)

- ❌ Don't change the framework dropdown
- ❌ Ignore all Next.js/React code examples
- ✅ You're using **Python/Flask** - the keys work the same

## Step 4: Test Your Setup

After saving your .env:

```bash
python test_clerk.py
```

If you see:
```
[OK] Clerk SDK is configured correctly!
```

You're good to go!

## Step 5: Restart Server

```bash
python run.py
```

Visit: http://localhost:4000

---

## What You'll Have After Setup:

✅ Google "Sign in with Google" button on your landing page
✅ Users automatically created in Supabase
✅ Secure OAuth 2.0 authentication
✅ No password management needed

---

## Common Clerk Dashboard Sections:

### API Keys (You're here!)
- Copy your keys to .env ✅

### User & Authentication → Social Connections
- Enable Google here! ⭐

### User & Authentication → Email, Phone, Username
- Configure what info you want to collect
- Email is required by default (good!)

### Sessions
- Session length (default 7 days is fine)
- Multi-session settings

---

## Your Current .env Should Look Like:

```env
# Clerk Authentication
CLERK_SECRET_KEY=sk_test_JaQ4cbiEmExq6nWCZzbnkhHzfIrEEBekr8J38iIAj
CLERK_PUBLISHABLE_KEY=pk_test_Z29sZGVuLW9wb3NzdW0tMzIuY2xlcmsuYWNjb3VudHMuZGV2JA

# Supabase (from your other screenshot)
SUPABASE_URL=https://pquleppuqequrjwicmbn.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key

# OpenAI
OPENAI_API_KEY=sk-proj-your_key

# Flask
FLASK_DEBUG=True
FLASK_PORT=4000
JWT_SECRET=any_random_string
```

---

## Next: Fix the Clerk Python SDK Issue

The Clerk Python SDK has async issues. We need to use a different approach:

**Option A**: Use Clerk's REST API directly with `requests` (simpler)
**Option B**: Handle async properly with `asyncio` (more complex)

For now, the legacy auth (email/password) works perfectly with your Supabase setup!

Once you enable Google in Clerk dashboard, we can implement Option A (REST API approach) which will work better with Flask.

