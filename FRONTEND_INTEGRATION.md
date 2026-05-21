# Frontend Integration Guide

This document outlines how to integrate a frontend application with the TrackIT Assets & Inventory API.

## Architecture Overview

```
Frontend (React/Vue/Angular)
    ↓
    ├─ JWT Authentication (via /api/auth)
    ├─ API Client with Axios/Fetch
    └─ State Management (Redux/Vuex/Pinia)
    
Backend (Flask)
    ├─ JWT Token Management (access + refresh)
    ├─ Role-Based Access Control
    ├─ Multi-tenant Isolation
    └─ PostgreSQL Database
```

## Authentication Flow

### 1. Organization Registration

**Request:**
```bash
POST /api/auth/register-org
Content-Type: application/json

{
  "org_name": "Acme Corp",
  "org_code": "ACME",
  "org_description": "Manufacturing",
  "admin_username": "admin",
  "admin_email": "admin@acme.com",
  "admin_password": "SecurePass123!",
  "admin_first_name": "John",
  "admin_last_name": "Doe"
}
```

**Response:**
```json
{
  "success": true,
  "status_code": 201,
  "message": "Institution registered successfully",
  "org_id": 1,
  "admin_id": 1
}
```

### 2. User Login

**Request:**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@acme.com",
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
    "username": "admin",
    "email": "admin@acme.com",
    "role": "admin",
    "organisation_id": 1
  }
}
```

**Cookies Set:**
- `access_token_cookie`: JWT access token (1 hour expiry)
- `refresh_token_cookie`: Refresh token (30 days expiry)

### 3. Token Refresh

**Request:**
```bash
POST /api/auth/refresh
```

**Response:**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Token refreshed"
}
```

### 4. Logout

**Request:**
```bash
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Logout successful"
}
```

## Frontend Implementation Example (React)

### API Client Setup

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Include cookies in requests
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include CSRF token if needed
apiClient.interceptors.request.use((config) => {
  const token = document.cookie
    .split('; ')
    .find((row) => row.startsWith('access_token_cookie='))
    ?.split('=')[1];
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      try {
        await apiClient.post('/auth/refresh');
        // Retry original request
        return apiClient(error.config);
      } catch {
        // Redirect to login
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Authentication Hook

```typescript
import { useState, useCallback } from 'react';
import apiClient from './apiClient';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      setUser(response.data.user);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/auth/logout');
      setUser(null);
    } catch (err) {
      setError(err.response?.data?.message || 'Logout failed');
    }
  }, []);

  const getCurrentUser = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/auth/me');
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { user, loading, error, login, logout, getCurrentUser };
};
```

## API Endpoints

### Authentication
- `POST /api/auth/register-org` - Register new organization
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user

### Assets
- `GET /api/assets` - List assets
- `POST /api/assets` - Create asset
- `GET /api/assets/{id}` - Get asset details
- `PUT /api/assets/{id}` - Update asset
- `DELETE /api/assets/{id}` - Delete asset

### Inventory
- `GET /api/inventory` - List inventory items
- `POST /api/inventory` - Create inventory item
- `GET /api/inventory/{id}` - Get item details
- `PUT /api/inventory/{id}` - Update item
- `POST /api/inventory/{id}/add-stock` - Add stock
- `POST /api/inventory/{id}/remove-stock` - Remove stock

### Reports
- `GET /api/reports/asset-summary` - Asset summary report
- `GET /api/reports/inventory-valuation` - Inventory valuation
- `GET /api/reports/depreciation` - Asset depreciation report

## Role-Based Access Control

The API enforces RBAC. Roles and their permissions:

| Role | Assets | Inventory | Transfers | Approval | Audit |
|------|--------|-----------|-----------|----------|-------|
| admin | Full | Full | Full | Full | Full |
| store_manager | Full | Full | Full | View | View |
| staff | View, Create, Edit | View, Edit | Create, View | - | - |
| dept_head | View, Approve | View | Approve | Full | View |
| viewer | View | View | View | - | - |
| auditor | View | View | View | - | Full |

## Environment Setup

Create `.env.local` in your frontend project:

```
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_ENV=development
```

For production:
```
REACT_APP_API_URL=https://api.yourdomain.com/api
REACT_APP_ENV=production
```

## Security Headers & CORS

The API enforces strict CORS and CSP policies:

**Development CORS Origins:**
- http://localhost:3000
- http://localhost:5000
- http://localhost:8080

**Production CORS Origins:**
- Set via `CORS_ORIGINS` environment variable

**CSP Policy:**
- No inline scripts or styles (prod)
- Only self-hosted resources
- External resources must be explicitly whitelisted

## Error Handling

All API errors follow this format:

```json
{
  "success": false,
  "status_code": 400,
  "error": "Validation failed",
  "details": {
    "field_name": ["error message"]
  }
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (no/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate resource)
- `500` - Server Error

## Testing

Example using Jest + React Testing Library:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { useAuth } from './hooks/useAuth';
import LoginComponent from './LoginComponent';

jest.mock('./apiClient', () => ({
  post: jest.fn(),
}));

test('should login user successfully', async () => {
  render(<LoginComponent />);
  
  fireEvent.change(screen.getByLabelText(/email/i), {
    target: { value: 'user@example.com' },
  });
  fireEvent.change(screen.getByLabelText(/password/i), {
    target: { value: 'Password123!' },
  });
  fireEvent.click(screen.getByText(/login/i));
  
  await screen.findByText(/login successful/i);
});
```

## Deployment

### Frontend Deployment (Vercel, Netlify, etc.)

1. Build the frontend:
   ```bash
   npm run build
   ```

2. Deploy to hosting service:
   ```bash
   npm run deploy
   ```

3. Set production environment variables for API URL

### Backend Deployment (See DOCKER_GUIDE.md and CI/CD configuration)

## Troubleshooting

### CORS Errors
- Check frontend origin is in CORS_ORIGINS
- Ensure `withCredentials: true` in Axios
- Verify Content-Type header

### 401 Unauthorized
- Check token expiry and refresh flow
- Clear browser cookies and re-login
- Check JWT_SECRET_KEY matches between requests

### Network Errors
- Verify API server is running
- Check API_URL environment variable
- Look for SSL certificate issues in production

## Additional Resources

- API Documentation: See `backend/README.md`
- Database Schema: See `backend/app/models/`
- Docker Setup: See `DOCKER_GUIDE.md`
- CI/CD Pipeline: See `.github/workflows/ci-cd.yml`
