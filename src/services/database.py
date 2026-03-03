import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.getenv("DB_PATH", "./data/bookings.db")

def init_db():
    """Initialize the database with required tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            service_key TEXT NOT NULL,
            service_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            payment_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reminder_sent BOOLEAN DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_date TEXT NOT NULL,
            slot_time TEXT NOT NULL,
            is_booked BOOLEAN DEFAULT 0,
            booking_id INTEGER,
            UNIQUE(slot_date, slot_time)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_booking(user_id: int, user_name: str, service_key: str, service_name: str, 
                price: int, booking_date: str, booking_time: str) -> int:
    """Add a new booking and return booking ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO bookings (user_id, user_name, service_key, service_name, price, booking_date, booking_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, service_key, service_name, price, booking_date, booking_time))
    
    booking_id = cursor.lastrowid
    
    # Mark time slot as booked
    cursor.execute('''
        INSERT OR REPLACE INTO time_slots (slot_date, slot_time, is_booked, booking_id)
        VALUES (?, ?, 1, ?)
    ''', (booking_date, booking_time, booking_id))
    
    conn.commit()
    conn.close()
    return booking_id

def get_user_bookings(user_id: int) -> List[Dict[str, Any]]:
    """Get all bookings for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, service_name, price, booking_date, booking_time, status, created_at
        FROM bookings WHERE user_id = ? ORDER BY booking_date DESC, booking_time DESC
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "service_name": row[1],
            "price": row[2],
            "date": row[3],
            "time": row[4],
            "status": row[5],
            "created_at": row[6]
        }
        for row in rows
    ]

def get_all_bookings(limit: int = 50) -> List[Dict[str, Any]]:
    """Get all bookings (for admin)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.id, b.user_id, b.user_name, b.service_name, b.price, 
               b.booking_date, b.booking_time, b.status, b.created_at
        FROM bookings b ORDER BY b.created_at DESC LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row[0],
            "user_id": row[1],
            "user_name": row[2],
            "service_name": row[3],
            "price": row[4],
            "date": row[5],
            "time": row[6],
            "status": row[7],
            "created_at": row[8]
        }
        for row in rows
    ]

def update_payment(booking_id: int, payment_method: str, payment_id: str):
    """Update booking with payment details."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE bookings SET payment_method = ?, payment_id = ?, status = 'confirmed'
        WHERE id = ?
    ''', (payment_method, payment_id, booking_id))
    
    conn.commit()
    conn.close()

def get_booking_by_id(booking_id: int) -> Optional[Dict[str, Any]]:
    """Get a single booking by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, user_id, user_name, service_name, price, booking_date, booking_time, status
        FROM bookings WHERE id = ?
    ''', (booking_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "user_id": row[1],
            "user_name": row[2],
            "service_name": row[3],
            "price": row[4],
            "date": row[5],
            "time": row[6],
            "status": row[7]
        }
    return None

def cancel_booking(booking_id: int) -> bool:
    """Cancel a booking and free up the time slot."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get booking details first
    cursor.execute('SELECT booking_date, booking_time FROM bookings WHERE id = ?', (booking_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False
    
    # Cancel booking
    cursor.execute('UPDATE bookings SET status = ? WHERE id = ?', ('cancelled', booking_id))
    
    # Free up time slot
    cursor.execute('''
        DELETE FROM time_slots WHERE slot_date = ? AND slot_time = ?
    ''', (row[0], row[1]))
    
    conn.commit()
    conn.close()
    return True

def get_revenue_stats() -> Dict[str, Any]:
    """Get revenue statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Total revenue
    cursor.execute('''
        SELECT COALESCE(SUM(price), 0) FROM bookings WHERE status = 'confirmed'
    ''')
    total_revenue = cursor.fetchone()[0]
    
    # Today's bookings
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        SELECT COUNT(*), COALESCE(SUM(price), 0) FROM bookings 
        WHERE booking_date = ? AND status = 'confirmed'
    ''', (today,))
    today_stats = cursor.fetchone()
    
    # Total bookings
    cursor.execute('SELECT COUNT(*) FROM bookings')
    total_bookings = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_revenue": total_revenue,
        "today_bookings": today_stats[0],
        "today_revenue": today_stats[1],
        "total_bookings": total_bookings
    }

def is_slot_available(date: str, time: str) -> bool:
    """Check if a time slot is available."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT is_booked FROM time_slots WHERE slot_date = ? AND slot_time = ?
    ''', (date, time))
    
    row = cursor.fetchone()
    conn.close()
    
    return row is None or not row[0]
