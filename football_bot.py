import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
import logging

# === Logging ===
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
)
logger = logging.getLogger(__name__)

# === Load Env Vars ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

team_members = {}

# === FastAPI App ===
app = FastAPI()
telegram_app = Application.builder().token(TOKEN).build()


@app.get("/")
async def root():
    logger.info("Health check received at '/' route.")
    return {"status": "✅ Bot is alive!"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    logger.info("Webhook route entered")
    body = await request.json()
    update = Update.de_json(body, telegram_app.bot)
    logger.info("Processing update: %s", update)
    await telegram_app.process_update(update)
    return {"ok": True}


# === Helper Functions ===
def get_team_message():
    if team_members:
        members = "\n".join(f"• @{u}" for u in team_members.values())
        return f"👥 <b>Current Team Members</b>:\n{members}"
    return "👥 <b>The team is currently empty.</b>"


def generate_buttons(user_id):
    if user_id in team_members:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➖ Remove Me", callback_data="remove")],
            [InlineKeyboardButton("👥 Show Team", callback_data="team")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me", callback_data="add")],
            [InlineKeyboardButton("👥 Show Team", callback_data="team")]
        ])


# === Bot Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Start command called")
    user_id = update.effective_user.id
    await update.message.reply_html(get_team_message(), reply_markup=generate_buttons(user_id))


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Handle button called")
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "anonymous"

    if query.data == "add":
        team_members[user_id] = username
    elif query.data == "remove":
        team_members.pop(user_id, None)

    text = get_team_message()
    buttons = generate_buttons(user_id)

    await query.edit_message_text(text, reply_markup=buttons, parse_mode="HTML")


# === Startup ===
@app.on_event("startup")
async def startup_event():
    logger.info("Setting up bot handlers and webhook")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(handle_button))
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    logger.info("Webhook set to: %s/webhook", WEBHOOK_URL)
