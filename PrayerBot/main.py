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


# ------- Handler Functions -------
async def starter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Start Command"""
    await update.message.reply_text(
        "Hi I'm the GFA rule Points Bot\n"
        "Commands:\n"
        "/rules will display all the rules\n"
        "/rule {number} will display a particular rule point\n"
        "/total will show the total rule points for the day"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "I help manage orders and rules in this group.\n"
        "Use /rules, /rule {number}, /total, or tap buttons when I show them."
    )


async def get_rules(
    update: Optional[Update] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None,
):
    # Execute query
    response = supabase.table("rules").select("rule_number","description", "rule").execute()

    # Extract records list from response.data
    rows = response.data
    text = "All rules "

    for row in rows:
        des = row.get("description", "")
        num = row.get("rule_number", "")
        rule = row.get("rule", "")

        if rule.endswith("."):
                    text += f"\n{num}. {des.title()}:\n{rule}\n\n"
        else:
            text += f"\n{num}. {des.title()}:\n{rule}.\n\n"
            

    print(text)

    # Send message to Telegram if triggered by a command
    if update and update.message:
        await update.message.reply_text(text)

    return rows

async def total_rule(update: Optional[Update] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None,
):
     resp = supabase.table("track")\
     .select("rule_number","total_times")\
     .execute()
     total = resp.count

async def each_rule(update: Optional[Update] = None,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None,
): 
    if not context.args:
        await update.message.reply_text(
            "Usage: /rule <number>\nExample: /rule 2")
        return

    try: 
        rule_number = int(context.args[0])
    except ValueError:
        await update.message.reply_text("/rule must be followed by a number")

        return

    resp = supabase.table("rules")\
    .select("rule","description")\
    .eq("rule_number",rule_number)\
    .eq("active",True)\
    .execute()

    rule = resp.data or []

    if not rule:
        await update.message.reply_text(
              f"No rule found with the number {rule_number}"
        )
        return
    rule = rule[0]

    text = f"\n{rule_number}. {rule['description'].title()}:\n{rule['rule']}\n\n"
    await update.message.reply_text(text)

async def rule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline keyboard button clicks for rule selection.
    callback_data format: 'rule:<number>'
    """
    query = update.callback_query
    await query.answer()  # acknowledge to remove "loading" state

    data = query.data  # e.g. "rule:2"
    if not data.startswith("rule:"):
        return

    try:
        rule_number = int(data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.edit_message_text("Invalid rule selection.")
        return

    # Fetch rule
    resp = (
        supabase
        .table("rules")
        .select("id, rule_number, description")
        .eq("rule_number", rule_number)
        .eq("active", True)
        .execute()
    )
    rules = resp.data or []

    if not rules:
        await query.edit_message_text(f"No active rule found with number {rule_number}.")
        return

    rule = rules[0]
    text = f"Selected rule:\n{rule['rule_number']}. {rule['description']}"

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
    application.add_handler(CommandHandler("rules",get_rules))
    application.add_handler(CommandHandler("rule",each_rule))

    application.add_handler(CallbackQueryHandler(rule_callback))

    application.add_error_handler(error_handler)

    # Starts telegram Bot asynchronously 
    async with application:
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Start Polling Bot")

    try:
            # Code to run while bot is live
            rule_text = await get_rules()
            print("Done!")

            # Keep the event loop open until interrupted (Ctrl+C)
            await asyncio.Event().wait()

    finally:
            # Stop polling and application before exiting context manager
            if application.updater.running:
                await application.updater.stop()
            if application.running:
                await application.stop()


    rule_text = await get_rules()
    print("Done!")
    return rule_text


if __name__ == "__main__":
    # Execute async test function safely
    import threading
    def run_fastapi():
    # Start FastAPI server
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    fastapi_thread =threading.Thread(target=run_fastapi, daemon= True)
    fastapi_thread.start()

    asyncio.run(main())

# Second Option
# def main():
#     application = Application.builder().token(TELEGRAM_TOKEN).build()
    
#     application.add_handler(CommandHandler("start", starter))
#     application.add_handler(CommandHandler("help", help_command))
#     application.add_handler(CommandHandler("rules", get_rules))
#     application.add_handler(CommandHandler("rule", each_rule))
#     application.add_handler(CallbackQueryHandler(rule_callback))
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