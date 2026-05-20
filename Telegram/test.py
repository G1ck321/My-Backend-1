import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load your local .env file configurations
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def test_telegram_dispatch():
    print("🚀 Initiating isolated Telegram Bot verification...")
    print(f"Using Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"Target Chat ID: {TELEGRAM_CHAT_ID}")
    
    # Simple, clean string payload to guarantee no HTML parsing rejections
    message = (
        "🔔 ITEM 7 BOT TEST SUCCESSFUL 🔔\n\n"
        "Your FastAPI script is talking to Telegram perfectly!\n"
        "If you see this, your credentials match."
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                print("\n🎉 SUCCESS! Check your Telegram app right now.")
            else:
                print("\n❌ FAILED: Telegram received the request but rejected it.")
        except Exception as e:
            print(f"\n💥 CRITICAL SYSTEM ERROR: {str(e)}")

# Execute the asynchronous loop runner
if __name__ == "__main__":
    asyncio.run(test_telegram_dispatch())