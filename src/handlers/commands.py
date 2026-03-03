"""
Command handlers for DesiBooking Bot
"""
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from services.database import (
    init_db, get_user_bookings, get_all_bookings, cancel_booking,
    get_revenue_stats, get_booking_by_id
)
from services.payments import generate_upi_qr, get_upi_link
from services.instamojo import create_payment_link

# Config
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
UPI_ID = os.getenv("UPI_ID", "")
UPI_NAME = os.getenv("UPI_NAME", "DesiBooking")
ENABLE_INSTAMOJO = os.getenv("ENABLE_INSTAMOJO", "true").lower() == "true"

# Services catalog (can be moved to DB later)
SERVICES = {
    "consultation": {"name": "1-on-1 Consultation", "price": 999, "duration": 60},
    "coaching": {"name": "Business Coaching", "price": 2499, "duration": 90},
    "astrology": {"name": "Astrology Reading", "price": 599, "duration": 45},
    "webdev": {"name": "Website Consultation", "price": 1499, "duration": 60},
}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with service menu."""
    user = update.effective_user
    
    # Initialize DB on first run
    init_db()
    
    welcome_text = f"""
🙏 <b>Namaste {user.first_name}!</b>

Welcome to <b>DesiBooking</b> — India's simplest booking bot for professionals.

<b>I help you book appointments with:</b>
✅ Instant UPI payments (PhonePe, GPay, Paytm)
✅ Card/NetBanking via Instamojo
✅ Automatic reminders

<i>Select a service below to book:</i>
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
        parse_mode="HTML"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = """
<b>📚 DesiBooking Help</b>

<b>🚀 Booking Commands:</b>
/start — Browse & book services
/mybookings — View your bookings
/cancel — Cancel a booking

<b>💳 Payments:</b>
• UPI: Scan QR code with any app
• Instamojo: Pay via card/netbanking

<b>👨‍💼 Admin:</b>
/admin — Admin dashboard

<b>ℹ️ Notes:</b>
• All prices in INR (₹)
• Bookings confirmed after payment
• Cancellations available 24h before

<b>❓ Need help?</b>
Contact admin or use /start to book!
"""
    await update.message.reply_text(help_text, parse_mode="HTML")

async def my_bookings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's bookings."""
    user_id = update.effective_user.id
    bookings = get_user_bookings(user_id)
    
    if not bookings:
        await update.message.reply_text(
            "📭 <b>No bookings found!</b>\n\nUse /start to book your first appointment.",
            parse_mode="HTML"
        )
        return
    
    text = "<b>📅 Your Bookings:</b>\n\n"
    keyboard = []
    
    for booking in bookings[:5]:  # Show last 5
        status_emoji = "✅" if booking['status'] == 'confirmed' else "⏳" if booking['status'] == 'pending' else "❌"
        text += f"{status_emoji} <b>{booking['service_name']}</b>\n"
        text += f"📅 {booking['date']} at {booking['time']}\n"
        text += f"💰 ₹{booking['price']} • Status: {booking['status'].upper()}\n\n"
        
        if booking['status'] in ['pending', 'confirmed']:
            keyboard.append([InlineKeyboardButton(
                f"❌ Cancel #{booking['id']}",
                callback_data=f"cancel_{booking['id']}"
            )])
    
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_bookings")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel a booking by ID."""
    user_id = update.effective_user.id
    bookings = get_user_bookings(user_id)
    
    if not bookings:
        await update.message.reply_text("📭 You have no bookings to cancel.")
        return
    
    keyboard = []
    for booking in bookings[:5]:
        if booking['status'] in ['pending', 'confirmed']:
            keyboard.append([InlineKeyboardButton(
                f"❌ Cancel #{booking['id']}: {booking['service_name']}",
                callback_data=f"cancel_{booking['id']}"
            )])
    
    if not keyboard:
        await update.message.reply_text("No active bookings to cancel.")
        return
    
    await update.message.reply_text(
        "<b>Select a booking to cancel:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin dashboard command."""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ <b>Admin access only.</b>", parse_mode="HTML")
        return
    
    stats = get_revenue_stats()
    
    dashboard_text = f"""
<b>⚙️ Admin Dashboard</b>

<b>📊 Revenue Stats:</b>
• Total Revenue: ₹{stats['total_revenue']:,}
• Total Bookings: {stats['total_bookings']}
• Today: {stats['today_bookings']} bookings (₹{stats['today_revenue']:,})

<b>🔧 Commands:</b>
/bookings — View all bookings
/earnings — Detailed revenue report
/settings — Configure services
"""
    keyboard = [
        [InlineKeyboardButton("📋 View Bookings", callback_data="admin_bookings")],
        [InlineKeyboardButton("💰 Earnings Report", callback_data="admin_earnings")],
    ]
    
    await update.message.reply_text(
        dashboard_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def all_bookings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View all bookings (admin only)."""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Admin only.")
        return
    
    bookings = get_all_bookings(limit=10)
    
    if not bookings:
        await update.message.reply_text("📭 No bookings found.")
        return
    
    text = "<b>📋 All Bookings:</b>\n\n"
    for booking in bookings:
        status_emoji = "✅" if booking['status'] == 'confirmed' else "⏳" if booking['status'] == 'pending' else "❌"
        text += f"#{booking['id']} {status_emoji} <b>{booking['service_name']}</b>\n"
        text += f"👤 {booking['user_name']} (ID: {booking['user_id']})\n"
        text += f"📅 {booking['date']} {booking['time']} • ₹{booking['price']}\n"
        text += f"Status: {booking['status'].upper()}\n\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def earnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View earnings report (admin only)."""
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Admin only.")
        return
    
    stats = get_revenue_stats()
    
    text = f"""
<b>💰 Earnings Report</b>

<b>Total Revenue:</b> ₹{stats['total_revenue']:,}
<b>Total Bookings:</b> {stats['total_bookings']}

<b>Today's Performance:</b>
• Bookings: {stats['today_bookings']}
• Revenue: ₹{stats['today_revenue']:,}

<i>Keep up the great work! 🚀</i>
"""
    await update.message.reply_text(text, parse_mode="HTML")
