# 🚨 App Startup Hang - Diagnostic & Fix Guide

**Problem**: App hangs during startup and never completes  
**Likely Cause**: Database connection timeout waiting for Supabase or missing DATABASE_URL  
**Fix Time**: 5 minutes

---

## 🔍 Diagnosis Steps

### Step 1: Check Environment Variables

```bash
# Windows
echo %DATABASE_URL_PROD%
echo %FLASK_ENV%
echo %SECRET_KEY%
echo %JWT_SECRET_KEY%
```

⚠️ **If empty**, that's your problem!

### Step 2: Check Supabase Status

1. Go to: https://supabase.com/dashboard
2. Click your project
3. **If it says "PAUSED"**: Click **"Resume"** immediately
4. Wait for status to be "Healthy"

### Step 3: Test Connection Directly

```bash
# In backend directory
python scripts/test_supabase_connection.py

# Or run this in Python shell:
import os
from sqlalchemy import create_engine, text
db_url = os.environ.get("DATABASE_URL_PROD")
print(f"Connection string: {db_url}")
if db_url:
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
else:
    print("DATABASE_URL_PROD not set!")
```

---

## ⚡ Quick Fixes (Try These First)

### Fix #1: Set Environment Variables

**Windows CMD:**
```bash
set FLASK_ENV=development
set DATABASE_URL=sqlite:///trackit_dev.db
set SECRET_KEY=test-key-12345
set JWT_SECRET_KEY=test-jwt-key-12345
set CORS_ORIGINS=http://localhost:3000
cd backend
python run.py
```

**Windows PowerShell:**
```powershell
$env:FLASK_ENV="development"
$env:DATABASE_URL="sqlite:///trackit_dev.db"
$env:SECRET_KEY="test-key-12345"
$env:JWT_SECRET_KEY="test-jwt-key-12345"
$env:CORS_ORIGINS="http://localhost:3000"
cd backend
python run.py
```

### Fix #2: Use SQLite for Development (Fastest)

Instead of Supabase, use local SQLite:

```bash
# Create .env file in backend directory
FLASK_ENV=development
DATABASE_URL=sqlite:///trackit_dev.db
SECRET_KEY=test-dev-secret-key-12345
JWT_SECRET_KEY=test-dev-jwt-secret-key-12345
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
DEBUG=True
```

Then run:
```bash
python run.py
```

Expected output:
```
[2026-05-22 15:05:00,139] INFO in logging_utils: TrackIT Management System startup
 * Running on http://127.0.0.1:5000
```

### Fix #3: Increase Database Connection Timeout

Edit `backend/config.py`:

```python
# Line 39-44: Add connection timeout
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "client_encoding": "utf8",
    "connect_args": {
        "connect_timeout": 10,  # 10 seconds instead of default 5
    },
}
```

---

## 🔧 Root Cause Investigation

### Most Likely Cause: Missing DATABASE_URL

The app tries to connect to the database but can't find the connection string.

**Check:**
```bash
# On Windows
echo %DATABASE_URL_PROD%
echo %DATABASE_URL%

# Should output something like:
# postgresql://postgres:password@host:5432/db
```

**If empty**, do this:

```bash
# Option A: Use SQLite for development
set DATABASE_URL=sqlite:///trackit_dev.db

# Option B: Use Supabase for production
set DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require
set FLASK_ENV=production
```

---

### Second Most Likely: Supabase is Paused

Supabase free tier pauses after 1 week of inactivity.

**Fix:**
1. Go to: https://supabase.com/dashboard
2. Click your project
3. Click **"Resume"** if it's paused
4. Wait 30 seconds
5. Try running app again

---

### Third Cause: Missing SSL Certificate

PostgreSQL connection requires SSL.

**Check in connection string:**
```
✅ postgresql://...?sslmode=require
❌ postgresql://... (missing sslmode)
```

**Fix:**
```bash
# Update .env or environment variable
DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require
```

---

## 🚀 Complete Fix Walkthrough

### Step 1: Create .env file (Development)

Create file: `backend/.env`

```env
FLASK_ENV=development
DATABASE_URL=sqlite:///trackit_dev.db
SECRET_KEY=dev-test-secret-key-12345
JWT_SECRET_KEY=dev-test-jwt-secret-key-12345
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
DEBUG=True
```

### Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Start App

```bash
python run.py
```

### Step 4: Verify

Should see:
```
[timestamp] INFO in logging_utils: TrackIT Management System startup
 * Running on http://127.0.0.1:5000
```

Then in another terminal:
```bash
curl http://localhost:5000/health
```

Should return:
```json
{"status":"healthy","services":{"database":"up"},...}
```

---

## 🆘 Still Hanging?

### Nuclear Option: Start Minimal

Create `test_startup_minimal.py`:

```python
import os
os.environ['FLASK_ENV'] = 'development'
os.environ['DATABASE_URL'] = 'sqlite:///trackit_dev.db'
os.environ['SECRET_KEY'] = 'test-key'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-key'

print("1. Importing Flask...")
from flask import Flask
print("   OK")

print("2. Creating app...")
from app import create_app
print("   OK")

print("3. Initializing app with config...")
app = create_app('development')
print("   OK")

print("4. Testing routes...")
with app.test_client() as client:
    print("   Testing /health...")
    response = client.get('/health')
    print(f"   Status: {response.status_code}")
    
print("\nALL CHECKS PASSED!")
```

Run it:
```bash
python test_startup_minimal.py
```

This will tell us exactly where it hangs.

---

## 🔌 Connection String Template

### Development (SQLite)
```
sqlite:///trackit_dev.db
```

### Production (Supabase PostgreSQL)
```
postgresql://postgres:PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres?sslmode=require
```

**Replace:**
- `PASSWORD` - Your Supabase password
- `PROJECT_ID` - Your Supabase project ID

---

## 📋 Checklist to Fix Hang

- [ ] Set FLASK_ENV (development or production)
- [ ] Set DATABASE_URL or DATABASE_URL_PROD
- [ ] Set SECRET_KEY
- [ ] Set JWT_SECRET_KEY
- [ ] If PostgreSQL: Add `?sslmode=require` to connection string
- [ ] If Supabase: Check project is "Healthy" (not paused)
- [ ] Test connection: `python scripts/test_supabase_connection.py`
- [ ] Start app: `python run.py`
- [ ] Should see "Running on" message within 5 seconds

---

## 🎯 Expected Startup Output

When working correctly:

```
[2026-05-22 15:05:00,139] INFO in logging_utils: TrackIT Management System startup
[2026-05-22 15:05:00,200] INFO in app: Flask app initialized
[2026-05-22 15:05:00,250] INFO in database: Database connection pooling configured
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

⏱️ **Should complete in < 5 seconds**

---

## 🔐 For Railway Production

Set these environment variables in Railway dashboard:

```env
FLASK_ENV=production
DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require
SECRET_KEY=<your-generated-key>
JWT_SECRET_KEY=<your-generated-jwt-key>
CORS_ORIGINS=https://yourdomain.com
DEBUG=False
```

Then deploy - it should start in < 10 seconds.

---

## 📞 Still Need Help?

1. **Run the minimal test**: `python test_startup_minimal.py`
2. **Check output for exact hang point**
3. **Post the output** so I can diagnose precisely

---

**Status**: 🔧 Fixable issue (likely config related)  
**Time to Fix**: 2-5 minutes  
**Next Step**: Try Fix #1 or #2 above
