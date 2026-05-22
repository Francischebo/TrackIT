# Supabase Multi-Tenant Setup Guide for TrackIT

This guide walks through configuring the TrackIT Assets & Inventory Management System with Supabase PostgreSQL for multi-tenant architecture.

---

## 📋 Prerequisites

- Supabase account (free tier for testing)
- Supabase project created
- Supabase credentials obtained
- Python 3.8+ installed
- Git installed

---

## 🔑 Supabase Project Credentials

Your Supabase project details:

| Item | Value |
|------|-------|
| **Project URL** | https://zatfehhphmxhtznnmggn.supabase.co |
| **Project ID** | zatfehhphmxhtznnmggn |
| **Anon/Publishable Key** | sb_publishable_HMxEKQLyP_P8fn5DDiO_cA_RX42ZFSx |
| **Database Host** | db.zatfehhphmxhtznnmggn.supabase.co |
| **Database Port** | 5432 |
| **Database Name** | postgres |
| **Database User** | postgres |
| **Direct Connection** | postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres |

---

## ✅ Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key packages for Supabase:
- `psycopg2-binary==2.9.9` (PostgreSQL adapter)
- `SQLAlchemy==1.4.54` (ORM)
- `Flask-SQLAlchemy==2.5.1` (Flask integration)
- `alembic==1.13.1` (Migrations)

---

## ✅ Step 2: Configure Environment Variables

### Option A: Copy template and configure

```bash
cp .env.example .env.production
```

Edit `.env.production` with:

```env
# Supabase Connection
DATABASE_URL_PROD=postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require

# Flask Settings
FLASK_ENV=production
SECRET_KEY=<generate-with-command-below>
JWT_SECRET_KEY=<generate-with-command-below>

# CORS Origins (update with your frontend domain)
CORS_ORIGINS=https://localhost:3000,https://yourdomain.com

# Multi-tenant Configuration
ENABLE_MULTI_TENANCY=True
MULTI_TENANT_SCHEMA_PREFIX=tenant_
```

**Generate secure keys:**

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

### Option B: Use provided .env.supabase

```bash
cp .env.supabase .env.production
# Then edit values as needed
```

**⚠️ IMPORTANT**: Never commit `.env.production` to Git!

Add to `.gitignore`:
```
.env
.env.production
.env.supabase
```

---

## ✅ Step 3: Test Supabase Connection

Create a test script `backend/test_supabase_connection.py`:

```python
#!/usr/bin/env python3
"""Test Supabase PostgreSQL connection"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.production')

# Get connection string
db_url = os.environ.get('DATABASE_URL_PROD')
if not db_url:
    print("❌ ERROR: DATABASE_URL_PROD not set in environment")
    exit(1)

print(f"📍 Connecting to: {db_url.split('@')[1] if '@' in db_url else 'unknown'}")

try:
    # Create engine
    engine = create_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={'sslmode': 'require'}
    )
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"📦 PostgreSQL Version: {version}")
        
        # Test schema listing
        result = conn.execute(text("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'extensions')
            ORDER BY schema_name;
        """))
        schemas = result.fetchall()
        print(f"\n📂 Available Schemas:")
        for schema in schemas:
            print(f"   - {schema[0]}")
        
        if not schemas:
            print("   (None yet - will be created during initialization)")
    
    print("\n✅ Supabase connection verified!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)
```

Run the test:

```bash
export DATABASE_URL_PROD='postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require'
python backend/test_supabase_connection.py
```

Expected output:
```
📍 Connecting to: db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres
✅ Connected successfully!
📦 PostgreSQL Version: PostgreSQL 14.x (Supabase)

📂 Available Schemas:
   - public
   (None yet - will be created during initialization)

✅ Supabase connection verified!
```

---

## ✅ Step 4: Initialize Database Schema

The TrackIT system uses multi-tenant architecture with:
- **Public schema** (shared): organizations, users, token_blacklist
- **Tenant schemas** (isolated): tenant_0001, tenant_0002, etc.

### Automatic Initialization

When the first organization is created, `tenant_migrations.py` automatically:

1. **Creates organization record** in public schema
2. **Creates tenant schema** (tenant_XXXX)
3. **Locks schema creation** with PostgreSQL advisory locks (prevents race conditions)
4. **Initializes all tables** in the tenant schema
5. **Records migration** in schema_migrations table

### Manual Schema Setup (Optional)

Create `backend/scripts/init_supabase.py`:

```python
#!/usr/bin/env python3
"""Initialize Supabase database for multi-tenant TrackIT"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.organization import Organization
from app.models.user import User

# Load environment
env_file = sys.argv[1] if len(sys.argv) > 1 else '.env.production'
load_dotenv(env_file)

print("🚀 Initializing TrackIT on Supabase...")

try:
    # Create Flask app
    app = create_app('production')
    
    with app.app_context():
        # Create all public schema tables
        print("📝 Creating public schema tables...")
        db.create_all()
        print("✅ Public schema initialized")
        
        # Create public schema migrations tracking
        from sqlalchemy import text
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        # Create schema_migrations table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("✅ Migration tracking table created")
        
        # Create default organization (optional, for testing)
        if not Organization.query.filter_by(code='ADMIN').first():
            print("📦 Creating admin organization...")
            admin_org = Organization(
                name='Admin Organization',
                code='ADMIN',
                description='System administration organization'
            )
            db.session.add(admin_org)
            db.session.commit()
            print(f"✅ Admin organization created (ID: {admin_org.id})")
        
        print("\n✅ Supabase initialization complete!")
        print("\n📊 Next steps:")
        print("   1. Register organizations via /api/auth/register")
        print("   2. Multi-tenant schemas will be created automatically")
        print("   3. Each organization gets isolated schema (tenant_XXXX)")
        
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
```

Run initialization:

```bash
python backend/scripts/init_supabase.py .env.production
```

---

## ✅ Step 5: Verify Multi-Tenant Schema Setup

After creating organizations, verify schemas are isolated:

Create `backend/scripts/verify_multi_tenancy.py`:

```python
#!/usr/bin/env python3
"""Verify multi-tenant schema isolation"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('.env.production')

db_url = os.environ.get('DATABASE_URL_PROD')
engine = create_engine(db_url, echo=False, connect_args={'sslmode': 'require'})

print("🔍 Verifying Multi-Tenant Schema Isolation\n")

with engine.connect() as conn:
    # List all schemas
    print("📂 Available Schemas:")
    result = conn.execute(text("""
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'tenant_%' OR schema_name = 'public'
        ORDER BY schema_name;
    """))
    schemas = result.fetchall()
    for schema in schemas:
        print(f"   ✓ {schema[0]}")
    
    # Show organizations
    print("\n👥 Organizations (public schema):")
    result = conn.execute(text("SELECT id, name, code FROM public.organizations;"))
    orgs = result.fetchall()
    if orgs:
        for org_id, name, code in orgs:
            print(f"   ✓ ID {org_id}: {name} ({code}) → Schema: tenant_{org_id:04d}")
    else:
        print("   (No organizations yet)")
    
    # Verify schema isolation
    print("\n🔐 Schema Isolation Test:")
    for org_id in [org[0] for org in orgs]:
        schema = f"tenant_{org_id:04d}"
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.assets;"))
            count = result.fetchone()[0]
            print(f"   ✓ {schema}: {count} assets")
        except Exception as e:
            print(f"   ❌ {schema}: {e}")
    
    print("\n✅ Multi-tenancy verification complete!")
```

Run verification:

```bash
python backend/scripts/verify_multi_tenancy.py
```

---

## ✅ Step 6: Configure Connection Pooling

For production, Supabase has built-in PgBouncer connection pooling.

Update `backend/config.py`:

```python
class ProductionConfig(Config):
    """Production configuration for Supabase"""
    
    DEBUG = False
    
    # Supabase connection with SSL required
    _db_url = os.environ.get("DATABASE_URL_PROD")
    if _db_url and "sslmode=" not in _db_url:
        _db_url += "?sslmode=require"
    SQLALCHEMY_DATABASE_URI = _db_url
    
    # Connection pool optimized for Supabase
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,              # Connection pool size
        "max_overflow": 0,             # No overflow connections
        "pool_pre_ping": True,         # Test connection before use
        "pool_recycle": 3600,          # Recycle connections every hour
        "client_encoding": "utf8",
        "echo": False,
    }
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    JWT_COOKIE_SECURE = True
    
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "").split(",")
```

---

## ✅ Step 7: Set Environment Variable for Runtime

When running the application:

**Development (SQLite):**
```bash
export FLASK_ENV=development
# Uses sqlite:///trackit_dev.db
python run.py
```

**Production (Supabase):**
```bash
export FLASK_ENV=production
export DATABASE_URL_PROD='postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require'
export SECRET_KEY='<your-generated-key>'
export JWT_SECRET_KEY='<your-generated-key>'
python run.py
```

**Using .env file:**
```bash
source .env.production  # On Linux/Mac
# or
set -a; source .env.production; set +a  # Bash
# or on Windows:
# (Manually set in Command Prompt or use python-dotenv)

python run.py
```

---

## ✅ Step 8: Test Multi-Tenant Organization Registration

### 1. Start the application

```bash
export FLASK_ENV=production
export DATABASE_URL_PROD='postgresql://postgres:Fr@38998653@db.zatfehhphmxhtznnmggn.supabase.co:5432/postgres?sslmode=require'
python run.py
```

### 2. Register first organization

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "organisation_name": "Acme Corporation",
    "organisation_code": "ACME",
    "username": "admin",
    "email": "admin@acme.com",
    "password": "Secure@Pass123"
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

### 3. Verify schema created

Check Supabase:
```sql
-- In Supabase SQL Editor or any PostgreSQL client
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name LIKE 'tenant_%' 
ORDER BY schema_name;
```

You should see: `tenant_0001`

### 4. Register second organization

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "organisation_name": "Manufacturing Inc",
    "organisation_code": "MFGINC",
    "username": "admin2",
    "email": "admin@mfginc.com",
    "password": "Secure@Pass456"
  }'
```

### 5. Verify both schemas exist

```sql
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name LIKE 'tenant_%' 
ORDER BY schema_name;
```

Should show: `tenant_0001`, `tenant_0002`

---

## 🔐 Security Checklist

- [x] SSL/TLS enabled (sslmode=require)
- [x] Database password changed from default
- [x] Connection pooling configured
- [x] Row-level security can be enabled via Supabase dashboard
- [x] JWT secrets properly generated
- [x] CORS origins restricted to frontend domain
- [ ] Multi-factor authentication enabled in Supabase
- [ ] Regular backups configured in Supabase

---

## ⚠️ Free Tier Limitations

**Supabase Free Tier:**
- 500 MB database storage
- 1 GB bandwidth/month
- No custom domains
- Paused after 1 week of inactivity
- Connection limit: 10 concurrent connections

**For Production Multi-Tenancy**, upgrade to:
- **Pro Plan** ($25/month): 100 GB storage, 250 GB bandwidth, always active
- **Enterprise**: Unlimited resources, custom SLAs

See: https://supabase.com/pricing

---

## 📚 Troubleshooting

### Connection Refused

```
Error: could not connect to server: Connection refused
```

**Solution:**
1. Verify Supabase project is active (not paused)
2. Check project is running (Supabase dashboard)
3. Verify password is correct
4. Check sslmode=require is in connection string

### Authentication Failed

```
Error: FATAL: password authentication failed for user "postgres"
```

**Solution:**
1. Double-check password: `Fr@38998653`
2. Verify special characters (@) are URL-encoded if needed
3. Reset database password in Supabase dashboard

### Pool Timeout

```
QueuePool limit exceeded with overflow=0, pool_size=10 timeout=30
```

**Solution:**
1. Increase pool_size in config.py
2. Check for connection leaks (connections not being returned)
3. Review application logs for hanging queries

### Schema Not Found

```
Error: schema "tenant_0001" does not exist
```

**Solution:**
1. Organization registration may have failed
2. Check organization record exists: `SELECT * FROM public.organizations;`
3. Verify tenant_migrations.py ran without errors
4. Check Supabase logs in dashboard

### Free Tier Project Paused

Supabase pauses free projects after 1 week of inactivity.

**Solution:**
1. Visit Supabase dashboard
2. Click project name
3. Click "Resume" button
4. Wait for restart (1-2 minutes)

---

## 🎯 Next Steps

1. **Push to GitHub**
   ```bash
   git add .env.supabase SUPABASE_SETUP.md backend/scripts/
   git commit -m "docs: Add Supabase multi-tenant configuration"
   git push origin main
   ```

2. **Build React Frontend**
   - Use FRONTEND_INTEGRATION.md guide
   - Point API_BASE_URL to your deployed backend

3. **Load Testing**
   - Test concurrent organization registrations
   - Verify advisory locks prevent race conditions
   - Monitor connection pool usage

4. **Upgrade to Pro Tier** (when ready for production)
   - Supabase dashboard → Projects → Settings → Upgrade
   - Gain: More storage, bandwidth, always-on, higher connection limits

---

## 📖 References

- **Supabase Docs**: https://supabase.com/docs
- **PostgreSQL Multi-Schema**: https://www.postgresql.org/docs/current/sql-createschema.html
- **Alembic Migrations**: https://alembic.sqlalchemy.org/
- **TrackIT Auth**: See AUTH_ARCHITECTURE.md
- **Multi-Tenancy**: See SYSTEM_ARCHITECTURE.md

---

**Created**: 2026-05-21  
**Status**: ✅ Ready for Testing  
**Tier**: Supabase Free (testing) → Pro/Enterprise (production)
