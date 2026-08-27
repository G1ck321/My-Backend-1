import asyncio
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.encoders import isoformat
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


# ------- Handler Functions -------
async def starter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Start Command"""
    await update.message.reply_text(
        "Hi I'm the GFA prayer Points Bot\n"
        "Commands:\n"
        "/prayers will display all the prayers\n"
        "/prayer {number} will display a particular prayer point\n"
        "/total will show the total prayer points for the day"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I help manage prayers in this group.\n"
        "Use /prayers, /prayer {number}, /totalprayed, or tap buttons when I show them."
    )


async def get_prayers(
    update: Optional[Update] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None,
):
    # Execute query
    response = supabase.table("prayers").select("prayer_number","description", "prayer").execute()

    # Extract records list from response.data
    rows = response.data
    text = "All prayers "

    for row in rows:
        des = row.get("description", "")
        num = row.get("prayer_number", "")
        prayer = row.get("prayer", "")

        if prayer.endswith("."):
                    text += f"\n{num}. {des.title()}:\n{prayer}\n\n"
        else:
            text += f"\n{num}. {des.title()}:\n{prayer}.\n\n"
            

    print(text)

    # Send message to Telegram if triggered by a command
    
    await update.message.reply_text(text)
    print(rows)
    return text

async def total_prayer(update: Optional[Update] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None,
):
    if not context.args:
        await update.message.reply_text(
              "Usage: /totalprayed <numofdays>\n num of days is the days that have passed" \
              "\n 1 is 24hours, 7 is seven days"
         )
        return

    try:
        number =  int(context.args[0])
    except:
        await update.message.reply_text(
                      f"Enter a valid number!"
                )
        return
    print(type(number))
    
    nigeria = ZoneInfo("Africa/Lagos")    
    now = datetime.now(nigeria)
    start = now - timedelta(days=number)
    resp = supabase.table("trackprayers")\
            .select("prayer","usage_count","last_used_at")\
            .gte("last_used_at", start.isoformat())\
            .lte("last_used_at",now.isoformat())\
            .order("usage_count", desc=False)\
            .execute()
    
    print(resp,"tt")
    total = resp.data or []
    print(total,"tt")
    if not total:
            await update.message.reply_text(
                  f"No prayers yet with the number {number}"
            )
            return
    text = f"These are the prayer points prayed already in the past {"day" if number ==1 else f"{number} days" }\n"
    for row in total:
        prayer_number = row.get("prayer", "")
        usage = row.get("usage_count", "")
                    
        text += f"Prayer {prayer_number}: {usage}\n"
    await update.message.reply_text(text)

async def each_prayer(update: Optional[Update] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None,
): 
    if not context.args:
        await update.message.reply_text(
            "Usage: /prayer <number>\nExample: /prayer 2")
        return

    try: 
        prayer_number = int(context.args[0])
    except ValueError:
        await update.message.reply_text("/prayer must be followed by a number")

        return

    resp = supabase.table("prayers")\
    .select("prayer","description")\
    .eq("prayer_number",prayer_number)\
    .eq("active",True)\
    .execute()

    update_row = supabase.rpc("increment_prayer_usage", {"target_prayer":prayer_number}).execute()

    print("RPC:", update_row.data)

    check = (
    supabase
    .table("trackprayers")
    .select("prayer, usage_count, last_used_at")
    .eq("prayer", prayer_number)
    .execute()
)
    prayer = resp.data or []

    

    if not prayer:
        await update.message.reply_text(
              f"No prayer found with the number {prayer_number}"
        )
        return
    prayer = prayer[0]

    text = f"\n{prayer_number}. {prayer['description'].title()}:\n{prayer['prayer']}\n\n"
    print(text)
    await update.message.reply_text(text)

async def prayer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline keyboard button clicks for prayer selection.
    callback_data format: 'prayer:<number>'
    """
    query = update.callback_query
    await query.answer()  # acknowledge to remove "loading" state

    data = query.data  # e.g. "prayer:2"
    if not data.startswith("prayer:"):
        return

    try:
        prayer_number = int(data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.edit_message_text("Invalid prayer selection.")
        return

    # Fetch prayer
    resp = (
        supabase
        .table("prayers")
        .select("id, prayer_number, description")
        .eq("prayer_number", prayer_number)
        .eq("active", True)
        .execute()
    )
    prayers = resp.data or []

    if not prayers:
        await query.edit_message_text(f"No prayer found with number {prayer_number}.")
        return

    prayer = prayers[0]
    text = f"Selected prayer:\n{prayer['prayer_number']}. {prayer['description']}"
    
    # Optionally edit the original message to show selection
    await query.edit_message_text(text)

async def error_handler(update: Update[Optional], context:ContextTypes.DEFAULT_TYPE):
    """logger error for update"""
    logger.error("Error while handling an"\
                 ,exc_info=context.error)
    

async def main():
    # Create Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start",starter))
    application.add_handler(CommandHandler("help",help_command))
    application.add_handler(CommandHandler("all",get_prayers))
    application.add_handler(CommandHandler("prayer",each_prayer))
    application.add_handler(CommandHandler("totalprayed",total_prayer))

    application.add_handler(CallbackQueryHandler(prayer_callback))

    application.add_error_handler(error_handler)

    # Starts telegram Bot asynchronously 
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Start Polling Bot")

    try:
            # Code to run while bot is live
            # prayer_text = await get_prayers()
            print("Done!")

            # Keep the event loop open until interrupted (Ctrl+C)
            await asyncio.Event().wait()

    finally:
            # Stop polling and application before exiting context manager
           # 3. Clean manual teardown sequence (reverse order)
            if application.updater and application.updater.running:
                await application.updater.stop()
            if application.running:
                await application.stop()

            await application.shutdown()


    # prayer_text = await get_prayers()
    # print("Done!")
    # return prayer_text


if __name__ == "__main__":
    # Execute async test function safely
    import threading
    def run_fastapi():
    # Start FastAPI server
        uvicorn.run(app, host="0.0.0.0",reload=True, port=8000, log_level="info")
    fastapi_thread =threading.Thread(target=run_fastapi, daemon= True)
    fastapi_thread.start()

    asyncio.run(main())

# Second Option
# def main():
#     application = Application.builder().token(TELEGRAM_TOKEN).build()
    
#     application.add_handler(CommandHandler("start", starter))
#     application.add_handler(CommandHandler("help", help_command))
#     application.add_handler(CommandHandler("prayers", get_prayers))
#     application.add_handler(CommandHandler("prayer", each_prayer))
#     application.add_handler(CallbackQueryHandler(prayer_callback))
#     application.add_error_handler(error_handler)

#     logger.info("Start Polling Bot")

#     # This blocks and runs the event loop internally
#     application.run_polling(allowed_updates=Update.ALL_TYPES)

# if __name__ == "__main__":
#     def run_fastapi():
#         uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

#     fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
#     fastapi_thread.start()

#     # Call main directly as a sync function
#     main()