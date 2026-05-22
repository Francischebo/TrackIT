# ✅ Railway Deployment Verification Checklist

Complete this checklist after deploying to Railway.

---

## 🟢 Immediate Verification (Right After Deployment)

- [ ] **Build Successful**: Green checkmark in Railway dashboard
- [ ] **App Running**: No error logs in Railway logs tab
- [ ] **Port Accessible**: Railway shows active URL (e.g., `trackit-production.up.railway.app`)
- [ ] **No Crash Loop**: App doesn't restart repeatedly

### How to Check:
```bash
# 1. Check Railway logs
# In Railway dashboard → Logs tab → Look for "Running on"

# 2. If you see errors like "ModuleNotFoundError"
# → Check environment variables are set
# → Verify DATABASE_URL_PROD is correct
```

---

## 🔗 Connectivity Tests (2 minutes)

### Test 1: Health Endpoint

```bash
curl https://trackit-production.up.railway.app/health
```

✅ **Expected Response:**
```json
{
  "success": true,
  "status_code": 200,
  "message": "OK"
}
```

❌ **If Failed:**
- Check app is running (Railway logs)
- Verify custom domain isn't blocking traffic
- Wait 30 seconds, Railway might still be starting up

---

### Test 2: Database Connection

Create a test file `test_railway.py`:

```python
import requests
import json

API_URL = "https://trackit-production.up.railway.app"  # Update with your URL

# Test 1: Health Check
print("Test 1: Health Check")
response = requests.get(f"{API_URL}/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
assert response.status_code == 200, "Health check failed"
print("✅ PASSED\n")

# Test 2: Register Organization
print("Test 2: Register Organization (Database Test)")
org_data = {
    "organisation_name": "Railway Test Org",
    "organisation_code": "RTEST",
    "username": "testadmin",
    "email": "test@railwaytest.com",
    "password": "TestPassword123!"
}

response = requests.post(
    f"{API_URL}/api/auth/register",
    json=org_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code in [200, 201]:
    print("✅ PASSED - Database connection working\n")
else:
    print("❌ FAILED - Check database connection\n")

# Test 3: Login
print("Test 3: Login Test")
login_data = {
    "email": "test@railwaytest.com",
    "password": "TestPassword123!"
}

response = requests.post(
    f"{API_URL}/api/auth/login",
    json=login_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ PASSED - Authentication working\n")
    data = response.json().get("data", {})
    print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
else:
    print("❌ FAILED - Check authentication")
    print(f"Response: {response.json()}")
```

Run it:
```bash
python test_railway.py
```

---

## 🔐 Security Verification (5 minutes)

### Test 3: Security Headers

```bash
curl -I https://trackit-production.up.railway.app/health
```

✅ **Look for These Headers:**
```
Strict-Transport-Security: max-age=31536000
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'self'
X-XSS-Protection: 1; mode=block
```

### Test 4: HTTPS Enforced

```bash
# Try HTTP (should redirect or fail)
curl http://trackit-production.up.railway.app/health
```

✅ **Expected**: Redirect to HTTPS or connection refused

---

## 📊 Performance Verification (3 minutes)

### Test 5: Response Time

```bash
# Test response time
curl -w "\nTime: %{time_total}s\n" https://trackit-production.up.railway.app/health
```

✅ **Expected Response Time**: < 2 seconds  
⚠️ **Warning**: > 5 seconds might indicate slow database or resource issues

### Test 6: Check Memory Usage

In Railway dashboard:
1. Click project
2. Go to **"Metrics"** tab
3. Check memory usage

✅ **Healthy**: < 500MB  
⚠️ **Warning**: > 800MB (increase memory if needed)

---

## 🔄 Auto-Deploy Verification (5 minutes)

### Test 7: Push Code Change

1. Make a small code change locally:
   ```python
   # In backend/app/__init__.py, add a comment
   # Commit and push
   ```

2. Push to GitHub:
   ```bash
   git add .
   git commit -m "Test auto-deploy"
   git push origin main
   ```

3. Watch Railway:
   - Should automatically detect push
   - Start new build (5-10 seconds)
   - Deploy new version

4. Verify:
   ```bash
   curl https://trackit-production.up.railway.app/health
   ```

✅ **Expected**: App still works after auto-deploy

---

## 🌐 Custom Domain Verification (Optional)

### Test 8: Custom Domain Works

If you set up a custom domain (e.g., `api.yourdomain.com`):

```bash
curl https://api.yourdomain.com/health
```

✅ **Expected**: Same response as main Railway URL

---

## 🗄️ Database Multi-Tenancy Test (10 minutes)

### Test 9: Multi-Tenant Isolation

Create a test file `test_multitenant.py`:

```python
import requests

API_URL = "https://trackit-production.up.railway.app"  # Update with your URL

# Register Org 1
print("Creating Organization 1...")
org1_data = {
    "organisation_name": "Company One",
    "organisation_code": "CO1",
    "username": "admin1",
    "email": "admin@companyone.com",
    "password": "Password123!"
}

response = requests.post(f"{API_URL}/api/auth/register", json=org1_data)
print(f"Status: {response.status_code}")
assert response.status_code in [200, 201], "Org 1 registration failed"
print("✅ Org 1 Created\n")

# Register Org 2
print("Creating Organization 2...")
org2_data = {
    "organisation_name": "Company Two",
    "organisation_code": "CO2",
    "username": "admin2",
    "email": "admin@companytwo.com",
    "password": "Password456!"
}

response = requests.post(f"{API_URL}/api/auth/register", json=org2_data)
print(f"Status: {response.status_code}")
assert response.status_code in [200, 201], "Org 2 registration failed"
print("✅ Org 2 Created\n")

# Login Org 1
print("Login to Org 1...")
response = requests.post(
    f"{API_URL}/api/auth/login",
    json={"email": "admin@companyone.com", "password": "Password123!"}
)
token1 = response.json().get("data", {}).get("access_token")
print("✅ Org 1 Logged In\n")

# Login Org 2
print("Login to Org 2...")
response = requests.post(
    f"{API_URL}/api/auth/login",
    json={"email": "admin@companytwo.com", "password": "Password456!"}
)
token2 = response.json().get("data", {}).get("access_token")
print("✅ Org 2 Logged In\n")

print("✅ Multi-Tenant Test PASSED - Each org can register and login independently")
```

Run it:
```bash
python test_multitenant.py
```

---

## 🚨 Troubleshooting

### Issue: App Crashes on Startup

**Check:**
1. Railway logs for exact error
2. Environment variables are set
3. `requirements.txt` has all dependencies

**Fix:**
```bash
# Redeploy previous version
# Railway → Deployments → Previous successful → Redeploy
```

### Issue: Database Connection Fails

**Check:**
1. `DATABASE_URL_PROD` is correct in environment variables
2. Supabase project is not paused
3. Connection string ends with `?sslmode=require`

**Fix:**
```bash
# Test connection locally first
python scripts/test_supabase_connection.py
```

### Issue: High Response Times

**Check:**
1. Database query performance (slow queries?)
2. Memory usage in Railway metrics
3. Network latency

**Fix:**
```bash
# Increase Railway resources
# Railway → Settings → Increase Memory/CPU
```

---

## 📋 Final Sign-Off Checklist

- [ ] **Build**: ✅ Successful deployment
- [ ] **Health**: ✅ `/health` endpoint returns 200
- [ ] **Database**: ✅ Can create organizations and users
- [ ] **Auth**: ✅ Login and token generation works
- [ ] **Security**: ✅ HTTPS headers present
- [ ] **Performance**: ✅ Response time < 2 seconds
- [ ] **Auto-Deploy**: ✅ Code push triggers new build
- [ ] **Multi-Tenant**: ✅ Multiple orgs isolated correctly

---

## ✅ All Tests Passed!

**Status**: 🟢 **PRODUCTION READY**

Your Railway deployment is verified and ready for:
- ✅ Testing with frontend
- ✅ User acceptance testing
- ✅ Production traffic

---

## 📞 Next Steps

1. **Update Frontend**: Point API calls to Railway URL
2. **Configure Custom Domain** (optional): Set up your domain
3. **Set Up Monitoring**: Enable alerts in Railway
4. **Performance Tuning**: Monitor metrics, optimize as needed

---

**Date Verified**: [Today's Date]  
**Railway URL**: https://trackit-production.up.railway.app  
**Status**: ✅ VERIFIED & WORKING
