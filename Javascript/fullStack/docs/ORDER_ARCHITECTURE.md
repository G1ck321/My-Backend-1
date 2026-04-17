# FoodyBites Order Management Architecture

## Executive Summary

This document defines the complete order management system for FoodyBites, covering business flows, data models, policies, and constraints. It serves as the specification for implementation phases 3 onwards.

---

## 1. Order Lifecycle & States

### State Machine Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ORDER LIFECYCLE                          │
└─────────────────────────────────────────────────────────────┘

[pending_payment] (Customer placing order, awaiting payment)
        ↓
   [Customer pays via Paystack or Bank Transfer]
        ↓
[confirmed] (Order confirmed, goes to kitchen)
        ↓
[preparing] (Kitchen is preparing the food)
        ↓
[ready_for_pickup] (Food ready, waiting for rider/customer)
        ↓
[on_the_way] (Rider has picked up, delivering to customer)
        ↓
[delivered] (Order successfully delivered, customer receives)
        ↓
[completed] (Final state: customer confirmed receipt & satisfaction)

ALTERNATE PATHS:
[pending_payment] → [payment_failed] → [pending_payment] (retry)
[pending_payment] → [cancelled] (customer cancels before payment)
[confirmed] → [cancelled] (customer cancels, gets refund)
[preparing] → [cancelled] (customer cancels, restaurant refunds)
Any state → [cancelled] (admin cancellation)
```

### State Definitions

| State | Duration | Entry Condition | Exit Condition | Stakeholder |
|-------|----------|-----------------|----------------|-------------|
| **pending_payment** | 10-15 min | Order placed | Payment confirmed or timeout | Customer |
| **payment_failed** | N/A | Payment declined | Customer retries or abandons | Customer |
| **confirmed** | ~2 min | Payment successful | Kitchen acknowledges | Kitchen |
| **preparing** | Variable (15-45 min) | Kitchen starts | Food plated | Kitchen |
| **ready_for_pickup** | Variable (2-30 min) | Food complete | Rider assigned & collected | Kitchen/Rider |
| **on_the_way** | Variable (10-30 min) | Rider departed | Rider at location | Rider |
| **delivered** | Instant | Rider at destination | Customer confirms receipt | Customer |
| **completed** | N/A | Customer confirmed | Fulfillment end | System |
| **cancelled** | N/A | At any state | Refund processed | Admin/Customer/System |

---

## 2. Business Policies & Rules

### 2.1 Pricing Policies

#### Base Pricing
```
subtotal = sum(item_qty × item_price for each item)
delivery_fee = 1500 NGN (default)
```

#### Discount Rules (Applied in Order)
1. **New Customer Discount**
   - Condition: Customer's first order (no `completed` orders before)
   - Amount: 10% of subtotal
   - Applies to: Subtotal only (not delivery)
   - Stackable: No (can't combine with promo codes)

2. **Zone-Based Discount**
   - Condition: Customer's delivery address within zone
   - Amount: Per-zone configurable (0-20%)
   - Applies to: Subtotal
   - Stackable: Yes (stacks with new customer only if both apply)

3. **Free Delivery Threshold**
   - Condition: `subtotal >= 15,000 NGN`
   - Amount: Waive delivery_fee entirely
   - Rule: Takes precedence over all other fees

4. **Promo Code** (Future Phase)
   - Condition: Valid code applied at checkout
   - Amount: Percentage or fixed amount
   - Applies to: Subtotal
   - Stackable: No (replaces other discounts)

#### Final Calculation
```javascript
discounts = newCustomerDiscount + zoneDiscount
total = subtotal + delivery_fee - discounts
minimum_order_total = 2000 // NGN minimum to place order
if (total >= 15000) delivery_fee = 0
final_total = max(total, 0)
```

### 2.2 Payment Policies

#### Payment Methods
1. **Paystack (Online)**
   - Supported: Debit/Credit cards, transfers, USSD
   - Processing: 5-30 seconds
   - Fee: Charged by Paystack (not by FoodyBites)
   - Refund: Automatic via Paystack API
   - Status: Order auto-confirms on successful charge

2. **Bank Transfer (Manual)**
   - Account: FoodyBites business account (to be configured)
   - Reference: Order ID + customer name
   - Processing: Manual verification (2-4 hours)
   - Status: Manual approval by admin via dashboard
   - Receipt: Customer uploads proof, admin verifies

3. **Cash on Delivery** (Future Phase)
   - Status: Rider collects upon delivery
   - Refund: N/A

#### Payment Timeout
- Window: 15 minutes from order creation
- Auto-cancel: If no payment received after 15 min, order moves to `cancelled`
- Notification: Email/SMS reminder at 5 min mark

#### Refund Policy
- **Before preparation**: 100% refund
- **During preparation or later**: 100% refund + 500 NGN cancellation fee (future)
- **After delivery**: Dispute resolution needed (future)

### 2.3 Delivery Policies

#### Service Areas
- Defined by `delivery_zones` table
- Zone = circular area with center (lat/lng) + radius_km
- Coordinates validated at checkout

#### Delivery Fee Rules
```
if order_subtotal >= 15000:
  delivery_fee = 0  // Free delivery
else:
  delivery_fee = 1500 NGN  // Flat rate for now
  // Future: Distance-based pricing
```

#### Delivery Window
- Target: 30-45 minutes from order confirmation
- Includes: Preparation (15-30 min) + Delivery (10-20 min)
- ETA calculation: preparation_time_minutes + estimated_delivery_10min

#### Rider Assignment
- Automatic: System assigns nearest available rider
- Manual: Admin can manually assign
- Reassignment: Allowed if rider cancels or is unresponsive

#### Special Conditions
- **Weather delays**: Manual rider note + customer notification
- **Address unavailable**: Rider contacts customer for directions
- **Customer unreachable**: After 3 contact attempts, order marked `delivery_failed`

---

## 3. Data Model & Storage

### 3.1 Core Tables

#### `orders`
```sql
orders (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL REFERENCES profiles(id),
  
  -- Pricing
  subtotal_amount DECIMAL(12,2),      -- raw sum of items
  delivery_fee DECIMAL(12,2),         -- 0 or 1500
  discount_amount DECIMAL(12,2),      -- new_cust + zone
  total_amount DECIMAL(12,2),         -- final charged
  currency TEXT DEFAULT 'NGN',
  
  -- Status
  status TEXT NOT NULL 
    CHECK (status IN (
      'pending_payment', 'payment_failed', 'confirmed', 
      'preparing', 'ready_for_pickup', 'on_the_way', 
      'delivered', 'completed', 'cancelled'
    )),
  
  -- Delivery
  delivery_address JSONB,             -- { street, city, zip, notes }
  delivery_lat DECIMAL(10,7),
  delivery_lng DECIMAL(10,7),
  delivery_zone_id UUID REFERENCES delivery_zones(id),
  
  -- Metadata
  promo_applied BOOLEAN DEFAULT false,
  notes TEXT,                         -- customer special requests
  admin_notes TEXT,                   -- kitchen/ops notes
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  payment_confirmed_at TIMESTAMPTZ,
  ready_at TIMESTAMPTZ,               -- when food is ready
  picked_up_at TIMESTAMPTZ,           -- when rider picked up
  delivered_at TIMESTAMPTZ,           -- when delivered
  completed_at TIMESTAMPTZ
)
```

#### `order_items`
```sql
order_items (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  menu_item_id UUID REFERENCES menu_items(id),  -- nullable for items removed from menu
  
  -- Snapshot at order time (in case menu item changes)
  item_name TEXT NOT NULL,
  item_description TEXT,
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price DECIMAL(12,2) NOT NULL,
  line_total DECIMAL(12,2),           -- quantity × unit_price
  
  -- Special requests
  special_instructions TEXT,          -- "no salt", "extra spicy", etc
  
  created_at TIMESTAMPTZ DEFAULT now()
)
```

#### `payments`
```sql
payments (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
  
  -- Payment method
  provider TEXT NOT NULL 
    CHECK (provider IN ('paystack', 'bank_transfer', 'cash')),
  method TEXT,                        -- 'card', 'transfer', 'ussd', 'cash'
  
  -- Status
  status TEXT NOT NULL 
    CHECK (status IN (
      'pending', 'processing', 'succeeded', 'failed', 'refunded'
    )),
  
  -- Amount
  amount DECIMAL(12,2) NOT NULL,
  currency TEXT DEFAULT 'NGN',
  
  -- Paystack specific
  reference TEXT UNIQUE,              -- Paystack transaction ref
  authorization_url TEXT,             -- Paystack checkout link
  access_code TEXT,                   -- Paystack access code
  
  -- Bank transfer specific
  receipt_url TEXT,                   -- S3/Supabase Storage path
  receipt_verified BOOLEAN DEFAULT false,
  verified_by_admin UUID REFERENCES profiles(id),
  verified_at TIMESTAMPTZ,
  
  -- Refund info
  refund_amount DECIMAL(12,2),
  refund_reason TEXT,
  refund_reference TEXT,              -- Paystack refund ref
  refunded_at TIMESTAMPTZ,
  
  -- Metadata
  ip_address TEXT,
  user_agent TEXT,
  
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
)
```

#### `delivery_events`
```sql
delivery_events (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  
  -- Event
  event_type TEXT NOT NULL 
    CHECK (event_type IN (
      'confirmed', 'preparing', 'ready', 'picked_up', 
      'on_route', 'arrived', 'delivered', 'cancelled'
    )),
  description TEXT,                   -- human readable
  
  -- Location
  latitude DECIMAL(10,7),
  longitude DECIMAL(10,7),
  address TEXT,                       -- "123 Main St, Lagos"
  
  -- Rider info
  rider_id UUID REFERENCES profiles(id),
  rider_name TEXT,
  rider_phone TEXT,
  
  -- Meta
  created_at TIMESTAMPTZ DEFAULT now()
)
```

#### `order_audit_log`
```sql
order_audit_log (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  
  old_status TEXT,
  new_status TEXT,
  changed_by UUID REFERENCES profiles(id),
  reason TEXT,
  
  created_at TIMESTAMPTZ DEFAULT now()
)
```

### 3.2 Indexes for Performance

```sql
-- Fast status queries (for dashboard, notifications)
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);

-- Fast payment lookups
CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_reference ON payments(reference);

-- Delivery tracking
CREATE INDEX idx_delivery_events_order_id ON delivery_events(order_id);
CREATE INDEX idx_delivery_events_created_at ON delivery_events(created_at DESC);

-- Audit trail
CREATE INDEX idx_audit_order_id ON order_audit_log(order_id);
```

---

## 4. Order Workflows

### 4.1 Standard Happy Path

```
1. BROWSE & CART
   ├─ Customer views /menu
   ├─ Adds items to localStorage cart
   └─ Sees subtotal + delivery estimate

2. CHECKOUT
   ├─ POST /api/v1/orders
   ├─ Server validates:
   │  ├─ Items still available
   │  ├─ Delivery coordinates in service area
   │  ├─ Customer is authenticated
   │  └─ Order >= 2000 NGN minimum
   ├─ Creates order row (status: pending_payment)
   ├─ Creates order_items rows
   └─ Returns orderId + payment details

3. PAYMENT (Paystack)
   ├─ POST /api/v1/payments/paystack/initialize
   ├─ Server creates payment row (status: pending)
   ├─ Paystack API returns authorization_url
   ├─ Frontend redirects to Paystack checkout
   ├─ Customer enters card details
   └─ Paystack calls webhook: POST /api/v1/payments/paystack/webhook

4. PAYMENT CONFIRMATION
   ├─ Server verifies webhook signature
   ├─ Queries Paystack API for transaction status
   ├─ Updates payment row (status: succeeded)
   ├─ Updates order row (status: confirmed, payment_confirmed_at)
   ├─ Sends confirmation email/SMS to customer
   └─ Kitchen receives order notification

5. KITCHEN PREPARES
   ├─ Staff marks order as 'preparing'
   ├─ Creates delivery_event (event_type: preparing)
   ├─ Plates food
   └─ Marks order as 'ready_for_pickup' (ready_at timestamp)

6. RIDER ASSIGNMENT & PICKUP
   ├─ System assigns nearest rider
   ├─ Rider sees order in app/dashboard
   ├─ Rider arrives at restaurant
   ├─ Confirms pickup (picked_up_at)
   ├─ Creates delivery_event (event_type: picked_up)
   └─ Order moves to 'on_the_way'

7. DELIVERY
   ├─ Rider location updates via GPS (optional realtime)
   ├─ Customer sees live tracking
   ├─ Rider arrives at destination
   ├─ Creates delivery_event (event_type: arrived)
   ├─ Rider contacts customer
   ├─ Customer receives & confirms
   └─ Rider marks delivered (delivered_at)

8. COMPLETION
   ├─ Order moves to 'delivered'
   ├─ Customer sees rating prompt
   ├─ Customer submits rating (1-5 stars)
   ├─ System creates review record
   ├─ Order moves to 'completed'
   └─ End of lifecycle
```

### 4.2 Bank Transfer Path

Same as above until PAYMENT:

```
3. PAYMENT (Bank Transfer)
   ├─ Customer selects "Bank Transfer" at checkout
   ├─ Server creates payment row (status: pending)
   ├─ Server returns FoodyBites bank details + reference
   ├─ Customer transfers amount to account
   ├─ Customer uploads bank receipt screenshot
   ├─ POST /api/v1/payments/verify-receipt
   ├─ File saved to Supabase Storage
   └─ Admin dashboard notified of pending verification

4. ADMIN VERIFICATION
   ├─ Admin reviews receipt
   ├─ Confirms transfer amount matches order total
   ├─ Confirms reference contains order ID
   ├─ PATCH /api/v1/payments/{paymentId}/verify
   ├─ Server updates payment (status: succeeded, verified_by_admin, verified_at)
   ├─ Server updates order (status: confirmed)
   └─ Kitchen receives order notification
   
   (Then continues from step 5: KITCHEN PREPARES)
```

### 4.3 Cancellation Paths

#### Customer-Initiated Cancellation

```
Timeline 1: Before Payment (pending_payment state)
├─ DELETE /api/v1/orders/{orderId}
├─ Server marks order as 'cancelled'
├─ No refund needed (no payment made)
└─ Order removed from customer history (soft delete flag)

Timeline 2: After Payment, Before Preparation
├─ DELETE /api/v1/orders/{orderId}
├─ Server verifies status is 'confirmed' (no refund on other states)
├─ Records cancellation reason
├─ Initiates refund via Paystack API
├─ Updates payment row (status: refunded)
├─ Creates delivery_event (event_type: cancelled)
├─ Sends refund confirmation email
└─ Order moves to 'cancelled'

Timeline 3: During Preparation or Later
├─ Can still cancel via support ticket (not API)
├─ Admin approves refund manually
├─ Same process as Timeline 2 but with fee deduction
```

#### Admin-Initiated Cancellation
```
├─ PATCH /api/v1/orders/{orderId}/admin-cancel
├─ Requires admin auth + reason
├─ If payment succeeded: refunds 100%
├─ Updates order_audit_log with admin ID + reason
├─ Sends apology + refund confirmation to customer
└─ Order moves to 'cancelled'
```

---

## 5. API Contracts (Order Endpoints)

### 5.1 Create Order

```
POST /api/v1/orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "items": [
    {
      "menuItemId": "uuid",
      "quantity": 2,
      "specialInstructions": "no salt"
    }
  ],
  "deliveryLat": 6.5244,
  "deliveryLng": 3.3792,
  "deliveryAddress": {
    "street": "123 Main St",
    "city": "Lagos",
    "zipCode": "100001",
    "notes": "Blue gate"
  },
  "promoCode": "FIRST10" // optional
}

Response 201:
{
  "success": true,
  "data": {
    "orderId": "uuid",
    "status": "pending_payment",
    "subtotalAmount": 13000,
    "deliveryFee": 1500,
    "discountAmount": 1300,
    "totalAmount": 13200,
    "createdAt": "2026-04-17T10:30:00Z"
  }
}
```

### 5.2 Get Order Details

```
GET /api/v1/orders/{orderId}
Authorization: Bearer <token>

Response 200:
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "on_the_way",
    "subtotalAmount": 13000,
    "deliveryFee": 0,
    "discountAmount": 1300,
    "totalAmount": 11700,
    "deliveryAddress": { ... },
    "items": [
      {
        "itemName": "Jollof Rice",
        "quantity": 2,
        "unitPrice": 6500,
        "lineTotal": 13000
      }
    ],
    "payment": {
      "status": "succeeded",
      "provider": "paystack",
      "amount": 11700
    },
    "events": [
      {
        "eventType": "confirmed",
        "description": "Order confirmed by kitchen",
        "createdAt": "2026-04-17T10:35:00Z"
      }
    ],
    "eta": 15  // minutes remaining
  }
}
```

### 5.3 List Customer Orders

```
GET /api/v1/orders?status=pending_payment&limit=10&offset=0
Authorization: Bearer <token>

Response 200:
{
  "success": true,
  "data": [
    { ...order details... }
  ],
  "pagination": {
    "total": 25,
    "limit": 10,
    "offset": 0
  }
}
```

### 5.4 Track Order (Real-time)

```
GET /api/v1/orders/{orderId}/tracking
Authorization: Bearer <token>

Response 200:
{
  "success": true,
  "data": {
    "orderId": "uuid",
    "status": "on_the_way",
    "eta": 12,  // minutes
    "rider": {
      "name": "Chidi Obi",
      "phone": "+2348012345678",
      "rating": 4.8,
      "vehicle": "Bike"
    },
    "currentLocation": {
      "lat": 6.5250,
      "lng": 3.3800,
      "address": "On Lekki-Epe Expressway"
    },
    "events": [
      {
        "type": "picked_up",
        "time": "2026-04-17T10:45:00Z"
      }
    ]
  }
}
```

### 5.5 Cancel Order

```
DELETE /api/v1/orders/{orderId}
Authorization: Bearer <token>

Body: { "reason": "Customer decision" }

Response 200:
{
  "success": true,
  "message": "Order cancelled. Refund initiated.",
  "data": {
    "orderId": "uuid",
    "status": "cancelled",
    "refundAmount": 11700,
    "refundReference": "paystack_ref_xyz"
  }
}
```

---

## 6. Business Constraints & Validations

### 6.1 Order Validation

| Rule | Enforcement | Error Code |
|------|-------------|-----------|
| Items exist in menu | At checkout | MENU_ITEMS_CHANGED |
| Item quantities > 0 | At checkout | INVALID_QUANTITY |
| Order subtotal >= 2000 NGN | At checkout | MINIMUM_ORDER_NOT_MET |
| Delivery coords in service area | At checkout | DELIVERY_OUTSIDE_SERVICE |
| Customer authenticated | Middleware | UNAUTHORIZED |
| Order not duplicated in 60s | API deduplication | DUPLICATE_REQUEST |

### 6.2 Payment Validation

| Rule | Enforcement | Error Code |
|------|-------------|-----------|
| Payment amount = order total | Server calculation | PAYMENT_MISMATCH |
| Payment provider valid | Enum check | INVALID_PROVIDER |
| Paystack API response valid | Webhook signature | INVALID_SIGNATURE |
| Bank transfer receipt uploaded | File upload check | RECEIPT_REQUIRED |

### 6.3 State Transition Validation

```javascript
// Only allowed transitions
const ALLOWED_TRANSITIONS = {
  'pending_payment': ['payment_failed', 'confirmed', 'cancelled'],
  'payment_failed': ['pending_payment', 'cancelled'],
  'confirmed': ['preparing', 'cancelled'],
  'preparing': ['ready_for_pickup', 'cancelled'],
  'ready_for_pickup': ['on_the_way'],
  'on_the_way': ['delivered'],
  'delivered': ['completed'],
  'completed': [],  // terminal
  'cancelled': []   // terminal
}

// Any state can go to cancelled (except cancelled/completed)
```

---

## 7. Performance & Scalability Considerations

### 7.1 Read Optimization
- Paginate order lists (default 10, max 50 per page)
- Use indexes on `customer_id`, `status`, `created_at`
- Cache menu item details in order_items snapshot

### 7.2 Write Consistency
- Order creation is transactional (order + items + audit in one tx)
- Payment status updates are idempotent (webhook can retry)
- Use optimistic locking for status transitions (version field)

### 7.3 Real-time Tracking
- Use Supabase Realtime subscriptions (not polling)
- Limit rider location updates to 10s intervals
- Cache rider location in Redis for 30s

### 7.4 Notification Queue
- Async email/SMS via job queue (Bull/BullMQ)
- Retry failed notifications 3x with exponential backoff
- Log all notification attempts in audit table

---

## 8. Security & Compliance

### 8.1 Authorization
- No order access across customers (verify `customer_id == req.user.id`)
- Admin endpoints require role check: `role == 'admin'`
- Refund endpoints require admin role

### 8.2 Payment Security
- PCI-DSS: Never store full card details (Paystack escrow)
- JWT: All endpoints protected by `authMiddleware`
- Webhook verification: Validate Paystack signature before trusting

### 8.3 Data Privacy
- Soft-delete sensitive fields (receipt URLs stay, customer phone redacted after 30 days)
- Audit log all sensitive changes (refunds, payment updates)
- Encrypt delivery address in transit (HTTPS enforced)

### 8.4 Rate Limiting
- Order creation: 3 per minute per user (prevent spam)
- Payment initialization: 10 per minute per user
- Admin endpoints: 100 per minute per user

---

## 9. Reporting & Analytics

### 9.1 Business Metrics
- Orders per day / week / month
- Revenue by payment method
- Average order value (AOV)
- Cancellation rate by reason

### 9.2 Operational Metrics
- Average preparation time
- Average delivery time
- On-time delivery %
- Rider utilization %

### 9.3 Customer Metrics
- Repeat order rate
- Customer lifetime value (CLV)
- NPS (Net Promoter Score)
- Discount impact on AOV

---

## 10. Implementation Roadmap

### Phase 3 ✅ (Complete)
- [x] Order creation with items
- [x] Basic order retrieval
- [x] Order status tracking
- [x] Delivery event logging

### Phase 4 (Next)
- [ ] Paystack payment integration
- [ ] Bank transfer receipt upload & verification
- [ ] Webhook handling
- [ ] Refund processing

### Phase 5
- [ ] Real-time delivery tracking (Supabase Realtime)
- [ ] Rider assignment algorithm
- [ ] SMS/Email notifications
- [ ] Admin dashboard

### Phase 6
- [ ] Review & rating system
- [ ] Advanced analytics & reporting
- [ ] Promo code engine
- [ ] Distance-based delivery pricing

### Phase 7+
- [ ] Multi-restaurant support
- [ ] Subscription plans
- [ ] AI-driven demand forecasting
- [ ] Inventory management

---

## 11. Known Gaps & Future Considerations

### To Be Designed
- [ ] Partial refund policy (for damaged items)
- [ ] Dispute resolution workflow
- [ ] Multi-language support for order communications
- [ ] Seasonal pricing/surge pricing
- [ ] Schedule future orders (pre-order)
- [ ] Group orders / shared carts
- [ ] Bundle offers
- [ ] Loyalty points system
- [ ] Two-factor auth for high-value orders

### Technical Debt
- [ ] Implement order versioning for audit trail
- [ ] Add pessimistic locking for concurrent updates
- [ ] Set up order cleanup job for stale pending_payment orders
- [ ] Implement circuit breaker for Paystack API calls
- [ ] Add order export (CSV/PDF) feature

---

## Summary

This order management architecture provides:
1. **Clear state machine** with all transitions defined
2. **Comprehensive pricing rules** for discounts and fees
3. **Flexible payment methods** (Paystack + Bank Transfer)
4. **Audit trail** for compliance and debugging
5. **Scalable data model** with proper indexing
6. **Security-first design** with auth, encryption, and validation
7. **Real-time tracking** foundation with delivery events

Use this as your north star for implementation. Any ambiguity should reference this document first.
