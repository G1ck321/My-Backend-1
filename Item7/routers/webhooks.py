from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks, status
import httpx
from database import supabase
from config import settings
from datetime import datetime, timezone
import resend

router = APIRouter(prefix="/webhooks", tags=["Third-Party Security Webhooks"])

# Initialize the Resend Master Token
resend.api_key = settings.RESEND_API_KEY

# ==========================================
# EMAIL DISPATCH HELPER
# ==========================================
def send_email_order_receipt(order_info: dict):
    """Fires a structured HTML transactional report to the manager's inbox"""
    name = order_info.get('name', 'N/A')
    details = order_info.get('orderDetails', 'N/A')
    amount = order_info.get('amountpaid', '0.0')
    tx_ref = order_info.get('tx_ref', 'N/A')
    matric = order_info.get("matricNumber","N/A")
    phone_num = order_info.get("number", "N/A")

    html_content = f"""
    <h3>🔔 Item 7 Management Dashboard</h3>
    <p>A new payment has been fully confirmed on the server.</p>
    <hr />
    <p><strong>Customer:</strong> {name}</p>
    <p><strong>Order Details:</strong><br />{details.replace('\n', '<br />')}</p>
    <p><strong>Amount Cleared:</strong> NGN {amount}</p>
    <p><strong>Transaction Reference:</strong> <code>{tx_ref}</code></p>
    <p><strong>Matric No:</strong> NGN {matric}</p>
    <p><strong>Phone Number:</strong> NGN {phone_num}</p>
    <hr />
    """

    try:
        # If using Resend's free tier, the "from" email must use "onboarding@resend.dev"
        # and "to" must be the email address you signed up to Resend with!
        resend.Emails.send({
            "from": "Item7Orders <onboarding@resend.dev>",
            "to": [settings.OWNER_EMAIL_ADDRESS],
            "subject": f"🔥 New Paid Order - NGN {amount}",
            "html": html_content,
        })
        print(f"DEBUG: Resend transaction alert sent successfully for {tx_ref}")
    except Exception as e:
        print(f"ERROR: Resend notification failed: {str(e)}")

# ==========================================
# 1. THE NEW PULL-BASED DASHBOARD HELPERS
# ==========================================

def get_todays_orders_from_supabase():
    """Queries Supabase for paid orders matching today's date"""
    # Calculates the start of today (UTC)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    response = supabase.table("orders") \
        .select("*") \
        .eq("status", "paid") \
        .gte("created_at", today_start.isoformat()) \
        .order("created_at", desc=False) \
        .execute()
        
    return response.data

def compile_orders_dashboard(orders_list: list) -> str:
    """Formats raw database rows into a single, clean text report"""
    if not orders_list:
        return "🍽️ **ITEM 7 DASHBOARD**\n\nNo paid orders logged yet for today. Keep pushing!"
        
    total_revenue = sum(order.get('amountpaid', 0.0) for order in orders_list)
    
    dashboard_text = (
        "📊 **ITEM 7 LIVE MANAGEMENT REPORT**\n"
        f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"✅ Total Paid Orders: {len(orders_list)}\n"
        f"💰 Total Revenue: NGN {total_revenue:,.2f}\n"
        "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n\n"
    )
    
    for i, order in enumerate(orders_list, 1):
        name = order.get('name', 'N/A')
        room = order.get('roomNumber', 'N/A')
        hall = order.get('address', 'N/A')
        details = order.get('orderDetails', 'N/A').replace('\n', ', ')
        ref = order.get('tx_ref', 'N/A')[-6:] # Grab last 6 chars of ref
        matric = order.get("matricNumber","N/A")
        phone_num = order.get("number", "N/A")
        
        dashboard_text += (
            f"{i}. 📦 **Order #{ref}** - {name}\n"
            f"   📍 {hall} (Room {room})\n"
            f"   🍔 {details}\n"
            f"Matric No: {matric}"
            f"Phone Number: {phone_num}"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        )
        
    return dashboard_text

async def send_telegram_notification(order_info: dict):
    """
    Asynchronous non-blocking network worker thread that formats data
    and fires it down into the Telegram Admin channel.
    """

    # Safe fallback data extraction using exact dict keys from your DB log
    name = order_info.get('name', 'N/A')
    matric = order_info.get('matricNumber', 'N/A')
    phone = order_info.get('phone', 'N/A')
    address = order_info.get('address', 'N/A')
    room = order_info.get('roomNumber', 'N/A')
    # Note the camelCase 'orderDetails' matching your Supabase log!
    details = order_info.get('orderDetails', 'N/A') 
    amount = order_info.get('amountpaid', '0.0')
    tx_ref = order_info.get('tx_ref', 'N/A')

    # Standard, pure text string (No HTML tags like <b> or <i>)
    message = (
        "🔔 ITEM 7 NEW ORDER 🔔\n\n"
        f"Student Name: {name}\n"
        f"Matric Number: {matric}\n"
        f"Phone: {phone}\n"
        f"Hall: {address} (Room: {room})\n"
        f"Items: {details}\n"
        f"Amount: NGN {amount}\n"
        f"Tx-Ref: {tx_ref}"
    )
    
    telegram_api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # 🌟 CRITICAL: Explicitly ensure "parse_mode" is NOT in this payload dictionary!
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": ""  # Passing an empty string completely disables HTML/Markdown parsing
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(telegram_api_url, json=payload, timeout=10.0)
            print(f"DEBUG: Telegram API response code: {response.status_code}")
            print(f"DEBUG: Telegram API response body: {response.text}")
            response.raise_for_status()
        except httpx.HTTPError:
            # Silent logging on network failure so API endpoint never crashes for external gateway
            print(f"CRITICAL: Failed dispatching notification for reference {order_info.get('tx_ref')}")

@router.post("/flutterwave")
async def handle_flutterwave_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    verif_hash: str = Header(None, alias="verif-hash")
):
    """
    Highly secure, signature-verified webhook handler.
    Listens directly to server updates from Flutterwave.
    """
    # 1. Enforce Webhook Header signature validation
    if not verif_hash or verif_hash != settings.FLW_SECRET_HASH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature validation handshake mismatch."
        )

    # 2. Extract payload body
    payload = await request.json()
    
    # Check if the payment status event payload is explicitly successful
    if payload.get("status") == "successful" or payload.get("data", {}).get("status") == "successful":
        
        # Flatten structure variations depending on webhook charge event type schemas
        data_block = payload.get("data", payload)
        tx_ref = data_block.get("tx_ref")
        
        # 3. Guard Against Duplication (Idempotency check)
        existing_order = supabase.table("orders").select("*").eq("tx_ref", tx_ref).execute()
        
        if not existing_order.data:
            raise HTTPException(status_code=404, detail="Order reference matching tx_ref not found.")
            
        order_record = existing_order.data[0]
        
        # If order was already marked paid by a previous duplicate webhook retry event, exit early safely
        if order_record.get("status") == "paid":
            return {"status": "ignored", "reason": "Already processed transaction pattern."}

        # 4. Atomic Database Updates via Supabase client
        updated_order = supabase.table("orders").update({"status": "paid"}).eq("tx_ref", tx_ref).execute()
        
        # 🌟 RIGHT HERE: Once your code successfully updates the database row to "paid"
        # Check if database update was successful
        if updated_order.data:
            order_record = updated_order.data[0]
            
            # 🌟 FIXED: Using background_tasks keeps the webhook lightning-fast 
            # and prevents runtime async/sync errors.
            background_tasks.add_task(send_email_order_receipt, order_record)
        else:
            print("DEBUG: Supabase update failed or returned empty data.")

    return {"status": "acknowledged"}

# ==========================================
# 3. THE NEW INCOMING TELEGRAM ENDPOINT
# ==========================================
@router.post("/telegram")
async def handle_telegram_incoming_traffic(request: Request):
    """Listens for inbound group or DM chat interactions from Telegram"""
    payload = await request.json()
    
    if "message" in payload and "text" in payload["message"]:
        chat_id = payload["message"]["chat"]["id"]
        incoming_text = payload["message"]["text"].strip()
        
        # If the owner types /orders, fetch data and respond instantly
        if incoming_text.startswith("/orders"):
            raw_orders = get_todays_orders_from_supabase()
            final_report = compile_orders_dashboard(raw_orders)
            
            telegram_api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            response_payload = {
                "chat_id": chat_id,
                "text": final_report,
                "parse_mode": "Markdown" # Renders the asterisks as beautiful bold text labels
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(telegram_api_url, json=response_payload)
                
    return {"status": "ok"}