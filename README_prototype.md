# PayWire Hello World — Day 2 prototype

Proves the core PayWire wiring works end-to-end:
agent ↦ Claude reasoning ↦ tool call ↦ Stripe Issuing API ↦ virtual card.

## Setup (5 min)

```bash
# 1. Create the project folder
mkdir paywire-sdk-python && cd paywire-sdk-python

# 2. Create + activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate           # (Windows: venv\Scripts\activate)

# 3. Drop the files in this directory:
#    - hello_world.py
#    - requirements.txt
#    - .env.example

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy the env template + fill in your real keys
cp .env.example .env
# now edit .env and paste in:
#   ANTHROPIC_API_KEY=sk-ant-...    (from console.anthropic.com)
#   STRIPE_SECRET_KEY=sk_test_...   (from dashboard.stripe.com → Developers → API Keys, TEST MODE)

# 6. Run it
python hello_world.py
```

## What you should see

```
🧑  User: I need you to buy me a USB-C cable for my robotics project. Budget is $20 max.

🤖  Claude: I'll issue a virtual card with a $20 spending limit for the USB-C cable purchase.

🛠  Claude called tool: issue_virtual_card
   with inputs: {
     "amount_usd": 20,
     "merchant_description": "USB-C cable for robotics project"
   }

💳  PayWire issued a virtual card:
{
  "card_id": "ic_1Q...",
  "cardholder_id": "ich_1Q...",
  "amount_usd_limit": 20,
  "purpose": "USB-C cable for robotics project",
  "status": "active",
  "brand": "Visa",
  "last4": "4242"
}
```

If you see that output, **the PayWire MVP works end-to-end.** Commit + push.

## If something breaks

- **"Issuing is not enabled"** → Stripe Dashboard → Test mode → More products → Issuing → Enable. Free in test mode.
- **"Invalid API key"** → check your `.env`. Stripe key must start with `sk_test_` (not `sk_live_`).
- **`ModuleNotFoundError`** → run `pip install -r requirements.txt` again with venv activated.
- **Claude returns text but no tool call** → tweak the prompt to be more imperative ("Issue a virtual card for…")

## What this is NOT yet

This is a 100-line proof of wiring. The real SDK will add:

- Per-call vs per-day vs per-merchant spend limits (you have only per_authorization here)
- Agent identity attestation (JWT signing)
- Real-time authorization webhook (the customer's code approving/denying)
- Audit log with prompt_hash, model_version, etc.
- Provider neutrality (Lithic adapter)
- Two-line install via a `paywire` package on PyPI

That's the next 90 days. This is Day 2.
