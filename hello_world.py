"""
PayWire Hello World v3 — audit trail.
 
What's new vs v2:
 - Every transaction is now tagged with the full audit chain:
   agent_id, principal_id, prompt_hash, model_version, policy_version, timestamp.
 - New tool: query_audit_trail — agent (or CFO) can ask "what did principal X
   spend across all agents today?"
 - Demonstrates G2 (multi-agent audit trail) from the PayWire design doc.
 
The CFO test: at any moment, you can answer "which agent spent what, under
whose authority, in response to which prompt." Right now no agent
infrastructure answers that natively. PayWire does.
 
Run:
    python hello_world.py
"""
 
import os
import json
import hashlib
import secrets
from datetime import datetime, timezone
 
from anthropic import Anthropic
from dotenv import load_dotenv
 
load_dotenv()
 
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-6"
POLICY_VERSION = "v0.1"
 
# --- "Database" ----------------------------------------------------------
 
ISSUED_CARDS: dict[str, dict] = {}
AUDIT_LOG: list[dict] = []  # G2: every transaction lives here, approved or not
 
 
def _now_iso():
    return datetime.now(timezone.utc).isoformat()
 
 
def _hash_prompt(prompt):
    """Hash the originating prompt for provenance (privacy + audit balance)."""
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]
 
 
# --- Tool definitions: 3 tools now (issue, attempt, query) ----------------
 
tools = [
    {
        "name": "issue_virtual_card",
        "description": (
            "Issue a virtual card tied to an agent_id under a principal. "
            "Returns a card_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "principal_id": {"type": "string"},
                "amount_usd": {"type": "number"},
                "merchant_whitelist": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "purpose": {"type": "string"},
            },
            "required": ["agent_id", "principal_id", "amount_usd", "purpose"],
        },
    },
    {
        "name": "attempt_purchase",
        "description": (
            "Try to charge a card. PayWire authorizes in real time and logs "
            "the full audit chain (approved OR declined)."
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
    {
        "name": "query_audit_trail",
        "description": (
            "Return the audit log of transactions. Filter by agent_id or "
            "principal_id to scope. Use this to answer 'what did X spend?'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_by_agent_id": {"type": "string"},
                "filter_by_principal_id": {"type": "string"},
            },
        },
    },
]
 
 
# --- The PayWire functions ----------------------------------------------
 
def issue_virtual_card(agent_id, principal_id, amount_usd, purpose,
                      merchant_whitelist=None):
    card_id = f"ic_mock_{secrets.token_hex(6)}"
    ISSUED_CARDS[card_id] = {
        "agent_id": agent_id,
        "principal_id": principal_id,
        "per_purchase_cap_usd": amount_usd,
        "merchant_whitelist": merchant_whitelist or ["*"],
        "purpose": purpose,
        "issued_at": _now_iso(),
    }
    return {
        "card_id": card_id,
        "agent_id": agent_id,
        "principal_id": principal_id,
        "amount_usd_limit": amount_usd,
        "allowed_merchants": merchant_whitelist or ["*"],
        "status": "active",
        "_mock": True,
    }
 
 
def attempt_purchase(card_id, amount_usd, merchant, prompt_hash="unknown"):
    card = ISSUED_CARDS.get(card_id)
    if not card:
        return {"approved": False, "reason": f"unknown card {card_id}"}
 
    # Run the authorization
    if amount_usd > card["per_purchase_cap_usd"]:
        result = {
            "approved": False,
            "reason": f"amount ${amount_usd} exceeds cap ${card['per_purchase_cap_usd']}",
        }
    elif "*" not in card["merchant_whitelist"] and merchant not in card["merchant_whitelist"]:
        result = {
            "approved": False,
            "reason": f"merchant '{merchant}' not in whitelist {card['merchant_whitelist']}",
        }
    else:
        result = {"approved": True, "txn_id": f"txn_{secrets.token_hex(4)}"}
 
    # G2: log EVERY attempt — approved or declined — with full provenance
    AUDIT_LOG.append({
        "timestamp": _now_iso(),
        "agent_id": card["agent_id"],
        "principal_id": card["principal_id"],
        "card_id": card_id,
        "amount_usd": amount_usd,
        "merchant": merchant,
        "approved": result["approved"],
        "reason": result.get("reason"),
        "txn_id": result.get("txn_id"),
        "prompt_hash": prompt_hash,
        "model_version": MODEL,
        "policy_version": POLICY_VERSION,
    })
 
    return result
 
 
def query_audit_trail(filter_by_agent_id=None, filter_by_principal_id=None):
    rows = AUDIT_LOG
    if filter_by_agent_id:
        rows = [r for r in rows if r["agent_id"] == filter_by_agent_id]
    if filter_by_principal_id:
        rows = [r for r in rows if r["principal_id"] == filter_by_principal_id]
    return {"count": len(rows), "transactions": rows}
 
 
# --- Agent loop ----------------------------------------------------------
 
def run_agent(user_request, max_turns=10):
    print(f"\n🧑  User: {user_request}\n")
    prompt_hash = _hash_prompt(user_request)
 
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
                print(
                    f"💳  PayWire issued: agent_id={result['agent_id']} "
                    f"card_id={result['card_id']}\n"
                )
            elif block.name == "attempt_purchase":
                result = attempt_purchase(prompt_hash=prompt_hash, **block.input)
                status = (
                    "APPROVED ✅"
                    if result["approved"]
                    else f"DECLINED ❌ — {result['reason']}"
                )
                print(f"   → {status}\n")
            elif block.name == "query_audit_trail":
                result = query_audit_trail(**block.input)
                print(f"📊  Audit trail: {result['count']} transactions")
                for txn in result["transactions"]:
                    sym = "✅" if txn["approved"] else "❌"
                    line = (
                        f"   {sym} {txn['timestamp']} | "
                        f"agent={txn['agent_id']} | "
                        f"${txn['amount_usd']} @ {txn['merchant']} | "
                        f"prompt={txn['prompt_hash']}"
                    )
                    print(line)
                print()
            else:
                result = {"error": f"unknown tool {block.name}"}
 
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })
 
        messages.append({"role": "user", "content": tool_results})
 
 
# --- Four demo runs ------------------------------------------------------
 
if __name__ == "__main__":
    print("=" * 60)
    print(" Test 1: APPROVE — research-bot, $15 @ amazon.com")
    print("=" * 60)
    run_agent(
        "Issue a card for agent_id 'research-bot' under principal 'alexis', "
        "$20 cap, amazon.com only. Then buy a $15 USB-C cable from amazon.com."
    )
 
    print("=" * 60)
    print(" Test 2: DECLINE over budget — shopping-bot, $99 @ amazon.com")
    print("=" * 60)
    run_agent(
        "Issue a card for agent_id 'shopping-bot' under principal 'alexis', "
        "$20 cap, amazon.com only. Then attempt a $99 keyboard from amazon.com."
    )
 
    print("=" * 60)
    print(" Test 3: DECLINE wrong merchant — travel-bot, $10 @ ebay.com")
    print("=" * 60)
    run_agent(
        "Issue a card for agent_id 'travel-bot' under principal 'alexis', "
        "$50 cap, amazon.com only. Then attempt a $10 purchase from ebay.com."
    )
 
    print("=" * 60)
    print(" Test 4: CFO query — show me everything principal 'alexis' did today")
    print("=" * 60)
    run_agent(
        "Query the full audit trail for principal 'alexis'. Show every "
        "transaction across all agents."
    )
 
