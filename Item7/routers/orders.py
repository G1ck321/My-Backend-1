import uuid
import traceback
from fastapi import APIRouter, HTTPException, status
import httpx
from schemas import FrontendPayRequest
from database import supabase
from config import settings
from fastapi.responses import JSONResponse
    # Add the delivery/convenience fee on the server so the frontend cannot alter it.

router = APIRouter(prefix="/api", tags=["Payment Initialization Pipeline"])
        # Generate a unique reference that ties the pending order to the payment session.
@router.post("/pay")
async def initialize_payment(payload: FrontendPayRequest):
        # Shape the request into the exact column names expected by Supabase.
        # 1. Generate unique reference tracking tokens
        tx_ref = f"order-{uuid.uuid4().hex[:8]}-{int(uuid.uuid4().time_low)}"

        
            "address": payload.address,
            "roomNumber": payload.roomNumber,
            "name": payload.name,
            "phone": payload.phone,
            "matricNumber": payload.matricNumber,
            "address": payload.address,        
            "roomNumber": payload.roomNumber,  
            "orderDetails": payload.orderDetails,
            "amountpaid": calculated_total,
        # Save the order before contacting the payment gateway.
            "status": "pending",
            "email": payload.email
        }
        
        # Build the Flutterwave payment payload with customer-facing details.
        print("DEBUG: Attempting to insert into Supabase...")
        db_response = supabase.table("orders").insert(db_payload).execute()
        print("DEBUG: Supabase insertion successful!")

        # 4. Attempt Flutterwave Call
        headers = {
            "Authorization": f"Bearer {settings.FW_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        #customer_email = payload.email if payload.email else f"{payload.phone}@customer.com"
            "redirect_url": "https://item7cu.vercel.app/",
        flutterwave_payload = {
            "amount": calculated_total,
            "currency": "NGN",
            "redirect_url": "https://item7cu.vercel.app/", 
            "customer": {
            # Extra order data goes into meta because the gateway customer block is limited.
            "meta": {
                "Matric Number": payload.matricNumber,
                "Delivery Room": payload.roomNumber,
                "Delivery Hall/Address": payload.address,
            },
            "payment_options": "card, ussd, banktransfer, opay",
        "Delivery Hall/Address": payload.address
    },
            "payment_options": "card, ussd, banktransfer, opay",
#enables multiple payment options 
            "customizations": {
                "title": "Item 7 Meals",
        # Ask Flutterwave for a hosted checkout link.
                "description": f"Food: NGN {payload.amount} | Convenience Fee: NGN 150"
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
