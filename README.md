# DesiBooking Telegram Bot

🚀 **India's simplest booking bot for professionals** — consultants, coaches, astrologers, tutors, and service providers.

## Features

- ✅ **Service Catalog** — List services with prices in INR (₹)
- 📅 **Smart Booking** — Date & time slot selection
- 📱 **UPI Payments** — Generate QR codes for PhonePe, GPay, Paytm
- 💳 **Instamojo Integration** — Card & netbanking payments
- 🔔 **Automatic Reminders** — Booking confirmations
- 👨‍💼 **Admin Dashboard** — Manage bookings & view earnings

## Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/realmpastai-web/desi-booking-telegram-bot.git
cd desi-booking-telegram-bot
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
ADMIN_USER_ID=your_telegram_user_id
UPI_ID=yourname@upi
UPI_NAME=Your Business Name
```

Optional (for Instamojo):
```env
INSTAMOJO_API_KEY=your_instamojo_key
INSTAMOJO_AUTH_TOKEN=your_instamojo_token
ENABLE_INSTAMOJO=true
```

### 3. Run with Docker

```bash
docker-compose up -d
```

### 4. Or Run Locally

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run bot
cd src
python main.py
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Browse services & book |
| `/mybookings` | View your bookings |
| `/cancel` | Cancel a booking |
| `/help` | Get help |
| `/admin` | Admin dashboard (admin only) |
| `/bookings` | View all bookings (admin only) |
| `/earnings` | Revenue report (admin only) |

## Payment Flow

1. User selects service → date → time
2. Chooses payment method:
   - **UPI**: QR code generated, user scans with any app
   - **Instamojo**: Secure payment link for cards/netbanking
3. Booking confirmed after payment verification
4. Reminders sent before appointment

## Customization

### Add/Edit Services

Edit `src/handlers/commands.py`:

```python
SERVICES = {
    "consultation": {"name": "1-on-1 Consultation", "price": 999, "duration": 60},
    "coaching": {"name": "Business Coaching", "price": 2499, "duration": 90},
    # Add your services here
}
```

### Change Time Slots

Edit `src/handlers/callbacks.py`:

```python
TIME_SLOTS = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]
```

## Monetization Tiers

| Tier | Price | Features |
|------|-------|----------|
| Free | ₹0 | 10 bookings/month, UPI only |
| Pro | ₹499/mo | Unlimited bookings, Instamojo, reminders |
| Business | ₹1499/mo | Multi-staff, analytics, custom branding |

## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

Or manually:

```bash
railway login
railway init
railway up
```

## Project Structure

```
desi-booking-telegram-bot/
├── src/
│   ├── main.py              # Entry point
│   ├── handlers/
│   │   ├── commands.py      # Command handlers
│   │   └── callbacks.py     # Button click handlers
│   └── services/
│       ├── database.py      # SQLite database operations
│       ├── payments.py      # UPI QR generation
│       └── instamojo.py     # Instamojo integration
├── data/                    # SQLite database (created on run)
├── .env.example             # Environment template
├── docker-compose.yml       # Docker setup
├── Dockerfile               # Container definition
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Tech Stack

- **Framework**: python-telegram-bot v20+
- **Database**: SQLite (single) / PostgreSQL (multi-user)
- **Payments**: UPI QR, Instamojo API
- **Hosting**: Docker, Railway, Fly.io, VPS
- **Reminders**: APScheduler (coming soon)

## Support

Need help? Contact us on Telegram: [@realmpastai](https://t.me/realmpastai)

## License

MIT License — feel free to use, modify, and sell!

---

Built with ❤️ for Indian SMBs by [QuantBitRealm](https://github.com/realmpastai-web)
