import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-bot.onrender.com

team_members = {}

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
    username = query.from_user.username

    if query.data == "add":
        if username:
            team_members[user_id] = username
            await query.edit_message_text(f"@{username} added to the team!", reply_markup=generate_menu(user_id))
        else:
            await query.edit_message_text("Please set a username in Telegram to be added.")
    elif query.data == "remove":
        if user_id in team_members:
            del team_members[user_id]
            await query.edit_message_text(f"@{username} removed from the team!", reply_markup=generate_menu(user_id))
        else:
            await query.edit_message_text(f"@{username} is not in the team.", reply_markup=generate_menu(user_id))
    elif query.data == "team":
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

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),  # Render uses PORT env variable
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

if __name__ == "__main__":
    main()
