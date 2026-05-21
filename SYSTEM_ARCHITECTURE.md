# TrackIT System Architecture & Data Models

Visual reference for system workflows, data models, and architecture patterns.

---

## 1. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Internet                                │
└────┬────────────────────────────────────────────────────────────┘
     │
     │ HTTPS + TLS 1.3
     │
┌────▼─────────────────────────────────────────────────────────┐
│                    Load Balancer (nginx)                      │
│  ├─ SSL/TLS termination                                       │
│  ├─ Rate limiting (global)                                    │
│  ├─ Security headers                                          │
│  └─ Request routing                                           │
└────┬─────────────────────────────────────────────────────────┘
     │
     ├─────────────────────┬─────────────────────┐
     │                     │                     │
┌────▼───────┐       ┌────▼───────┐       ┌────▼───────┐
│  Instance 1 │       │  Instance 2 │       │  Instance 3 │
│  :8000     │       │  :8001     │       │  :8002     │
└────┬───────┘       └────┬───────┘       └────┬───────┘
     │                    │                     │
     └────────────────────┬─────────────────────┘
                          │
                   ┌──────▼──────┐
                   │  Shared DB  │
                   │ (Supabase   │
                   │  PostgreSQL)│
                   └─────────────┘
```

### Application Instance (Flask)

```
┌─────────────────────────────────────────────────────────┐
│            Flask Application Instance                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │  Request Middleware Stack                      │   │
│  ├────────────────────────────────────────────────┤   │
│  │ 1. WSGI Application (Gunicorn)                 │   │
│  │ 2. CORSMiddleware (flask-cors)                 │   │
│  │ 3. Limiter (flask-limiter)                     │   │
│  │ 4. Talisman (security headers)                 │   │
│  │ 5. JWT Verification (flask-jwt-extended)      │   │
│  │ 6. Request Context (tenant isolation)          │   │
│  └────────────────────────────────────────────────┘   │
│                        │                               │
│  ┌────────────────────▼─────────────────────────┐    │
│  │  Route Handlers (Blueprints)                 │    │
│  ├────────────────────────────────────────────────┤   │
│  │ • /api/auth                 (Authentication) │    │
│  │ • /api/assets               (Asset CRUD)     │    │
│  │ • /api/inventory            (Stock CRUD)     │    │
│  │ • /api/transfers            (Transfers)      │    │
│  │ • /api/warehouses           (Locations)      │    │
│  │ • /api/users                (User mgmt)      │    │
│  │ • /api/reports              (Reporting)      │    │
│  │ • /api/analytics            (Dashboard)      │    │
│  │ • /api/audit                (Audit logs)     │    │
│  │ • /api/tracking             (QR scanning)    │    │
│  │ • /api/restock              (Alerts)         │    │
│  │ • /api/search               (Full-text)      │    │
│  └────────────────────┬────────────────────────┘    │
│                       │                              │
│  ┌────────────────────▼────────────────────────┐   │
│  │  Service Layer (Business Logic)             │   │
│  ├────────────────────────────────────────────┤   │
│  │ • AssetService                             │   │
│  │ • InventoryService                         │   │
│  │ • TransferService                          │   │
│  │ • RestockService                           │   │
│  │ • ReportingService                         │   │
│  │ • AnalyticsService                         │   │
│  │ • AuditService                             │   │
│  │ • TrackingService                          │   │
│  │ • ExportService                            │   │
│  │ • AnomalyService                           │   │
│  │ • EventBus (pub/sub)                       │   │
│  └────────────────────┬────────────────────────┘   │
│                       │                             │
│  ┌────────────────────▼────────────────────────┐   │
│  │  Repository Layer (Data Access)            │   │
│  ├────────────────────────────────────────────┤   │
│  │ • AssetRepository                          │   │
│  │ • InventoryRepository                      │   │
│  │ • TransferRepository                       │   │
│  │ • (+ ORM: SQLAlchemy models)               │   │
│  │ • Query caching                            │   │
│  │ • Row-level locking                        │   │
│  │ • Transaction retry (3 attempts)           │   │
│  └────────────────────┬────────────────────────┘   │
│                       │                             │
│  ┌────────────────────▼────────────────────────┐   │
│  │  SQLAlchemy ORM + Connections               │   │
│  ├────────────────────────────────────────────┤   │
│  │ • Connection pooling (pool_pre_ping)       │   │
│  │ • Multi-tenant schema routing              │   │
│  │ • Transaction management                   │   │
│  │ • Advisory lock handling                   │   │
│  └────────────────────┬────────────────────────┘   │
│                       │                             │
└───────────────────────┼──────────────────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  PostgreSQL (Supabase)      │
         │  • Multi-tenant schemas     │
         │  • Row-level security       │
         │  • SSL/TLS encryption       │
         │  • Automated backups        │
         │  • Connection pooling       │
         └─────────────────────────────┘
```

---

## 2. Database Schema Architecture

### Public Schema (Shared)

```
public schema (shared across all organizations)
│
├─ organizations
│  ├─ id (PK)
│  ├─ name (unique)
│  ├─ code (unique)
│  ├─ description
│  ├─ created_at
│  └─ updated_at
│
├─ users (auth only - row-level security)
│  ├─ id (PK)
│  ├─ organisation_id (FK)
│  ├─ username
│  ├─ email
│  ├─ password_hash
│  ├─ role (enum)
│  ├─ is_active
│  ├─ failed_login_attempts
│  ├─ locked_until
│  ├─ last_login
│  ├─ created_at
│  └─ updated_at
│
├─ token_blacklist (revoked JWT tokens)
│  ├─ jti (PK)
│  ├─ token_type
│  ├─ user_id (FK)
│  ├─ expires_at
│  └─ created_at
│
└─ schema_migrations (tracks DB migrations per tenant)
   ├─ version (PK)
   └─ applied_at

(SQL-level isolation with RLS policies)
```

### Tenant Schema (tenant_XXXX)

```
tenant_0001 schema (org_id = 1, Acme Corp)
│
├─ ASSETS
│  ├─ assets (core asset records)
│  │  ├─ id (PK)
│  │  ├─ organisation_id
│  │  ├─ asset_code (unique)
│  │  ├─ name
│  │  ├─ type
│  │  ├─ serial_number (unique)
│  │  ├─ department_id (FK)
│  │  ├─ assigned_to
│  │  ├─ status (enum: requested, approved, in_use, maintenance, disposed)
│  │  ├─ condition (enum: new, good, fair, repair, condemned)
│  │  ├─ location
│  │  ├─ warehouse_id (FK) [optional]
│  │  ├─ bin_id (FK) [optional]
│  │  ├─ purchase_date
│  │  ├─ purchase_value
│  │  ├─ useful_life (years)
│  │  ├─ depreciation_method
│  │  ├─ current_value (calculated)
│  │  ├─ qr_code_data
│  │  ├─ created_at
│  │  ├─ updated_at
│  │  └─ Indexes: org_id, dept_id, status, asset_code, serial_number
│  │
│  ├─ asset_audit_logs (change history per asset)
│  │  ├─ id (PK)
│  │  ├─ asset_id (FK)
│  │  ├─ action
│  │  ├─ old_values (JSON)
│  │  ├─ new_values (JSON)
│  │  └─ created_at
│  │
│  └─ asset_conditions (optional enum table)
│     ├─ id (PK)
│     └─ code, description
│
├─ INVENTORY
│  ├─ inventory_items (consumable items)
│  │  ├─ id (PK)
│  │  ├─ organisation_id
│  │  ├─ name
│  │  ├─ sku (unique)
│  │  ├─ description
│  │  ├─ quantity (current stock)
│  │  ├─ reorder_level
│  │  ├─ min_stock
│  │  ├─ unit_price
│  │  ├─ unit (box, piece, pack)
│  │  ├─ is_active
│  │  ├─ created_at
│  │  ├─ updated_at
│  │  └─ Indexes: org_id, sku, is_active, low_stock_query
│  │
│  ├─ stock_movements (IN/OUT log)
│  │  ├─ id (PK)
│  │  ├─ item_id (FK)
│  │  ├─ type (enum: IN, OUT)
│  │  ├─ quantity
│  │  ├─ reference (PO/receipt/etc)
│  │  ├─ notes
│  │  ├─ date
│  │  ├─ created_at
│  │  └─ Indexes: item_id, date, type
│  │
│  └─ restock_alerts (low-stock alerts)
│     ├─ id (PK)
│     ├─ item_id (FK)
│     ├─ organisation_id
│     ├─ status (enum: active, resolved)
│     ├─ urgency (enum: critical, warning)
│     ├─ created_at
│     ├─ resolved_at
│     └─ notes
│
├─ WAREHOUSES & LOCATIONS
│  ├─ warehouses (physical locations)
│  │  ├─ id (PK)
│  │  ├─ organisation_id
│  │  ├─ name
│  │  ├─ location
│  │  ├─ capacity
│  │  ├─ created_at
│  │  └─ updated_at
│  │
│  ├─ warehouse_bins (storage bins)
│  │  ├─ id (PK)
│  │  ├─ warehouse_id (FK)
│  │  ├─ bin_code (unique)
│  │  ├─ location (aisle/row/shelf)
│  │  ├─ capacity
│  │  ├─ is_active
│  │  └─ created_at
│  │
│  └─ warehouse_stock (inventory by warehouse)
│     ├─ id (PK)
│     ├─ item_id (FK)
│     ├─ warehouse_id (FK)
│     ├─ quantity_on_hand
│     ├─ last_counted_at
│     └─ notes
│
├─ DEPARTMENTS
│  ├─ departments
│  │  ├─ id (PK)
│  │  ├─ organisation_id
│  │  ├─ name
│  │  ├─ code
│  │  ├─ description
│  │  ├─ head_id (FK → users) [optional]
│  │  ├─ budget
│  │  ├─ created_at
│  │  └─ updated_at
│  │
│  └─ location_topology (hierarchical organization)
│     ├─ id (PK)
│     ├─ parent_id (self-FK)
│     ├─ name (building/floor/wing)
│     ├─ level (hierarchy)
│     └─ created_at
│
├─ TRANSFERS
│  ├─ transfer_requests
│  │  ├─ id (PK)
│  │  ├─ asset_id (FK)
│  │  ├─ from_department_id (FK)
│  │  ├─ to_department_id (FK)
│  │  ├─ status (enum: requested, approved, dispatched, received, rejected)
│  │  ├─ requested_by_id (FK → users)
│  │  ├─ approved_by_id (FK → users)
│  │  ├─ dispatched_by_id (FK → users)
│  │  ├─ received_by_id (FK → users)
│  │  ├─ requested_at
│  │  ├─ approved_at
│  │  ├─ dispatched_at
│  │  ├─ received_at
│  │  ├─ reason
│  │  ├─ notes
│  │  └─ expected_date
│  │
│  └─ transfer_history (immutable log)
│     ├─ id (PK)
│     ├─ transfer_id (FK)
│     ├─ from_status
│     ├─ to_status
│     ├─ changed_at
│     └─ changed_by_id (FK → users)
│
├─ TRACKING & QR
│  ├─ scan_events (QR code scans)
│  │  ├─ id (PK)
│  │  ├─ asset_id (FK)
│  │  ├─ scan_location (lat/lon or bin_id)
│  │  ├─ timestamp
│  │  ├─ device_id
│  │  ├─ user_id (FK)
│  │  ├─ confidence
│  │  └─ notes
│  │
│  ├─ item_instances (physical item instances)
│  │  ├─ id (PK)
│  │  ├─ item_id (FK)
│  │  ├─ serial_number
│  │  ├─ qr_code_data
│  │  ├─ location_id (FK)
│  │  ├─ status
│  │  ├─ last_scanned_at
│  │  └─ created_at
│  │
│  └─ events (system events for pub/sub)
│     ├─ id (PK)
│     ├─ event_type
│     ├─ entity_type
│     ├─ entity_id
│     ├─ data (JSON)
│     ├─ processed_at
│     └─ created_at
│
├─ AUDIT & COMPLIANCE
│  ├─ audit_logs (general audit trail)
│  │  ├─ id (PK)
│  │  ├─ organisation_id
│  │  ├─ user_id (FK)
│  │  ├─ action
│  │  ├─ entity_type
│  │  ├─ entity_id
│  │  ├─ details (JSON)
│  │  ├─ ip_address
│  │  ├─ created_at
│  │  └─ Indexes: org_id, user_id, entity_type, action, created_at
│  │
│  └─ schema_migrations (tenant-specific)
│     ├─ version (PK)
│     └─ applied_at
│
└─ SUPPLIER & SOURCING
   ├─ suppliers
   │  ├─ id (PK)
   │  ├─ organisation_id
   │  ├─ name
   │  ├─ code
   │  ├─ contact_person
   │  ├─ email
   │  ├─ phone
   │  ├─ address
   │  ├─ payment_terms
   │  ├─ is_active
   │  └─ created_at
   │
   └─ purchase_orders (PO tracking)
      ├─ id (PK)
      ├─ po_number (unique)
      ├─ supplier_id (FK)
      ├─ order_date
      ├─ delivery_date
      ├─ total_amount
      ├─ status (enum: draft, approved, ordered, delivered, cancelled)
      ├─ line_items (JSON)
      └─ created_at
```

---

## 3. Entity Relationship Diagram (ERD)

```
                        ┌─────────────────┐
                        │ Organizations   │
                        ├─────────────────┤
                        │ id              │
                        │ name            │
                        │ code            │
                        └────────┬────────┘
                                 │ 1
                                 │
                ┌────────────────┼────────────────┐
                │                │                │ N
                │ N              │ N              │
        ┌───────▼──────┐  ┌──────▼──────┐  ┌────▼───────┐
        │    Users     │  │  Departments│  │   Assets   │
        ├──────────────┤  ├─────────────┤  ├────────────┤
        │ id           │  │ id          │  │ id         │
        │ org_id (FK)  │  │ org_id (FK) │  │ org_id(FK) │
        │ username     │  │ name        │  │ asset_code │
        │ role         │  │ head_id(FK) │  │ dept_id(FK)│
        │ email        │  │ budget      │  │ status     │
        └──────────────┘  └─────────────┘  │ value      │
                                           └────┬───────┘
                                                │ 1
                                                │ N
                        ┌──────────────────────┘
                        │
                ┌───────▼──────────┐    ┌──────────────────┐
                │ TransferRequests │◄───┤ AssetAuditLogs   │
                ├──────────────────┤    ├──────────────────┤
                │ id               │    │ id               │
                │ asset_id (FK)    │    │ asset_id (FK)    │
                │ from_dept (FK)   │    │ action           │
                │ to_dept (FK)     │    │ old_values       │
                │ status           │    │ new_values       │
                │ requested_by(FK) │    │ created_at       │
                └──────────────────┘    └──────────────────┘
                        │ 1
                        │
        ┌───────────────┴───────────────┐
        │                               │ N
        │ N
        ▼
    ┌──────────────────────┐    ┌─────────────────┐
    │ InventoryItems       │    │ StockMovements  │
    ├──────────────────────┤    ├─────────────────┤
    │ id                   │◄───┤ id              │
    │ org_id (FK)          │ 1  │ item_id (FK)    │
    │ sku                  │    │ type (IN/OUT)   │
    │ name                 │    │ quantity        │
    │ quantity             │    │ date            │
    │ reorder_level        │    │ reference       │
    └──────────┬───────────┘    └─────────────────┘
               │ 1
               │ N
    ┌──────────▼───────────┐    ┌────────────────┐
    │ RestockAlerts        │    │ WarehouseStock │
    ├──────────────────────┤    ├────────────────┤
    │ id                   │    │ id             │
    │ item_id (FK)         │    │ item_id (FK)   │
    │ status               │    │ warehouse_id   │
    │ urgency              │    │ quantity_on    │
    │ created_at           │    │   _hand        │
    └──────────────────────┘    └────────────────┘
                                     │ 1
                                     │ N
                        ┌────────────▼──────────┐
                        │ Warehouses & Bins    │
                        ├──────────────────────┤
                        │ id, name, location   │
                        │ bins (children)      │
                        └──────────────────────┘
```

---

## 4. Request-Response Sequence Diagram

```
Client                    API                    Service               Database
  │                       │                        │                     │
  │ 1. POST /auth/login   │                        │                     │
  ├──────────────────────►│                        │                     │
  │                       │ 2. Validate input      │                     │
  │                       │ 3. Rate limit check    │                     │
  │                       │─┐                      │                     │
  │                       │ │                      │                     │
  │                       │◄┘                      │                     │
  │                       │ 4. Call login service  │                     │
  │                       ├───────────────────────►│                     │
  │                       │                        │ 5. Query user       │
  │                       │                        ├────────────────────►│
  │                       │                        │                     │ 6. SELECT users
  │                       │                        │◄────────────────────┤
  │                       │                        │                     │
  │                       │                        │ 7. Verify password  │
  │                       │                        │ 8. Create JWT       │
  │                       │                        │ 9. Log event        │
  │                       │                        │◄─┐                  │
  │                       │                        │  │ (in memory)      │
  │                       │◄───────────────────────┤                     │
  │ 10. 200 + JWT cookies │                        │                     │
  │◄──────────────────────┤                        │                     │
  │                       │                        │                     │
  │ 11. Store JWT locally │                        │                     │
  │ 12. Redirect to assets│                        │                     │
  │                       │                        │                     │
  │ 13. GET /api/assets   │                        │                     │
  │ with JWT in cookie    │                        │                     │
  ├──────────────────────►│                        │                     │
  │                       │ 14. Verify JWT        │                     │
  │                       │ 15. Extract org_id    │                     │
  │                       │ 16. SET search_path   │                     │
  │                       │────────────────────────────────────────────►│
  │                       │                        │                     │ 17. SET search_path TO tenant_0001
  │                       │                        │                     │◄──────────────────────────────────
  │                       │ 18. Call asset service │                     │
  │                       ├───────────────────────►│                     │
  │                       │                        │ 19. Query assets    │
  │                       │                        ├────────────────────►│
  │                       │                        │                     │ 20. SELECT FROM tenant_0001.assets
  │                       │                        │◄────────────────────┤
  │                       │                        │ 21. Calculate depreciation
  │                       │                        │ 22. Serialize to JSON
  │                       │◄───────────────────────┤                     │
  │ 23. 200 + Assets JSON │                        │                     │
  │◄──────────────────────┤                        │                     │
  │                       │                        │                     │
  │ 24. Parse & render    │                        │                     │
  │     asset list UI     │                        │                     │
```

---

## 5. Data State Transitions

### Asset Status State Machine

```
                    ┌──────────┐
                    │REQUESTED │◄─────────────────┐
                    └──────┬───┘                  │
                           │                     │
                    Dept Head                Rejected
                    reviews                 (re-request)
                           │                     │
            ┌──────────────┴──────────────┐     │
            │                             │     │
    ┌───────▼────────┐         ┌─────────▼──┐  │
    │   APPROVED     │         │  REJECTED  │──┘
    └───────┬────────┘         └────────────┘
            │
     Procurement
     in progress
            │
    ┌───────▼────────┐
    │    IN_USE      │◄──────────────┐
    └───────┬────────┘               │
            │                   Repair complete
        Needs                        │
    repair?  │              ┌────────┴─────────┐
            │               │                  │
    ┌───────▼──────┐  ┌────▼──────┐  ┌────────▼────┐
    │  MAINTENANCE │  │  IN_USE   │  │  DISPOSED   │
    └───────┬──────┘  └───────────┘  └─────────────┘
            │           (end of life)  (final state)
         Repair
         complete
            │
            └──────────────────────────────────┘
```

### Transfer Status State Machine

```
             ┌──────────┐
             │REQUESTED │
             └─────┬────┘
                   │
          Dept Head review
                   │
        ┌──────────┴──────────┐
        │                     │
    Rejected              Approved
        │                     │
    ┌───▼──────┐          ┌───▼──────┐
    │REJECTED  │          │APPROVED  │
    └──────────┘          └───┬──────┘
                               │
                        Asset shipped
                               │
                          ┌───▼───────┐
                          │DISPATCHED │
                          └───┬───────┘
                               │
                        Asset received &
                        verified (scan QR)
                               │
                          ┌───▼────────┐
                          │ RECEIVED   │
                          └────────────┘
                          (final state)
```

### Inventory Stock Status

```
─ HEALTHY ───────────────────────────── BELOW THRESHOLD ───
                                              │
                                         ┌────▼───────┐
                                         │ WARNING    │
                                         │ (qty <     │
                                         │reorder_lvl)│
                                         └────┬───────┘
                                              │
                                        ┌─────▼──────┐
                                        │ CRITICAL   │
                                        │(qty <25%   │
                                        │reorder_lvl)│
                                        └─────┬──────┘
                                              │
         NEW STOCK                      ┌─────▼──────┐
         RECEIVED ◄──────────────────────┤ ORDER NOW!│
              │                          └────────────┘
              │
         ┌────▼──────────┐
         │ Stock checked │
         │ vs reorder    │
         └────┬──────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    HEALTHY         BELOW
```

---

## 6. Multi-Tenancy Architecture

```
PostgreSQL Instance (Supabase)
│
├─ public schema (shared)
│  ├─ organizations (1 row per org)
│  └─ users (auth only)
│
├─ tenant_0001 (Acme Corp)
│  ├─ assets (Acme's assets only)
│  ├─ inventory_items (Acme's inventory)
│  ├─ transfers (Acme's transfers)
│  ├─ audit_logs (Acme's audit trail)
│  └─ ... (all business tables)
│     └─ All rows must have organisation_id = 1
│
├─ tenant_0002 (MfgInc)
│  ├─ assets (MfgInc's assets only)
│  ├─ inventory_items (MfgInc's inventory)
│  └─ ... (isolated completely from 0001)
│     └─ All rows must have organisation_id = 2
│
└─ tenant_XXXX
   └─ ... (one schema per organization)

Isolation mechanisms:
1. SQL-level: SET search_path TO tenant_0001
2. Data-level: organisation_id filter on all queries
3. JWT-level: organisation_id in claims
4. App-level: @before_request sets tenant context
5. Row-level: PostgreSQL RLS policies (optional)
```

---

## 7. Security & Permission Flow

```
User Request
    │
    ├─ 1. HTTPS/TLS only (transport security)
    │
    ├─ 2. Rate limiting (limiter)
    │   └─ 200/day, 50/hour per IP
    │
    ├─ 3. CSRF token check (for state-changing ops)
    │
    ├─ 4. JWT verification
    │   ├─ Signature check (secret key)
    │   ├─ Expiry check
    │   └─ Blacklist check (revoked tokens)
    │
    ├─ 5. Extract JWT claims
    │   ├─ identity (user_id)
    │   ├─ organisation_id (tenant)
    │   └─ role (admin|staff|etc)
    │
    ├─ 6. Set tenant context
    │   ├─ SET search_path TO tenant_0001
    │   └─ organisation_id in request context
    │
    ├─ 7. Route handler permission check
    │   ├─ Load user from DB
    │   ├─ Get user.role
    │   ├─ Check has_permission(action, resource)
    │   └─ If denied: 403 Forbidden
    │
    ├─ 8. Row-level filtering
    │   ├─ Query auto-filters: WHERE organisation_id = tenant_id
    │   └─ All results belong to tenant only
    │
    ├─ 9. Business logic validation
    │   ├─ Asset exists? Belongs to this org?
    │   ├─ User can edit? (status checks)
    │   └─ Data constraints satisfied?
    │
    ├─ 10. Database transaction
    │   ├─ Row-level locks (FOR UPDATE)
    │   ├─ Atomic operation
    │   └─ Rollback on error
    │
    └─ 11. Audit log
        ├─ Log action, user, timestamp
        ├─ Capture before/after values
        └─ Store in audit_logs (immutable)

Response
    ├─ Security headers (CSP, HSTS, etc)
    ├─ JSON envelope (success flag)
    ├─ Correct HTTP status code
    └─ Secure cookies (HTTP-only, Secure, SameSite)
```

---

## 8. Deployment Architecture

```
GitHub
   │
   ├─ Source code
   ├─ CI/CD workflow (GitHub Actions)
   └─ Automatic on push to main
         │
         ├─ Stage 1: Test
         │  ├─ Run pytest
         │  ├─ Run pylint
         │  ├─ Generate coverage
         │  └─ Upload to codecov
         │
         ├─ Stage 2: Build
         │  ├─ Build Docker image
         │  ├─ Tag with SHA + semver
         │  └─ Push to GHCR
         │
         └─ Stage 3: Deploy
            ├─ SSH to prod server
            ├─ Pull latest image
            ├─ Run migrations
            ├─ Restart containers
            └─ Health check

Production Infrastructure
   │
   ├─ Nginx (Load balancer)
   │  ├─ SSL/TLS termination
   │  ├─ Rate limiting
   │  └─ Route to Flask instances
   │
   ├─ Flask Instances (3+)
   │  ├─ Gunicorn workers
   │  ├─ Auto-scaling
   │  └─ Health checks
   │
   └─ Supabase PostgreSQL
      ├─ Multi-tenant schemas
      ├─ Automated backups (daily)
      ├─ SSL/TLS encryption
      ├─ Connection pooling
      └─ Read replicas (optional)
```

---

## References

See `WORKFLOW_PROCESSES.md` for complete process details.
