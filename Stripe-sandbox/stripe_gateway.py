"""
Stripe Payment Gateway
======================
A simple module for payments with Stripe

How Stripe works:
1. Create a Session → Stripe gives you a payment URL
2. Send user to that URL → they pay
3. Stripe calls your Webhook → you know if payment succeeded
"""

import stripe
from typing import Dict, Any


class StripeGateway:

    def __init__(
        self,
        api_key: str,
        webhook_secret: str,
        success_url: str,
        cancel_url: str,
    ):
        """
        :param api_key: API key from Stripe Dashboard (starts with sk_test_ or sk_live_)
        :param webhook_secret: Webhook key from Stripe Dashboard (starts with whsec_)
        :param success_url: Where user goes after successful payment
        :param cancel_url: Where user goes if they cancel
        """
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self.success_url = success_url
        self.cancel_url = cancel_url
        stripe.api_key = api_key

    # ══════════════════════════════════════════════════════════════════════════
    # Create Session - One-Time Payment
    # ══════════════════════════════════════════════════════════════════════════
    def create_one_time_session(
        self,
        product_name: str,
        amount: float,
        metadata: Dict[str, str],
        currency: str = "usd",
    ) -> Dict[str, Any]:
        """
        Create a one-time payment checkout link
        
        :param product_name: Product name shown to user
        :param amount: Amount in dollars (e.g., 10.50)
        :param metadata: Your data returned in webhook (e.g., {"order_id": "123"})
        :param currency: Currency code
        
        :return: {"success": True, "url": "https://checkout.stripe.com/...", "session_id": "cs_xxx"}
        
        Example:
            result = gateway.create_one_time_session(
                product_name="Buy 100 coins",
                amount=5.00,
                metadata={"user_id": "123", "coins": "100"}
            )
            # Send user to result["url"]
        """
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                success_url=self.success_url,
                cancel_url=self.cancel_url,
                metadata=metadata,
                payment_intent_data={"metadata": metadata},  # metadata also return in webhook 
                line_items=[{
                    "quantity": 1,
                    "price_data": {
                        "currency": currency,
                        "unit_amount": int(amount * 100),
                        "product_data": {"name": product_name},
                    },
                }],
            )
            return {"success": True, "url": session.url, "session_id": session.id}
        
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}

    # ══════════════════════════════════════════════════════════════════════════
    # Create Session - Subscription Payment (Recurring)
    # ══════════════════════════════════════════════════════════════════════════
    def create_subscription_session(
        self,
        product_name: str,
        amount: float,
        interval: str,
        metadata: Dict[str, str],
        interval_count: int = 1,
        currency: str = "usd",
    ) -> Dict[str, Any]:
        """
        Create a subscription checkout link
        
        :param product_name: Plan name
        :param amount: Amount per period in dollars
        :param interval: Billing period → "day" | "week" | "month" | "year"
        :param metadata: Your data returned in webhook
        :param interval_count: How many intervals between billings (e.g., 3 = every 3 months)
        :param currency: Currency code
        
        :return: {"success": True, "url": "...", "session_id": "cs_xxx"}
        
        Example:
            result = gateway.create_subscription_session(
                product_name="VIP Subscription",
                amount=9.99,
                interval="month",
                metadata={"user_id": "123", "plan": "vip"}
            )
        """
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                payment_method_types=["card"],
                success_url=self.success_url,
                cancel_url=self.cancel_url,
                metadata=metadata,
                subscription_data={"metadata": metadata},  # metadata در webhook هم باشه
                line_items=[{
                    "quantity": 1,
                    "price_data": {
                        "currency": currency,
                        "unit_amount": int(amount * 100),
                        "product_data": {"name": product_name},
                        "recurring": {
                            "interval": interval,
                            "interval_count": interval_count,
                        },
                    },
                }],
            )
            return {"success": True, "url": session.url, "session_id": session.id}
        
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}

    # ══════════════════════════════════════════════════════════════════════════
    # Cancel Subscription
    # ══════════════════════════════════════════════════════════════════════════
    def cancel_subscription(self, stripe_subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a subscription
        
        :param stripe_subscription_id: Subscription ID from Stripe (sub_xxx) - get from webhook
        :return: {"success": True, "status": "canceled"}
        """
        try:
            result = stripe.Subscription.delete(stripe_subscription_id)
            return {"success": True, "status": result["status"]}
        
        except stripe.error.StripeError as e:
            return {"success": False, "error": str(e)}

    # ══════════════════════════════════════════════════════════════════════════
    # Webhook - Verify Signature
    # ══════════════════════════════════════════════════════════════════════════
    def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Verify that the request really came from Stripe
        
        :param payload: Request body → request.get_data()
        :param signature: Signature header → request.headers.get("Stripe-Signature")
        :return: {"success": True, "event": {...}}
        """
        try:
            event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
            return {"success": True, "event": event}
        
        except ValueError:
            return {"success": False, "error": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            return {"success": False, "error": "Invalid signature"}

    # ══════════════════════════════════════════════════════════════════════════
    # Webhook - Parse Event
    # ══════════════════════════════════════════════════════════════════════════
    def parse_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse event and extract important information
        
        :param event: From verify_webhook
        :return: Payment information including your metadata
        
        Important outputs:
        - is_paid: Was payment successful?
        - payment_type: "one_time" or "subscription"
        - metadata: Same data you provided when creating session
        """
        event_type = event["type"]
        data = event["data"]["object"]

        # Subscription payment - succeeded (happens every billing period)
        if event_type == "invoice.payment_succeeded":
            metadata = (data.get("subscription_details") or {}).get("metadata", {})
            return {
                "is_paid": True,
                "event_type": event_type,
                "payment_type": "subscription",
                "metadata": metadata,
                "amount": data["amount_paid"] / 100,
                "currency": data["currency"],
                "stripe_subscription_id": data.get("subscription"),
                "stripe_customer_id": data.get("customer"),
            }

        # Subscription payment - failed
        if event_type == "invoice.payment_failed":
            metadata = (data.get("subscription_details") or {}).get("metadata", {})
            return {
                "is_paid": False,
                "event_type": event_type,
                "payment_type": "subscription",
                "metadata": metadata,
                "stripe_subscription_id": data.get("subscription"),
            }

        # One-time payment - succeeded
        if event_type == "payment_intent.succeeded":
            return {
                "is_paid": True,
                "event_type": event_type,
                "payment_type": "one_time",
                "metadata": data.get("metadata", {}),
                "amount": data["amount"] / 100,
                "currency": data["currency"],
                "stripe_payment_id": data["id"],
            }

        # One-time payment - failed
        if event_type == "payment_intent.payment_failed":
            return {
                "is_paid": False,
                "event_type": event_type,
                "payment_type": "one_time",
                "metadata": data.get("metadata", {}),
                "stripe_payment_id": data["id"],
            }

        # Subscription canceled
        if event_type == "customer.subscription.deleted":
            return {
                "is_paid": False,
                "event_type": event_type,
                "payment_type": "subscription_canceled",
                "metadata": data.get("metadata", {}),
                "stripe_subscription_id": data["id"],
            }

        # Other events
        return {
            "is_paid": False,
            "event_type": event_type,
            "payment_type": "unknown",
            "metadata": {},
        }
