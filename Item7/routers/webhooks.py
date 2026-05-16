from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks, status
import httpx
from database import supabase
from config import settings

router = APIRouter(prefix="/webhooks", tags=["Third-Party Security Webhooks"])

async def send_telegram_notification(order_info: dict):
    """
    Asynchronous non-blocking network worker thread that formats data
    and fires it down into the Telegram Admin channel.
    """
    message = (
        f"🚨 NEW PAID ORDER RECEIVED</b> 🚨\n\n"
        f"👤 Customer: {order_info.get('name')}\n"
        f"📞 Phone: {order_info.get('phone')}\n"
        f"📞 MATRIC No: {order_info.get('matricno')}\n"
        f"📍 Hall: {order_info.get('hall')}, Room No {order_info.get('roomno')}\n"
        f"🛍️ Items Ordered:\n{order_info.get('orderdetails')}\n\n"
        f"💰 Paid Amount: NGN {order_info.get('amountpaid')}\n"
        f"🔖 Ref IDs: <code>{order_info.get('tx_ref')}</code>"
        # -----------------------
        # f"🔔 ITEM 7 NEW ORDER 🔔\n\n"
        # f"Customer: {order_info.get('name')}\n"
        # f"Phone: {order_info.get('phone')}\n"
        # f"Location: {order_info.get('location')} (House: {order_info.get('housenumber')})\n"
        # f"Items: {order_info.get('orderdetails')}\n"
        # f"Amount: NGN {order_info.get('amountpaid')}\n"
        # f"Ref: {order_info.get('tx_ref')}"
    )
    
    telegram_api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
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
async def process_flutterwave_payment_webhook(
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

    # 2. Extract payload payload body
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
        print(f"DEBUG: Webhook verified for ref {tx_ref}. Updating DB status...")
        updated_order = supabase.table("orders").update({"status": "paid"}).eq("tx_ref", tx_ref).execute()
        
        if updated_order.data:
            order_data = updated_order.data[0]
            print(f"DEBUG: DB updated successfully to paid! Data: {order_data}")
            
            # 🌟 BYPASS BACKGROUND WORKER: Run it immediately in-line to force error visibility
            print("DEBUG: Invoking Telegram dispatch function...")
            await send_telegram_notification(order_data)
        else:
            print("DEBUG: Supabase update failed or returned empty data.")

    return {"status": "acknowledged"}