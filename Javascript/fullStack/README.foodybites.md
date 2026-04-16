# FoodyBites Implementation Starter

This repository is now being converted from a single-file Express demo into a production-oriented food ordering backend.

## What is in this first implementation

- Secure Express app bootstrap with Helmet, CORS, request logging, and centralized errors.
- API route layout for health, auth, menu, orders, payments, and reminders.
- Supabase client wiring for the next phase.
- A starter SQL schema for the core FoodyBites tables.
- Sample menu data for Nigerian snacks and main dishes.

## Next implementation phases

1. Supabase Auth integration for signup/login.
2. Menu, order, and payment persistence.
3. Paystack initialization and webhook verification.
4. Receipt uploads with Supabase Storage.
5. Real-time order tracking with delivery events and live updates.
6. Email/SMS reminder jobs.
7. Delivery zone discount logic.

## Environment variables

Create a `.env` file with:

- `PORT=3000`
- `SUPABASE_URL=your-supabase-url`
- `SUPABASE_ANON_KEY=your-anon-key`
- `SUPABASE_SERVICE_ROLE_KEY=your-service-role-key`
- `CORS_ORIGIN=http://localhost:3000`

## Start the app

```bash
npm install
npm run dev
```
