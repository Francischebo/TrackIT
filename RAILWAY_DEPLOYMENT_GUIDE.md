# Railway Deployment Guide for TrackIT Backend

Complete step-by-step guide to deploy TrackIT on Railway with Supabase PostgreSQL.

---

## 📋 Prerequisites

Before starting, you'll need:

- ✅ TrackIT code pushed to GitHub (with all configurations)
- ✅ GitHub account with repository: `https://github.com/Francischebo/TrackIT`
- ✅ Supabase account with database configured
- ✅ Railway account (free tier available)
- ✅ Your Supabase credentials ready

---

## 🚀 Step 1: Create Railway Account

### 1.1 Sign Up

1. Visit: https://railway.app
2. Click **"Start Free"**
3. Sign up with GitHub (recommended - easier integration)
4. Authorize Railway to access your GitHub account

### 1.2 Create New Project

1. After login, click **"New Project"**
2. Select **"Deploy from GitHub"**
3. Connect your GitHub account (if not already connected)

---

## 🔗 Step 2: Connect GitHub Repository

### 2.1 Select Repository

1. Click **"Deploy from GitHub"**
2. Search for: `TrackIT` or `Francischebo/TrackIT`
3. Click the repository to select it
4. Click **"Deploy"**

### 2.2 Configure Build Settings

Railway should auto-detect:
- **Root Directory**: `./backend` (if needed, set this)
- **Start Command**: `python run.py`
- **Build Command**: `pip install -r requirements.txt`

If not auto-detected, you can configure manually.

---

## 🔧 Step 3: Add Environment Variables

### 3.1 Access Environment Variables

In Railway dashboard:
1. Click your project
2. Go to **"Variables"** tab
3. Add the following variables

### 3.2 Add Required Variables

```env
FLASK_ENV=production
FLASK_APP=run.py

# Supabase Database Connection
DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require

# Security Keys (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=<your-generated-key-here>
JWT_SECRET_KEY=<your-generated-jwt-secret-key-here>

# CORS Origins (update with your frontend domain)
CORS_ORIGINS=https://localhost:3000,https://yourdomain.com

# Other Settings
BCRYPT_LOG_ROUNDS=12
FORCE_HTTPS=False
DEBUG=False
```

**⚠️ IMPORTANT**: 
- Generate new keys with: `python -c "import secrets; print(secrets.token_hex(32))"`
- Never commit these to GitHub
- Keep them private

### 3.3 Save Variables

Click **"Save"** after adding all variables.

---

## 🐘 Step 4: Add PostgreSQL Plugin (Optional)

Railway has a built-in PostgreSQL addon, but you're using Supabase. **Skip this step** - your database connection is in the environment variables.

---

## 📦 Step 5: Configure Procfile (Optional)

Create `backend/Procfile` in your repository:

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT run:app
```

This tells Railway how to start your app. If not present, Railway will use the default start command.

### Alternative: Create Dockerfile

If you want more control, create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "run:app"]
```

---

## 🚀 Step 6: Deploy

### 6.1 Start Deployment

1. After adding all environment variables
2. Click **"Deploy"** button
3. Railway will start building and deploying

### 6.2 Monitor Deployment

Watch the logs in real-time:
- Build logs show: `pip install`, dependencies
- Deployment logs show: Flask starting, port assignment
- Green checkmark = Successful deployment

Expected final log:
```
 * Running on http://0.0.0.0:8000
```

---

## ✅ Step 7: Verify Deployment

### 7.1 Get Your Railway URL

In Railway dashboard:
1. Click your project
2. Look for **"Domains"** or **"URL"** section
3. Your public URL will be something like: `https://trackit-production.up.railway.app`

### 7.2 Test Health Endpoint

```bash
curl https://trackit-production.up.railway.app/health
```

Expected response:
```json
{"success":true,"status_code":200,"message":"OK"}
```

### 7.3 Test With Postman

1. Open Postman
2. Create new request: **GET**
3. URL: `https://trackit-production.up.railway.app/health`
4. Send
5. Should see 200 OK response

---

## 👥 Step 8: Test Organization Registration

Test multi-tenant functionality:

```bash
curl -X POST https://trackit-production.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "organisation_name": "Acme Corporation",
    "organisation_code": "ACME",
    "username": "admin",
    "email": "admin@acme.com",
    "password": "SecurePassword123!"
  }'
```

Expected response:
```json
{
  "success": true,
  "status_code": 201,
  "message": "Organization and admin user created successfully",
  "data": {
    "organisation_id": 1,
    "username": "admin",
    "email": "admin@acme.com"
  }
}
```

---

## 📊 Step 9: Monitor Application

### 9.1 View Logs

In Railway:
1. Click project
2. Go to **"Logs"** tab
3. See real-time application logs

### 9.2 View Metrics

1. Click **"Metrics"** tab
2. See CPU, memory, and request statistics

### 9.3 View Network

1. Click **"Network"** tab
2. See incoming and outgoing traffic

---

## 🔄 Step 10: Auto-Deploy Updates

Railway auto-deploys when you push to GitHub:

1. Make code changes locally
2. Push to GitHub: `git push origin main`
3. Railway automatically:
   - Detects the push
   - Rebuilds the app
   - Deploys the new version
4. Check Railway dashboard to see build progress

---

## 🔐 Security Configuration

### 10.1 Custom Domain

To use your own domain instead of `*.railway.app`:

1. In Railway: **"Domains"** tab
2. Click **"Add Domain"**
3. Enter your domain: `api.yourdomain.com`
4. Follow DNS configuration steps (update your DNS provider)
5. Update `CORS_ORIGINS` in environment variables

### 10.2 Enable HTTPS

Railway automatically provides HTTPS with SSL certificates. ✅ Already enabled.

### 10.3 Restrict CORS

Update `CORS_ORIGINS` environment variable:

```env
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

Don't allow localhost in production:
```env
CORS_ORIGINS=https://yourdomain.com
```

---

## 📈 Step 11: Scaling (When You Grow)

### 11.1 Increase Resources

As traffic grows, scale up:

1. In Railway: **"Settings"**
2. Adjust resources:
   - **Memory**: Increase if app crashes with "out of memory"
   - **CPU**: Increase if requests are slow
3. For production: Start with 2x memory, 2x CPU

### 11.2 Multiple Instances

Run multiple backend instances:

1. In Railway: **"Deployments"**
2. Set **"Replicas"** to 2 or more
3. Railway auto-load balances requests

---

## 🚨 Step 12: Troubleshooting

### Issue: Build Fails

```
Error: Failed to install dependencies
```

**Solution:**
1. Check `requirements.txt` is in root or `backend/` directory
2. Verify all package versions are compatible
3. Check Python version matches `requirements.txt`

### Issue: App Crashes After Deploy

```
Error: ModuleNotFoundError
```

**Solution:**
1. Check environment variables are set
2. Verify `DATABASE_URL_PROD` is correct
3. Check logs for full error
4. Verify `run.py` exists in backend directory

### Issue: Database Connection Fails

```
Error: FATAL: password authentication failed
```

**Solution:**
1. Verify Supabase credentials are correct
2. Confirm `sslmode=require` in connection string
3. Check Supabase project is active (not paused)
4. Test connection locally first

### Issue: Requests Timeout

```
504 Gateway Timeout
```

**Solution:**
1. Increase Railway memory allocation
2. Optimize slow database queries
3. Add caching layer (Redis)
4. Increase request timeout

### Issue: High Memory Usage

```
Memory: 1.2GB / 1GB limit
```

**Solution:**
1. Increase memory in Railway settings
2. Check for memory leaks in code
3. Profile application with tools like `memory_profiler`
4. Add pagination to large queries

---

## 📝 Environment Variables Reference

| Variable | Example | Required |
|----------|---------|----------|
| `FLASK_ENV` | `production` | ✅ Yes |
| `DATABASE_URL_PROD` | `postgresql://...` | ✅ Yes |
| `SECRET_KEY` | `<64-char hex>` | ✅ Yes |
| `JWT_SECRET_KEY` | `<64-char hex>` | ✅ Yes |
| `CORS_ORIGINS` | `https://domain.com` | ✅ Yes |
| `BCRYPT_LOG_ROUNDS` | `12` | ❌ No (default: 12) |
| `FORCE_HTTPS` | `True` | ❌ No (default: False) |
| `DEBUG` | `False` | ❌ No (default: False) |

---

## 🎯 Your Railway Deployment Checklist

- [ ] Railway account created
- [ ] GitHub repository connected
- [ ] `backend/Procfile` created (or Dockerfile)
- [ ] Environment variables added (all 8+ variables)
- [ ] Deployment successful (green checkmark)
- [ ] Health endpoint tested (`/health` returns 200)
- [ ] Organization registration tested (`/api/auth/register`)
- [ ] Custom domain configured (optional)
- [ ] CORS origins updated
- [ ] Monitoring set up (logs, metrics)
- [ ] Auto-deploy working (GitHub push triggers build)

---

## 🚀 Final URLs

After deployment:

| Service | URL |
|---------|-----|
| **Backend API** | `https://trackit-production.up.railway.app` |
| **Health Check** | `https://trackit-production.up.railway.app/health` |
| **Your Domain** | `https://api.yourdomain.com` (after DNS setup) |
| **Railway Dashboard** | `https://railway.app/dashboard` |

---

## 💾 Backup & Recovery

### 11.1 Database Backups

Supabase handles backups automatically:
1. Daily automated backups
2. Point-in-time recovery available
3. Manual backups via Supabase dashboard

### 11.2 Code Rollback

If deployment goes wrong:

1. In Railway: **"Deployments"**
2. Find previous successful deployment
3. Click **"Redeploy"**
4. Railway deploys previous version

---

## 📞 Support Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Status**: https://status.railway.app
- **Supabase Docs**: https://supabase.com/docs
- **Flask Docs**: https://flask.palletsprojects.com
- **Your Repo**: https://github.com/Francischebo/TrackIT

---

## 🎓 Next Steps

1. ✅ Follow steps 1-10 above
2. ✅ Test deployment is working
3. ✅ Update frontend to point to Railway URL
4. ✅ Configure custom domain (optional)
5. ✅ Set up monitoring and alerting
6. ✅ Plan scaling strategy as you grow

---

**Status**: ✅ Ready for Railway deployment  
**Estimated Time**: 15-30 minutes  
**Complexity**: Easy (Railway handles most configuration)  
**Cost**: Free tier included ($5/month for hobby tier)

Next: Deploy your backend to Railway now! 🚀
