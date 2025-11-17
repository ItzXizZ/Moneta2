# 🚀 Quick Setup Guide - Moneta AI

## ⚡ Fast Setup (20 minutes)

Your authentication system has been completely upgraded! Follow these steps:

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Your .env File

Copy `.env.example` to `.env` and fill in your API keys:

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Then edit `.env` with your keys from:
- **Clerk**: https://clerk.com (Google sign-in)
- **Supabase**: https://supabase.com (Database)
- **OpenAI**: https://platform.openai.com (AI Chat)

### 3. Set Up Supabase Database

1. Go to your Supabase project
2. Open SQL Editor
3. Copy and run the SQL from: `docs/CLERK_SUPABASE_SCHEMA.sql`

### 4. Run the App

```bash
python run.py
```

Visit: http://localhost:4000

---

## 📚 Detailed Documentation

All setup documentation is in `docs/setup/`:

- **START_HERE_NEW_AUTH.md** - Complete overview
- **CLERK_SETUP_COMPLETE_GUIDE.md** - Step-by-step guide with screenshots
- **AUTHENTICATION_UPGRADE_SUMMARY.md** - Technical details
- **WHATS_CHANGED.md** - List of all changes
- **ENV_VARIABLES.md** - Environment variable guide

---

## 🔑 What You Need

### API Keys Required:
1. ✅ **Clerk** (Free) - Google OAuth authentication
2. ✅ **Supabase** (Free) - PostgreSQL database
3. ✅ **OpenAI** (Paid) - AI chat (requires billing)

### Time to Setup:
- Get API keys: ~10 minutes
- Configure .env: ~2 minutes
- Install & run: ~5 minutes
- **Total: ~20 minutes**

---

## ⚠️ Common Issues

### Issue: "Clerk SDK not installed"
```bash
pip install --upgrade clerk-backend-sdk
```

### Issue: "OpenAI API not configured"
Add your OpenAI API key to `.env`:
```env
OPENAI_API_KEY=sk-your_key_here
```

### Issue: "Supabase connection failed"
1. Check your SUPABASE_URL and SUPABASE_SERVICE_KEY in `.env`
2. Make sure you ran the SQL schema

---

## 📞 Need Help?

1. Check `docs/setup/CLERK_SETUP_COMPLETE_GUIDE.md` for detailed instructions
2. Review the troubleshooting section in the guide
3. Check the error messages in the terminal

---

## ✨ Features

- ✅ One-click Google sign-in
- ✅ Secure database with Supabase
- ✅ AI chat with GPT-4
- ✅ Personal memory system
- ✅ Production-ready

**Start here:** Open `docs/setup/START_HERE_NEW_AUTH.md`

