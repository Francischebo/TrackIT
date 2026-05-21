# Authentication Architecture (JWT-Only)

## Overview

TrackIT uses **JWT (JSON Web Token)** authentication exclusively. Flask-Login has been removed to eliminate complexity and security gaps from dual-auth mechanisms.

## Architecture

```
┌─────────────────┐
│     Client      │
│   (Browser/    │
│    Mobile)      │
└────────┬────────┘
         │
         │ POST /api/auth/login
         │ {email, password}
         │
    ┌────▼──────────────────┐
    │  Flask Backend        │
    │  ┌────────────────┐   │
    │  │  Auth Handler  │   │
    │  └────────┬───────┘   │
    │           │           │
    │  ┌────────▼───────┐   │
    │  │ Verify Password│   │
    │  │ (bcrypt)       │   │
    │  └────────┬───────┘   │
    │           │           │
    │  ┌────────▼──────────────┐
    │  │ Create Tokens        │
    │  │ • Access (1h)         │
    │  │ • Refresh (30d)       │
    │  └────────┬──────────────┘
    │           │
    └───────────┼──────────────┘
                │
        ┌───────▼────────┐
        │ Set Secure     │
        │ Cookies +      │
        │ CSRF Tokens    │
        └───────┬────────┘
                │
         ┌──────▼──────────┐
         │  Client Storage │
         │  (Cookies /     │
         │   SessionStore) │
         └─────────────────┘
```

## Token Types

### Access Token
- **Payload:**
  - `identity`: User ID
  - `organisation_id`: Tenant ID
  - `role`: User role
  - `username`: Username
  - `exp`: Expiry (1 hour default)
  - `iat`: Issued at
  - `type`: "access"
  - `jti`: JWT ID (for revocation)

- **Storage:** Secure HTTP-only cookie (production) or memory (development)
- **Usage:** Authorization header on each API request

### Refresh Token
- **Payload:**
  - `identity`: User ID
  - `exp`: Expiry (30 days default)
  - `type`: "refresh"
  - `jti`: JWT ID

- **Storage:** Secure HTTP-only cookie (production only)
- **Usage:** Refresh access token when expired

## Token Lifecycle

### 1. Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@org.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "user",
    "email": "user@org.com",
    "role": "staff",
    "organisation_id": 1
  }
}
```

**Cookies Set:**
- `access_token_cookie` (1 hour)
- `refresh_token_cookie` (30 days)
- `csrf_access_token` (CSRF protection)

### 2. Authenticated Requests

```bash
GET /api/assets
Authorization: Bearer <access_token>
Cookie: access_token_cookie=<token>; csrf_access_token=<token>
```

The backend validates:
1. Token signature (JWT secret)
2. Token expiry
3. Token revocation status (blacklist)
4. Tenant/organization isolation

### 3. Token Refresh

When access token expires:

```bash
POST /api/auth/refresh
Cookie: refresh_token_cookie=<token>
```

Response includes new access token (refreshes cookies).

### 4. Logout

```bash
POST /api/auth/logout
Authorization: Bearer <access_token>
```

Adds token to blacklist, unsets cookies.

## Security Features

### Password Security
- **Hashing:** bcrypt with 12 rounds
- **Validation:** 
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

### Account Lockout
- Failed login attempts tracked
- After 5 failed attempts: Account locked for 15 minutes
- Counters reset on successful login

### Token Security

| Feature | Implementation |
|---------|-----------------|
| HTTP-Only Cookies | Prevents XSS token theft |
| CSRF Protection | CSRF tokens validated per request |
| Token Rotation | Access tokens refreshed regularly |
| Token Revocation | Blacklist checked on each request |
| Expiry Enforcement | Tokens expire automatically |
| Secure Transport | HTTPS required in production |

### CORS & CSP

**Development CORS Origins:**
```
http://localhost:3000
http://localhost:5000
http://localhost:8080
```

**Production CORS Origins:**
- Set via `CORS_ORIGINS` environment variable
- Wildcards disabled in production

**Content Security Policy:**
- No inline scripts/styles in production
- Only self-hosted or whitelisted resources
- Frame ancestors: DENY (prevent clickjacking)

## Multi-Tenancy Integration

Each request automatically establishes tenant context via JWT claims:

```python
@app.before_request
def handle_tenant_isolation():
    """Switch database schema based on JWT organisation_id"""
    verify_jwt_in_request(optional=True)
    claims = get_jwt()
    if claims and 'organisation_id' in claims:
        set_tenant_schema(claims['organisation_id'])
```

This ensures:
- User can only access their organization's data
- Database queries automatically scoped to tenant schema
- No data leakage between organizations

## Role-Based Access Control (RBAC)

Roles are embedded in JWT and checked before API operations:

```python
@jwt_required()
def create_asset():
    claims = get_jwt()
    if not User(id=claims['identity']).has_permission('assets:create'):
        raise AuthorizationError("Insufficient permissions")
    # ... create asset
```

**Available Roles:**
- `admin` - Full system access
- `store_manager` - Inventory + transfer management
- `staff` - View, create, edit assets/inventory
- `dept_head` - Approval authority
- `viewer` - Read-only access
- `auditor` - Audit log access

## Error Handling

### 401 Unauthorized (Missing/Invalid Token)
```json
{
  "success": false,
  "status_code": 401,
  "error": "Missing Authorization Header"
}
```

**Causes:**
- No token provided
- Token expired
- Token signature invalid
- Token revoked (on blacklist)

**Client Action:**
- Redirect to login
- Clear cookies
- Retry with refresh token

### 403 Forbidden (Insufficient Permissions)
```json
{
  "success": false,
  "status_code": 403,
  "error": "Insufficient permissions for this action"
}
```

**Client Action:**
- Display error message
- Disable UI elements based on role

## Token Revocation (Blacklist)

### When Tokens Are Revoked
- User logs out
- Password changed
- Account locked
- User deactivated
- Admin revokes token

### Revocation Store
- `TokenBlacklist` table tracks revoked JTIs
- Checked on every authenticated request
- Expired tokens auto-purged (no cleanup needed)

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=<generate-secure-random>
JWT_ACCESS_TOKEN_EXPIRES=3600        # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=2592000    # 30 days

# Cookie Security
JWT_COOKIE_SECURE=True              # HTTPS only (prod)
JWT_COOKIE_HTTPONLY=True            # No JS access
JWT_COOKIE_SAMESITE=Lax             # CSRF protection

# CSRF Token Protection
JWT_COOKIE_CSRF_PROTECT=True
JWT_ACCESS_CSRF_HEADER_NAME=X-CSRF-TOKEN
```

### Development vs Production

**Development:**
- `JWT_COOKIE_SECURE=False` (allows HTTP)
- `SESSION_COOKIE_SECURE=False`
- Debug logging enabled
- CORS: Multiple localhost origins

**Production:**
- `JWT_COOKIE_SECURE=True` (HTTPS only)
- `SESSION_COOKIE_SECURE=True`
- Debug logging disabled
- CORS: Only production domain(s)
- HTTPS enforced via Talisman

## Implementation Examples

### Frontend: Login Flow (React)

```typescript
import axios from 'axios';

const login = async (email: string, password: string) => {
  try {
    const response = await axios.post('/api/auth/login', 
      { email, password },
      { withCredentials: true }  // Include cookies
    );
    
    // Tokens stored in secure cookies by backend
    // No client-side token storage needed
    localStorage.setItem('user', JSON.stringify(response.data.user));
    
    return response.data;
  } catch (error) {
    throw error.response?.data?.error;
  }
};

const logout = async () => {
  await axios.post('/api/auth/logout', {}, 
    { withCredentials: true }
  );
  localStorage.removeItem('user');
};

const refresh = async () => {
  return axios.post('/api/auth/refresh', {}, 
    { withCredentials: true }
  );
};
```

### Frontend: Automatic Token Refresh

```typescript
const apiClient = axios.create({
  baseURL: '/api',
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        await refresh();
        return apiClient(error.config);  // Retry request
      } catch {
        window.location.href = '/login';  // Redirect to login
      }
    }
    return Promise.reject(error);
  }
);
```

### Backend: Protected Route

```python
from flask_jwt_extended import jwt_required, get_jwt

@assets_bp.route('/assets', methods=['GET'])
@jwt_required()
def list_assets():
    claims = get_jwt()
    user_id = claims['identity']
    org_id = claims['organisation_id']
    
    # Tenant automatically isolated via set_tenant_schema()
    assets = Asset.query.filter_by(organisation_id=org_id).all()
    
    return jsonify([asset.to_dict() for asset in assets])
```

## Migration from Mixed Auth

**Why Flask-Login was removed:**
1. Unnecessary complexity with JWT
2. Potential for auth bypass if both mechanisms used incorrectly
3. Session management conflicts with stateless JWT
4. Flask-Login not needed for API-only (vs. server-rendered pages)

**What Changed:**
- ✅ Removed: `LoginManager`, `@login_required`, user_loader callback
- ✅ Kept: JWT infrastructure, RBAC, token management
- ✅ Simplified: Single auth mechanism for all endpoints
- ✅ Secured: CSRF protection, HTTP-only cookies, rate limiting

## Troubleshooting

### Issue: "Missing Authorization Header"
- Ensure request includes `Authorization: Bearer <token>` header
- Or cookies are being sent (`withCredentials: true` in frontend)

### Issue: "Token has expired"
- Use refresh token endpoint to get new access token
- Check system clock sync

### Issue: "Token has been revoked"
- User has been logged out or account locked
- Redirect to login

### Issue: CORS errors
- Verify frontend origin in `CORS_ORIGINS`
- Ensure `withCredentials: true` in frontend
- Check CSP policy allows frontend origin

## Performance Considerations

- JWT validation: ~1-2ms per request (cryptographic verification)
- No database lookups for token validation (stateless)
- Token revocation check: ~0.1ms (indexed JTI lookup)
- CORS preflight: Cached 1 hour
- Rate limiting: In-memory store (fast)

## References

- JWT.io Debugger: https://jwt.io/
- RFC 7519 (JWT): https://tools.ietf.org/html/rfc7519
- OWASP Authentication: https://cheatsheetseries.owasp.org/
- Flask-JWT-Extended Docs: https://flask-jwt-extended.readthedocs.io/
