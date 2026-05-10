# TrackIT Developer Quick Reference

## Getting Started (5 minutes)

```bash
# 1. Initialize project structure
python init_project.py

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed test database
python db_seed.py

# 4. Run development server
python run.py

# Open: http://localhost:5000
```

## File Organization

```
trackit/
├── app/                        # Main Flask application
│   ├── __init__.py            # App factory (create_app)
│   ├── models/                # Database models
│   │   ├── user.py            # User + permissions
│   │   ├── organization.py    # Org + Department
│   │   ├── asset.py           # Asset + audit logs
│   │   └── inventory.py       # Inventory + stock movements
│   ├── blueprints/            # API routes (by feature)
│   ├── templates/             # Jinja2 HTML
│   └── static/                # CSS, JS, images
├── config.py                  # Configuration profiles
├── run.py                      # Entry point
├── db_seed.py                 # Test data
└── requirements.txt           # Dependencies
```

## Database Models Summary

| Model | Purpose | Key Fields |
|-------|---------|-----------|
| **Organization** | Tenant isolation | id, name, code, is_active |
| **User** | Authentication | username, email, password_hash, role, organisation_id |
| **Department** | Asset grouping | code, head_id, organisation_id |
| **Asset** | Fixed assets | asset_code, status, condition, current_value, organisation_id |
| **InventoryItem** | Stock | sku, quantity, reorder_level, organisation_id |
| **StockMovement** | Audit trail | type(IN/OUT), quantity, item_id |
| **AuditLog** | System audit | action, entity_type, organisation_id |

## Model Methods You Can Use

### Asset
```python
asset.can_transition_to('in_use')      # Validate status change
asset.update_current_value()            # Calculate depreciation
```

### InventoryItem
```python
item.add_stock(100)                     # Adds stock + creates movement
item.remove_stock(10)                   # Removes stock + creates movement
item.is_low_stock()                     # Check if below reorder level
```

### User
```python
user.set_password('newpassword')        # Hash and set password
user.check_password('password')         # Verify password
user.has_permission('approve')          # Check permission
```

## Enums

### Asset Status
- `requested` → `approved` → `in_use` ⇄ `maintenance` → `disposed` (terminal)

### Asset Condition
- `new` | `good` | `fair` | `repair` | `condemned`

### User Roles & Permissions
| Role | Create | Edit | Delete | Approve | View |
|------|--------|------|--------|---------|------|
| admin | ✓ | ✓ | ✓ | ✓ | ✓ |
| staff | ✓ | ✓ | ✗ | ✗ | ✓ |
| viewer | ✗ | ✗ | ✗ | ✗ | ✓ |
| auditor | ✗ | ✗ | ✗ | ✗ | ✓ |
| dept_head | ✗ | ✗ | ✗ | ✓ | ✓ |
| store_manager | ✓ | ✓ | ✗ | ✗ | ✓ |

## Test Credentials

```
Organization: TechCorp
  - Admin: admin / admin123
  - Staff: staff1 / staff123
  - Dept Head: depthead / head123

Organization: Manufacturing Inc
  - Store Manager: storemmgr / store123
```

## Common Tasks

### Creating an Asset
```python
from app import create_app, db
from app.models.asset import Asset

app = create_app()
with app.app_context():
    asset = Asset(
        organisation_id=1,
        asset_code='TECH-001',
        name='Laptop',
        type='IT',
        department_id=1,
        purchase_date=date(2024, 1, 1),
        purchase_value=80000,
        useful_life=5,
        current_value=80000
    )
    db.session.add(asset)
    db.session.commit()
```

### Updating Stock
```python
item = InventoryItem.query.get(1)
item.add_stock(100)        # Stock in
item.remove_stock(10)      # Stock out
db.session.commit()
```

### Checking Permissions
```python
if user.has_permission('approve'):
    # Approver route
    pass
```

### Changing Asset Status
```python
if asset.can_transition_to('in_use'):
    asset.status = 'in_use'
    db.session.commit()
```

## Environment Variables

```env
FLASK_ENV=development          # development | production | testing
FLASK_APP=run.py
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///trackit.db
DATABASE_URL_PROD=postgresql://user:pass@host:5432/trackit
DEBUG=True
```

## Multi-Tenant Safety

⚠️ **CRITICAL**: All queries MUST filter by `organisation_id`

```python
# WRONG - exposes cross-tenant data!
assets = Asset.query.all()

# CORRECT - filters by organization
assets = Asset.query.filter_by(organisation_id=org_id).all()
```

## Depreciation Formula

```
current_value = purchase_value - (purchase_value / useful_life) × years_used
minimum: 0
```

## Phase Progress

- [x] Phase 1: Project Setup & Database Models
- [ ] Phase 2: Authentication & Multi-Tenancy  
- [ ] Phase 3: Core Business Logic
- [ ] Phase 4-6: API Endpoints
- [ ] Phase 7: QR Code & Reporting
- [ ] Phase 8: Frontend Templates
- [ ] Phase 9-12: Testing, Deployment, Docs

## Useful Commands

```bash
# Interactive Flask shell
flask shell

# Run tests (when added)
pytest

# Format code
black app/

# Lint
flake8 app/

# Run specific seed
python db_seed.py

# Generate migrations (Phase 2)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Links & References

- Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/
- Flask-Login: https://flask-login.palletsprojects.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- SRS Spec: See PHASE_1_SUMMARY.md

## Troubleshooting

**Database locked error?**
- Delete `.db` files and re-run `python db_seed.py`

**Module not found?**
- Run `python init_project.py` first
- Check `app/models/` contains all .py files

**Import errors?**
- Ensure `pip install -r requirements.txt` completed
- Virtual environment activated?

**Port 5000 already in use?**
- Change in run.py: `app.run(debug=True, port=5001)`
