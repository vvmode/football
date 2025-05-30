import os
import logging
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()

# === Setup ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://yourapp.onrender.com
PORT = int(os.getenv("PORT", 10000))

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

team_members = {}  # {user_id: {"username": str, "full_name": str}}

# === Telegram bot application ===
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()


# === FastAPI lifespan events ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("📦 Starting up app...")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(handle_button))
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logger.info("✅ Webhook set")
    yield
    logger.info("🧹 Shutting down app...")
    await telegram_app.shutdown()


# === FastAPI app ===
app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "🤖 Bot is alive!"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


# === Telegram Bot Handlers ===
def get_team_message():
    if team_members:
        members = "\n".join(
            f"• {info['full_name']} (@{info['username']})" for info in team_members.values()
        )
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_html(get_team_message(), reply_markup=generate_buttons(user_id))


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = query.from_user
    user_id = user.id
    username = user.username or "anonymous"
    full_name = f"{user.first_name} {user.last_name}".strip() if user.last_name else user.first_name

    if query.data == "add":
        team_members[user_id] = {"username": username, "full_name": full_name}
    elif query.data == "remove":
        team_members.pop(user_id, None)

    text = get_team_message()
    buttons = generate_buttons(user_id)
    
    await query.edit_message_text(text, reply_markup=buttons, parse_mode="HTML")

# === Uvicorn entrypoint ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("football_bot:app", host="0.0.0.0", port=PORT, reload=False)
