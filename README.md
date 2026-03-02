# DesiBooking Telegram Bot 🇮🇳

> Professional booking & payments bot for Indian businesses — UPI + Instamojo integrated

## Features

- 📋 **Service Catalog** — List your services with prices in ₹
- 📅 **Smart Booking** — Date/time slot picker with IST timezone
- 💸 **UPI Payments** — Instant QR code generation
- 💳 **Instamojo** — Card/netbanking fallback
- 🔔 **Reminders** — Automated booking reminders
- 📊 **Admin Dashboard** — Bookings, earnings, analytics

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/realmpastai-web/desi-booking-telegram-bot.git
cd desi-booking-telegram-bot
cp .env.example .env
# Edit .env with your Telegram bot token

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python src/main.py
```

## Environment Variables

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
INSTAMOJO_API_KEY=your_instamojo_key
INSTAMOJO_AUTH_TOKEN=your_instamojo_token
INSTAMOJO_SALT=your_webhook_salt
ADMIN_USER_ID=your_telegram_user_id
DB_PATH=bookings.db
```

## Pricing Tiers

| Plan | Price | Features |
|------|-------|----------|
| Free | ₹0 | 10 bookings/month, UPI only |
| Pro | ₹499/mo | Unlimited, Instamojo, reminders |
| Business | ₹1499/mo | Multi-staff, analytics, custom branding |

## Commands

- `/start` — Welcome & service menu
- `/book` — Start booking flow
- `/mybookings` — View your bookings
- `/cancel` — Cancel a booking
- `/help` — Help & support

**Admin Only:**
- `/admin` — Admin dashboard
- `/bookings` — View all bookings
- `/earnings` — View earnings report
- `/settings` — Configure services

## Deployment

```bash
# Docker
docker-compose up -d

# Railway
railway up
```

## License

MIT © QuantBitRealm

---
Built for Indian professionals 🇮🇳
