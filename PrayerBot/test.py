import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import Client, create_client
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
import uvicorn

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------- Supabase Client ----------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- FastAPI App (minimal) ----------
app = FastAPI()


# --------- Connectivity Check ---------
@app.head("/health")
async def health():
    return {"status": "ok"}

def get_prayers(
    update: Optional[Update] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None,
):
    # Execute query
    # response = supabase.table("prayers").select("prayer_number","description", "prayer").execute()
    
    #     # Extract records list from response.data
    # rows = response.data
    # text = "All prayers "
    
    # for row in rows:
    #     des = row.get("description", "")
    #     num = row.get("prayer_number", "")
    #     prayer = row.get("prayer", "")    

    #     if prayer.endswith("."):
    #         text += f"\n{num}. {des.title()}:\n{prayer}\n\n"
    #     else:
    #         text += f"\n{num}. {des.title()}:\n{prayer}.\n\n"

    # print(text)

    # # Send message to Telegram if triggered by a command
    # if update and update.message:
    #      update.message.reply_text(text)

    # return text
    resp = supabase.table("prayers")\
        .select("prayer","description")\
        .eq("prayer_number",2)\
        .eq("active",True)\
        .execute()

    prayer = resp.data or []
    print("Prayer",prayer)
    if not prayer:
        print(
            f"No Prayer found with the number {2}"            )
        return
    prayer = prayer[0]

    text = f"\n{2}. {prayer['description'].title()}:\n{prayer['prayer']}\n\n"
    print(text)

def main():
    prayer_text =  get_prayers()
    print("Done!")
    return prayer_text


if __name__ == "__main__":
    # Execute async test function safely
    main()

    # Start FastAPI server
    uvicorn.run("main:app", port=4000, reload=True)