import os
from dotenv import load_dotenv
from telegram.ext import Application
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
# Load .env file
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set. Please check your .env file or Render environment variables.")

# Store team members in a dictionary
team_members = {}

async def add_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds a user to the team list."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    if username:
        team_members[user_id] = username
        await update.message.reply_text(f"@{username} added to the team!")
    else:
         await update.message.reply_text("Please set a username in Telegram to be added to the team.")

async def remove_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Removes a user from the team list."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    if user_id in team_members:
        del team_members[user_id]
        await update.message.reply_text(f"@{username} removed from the team!")
    else:
        await update.message.reply_text(f"@{username} is not in the team.")

async def show_team(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the current team list."""
    if team_members:
        team_list = "\n".join([f"@{username}" for username in team_members.values()])
        await update.message.reply_text(f"Current team:\n{team_list}")
    else:
        await update.message.reply_text("The team is empty.")

def main() -> None:
    """Start the bot."""
    # Replace 'YOUR_TOKEN' with your actual bot token
    application = ApplicationBuilder().token("YOUR_TOKEN").build()

    # Add command handlers
    application.add_handler(CommandHandler("add", add_member))
    application.add_handler(CommandHandler("remove", remove_member))
    application.add_handler(CommandHandler("team", show_team))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
