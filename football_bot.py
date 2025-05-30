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
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-bot.onrender.com

team_members = {}

# === Flask app for webhook + health check ===
flask_app = Flask(__name__)
telegram_app = Application.builder().token(TOKEN).build()

@flask_app.route("/")
def home():
    return "Bot is alive!", 200

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK", 200

# === Telegram Bot Logic ===
def generate_menu(user_id):
    if user_id in team_members:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➖ Remove Me", callback_data="remove")],
            [InlineKeyboardButton("👥 Show Team", callback_data="team")],
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me", callback_data="add")],
            [InlineKeyboardButton("👥 Show Team", callback_data="team")],
        ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = generate_menu(update.effective_user.id)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "anonymous"

    if query.data == "add":
        team_members[user_id] = username

    elif query.data == "remove":
        team_members.pop(user_id, None)

    if query.data == "back":
        await query.edit_message_text("Choose an action:", reply_markup=generate_menu(user_id))
        return

    if query.data == "team":
        if team_members:
            members = "\n".join(f"• @{u}" for u in team_members.values())
            text = f"👥 <b>Current Team Members</b>:\n{members}"
        else:
            text = "👥 <b>The team is currently empty.</b>"

        action = InlineKeyboardButton("➖ Remove Me", callback_data="remove") if user_id in team_members \
                 else InlineKeyboardButton("➕ Add Me", callback_data="add")

        markup = InlineKeyboardMarkup([
            [action],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ])

        await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

# === Main Setup ===
def main():
    # Register handlers
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(handle_button))

    # Start Flask in background thread
    threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()

    # Start polling so application.update_queue works
    telegram_app.run_polling()

if __name__ == "__main__":
    main()
