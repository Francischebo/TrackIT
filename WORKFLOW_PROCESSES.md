# System Workflow Processes - TrackIT

Complete documentation of all business workflows, data flows, and operational processes in the TrackIT Assets & Inventory Management System.

---

## Table of Contents

1. [Organization Onboarding Workflow](#organization-onboarding)
2. [User Management Workflow](#user-management)
3. [Asset Lifecycle Workflow](#asset-lifecycle)
4. [Inventory Management Workflow](#inventory-management)
5. [Stock Movement Workflow](#stock-movement)
6. [Asset Transfer Workflow](#asset-transfer)
7. [Restock & Alert Workflow](#restock-alert)
8. [QR Code & Tracking Workflow](#qr-tracking)
9. [Reporting & Analytics Workflow](#reporting-analytics)
10. [Audit & Compliance Workflow](#audit-compliance)
11. [Data Flow Architecture](#data-flow-architecture)
12. [Error Handling & Recovery](#error-recovery)

---

## 1. Organization Onboarding Workflow {#organization-onboarding}

### Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Client (Frontend)                                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ POST /api/auth/register-org
                       │ {org_name, org_code, admin_credentials}
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Backend - Auth Handler                                  │
├─────────────────────────────────────────────────────────┤
│ 1. Validate input (schema, length, format)             │
│ 2. Check uniqueness:                                    │
│    - org_code not already registered                   │
│    - org_name not taken                                │
│    - admin_email not used                              │
│ 3. Create Organization record (public schema)          │
│ 4. Create Tenant Schema (tenant_XXXX)                 │
│    ├─ CREATE SCHEMA IF NOT EXISTS                     │
│    ├─ Acquire advisory lock                           │
│    ├─ Create schema_migrations table                  │
│    └─ Run db.create_all() in tenant schema            │
│ 5. Create Admin User (encrypted password)             │
│ 6. Log AUTH event                                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ 201 Created
                       │ {org_id, admin_id}
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Organization Ready                                      │
├─────────────────────────────────────────────────────────┤
│ ✓ Public schema: Organization record                   │
│ ✓ Tenant schema (tenant_0001): Empty tables ready      │
│ ✓ First admin user created                             │
│ ✓ JWT tokens can now be generated                      │
└─────────────────────────────────────────────────────────┘
```

### Step-by-Step Process

1. **Input Validation**
   - Check organization name (2-100 chars, unique)
   - Check organization code (2-20 chars, alphanumeric, unique)
   - Check admin email format and uniqueness
   - Validate password meets complexity requirements

2. **Database Transaction**
   - Begin transaction (rollback on any error)
   - Insert Organization into public.organizations
   - Get auto-assigned organization_id
   - Create tenant schema with advisory lock
   - Initialize all tenant tables
   - Create admin User with bcrypt-hashed password
   - Commit transaction

3. **Audit & Notification**
   - Log ORG_REGISTERED event with metadata
   - Return org_id and admin_id to client
   - Client stores for future login

### Database Changes

```sql
-- Public schema
INSERT INTO organizations (name, code, description) 
VALUES ('Acme Corp', 'ACME', 'Manufacturing');
-- Returns: org_id = 1

-- Tenant schema created
CREATE SCHEMA tenant_0001;

-- Tenant tables
CREATE TABLE tenant_0001.schema_migrations (
  version VARCHAR(50) PRIMARY KEY,
  applied_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE tenant_0001.assets (
  id SERIAL PRIMARY KEY,
  organisation_id INTEGER,
  ...
);

-- Admin user in shared schema
INSERT INTO users (organisation_id, username, email, password_hash, role)
VALUES (1, 'admin', 'admin@acme.com', '$2b$12$...', 'admin');
```

### Error Scenarios

| Error | Cause | Recovery |
|-------|-------|----------|
| Org code exists | Duplicate code | Suggest alternative code |
| Org name exists | Duplicate name | Try different name |
| Email exists | Reuse across orgs | Different email |
| Schema creation failed | DB connection | Rollback, retry |
| Advisory lock timeout | Concurrent creates | Retry with backoff |
| Invalid password | Weak password | Return requirements |

---

## 2. User Management Workflow {#user-management}

### User Creation Process

```
Admin → POST /api/users
├─ {username, email, password, first_name, last_name, role}
│
├─ Validate:
│  ├─ Username unique within org
│  ├─ Email unique within org
│  ├─ Password meets complexity
│  └─ Role is valid (admin|staff|viewer|auditor|dept_head|store_manager)
│
├─ Create User record:
│  ├─ Hash password (bcrypt, 12 rounds)
│  ├─ Set is_active = true
│  ├─ Set created_at = now()
│  └─ Store in tenant schema
│
├─ Create AuditLog:
│  ├─ action = USER_CREATED
│  ├─ entity = User
│  ├─ details = {username, role, email}
│  └─ user_id = admin_id
│
└─ Return: {id, username, email, role, organisation_id}
```

### User Login Process

```
Client → POST /api/auth/login
├─ {email, password}
│
├─ Find user by email
│  └─ If not found → 401 Unauthorized
│
├─ Check if active
│  └─ If not → 401 Unauthorized
│
├─ Check account lock status
│  ├─ If locked_until > now() → 401 + retry message
│  └─ If locked_until < now() → Clear lock
│
├─ Verify password
│  ├─ If match:
│  │  ├─ Reset failed_login_attempts = 0
│  │  ├─ Reset locked_until = NULL
│  │  ├─ Set last_login = now()
│  │  └─ Create JWT tokens
│  │
│  └─ If no match:
│     ├─ Increment failed_login_attempts
│     ├─ If attempts >= 5:
│     │  ├─ Set locked_until = now() + 15 min
│     │  ├─ Reset failed_login_attempts = 0
│     │  └─ Return 401 + "Account locked"
│     └─ Return 401 + "Invalid credentials"
│
├─ Generate tokens:
│  ├─ Access token (1 hour expiry)
│  │  └─ Claims: {identity, organisation_id, role, username, jti}
│  │
│  └─ Refresh token (30 days expiry)
│     └─ Claims: {identity, jti}
│
├─ Set secure cookies:
│  ├─ access_token_cookie (HTTP-only, Secure, SameSite=Lax)
│  ├─ refresh_token_cookie (HTTP-only, Secure, SameSite=Lax)
│  └─ csrf_access_token (CSRF protection)
│
├─ Log authentication:
│  ├─ action = USER_LOGIN
│  ├─ user_id = user.id
│  ├─ details = {ip_address, user_agent}
│  └─ timestamp = now()
│
└─ Return: {user: {...}, message: "Login successful"}
```

### User Role & Permission Model

```
Role               | Assets | Inventory | Transfers | Approval | Admin
──────────────────┼────────┼───────────┼───────────┼──────────┼──────
admin              | CRUD   | CRUD      | CRUD      | Full     | Full
store_manager      | CRUD   | CRUD      | CRUD      | View     | View
staff              | CR*    | R+Edit    | Create    | —        | —
dept_head          | View   | View      | Approve   | Full     | —
viewer             | View   | View      | View      | —        | —
auditor            | View   | View      | View      | —        | Full
```

### Logout Process

```
Client → POST /api/auth/logout
├─ (requires valid JWT)
│
├─ Extract JTI from token
│  └─ jti = unique token identifier
│
├─ Add to TokenBlacklist:
│  ├─ INSERT INTO token_blacklist (jti, token_type, user_id, expires_at)
│  └─ Prevents token reuse
│
├─ Log event:
│  ├─ action = USER_LOGOUT
│  ├─ user_id = identity
│  └─ details = {token_issued_at, token_expires_at}
│
├─ Unset cookies:
│  ├─ access_token_cookie = null
│  ├─ refresh_token_cookie = null
│  └─ csrf_access_token = null
│
└─ Return: {message: "Logout successful"}
```

---

## 3. Asset Lifecycle Workflow {#asset-lifecycle}

### Asset Status Lifecycle

```
                    ┌─────────────┐
                    │  REQUESTED  │◄─── Staff creates asset request
                    └──────┬──────┘
                           │
                    Dept Head reviews
                           │
            ┌──────────────┴──────────────┐
            │                             │
    ┌───────▼────────┐        ┌──────────▼───────┐
    │    APPROVED    │        │    REJECTED      │
    └───────┬────────┘        └──────────┬───────┘
            │                            │
     Asset procured            Can re-request or
            │                  abandon request
    ┌───────▼────────┐
    │    IN_USE      │
    └───────┬────────┘
            │
    ┌───────┴────────┐
    │                │
    │         Needs maintenance/
    │         repair?
    │         │
    │    ┌────▼─────────┐
    │    │  MAINTENANCE │
    │    └────┬─────────┘
    │         │
    │         │ Repair complete
    │    ┌────▼─────────┐
    │    │  IN_USE      │
    │    └──────────────┘
    │
    │ End of life?
    ▼
┌─────────────┐
│  DISPOSED   │ (Final state)
└─────────────┘
```

### Asset Creation Process

```
POST /api/assets
├─ Payload:
│  ├─ asset_code (unique within org)
│  ├─ name
│  ├─ type (IT, Furniture, Equipment, etc.)
│  ├─ serial_number (unique within org)
│  ├─ department_id
│  ├─ assigned_to
│  ├─ purchase_date
│  ├─ purchase_value
│  ├─ useful_life (years)
│  └─ location
│
├─ Validation:
│  ├─ asset_code unique
│  ├─ serial_number unique
│  ├─ purchase_value > 0
│  ├─ useful_life > 0
│  ├─ department exists
│  └─ User has permission (staff+)
│
├─ Create Asset:
│  ├─ Status = REQUESTED
│  ├─ Condition = NEW
│  ├─ Calculate initial depreciation
│  ├─ current_value = purchase_value
│  ├─ created_at = now()
│  └─ Store in tenant schema
│
├─ Create Audit Log:
│  ├─ action = ASSET_CREATED
│  ├─ old_values = NULL
│  └─ new_values = {all asset fields}
│
└─ Return: {asset_id, status: REQUESTED, ...}
```

### Asset Approval Process

```
POST /api/assets/{id}/approve
├─ (requires dept_head or admin role)
│
├─ Load asset
│  └─ Check status = REQUESTED
│
├─ Update asset:
│  ├─ status = APPROVED
│  ├─ approved_at = now()
│  └─ approved_by_id = current_user.id
│
├─ Audit log:
│  ├─ action = ASSET_APPROVED
│  ├─ old_values = {status: REQUESTED}
│  └─ new_values = {status: APPROVED}
│
└─ Return: {asset_id, status: APPROVED, ...}
```

### Depreciation Calculation

```
Annual Depreciation = Purchase Value / Useful Life
Current Value = Purchase Value - (Annual Depreciation × Years Used)

Example:
├─ Purchase Value: $10,000
├─ Useful Life: 5 years
├─ Annual Depreciation: $2,000/year
├─ After 2 years: Current Value = $10,000 - ($2,000 × 2) = $6,000
└─ After 5 years: Current Value = $0 (fully depreciated)

Runs automatically:
├─ On asset creation (calculate_depreciation_details)
├─ On asset view (update_current_value)
└─ On reports (asset valuation)
```

---

## 4. Inventory Management Workflow {#inventory-management}

### Inventory Item Creation

```
POST /api/inventory
├─ Payload:
│  ├─ name (e.g., "Office Paper A4")
│  ├─ sku (unique within org)
│  ├─ description
│  ├─ quantity (initial stock)
│  ├─ reorder_level (alert threshold)
│  ├─ unit_price
│  └─ unit (box, piece, pack, etc.)
│
├─ Validation:
│  ├─ SKU unique within org
│  ├─ quantity >= 0
│  ├─ reorder_level >= 0
│  ├─ unit_price > 0
│  └─ User has permission (staff+)
│
├─ Create InventoryItem:
│  ├─ Store in tenant schema
│  ├─ is_active = true
│  ├─ created_at = now()
│  └─ updated_at = now()
│
├─ Trigger ReStock Service:
│  ├─ Evaluate stock health
│  ├─ Create RestockAlert if quantity < reorder_level
│  └─ Determine urgency (critical, warning, ok)
│
└─ Return: {item_id, sku, quantity, ...}
```

### Stock Health Evaluation

```
RestockService.evaluate_stock_health(item_id)
├─ Load item
├─ Compare quantity vs reorder_level
│
├─ If quantity < reorder_level:
│  ├─ Create RestockAlert
│  ├─ urgency = 'critical' (if qty < 50% of reorder_level)
│  ├─ urgency = 'warning' (if qty < reorder_level)
│  └─ Log alert
│
├─ If quantity >= reorder_level:
│  ├─ Clear any existing alerts
│  └─ status = 'healthy'
│
└─ Update item status & audit log
```

### Low Stock Alert System

```
GET /api/inventory/low-stock
├─ Query RestockAlert table
│  ├─ WHERE organisation_id = current_org
│  ├─ AND status = 'active'
│  └─ ORDER BY urgency DESC, created_at ASC
│
├─ Return alerts with:
│  ├─ item_id, sku, name
│  ├─ current_quantity
│  ├─ reorder_level
│  ├─ unit_price
│  ├─ estimated_cost_to_reorder
│  ├─ urgency
│  └─ last_stock_in_date
│
└─ Frontend displays:
   ├─ Critical (red) - order immediately
   ├─ Warning (yellow) - order soon
   └─ Info (blue) - normal
```

---

## 5. Stock Movement Workflow {#stock-movement}

### Add Stock (Receiving)

```
POST /api/inventory/{id}/stock
├─ Payload:
│  ├─ quantity (must be > 0)
│  ├─ warehouse_id (optional)
│  ├─ reference (PO number, receipt number)
│  ├─ notes
│  └─ date (defaults to now())
│
├─ Validation:
│  ├─ quantity > 0
│  ├─ Item exists
│  ├─ Warehouse exists (if provided)
│  └─ User has permission
│
├─ Database Transaction:
│  ├─ WITH ROW LOCK:
│  │  ├─ Load InventoryItem with FOR UPDATE
│  │  ├─ item.quantity += quantity
│  │
│  │  ├─ If warehouse_id provided:
│  │  │  ├─ Load WarehouseStock with FOR UPDATE
│  │  │  ├─ If not exists: Create new
│  │  │  └─ warehouse_stock.quantity_on_hand += quantity
│  │
│  │  └─ Create StockMovement record:
│  │     ├─ type = 'IN'
│  │     ├─ quantity = quantity
│  │     ├─ reference = reference
│  │     ├─ notes = notes
│  │     ├─ date = date
│  │     └─ item_id = item.id
│  │
│  └─ Trigger RestockService.evaluate_stock_health()
│
├─ Audit Log:
│  ├─ action = STOCK_RECEIVED
│  ├─ quantity = quantity
│  └─ details = {reference, warehouse_id}
│
└─ Return: {item_id, new_quantity, movement_id, ...}
```

### Remove Stock (Issue/Consumption)

```
POST /api/inventory/{id}/remove-stock
├─ Payload:
│  ├─ quantity (must be > 0, <= available)
│  ├─ warehouse_id (optional - specific location)
│  ├─ reference (request #, issue #)
│  └─ notes
│
├─ Validation:
│  ├─ quantity > 0
│  ├─ Item exists
│  ├─ total_quantity >= quantity
│  └─ If warehouse_id: warehouse_quantity >= quantity
│
├─ Database Transaction:
│  ├─ WITH ROW LOCK:
│  │  ├─ Load InventoryItem with FOR UPDATE
│  │  ├─ Check: item.quantity >= quantity
│  │  │  └─ Throw if insufficient
│  │  │
│  │  ├─ item.quantity -= quantity
│  │
│  │  ├─ If warehouse_id provided:
│  │  │  ├─ Load WarehouseStock with FOR UPDATE
│  │  │  ├─ Check: warehouse_stock.qty >= quantity
│  │  │  │  └─ Throw if insufficient
│  │  │  └─ warehouse_stock.quantity_on_hand -= quantity
│  │
│  │  └─ Create StockMovement record:
│  │     ├─ type = 'OUT'
│  │     ├─ quantity = quantity
│  │     ├─ reference = reference
│  │     └─ notes = notes
│  │
│  └─ Trigger RestockService.evaluate_stock_health()
│
├─ Audit Log:
│  ├─ action = STOCK_ISSUED
│  ├─ quantity = quantity
│  └─ details = {reference, warehouse_id}
│
└─ Return: {item_id, new_quantity, movement_id, ...}
```

### Stock Movement Query

```
GET /api/analytics/export/movement?date_from=&date_to=
├─ Query StockMovement table:
│  ├─ WHERE organisation_id = current_org
│  ├─ AND date BETWEEN date_from AND date_to
│  └─ ORDER BY date DESC
│
├─ Return movements with:
│  ├─ item_id, sku, name
│  ├─ type (IN/OUT)
│  ├─ quantity
│  ├─ reference
│  ├─ notes
│  ├─ date
│  ├─ created_by (user)
│  └─ warehouse_id
│
└─ Export as CSV/Excel
```

---

## 6. Asset Transfer Workflow {#asset-transfer}

### Transfer Request Creation

```
POST /api/transfers/request
├─ Payload:
│  ├─ asset_id
│  ├─ from_department_id (source)
│  ├─ to_department_id (destination)
│  ├─ reason (maintenance, relocation, handover, etc.)
│  ├─ notes
│  └─ expected_date (optional)
│
├─ Validation:
│  ├─ Asset exists and is IN_USE
│  ├─ Source/dest departments exist
│  ├─ Source != destination
│  ├─ Asset not already in transfer
│  └─ User has permission
│
├─ Create TransferRequest:
│  ├─ status = REQUESTED
│  ├─ requested_by_id = current_user.id
│  ├─ requested_at = now()
│  ├─ asset_id, from_dept_id, to_dept_id
│  └─ Store in tenant schema
│
├─ Create Audit Log:
│  ├─ action = TRANSFER_REQUESTED
│  ├─ entity_type = TransferRequest
│  └─ details = {from_dept, to_dept, reason}
│
├─ Notify dept head of source department
│  └─ Email/in-app notification
│
└─ Return: {request_id, status: REQUESTED, ...}
```

### Transfer Approval Flow

```
┌─ REQUESTED (initial state)
│  └─ Dept Head reviews
│
│  POST /api/transfers/requests/{id}/approve
│  ├─ Load request
│  ├─ Check status = REQUESTED
│  ├─ Require dept_head or admin
│  ├─ Update: status = APPROVED, approved_by, approved_at
│  └─ Notify recipient department
│
└─ APPROVED
   │
   │  POST /api/transfers/requests/{id}/dispatch
   │  ├─ Load request
   │  ├─ Check status = APPROVED
   │  ├─ Update asset.location = in-transit
   │  ├─ Update: status = DISPATCHED, dispatched_by, dispatched_at
   │  └─ Generate transfer receipt (if QR enabled)
   │
   └─ DISPATCHED
      │
      │  (Asset physically moved)
      │
      │  POST /api/transfers/requests/{id}/receive
      │  ├─ Load request
      │  ├─ Check status = DISPATCHED
      │  ├─ Scan QR or verify asset
      │  ├─ Verify condition (optional)
      │  ├─ Update asset:
      │  │  ├─ department_id = to_department_id
      │  │  ├─ assigned_to = (new employee)
      │  │  └─ location = (new location)
      │  ├─ Update: status = RECEIVED, received_by, received_at
      │  └─ Log asset movement
      │
      └─ RECEIVED (complete)
```

### Transfer Rejection Flow

```
POST /api/transfers/requests/{id}/reject
├─ Load request
├─ Check status = REQUESTED or APPROVED
├─ Reason field required
│
├─ Update:
│  ├─ status = REJECTED
│  ├─ rejected_by = current_user.id
│  ├─ rejected_at = now()
│  └─ rejection_reason = reason
│
├─ Notify requesting user
│
└─ Asset remains with original department
```

### Bulk Transfer

```
POST /api/transfers/bulk
├─ Payload:
│  └─ transfers: [
│     {asset_id, from_dept_id, to_dept_id, reason},
│     ...
│   ]
│
├─ Transaction:
│  ├─ FOR EACH transfer:
│  │  ├─ Create TransferRequest (as above)
│  │  └─ Add to batch
│  │
│  └─ Commit all or rollback all
│
└─ Return: {successful: N, failed: N, transfers: [...]}
```

---

## 7. Restock & Alert Workflow {#restock-alert}

### Restock Alert Creation & Management

```
RestockService.evaluate_stock_health(item_id)
├─ Load InventoryItem
├─ Current quantity vs reorder_level
│
├─ If quantity < reorder_level:
│  ├─ Check if alert already exists
│  │  ├─ If yes: Update status to 'active'
│  │  └─ If no: Create new alert
│  │
│  ├─ Determine urgency:
│  │  ├─ If quantity < (reorder_level * 0.25): CRITICAL
│  │  └─ Else: WARNING
│  │
│  ├─ Create/Update RestockAlert:
│  │  ├─ item_id
│  │  ├─ organisation_id
│  │  ├─ status = 'active'
│  │  ├─ urgency
│  │  ├─ created_at = now()
│  │  └─ Store in tenant schema
│  │
│  └─ Create AlertEvent (for notifications)
│     ├─ Type: RESTOCK_NEEDED
│     ├─ Severity: CRITICAL|WARNING
│     └─ Recipients: store_manager, admin
│
├─ Else (quantity >= reorder_level):
│  ├─ Clear any active alerts
│  ├─ Update status = 'resolved'
│  └─ resolved_at = now()
│
└─ Update item cache for dashboard
```

### Restock Recommendation Engine

```
GET /api/restock/recommendations/{item_id}
├─ Load item and its history
├─ Analyze:
│  ├─ Average consumption rate (qty/day)
│  ├─ Lead time (days to receive new stock)
│  ├─ Seasonality patterns
│  └─ Historical min/max levels
│
├─ Calculate:
│  ├─ Recommended order quantity
│  │  = Avg daily consumption × (lead_time + buffer_days)
│  │
│  ├─ Optimal reorder level
│  │  = Recommended order quantity / 2
│  │
│  └─ Cost to reorder
│     = Recommended quantity × unit_price
│
└─ Return:
   ├─ item_id, sku, name
   ├─ current_quantity
   ├─ current_reorder_level
   ├─ recommended_quantity
   ├─ recommended_reorder_level
   ├─ estimated_cost
   ├─ avg_consumption_rate
   ├─ lead_time_days
   └─ confidence_score (%)
```

### Threshold Management

```
PUT /api/restock/thresholds
├─ Payload:
│  └─ thresholds: [
│     {item_id, new_reorder_level, new_min_stock},
│     ...
│   ]
│
├─ For each threshold:
│  ├─ Validate item exists
│  ├─ Validate new values > 0
│  │
│  ├─ Update InventoryItem:
│  │  ├─ reorder_level = new_reorder_level
│  │  └─ min_stock = new_min_stock (if applicable)
│  │
│  ├─ Immediately evaluate health
│  │  └─ May trigger/clear alerts
│  │
│  └─ Audit log
│     └─ action = REORDER_LEVEL_UPDATED
│
└─ Return: {successful, failed, items_updated}
```

---

## 8. QR Code & Tracking Workflow {#qr-tracking}

### QR Code Generation

```
GET /api/assets/{id}/qr-sticker
├─ Load asset
├─ Generate QR payload:
│  └─ {
│     "type": "asset",
│     "asset_id": id,
│     "asset_code": "TECH-001",
│     "name": "Dell Laptop",
│     "serial": "DELL-12345",
│     "generated_at": timestamp
│    }
│
├─ Create QR image:
│  ├─ Library: qrcode + Pillow
│  ├─ Format: PNG
│  ├─ Size: 200x200 pixels
│  ├─ Error correction: HIGH (30%)
│  └─ Include asset code as text
│
├─ Cache QR (optional)
│  └─ Store qr_code_data in asset record
│
└─ Return: PNG image file
   └─ Downloadable/printable sticker
```

### Bulk QR Generation

```
GET /api/assets/bulk-qr?department_id=X&status=Y
├─ Query assets matching filters
├─ FOR EACH asset:
│  ├─ Generate QR code
│  └─ Add to PDF/ZIP archive
│
├─ Return downloadable archive:
│  └─ asset_qr_codes.pdf or .zip
     └─ One page per asset (or multiple per page)
```

### QR Scan & Tracking

```
POST /api/tracking/scan
├─ Payload:
│  ├─ qr_data (scanned QR content)
│  ├─ scan_location (GPS lat/lon or warehouse bin)
│  ├─ timestamp
│  └─ device_id (scanner device)
│
├─ Decode QR payload
│  └─ Extract asset_id, asset_code
│
├─ Validate:
│  ├─ Asset exists
│  ├─ Is not disposed
│  └─ Belongs to current org
│
├─ Create ScanEvent:
│  ├─ asset_id, organisation_id
│  ├─ scan_location
│  ├─ timestamp
│  ├─ device_id
│  └─ confidence = 1.0 (QR is definitive)
│
├─ Update Asset (optional):
│  ├─ If location provided: asset.location = scan_location
│  ├─ last_scanned = now()
│  └─ last_scanned_by = current_user.id
│
├─ Detect Anomalies:
│  ├─ Asset scanned in multiple locations same hour?
│  │  → Possible theft/loss
│  │  → Trigger ANOMALY alert
│  │
│  └─ Asset outside expected zone?
│     → GEOFENCE violation
│     → Trigger alert if configured
│
├─ Audit Log:
│  └─ action = ASSET_SCANNED
│
└─ Return: {asset_id, asset_code, name, location, status, condition, assigned_to}
```

### Bin Environment Tracking

```
GET /api/tracking/bin-environment/{bin_id}
├─ Load WarehouseBin
├─ Get bin conditions:
│  ├─ temperature (if sensor)
│  ├─ humidity (if sensor)
│  ├─ light level
│  ├─ access logs (scans)
│  └─ last_inventory_date
│
├─ Check items in bin:
│  ├─ List all InventoryItems
│  ├─ For each: quantity_on_hand
│  └─ Sum total value
│
└─ Return:
   ├─ bin_id, warehouse_id, location
   ├─ items: [{sku, quantity, unit_price, total_value}, ...]
   ├─ environment: {temp, humidity, light}
   ├─ access_log: [{user, scan_time, action}, ...]
   └─ total_value: sum
```

---

## 9. Reporting & Analytics Workflow {#reporting-analytics}

### Dashboard Summary

```
GET /api/analytics/dashboard/summary
├─ Load KPIs:
│  ├─ Total assets (by status)
│  ├─ Total inventory value
│  ├─ Assets in maintenance
│  ├─ Low stock items
│  ├─ Assets due for depreciation
│  └─ Pending transfers
│
├─ Calculate trends:
│  ├─ Assets added (this month)
│  ├─ Assets disposed (this month)
│  ├─ Stock movements (last 30 days)
│  ├─ Reorder frequency
│  └─ Depreciation rate
│
└─ Return:
   ├─ charts: {type, data, labels}
   ├─ metrics: {label, value, trend, change%}
   └─ alerts: [{type, severity, message}, ...]
```

### Asset Register Report

```
GET /api/reports/asset-register
├─ Query filters:
│  ├─ status (REQUESTED, APPROVED, IN_USE, DISPOSED)
│  ├─ department_id
│  ├─ date_range (purchase date)
│  └─ asset_type
│
├─ Build result set:
│  ├─ FOR EACH asset:
│  │  ├─ asset_code, serial_number, name, type
│  │  ├─ purchase_date, purchase_value
│  │  ├─ current_value (depreciated)
│  │  ├─ useful_life, years_used
│  │  ├─ status, condition, location
│  │  ├─ department, assigned_to
│  │  ├─ last_maintenance, next_maintenance
│  │  └─ depreciation_method
│  │
│  └─ Add summary rows
│     ├─ Total assets: N
│     ├─ Total purchase value: $X
│     ├─ Total current value: $X
│     └─ Total depreciation: $X
│
├─ Export formats: CSV, Excel, PDF
│
└─ Include:
   ├─ Report title
   ├─ Generated date/time
   ├─ Organization name
   ├─ Generated by: user
   └─ Certification: "Prepared per IFRS depreciation standards"
```

### Inventory Valuation Report

```
GET /api/reports/inventory-valuation?as_of_date=YYYY-MM-DD
├─ Get inventory snapshot as of date
│  ├─ Current quantities (as of date)
│  └─ Unit prices (as of date or current)
│
├─ Calculate valuation:
│  ├─ Total value = SUM(quantity × unit_price)
│  │
│  ├─ By warehouse:
│  │  ├─ Warehouse A: $X
│  │  ├─ Warehouse B: $Y
│  │  └─ Total: $X + $Y
│  │
│  └─ By category:
│     ├─ Office Supplies: $X
│     ├─ Maintenance: $Y
│     └─ Total: $X + $Y
│
├─ Variance analysis:
│  ├─ Expected vs actual quantities
│  ├─ Shrinkage/damage
│  └─ Missing items
│
└─ Return: PDF/Excel with:
   ├─ Item detail (sku, qty, unit price, total)
   ├─ Subtotals by warehouse
   ├─ Subtotals by category
   ├─ Grand total
   └─ Accounting certification
```

### Depreciation Report

```
GET /api/reports/depreciation?fiscal_year=2024
├─ Load all assets active during year
├─ Calculate depreciation per asset:
│  ├─ Days active in year
│  ├─ Monthly depreciation
│  └─ YTD total
│
├─ Aggregate:
│  ├─ By asset type
│  ├─ By department
│  ├─ By depreciation method
│  └─ Total annual depreciation
│
├─ Generate GL entries (accounting):
│  ├─ DR Depreciation Expense
│  ├─ CR Accumulated Depreciation
│  └─ Amount = total annual depreciation
│
└─ Return:
   ├─ Depreciation schedule
   ├─ Asset detail (code, value, depreciation)
   ├─ Summary by type/department
   ├─ GL entry journal
   └─ Tax calculation (if applicable)
```

### Audit Trail Report

```
GET /api/reports/audit-trail?entity_type=Asset&entity_id=123
├─ Query AuditLog & AssetAuditLog
├─ Filter:
│  ├─ entity_type = Asset|Inventory|Transfer|etc.
│  ├─ entity_id (specific asset/item)
│  ├─ date_range
│  ├─ user_id
│  └─ action (CREATE, UPDATE, DELETE, APPROVE, etc.)
│
├─ Build timeline:
│  ├─ FOR EACH log entry:
│  │  ├─ timestamp
│  │  ├─ user (who)
│  │  ├─ action (what)
│  │  ├─ old_values (before)
│  │  ├─ new_values (after)
│  │  ├─ ip_address
│  │  └─ user_agent
│  │
│  └─ Reconstruct state at each point in time
│
└─ Return:
   ├─ Chronological audit trail
   ├─ Change details
   ├─ User activity
   └─ Compliance evidence
```

---

## 10. Audit & Compliance Workflow {#audit-compliance}

### Audit Logging Architecture

```
Every write operation (CREATE, UPDATE, DELETE) logs:

┌─────────────────────────────────────────────┐
│ User Action (e.g., Update Asset)            │
└────────────────┬────────────────────────────┘
                 │
        ┌────────▼────────┐
        │ Validate input  │
        └────────┬────────┘
                 │
        ┌────────▼────────────────────┐
        │ Execute business logic      │
        │ (Update database record)    │
        └────────┬────────────────────┘
                 │
        ┌────────▼────────────────────┐
        │ Capture old & new values    │
        └────────┬────────────────────┘
                 │
        ┌────────▼─────────────────────────┐
        │ Create AuditLog entry:          │
        │ ├─ action = 'UPDATE'            │
        │ ├─ entity_type = 'Asset'        │
        │ ├─ entity_id = 123              │
        │ ├─ old_values = {...}           │
        │ ├─ new_values = {...}           │
        │ ├─ user_id = current_user       │
        │ ├─ ip_address = request.ip      │
        │ ├─ created_at = now()           │
        │ └─ organisation_id = tenant_id  │
        └────────┬─────────────────────────┘
                 │
        ┌────────▼────────┐
        │ Return response │
        └─────────────────┘
```

### Audit Log Queries

```
GET /api/audit/logs
├─ Filter:
│  ├─ entity_type (Asset|Inventory|Transfer|User)
│  ├─ entity_id
│  ├─ user_id
│  ├─ action (CREATE|UPDATE|DELETE|APPROVE|etc.)
│  ├─ date_range
│  └─ search_term
│
├─ Return paginated results:
│  ├─ timestamp, user, action, entity, changes
│  └─ Order by timestamp DESC
│
└─ Search capabilities:
   ├─ Full-text search on details
   ├─ IP address lookup
   ├─ User activity timeline
   └─ Entity change history
```

### Compliance & Export

```
GET /api/audit/export?format=csv&type=full_audit
├─ Generate compliance report:
│  ├─ All transactions during period
│  ├─ User access log
│  ├─ Change history
│  ├─ Permission changes
│  ├─ Data access
│  └─ System events
│
├─ Digital signature (optional):
│  ├─ Hash of report
│  ├─ Timestamp
│  └─ Auditor signature
│
└─ Export as:
   ├─ CSV (for spreadsheet)
   ├─ PDF (for printing/filing)
   └─ ZIP (archive with metadata)
```

---

## 11. Data Flow Architecture {#data-flow-architecture}

### Complete System Data Flow

```
┌─────────────────────┐
│   Frontend Client   │
│   (React/Vue/etc)   │
└──────────┬──────────┘
           │
           │ HTTPS
           │ JWT in cookie
           │
    ┌──────▼────────────────────┐
    │  API Gateway / Load Bal    │
    │  (nginx / AWS ALB)         │
    └──────┬────────────────────┘
           │
    ┌──────▼─────────────────────────────┐
    │   Flask Application                │
    │   ├─ Auth middleware               │
    │   ├─ Verify JWT                    │
    │   ├─ Extract organisation_id       │
    │   └─ Set tenant schema             │
    └──────┬─────────────────────────────┘
           │
    ┌──────▼──────────────────────┐
    │  Tenant Request Context     │
    │  ├─ current_user            │
    │  ├─ current_org             │
    │  ├─ db search_path          │
    │  └─ permissions             │
    └──────┬──────────────────────┘
           │
    ┌──────▼─────────────────────────────┐
    │  Route Handler                     │
    │  ├─ Validate input                 │
    │  ├─ Check permissions              │
    │  ├─ Call service layer             │
    │  └─ Log audit event                │
    └──────┬─────────────────────────────┘
           │
    ┌──────▼──────────────────────────────┐
    │  Service Layer                      │
    │  ├─ Business logic                  │
    │  ├─ Data validation                 │
    │  ├─ Transaction management          │
    │  └─ Event bus / notifications       │
    └──────┬──────────────────────────────┘
           │
    ┌──────▼──────────────────────────────┐
    │  Repository Layer                   │
    │  ├─ Query building                  │
    │  ├─ Row-level locking               │
    │  ├─ Retry logic                     │
    │  └─ Cache management                │
    └──────┬──────────────────────────────┘
           │
    ┌──────▼──────────────────────────────┐
    │  PostgreSQL (Tenant Schemas)        │
    │  ├─ public:                         │
    │  │  ├─ organizations                │
    │  │  ├─ users                        │
    │  │  └─ token_blacklist              │
    │  │                                  │
    │  ├─ tenant_0001:                    │
    │  │  ├─ assets                       │
    │  │  ├─ inventory_items              │
    │  │  ├─ warehouses                   │
    │  │  ├─ transfers                    │
    │  │  ├─ audit_logs                   │
    │  │  └─ ... (25+ tables)             │
    │  │                                  │
    │  ├─ tenant_0002:                    │
    │  │  └─ ... (same structure)         │
    │  │                                  │
    │  └─ tenant_XXXX:                    │
    │     └─ ... (isolated per org)       │
    │                                     │
    └──────────────────────────────────────┘
```

### Request-Response Flow

```
1. Client Sends Request
   ├─ Method: POST /api/assets
   ├─ Headers: {Authorization: Bearer <JWT>, Content-Type: application/json}
   ├─ Body: {asset_code, name, purchase_value, ...}
   └─ Cookies: {access_token_cookie, csrf_token}

2. Middleware Processing
   ├─ Rate limiting check (limiter)
   ├─ JWT verification (jwt_required)
   ├─ Extract claims (organisation_id, role, user_id)
   ├─ Set tenant schema (SET search_path TO tenant_0001)
   └─ Verify CSRF token (if POST/PUT/DELETE)

3. Route Handler
   ├─ Input validation (schema)
   ├─ Permission check (has_permission)
   ├─ Call service method
   └─ Collect audit data

4. Service Layer
   ├─ Business validation
   ├─ Database transaction begin
   ├─ Call repository methods
   ├─ Trigger side effects (restock alerts, etc.)
   └─ Commit transaction

5. Database Operations
   ├─ INSERT into assets (tenant_0001)
   ├─ INSERT into asset_audit_logs
   ├─ INSERT into audit_logs
   └─ COMMIT or ROLLBACK

6. Response Building
   ├─ Serialize asset to JSON
   ├─ Apply after_request normalizer
   ├─ Preserve HTTP status code
   ├─ Add success/status_code envelope
   └─ Set security headers

7. Response Sent to Client
   ├─ Status: 201 Created
   ├─ Headers: {CSP, CORS, HSTS, etc.}
   ├─ Body: {success: true, status_code: 201, data: {...}}
   └─ Cookies: Updated if JWT refreshed

8. Client Processes Response
   ├─ Check success flag
   ├─ Parse data
   ├─ Update UI
   └─ Store asset locally (if needed)
```

---

## 12. Error Handling & Recovery {#error-recovery}

### Error Response Format

```json
{
  "success": false,
  "status_code": 400,
  "error": "Validation failed",
  "details": {
    "asset_code": ["This field is required"],
    "purchase_value": ["Must be a positive number"]
  }
}
```

### Common Error Scenarios

| Error | HTTP | Recovery | Example |
|-------|------|----------|---------|
| Invalid input | 400 | Retry with corrected data | Missing required field |
| Unauthorized | 401 | Redirect to login, refresh token | Expired JWT |
| Forbidden | 403 | Show error, request permissions | Insufficient role |
| Not found | 404 | Check ID, reload list | Asset doesn't exist |
| Conflict | 409 | Use different value | Duplicate asset code |
| Rate limited | 429 | Backoff + retry | Too many requests |
| Server error | 500 | Retry later, contact support | DB connection lost |

### Transaction Rollback Scenarios

```
1. Input Validation Fails
   └─ Rollback: Don't create asset
   └─ Return: 400 Bad Request

2. Permission Check Fails
   └─ Rollback: Don't modify asset
   └─ Return: 403 Forbidden

3. Database Lock Timeout
   └─ Retry with exponential backoff (up to 3 times)
   └─ If still fails: Return 503 Service Unavailable

4. Constraint Violation (e.g., duplicate key)
   └─ Rollback transaction
   └─ Return: 409 Conflict with details

5. Foreign Key Violation
   └─ Rollback transaction
   └─ Return: 400 Bad Request (referenced item not found)

6. Partial Failure (e.g., bulk operation)
   ├─ Rollback entire batch (atomic)
   └─ Return: 400 with error details
```

### Retry Logic

```
@transaction_retry(max_retries=3)
def add_stock(self, quantity):
    """Retry on lock timeout"""
    with db.session.begin_nested():
        # Row-level locking
        item = InventoryItem.query.with_for_update().get(self.id)
        item.quantity += quantity
        db.session.flush()

# Retry algorithm:
# 1st attempt → fails with lock → wait 100ms → retry
# 2nd attempt → fails → wait 200ms → retry
# 3rd attempt → fails → wait 400ms → retry
# 4th attempt → fails → raise exception
```

---

## Workflow Summary Table

| Workflow | Trigger | Key Steps | Audit | Duration |
|----------|---------|-----------|-------|----------|
| Org Onboard | Register-org | Create org → Schema → Admin user | Logged | Seconds |
| Asset Create | POST /assets | Validate → Create → Log | Logged | Immediate |
| Asset Approve | PUT /assets/approve | Validate → Update status | Logged | Immediate |
| Stock IN | POST /add-stock | Validate → Lock → Update → Alert | Logged | Seconds |
| Stock OUT | POST /remove-stock | Validate → Check qty → Lock → Update | Logged | Seconds |
| Transfer Request | POST /transfers | Create → Notify dept | Logged | Immediate |
| Transfer Approve | POST /approve | Validate → Update → Dispatch | Logged | Immediate |
| Transfer Receive | POST /receive | Validate → Update asset → Complete | Logged | Immediate |
| QR Scan | POST /scan | Decode → Validate → Update location | Logged | < 1 sec |
| Report Generate | GET /reports/X | Query → Calculate → Format → Export | Not audited | Seconds |
| Restock Alert | Evaluate health | Check qty → Create/clear alert | Logged | Automatic |

---

## References

- See `FRONTEND_INTEGRATION.md` for client-side workflow implementation
- See `AUTH_ARCHITECTURE.md` for authentication details
- See `MIGRATION_AND_DEPLOYMENT.md` for deployment workflows
- See `VALIDATION_CHECKLIST.md` for testing workflows
