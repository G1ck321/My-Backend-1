import requests

# 1. Your live Render webhook endpoint URL
URL = "https://my-backend-1-s57s.onrender.com/webhooks/flutterwave"

# 2. Your security handshake headers
# Replace this with the exact secret hash string you put in your Render env variables!
HEADERS = {
    "verif-hash": "",
    "Content-Type": "application/json"
}

# 3. The mock Flutterwave payload
# ⚠️ CRITICAL: Make sure this tx_ref matches a row in your Supabase 'orders' table 
# that is currently set to 'pending'!
PAYLOAD = {
    "event": "charge.completed",
    "status": "successful",
    "data": {
        "status": "successful",
        "id": 123456,
        "tx_ref": "order-277b84b4-3939044385",  # Replace with your actual pending tx_ref
        "amount": 2500,
        "currency": "NGN"
    }
}

print("🚀 Firing mock Flutterwave webhook to Render...")

try:
    # Send the POST request with the JSON data and secure headers
    response = requests.post(URL, json=PAYLOAD, headers=HEADERS, timeout=10.0)
    
    print(f"🔹 Server Status Code: {response.status_code}")
    print(f"🔹 Server Response: {response.json()}")
    
    if response.status_code == 200:
        print("\n✅ Success! Check your Supabase database to see if the status changed to 'paid'.")
        print("📧 Check your Resend email inbox (and Spam folder) for the manager receipt!")
    else:
        print("\n❌ The server rejected the request. Double-check your verif-hash and tx_ref.")

except Exception as e:
    print(f"\n💥 Network Error: Could not connect to your server. {str(e)}")