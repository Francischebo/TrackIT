# TrackIT Phase 1 - Visual Overview

## Project Structure (Created)

```
Assets & Inventory TrackIT/
│
├── 📄 Core Application Files
│   ├── run.py                      Entry point - starts Flask app
│   ├── config.py                   Dev/Prod/Test configuration
│   ├── requirements.txt             Python dependencies
│   ├── .env.example                 Environment variables template
│   └── .gitignore                  Git exclusions
│
├── 📁 app/                          Flask Application (created by init_project.py)
│   ├── __init__.py                 App factory + Flask setup
│   ├── models/                     Database models
│   │   ├── user.py                User model (authentication)
│   │   ├── organization.py        Organization & Department models
│   │   ├── asset.py               Asset model + audit + enums
│   │   └── inventory.py           Inventory + stock + audit logs
│   ├── blueprints/                (Ready for Phase 3-4)
│   ├── templates/                 (Ready for Phase 8)
│   └── static/                    (Ready for Phase 8)
│
├── 📊 Database Setup
│   ├── db_seed.py                 Creates test data
│   ├── trackit_dev.db             SQLite database (auto-created)
│   └── migrations/                (Ready for Alembic - Phase 5)
│
├── 🚀 Setup & Utilities
│   ├── init_project.py            Creates directory structure
│   ├── execute_phase1.py           Runs all setup steps
│   ├── verify_setup.py            System checks
│   ├── bootstrap.py               Directory bootstrap
│   └── setup.py                   Alternative setup
│
├── 📚 Documentation
│   ├── README.md                   Quick start guide
│   ├── QUICK_REFERENCE.md         ⭐ Developer reference (START HERE!)
│   ├── PHASE_1_SUMMARY.md         Technical details
│   ├── PHASE_1_DELIVERY.md        Completion report
│   └── PHASE_1_VISUAL.md          This file
│
└── ✅ Status: COMPLETE
```

## Database Models (8 Total)

```
┌─────────────────┐
│  Organization   │  (Multi-tenant root)
│─────────────────│
│ id (PK)         │
│ name            │
│ code            │
│ is_active       │
└────────┬────────┘
         │
    ┌────┴─────────────────────────────┐
    │                                   │
    ▼                                   ▼
┌─────────────┐               ┌──────────────────┐
│   User      │               │  Department      │
├─────────────┤               ├──────────────────┤
│ id          │               │ id               │
│ username    │               │ code (UQ/org)    │
│ email       │               │ name             │
│ role        │               │ head_id (FK)     │
│ org_id (FK) │               │ org_id (FK)      │
│ password    │               └────────┬─────────┘
└─────────────┘                        │
                                      │ manages
                                      ▼
                            ┌──────────────────┐
                            │     Asset        │
                            ├──────────────────┤
                            │ id               │
                            │ asset_code (UQ)  │
                            │ status           │
                            │ current_value    │
                            │ org_id (FK)      │
                            │ dept_id (FK)     │
                            └────────┬─────────┘
                                     │
                                     │ audited
                                     ▼
                            ┌──────────────────┐
                            │ AssetAuditLog    │
                            ├──────────────────┤
                            │ asset_id (FK)    │
                            │ action           │
                            │ old_values (JSON)│
                            │ new_values (JSON)│
                            └──────────────────┘


    ┌─────────────────────┐
    │  InventoryItem      │
    ├─────────────────────┤
    │ id                  │
    │ sku (UQ/org)        │
    │ quantity            │
    │ reorder_level       │
    │ org_id (FK)         │
    └──────────┬──────────┘
               │
               │ tracked by
               ▼
    ┌─────────────────────┐
    │  StockMovement      │
    ├─────────────────────┤
    │ id                  │
    │ type (IN/OUT)       │
    │ quantity            │
    │ item_id (FK)        │
    │ date                │
    └─────────────────────┘

        ┌──────────────────┐
        │   AuditLog       │
        ├──────────────────┤
        │ id               │
        │ action           │
        │ entity_type      │
        │ user_id (FK)     │
        │ org_id (FK)      │
        │ details (JSON)   │
        └──────────────────┘
```

## Data Flow

### Creating an Asset
```
User submits form
    ↓
[Validate input]
    ↓
[Generate asset_code]
    ↓
Create Asset {
  status: "requested"
  condition: "new"
  current_value: calculated
}
    ↓
Save to database
    ↓
Create AuditLog entry
    ↓
Done (Status: requested)
```

### Asset Lifecycle
```
              ┌─────────────────┐
              │   requested     │ ← Initial state
              └────────┬────────┘
                       │ approve
                       ▼
              ┌─────────────────┐
              │   approved      │
              └────────┬────────┘
                       │ put in use
                       ▼
    ┌──────────────────────────────────────┐
    │            in_use                    │
    │ (Normal operating state)             │
    └──────────┬───────────────────────────┘
    ┌──────────┴──────────┐
    │ maintenance needed  │ repair completed
    │                     │
    ▼                     │
┌──────────────────┐     │
│  maintenance     ├─────┘
└──────────────────┘

    ┌──────────────────────────────────────┐
    │ Disposal path                        │
    │ in_use → disposed (terminal state)   │
    │ Cannot transition from disposed      │
    └──────────────────────────────────────┘
```

### Stock Movement
```
InventoryItem (5 units, reorder level 10)
    │
    ├─ add_stock(100)
    │   ↓
    │   Update quantity: 5 + 100 = 105
    │   Create StockMovement(IN, 100)
    │   ✓ Not low stock anymore
    │
    └─ remove_stock(20)
        ↓
        Check: 105 ≥ 20? Yes
        Update quantity: 105 - 20 = 85
        Create StockMovement(OUT, 20)
        ✓ Stock decreased
```

## User Roles & Permissions

```
┌────────────────────────────────────────────────────────┐
│ Role              │ Create │ Edit │ Delete │ Approve   │
├────────────────────────────────────────────────────────┤
│ admin             │   ✓    │  ✓   │   ✓    │    ✓      │
│ staff             │   ✓    │  ✓   │   ✗    │    ✗      │
│ viewer            │   ✗    │  ✗   │   ✗    │    ✗      │
│ auditor           │   ✗    │  ✗   │   ✗    │    ✗      │
│ dept_head         │   ✗    │  ✗   │   ✗    │    ✓      │
│ store_manager     │   ✓    │  ✓   │   ✗    │    ✗      │
└────────────────────────────────────────────────────────┘

Each role has user.has_permission('action') checking built-in
Routes will use @require_permission decorator (Phase 2)
```

## Multi-Tenancy Architecture

```
┌──────────────────────────────────────────────────────┐
│           Organization A (TechCorp)                  │
│                                                      │
│  Dept: IT          Dept: HR                         │
│  Users: 3          Users: 2                         │
│  Assets: 50        Assets: 30                       │
│  Inventory: 40     Inventory: 20                    │
│                                                      │
│  Database records marked with: org_id = 1           │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│      Organization B (Manufacturing Inc)              │
│                                                      │
│  Dept: Operations  Dept: Warehouse                  │
│  Users: 4          Users: 3                         │
│  Assets: 200       Assets: 150                      │
│  Inventory: 500    Inventory: 300                   │
│                                                      │
│  Database records marked with: org_id = 2           │
└──────────────────────────────────────────────────────┘

⚠️  CRITICAL: All queries MUST filter by organisation_id
    to prevent cross-tenant data leakage
    
    WRONG:  Asset.query.all()
    RIGHT:  Asset.query.filter_by(organisation_id=2).all()
```

## Depreciation Calculation

```
Asset: Dell Laptop
├─ purchase_date: 2023-01-01
├─ purchase_value: 100,000
├─ useful_life: 5 years
│
├─ Today (2024-01-01 = 1 year later):
│   annual_depreciation = 100,000 / 5 = 20,000
│   years_used = 1
│   current_value = 100,000 - (20,000 × 1) = 80,000 ✓
│
└─ In 5 years (2028-01-01 = end of life):
    current_value = 100,000 - (20,000 × 5) = 0 ✓
    (Cannot go negative)
```

## Quick Start Flow

```
1. Run init_project.py
   ├─ Creates app/ directory
   ├─ Creates models/ with 6 .py files
   ├─ Creates blueprints/, templates/, static/
   └─ Creates migrations/

2. Run: pip install -r requirements.txt
   └─ Installs Flask, SQLAlchemy, etc.

3. Run db_seed.py
   ├─ Creates trackit_dev.db
   ├─ Creates 8 database tables
   ├─ Inserts 2 organizations
   ├─ Inserts 4+ users
   ├─ Inserts 2 departments
   ├─ Inserts 2 assets
   ├─ Inserts 2 inventory items
   └─ Inserts 3 stock movements

4. Run run.py
   ├─ Starts Flask development server
   └─ Listens on http://localhost:5000

5. Login with:
   username: admin
   password: admin123
```

## Compliance Mapping

```
SRS Section → Implementation → File

3.1 Asset Model
  ✓ All 17 fields        → app/models/asset.py
  ✓ Serial number unique → __table_args__ constraint
  ✓ Status enum          → AssetStatus enum class
  ✓ Condition enum       → AssetCondition enum class

3.2 InventoryItem Model
  ✓ All fields           → app/models/inventory.py
  ✓ Quantity constraint  → CheckConstraint('quantity >= 0')
  ✓ Reorder level        → reorder_level field + is_low_stock()

3.3 StockMovement Model
  ✓ Type IN/OUT          → StockMovementType enum
  ✓ Quantity > 0         → CheckConstraint('quantity > 0')

4.1 State Machine
  ✓ Transitions          → Asset.can_transition_to() method
  ✓ Forbidden paths      → Enforced in method logic

6 Depreciation
  ✓ Straight-line        → Asset.update_current_value()
  ✓ Formula              → current_value = purchase_value - (depreciation × years)
  ✓ Cannot be negative   → max(0, result)

7 Roles & Permissions
  ✓ 6 roles              → role field in User model
  ✓ Permission matrix    → User.has_permission() method
  ✓ All 5 actions        → create, edit, delete, approve, view

9 Validation
  ✓ Unique constraints   → __table_args__ on models
  ✓ Check constraints    → CheckConstraint() on fields
  ✓ Foreign keys         → ForeignKey() relationships

11 Multi-tenancy
  ✓ organisation_id      → On all core models
  ✓ Data isolation       → Ready for query filtering (Phase 2)
```

## Files by Purpose

| Purpose | Files |
|---------|-------|
| 🎯 **START HERE** | QUICK_REFERENCE.md |
| 📖 **Getting Started** | README.md, execute_phase1.py |
| 🔧 **Application** | run.py, config.py, app/__init__.py |
| 📊 **Database** | app/models/*.py, db_seed.py |
| 📚 **Reference** | PHASE_1_SUMMARY.md, PHASE_1_DELIVERY.md |
| ⚙️ **Setup** | init_project.py, requirements.txt |

## What's Ready ✅

- ✅ Full database schema with 8 models
- ✅ All business logic methods (state machine, depreciation, etc.)
- ✅ Role-based permission structure
- ✅ Multi-tenant isolation framework
- ✅ Test data seeder
- ✅ Flask app factory
- ✅ Configuration management
- ✅ Complete documentation

## What's NOT Ready (Later Phases)

- ❌ Routes/APIs (Phase 3-6)
- ❌ Authentication middleware (Phase 2)
- ❌ QR code generation (Phase 7)
- ❌ PDF/Excel reporting (Phase 7)
- ❌ Frontend templates (Phase 8)
- ❌ Mobile responsiveness (Phase 8)

---

**Status**: Phase 1 ✅ COMPLETE - Ready for Phase 2
