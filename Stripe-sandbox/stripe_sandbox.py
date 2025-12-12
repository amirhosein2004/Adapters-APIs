import stripe
from config import STRIPE_TEST_SECRET_KEY, STRIPE_CURRENCY

class StripeGateway:
    def __init__(self):
        stripe.api_key = STRIPE_TEST_SECRET_KEY

    def create_payment_intent(self, amount: float):
        # Stripe accespt the amount in cents
        amount_in_cents = int(amount * 100)

        payment_intent = stripe.PaymentIntent.create( # send POST request to Stripe
            amount=amount_in_cents,
            currency=STRIPE_CURRENCY,
            payment_method_types=["card"]
        )

        return payment_intent

    def confirm_payment(self, payment_intent_id: str, payment_method: str):
        payment_intent = stripe.PaymentIntent.confirm(
            payment_intent_id,
            payment_method=payment_method
        )
        return payment_intent

    def format_payment_intent(self, payment_intent):
        """Format payment intent data for clean display"""
        return {
            "id": payment_intent.id,
            "amount": f"${payment_intent.amount / 100:.2f}",
            "currency": payment_intent.currency.upper(),
            "status": payment_intent.status,
            "client_secret": payment_intent.client_secret[:20] + "..." if payment_intent.client_secret else None,
            "created": payment_intent.created,
        }
