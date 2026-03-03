"""
DesiBooking Telegram Bot - Main Entry Point
Professional booking & payments for Indian businesses

Features:
- Service catalog browsing
- Date/time slot selection
- UPI QR code payments
- Instamojo card/netbanking payments
- Booking management
- Admin dashboard
"""
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import handlers
from handlers.commands import (
    start_command, help_command, my_bookings_command, 
    cancel_command, admin_dashboard, all_bookings_command, earnings_command
)
from handlers.callbacks import callback_router
from services.database import init_db

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

def main() -> None:
    """Start the bot."""
    if not TOKEN:
        logger.error("❌ No TELEGRAM_BOT_TOKEN found in .env!")
        logger.error("Please set TELEGRAM_BOT_TOKEN in your .env file")
        return
    
    if TOKEN == "your_telegram_bot_token_here":
        logger.error("❌ TELEGRAM_BOT_TOKEN is still set to placeholder value!")
        logger.error("Please update .env with your actual bot token from @BotFather")
        return
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return
    
    # Build application
    application = Application.builder().token(TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mybookings", my_bookings_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("admin", admin_dashboard))
    application.add_handler(CommandHandler("bookings", all_bookings_command))
    application.add_handler(CommandHandler("earnings", earnings_command))
    
    # Callback handler (routes all inline button clicks)
    application.add_handler(CallbackQueryHandler(callback_router))
    
    # Error handler
    async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors caused by updates."""
        logger.error(f"Update {update} caused error {context.error}")
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or contact support."
            )
    
    application.add_error_handler(error_handler)
    
    # Run the bot
    logger.info("🚀 Starting DesiBooking Bot...")
    logger.info(f"👤 Admin ID: {ADMIN_USER_ID}")
    
    # Start polling
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
