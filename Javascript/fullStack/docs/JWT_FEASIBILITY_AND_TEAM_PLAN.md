# FoodyBites Auth Phase: JWT & Mobile-Ready Implementation
## Feasibility Study & Team Execution Plan

---

## Executive Summary

We're transitioning from session-based auth to JWT for mobile-first compatibility. This document covers:
- Why JWT fits the mobile delivery app context
- Security decisions and trade-offs
- Implementation roadmap
- Team coordination checkpoints

---

## 1. Context: Food Delivery App Requirements

### What we're building:
- Cross-platform food ordering (web → React Native/Flutter later)
- Real-time order tracking
- Push notifications (order status)
- Offline-capable cart and order history
- Location-based operations

### Why JWT is the right fit:
- **Stateless**: No server session storage needed as you scale
- **Mobile-friendly**: Native apps and PWAs use bearer tokens naturally
- **Cross-domain**: Easier for API microservices and third-party integrations (payment gateways, delivery partners)
- **Self-contained**: User data included in token (no extra DB lookup per request in ideal case)

### What JWT is NOT good for:
- Real-time session revocation (can't instantly invalidate a token everywhere)
- Heavy logout operations (token still valid until expiry)
- Frequent permission changes within a session

---

## 2. Security Decisions

### Token expiry strategy:
- **Access token**: 24 hours (long enough for mobile usage, short enough for security)
- **Refresh token**: 30 days (kept in secure storage on mobile, sent only for token refresh)
- **Rationale**: Long access token reduces auth requests and server load; separate refresh token limits blast radius if access token is compromised

### Where to store tokens (mobile/web):
| Storage | Best for | Risk |
|---------|----------|------|
| HttpOnly cookie | Traditional web/SPAs | None (secure) |
| localStorage | SPA/PWA | XSS: tokens visible to scripts |
| Memory + secure headers | Native mobile | Safe; lost on app restart (intended) |

**Decision for FoodyBites**: Issue both; client chooses:
- Web clients: use cookies (we'll set HttpOnly from backend)
- Mobile clients: use Authorization header with Bearer token

### Password hashing:
- Supabase Auth handles this (bcrypt under the hood)
- We don't store raw passwords

### Token payload (claims):
```json
{
  "sub": "user-id-uuid",
  "email": "user@example.com",
  "role": "customer",
  "iat": 1713268800,
  "exp": 1713355200
}
```
- Minimal payload: just enough to identify user and enforce basic permissions
- Larger data (profile, preferences) fetched separately via authenticated API calls

---

## 3. Implementation Roadmap (Phase-based)

### Phase 1: Backend JWT setup (THIS PHASE)
- [ ] Add JWT signing/verification library (jsonwebtoken)
- [ ] Create JWT middleware for protected routes
- [ ] Update signup/login endpoints to issue JWTs
- [ ] Add token refresh endpoint
- [ ] Add logout endpoint (client-side token clearing)

### Phase 2: Frontend signup/login pages (THIS PHASE)
- [ ] Build responsive signup form with validation
- [ ] Build responsive login form
- [ ] Handle token storage (localStorage for now, migrate to secure storage for mobile apps)
- [ ] Protect authenticated pages with token checks
- [ ] Handle token refresh transparently

### Phase 3: Mobile app handoff (future)
- Implementation largely reuses our JWT infrastructure
- Switch from cookies to Authorization headers
- Use platform-specific secure storage (Keychain on iOS, Keystore on Android)

### Phase 4: Advanced security (future phases)
- CSRF protection (not needed with JWTs in Authorization headers)
- Rate limiting on auth endpoints
- Suspicious login alerts
- Two-factor authentication

---

## 4. Team Responsibilities & Coordination

### Backend team:
1. Update [src/routes/auth.routes.js](auth routes) to sign JWTs on signup/login
2. Create [src/middleware/auth.middleware.js](new) for token verification
3. Create [src/services/jwt.service.js](new) for token operations
4. Test with Postman/curl using Authorization header
5. Document API endpoints and JWT flow

### Frontend team:
1. Create [public/signup.html](signup page) with form and validation
2. Create [public/login.html](login page) with form and validation
3. Add [public/auth.js](new) for token management utilities
4. Add [public/page-guard.js](new) to protect authenticated pages
5. Update [public/styles.css] with form styling
6. Test signup → login → menu page flow

### DevOps/QA:
1. .env secrets: ensure JWT_SECRET is long and random
2. Test token expiry behavior
3. Test refresh token flow under load
4. Security audit: ensure tokens not logged, HttpOnly where applicable

### Meeting points:
- **Kickoff**: Confirm JWT secret strategy and token expiry times
- **Midpoint**: Backend JWT endpoints ready, frontend ready to integrate
- **Sign-off**: End-to-end auth flow tested on desktop and mobile browser

---

## 5. Technical Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Web/Mobile)                       │
├─────────────────────────────────────────────────────────────┤
│  1. User fills signup/login form                            │
│  2. POST /api/v1/auth/signup or /api/v1/auth/login          │
│  3. Receive { accessToken, refreshToken }                   │
│  4. Store securely (localStorage or device secure storage)  │
│  5. Set Authorization: Bearer <accessToken> on all requests │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Server (Express)                          │
├─────────────────────────────────────────────────────────────┤
│  POST /signup     → hash pwd, create user, issue JWT        │
│  POST /login      → verify pwd, issue JWT                   │
│  POST /refresh    → validate refresh token, new access JWT  │
│  POST /logout     → (no-op; client deletes token)           │
│                                                              │
│  [Auth middleware] → verify JWT → attach user to req.user   │
│  GET /api/v1/orders  [auth]  → list user's orders           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Supabase Database                         │
├─────────────────────────────────────────────────────────────┤
│  - profiles: user data, role, phone                         │
│  - orders: order records with customer_id                   │
│  - (JWT secret stored in env, NOT in DB)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Security Checklist

- [ ] JWT_SECRET is 32+ random bytes (use `openssl rand -hex 32`)
- [ ] JWT_SECRET never committed to git (lives in .env)
- [ ] Access token NOT stored in localStorage on production (unless SPA only)
- [ ] Refresh token rotation on each use (optional but recommended)
- [ ] Token expiry enforced on server (not just client)
- [ ] Logout clears client storage (token still valid on server until expiry, acceptable trade-off)
- [ ] HTTPS only in production (tokens compromised on HTTP)
- [ ] Rate limiting on /signup and /login (prevent brute force)
- [ ] Password requirements enforced (min 8 chars; we use Supabase Auth which has its own rules)

---

## 7. Failure Modes & Mitigation

| Failure | Cause | Mitigation |
|---------|-------|-----------|
| Token leaked | XSS attack | Minimize XSS surface; use Content Security Policy |
| Token stolen from localStorage | Compromised device | Educate users; offer account recovery flow |
| User can't logout | Token still valid | Expected; users understand token has expiry; support team can invalidate in DB if needed |
| Refresh token expired | User was inactive for 30 days | Graceful re-login flow; explain to user |
| Token server-side validation fails | Bad parsing/signature | Return 401; force re-auth |

---

## 8. API Endpoints (Finalized)

### POST /api/v1/auth/signup
Request:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "fullName": "Anu Okonkwo",
  "phoneNumber": "+2348012345678"
}
```
Response (201):
```json
{
  "success": true,
  "message": "Signup successful.",
  "data": {
    "user": { "id": "uuid", "email": "..." },
    "accessToken": "eyJ...",
    "refreshToken": "eyJ...",
    "expiresIn": 86400
  }
}
```

### POST /api/v1/auth/login
Request:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```
Response (200):
```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "user": { "id": "uuid", "email": "..." },
    "accessToken": "eyJ...",
    "refreshToken": "eyJ...",
    "expiresIn": 86400,
    "profile": { "full_name": "...", "phone_number": "..." }
  }
}
```

### POST /api/v1/auth/refresh
Request:
```json
{
  "refreshToken": "eyJ..."
}
```
Response (200):
```json
{
  "success": true,
  "data": {
    "accessToken": "eyJ...",
    "expiresIn": 86400
  }
}
```

### POST /api/v1/auth/logout
Request: (just send this; client deletes tokens)
Response (200):
```json
{
  "success": true,
  "message": "Logout acknowledged. Clear tokens on client."
}
```

---

## 9. Team Handoff Notes

- **For backend**: JWT library is `jsonwebtoken`. Secret is `process.env.JWT_SECRET`.
- **For frontend**: Store tokens in localStorage (plan to migrate to secure storage for native app). Always include `Authorization: Bearer <token>` on API requests.
- **For QA**: Test token expiry by manually editing token expiry in JWT, then making API calls.
- **For DevOps**: Ensure JWT_SECRET rotates yearly; update .env on deploy.

---

## Next Steps (Immediate)

1. Generate JWT_SECRET: `openssl rand -hex 32` → add to .env
2. Backend: Implement JWT service and update auth routes
3. Frontend: Build signup/login forms and token handling
4. Integration test: Signup → login → authenticated API call
5. Review: Security audit of implementation

---
