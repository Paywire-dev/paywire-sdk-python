"""
PayWire Hello World — Day 2 prototype (mock issuer).

Stripe Issuing requires a verified US business (Delaware C-Corp + compliance
approval). We don't have that yet. For the prototype, we MOCK the issuer.
The wiring — agent → Claude → tool call → issuer — is what matters.

Architecture upside: this is exactly the "provider-neutral" goal from the
PayWire design doc (Section 2 / G5). The issuer is an abstracted function
call. In Month 6, when we incorporate via Stripe Atlas, we swap the body of
`issue_virtual_card` to call real Stripe Issuing or Lithic. 5-line change.

Run:
    python hello_world.py
"""

import os
import json
import secrets

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"

# --- Tool definition (what Claude is allowed to ask for) -----------------

tools = [
    {
        "name": "issue_virtual_card",
        "description": (
            "Issue a virtual payment card for a one-time purchase. "
            "Returns a card token the agent can use to pay a merchant."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "amount_usd": {
                    "type": "number",
                    "description": "Maximum spend allowed on this card, in USD.",
                },
                "merchant_description": {
                    "type": "string",
                    "description": "Brief description of what the agent is buying.",
                },
            },
            "required": ["amount_usd", "merchant_description"],
        },
    }
]


# --- The "PayWire" issuer function (MOCKED for now) -----------------------

def issue_virtual_card(amount_usd: float, merchant_description: str) -> dict:
    """Mock issuer. Returns realistic-looking card data without hitting
    Stripe.

    Replace this body in Month 6 with real stripe.issuing.Card.create()
    once PayWire is incorporated and has issuer access.
    """
    return {
        "card_id": f"ic_mock_{secrets.token_hex(8)}",
        "cardholder_id": f"ich_mock_{secrets.token_hex(8)}",
        "card_token": f"tok_pw_{secrets.token_hex(12)}",
        "amount_usd_limit": amount_usd,
        "purpose": merchant_description,
        "status": "active",
        "brand": "Visa",
        "last4": str(secrets.randbelow(10000)).zfill(4),
        "_mock": True,  # so we never confuse this with a real card later
    }


# --- Agent loop -----------------------------------------------------------

def run_agent(user_request: str) -> None:
    print(f"\n🧑  User: {user_request}\n")

    response = anthropic_client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=tools,
        messages=[{"role": "user", "content": user_request}],
    )

    for block in response.content:
        if block.type == "text":
            print(f"🤖  Claude: {block.text}\n")
        elif block.type == "tool_use":
            print(f"🛠  Claude called tool: {block.name}")
            print(f"   with inputs: {json.dumps(block.input, indent=2)}\n")

            result = issue_virtual_card(**block.input)
            print("💳  PayWire issued a virtual card (mock):")
            print(json.dumps(result, indent=2))
            print()


if __name__ == "__main__":
    run_agent(
        "I need you to buy me a USB-C cable for my robotics project. "
        "Budget is $20 max."
    )
