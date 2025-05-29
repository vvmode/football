import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

# Load environment variables from .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-bot.onrender.com

# Store team members in memory
team_members = {}

# Generate inline keyboard menu based on whether the user is in the team
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

# Handle /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = generate_menu(update.effective_user.id)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

# Handle button callbacks
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username

    if query.data == "add":
        if username:
            team_members[user_id] = username
        else:
            await query.edit_message_text("Please set a username in Telegram to be added.")
            return

    elif query.data == "remove":
        team_members.pop(user_id, None)

    if query.data in ("add", "remove", "team"):
        if team_members:
            members = "\n".join(f"• @{u}" for u in team_members.values())
            text = f"👥 <b>Current Team Members</b>:\n{members}"
        else:
            text = "👥 <b>The team is currently empty.</b>"

        action = InlineKeyboardButton("➖ Remove Me", callback_data="remove") if user_id in team_members \
                 else InlineKeyboardButton("➕ Add Me", callback_data="add")
        markup = InlineKeyboardMarkup([[action], [InlineKeyboardButton("⬅️ Back", callback_data="back")]])
        await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

    elif query.data == "back":
        await query.edit_message_text("Choose an action:", reply_markup=generate_menu(user_id))

# Main entry point
def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),  # Render sets this PORT automatically
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

if __name__ == "__main__":
    main()
