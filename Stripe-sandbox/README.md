# Stripe Payment Gateway

## 🔷 How Stripe Works

![Stripe Flow](./assets/flowchary.svg)


Summary:
1. Create a Session → Stripe gives you a payment URL
2. Send user to that URL → they pay
3. Stripe calls your Webhook → you know if payment succeeded

---

## 📦 Installation

```bash
pip install stripe
```

---

## ⚙️ Setup

```python
from stripe_gateway import StripeGateway

gateway = StripeGateway(
    api_key="sk_test_xxx",                    # From Stripe Dashboard
    webhook_secret="whsec_xxx",               # From Stripe Dashboard
    success_url="https://site.com/success",
    cancel_url="https://site.com/cancel",
)
```

---

## 💳 One-Time Payment

```python
result = gateway.create_one_time_session(
    product_name="Buy 100 coins",
    amount=5.00,                              # USD
    metadata={"user_id": "123", "coins": "100"}
)

if result["success"]:
    payment_url = result["url"]               # Send user here
    session_id = result["session_id"]
```

### Response:
```python
{
    "success": True,
    "url": "https://checkout.stripe.com/c/pay/cs_test_xxx",
    "session_id": "cs_test_xxx"
}
```

---

## 🔄 Subscription Payment (Recurring)

```python
result = gateway.create_subscription_session(
    product_name="VIP Monthly Subscription",
    amount=9.99,
    interval="month",                         # day | week | month | year
    metadata={"user_id": "123", "plan": "vip"}
)

if result["success"]:
    payment_url = result["url"]
```

### Cancel Subscription:
```python
# Get stripe_subscription_id from webhook
result = gateway.cancel_subscription("sub_1234567890")
```

---

## 🔔 What is Webhook?

Webhook is an endpoint on your server that Stripe calls to tell you about payment results.

Why is it needed?
- User might close tab after payment
- success_url is not reliable (user can go there manually)
- Only Webhook is trustworthy

### Setup in Stripe Dashboard:

1. Go to https://dashboard.stripe.com
2. Developers → Webhooks → Add endpoint
3. Set URL: `https://yoursite.com/webhook/stripe`
4. Select these Events:
   - `payment_intent.succeeded` (one-time payment succeeded)
   - `payment_intent.payment_failed` (one-time payment failed)
   - `invoice.payment_succeeded` (subscription payment succeeded)
   - `invoice.payment_failed` (subscription payment failed)
   - `customer.subscription.deleted` (subscription canceled)
5. Copy Webhook Secret (whsec_xxx)

### Webhook Code:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    
    # 1. Verify signature (make sure request is from Stripe)
    verify = gateway.verify_webhook(
        payload=request.get_data(),
        signature=request.headers.get("Stripe-Signature")
    )
    
    if not verify["success"]:
        return {"error": verify["error"]}, 400
    
    # 2. Parse event
    result = gateway.parse_webhook_event(verify["event"])
    
    # 3. Do your business logic
    if result["is_paid"]:
        
        # One-time payment succeeded
        if result["payment_type"] == "one_time":
            user_id = result["metadata"]["user_id"]
            coins = result["metadata"]["coins"]
            # Give coins to user
        
        # Subscription payment succeeded
        elif result["payment_type"] == "subscription":
            user_id = result["metadata"]["user_id"]
            plan = result["metadata"]["plan"]
            stripe_sub_id = result["stripe_subscription_id"]  # Save for later cancellation
            # Activate subscription
    
    # Subscription canceled
    if result["payment_type"] == "subscription_canceled":
        user_id = result["metadata"]["user_id"]
        # Deactivate subscription
    
    return {"received": True}
```

### parse_webhook_event Output:

```python
# One-time payment succeeded
{
    "is_paid": True,
    "event_type": "payment_intent.succeeded",
    "payment_type": "one_time",
    "metadata": {"user_id": "123", "coins": "100"},  # Same as when creating session
    "amount": 5.00,
    "currency": "usd",
    "stripe_payment_id": "pi_xxx"
}

# Subscription payment succeeded
{
    "is_paid": True,
    "event_type": "invoice.payment_succeeded",
    "payment_type": "subscription",
    "metadata": {"user_id": "123", "plan": "vip"},
    "amount": 9.99,
    "currency": "usd",
    "stripe_subscription_id": "sub_xxx",  # Needed for cancellation
    "stripe_customer_id": "cus_xxx"
}

# Subscription canceled
{
    "is_paid": False,
    "event_type": "customer.subscription.deleted",
    "payment_type": "subscription_canceled",
    "metadata": {"user_id": "123", "plan": "vip"},
    "stripe_subscription_id": "sub_xxx"
}
```

---

## 🏷️ What is Metadata?

Metadata is data you send when creating a session and Stripe returns it in the webhook.

Why is it important? Because you need to know who this payment is for and what it's for.

```python
# When creating session
metadata = {
    "user_id": "123",
    "order_id": "456",
    "product": "vip_plan"
}

# Same data comes back in webhook
result["metadata"]  # {"user_id": "123", "order_id": "456", "product": "vip_plan"}
```

---

## 💾 Storing stripe_subscription_id

For subscription payments, Stripe gives you a `stripe_subscription_id` (sub_xxx). This ID is **permanent** and **never changes** for that subscription.

**You MUST save it** because:
- You need it to cancel the subscription later
- It's the only way to identify the subscription in Stripe
- It stays the same for the entire subscription lifetime

### Where to save it:

Save it in your database when you receive the webhook:

```python
@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    verify = gateway.verify_webhook(...)
    result = gateway.parse_webhook_event(verify["event"])
    
    if result["payment_type"] == "subscription" and result["is_paid"]:
        user_id = result["metadata"]["user_id"]
        stripe_sub_id = result["stripe_subscription_id"]  # sub_xxx
        
        # Save to database
        db.update_user_subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_sub_id,  # SAVE THIS!
            status="active"
        )
    
    return {"received": True}
```

### Use it later to cancel:

```python
# When user wants to cancel
user = db.get_user(user_id)
stripe_sub_id = user.stripe_subscription_id  # Get from database

result = gateway.cancel_subscription(stripe_sub_id)
```

---

## 🔍 Understanding Webhook Events

### Important: Invoice vs Payment Intent

For **subscription payments**, Stripe sends `invoice` events, NOT `payment_intent` events.

- **One-time payment**: Uses `payment_intent` events
- **Subscription payment**: Uses `invoice` events

This is why in the webhook handler we check `invoice.payment_succeeded` for subscriptions.

### Webhook Event Flow:

```
One-Time Payment:
1. User pays
2. Stripe sends: payment_intent.succeeded
3. You get: payment_intent data

Subscription Payment:
1. User subscribes
2. Stripe sends: invoice.payment_succeeded (first payment)
3. You get: invoice data
4. Every billing period: invoice.payment_succeeded again
5. User cancels: customer.subscription.deleted
```

### Why verify_webhook is important:

```python
verify = gateway.verify_webhook(
    payload=request.get_data(),           # Raw request body from Stripe
    signature=request.headers.get("Stripe-Signature")  # Stripe's signature
)
```

This verifies that:
- The request really came from Stripe (not someone else)
- The data wasn't modified in transit
- Only then you process it

---

## 🚀 How to Use This in Your Project

This module provides the **core functionality** you need. Here's how to integrate it:

### Step 1: Initialize Gateway

```python
from stripe_gateway import StripeGateway

gateway = StripeGateway(
    api_key="sk_test_xxx",
    webhook_secret="whsec_xxx",
    success_url="https://yoursite.com/success",
    cancel_url="https://yoursite.com/cancel",
)
```

### Step 2: Create Payment Sessions

```python
# One-time payment
result = gateway.create_one_time_session(
    product_name="Buy coins",
    amount=5.00,
    metadata={"user_id": "123", "coins": "100"}
)

# Subscription
result = gateway.create_subscription_session(
    product_name="VIP Plan",
    amount=9.99,
    interval="month",
    metadata={"user_id": "123", "plan": "vip"}
)
```

### Step 3: Handle Webhook

```python
@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    verify = gateway.verify_webhook(
        payload=request.get_data(),
        signature=request.headers.get("Stripe-Signature")
    )
    
    if not verify["success"]:
        return {"error": verify["error"]}, 400
    
    result = gateway.parse_webhook_event(verify["event"])
    
    # Now customize based on YOUR business logic
    if result["is_paid"]:
        if result["payment_type"] == "one_time":
            # Your code: give coins to user
            pass
        elif result["payment_type"] == "subscription":
            # Your code: activate subscription, save stripe_subscription_id
            pass
    
    return {"received": True}
```

### Step 4: Cancel Subscription

```python
# When user wants to cancel
stripe_sub_id = db.get_user_subscription_id(user_id)
result = gateway.cancel_subscription(stripe_sub_id)
```

---

## 📝 Summary

This module handles:
- ✅ Creating payment sessions
- ✅ Creating subscription sessions
- ✅ Verifying webhook signatures
- ✅ Parsing webhook events
- ✅ Canceling subscriptions

You need to:
- ✅ Save `stripe_subscription_id` in your database
- ✅ Implement your business logic in webhook handler
- ✅ Customize metadata based on your needs
- ✅ Handle errors appropriately

---

## 🧪 Testing

### Test Card:
```
Number: 4242 4242 4242 4242
Date: 12/25
CVC: 123
```

### Test Webhook Locally:

1. Install ngrok: https://ngrok.com
2. Run: `ngrok http 5000`
3. Use the URL it gives you in Stripe Dashboard
4. Example: `https://abc123.ngrok.io/webhook/stripe`

---

## 📁 Structure

```
Stripe-sandbox/
├── stripe_gateway.py   # All code here
├── requirements.txt    # pip install stripe
└── README.md           # This file
```
