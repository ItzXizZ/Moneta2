# 🚀 Complete Setup Guide: Clerk + Supabase + OpenAI Integration

This guide will walk you through setting up Moneta with Google sign-in via Clerk, Supabase database, and OpenAI API integration.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clerk Setup (Google Sign-In)](#1-clerk-setup)
3. [Supabase Setup (Database)](#2-supabase-setup)
4. [OpenAI Setup (AI Chat)](#3-openai-setup)
5. [Environment Configuration](#4-environment-configuration)
6. [Installation & Running](#5-installation--running)
7. [Testing the Integration](#6-testing)
8. [Troubleshooting](#7-troubleshooting)

---

## Prerequisites

- Python 3.8 or higher
- A Google account (for Clerk OAuth)
- Internet connection
- Basic command line knowledge

---

## 1. Clerk Setup (Google Sign-In)

Clerk provides enterprise-grade authentication with Google OAuth.

### Step 1.1: Create a Clerk Account

1. Go to [https://clerk.com](https://clerk.com)
2. Click "Get Started" or "Sign Up"
3. Create your account (you can sign up with Google)

### Step 1.2: Create a New Application

1. After logging in, click "**+ Create Application**"
2. Give your application a name (e.g., "Moneta AI")
3. Choose your authentication methods:
   - ✅ Enable **Google** (this is important!)
   - You can also enable Email/Password if you want
4. Click "**Create Application**"

### Step 1.3: Configure Google OAuth

1. In your Clerk dashboard, go to "**User & Authentication**" → "**Social Connections**"
2. Click on **Google**
3. Clerk will show you:
   - **Google Client ID** (already configured)
   - **Google Client Secret** (already configured)
4. Clerk handles all the Google OAuth configuration automatically!
5. Make sure the toggle is **ON** for Google

### Step 1.4: Get Your API Keys

1. Go to "**API Keys**" in the left sidebar
2. You'll see two keys:
   - **Publishable Key** (starts with `pk_test_...` or `pk_live_...`)
   - **Secret Key** (starts with `sk_test_...` or `sk_live_...`)
3. **Copy both keys** - you'll need them in a moment

**Important Notes:**
- Use `pk_test_...` and `sk_test_...` for development
- Use `pk_live_...` and `sk_live_...` for production
- **Never share your Secret Key publicly!**

---

## 2. Supabase Setup (Database)

Supabase is an open-source Firebase alternative with PostgreSQL.

### Step 2.1: Create a Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click "**Start your project**"
3. Sign in with GitHub or create an account

### Step 2.2: Create a New Project

1. Click "**New Project**"
2. Choose your organization (or create one)
3. Fill in the details:
   - **Name**: `moneta-database` (or any name you like)
   - **Database Password**: Create a strong password (save it!)
   - **Region**: Choose closest to your users
4. Click "**Create new project**"
5. Wait 2-3 minutes for the database to be provisioned

### Step 2.3: Get Your Connection Details

1. Once your project is ready, go to "**Settings**" (gear icon)
2. Click on "**API**" in the settings menu
3. You'll need three things:

   **Project URL:**
   ```
   https://xxxxx.supabase.co
   ```

   **Anon/Public Key** (under "Project API keys"):
   ```
   eyJhbGc...  (very long key)
   ```

   **Service Role Key** (under "Project API keys"):
   ```
   eyJhbGc...  (very long key)
   ```

4. **Copy all three** - keep them safe!

**⚠️ Security Warning:**
- The `anon` key is safe to use in client-side code
- The `service_role` key has full database access - **never expose it publicly!**

### Step 2.4: Set Up Database Tables

1. In your Supabase dashboard, click on "**SQL Editor**" (left sidebar)
2. Click "**New Query**"
3. Copy the entire contents of `docs/CLERK_SUPABASE_SCHEMA.sql`
4. Paste it into the SQL editor
5. Click "**Run**" (or press Ctrl/Cmd + Enter)
6. You should see "Success. No rows returned"

This creates all the necessary tables:
- `users` - User accounts linked to Clerk
- `user_memories` - Personal memories for each user
- `user_memory_databases` - Memory statistics
- Plus helper functions and security policies

### Step 2.5: Verify the Setup

1. Go to "**Table Editor**" in the left sidebar
2. You should see these tables:
   - users
   - user_memories
   - user_memory_databases
   - (possibly others from previous setup)

If you see these tables, you're good to go! ✅

---

## 3. OpenAI Setup (AI Chat)

OpenAI powers the conversational AI in Moneta.

### Step 3.1: Create an OpenAI Account

1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Click "**Sign up**"
3. Create your account (you can use Google sign-in)
4. Verify your email address

### Step 3.2: Add Billing Information

⚠️ **Important:** OpenAI requires billing information even for the API.

1. Go to "**Settings**" → "**Billing**"
2. Click "**Add payment method**"
3. Add your credit card
4. Set a usage limit (recommended: $10-20/month for testing)

**Pricing (as of 2024):**
- GPT-4o-mini: ~$0.15 per 1M tokens (very affordable)
- GPT-4: ~$30 per 1M tokens (more expensive)

### Step 3.3: Create an API Key

1. Go to "**API keys**" in the left sidebar
2. Click "**+ Create new secret key**"
3. Give it a name (e.g., "Moneta Development")
4. **Copy the API key immediately!**
   - It starts with `sk-...`
   - You won't be able to see it again!
5. Click "**Done**"

**Security Best Practices:**
- Never commit API keys to Git
- Use environment variables (we'll set this up next)
- Set usage limits to prevent surprise bills
- Rotate keys regularly

---

## 4. Environment Configuration

Now we'll put all your keys together in a `.env` file.

### Step 4.1: Create the .env File

1. In your terminal, navigate to the `Moneta2` directory:
   ```bash
   cd Moneta2
   ```

2. Create a new `.env` file:
   ```bash
   # On Windows:
   type nul > .env
   
   # On Mac/Linux:
   touch .env
   ```

3. Open the `.env` file in your favorite text editor

### Step 4.2: Add Your Configuration

Copy and paste this template, then replace the placeholder values with your actual keys:

```env
# ============================================
# CLERK AUTHENTICATION
# ============================================
# Get these from: https://dashboard.clerk.com → API Keys
CLERK_SECRET_KEY=sk_test_xxxxx_YOUR_SECRET_KEY_HERE
CLERK_PUBLISHABLE_KEY=pk_test_xxxxx_YOUR_PUBLISHABLE_KEY_HERE

# ============================================
# SUPABASE DATABASE
# ============================================
# Get these from: https://supabase.com → Project Settings → API
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc_YOUR_ANON_KEY_HERE
SUPABASE_SERVICE_KEY=eyJhbGc_YOUR_SERVICE_ROLE_KEY_HERE

# ============================================
# OPENAI API
# ============================================
# Get this from: https://platform.openai.com → API Keys
OPENAI_API_KEY=sk-proj-xxxxx_YOUR_OPENAI_KEY_HERE

# ============================================
# FLASK CONFIGURATION
# ============================================
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=4000

# JWT Secret (for legacy auth support)
JWT_SECRET=your_random_secret_key_here_generate_a_long_random_string
```

### Step 4.3: Generate a JWT Secret

For the `JWT_SECRET`, generate a random string:

**Python method:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Or use any random string generator online** (search "random string generator")

### Step 4.4: Save and Verify

1. Save the `.env` file
2. **Double-check all keys are correct:**
   - No extra spaces
   - No quotes around values
   - All keys are complete (not cut off)

---

## 5. Installation & Running

### Step 5.1: Install Dependencies

1. Open a terminal in the `Moneta2` directory

2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - Flask (web framework)
   - Clerk SDK (authentication)
   - Supabase client (database)
   - OpenAI SDK (AI chat)
   - And all other dependencies

   **Note:** Installation may take 5-10 minutes due to ML libraries.

### Step 5.2: Verify Installation

Check that everything installed correctly:

```bash
python -c "import flask, openai, supabase; print('✅ All packages installed successfully!')"
```

If you see the success message, you're good! If you get errors, make sure you're in the right directory and try installing again.

### Step 5.3: Run the Application

Start the server:

```bash
python run.py
```

You should see output like:

```
[OK] OpenAI client initialized successfully
[INFO] Full ML-powered memory system initialized successfully!
[INFO] Clerk Authentication System initialized
[OK] Clerk authentication system ready
[INFO] Starting Moneta - AI Memory Management System...
[INFO] Open your browser and go to: http://localhost:4000
 * Running on http://0.0.0.0:4000
```

---

## 6. Testing the Integration

### Test 1: Access the Landing Page

1. Open your browser
2. Go to: `http://localhost:4000`
3. You should see:
   - The Moneta landing page
   - A "Sign in with Google" button
   - Beautiful UI with features

### Test 2: Sign In with Google

1. Click "**Sign in with Google**"
2. Clerk's sign-in modal will appear
3. Choose your Google account
4. Authorize the app
5. You should be redirected back

### Test 3: Verify Database Sync

1. After signing in, check your Supabase dashboard
2. Go to "**Table Editor**" → "**users**"
3. You should see a new row with your account:
   - `clerk_id`: Your Clerk user ID
   - `email`: Your Google email
   - `name`: Your Google name
   - `profile_image`: Your Google avatar

### Test 4: Test the Chat

1. Click "**Go to Dashboard**" after signing in
2. Try sending a message to the AI
3. You should get a response from OpenAI

**Example test messages:**
- "Hello! What can you help me with?"
- "Remember that I love pizza"
- "What's my favorite food?" (should reference pizza)

### Test 5: Check API Endpoints

Test the API directly:

1. Get your session token from Clerk (check browser developer console)
2. Test the verify endpoint:

```bash
curl -X GET http://localhost:4000/api/clerk/verify \
  -H "Authorization: Bearer YOUR_SESSION_TOKEN"
```

You should get your user info back.

---

## 7. Troubleshooting

### Issue: "Clerk authentication not configured"

**Solution:**
- Check that `CLERK_SECRET_KEY` is in your `.env` file
- Make sure the key starts with `sk_test_` or `sk_live_`
- Restart the server after adding the key

### Issue: "OpenAI API authentication failed"

**Solution:**
- Verify your `OPENAI_API_KEY` in `.env`
- Check that billing is set up on OpenAI
- Make sure the key starts with `sk-`
- Test the key on OpenAI's playground

### Issue: "Supabase connection failed"

**Solution:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Check that your Supabase project is running
- Ensure the SQL schema was executed successfully
- Check for typos in the keys

### Issue: "Module not found" errors

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Issue: Google Sign-In doesn't work

**Solution:**
- Check that Google is enabled in Clerk dashboard
- Verify your domain is allowed in Clerk settings
- Clear browser cookies and try again
- Check browser console for errors

### Issue: User not syncing to Supabase

**Solution:**
- Check that you're using `SUPABASE_SERVICE_KEY` (not anon key)
- Verify the SQL schema was run
- Check Python console for error messages
- Ensure RLS policies are set correctly

### Getting Help

If you're still stuck:

1. **Check the logs:** Look at terminal output for error messages
2. **Check browser console:** Press F12 and look for errors
3. **Verify all keys:** Double-check every environment variable
4. **Start fresh:** Delete `.env`, recreate it carefully
5. **Check service status:** Make sure Clerk, Supabase, and OpenAI are online

---

## 🎉 Success!

If you've made it this far and everything is working, congratulations! You now have:

- ✅ Google sign-in with Clerk OAuth
- ✅ User data synced to Supabase
- ✅ AI chat powered by OpenAI
- ✅ Personal memory system per user
- ✅ Secure, scalable architecture

### Next Steps

- **Explore the memory system:** Try having conversations and see how memories are extracted
- **Check the database:** Watch as memories are saved in Supabase
- **Customize:** Modify the UI, adjust AI prompts, add features
- **Deploy:** When ready, deploy to Render, Railway, or Vercel

---

## 📚 Additional Resources

### Documentation
- [Clerk Documentation](https://clerk.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)

### Architecture Files
- `app/core/clerk_auth_system.py` - Clerk authentication logic
- `app/blueprints/clerk_auth.py` - API endpoints
- `docs/CLERK_SUPABASE_SCHEMA.sql` - Database schema
- `app/services/openai_service.py` - OpenAI integration

### Support
- Clerk Support: https://clerk.com/support
- Supabase Discord: https://discord.supabase.com
- OpenAI Community: https://community.openai.com

---

**Made with ❤️ by the Moneta team**

*Last updated: 2024*


