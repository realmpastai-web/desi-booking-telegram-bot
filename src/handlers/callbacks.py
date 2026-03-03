"""
Callback query handlers for booking flow
"""
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from services.database import add_booking, get_user_bookings, cancel_booking, is_slot_available, get_booking_by_id
from services.payments import generate_upi_qr
from services.instamojo import create_payment_link

# Config
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
UPI_ID = os.getenv("UPI_ID", "")
UPI_NAME = os.getenv("UPI_NAME", "DesiBooking")
ENABLE_INSTAMOJO = os.getenv("ENABLE_INSTAMOJO", "true").lower() == "true"

SERVICES = {
    "consultation": {"name": "1-on-1 Consultation", "price": 999, "duration": 60},
    "coaching": {"name": "Business Coaching", "price": 2499, "duration": 90},
    "astrology": {"name": "Astrology Reading", "price": 599, "duration": 45},
    "webdev": {"name": "Website Consultation", "price": 1499, "duration": 60},
}

# Time slots (9 AM to 6 PM, hourly)
TIME_SLOTS = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route callback queries to appropriate handlers."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("service_"):
        await handle_service_selection(update, context, data)
    elif data.startswith("date_"):
        await handle_date_selection(update, context, data)
    elif data.startswith("time_"):
        await handle_time_selection(update, context, data)
    elif data.startswith("pay_"):
        await handle_payment_selection(update, context, data)
    elif data.startswith("cancel_"):
        await handle_cancel(update, context, data)
    elif data == "help":
        await handle_help(update, context)
    elif data == "back_services":
        await handle_back_to_services(update, context)
    elif data == "refresh_bookings":
        await handle_refresh_bookings(update, context)
    elif data == "admin_bookings":
        await handle_admin_bookings(update, context)
    elif data == "admin_earnings":
        await handle_admin_earnings(update, context)
    elif data == "confirm_upi":
        await handle_upi_confirmation(update, context)

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle service selection - show date picker."""
    query = update.callback_query
    service_key = data.replace("service_", "")
    service = SERVICES.get(service_key)
    
    if not service:
        await query.edit_message_text("❌ Service not found. Use /start to try again.")
        return
    
    # Store selected service
    context.user_data["selected_service"] = service
    context.user_data["selected_service_key"] = service_key
    
    # Build date keyboard
    text = f"<b>{service['name']}</b>\n💰 ₹{service['price']} • ⏱️ {service['duration']} min\n\n📅 Select a date:"
    
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
        parse_mode="HTML"
    )

async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle date selection - show time picker."""
    query = update.callback_query
    date_str = data.replace("date_", "")
    service = context.user_data.get("selected_service")
    
    if not service:
        await query.edit_message_text("❌ Session expired. Use /start to try again.")
        return
    
    # Store selected date
    context.user_data["selected_date"] = date_str
    
    # Build time keyboard (show available slots)
    text = f"<b>{service['name']}</b>\n📅 {date_str}\n\n⏰ Select a time slot:"
    
    keyboard = []
    for time_slot in TIME_SLOTS:
        if is_slot_available(date_str, time_slot):
            keyboard.append([InlineKeyboardButton(
                f"{time_slot} ✅", 
                callback_data=f"time_{time_slot}"
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                f"{time_slot} ❌ Booked", 
                callback_data="ignore"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"service_{context.user_data.get('selected_service_key', '')}")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle time selection - show payment options."""
    query = update.callback_query
    time_str = data.replace("time_", "")
    service = context.user_data.get("selected_service")
    date_str = context.user_data.get("selected_date")
    
    if not service or not date_str:
        await query.edit_message_text("❌ Session expired. Use /start to try again.")
        return
    
    # Store selected time
    context.user_data["selected_time"] = time_str
    
    # Show booking summary and payment options
    text = f"""
<b>📋 Booking Summary</b>

<b>Service:</b> {service['name']}
<b>Date:</b> {date_str}
<b>Time:</b> {time_str}
<b>Duration:</b> {service['duration']} minutes
<b>Amount:</b> ₹{service['price']}

<i>Select payment method:</i>
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Pay via UPI (QR Code)", callback_data="pay_upi")],
    ]
    
    if ENABLE_INSTAMOJO:
        keyboard.append([InlineKeyboardButton("💳 Pay via Card/NetBanking", callback_data="pay_instamojo")])
    
    keyboard.append([InlineKeyboardButton("🔙 Change Time", callback_data=f"date_{date_str}")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def handle_payment_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle payment method selection."""
    query = update.callback_query
    user = update.effective_user
    service = context.user_data.get("selected_service")
    date_str = context.user_data.get("selected_date")
    time_str = context.user_data.get("selected_time")
    service_key = context.user_data.get("selected_service_key")
    
    if not all([service, date_str, time_str]):
        await query.edit_message_text("❌ Session expired. Use /start to try again.")
        return
    
    # Create booking in database
    booking_id = add_booking(
        user_id=user.id,
        user_name=user.first_name or user.username or "Unknown",
        service_key=service_key,
        service_name=service['name'],
        price=service['price'],
        booking_date=date_str,
        booking_time=time_str
    )
    
    context.user_data["booking_id"] = booking_id
    
    if data == "pay_upi":
        # Generate UPI QR code
        transaction_note = f"Booking#{booking_id}"
        
        await query.edit_message_text(
            f"<b>💳 Payment for Booking #{booking_id}</b>\n\n"
            f"Generating UPI QR code... Please wait.",
            parse_mode="HTML"
        )
        
        try:
            qr_buffer = generate_upi_qr(UPI_ID, UPI_NAME, service['price'], transaction_note)
            
            # Send QR code image
            await context.bot.send_photo(
                chat_id=user.id,
                photo=qr_buffer,
                caption=f"""
<b>📱 Scan to Pay via UPI</b>

<b>Amount:</b> ₹{service['price']}
<b>UPI ID:</b> {UPI_ID}
<b>Booking ID:</b> #{booking_id}

<b>Instructions:</b>
1️⃣ Open PhonePe, GPay, or Paytm
2️⃣ Scan this QR code
3️⃣ Complete the payment
4️⃣ Click "I've Paid" below

<i>Payment will be verified within 5 minutes.</i>
""",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ I've Paid", callback_data="confirm_upi")],
                    [InlineKeyboardButton("❓ Payment Help", url="https://t.me/admin")]
                ])
            )
            
            # Update original message
            await query.edit_message_text(
                f"<b>✅ Booking #{booking_id} Created!</b>\n\n"
                f"📱 QR code sent to your DM.\n"
                f"Complete payment to confirm your slot.",
                parse_mode="HTML"
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"<b>❌ Error generating QR:</b> {str(e)}\n\n"
                f"Please pay manually to: <code>{UPI_ID}</code>\n"
                f"Amount: ₹{service['price']}\n"
                f"Note: {transaction_note}",
                parse_mode="HTML"
            )
    
    elif data == "pay_instamojo":
        # Create Instamojo payment link
        await query.edit_message_text(
            f"<b>💳 Creating Payment Link...</b>\n\nPlease wait...",
            parse_mode="HTML"
        )
        
        result = create_payment_link(
            booking_id=booking_id,
            service_name=service['name'],
            amount=service['price'],
            customer_name=user.first_name or user.username or "Customer",
            customer_email=f"user_{user.id}@desibooking.local"
        )
        
        if result.get("success"):
            payment_url = result.get("payment_url")
            payment_id = result.get("payment_id")
            
            await query.edit_message_text(
                f"""
<b>💳 Complete Your Payment</b>

<b>Booking ID:</b> #{booking_id}
<b>Amount:</b> ₹{service['price']}

<b>Click below to pay securely:</b>
<i>You'll be redirected to Instamojo's secure payment page.</i>

After payment, you'll receive confirmation automatically.
""",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Pay ₹{} via Card/NetBanking".format(service['price']), url=payment_url)],
                    [InlineKeyboardButton("🔙 Back", callback_data=f"time_{time_str}")]
                ]),
                parse_mode="HTML"
            )
        else:
            error = result.get("error", "Unknown error")
            await query.edit_message_text(
                f"<b>❌ Payment Link Failed:</b> {error}\n\n"
                f"Please try UPI payment or contact support.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📱 Try UPI Instead", callback_data="pay_upi")],
                    [InlineKeyboardButton("❓ Contact Support", url="https://t.me/admin")]
                ]),
                parse_mode="HTML"
            )

async def handle_upi_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle UPI payment confirmation."""
    query = update.callback_query
    await query.answer("⏳ Verifying payment... Please wait 5 minutes for manual verification.")
    
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Payment Submitted for Verification", callback_data="ignore")],
        ])
    )
    
    # Notify admin
    booking_id = context.user_data.get("booking_id")
    user = update.effective_user
    
    if ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"""
<b>🔔 UPI Payment Submitted</b>

<b>Booking ID:</b> #{booking_id}
<b>User:</b> {user.first_name} (@{user.username})
<b>User ID:</b> {user.id}

Please verify and confirm payment manually.
Use /admin to view bookings.
""",
            parse_mode="HTML"
        )

async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle booking cancellation."""
    query = update.callback_query
    booking_id = int(data.replace("cancel_", ""))
    user_id = update.effective_user.id
    
    # Verify booking belongs to user
    booking = get_booking_by_id(booking_id)
    if not booking or (booking['user_id'] != user_id and user_id != ADMIN_USER_ID):
        await query.answer("❌ Unauthorized", show_alert=True)
        return
    
    if cancel_booking(booking_id):
        await query.answer("✅ Booking cancelled successfully!")
        await query.edit_message_text(
            f"<b>✅ Booking #{booking_id} Cancelled</b>\n\n"
            f"Your slot has been released.\n"
            f"Use /start to make a new booking.",
            parse_mode="HTML"
        )
    else:
        await query.answer("❌ Could not cancel booking", show_alert=True)

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help in response to callback."""
    query = update.callback_query
    
    help_text = """
<b>📚 How to Book:</b>

1️⃣ Select a service
2️⃣ Pick a date
3️⃣ Choose available time slot
4️⃣ Pay via UPI or Card/NetBanking
5️⃣ Receive confirmation & reminders

<b>Commands:</b>
/start — Browse services
/mybookings — View your bookings
/cancel — Cancel a booking

Need help? Contact @admin
"""
    await query.edit_message_text(help_text, parse_mode="HTML")

async def handle_back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Go back to service selection."""
    query = update.callback_query
    
    text = "<b>🙏 Welcome!</b>\n\nSelect a service to book:"
    keyboard = []
    for key, service in SERVICES.items():
        keyboard.append([InlineKeyboardButton(
            f"{service['name']} — ₹{service['price']}",
            callback_data=f"service_{key}"
        )])
    keyboard.append([InlineKeyboardButton("❓ Help", callback_data="help")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def handle_refresh_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Refresh bookings list."""
    query = update.callback_query
    user_id = update.effective_user.id
    bookings = get_user_bookings(user_id)
    
    if not bookings:
        await query.edit_message_text(
            "📭 <b>No bookings found!</b>\n\nUse /start to book your first appointment.",
            parse_mode="HTML"
        )
        return
    
    text = "<b>📅 Your Bookings:</b>\n\n"
    keyboard = []
    
    for booking in bookings[:5]:
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
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def handle_admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin bookings button."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await query.answer("⛔ Admin only")
        return
    
    from services.database import get_all_bookings
    bookings = get_all_bookings(limit=10)
    
    if not bookings:
        await query.edit_message_text("📭 No bookings found.")
        return
    
    text = "<b>📋 All Bookings:</b>\n\n"
    for booking in bookings:
        status_emoji = "✅" if booking['status'] == 'confirmed' else "⏳" if booking['status'] == 'pending' else "❌"
        text += f"#{booking['id']} {status_emoji} <b>{booking['service_name']}</b>\n"
        text += f"👤 {booking['user_name']} (ID: {booking['user_id']})\n"
        text += f"📅 {booking['date']} {booking['time']} • ₹{booking['price']}\n"
        text += f"Status: {booking['status'].upper()}\n\n"
    
    await query.edit_message_text(text, parse_mode="HTML")

async def handle_admin_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin earnings button."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id != ADMIN_USER_ID:
        await query.answer("⛔ Admin only")
        return
    
    from services.database import get_revenue_stats
    stats = get_revenue_stats()
    
    text = f"""
<b>💰 Earnings Report</b>

<b>Total Revenue:</b> ₹{stats['total_revenue']:,}
<b>Total Bookings:</b> {stats['total_bookings']}

<b>Today's Performance:</b>
• Bookings: {stats['today_bookings']}
• Revenue: ₹{stats['today_revenue']:,}
"""
    await query.edit_message_text(text, parse_mode="HTML")
