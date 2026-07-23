# Item 7 FastAPI Backend

This folder contains a small FastAPI checkout service. It creates payment sessions with Flutterwave, stores orders in Supabase, receives payment webhooks, and exposes a Telegram bot-style admin interface for order summaries.

## What lives where

- `main.py` starts the FastAPI app, installs CORS, and wires the routers together.
- `config.py` loads environment variables from `.env` and normalizes a couple of Telegram values.
- `database.py` creates the shared Supabase client.
- `schemas.py` defines the request body the frontend must send to `/api/pay`.
- `routers/orders.py` handles payment initialization and health checks.
- `routers/webhooks.py` handles Flutterwave webhooks, Telegram admin commands, and CSV export.

## Request flow

1. The frontend posts an order payload to `POST /api/pay`.
2. The server validates the payload with Pydantic.
3. The server adds the delivery fee, stores a `pending` order in Supabase, and asks Flutterwave for a hosted checkout link.
4. Flutterwave redirects the customer back to the frontend after payment.
5. Flutterwave also calls `POST /webhooks/flutterwave` on successful payment.
6. The webhook handler marks the order as `paid` and sends an admin notification to Telegram.

## Setup

Install dependencies from inside this folder:

```bash
pip install -r requirements.txt
```

Run the app with Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

If you prefer the built-in runner, `python main.py` works too.

## Environment variables

Create a `.env` file in this folder with these keys:

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service or anon key used by this backend |
| `FLW_SECRET_HASH` | Flutterwave webhook secret header value |
| `FW_SECRET_KEY` | Flutterwave secret key used to create checkout sessions |
| `TELEGRAM_BOT_TOKEN` | Bot token for admin notifications and commands |
| `TELEGRAM_CHAT_ID` | Chat ID for the admin Telegram channel or chat |
| `RESEND_API_KEY` | API key for email notifications if you enable the email helper |
| `OWNER_EMAIL_ADDRESS` | Admin email address for receipts and alerts |

The code expects `.env` to sit next to `main.py`.

## Endpoints

### `POST /api/pay`

Creates a payment session.

Example payload:

```json
{
  "name": "Jane Doe",
  "phone": "08012345678",
  "matricNumber": "12AB345678",
  "address": "Hall A",
  "email": "jane@example.com",
  "roomNumber": "12",
  "orderDetails": "Jollof rice, chicken, and drink",
  "amount": 2500
}
```

The server adds a 150 NGN convenience fee before sending the payment request to Flutterwave.

### `GET /api/health`

Returns a simple operational status response. Useful for uptime checks.

### `HEAD /api/health`

Same health target, but without a body.

### `POST /webhooks/flutterwave`

Receives Flutterwave payment updates.

The request must include the `verif-hash` header matching `FLW_SECRET_HASH`.

### `POST /webhooks/telegram`

Accepts Telegram bot updates and understands these commands:

- `/today`
- `/todaynumber`
- `/orders`
- `/ordersnumber`
- `/<matricNumber>` such as `/12AB345678`

### `GET /webhooks/admin/export-csv`

Downloads a CSV export of all paid orders.

## Supabase table expectation

The code assumes an `orders` table with fields similar to these:

- `name`
- `phone`
- `matricNumber`
- `address`
- `roomNumber`
- `orderDetails`
- `amountpaid`
- `tx_ref`
- `status`
- `email`
- `created_at`

The webhook logic filters on `status = "paid"`, so make sure that column exists and is writable.

## Notes for beginners

- The backend uses Pydantic models to reject bad request payloads before the payment logic runs.
- `BackgroundTasks` is used so notification work happens after the webhook response is ready.
- CORS is currently wide open for development. Tighten it before production.
- The CSV export writes to memory and returns the file directly, which is fine for small-to-medium order volumes.

## Common troubleshooting checks

1. If `/api/pay` fails immediately, confirm the `.env` file is being loaded and the Supabase keys are correct.
2. If Flutterwave never calls the webhook, verify the public URL and the `verif-hash` value.
3. If Telegram commands do nothing, confirm the bot token, chat ID, and webhook setup.
4. If CSV export is empty, check whether any orders have actually been marked `paid`.