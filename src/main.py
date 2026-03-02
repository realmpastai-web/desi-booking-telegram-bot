"""
DesiBooking Telegram Bot
Professional booking & payments for Indian businesses
"""
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States for conversation
SELECTING_SERVICE, SELECTING_DATE, SELECTING_TIME, CONFIRMING, PAYMENT = range(5)

# Bot configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# Services catalog (configurable via /settings)
SERVICES = {
    "consultation": {"name": "1-on-1 Consultation", "price": 999, "duration": 60},
    "coaching": {"name": "Business Coaching", "price": 2499, "duration": 90},
    "astrology": {"name": "Astrology Reading", "price": 599, "duration": 45},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with service menu."""
    user = update.effective_user
    welcome_text = f"""
🙏 Namaste {user.first_name}!

Welcome to **DesiBooking** — India's simplest booking bot.

I help you book appointments with:
• Instant UPI payments
• Instamojo card/netbanking
• Automatic reminders

Select a service to get started:
"""
    keyboard = []
    for key, service in SERVICES.items():
        keyboard.append([InlineKeyboardButton(
            f"{service['name']} — ₹{service['price']}",
            callback_data=f"service_{key}"
        )])
    keyboard.append([InlineKeyboardButton("❓ Help", callback_data="help")])
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = """
**DesiBooking Help** 📚

**Booking:**
/start — Browse services
/book — Quick book last service
/mybookings — View your bookings
/cancel — Cancel a booking

**Payments:**
• UPI: Scan QR code
• Instamojo: Pay via card/netbanking

**Support:**
Contact @admin for help

_Note: All prices in INR (₹)_
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("service_"):
        service_key = data.replace("service_", "")
        service = SERVICES.get(service_key)
        if service:
            context.user_data["selected_service"] = service
            await show_date_selector(query, service)
    elif data == "help":
        await query.edit_message_text(
            "**How to book:**\n\n"
            "1. Select a service\n"
            "2. Pick a date\n" 
            "3. Choose time slot\n"
            "4. Pay via UPI or Instamojo\n"
            "5. Get confirmation & reminders\n\n"
            "Use /start to browse services!",
            parse_mode="Markdown"
        )

async def show_date_selector(query, service):
    """Show date selection keyboard."""
    from datetime import datetime, timedelta
    
    text = f"**{service['name']}** — ₹{service['price']}\n\nSelect a date:"
    
    keyboard = []
    today = datetime.now()
    for i in range(7):  # Next 7 days
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        display = date.strftime("%a, %d %b")
        keyboard.append([InlineKeyboardButton(display, callback_data=f"date_{date_str}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_services")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin dashboard command."""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Admin only.")
        return
    
    dashboard_text = """
**Admin Dashboard** ⚙️

📊 Quick Stats:
• Total Bookings: 0
• Today: 0  
• Revenue: ₹0

**Commands:**
/bookings — View all bookings
/earnings — Revenue report
/settings — Configure services
"""
    await update.message.reply_text(dashboard_text, parse_mode="Markdown")

def main() -> None:
    """Start the bot."""
    if not TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN found!")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_dashboard))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Run the bot
    logger.info("Starting DesiBooking Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
