# Quick Troubleshooting Guide

## Error: "TypeError: Talisman.init_app() got an unexpected keyword argument"

✅ **FIXED** - Updated Flask-Talisman parameters in `backend/app/__init__.py`

---

## Test 1: Verify App Can Start

```bash
cd backend
python -c "from app import create_app; app = create_app('development'); print('✅ App OK')"
```

Expected: `✅ App OK`

---

## Test 2: Start Dev Server

```bash
cd backend
set FLASK_ENV=development
python run.py
```

Expected output:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

---

## Test 3: Check Health Endpoint

In another terminal:

```bash
curl http://localhost:5000/health
```

Expected response:
```json
{"success":true,"status_code":200,"message":"OK"}
```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "Address already in use"

Port 5000 is already in use.

**Solution:**
```bash
# Find and kill the process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or use a different port:
set FLASK_RUN_PORT=5001
python run.py
```

### Issue: "database is locked" (SQLite)

SQLite doesn't handle concurrent access well.

**Solution:**
- Use Supabase (PostgreSQL) for production
- For dev, use production mode with SQLite pragmas already configured

### Issue: "Password authentication failed" (Supabase)

Connection string password is wrong.

**Solution:**
- Verify password: `Fr@38998653`
- Verify connection string format with `?sslmode=require`
- Test connection: `python scripts/test_supabase_connection.py`

---

## Environment Variable Check

To verify variables are loaded:

```bash
# Windows
echo %FLASK_ENV%
echo %DATABASE_URL_PROD%

# Linux/Mac
echo $FLASK_ENV
echo $DATABASE_URL_PROD
```

Should show your values, not empty.

---

## Run Tests

```bash
cd backend
pytest -v --cov=app
```

This will run all unit tests and show coverage.

---

## Debug Mode

For more detailed error messages:

```bash
set FLASK_DEBUG=1
set FLASK_ENV=development
python run.py
```

The app will reload on code changes and show detailed error pages.

---

## Need More Help?

See full documentation:
- `SUPABASE_QUICK_START.md` - Quick start guide
- `SUPABASE_SETUP.md` - Complete setup
- `TALISMAN_FIX.md` - Security headers fix
- `AUTH_ARCHITECTURE.md` - Authentication details

---

**Status**: ✅ Ready to run!
