# 🚀 Production Deployment Checklist

This checklist ensures your Moneta app is production-ready.

## ❌ **CRITICAL - Must Fix Before Production**

### 1. Fix Clerk DNS Configuration
**Status**: ❌ BLOCKING

Your live Clerk key is configured for `clerk.moneta.lol` which doesn't exist.

**Fix Option A - Remove Custom Domain (Recommended)**:
1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Select your **Production** application
3. Navigate to **Domains** section
4. Remove the custom domain `clerk.moneta.lol`
5. Clerk will use default domain (e.g., `your-app.clerk.accounts.dev`)
6. Generate new live keys if needed

**Fix Option B - Set Up Custom Domain**:
1. Own the domain `moneta.lol`
2. Add DNS CNAME record:
   ```
   clerk.moneta.lol → your-clerk-instance.clerk.accounts.dev
   ```
3. Verify in Clerk Dashboard
4. Wait for DNS propagation (5-30 minutes)

**Test**: Run `python debug_clerk_key.py` - should show "Domain is accessible"

---

### 2. Secure JWT Secret
**Status**: ⚠️ NEEDS ATTENTION

**Current**: May be using default `'your-secret-key-here'`

**Fix**:
```bash
# Generate a secure random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
JWT_SECRET=<generated_secret_here>
```

---

### 3. Disable Debug Mode
**Status**: ✅ FIXED

Debug mode now reads from environment variable.

**Ensure in .env**:
```bash
FLASK_DEBUG=False
ENVIRONMENT=production
```

---

### 4. Use Production Server (Not Flask Dev Server)
**Status**: ⚠️ REQUIRED

Flask's built-in server (`app.run()`) is NOT production-ready.

**Development**:
```bash
python run.py
```

**Production** (use Gunicorn):
```bash
gunicorn --workers 4 --bind 0.0.0.0:4000 run:app
```

Or with more options:
```bash
gunicorn \
  --workers 4 \
  --threads 2 \
  --bind 0.0.0.0:4000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  run:app
```

---

### 5. HTTPS/SSL Required
**Status**: ❌ REQUIRED

Clerk **requires HTTPS** in production. You need:

**Option A - Use a Platform** (Easiest):
- Render.com (free SSL, already configured in `render.yaml`)
- Heroku
- Railway
- Fly.io

**Option B - Self-Hosted with Nginx**:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ⚠️ **IMPORTANT - Should Fix**

### 6. Environment Variables Security
**Checklist**:
- [ ] Never commit `.env` file to Git (already in `.gitignore`)
- [ ] Use platform-specific secret management in production
- [ ] Rotate secrets regularly
- [ ] Use different keys for dev/staging/production

---

### 7. Database Security
**Supabase Checklist**:
- [ ] Use SERVICE_KEY (not anon key) in backend
- [ ] Enable Row Level Security (RLS) policies
- [ ] Restrict database access by IP if possible
- [ ] Regular backups enabled

---

### 8. Rate Limiting
**Status**: ❌ NOT IMPLEMENTED

Add rate limiting to prevent abuse:

```python
# Install: pip install flask-limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/chat/send")
@limiter.limit("10 per minute")
def send_message():
    # ...
```

---

### 9. Error Handling
**Status**: ⚠️ NEEDS REVIEW

Ensure errors don't expose sensitive info:

```python
@app.errorhandler(500)
def handle_500(e):
    # Log the actual error
    app.logger.error(f"Server error: {e}")
    # Return generic message to user
    return jsonify({'error': 'Internal server error'}), 500
```

---

### 10. Monitoring & Logging
**Status**: ❌ NOT IMPLEMENTED

**Recommendations**:
- Use Sentry for error tracking
- Set up application monitoring (New Relic, DataDog)
- Configure structured logging
- Set up uptime monitoring (UptimeRobot, Pingdom)

---

## ✅ **Already Configured**

- ✅ Clerk authentication system
- ✅ Supabase database
- ✅ Environment variable management
- ✅ Gunicorn in requirements.txt
- ✅ Render deployment config
- ✅ CORS configuration
- ✅ Blueprint architecture

---

## 🚀 **Deployment Options**

### Option 1: Render.com (Recommended - Easiest)

1. **Fix Clerk DNS** (see above)
2. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Production ready"
   git push origin main
   ```

3. **Deploy to Render**:
   - Go to [render.com](https://render.com)
   - New → Web Service
   - Connect your GitHub repo
   - Render will auto-detect `render.yaml`
   - Add environment variables from `.env`
   - Deploy!

4. **Configure domain** (optional):
   - Add custom domain in Render dashboard
   - Update DNS records

### Option 2: VPS (DigitalOcean, Linode, AWS)

1. Set up server with Ubuntu 22.04
2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-pip nginx certbot python3-certbot-nginx
   ```

3. Clone repository:
   ```bash
   git clone <your-repo>
   cd moneta-demi
   pip install -r requirements.txt
   ```

4. Create `.env` file with production values

5. Set up systemd service:
   ```bash
   sudo nano /etc/systemd/system/moneta.service
   ```
   ```ini
   [Unit]
   Description=Moneta AI Memory System
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/moneta-demi
   Environment="PATH=/usr/bin"
   ExecStart=/usr/local/bin/gunicorn --workers 4 --bind 0.0.0.0:4000 run:app

   [Install]
   WantedBy=multi-user.target
   ```

6. Start service:
   ```bash
   sudo systemctl start moneta
   sudo systemctl enable moneta
   ```

7. Configure Nginx (see above)

8. Get SSL certificate:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

---

## 🧪 **Pre-Launch Testing**

Before going live, test:

- [ ] Sign up new user works
- [ ] Sign in works
- [ ] Sign out works
- [ ] Chat functionality works
- [ ] Memory creation/retrieval works
- [ ] All pages load correctly
- [ ] Mobile responsiveness
- [ ] SSL certificate valid
- [ ] No console errors in browser
- [ ] Backend logs show no errors

---

## 📊 **Post-Launch Monitoring**

First week after launch:

1. Monitor error rates
2. Check database performance
3. Review authentication success/failure rates
4. Monitor memory usage and server resources
5. Gather user feedback

---

## ⏱️ **Time Estimate**

- Fix Clerk DNS: **5-10 minutes** (or 30 min for custom domain)
- Security fixes: **15 minutes**
- Deploy to Render: **10 minutes**
- Testing: **30 minutes**

**Total: ~1-2 hours to production**

---

## 🆘 **Quick Production Deploy (Render)**

If you just want it live fast:

1. **Fix Clerk**: Remove custom domain from Clerk dashboard
2. **Update .env**:
   ```bash
   FLASK_DEBUG=False
   ENVIRONMENT=production
   JWT_SECRET=<run: python -c "import secrets; print(secrets.token_urlsafe(32))">
   ```
3. **Push to GitHub**
4. **Deploy on Render** (connects to GitHub, auto-deploys)
5. **Done!** ✅

Render provides HTTPS automatically and manages the Gunicorn server for you.

