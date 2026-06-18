# PayWire Architecture

> Open payment infrastructure for AI agents. The governance layer above existing card rails: identity, policy, audit, and cryptographic attestation, in one open protocol.

**Version:** v0.5.1
**Status:** Alpha (mock issuer)
**License:** MIT
**Maintainer:** Alexis Ortiz-Bau ([@alexistheron](https://x.com/alexistheron))

---

## 1. The problem in 30 seconds

AI agents are starting to spend real money. They book flights, pay SaaS bills, run compute, execute trades. Stripe shipped Agent SDK in November. Mastercard shipped Agent Pay for Machines last week. Visa is next.

The card primitive for agent transactions is solved. Four problems aren't:

| # | Problem | Question it asks |
|---|---------|------------------|
| G1 | Identity | Which agent ran this transaction? |
| G2 | Audit | Can a regulator reconstruct the chain later? |
| G3 | Attestation | Can anyone cryptographically prove this came from an authorized agent? |
| G4 | Policy | Was this transaction authorized under the principal's rules? |

Stripe Issuing and Lithic give agents cards. They don't give them governance. Every team integrating agents into a real workflow rebuilds those four primitives from scratch. PayWire builds them once, open.

---

## 2. Where PayWire sits in the stack

```
┌──────────────────────────────────────────────┐
│  AI Agent (Claude, GPT, custom)              │
└─────────────────┬────────────────────────────┘
                  │ signed authorize() call
                  ▼
┌──────────────────────────────────────────────┐
│  PayWire (this protocol)                     │
│  ├─ G1: Identity layer                       │
│  ├─ G2: Audit trail (append-only)            │
│  ├─ G3: Attestation (JWT signatures)         │
│  └─ G4: Policy engine                        │
└─────────────────┬────────────────────────────┘
                  │ clean authorization request
                  ▼
┌──────────────────────────────────────────────┐
│  Card rail (Stripe Issuing / Lithic / etc.)  │
└─────────────────┬────────────────────────────┘
                  ▼
┌──────────────────────────────────────────────┐
│  Card network (Visa / Mastercard)            │
└──────────────────────────────────────────────┘
```

PayWire is middleware. No funds held. No card networks replaced. The card network sees a clean authorization. PayWire carries the full lineage (agent, principal, prompt, model, policy version) on the side. Provable later. Auditable by a regulator.

---

## 3. The four governance primitives

### G1 — Identity

Every agent has a verifiable identity tied to a principal (the human or business it acts for). v0.5 represents identity as:

- `agent_id` — unique identifier (e.g., `claude-bot-1`)
- `principal_id` — the human or org the agent represents (e.g., `alexis@paywire.dev`)
- `model_version` — which model made the call (e.g., `claude-3-5-sonnet`)

In production, identity moves to JWT or DID with key rotation and revocation. v0.6 ships the first version.

### G2 — Audit

Every transaction lands in an append-only audit trail. v0.5.1 stores in memory (fine for a protocol proof). Production will use Postgres + S3.

Each row:

- `audit_id` — globally unique transaction ID
- `timestamp` — ISO 8601 UTC
- `agent_id`, `principal_id`
- `merchant`, `amount_usd`
- `prompt_hash` — SHA-256 of the prompt that triggered the transaction
- `model_version`, `policy_version`
- `approved`, `reason`

Given a transaction ID, anyone can reconstruct the chain: who did what, on whose authority, against what prompt, under which policy.

### G3 — Attestation

Every approved transaction is signed with a JWT (HS256 in v0.5.1; RSA/ECDSA with key rotation from v0.6). The signature payload:

```json
{
  "audit_id": "txn_e9ab9c62a733",
  "agent_id": "claude-bot-1",
  "principal_id": "alexis@paywire.dev",
  "merchant": "openai.com",
  "amount_usd": 20.0,
  "approved": true,
  "policy_version": "v0.4"
}
```

`POST /verify` lets anyone with the key check that a transaction is authentic and untampered. No "the LLM did it" excuse.

### G4 — Policy

Spend rules are programmable, versioned, and enforced before any card-rail authorization. v0.5.1 supports:

- Per-call spend caps (e.g., `$25 max`)
- Merchant whitelist (e.g., `openai.com, anthropic.com, modal.com, fal.ai`)

v0.6 adds:

- Per-agent policies (not one global)
- Time-window rules
- MCC restrictions
- Principal-approval requirements (human in the loop above $X)

Policies are versioned. Every transaction is signed with the active `policy_version`, so the exact rules at decision time are provable later.

### G5 — Open

The protocol spec is MIT-licensed. The reference implementation is open-source. Anyone can implement, fork, contribute.

The governance layer will be adopted by customers of Stripe, Lithic, Marqeta, and Mastercard. Different card rails, same governance need. An open neutral protocol gets adopted by all. A closed proprietary protocol from any one network forces a tribal choice.

---

## 4. Protocol surface (v0.5.1)

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `/authorize` | POST | Real-time agent authorization with policy enforcement + JWT signature |
| `/audit` | GET | Queryable transaction trail, filter by `agent_id` |
| `/policies` | GET | The currently enforced spend policy |
| `/verify` | POST | Verify a JWT signature; returns the original payload or an error if tampered |
| `/docs` | GET | Auto-generated Swagger UI |

FastAPI in the reference implementation. Response time target: under 50ms on the hot path.

---

## 5. Why open, not closed

Mastercard shipped Agent Pay for Machines last week. Visa and Stripe will follow. Each one ships a closed standard tied to their network.

That's fine at the card-primitive layer. Wrong at the governance layer.

Three reasons:

1. Enterprises use multiple card rails. A SaaS company might use Stripe for some agents, Mastercard for others. Closed standards lock you into one network.

2. Regulators need a neutral standard. Compliance frameworks won't reference Mastercard's Agent Pay. They'll reference whichever protocol gets adopted across the industry.

3. Developers pick open. It's how TCP/IP, OAuth, and JWT all won.

---

## 6. What's NOT in v0.5.1 (honest)

This is alpha. The architecture is real. Production readiness is not.

- No real card-rail integration yet. The issuer is mocked. v0.8 ships Lithic sandbox.
- No key rotation. Static HS256 secret. v0.6 ships RSA/ECDSA with rotation.
- No multi-tenant isolation. Single in-memory audit trail.
- No production deployment. Local only. v0.9 ships to `api.paywire.dev`.
- No language SDKs. v0.6 ships `pip install paywire-sdk`. v0.7 ships TypeScript.
- No multi-policy support. One global policy for now.
- No real auth. Anyone can hit the local endpoint. v0.9 ships API keys.

---

## 7. Roadmap

| Version | Target | Theme | Headline shipping |
|---------|--------|-------|-------------------|
| v0.6 | Late June 2026 | Harden primitives | Key rotation, multi-policy, pip SDK, pytest suite |
| v0.7 | Early July 2026 | Developer ergonomics | TypeScript SDK, WebSocket, batch authorize |
| v0.8 | Mid July 2026 | First real rail | Lithic sandbox, agent provisioning |
| v0.9 | Late July 2026 | Production infra | Postgres, API key auth, deployed |
| v1.0 | End August 2026 | Production | First design partner in pilot, technical paper |
| v1.1+ | Sep-Oct 2026 | Scale | Multi-language SDKs, enterprise features, first paying customer |

---

## 8. Why this matters

In the 70s, banks settled directly with each other. No shared format, no shared rules, no shared dispute process. Visa was founded to fix that — give every bank a common protocol.

Same thing is happening now for AI agents. Every team is solving the same four problems separately. PayWire does it once.

If this layer ends up owned by Mastercard or Stripe, the AI agent economy is built on closed infrastructure. If it stays open, it's a neutral layer anyone can build on.

That's why I'm building it open.

---

## 9. Contributing

PayWire is alpha. The protocol is being designed in the open. If you're:

- Building AI agents that need to spend money
- Working at a card-issuing platform (Stripe, Lithic, Highnote, Marqeta)
- Thinking about agent-payment regulation
- Curious about the architecture

Open an issue, start a discussion, or DM [@alexistheron](https://x.com/alexistheron).

If you'd want this layer to exist, star the repo.

---

*Last updated: June 18, 2026. v0.5.1.*
