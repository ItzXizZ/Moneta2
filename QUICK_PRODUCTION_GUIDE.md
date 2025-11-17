# 🚀 Quick Production Deployment Guide

## TL;DR - Is it Production Ready?

**Short Answer**: Almost! You need to fix **2 critical things**:

1. ❌ **Fix Clerk DNS** (10 minutes)
2. ⚠️ **Use production server** (use Gunicorn, not Flask dev server)

Then deploy to Render.com (free, HTTPS included) and you're live! ✅

---

## 🎯 Fastest Path to Production (30 minutes)

### Step 1: Fix Clerk DNS (10 min)

Your live Clerk key points to `clerk.moneta.lol` which doesn't exist.

**Easiest Fix**:
1. Go to https://dashboard.clerk.com
2. Select your Production app
3. Go to **Domains** section
4. **Remove** the custom domain `clerk.moneta.lol`
5. Clerk will use their default domain automatically
6. Done! ✅

**Test it works**:
```bash
python debug_clerk_key.py
# Should show: "Domain is accessible"
```

---

### Step 2: Secure Your Secrets (5 min)

Generate a strong JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to your `.env`:
```bash
JWT_SECRET=<paste_generated_secret>
FLASK_DEBUG=False
ENVIRONMENT=production
```

---

### Step 3: Deploy to Render (15 min)

**Why Render?**
- ✅ Free tier available
- ✅ Automatic HTTPS/SSL
- ✅ Already configured in your `render.yaml`
- ✅ Auto-deploys from GitHub
- ✅ No server management needed

**Steps**:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for production"
   git push origin main
   ```

2. **Go to [render.com](https://render.com)** and sign in

3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `moneta-demi`

4. **Render auto-detects settings** from `render.yaml`:
   - Name: `moneta`
   - Environment: `python`
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn --bind 0.0.0.0:$PORT run:app`

5. **Add Environment Variables**:
   Click "Environment" and add from your `.env`:
   ```
   CLERK_SECRET_KEY=sk_live_...
   CLERK_PUBLISHABLE_KEY=pk_live_...
   SUPABASE_URL=https://...
   SUPABASE_SERVICE_KEY=eyJ...
   OPENAI_API_KEY=sk-proj-...
   JWT_SECRET=<your_generated_secret>
   FLASK_DEBUG=False
   ENVIRONMENT=production
   ```

6. **Click "Create Web Service"**

7. **Wait 3-5 minutes** for deployment

8. **Done!** ✅ Your app is live at `https://moneta-xyz.onrender.com`

---

## 🧪 Testing Your Production Site

Once deployed, test:

1. ✅ Visit your Render URL
2. ✅ Click "Sign In" - Google sign-in modal appears
3. ✅ Sign in with Google
4. ✅ Dashboard loads with your info
5. ✅ Go to Chat - can send messages
6. ✅ Memories are created/retrieved
7. ✅ Sign out works

If all pass → **You're production ready!** 🎉

---

## 🔒 Security Checklist

Before going live, verify:

- [ ] `FLASK_DEBUG=False` in production
- [ ] Strong JWT secret (not default)
- [ ] Clerk DNS fixed (no `clerk.moneta.lol` errors)
- [ ] Using HTTPS (Render does this automatically)
- [ ] Using Gunicorn (not Flask dev server)
- [ ] `.env` not committed to Git (check `.gitignore`)

---

## 🆘 Common Issues

### "Clerk authentication failed"
- **Fix**: Remove custom domain from Clerk Dashboard → Domains
- **Test**: `python debug_clerk_key.py` should pass

### "Internal Server Error"
- **Check**: Render logs (Dashboard → Logs tab)
- **Common cause**: Missing environment variable

### "502 Bad Gateway"
- **Cause**: Server failed to start
- **Check**: Render logs for Python errors
- **Fix**: Verify all env vars are set

### "HTTPS required"
- **Fix**: Render provides HTTPS automatically
- **For VPS**: Use Nginx with Certbot SSL

---

## 💰 Cost Estimate

**Free Option** (Render):
- Free tier: 750 hours/month
- Perfect for MVP/testing
- Auto-sleeps after 15min inactivity
- Takes 30s to wake up

**Paid Option** (Render Pro):
- $7/month
- Always on (no sleep)
- Faster builds
- Custom domains included

**Other Costs**:
- Supabase: Free up to 500MB
- Clerk: Free up to 10,000 MAU
- OpenAI: Pay per use (~$0.002/1K tokens)

**Total**: Can run entirely **FREE** for small scale!

---

## 📈 Scaling Later

When you need to scale:

1. **Upgrade Render plan** ($7/mo → $25/mo)
2. **Add caching** (Redis)
3. **Add CDN** (Cloudflare - free)
4. **Database optimization** (Supabase indexes)
5. **Rate limiting** (already noted in checklist)

---

## 🎯 Your Action Items

**Right Now** (to be production ready):

1. [ ] Fix Clerk DNS (remove custom domain)
2. [ ] Generate strong JWT secret
3. [ ] Update `.env` with production settings
4. [ ] Test locally works: `python run.py`
5. [ ] Push to GitHub
6. [ ] Deploy on Render
7. [ ] Test production site
8. [ ] 🎉 **You're live!**

**Time**: 30-45 minutes

---

## 📚 Full Documentation

- **Detailed checklist**: See `PRODUCTION_CHECKLIST.md`
- **Deployment options**: VPS, Docker, AWS, etc.
- **Security hardening**: Rate limiting, monitoring, etc.

---

## ✅ Summary

**Current Status**:
- ✅ Code is solid
- ✅ Database configured
- ✅ Auth system working
- ❌ Need to fix Clerk DNS
- ⚠️ Need to use Gunicorn in production

**After fixes**: **100% production ready!** 🚀

**Recommended path**: Fix Clerk → Deploy to Render → Done in 30 min!

