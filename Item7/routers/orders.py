import uuid
import traceback
from fastapi import APIRouter, HTTPException, status
import httpx
from schemas import FrontendPayRequest
from database import supabase
from config import settings
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["Payment Initialization Pipeline"])

@router.post("/pay")
async def initialize_payment(payload: FrontendPayRequest):
    # Add the delivery/convenience fee on the server so the frontend cannot alter it.
    calculated_total = float(payload.amount) + 150
    try:
        # Generate a unique reference that ties the pending order to the payment session.
        tx_ref = f"order-{uuid.uuid4().hex[:8]}-{int(uuid.uuid4().time_low)}"

        # Shape the request into the exact column names expected by Supabase.
        db_payload = {
            "name": payload.name,
            "phone": payload.phone,
            "matricNumber": payload.matricNumber,
            "address": payload.address,
            "roomNumber": payload.roomNumber,
            "orderDetails": payload.orderDetails,
            "amountpaid": calculated_total,
            "tx_ref": tx_ref,
            "status": "pending",
            "email": payload.email
        }

        # Save the order before contacting the payment gateway.
        print("DEBUG: Attempting to insert into Supabase...")
        db_response = supabase.table("orders").insert(db_payload).execute()
        print("DEBUG: Supabase insertion successful!")

        # Build the Flutterwave payment payload with customer-facing details.
        flutterwave_api_url = "https://api.flutterwave.com/v3/payments"
        headers = {
            "Authorization": f"Bearer {settings.FW_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        flutterwave_payload = {
            "tx_ref": tx_ref,
            "amount": calculated_total,
            "currency": "NGN",
            "redirect_url": "https://item7cu.vercel.app/",
            "customer": {
                "name": payload.name,
                "phone": payload.phone,
                "email": payload.email,
            },
            # Extra order data goes into meta because the gateway customer block is limited.
            "meta": {
                "Matric Number": payload.matricNumber,
                "Delivery Room": payload.roomNumber,
                "Delivery Hall/Address": payload.address,
            },
            "payment_options": "card, ussd, banktransfer, opay",
            "customizations": {
                "title": "Item 7 Meals",
                "description": f"Food: NGN {payload.amount} | Convenience Fee: NGN 150"
            }
        }

        # Ask Flutterwave for a hosted checkout link.
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
        # Keep the full traceback in the terminal during development.
        print("\n💥!!! CRITICAL BACKEND EXCEPTION DETECTED !!!💥")
        traceback.print_exc()
        print("💥!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!💥\n")
        
        # Return a clean 500 response to the client.
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

@router.head("/health", status_code=status.HTTP_200_OK, tags=["System Health"])
async def health_check_head():
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
