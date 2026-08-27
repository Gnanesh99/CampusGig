import logging
import razorpay
from django.conf import settings

logger = logging.getLogger(__name__)


def create_razorpay_order(payment):
    """
    Creates a Razorpay order for the given Payment instance
    and updates the razorpay_order_id field.
    """
    # If an order already exists, return it
    if payment.razorpay_order_id:
        return payment.razorpay_order_id

    if not payment.amount or payment.amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    try:
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    except Exception as e:
        logger.error("Failed to initialize Razorpay client.")
        raise Exception("Payment gateway configuration error.")

    # Convert Decimal amount to paise (smallest currency unit for INR)
    amount_in_paise = int(payment.amount * 100)

    order_data = {
        'amount': amount_in_paise,
        'currency': 'INR',
        'receipt': str(payment.id),
    }

    try:
        # Create order in Razorpay
        razorpay_order = client.order.create(data=order_data)

        # Save order ID to payment record
        payment.razorpay_order_id = razorpay_order.get('id')
        payment.save(update_fields=['razorpay_order_id', 'updated_at'])

        return razorpay_order
    except Exception as e:
        # Catch any Razorpay API errors and log them without exposing secrets
        logger.error(f"Failed to create Razorpay order for Payment ID {payment.id}: {e}")
        raise Exception("Failed to communicate with the payment gateway. Please try again later.")
