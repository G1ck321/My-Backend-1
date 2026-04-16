-- FoodyBites Supabase schema starter

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  full_name text not null,
  phone_number text,
  role text not null default 'customer',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.menu_categories (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  slug text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.menu_items (
  id uuid primary key default gen_random_uuid(),
  category_id uuid references public.menu_categories (id) on delete set null,
  name text not null,
  description text,
  price numeric(12, 2) not null,
  currency text not null default 'NGN',
  image_url text,
  is_available boolean not null default true,
  is_nigerian_snack boolean not null default false,
  preparation_time_minutes int not null default 30,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles (id) on delete cascade,
  status text not null default 'pending',
  total_amount numeric(12, 2) not null default 0,
  delivery_fee numeric(12, 2) not null default 0,
  discount_amount numeric(12, 2) not null default 0,
  delivery_address jsonb not null,
  delivery_lat numeric(10, 7),
  delivery_lng numeric(10, 7),
  promo_applied boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders (id) on delete cascade,
  menu_item_id uuid not null references public.menu_items (id),
  quantity int not null check (quantity > 0),
  unit_price numeric(12, 2) not null,
  created_at timestamptz not null default now()
);

create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders (id) on delete cascade,
  provider text not null,
  status text not null default 'pending',
  amount numeric(12, 2) not null,
  reference text unique,
  receipt_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.delivery_events (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.orders (id) on delete cascade,
  status text not null,
  location_label text,
  latitude numeric(10, 7),
  longitude numeric(10, 7),
  created_at timestamptz not null default now()
);

create table if not exists public.customer_reminders (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references public.profiles (id) on delete cascade,
  channel text not null check (channel in ('email', 'sms', 'both')),
  reminder_type text not null,
  next_send_at timestamptz not null,
  sent_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.delivery_zones (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  center_lat numeric(10, 7) not null,
  center_lng numeric(10, 7) not null,
  radius_km numeric(10, 2) not null,
  discount_percentage numeric(5, 2) not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists idx_orders_customer_id on public.orders (customer_id);
create index if not exists idx_orders_status on public.orders (status);
create index if not exists idx_menu_items_category_id on public.menu_items (category_id);
create index if not exists idx_delivery_events_order_id on public.delivery_events (order_id);