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
from telegram.ext import MessageHandler, filters

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
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
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

def generate_buttons(user_id, username):
    is_admin = team_manager.is_admin( username=username)
    print("Is Admin")
    print(is_admin)
    is_super_admin = team_manager.is_super_admin(user_id=user_id, username=username)
    in_main_team = any(member_id == user_id for member_id, _, _ in team_manager.main_team)
    
    buttons = []

    if in_main_team:
        buttons.append([InlineKeyboardButton("➖ Remove Me", callback_data="remove")])
    else:
        buttons.append([InlineKeyboardButton("➕ Add Me", callback_data="add")])

    buttons.append([InlineKeyboardButton("👥 Show Team", callback_data="team")])

    if is_admin:
        buttons.append([InlineKeyboardButton("⚙️ Settings", callback_data="settings")])

    if is_super_admin:
        buttons.append([InlineKeyboardButton("⚙️ Settings", callback_data="settings")])
        
    return InlineKeyboardMarkup(buttons)

def generate_settings_buttons(is_super_admin=False):
    buttons = [
        [InlineKeyboardButton("📅 Set Date", callback_data="set_date")],
        [InlineKeyboardButton("📍 Set Venue", callback_data="set_venue")],
        [InlineKeyboardButton("👥 Set Max Team Size", callback_data="set_max")],
        [InlineKeyboardButton("🧹 Clear Team Lists", callback_data="clear_team")],
    ]

    if is_super_admin:
        buttons.append([InlineKeyboardButton("➕ Add Admin", callback_data="add_admin")])
        buttons.append([InlineKeyboardButton("📋 List Admins", callback_data="list_admins")])

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
    return InlineKeyboardMarkup(buttons)
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    full_name = f"{user.first_name} {user.last_name}".strip() if user.last_name else user.first_name

    await update.message.reply_html(
        get_team_message(),
        reply_markup=generate_buttons(user_id, username)
    )

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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "awaiting_input" not in context.user_data:
        return

    field = context.user_data.pop("awaiting_input")
    value = update.message.text.strip()

    if field == "event_date":
        team_manager.event_date = value
        await update.message.reply_text(f"✅ Event date set to: {value}")
    elif field == "venue":
        team_manager.venue = value
        await update.message.reply_text(f"✅ Venue set to: {value}")
    elif field == "max_players":
        try:
            team_manager.max_players = int(value)
            await update.message.reply_text(f"✅ Max players set to: {value}")
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number.")

    elif field == "add_admin":
        username = value.strip().lstrip('@')
        if team_manager.add_admin(username):
            await update.message.reply_text(f"✅ @{username} has been added as an admin.")
        else:
            await update.message.reply_text("❌ Failed to add admin. Make sure the username is valid.")
            
    await update.message.reply_html(
        get_team_message(),
        reply_markup=generate_buttons(update.effective_user.id, update.effective_user.username)
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
        buttons = generate_buttons(user_id, username)
        await query.edit_message_text(get_team_message(), reply_markup=buttons, parse_mode="HTML")
        return

    elif query.data == "remove":
        response = team_manager.leave_team(user_id)
        buttons = generate_buttons(user_id, username)
        await query.edit_message_text(get_team_message(), reply_markup=buttons, parse_mode="HTML")
        return

    elif query.data == "team":
        await query.edit_message_text(get_team_message(), reply_markup=generate_buttons(user_id, username), parse_mode="HTML")
        return

    elif query.data == "settings":
        is_super_admin = team_manager.is_super_admin(user_id=user_id, username=username)
        await query.edit_message_text(
            "⚙️ <b>Event Settings</b>\nChoose what you want to configure:",
            reply_markup=generate_settings_buttons(is_super_admin=is_super_admin),
            parse_mode="HTML"
        )
        return

    elif query.data == "set_date":
        await query.edit_message_text("📅 Send me the new event date (e.g., 2025-06-01):", parse_mode="HTML")
        context.user_data["awaiting_input"] = "event_date"
        return

    elif query.data == "set_venue":
        await query.edit_message_text("📍 Send me the new venue name:", parse_mode="HTML")
        context.user_data["awaiting_input"] = "venue"
        return

    elif query.data == "set_max":
        await query.edit_message_text("👥 Send the new max number of players (e.g., 18):", parse_mode="HTML")
        context.user_data["awaiting_input"] = "max_players"
        return

    elif query.data == "clear_team":
        if team_manager.is_admin(user_id=user_id, username=username):
            team_manager.main_team.clear()
            team_manager.reserve_team.clear()
            await query.edit_message_text(
                "🧹 <b>Team lists have been cleared.</b>",
                reply_markup=generate_settings_buttons(),
                parse_mode="HTML"
            )
        else:
            await query.answer("⛔ You are not authorized.", show_alert=True)
        return

    elif query.data == "add_admin":
        await query.edit_message_text("👤 Send the @username of the user to add as admin:", parse_mode="HTML")
        context.user_data["awaiting_input"] = "add_admin"
        return

    elif query.data == "list_admins":
        admins = team_manager.get_admins()  # Should return list of (user_id, username)
        if not admins:
            await query.edit_message_text("❌ No admins found.", parse_mode="HTML")
        else:
            buttons = [
                [InlineKeyboardButton(f"🗑 Remove @{uname}", callback_data=f"remove_admin:{uname}")]
                for uname in admins
            ]
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings")])
            await query.edit_message_text(
                "📋 <b>Admin List</b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="HTML"
            )
        return

    elif query.data.startswith("remove_admin:"):
        if not team_manager.is_super_admin(user_id, username):
            await query.answer("⛔ Only super admins can remove admins.", show_alert=True)
            return
        admin_id_to_remove = int(query.data.split(":")[1])
        team_manager.remove_admin(admin_id_to_remove)
        await query.edit_message_text("✅ Admin removed successfully.", parse_mode="HTML")
        return
        
    elif query.data == "back_to_main":
        await query.edit_message_text(
            get_team_message(),
            reply_markup=generate_buttons(user_id, username),
            parse_mode="HTML"
        )
        return

    # Unknown action fallback
    await query.edit_message_text("❌ Unknown action.", parse_mode="HTML")


# === Uvicorn entrypoint ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("football_bot:app", host="0.0.0.0", port=PORT, reload=False)
