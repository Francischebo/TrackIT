# TrackIT - Asset & Inventory Management System

A multi-tenant web application for managing fixed assets and consumable inventory.

## Quick Start

### 1. Initialize Project
```bash
python init_project.py
```

This creates the full directory structure and all model files.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Database
```bash
python db_seed.py
```

Creates test organizations, users, departments, assets, and inventory items.

### 4. Run Development Server
```bash
python run.py
```

Access at http://localhost:5000

## Project Structure

```
trackit/
├── app/                          # Flask application
│   ├── __init__.py              # App factory
│   ├── models/                  # Database models
│   │   ├── user.py             # User model
│   │   ├── organization.py      # Org & Department models
│   │   ├── asset.py            # Asset models
│   │   └── inventory.py        # Inventory models
│   ├── blueprints/             # API routes (to be created)
│   ├── templates/              # HTML templates (to be created)
│   └── static/                 # CSS/JS/images (to be created)
├── config.py                    # Configuration
├── run.py                       # Application entry point
├── db_seed.py                   # Database seeder
├── init_project.py              # Project initializer
├── requirements.txt             # Python dependencies
└── README.md                    # This file

```

## Models Overview

### Organization
- Multi-tenant isolation (all queries filter by `organisation_id`)
- Users, departments, assets, inventory items belong to organizations

### User
- Authentication with Flask-Login
- Roles: admin, staff, viewer, auditor, dept_head, store_manager
- Role-based permissions built-in

### Asset
- Status lifecycle: requested → approved → in_use → (maintenance|disposed)
- Straight-line depreciation calculation
- Audit logging for all changes
- QR code support

### InventoryItem
- Stock tracking with reorder levels
- Stock movements logged (IN/OUT)
- Quantity validation

## Test Credentials

After running `db_seed.py`:

- **Admin**: admin / admin123 (TechCorp)
- **Staff**: staff1 / staff123 (TechCorp)
- **Dept Head**: depthead / head123 (TechCorp)
- **Store Manager**: storemmgr / store123 (Manufacturing Inc)

## Environment Variables

Copy `.env.example` to `.env` and update:

```
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///trackit.db (dev)
DATABASE_URL_PROD=postgresql://... (production)
DEBUG=True
```

## Database Support

- **Development**: SQLite (lightweight, no setup required)
- **Production**: PostgreSQL (scalable, multi-user)

Switch by updating `DATABASE_URL` in `.env`

## Next Steps

- Phase 2: Authentication & Multi-Tenancy
- Phase 3: Core Business Logic
- Phase 4-6: API Endpoints
- Phase 7: QR Code & Reporting
- Phase 8: Frontend Templates

