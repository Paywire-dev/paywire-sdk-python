"""
PayWire /authorize endpoint — v0.5.1
Mock issuer that authorizes (or denies) AI agent transactions in real time.
Same shape as Stripe Issuing's real-time authorization webhook:
the card network calls this endpoint; we must respond in < 2 seconds.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid
import jwt
import os

# --- Cryptographic signing (G3: Attestation) ---
JWT_SECRET = os.getenv("PAYWIRE_JWT_SECRET", "demo-secret-do-not-use-in-prod")
JWT_ALGORITHM = "HS256"


def sign_transaction(payload: dict) -> str:
    """Sign a transaction payload. Returns a JWT."""
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_signature(token: str) -> dict:
    """Verify a transaction JWT. Raises if invalid."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


app = FastAPI(title="PayWire Authorize", version="0.5.1")

# --- Policy (same rules as v3) ---
PER_CALL_CAP_USD = 25.00
ALLOWED_MERCHANTS = {"openai.com", "anthropic.com", "modal.com", "fal.ai"}

# --- In-memory audit trail ---
AUDIT_TRAIL = []


class AuthorizeRequest(BaseModel):
    agent_id: str
    principal_id: str
    merchant: str
    amount_usd: float
    prompt_hash: str
    model_version: str = "unknown"
    policy_version: str = "v0.4"


class AuthorizeResponse(BaseModel):
    approved: bool
    reason: str
    audit_id: str
    signature: str  # JWT attestation


@app.post("/authorize", response_model=AuthorizeResponse)
def authorize(req: AuthorizeRequest):
    """Approve or deny an agent-initiated transaction.

    In production: the card network calls this when the agent's card is
    swiped. We have < 2 seconds to decide.
    """
    audit_id = f"txn_{uuid.uuid4().hex[:12]}"

    if req.amount_usd > PER_CALL_CAP_USD:
        approved = False
        reason = f"amount ${req.amount_usd:.2f} exceeds per-call cap ${PER_CALL_CAP_USD:.2f}"
    elif req.merchant not in ALLOWED_MERCHANTS:
        approved = False
        reason = f"merchant '{req.merchant}' not in whitelist"
    else:
        approved = True
        reason = "merchant whitelisted, under cap"

    AUDIT_TRAIL.append({
        "audit_id": audit_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": req.agent_id,
        "principal_id": req.principal_id,
        "merchant": req.merchant,
        "amount_usd": req.amount_usd,
        "prompt_hash": req.prompt_hash,
        "model_version": req.model_version,
        "policy_version": req.policy_version,
        "approved": approved,
        "reason": reason,
    })

    # Sign the transaction for cryptographic attestation (G3)
    signature_payload = {
        "audit_id": audit_id,
        "agent_id": req.agent_id,
        "principal_id": req.principal_id,
        "merchant": req.merchant,
        "amount_usd": req.amount_usd,
        "approved": approved,
        "policy_version": req.policy_version,
    }
    signature = sign_transaction(signature_payload)

    return AuthorizeResponse(
        approved=approved,
        reason=reason,
        audit_id=audit_id,
        signature=signature,
    )


@app.get("/audit")
def get_audit_trail(agent_id: str | None = None):
    """Return the full audit trail. Optionally filter by agent_id (CFO query)."""
    if agent_id:
        return [row for row in AUDIT_TRAIL if row["agent_id"] == agent_id]
    return AUDIT_TRAIL


@app.get("/policies")
def get_policies():
    """Return the currently active spend policy.

    Anyone integrating PayWire can introspect what's enforced.
    Transparency by default — the foundation of regulator-grade audit.
    """
    return {
        "version": "v0.5",
        "rules": {
            "per_call_cap_usd": PER_CALL_CAP_USD,
            "allowed_merchants": sorted(list(ALLOWED_MERCHANTS)),
        },
        "description": "Active policy enforced on every /authorize call",
    }


@app.post("/verify")
def verify(token: str):
    """Verify a transaction signature.

    Pass the JWT signature from a previous /authorize response.
    Returns the original payload if valid, or an error if tampered.
    """
    try:
        payload = verify_signature(token)
        return {
            "valid": True,
            "payload": payload,
            "message": "Signature verified. Transaction is authentic and untampered."
        }
    except jwt.InvalidTokenError as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Signature invalid. Transaction may be tampered or forged."
        }


@app.get("/")
def root():
    return {
        "name": "PayWire Authorize v0.5.1",
        "endpoints": ["/authorize (POST)", "/audit (GET)", "/policies (GET)", "/verify (POST)", "/docs"],
    }
