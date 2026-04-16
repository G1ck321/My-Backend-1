# FoodyBites JWT Auth - Testing & Integration Guide

## Overview

You now have a complete JWT auth system implemented. This guide explains how to test it, integrate it, and understand the flow.

---

## Setup Checklist (Do This First)

### 1. Generate JWT Secret

```bash
openssl rand -hex 32
```

Output example: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### 2. Add to .env

```env
JWT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
SUPABASE_URL=your-url
SUPABASE_ANON_KEY=your-key
SUPABASE_SERVICE_ROLE_KEY=your-key
```

### 3. Install dependencies

```bash
npm install
```

### 4. Run the server

```bash
npm run dev
```

Server starts at `http://localhost:3000`

---

## Flow Diagram

```
User visits /public/signup.html
         ↓
User fills form, clicks "Create Account"
         ↓
POST /api/v1/auth/signup with email, password, fullName, phoneNumber
         ↓
        [Server validates with Zod]
         ↓
        [Create Supabase auth user]
         ↓
        [Create profile in profiles table]
         ↓
        [Sign JWT access token (24h expiry)]
         ↓
        [Sign JWT refresh token (30d expiry)]
         ↓
Return { accessToken, refreshToken, expiresIn: 86400 }
         ↓
Client stores in localStorage
         ↓
Client redirects to /public/menu.html
         ↓
Menu page calls requireAuth() - checks for token
         ↓
Menu page calls fetchWithAuth() with Authorization: Bearer <token>
         ↓
Server middleware verifies token signature and expiry
         ↓
If valid: request proceeds, req.user is set
If expired but has refresh: auto-refresh token
If no token: return 401, client redirects to login
```

---

## Testing with Postman

### 1. Signup Test

**Method:** POST  
**URL:** `http://localhost:3000/api/v1/auth/signup`

**Body (JSON):**
```json
{
  "email": "test@example.com",
  "password": "SecurePass123",
  "fullName": "Test User",
  "phoneNumber": "+2348012345678"
}
```

**Expected Response (201):**
```json
{
  "success": true,
  "message": "Signup successful.",
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "test@example.com"
    },
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400
  }
}
```

### 2. Login Test

**Method:** POST  
**URL:** `http://localhost:3000/api/v1/auth/login`

**Body (JSON):**
```json
{
  "email": "test@example.com",
  "password": "SecurePass123"
}
```

**Expected Response (200):**
Same as signup response (minus the "Signup" message).

### 3. Protected Endpoint Test (Menu)

**Method:** GET  
**URL:** `http://localhost:3000/api/v1/menu`

**Headers:**
```
Authorization: Bearer <accessToken from signup/login>
```

**Expected Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "m1",
      "name": "Jollof Rice Special",
      "price": 6500,
      "currency": "NGN",
      "is_available": true
    },
    ...
  ]
}
```

**If no token:**
```json
{
  "success": false,
  "message": "Missing or invalid Authorization header."
}
```

**If expired token:**
```json
{
  "success": false,
  "message": "Unauthorized: Token verification failed: jwt expired"
}
```

### 4. Refresh Token Test

**Method:** POST  
**URL:** `http://localhost:3000/api/v1/auth/refresh`

**Body (JSON):**
```json
{
  "refreshToken": "<refreshToken from signup/login>"
}
```

**Expected Response (200):**
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400
  }
}
```

### 5. Logout Test

**Method:** POST  
**URL:** `http://localhost:3000/api/v1/auth/logout`

**Expected Response (200):**
```json
{
  "success": true,
  "message": "Logout acknowledged. Clear tokens on client."
}
```

Note: Server doesn't track logout; client just clears tokens.

---

## Testing with Browser

### Signup Flow

1. Open `http://localhost:3000/public/signup.html`
2. Fill in form:
   - Full Name: Anu Okonkwo
   - Email: anu@example.com
   - Phone: +2348012345678
   - Password: SecurePass123
   - Confirm: SecurePass123
3. Click "Create Account"
4. Success message appears, redirect to menu page
5. Menu loads with authenticated data

### Login Flow

1. Open `http://localhost:3000/public/login.html`
2. Fill in:
   - Email: anu@example.com
   - Password: SecurePass123
3. Click "Sign In"
4. Success message appears, redirect to menu page
5. Menu loads with authenticated data

### Check Token in Browser DevTools

1. Open DevTools (F12)
2. Go to Application tab
3. Click "LocalStorage" → `http://localhost:3000`
4. Look for keys:
   - `fb_access_token`: Your JWT
   - `fb_refresh_token`: Refresh JWT
   - `fb_user`: User info (if saved)

### Decode JWT (optional verification)

Visit https://jwt.io/ and paste your token:
- Should show payload with `sub` (user ID), `email`, `role`, `exp` (expiry timestamp)

---

## Code Locations & What They Do

| File | Purpose |
|------|---------|
| `src/services/jwt.service.js` | Signs and verifies JWTs |
| `src/middleware/auth.middleware.js` | Validates token on protected routes |
| `src/routes/auth.routes.js` | Signup, login, refresh, logout endpoints |
| `public/auth.js` | Client-side token manager and fetchWithAuth wrapper |
| `public/signup.html` | Signup form UI |
| `public/login.html` | Login form UI |
| `public/menu.html` | Protected menu page (requires auth) |
| `public/styles.css` | Form styling + responsive design |

---

## Frontend JavaScript API

### TokenManager

```javascript
// Store tokens
TokenManager.setAccessToken(token)
TokenManager.setRefreshToken(token)

// Retrieve tokens
const access = TokenManager.getAccessToken()
const refresh = TokenManager.getRefreshToken()

// Clear tokens (logout)
TokenManager.logout()

// Check auth
if (TokenManager.isAuthenticated()) { ... }
```

### fetchWithAuth

```javascript
// Use like fetch, but auto-includes Authorization header
const response = await fetchWithAuth('/api/v1/menu')
const data = await response.json()
```

Handles:
- Automatically adds `Authorization: Bearer <token>`
- If 401, tries to refresh token
- If refresh fails, redirects to login

### Page Guards

```javascript
// Redirect unauthenticated users to login
requireAuth()

// Redirect authenticated users away from auth pages
redirectIfAuthenticated()
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "JWT_SECRET is not set" | Missing .env variable | Add `JWT_SECRET=...` to .env |
| Signup works, but profile not created | Supabase service role key invalid | Verify SUPABASE_SERVICE_ROLE_KEY in .env |
| Token expires after 1 second | ACCESS_TOKEN_EXPIRY is '1s' (for testing) | Change to '24h' in jwt.service.js |
| CORS error on POST /signup | CORS not configured | Ensure helmet and cors middleware in src/app.js |
| "Passwords do not match" on signup | Form validation failed | Check password == confirmPassword |
| 401 on menu page | Token expired | Refresh token auto-triggers; if still fails, logout and re-login |
| localStorage empty after refresh | Browser privacy mode | Use incognito mode test or switch to sessionStorage |

---

## Security Best Practices Implemented

✅ JWT secret is environment variable (not in code)  
✅ Access token is 24 hours (short-lived)  
✅ Refresh token is 30 days (extends session safely)  
✅ Tokens are validated on server every request  
✅ Password hashing handled by Supabase Auth  
✅ Form validation with Zod on server  
✅ Error messages don't leak auth status  
✅ HTTPS enforced in production (via helmet, CORS settings)

---

## Next Production Steps

1. **Add rate limiting** on /signup and /login (prevent brute force)
2. **Switch to secure token storage** on mobile apps (Keychain/Keystore)
3. **Add token rotation** on refresh (issue new refresh token each time)
4. **Implement 2FA** if needed (SMS or email verification)
5. **Log suspicious login attempts** (unusual IP, rapid failures)
6. **Add password reset flow** (email with reset link)
7. **HTTPS enforcement** in production
8. **Monitor JWT secret rotation** (yearly or on suspected breach)

---

## Team Checklist

- [ ] Backend team: Ran `npm install` and tested POST /signup in Postman
- [ ] Backend team: Generated JWT_SECRET and added to .env
- [ ] Frontend team: Tested /public/signup.html → /public/menu.html flow
- [ ] Frontend team: Verified tokens appear in localStorage after signup
- [ ] Frontend team: Tested logout and re-login
- [ ] QA: Tested with expired token (manually change expiry in JWT)
- [ ] QA: Tested with invalid token (malformed JWT)
- [ ] QA: Tested CORS by calling from different origin
- [ ] DevOps: Verified JWT_SECRET is in production .env (not in git)

---

## Questions?

Refer to:
- JWT spec: https://tools.ietf.org/html/rfc7519
- jsonwebtoken lib: https://www.npmjs.com/package/jsonwebtoken
- Supabase Auth: https://supabase.com/docs/guides/auth
