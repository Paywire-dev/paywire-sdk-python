"""
PayWire Hello World v2 — spend rule enforcement.

What's new vs v1:
 - Agent now has TWO tools (issue + attempt_purchase), not just one.
 - PayWire authorizes every purchase against the spend rules set at issuance.
 - Three demo runs: in-budget approve, over-budget decline, wrong-merchant decline.

This is PayWire G1 (programmatic spend governance) made concrete. The
issuer creates a card with rules; the authorizer enforces them in real
time before any transaction clears.

Run:
    python hello_world.py
"""

import os
import json
import secrets

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"

# In-memory "card database" — replaces real Stripe Issuing for now.
ISSUED_CARDS: dict[str, dict] = {}


# --- Tool definitions ------------------------------------------------------

tools = [
    {
        "name": "issue_virtual_card",
        "description": (
            "Issue a virtual card with spend rules. Returns a card_id "
            "that can be used in subsequent purchase attempts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "amount_usd": {
                    "type": "number",
                    "description": "Per-purchase cap, in USD.",
                },
                "merchant_whitelist": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Allowed merchant domains. Use ['*'] to allow any.",
                },
                "purpose": {"type": "string"},
            },
            "required": ["amount_usd", "purpose"],
        },
    },
    {
        "name": "attempt_purchase",
        "description": (
            "Try to charge a card. PayWire authorizes in real time against "
            "the spend rules set at issuance. Returns approved=true/false."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "card_id": {"type": "string"},
                "amount_usd": {"type": "number"},
                "merchant": {"type": "string"},
            },
            "required": ["card_id", "amount_usd", "merchant"],
        },
    },
]


# --- The PayWire issuer + real-time authorizer ---------------------------

def issue_virtual_card(amount_usd, purpose, merchant_whitelist=None):
    card_id = f"ic_mock_{secrets.token_hex(6)}"
    ISSUED_CARDS[card_id] = {
        "per_purchase_cap_usd": amount_usd,
        "merchant_whitelist": merchant_whitelist or ["*"],
        "purpose": purpose,
        "transactions": [],
    }
    return {
        "card_id": card_id,
        "amount_usd_limit": amount_usd,
        "allowed_merchants": merchant_whitelist or ["*"],
        "purpose": purpose,
        "status": "active",
        "_mock": True,
    }


def attempt_purchase(card_id, amount_usd, merchant):
    """PayWire's real-time authorization hook. Every payment company wants
    this layer; nobody offers it today as a clean primitive."""
    card = ISSUED_CARDS.get(card_id)
    if not card:
        return {"approved": False, "reason": f"unknown card {card_id}"}

    # Rule 1: per-purchase cap
    if amount_usd > card["per_purchase_cap_usd"]:
        return {
            "approved": False,
            "reason": (
                f"amount ${amount_usd} exceeds per-purchase cap of "
                f"${card['per_purchase_cap_usd']}"
            ),
        }

    # Rule 2: merchant whitelist
    allowed = card["merchant_whitelist"]
    if "*" not in allowed and merchant not in allowed:
        return {
            "approved": False,
            "reason": f"merchant '{merchant}' not in whitelist {allowed}",
        }

    # Approved — record the transaction.
    txn = {
        "merchant": merchant,
        "amount_usd": amount_usd,
        "txn_id": f"txn_{secrets.token_hex(4)}",
    }
    card["transactions"].append(txn)
    return {
        "approved": True,
        "txn_id": txn["txn_id"],
        "card_id": card_id,
    }


# --- Agent loop (multi-turn) ---------------------------------------------

def run_agent(user_request, max_turns=6):
    print(f"\n🧑  User: {user_request}\n")
    messages = [{"role": "user", "content": user_request}]

    for _ in range(max_turns):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        text_blocks = [b.text for b in resp.content if b.type == "text"]
        if text_blocks:
            print(f"🤖  Claude: {' '.join(text_blocks)}\n")

        if resp.stop_reason != "tool_use":
            return

        messages.append({"role": "assistant", "content": resp.content})

        tool_results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue

            print(f"🛠  {block.name}({json.dumps(block.input)})")

            if block.name == "issue_virtual_card":
                result = issue_virtual_card(**block.input)
                print(f"💳  PayWire issued: {json.dumps(result, indent=2)}\n")
            elif block.name == "attempt_purchase":
                result = attempt_purchase(**block.input)
                if result["approved"]:
                    print(f"✅  PayWire APPROVED: {json.dumps(result, indent=2)}\n")
                else:
                    print(f"❌  PayWire DECLINED: {result['reason']}\n")
            else:
                result = {"error": f"unknown tool {block.name}"}

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})


# --- Three demo runs ------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print(" Test 1: in-budget + allowed merchant → APPROVE")
    print("=" * 60)
    run_agent(
        "Issue me a virtual card with a $20 cap, only usable at amazon.com. "
        "Then use it to buy a USB-C cable from amazon.com for $15."
    )

    print("=" * 60)
    print(" Test 2: over-budget → DECLINE")
    print("=" * 60)
    run_agent(
        "Issue me a virtual card with a $20 cap, usable at amazon.com. "
        "Then attempt to buy a $99 keyboard from amazon.com."
    )

    print("=" * 60)
    print(" Test 3: wrong merchant → DECLINE")
    print("=" * 60)
    run_agent(
        "Issue me a $50 card limited to amazon.com only. "
        "Then attempt a $10 purchase from ebay.com."
    )
