import os
import threading
from dotenv import load_dotenv
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-bot.onrender.com

team_members = {}

# === Flask app for webhook + health check ===
flask_app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

@flask_app.route("/")
def home():
    return "Bot is alive!", 200

def start_flask():
    flask_app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
    
@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200

# === Helper functions ===
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

# === Telegram Bot Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_html(
        get_team_message(),
        reply_markup=generate_buttons(user_id)
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "anonymous"

    if query.data == "add":
        team_members[user_id] = username
    elif query.data == "remove":
        team_members.pop(user_id, None)
    # "team" just refreshes the view

    if query.data in ("team", "add", "remove"):
        text = get_team_message()

        if user_id in team_members:
            buttons = [
                InlineKeyboardButton("➖ Remove Me", callback_data="remove"),
                InlineKeyboardButton("👥 Show Team", callback_data="team"),
            ]
        else:
            buttons = [
                InlineKeyboardButton("➕ Add Me", callback_data="add"),
                InlineKeyboardButton("👥 Show Team", callback_data="team"),
            ]

        markup = InlineKeyboardMarkup([buttons])

        await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

# === Run Flask in thread ===
def start_flask():
    flask_app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# === Main Setup ===
def main():
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(handle_button))

    # Start Flask app (health check + webhook route)
    threading.Thread(target=start_flask).start()

    # Start telegram webhook listening on port 5000
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=5000,
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

if __name__ == "__main__":
    main()
