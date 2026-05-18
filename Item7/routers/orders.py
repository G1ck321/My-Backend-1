import uuid
import traceback  # 👈 Added to print the full error layout
from fastapi import APIRouter, HTTPException, status
import httpx
from schemas import FrontendPayRequest
from database import supabase
from config import settings
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["Payment Initialization Pipeline"])

@router.post("/pay")
async def initialize_payment(payload: FrontendPayRequest):
    try:
        # 1. Generate unique reference tracking tokens
        tx_ref = f"order-{uuid.uuid4().hex[:8]}-{int(uuid.uuid4().time_low)}"
        
        # 2. Map data to your Supabase schema format
        db_payload = {
            "name": payload.name,
            "phone": payload.phone,
            "matricNumber": payload.matricNumber,
            "address": payload.address,        
            "roomNumber": payload.roomNumber,  
            "orderDetails": payload.orderDetails,
            "amountpaid": payload.amount,
            "tx_ref": tx_ref,
            "status": "pending"
        }
        
        # 3. Attempt Database Write
        print("DEBUG: Attempting to insert into Supabase...")
        db_response = supabase.table("orders").insert(db_payload).execute()
        print("DEBUG: Supabase insertion successful!")

        # 4. Attempt Flutterwave Call
        flutterwave_api_url = "https://api.flutterwave.com/v3/payments"
        headers = {
            "Authorization": f"Bearer {settings.FW_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        customer_email = payload.email if payload.email else f"{payload.phone}@customer.com"
        
        flutterwave_payload = {
            "tx_ref": tx_ref,
            "amount": payload.amount,
            "currency": "NGN",
            "redirect_url": "http://localhost:3000/", 
            "customer": {
                "email": customer_email,
                "phone_number": payload.phone,
                "name": payload.name
            },
            "customizations": {
                "title": "Your Store Automation Engine",
                "description": "Secure payment confirmation processing."
            }
        }
        
        print("DEBUG: Reaching out to Flutterwave...")
        async with httpx.AsyncClient() as client:
            response = await client.post(flutterwave_api_url, json=flutterwave_payload, headers=headers)
            flw_data = response.json()
            
            if response.status_code == 200 and flw_data.get("status") == "success":
                hosted_checkout_url = flw_data.get("data", {}).get("link")
                print("DEBUG: Checkout link generated successfully!")
                return {"checkout_url": hosted_checkout_url}
            else:
                print(f"DEBUG: Flutterwave rejected request with status {response.status_code}: {flw_data}")
                raise HTTPException(status_code=400, detail=f"Gateway Error: {flw_data.get('message')}")
                
    except Exception as e:
        # 🚨 This prints the exact traceback down to the line number in your terminal terminal window
        print("\n💥!!! CRITICAL BACKEND EXCEPTION DETECTED !!!💥")
        traceback.print_exc()
        print("💥!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!💥\n")
        
        # Send the exact text explanation back to the client response payload
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crash details: {str(e)}"
        )
    
@router.get("/health", status_code=status.HTTP_200_OK, tags=["System Health"])
async def health_check():
    """
    Lightweight system performance & availability monitor target.
    Used by UptimeRobot to prevent Render containers from entering sleep states.
    """
    return JSONResponse(
        content={
            "status": "operational",
            "environment": "development",
            "message": "Item 7 API system is running smoothly."
        }
    )
