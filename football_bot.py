import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# Load token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set.")

# Team member storage
team_members = {}

# Show the menu with buttons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("➕ Add Me", callback_data="add")],
        [InlineKeyboardButton("➖ Remove Me", callback_data="remove")],
        [InlineKeyboardButton("👥 Show Team", callback_data="team")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

# Handle button press
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username

    if query.data == "add":
        if username:
            team_members[user_id] = username
            await query.edit_message_text(f"@{username} added to the team!")
        else:
            await query.edit_message_text("Please set a username in Telegram to be added.")
    elif query.data == "remove":
        if user_id in team_members:
            del team_members[user_id]
            await query.edit_message_text(f"@{username} removed from the team!")
        else:
            await query.edit_message_text(f"@{username} is not in the team.")
    elif query.data == "team":
        if team_members:
            team_list = "\n".join([f"@{u}" for u in team_members.values()])
            await query.edit_message_text(f"Current team:\n{team_list}")
        else:
            await query.edit_message_text("The team is empty.")

# Main bot function
def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))
    application.run_polling()

if __name__ == "__main__":
    main()
