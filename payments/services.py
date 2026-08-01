"""Mock payment gateway — in a real system this would call Razorpay/Stripe/etc.
Here it just deterministically succeeds, so the demo flow is repeatable.
"""
from django.utils import timezone
from .models import Payment


def process_payment(payment: Payment, simulate_failure: bool = False) -> Payment:
    payment.status = "FAILED" if simulate_failure else "SUCCESS"
    payment.save(update_fields=["status"])

    if payment.status == "SUCCESS" and payment.invoice:
        payment.invoice.status = "PAID"
        payment.invoice.save(update_fields=["status"])

    return payment
