import os
import requests
import json

INSTAMOJO_API_KEY = os.getenv("INSTAMOJO_API_KEY")
INSTAMOJO_AUTH_TOKEN = os.getenv("INSTAMOJO_AUTH_TOKEN")
INSTAMOJO_SALT = os.getenv("INSTAMOJO_SALT")
ENABLE_INSTAMOJO = os.getenv("ENABLE_INSTAMOJO", "true").lower() == "true"

# Instamojo API base URL (use sandbox for testing)
INSTAMOJO_BASE_URL = "https://www.instamojo.com/api/1.1"

def create_payment_link(booking_id: int, service_name: str, amount: int, 
                        customer_name: str, customer_email: str, 
                        redirect_url: str = None) -> dict:
    """Create an Instamojo payment link.
    
    Returns:
        Dict with payment_url, payment_id, and status
    """
    if not ENABLE_INSTAMOJO or not INSTAMOJO_API_KEY or not INSTAMOJO_AUTH_TOKEN:
        return {
            "success": False,
            "error": "Instamojo not configured"
        }
    
    headers = {
        "X-Api-Key": INSTAMOJO_API_KEY,
        "X-Auth-Token": INSTAMOJO_AUTH_TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {
        "purpose": f"Booking #{booking_id}: {service_name}",
        "amount": str(amount),
        "buyer_name": customer_name,
        "email": customer_email,
        "send_email": False,
        "send_sms": False,
        "allow_repeated_payments": False
    }
    
    if redirect_url:
        payload["redirect_url"] = redirect_url
    
    try:
        response = requests.post(
            f"{INSTAMOJO_BASE_URL}/payment-requests/",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            payment_request = data.get("payment_request", {})
            return {
                "success": True,
                "payment_url": payment_request.get("longurl"),
                "payment_id": payment_request.get("id"),
                "status": payment_request.get("status")
            }
        else:
            return {
                "success": False,
                "error": data.get("message", "Unknown error")
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }

def verify_payment(payment_id: str, payment_request_id: str) -> dict:
    """Verify if a payment was successful.
    
    Returns:
        Dict with verified status and payment details
    """
    if not ENABLE_INSTAMOJO or not INSTAMOJO_API_KEY or not INSTAMOJO_AUTH_TOKEN:
        return {"verified": False, "error": "Instamojo not configured"}
    
    headers = {
        "X-Api-Key": INSTAMOJO_API_KEY,
        "X-Auth-Token": INSTAMOJO_AUTH_TOKEN
    }
    
    try:
        response = requests.get(
            f"{INSTAMOJO_BASE_URL}/payment-requests/{payment_request_id}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            payment_request = data.get("payment_request", {})
            payments = payment_request.get("payments", [])
            
            # Check if any payment matches our payment_id and is successful
            for payment in payments:
                if payment.get("payment_id") == payment_id and payment.get("status") == "Credit":
                    return {
                        "verified": True,
                        "amount": payment.get("amount"),
                        "fees": payment.get("fees"),
                        "payment_id": payment_id
                    }
            
            return {"verified": False, "status": "No successful payment found"}
        else:
            return {"verified": False, "error": data.get("message")}
            
    except requests.exceptions.RequestException as e:
        return {"verified": False, "error": str(e)}

def get_payment_status(payment_request_id: str) -> dict:
    """Get the status of a payment request."""
    if not ENABLE_INSTAMOJO or not INSTAMOJO_API_KEY or not INSTAMOJO_AUTH_TOKEN:
        return {"error": "Instamojo not configured"}
    
    headers = {
        "X-Api-Key": INSTAMOJO_API_KEY,
        "X-Auth-Token": INSTAMOJO_AUTH_TOKEN
    }
    
    try:
        response = requests.get(
            f"{INSTAMOJO_BASE_URL}/payment-requests/{payment_request_id}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
