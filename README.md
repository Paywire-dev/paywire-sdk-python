<div align="center">

# PayWire

**Open payment infrastructure for AI agents.**

The governance layer above Stripe Issuing, Lithic, and Marqeta — built for the moment AI agents start moving real money.

![License](https://img.shields.io/badge/license-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Status](https://img.shields.io/badge/status-v0.4--alpha-orange.svg)

[Design Doc](https://github.com/Paywire-dev/paywire-protocol) · [Live API](#whats-shipped--v04) · [Roadmap](#roadmap)

</div>

---

## The problem

AI agents are starting to spend real money on behalf of people and businesses — booking flights, paying SaaS bills, running compute, executing trades.

But the payment system was built for humans with credit cards, not for AI. When an agent spends today, no one cleanly knows:

- **Which agent** ran the transaction
- **On whose authority** (the principal)
- **Under what spend policy**
- **Against which prompt and model**

Stripe Issuing and Lithic give agents *cards*. PayWire adds the *governance* — identity, policy, audit, attestation — as an open protocol above them.

## What's shipped — v0.4

A working mock issuer authorization endpoint built on FastAPI:

- ✅ `POST /authorize` — Real-time agent transaction authorization with policy enforcement
- ✅ `GET /audit` — Queryable audit trail, filterable by agent_id
- ✅ Every transaction signed with `agent_id`, `principal_id`, `prompt_hash`, `model_version`, `policy_version`
- ✅ Auto-generated Swagger UI at `/docs`
- ✅ Pure middleware — no funds held, regulator-friendly

![Swagger UI](screenshots/swagger.png)
![Approved authorization](screenshots/approved.png)
![Audit trail](screenshots/audit.png)

## Quick start

```bash
