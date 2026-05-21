# Database Migration & Deployment Guide

## Overview

This guide covers database migrations, deployment strategies, and CI/CD configuration for the TrackIT system.

## Migration Architecture

### Multi-Tenant Migration Strategy

Each tenant (organization) gets its own schema in PostgreSQL:
- Schema naming: `tenant_XXXX` (where XXXX is org_id padded to 4 digits)
- Each schema has its own `schema_migrations` table
- Migrations are applied per-schema to maintain isolation

### Migration Lifecycle

```
1. Dev creates migration file (alembic revision)
2. Migration placed in alembic/versions/
3. Tenant initialization auto-applies initial migration
4. Subsequent migrations run per-schema via maintenance scripts
```

## Setting Up Alembic

### Initial Setup (Already Done)

```bash
cd backend
alembic init alembic
```

### Configuration

The `alembic.ini` file is configured to:
- Use SQLAlchemy for database connection
- Store migration versions in `alembic/versions/`
- Track schema migrations per tenant

### Alembic Environment Setup

Edit `alembic/env.py` to support multi-tenant migrations:

```python
from app import create_app, db
from app.models import *

def run_migrations_online():
    """Run migrations in multi-tenant mode"""
    
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        connectable = db.engine
        
        with connectable.connect() as connection:
            # For multi-tenant: handle schema switching here
            transaction = connection.begin()
            try:
                context.configure(
                    connection=connection,
                    target_metadata=db.metadata,
                )
                
                with context.begin_transaction():
                    context.run_migrations()
                transaction.commit()
            except Exception:
                transaction.rollback()
                raise
```

## Running Migrations

### Local Development

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "Add column to assets"

# Review the generated migration file
cat alembic/versions/xxxx_add_column_to_assets.py

# Apply migration to all tenant schemas
python scripts/migrate_all_tenants.py upgrade

# Rollback last migration
python scripts/migrate_all_tenants.py downgrade
```

### Production (Supabase PostgreSQL)

```bash
# Set environment variables
export DATABASE_URL_PROD="postgresql://user:pass@your-supabase.com/database?sslmode=require"
export FLASK_ENV=production

# Apply migrations
python scripts/migrate_all_tenants.py upgrade

# Verify migration status
python scripts/check_migration_status.py
```

## Migration Scripts

### Migrate All Tenants

Create `backend/scripts/migrate_all_tenants.py`:

```python
#!/usr/bin/env python
import os
import sys
import click
from dotenv import load_dotenv
load_dotenv()

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text, create_engine

@click.command()
@click.argument('command', type=click.Choice(['upgrade', 'downgrade']))
@click.option('--org-id', type=int, help='Specific org ID to migrate')
def migrate(command, org_id):
    """Migrate database schemas for all or specific tenant"""
    
    db_url = os.environ.get('DATABASE_URL_PROD') or os.environ.get('DATABASE_URL')
    engine = create_engine(db_url)
    
    from app import create_app
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Get all organizations
        from app.models.organization import Organization
        orgs = [Organization.query.get(org_id)] if org_id else Organization.query.all()
        
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        for org in orgs:
            schema_name = f"tenant_{org.id:04d}"
            click.echo(f"Migrating {schema_name}...")
            
            with engine.connect() as conn:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.execute(text(f"SET search_path TO {schema_name}"))
                conn.commit()
                
                # Apply migrations
                alembic_script = ScriptDirectory.from_config(alembic_cfg)
                migration_context = MigrationContext.configure(conn)
                
                if command == "upgrade":
                    upgrade(alembic_cfg, conn, alembic_script)
                else:
                    downgrade(alembic_cfg, conn, alembic_script)

if __name__ == '__main__':
    migrate()
```

## Deployment Strategies

### Strategy 1: Docker Compose (Development)

```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec app python scripts/migrate_all_tenants.py upgrade

# Seed test data
docker-compose exec app python db_seed.py
```

### Strategy 2: Docker (Production on Supabase)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Migrations run on startup
CMD ["sh", "-c", "python scripts/migrate_all_tenants.py upgrade && gunicorn --bind 0.0.0.0:8000 --workers 4 'app:create_app()']
```

### Strategy 3: CI/CD Pipeline (GitHub Actions)

See `.github/workflows/ci-cd.yml` for:
- Automated testing on PR
- Docker image building on merge to main
- Automatic deployment to production

### Strategy 4: Manual Deployment (SSH + Git)

```bash
# SSH into server
ssh user@production-server

# Navigate to app directory
cd /app/TrackIT

# Pull latest code
git pull origin main

# Install/update dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend
python scripts/migrate_all_tenants.py upgrade

# Restart service
sudo systemctl restart trackit-api

# Verify
curl http://localhost:5000/health
```

## Environment Configuration for Deployment

### Development (.env)

```
FLASK_ENV=development
DEBUG=True
DATABASE_URL=sqlite:///trackit_dev.db
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:5000,http://localhost:8080
```

### Production (.env.production)

```
FLASK_ENV=production
DEBUG=False
DATABASE_URL_PROD=postgresql://user:password@supabase-project.supabase.co:5432/postgres?sslmode=require
SECRET_KEY=<generate-secure-random-key>
JWT_SECRET_KEY=<generate-secure-random-key>
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
BCRYPT_LOG_ROUNDS=12
RATELIMIT_STORAGE_URL=redis://cache-server:6379
```

## Backup & Recovery

### Automated Backups (PostgreSQL)

```bash
# Schedule daily backups with cron
0 2 * * * pg_dump -h supabase-project.supabase.co -U postgres dbname > /backups/trackit_$(date +\%Y\%m\%d).sql

# Restore from backup
psql -h supabase-project.supabase.co -U postgres dbname < /backups/trackit_20240101.sql
```

### Supabase Backups

Supabase provides automated daily backups via dashboard. To restore:

1. Go to Supabase Dashboard
2. Navigate to Backups
3. Select desired backup
4. Click "Restore"

## Health Checks & Monitoring

### Application Health Check

```bash
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "database": "up"
  },
  "system": {
    "disk_free_gb": 450.5,
    "disk_total_gb": 500
  }
}
```

### Database Connectivity Test

```bash
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.session.execute('SELECT 1')
    print('Database connection OK')
"
```

### Migration Status Check

```bash
python scripts/check_migration_status.py

# Shows which migrations are applied per tenant
```

## Troubleshooting Deployments

### Issue: Migration Fails on Production

```bash
# Check migration status
python scripts/check_migration_status.py

# Check database connectivity
python scripts/test_db_connection.py

# View migration history
psql -c "SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 10"
```

### Issue: Tenant Schema Not Created

```bash
# Manually create schema
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from app.tenant_migrations import initialize_tenant_schema
    initialize_tenant_schema(1)  # org_id = 1
"
```

### Issue: Database Lock During Migration

```bash
# Check active connections
psql -c "SELECT * FROM pg_stat_activity WHERE state='active'"

# Kill specific session
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <pid>;
```

## Rollback Procedures

### Code Rollback

```bash
# Revert to previous version
git checkout <previous-commit>
git push origin main

# Restart service
sudo systemctl restart trackit-api
```

### Database Rollback (PostgreSQL)

```bash
# List applied migrations
python scripts/check_migration_status.py

# Downgrade specific tenant
python scripts/migrate_all_tenants.py downgrade --org-id=1

# Or rollback all tenants
python scripts/migrate_all_tenants.py downgrade
```

## Performance Optimization

### Database Indexing

Migrations automatically create necessary indexes. Verify:

```bash
psql -c "SELECT * FROM pg_indexes WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
```

### Query Optimization

- Ensure CORS_ORIGINS is tightly scoped
- Enable query logging in development
- Use database query analyzer: `EXPLAIN ANALYZE <query>`

## Monitoring & Logging

### Application Logs

```bash
# Check Flask logs
tail -f /var/log/trackit/app.log

# Structured logging with ELK stack
# Logs are JSON formatted for easy parsing
```

### Database Logs

```bash
# PostgreSQL slow queries
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();
```

## Additional Resources

- Alembic Documentation: https://alembic.sqlalchemy.org/
- PostgreSQL Multi-tenancy: https://www.postgresql.org/
- Supabase Documentation: https://supabase.com/docs
- Docker Deployment: https://docs.docker.com/
