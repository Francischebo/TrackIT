# Supabase Quick Start for TrackIT

Fast setup guide for running TrackIT on Supabase with multi-tenant architecture.

---

## 🚀 5-Minute Setup

### 1. Copy Credentials to `.env.production`

Create `backend/.env.production`:

```env
# Supabase PostgreSQL Connection
DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require

# Generate these with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<your-generated-secret-key>
JWT_SECRET_KEY=<your-generated-jwt-secret-key>

# Flask Settings
FLASK_ENV=production
FLASK_APP=run.py

# CORS (update with your frontend URL)
CORS_ORIGINS=https://localhost:3000,https://yourdomain.com

# Security
BCRYPT_LOG_ROUNDS=12
FORCE_HTTPS=True
DEBUG=False
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Test Connection

```bash
# Windows
set DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require
python ../scripts/test_supabase_connection.py

# Linux/Mac
export DATABASE_URL_PROD='postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require'
python ../scripts/test_supabase_connection.py
```

Expected output:
```
✅ Connected successfully!
📦 PostgreSQL Version: PostgreSQL 14.x (Supabase)
📂 Current Database: postgres
👤 Current User: postgres
```

### 4. Start the Application

```bash
# Windows
set FLASK_ENV=production
set DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require
set SECRET_KEY=<your-key>
set JWT_SECRET_KEY=<your-key>
python run.py

# Linux/Mac
export FLASK_ENV=production
export DATABASE_URL_PROD='postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require'
export SECRET_KEY='<your-key>'
export JWT_SECRET_KEY='<your-key>'
python run.py
```

### 5. Register First Organization

```bash
curl -X POST http://localhost:5000/api/auth/register \
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

**✅ Your first tenant schema is now created: `tenant_0001`**

---

## 📊 Supabase Credentials Reference

| Key | Value |
|-----|-------|
| Project URL | https://zatfehhphmxhtznnmggn.supabase.co |
| Project ID | zatfehhphmxhtznnmggn |
| Database Host | db.zatfehhphmxhtznnmggn.supabase.co |
| Database Port | 5432 |
| Database User | postgres |
| Database Password | Fr@38998653 |
| SSL Mode | require |
| Anon Key | sb_publishable_HMxEKQLyP_P8fn5DDiO_cA_RX42ZFSx |

---

## 🔐 Security Notes

⚠️ **IMPORTANT**: The `.env.production` file contains secrets!

1. **Never commit to Git** - Add to `.gitignore`:
   ```
   .env
   .env.production
   .env.supabase
   ```

2. **In production**, use:
   - Environment variables in CI/CD (GitHub Actions secrets)
   - Managed secrets service (AWS Secrets Manager, etc.)
   - Never hardcode credentials

3. **Generate strong keys**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

---

## 🧪 Testing Multi-Tenancy

### Create Second Organization

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "organisation_name": "MFG Inc",
    "organisation_code": "MFGINC",
    "username": "admin2",
    "email": "admin2@mfginc.com",
    "password": "SecurePassword456!"
  }'
```

### Verify Both Schemas

```bash
python scripts/verify_multi_tenancy.py
```

Expected output:
```
📂 Available Schemas:
   ✓ public (2 tables)
   ✓ tenant_0001 (20 tables)
   ✓ tenant_0002 (20 tables)

👥 Organizations:
   ✓ ID 1: Acme Corporation (ACME) → tenant_0001
   ✓ ID 2: MFG Inc (MFGINC) → tenant_0002
```

---

## 🔄 Architecture Overview

```
Your Application
    │
    ├─ Login: org_id=1 → SET search_path TO tenant_0001
    │                  → All queries use tenant_0001 schema
    │
    ├─ Login: org_id=2 → SET search_path TO tenant_0002
    │                  → All queries use tenant_0002 schema
    │
    └─ Public Data    → organizations, users (shared, row-level filtered)

Supabase PostgreSQL
    │
    ├─ public schema
    │  ├─ organizations (org1, org2, ...)
    │  ├─ users (user1, user2, ...)
    │  └─ token_blacklist
    │
    ├─ tenant_0001 schema (Acme Corp - completely isolated)
    │  ├─ assets (Acme's assets only)
    │  ├─ inventory_items (Acme's inventory)
    │  └─ ... (all business tables)
    │
    └─ tenant_0002 schema (MFG Inc - completely isolated)
       ├─ assets (MFG's assets only)
       ├─ inventory_items (MFG's inventory)
       └─ ... (all business tables)
```

---

## 💡 Key Features

### ✅ Multi-Tenancy (Free Tier Ready)
- Each organization gets isolated PostgreSQL schema
- Complete data separation
- No data leakage between tenants
- Race-condition free with advisory locks

### ✅ Zero Downtime
- Works with existing Flask app
- SQLite for dev, PostgreSQL for prod
- Connection pooling configured

### ✅ Enterprise Ready
- SSL/TLS encrypted
- HSTS headers (1 year)
- JWT authentication
- Rate limiting
- CORS hardening
- CSP security headers

---

## ⚠️ Free Tier Limitations

| Limit | Value |
|-------|-------|
| Storage | 500 MB |
| Bandwidth | 1 GB/month |
| Connections | 10 concurrent |
| Projects | Paused after 1 week inactivity |
| Custom Domain | ❌ Not available |
| SLA | ❌ Not included |

**Upgrade to Pro** when needed: https://supabase.com/pricing

---

## 🐛 Troubleshooting

### Connection Refused
```
Error: could not connect to server
```
- ✓ Verify Supabase project is active (check dashboard)
- ✓ Verify password: `Fr@38998653`
- ✓ Verify `sslmode=require` is in URL

### Authentication Failed
```
Error: password authentication failed
```
- ✓ Check password exactly: `Fr@38998653`
- ✓ URL encode special chars if needed: `@` → `%40`
- ✓ Reset password in Supabase dashboard

### Pool Timeout
```
QueuePool limit exceeded
```
- ✓ Increase `pool_size` in `config.py`
- ✓ Check for connection leaks
- ✓ Review application logs

### Schema Not Found
```
Error: schema "tenant_0001" does not exist
```
- ✓ Organization registration failed
- ✓ Check: `SELECT * FROM public.organizations;`
- ✓ Check Supabase logs in dashboard

### Free Tier Paused
Project automatically pauses after 1 week of inactivity.
- ✓ Visit Supabase dashboard
- ✓ Click "Resume" button
- ✓ Wait 1-2 minutes for restart

---

## 📖 Full Documentation

For complete setup details, see:
- **SUPABASE_SETUP.md** - Comprehensive guide
- **SYSTEM_ARCHITECTURE.md** - Database schemas
- **AUTH_ARCHITECTURE.md** - Authentication
- **FRONTEND_INTEGRATION.md** - React integration

---

## 🚀 Next Steps

1. **Customize Organization Names**
   - Edit `organisation_code` in registration

2. **Add More Users**
   - POST to `/api/users/` endpoint (admin only)

3. **Upload Assets**
   - POST to `/api/assets/` endpoint

4. **Build React Frontend**
   - Follow FRONTEND_INTEGRATION.md

5. **Deploy to Production**
   - Use GitHub Actions CI/CD
   - Set DATABASE_URL_PROD in CI/CD secrets

---

**Status**: ✅ Ready for Testing  
**Tier**: Supabase Free (testing) → Pro (production)  
**Multi-Tenancy**: ✅ Enabled  
**Data Isolation**: ✅ Guaranteed
