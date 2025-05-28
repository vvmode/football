import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set.")

# Store team members
team_members = {}

# Generate keyboard based on user's status
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

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    reply_markup = generate_menu(user_id)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

# Handle button presses
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username

    if query.data == "add":
        if username:
            team_members[user_id] = username
            reply_markup = generate_menu(user_id)
            await query.edit_message_text(
                f"✅ @{username} added to the team!", reply_markup=reply_markup
            )
        else:
            await query.edit_message_text("❌ Please set a username in Telegram to be added.")

    elif query.data == "remove":
        if user_id in team_members:
            del team_members[user_id]

            # Generate updated team list
            if team_members:
                team_list = "\n".join([f"• @{u}" for u in team_members.values()])
                text = f"✅ @{username} removed from the team!\n\n👥 <b>Current Team Members:</b>\n{team_list}"
            else:
                text = f"✅ @{username} removed from the team!\n\n👥 <b>The team is now empty.</b>"

            reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ Add Me", callback_data="add"),
                InlineKeyboardButton("⬅️ Back", callback_data="back")
            ]])
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

        else:
            reply_markup = generate_menu(user_id)
            await query.edit_message_text(
                f"⚠️ @{username} is not in the team.", reply_markup=reply_markup
            )

    elif query.data == "team":
        if team_members:
            team_list = "\n".join([f"• @{u}" for u in team_members.values()])
            text = f"👥 <b>Current Team Members:</b>\n{team_list}"
        else:
            text = "👥 <b>The team is currently empty.</b>"

        if user_id in team_members:
            action_button = InlineKeyboardButton("➖ Remove Me", callback_data="remove")
        else:
            action_button = InlineKeyboardButton("➕ Add Me", callback_data="add")

        reply_markup = InlineKeyboardMarkup([
            [action_button],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")]
        ])
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

    elif query.data == "back":
        reply_markup = generate_menu(user_id)
        await query.edit_message_text("Choose an action:", reply_markup=reply_markup)

# Main bot setup
def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button))
    application.run_polling()

if __name__ == "__main__":
    main()
