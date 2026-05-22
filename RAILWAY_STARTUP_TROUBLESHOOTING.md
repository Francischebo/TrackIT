# 🚀 Railway Startup & Troubleshooting Guide

Complete guide to troubleshoot any startup issues with Railway deployment.

---

## ✅ What Should Happen on Startup

When your app starts successfully on Railway, you should see logs like:

```
[2026-05-22 14:41:31,014] INFO in logging_utils: TrackIT Management System startup
[2026-05-22 14:41:31,200] INFO in app: Creating Flask application
[2026-05-22 14:41:31,250] INFO in database: Initializing database connection
[2026-05-22 14:41:31,400] INFO in app: Application startup complete
 * Running on http://0.0.0.0:8000
```

✅ **Expected**: App should be ready to accept requests

---

## 🔍 Common Startup Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'X'"

**What This Means:**
A Python package is missing from `requirements.txt`

**Example Error:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solution:**

1. **Check requirements.txt includes the package:**
   ```bash
   grep -i psycopg2 backend/requirements.txt
   ```

2. **If missing, add it:**
   ```
   psycopg2-binary==2.9.9
   ```

3. **Push to GitHub:**
   ```bash
   git add backend/requirements.txt
   git commit -m "Add missing psycopg2 dependency"
   git push origin main
   ```

4. **Railway will auto-rebuild** (5-10 seconds)

**Prevention:**
- Always test locally first: `pip install -r requirements.txt`
- When adding new packages: `pip install package-name && pip freeze > requirements.txt`

---

### Issue 2: "Error: DATABASE_URL_PROD not set"

**What This Means:**
Environment variable is missing in Railway

**Example Error:**
```
KeyError: 'DATABASE_URL_PROD'
```

**Solution:**

1. **Go to Railway Dashboard**
2. **Click your project**
3. **Click "Variables" tab**
4. **Verify these are set:**
   ```env
   FLASK_ENV=production
   DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require
   SECRET_KEY=<your-generated-key>
   JWT_SECRET_KEY=<your-generated-jwt-key>
   ```

5. **Click "Save"**
6. **Railway will auto-restart** (30 seconds)

**Verify in Railway logs:**
```
✅ Database connection successful
```

---

### Issue 3: "FATAL: password authentication failed"

**What This Means:**
Supabase credentials are wrong OR database is paused

**Solution:**

1. **Verify Supabase project is active:**
   - Go to: https://supabase.com/dashboard
   - Click your project
   - If it says "Paused", click **"Resume"**

2. **Verify credentials are correct:**
   ```env
   # Should match exactly from Supabase Dashboard
   DATABASE_URL_PROD=postgresql://postgres:PASSWORD@db.PROJECTID.supabase.co:5432/postgres?sslmode=require
   ```

3. **Test connection locally first:**
   ```bash
   python scripts/test_supabase_connection.py
   ```

4. **If local test passes**, update Railway and push code to trigger rebuild

---

### Issue 4: "OperationalError: could not connect to server"

**What This Means:**
Cannot reach the database server (network/DNS issue)

**Solution:**

1. **Check Supabase is running:**
   - Supabase Dashboard → Your project → Verify "Status: Healthy"

2. **Verify SSL requirement:**
   ```env
   # MUST include this
   DATABASE_URL_PROD=postgresql://...?sslmode=require
   ```

3. **Check firewall/network:**
   - Supabase allows all IPs by default
   - Railway can reach any external database
   - If still failing, test from local terminal:
     ```bash
     psql postgresql://postgres:PASSWORD@db.PROJECTID.supabase.co:5432/postgres
     ```

---

### Issue 5: "Port Already in Use"

**What This Means:**
Railway port assignment conflict (rare)

**Solution:**

1. **Don't specify port in code** - Railway sets `PORT` environment variable
2. **Use in Procfile/Dockerfile:**
   ```
   gunicorn -w 4 -b 0.0.0.0:$PORT run:app
   ```

3. **Or in Python code:**
   ```python
   port = int(os.environ.get('PORT', 8000))
   app.run(host='0.0.0.0', port=port)
   ```

4. **Check Procfile exists:**
   ```bash
   cat backend/Procfile
   # Should output: web: gunicorn -w 4 -b 0.0.0.0:$PORT run:app
   ```

---

### Issue 6: "Out of Memory" or Sudden Crash

**What This Means:**
App using more memory than Railway allocated

**Solution:**

1. **Check memory usage in Railway:**
   - Railway Dashboard → Metrics tab → Memory graph
   - If constantly climbing → memory leak

2. **Quick fix: Increase memory in Railway:**
   - Railway Dashboard → Settings → Memory
   - Increase from 512MB to 1GB

3. **Better fix: Find memory leak:**
   ```bash
   # Test locally with memory profiling
   pip install memory-profiler
   python -m memory_profiler run.py
   ```

4. **Check for:**
   - Large objects not being garbage collected
   - Infinite loops
   - Unbounded caches

---

### Issue 7: "TimeoutError" or "504 Gateway Timeout"

**What This Means:**
Request taking too long to complete

**Solution:**

1. **Check database performance:**
   ```bash
   # Add timing to slow queries
   # Supabase Dashboard → Analytics → Slow queries
   ```

2. **Check app logs for slow requests:**
   - Railway Logs → Look for duration > 30 seconds

3. **Optimize:**
   - Add database indexes
   - Implement query caching
   - Reduce data returned per request

4. **Increase timeout in Procfile:**
   ```
   web: gunicorn --timeout 120 -w 4 -b 0.0.0.0:$PORT run:app
   ```

---

### Issue 8: "500 Internal Server Error"

**What This Means:**
Unhandled exception in your application code

**Solution:**

1. **Check Railway logs for full error:**
   ```
   Railway Dashboard → Logs → Search for "Traceback"
   ```

2. **Read the full error message:**
   ```
   Traceback (most recent call last):
     File "app/__init__.py", line X, in create_app
       ...
   Exception: Description of what went wrong
   ```

3. **Common causes:**
   - Missing database table (run `db.create_all()`)
   - Syntax error in code
   - Missing import statement
   - Configuration issue

4. **Fix locally first:**
   ```bash
   python backend/run.py
   # Reproduce the error locally
   # Fix the code
   # Commit and push
   ```

---

### Issue 9: "ImportError: Cannot import name 'X'"

**What This Means:**
Module exists but doesn't have the symbol you're trying to import

**Example:**
```
ImportError: cannot import name 'LimitExceeded' from 'flask_limiter'
```

**Solution:**

1. **Check correct import path:**
   ```bash
   pip show flask-limiter
   python -c "from flask_limiter import Limiter"  # works
   python -c "from flask_limiter import LimitExceeded"  # check if exists
   ```

2. **Fix import in code:**
   ```python
   # Wrong
   from flask_limiter import LimitExceeded

   # Right (check docs)
   from flask_limiter.util import get_remote_address
   ```

3. **Verify package version compatibility:**
   ```bash
   pip list | grep flask-limiter
   # Check Flask-Limiter version in docs
   ```

---

### Issue 10: "ProgrammingError: relation does not exist"

**What This Means:**
Database table not created

**Solution:**

1. **Ensure `db.create_all()` is called:**
   ```python
   # In run.py (should already be there)
   if __name__ == '__main__':
       with app.app_context():
           db.create_all()
       app.run()
   ```

2. **For Railway deployment:**
   - Add initialization command to Procfile:
   ```
   release: python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"
   web: gunicorn -w 4 -b 0.0.0.0:$PORT run:app
   ```

3. **Or in Flask shell:**
   ```bash
   flask shell
   >>> db.create_all()
   >>> exit()
   ```

---

## 🔧 Debug Mode: Getting More Info

### Enable Verbose Logging

Add to `.env.production`:
```env
DEBUG=True
FLASK_ENV=development  # Temporarily for debugging
LOG_LEVEL=DEBUG
```

⚠️ **Warning**: Don't use `DEBUG=True` in production permanently (security risk)

### View Full Error Traceback

```bash
# In Railway Logs tab, scroll up to see full error
# Click "Expand" on log line to see full message
```

### Local Testing Before Railway Push

```bash
# Set same env vars locally
export FLASK_ENV=production
export DATABASE_URL_PROD=<your-supabase-url>
export SECRET_KEY=<your-key>
export JWT_SECRET_KEY=<your-jwt-key>

# Run locally
python backend/run.py

# Should show same startup sequence as Railway
```

---

## ✅ Health Check After Startup

Once app starts successfully:

```bash
# 1. Check health endpoint
curl https://trackit-production.up.railway.app/health

# 2. Should return 200 with:
{
  "success": true,
  "status_code": 200,
  "message": "OK"
}

# 3. Test database connectivity
curl -X POST https://trackit-production.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "organisation_name": "Test Org",
    "organisation_code": "TEST",
    "username": "admin",
    "email": "admin@test.com",
    "password": "Test123!"
  }'

# 4. Should create organization and return 201
```

---

## 📋 Startup Checklist

Before deploying to Railway:

- [ ] `backend/Procfile` exists with correct command
- [ ] `backend/requirements.txt` includes ALL dependencies
- [ ] `.env.production` has all required variables
- [ ] `run.py` calls `db.create_all()`
- [ ] App starts locally without errors
- [ ] Health endpoint works locally
- [ ] `psycopg2-binary` is in requirements.txt (for PostgreSQL)
- [ ] `gunicorn` is in requirements.txt (for Railway)
- [ ] No hardcoded database paths or localhost connections
- [ ] All imports use relative paths

---

## 🚨 Emergency Recovery

If Railway app won't start and keeps crashing:

### Option 1: Rollback to Previous Version

```
Railway Dashboard → Deployments tab → Find last working deployment → "Redeploy"
```

### Option 2: Disable Auto-Deploy

```
Railway → Settings → Uncheck "Auto-deploy on push"
```

Then manually fix code and redeploy.

### Option 3: Check Procfile

```bash
# Railway uses Procfile to start app
# It should exist at backend/Procfile
cat backend/Procfile
# Should show: web: gunicorn -w 4 -b 0.0.0.0:$PORT run:app
```

If Procfile is wrong:
1. Fix it locally
2. Commit: `git add backend/Procfile && git commit -m "Fix Procfile" && git push`
3. Railway redeploys (30 seconds)

---

## 📊 Monitoring Startup Health

### Check These Metrics Right After Deploy

In Railway Dashboard → Metrics:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| **Memory** | < 200MB | 200-500MB | > 500MB |
| **CPU** | < 10% | 10-50% | > 50% |
| **Restart Count** | 0 | 1-2 | > 3 |
| **Request Latency** | < 100ms | 100-500ms | > 1000ms |

---

## 📞 Support Resources

- **Railway Docs**: https://docs.railway.app
- **Flask Docs**: https://flask.palletsprojects.com
- **Supabase Docs**: https://supabase.com/docs
- **Gunicorn Docs**: https://gunicorn.org
- **Your GitHub**: https://github.com/Francischebo/TrackIT

---

## 🎯 Next Steps

1. **Deploy to Railway** using guide: `RAILWAY_DEPLOYMENT_GUIDE.md`
2. **Verify health** using checklist: `RAILWAY_VERIFICATION_CHECKLIST.md`
3. **Troubleshoot** using this guide if any issues
4. **Monitor** via Railway dashboard metrics

---

**Status**: ✅ Ready for production deployment  
**Last Updated**: [2026-05-22]  
**Guide Version**: 1.0
