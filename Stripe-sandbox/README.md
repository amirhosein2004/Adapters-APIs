# Stripe Sandbox Environment

A sandbox testing environment for Stripe payment processing. This module demonstrates how to create payment intents and confirm payments using Stripe's test API.

## Overview

This is a simple gateway code for connect to stripe
this gateway do two job:

1. Create PaymentIntent for start payment

2. Confirm PaymentIntent with a PaymentMethod


## Getting Started

### Installation

1. Go to Dir:
    ```bash
    cd Stripe-sandbox
    ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify your Stripe API key in `config.py`:
   ```python
   STRIPE_TEST_SECRET_KEY = "your_test_secret_key"
   STRIPE_CURRENCY = "usd"
   ```

### Running the Example

Execute the main script to test the payment flow:

```bash
py main.py
```

### Example Output

When you run the script, you'll see clean and organized output:

```
============================================================
  1. Creating Payment Intent
============================================================
  ID                  : pi_3SdT8EEv8ZVm0MQK0mI9b45F
  AMOUNT              : $19.98
  CURRENCY            : USD
  STATUS              : requires_payment_method
  CLIENT_SECRET       : pi_3SdT8EEv8ZVm0MQK0...
  CREATED             : 1765533566

============================================================
  2. Confirming Payment
============================================================
  ID                  : pi_3SdT8EEv8ZVm0MQK0mI9b45F
  AMOUNT              : $19.98
  CURRENCY            : USD
  STATUS              : succeeded
  CLIENT_SECRET       : pi_3SdT8EEv8ZVm0MQK0...
  CREATED             : 1765533566

============================================================
  ✓ Payment Process Completed Successfully
============================================================
```

## Configuration

Edit `config.py` to customize settings:

```python
STRIPE_TEST_SECRET_KEY = "sk_test_..."  # Your Stripe test secret key
STRIPE_CURRENCY = "usd"                  # Currency code (usd, eur, gbp, etc.)
```

## API

* stripe.PaymentIntent.create() --> Send POST request to Stripe 

  POST https://api.stripe.com/v1/payment_intents

* stripe.PaymentIntent.confirm() --> Send POST request to Stripe 

  POST https://api.stripe.com/v1/payment_intents/{id}/confirm