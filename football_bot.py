import os
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
import logging 
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-bot.onrender.com

team_members = {}

# === Flask app for webhook + health check ===
flask_app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()


@flask_app.route("/")
def home():
    logger.info("Health check received at '/' route.")
    return "✅ Bot is alive!", 200


@flask_app.route("/webhook", methods=["POST"])
def webhook():
    logger.info("Webhook route enetered")
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    logger.info("Webhook route entered with update: %s", update)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200


# === Helper functions ===
def get_team_message():
    logger.info("Get Message enetered")
    if team_members:
        members = "\n".join(f"• @{u}" for u in team_members.values())
        return f"👥 <b>Current Team Members</b>:\n{members}"
    return "👥 <b>The team is currently empty.</b>"


def generate_buttons(user_id):
    logger.info("Generate button enetered")
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


# === Telegram Bot Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Start Cleed enetered")
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


def main():
    logger.info("Main called called")
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(handle_button))

    telegram_app.initialize()  # IMPORTANT: Initializes the app for manual queue usage

    # Set webhook URL (do this once)
    telegram_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

    # Start Flask app
    flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

if __name__ == "__main__":
    main()
