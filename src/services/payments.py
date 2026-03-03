import qrcode
import io
from PIL import Image
import os

def generate_upi_qr(upi_id: str, upi_name: str, amount: int, transaction_note: str) -> io.BytesIO:
    """Generate a UPI QR code for payment.
    
    Args:
        upi_id: UPI ID (e.g., name@upi)
        upi_name: Business/Receiver name
        amount: Amount in INR
        transaction_note: Payment description
        
    Returns:
        BytesIO object containing PNG image
    """
    # Build UPI URI
    upi_uri = f"upi://pay?pa={upi_id}&pn={upi_name}&am={amount}&cu=INR&tn={transaction_note}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to BytesIO
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer

def get_upi_link(upi_id: str, upi_name: str, amount: int, transaction_note: str) -> str:
    """Get a UPI payment link that opens any UPI app.
    
    Returns a URL that can be clicked to open UPI apps.
    """
    return f"upi://pay?pa={upi_id}&pn={upi_name}&am={amount}&cu=INR&tn={transaction_note}"
