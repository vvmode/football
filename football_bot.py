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
from team_manager import TeamManager  # import your TeamManager class

load_dotenv()

# === Setup ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://yourapp.onrender.com
PORT = int(os.getenv("PORT", 10000))

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

team_manager = TeamManager()  # create TeamManager instance

# === Telegram bot application ===
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# === FastAPI lifespan events ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("📦 Starting up app...")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("setevent", set_event))  # add setevent handler
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
    if team_manager.main_team or team_manager.reserve_team:
        members = []
        for i, (_, name, username) in enumerate(team_manager.main_team, 1):
            members.append(f"{i}. {name} (@{username})")
        main_list = "\n".join(members) if members else "No team members yet."

        reserve_list = ""
        if team_manager.reserve_team:
            reserve_members = [
                f"{i}. {name} (@{username})" for i, (_, name, username) in enumerate(team_manager.reserve_team, 1)
            ]
            reserve_list = "\n\n🕒 <b>Reserve List:</b>\n" + "\n".join(reserve_members)

        return (
            f"👥 <b>Current Team Members (Max {team_manager.max_players}):</b>\n"
            f"{main_list}"
            f"{reserve_list}\n\n"
            f"📅 Event Date: {team_manager.event_date}\n"
            f"📍 Venue: {team_manager.venue}"
        )
    return "👥 <b>The team is currently empty.</b>"

def generate_buttons(user_id):
    if user_id in [uid for uid, _, _ in team_manager.main_team + team_manager.reserve_team]:
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

async def set_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # For demo: allow only super admin (or all admins) to set event details
    if not team_manager.is_admin(user_id):
        await update.message.reply_text("❌ You don't have permission to set the event.")
        return

    # Expect command like: /setevent 20 Stadium 2025-06-01
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /setevent <max_players> <venue> <event_date>\nExample: /setevent 20 Stadium 2025-06-01")
        return

    try:
        max_players = int(args[0])
        venue = args[1]
        event_date = args[2]
    except Exception:
        await update.message.reply_text("Invalid arguments. Please check the format.")
        return

    team_manager.set_event_details(max_players, venue, event_date)
    await update.message.reply_text(
        f"✅ Event updated:\nMax Players: {max_players}\nVenue: {venue}\nDate: {event_date}"
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id
    username = user.username or "anonymous"
    full_name = f"{user.first_name} {user.last_name}".strip() if user.last_name else user.first_name

    if query.data == "add":
        response = team_manager.join_team(user_id, full_name, username)
    elif query.data == "remove":
        response = team_manager.leave_team(user_id)
    elif query.data == "team":
        response = get_team_message()
    else:
        response = "Unknown action."

    buttons = generate_buttons(user_id)
    await query.edit_message_text(response, reply_markup=buttons, parse_mode="HTML")

# === Uvicorn entrypoint ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("football_bot:app", host="0.0.0.0", port=PORT, reload=False)
