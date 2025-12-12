from stripe_sandbox import StripeGateway

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_payment_details(payment_data):
    """Print payment details in a formatted way"""
    for key, value in payment_data.items():
        print(f"  {key.upper():<20}: {value}")

if __name__ == "__main__":
    stripe_service = StripeGateway()

    # 1) Create Payment Intent
    print_section("1. Creating Payment Intent")
    payment = stripe_service.create_payment_intent(amount=19.99)
    payment_data = stripe_service.format_payment_intent(payment)
    print_payment_details(payment_data)

    # 2) Confirm Payment
    print_section("2. Confirming Payment")
    confirmed = stripe_service.confirm_payment(
        payment_intent_id=payment.id,
        payment_method="pm_card_visa"
    )
    confirmed_data = stripe_service.format_payment_intent(confirmed)
    print_payment_details(confirmed_data)

    print("\n" + "="*60)
    print("  ✓ Payment Process Completed Successfully")
    print("="*60 + "\n")
