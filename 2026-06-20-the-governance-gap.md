# Mastercard shipped Agent Pay. The governance layer above it still doesn't exist.

On June 10, Mastercard shipped "Agent Pay for Machines." 30+ launch partners. A real category announcement from one of the two card networks.

I read the press release three times. Then I noticed what wasn't there.

## What Mastercard actually announced

Agent Pay for Machines is a card-network-level update that lets AI agents transact on Mastercard rails. Mastercard's framing: bringing "structure, governance, and trust" to a new class of payments.

The 30+ launch partners include Crossmint (crypto-native agent payments) and a list of fintech and developer-tools companies you'd expect to see in any ecosystem announcement. The shape of it is real: Mastercard isn't just talking, they shipped infrastructure changes and lined up adopters.

Stripe shipped Agent SDK in November 2025. Visa is presumably next. Each major card network is now committing to make agent transactions a first-class category on their rails.

That's the validation moment everyone in this space was waiting for. AI agent payments stopped being a thesis last week.

## What it solves

To be fair, Agent Pay for Machines does real work:

- **Card-primitive support for agents** — Mastercard rails now recognize agent-initiated transactions as a category, not just "weird non-human card swipes"
- **Risk treatment** — different fraud and chargeback rules for agent transactions vs. human transactions
- **Ecosystem alignment** — 30+ partners means a coordinated rollout, not a one-off pilot
- **Network awareness** — Mastercard's full network now knows what an agent transaction looks like

This is the kind of thing only a card network can do. You can't build a card-network-level standard from outside the card network.

## What it doesn't solve

Here's what I noticed when I read the announcement carefully. Four problems remain wide open at the protocol level above the card.

**1. Identity.** When an AI agent transacts via Mastercard Agent Pay, which agent ran the transaction? The card sees a cardholder. There can be 50 agents using the same card. Without a portable identity standard at the governance layer, you can't tell them apart.

**2. Policy.** Was this transaction authorized under the principal's spend rules? Mastercard supports per-card limits. They don't support "this agent can spend $50 on OpenAI but only $20 on anything else, never after midnight, never without a prompt hash that maps to a documented agent task."

**3. Audit.** Six months from now, when a CFO or regulator asks "prove this AI-initiated transaction was authorized," what's the answer? A card statement doesn't say which agent, with what authority, against what prompt, under which policy.

**4. Attestation.** Can anyone cryptographically prove this transaction came from an authorized agent and hasn't been tampered with after the fact? Card networks don't sign individual transactions at the agent level. They handle authorization between issuer and acquirer, then the transaction enters the regular settlement flow.

None of these four problems are bugs in Mastercard's design. They're outside the scope of what a card network is supposed to do. The card network handles the card primitive. The governance primitives above the card network are a different layer.

## Why a closed standard isn't enough at the governance layer

Mastercard's Agent Pay is a closed proprietary standard tied to Mastercard's network. Visa will ship their own. Stripe Agent SDK already exists for Stripe Issuing customers. Lithic will follow.

That's fine at the card-primitive layer. Each card network can have its own internal way of recognizing agent transactions. It's the wrong shape at the governance layer.

Three reasons:

**1. Enterprises use multiple card rails.** A SaaS company might issue agent cards via Stripe Issuing for some workflows and Mastercard's Agent Pay for others. If the governance layer is owned by the card network, you have to choose. Closed standards force lock-in.

**2. Regulators need a neutral standard.** Compliance frameworks for AI agent transactions are coming. They won't reference "Mastercard Agent Pay" or "Stripe Agent SDK" — they'll reference whichever governance protocol is widely adopted and neutral.

**3. Developers default to open at the protocol layer.** TCP/IP beat proprietary networks. OAuth beat custom auth schemes. JWT beat closed signed-cookie systems. At the protocol layer, open wins.

## What an open governance layer looks like

If you take the four problems above and ask "what should the open neutral standard for AI agent payment governance contain," you get something like:

- **Identity:** Every agent has a verifiable, cryptographic identity tied to a principal. Portable across card rails.
- **Audit:** Every agent transaction carries the lineage — agent_id, principal_id, prompt_hash, model_version, policy_version. Stored append-only. Provable later.
- **Attestation:** Every transaction is signed. Anyone can verify authenticity and detect tampering.
- **Policy:** Spend rules are programmable, versioned, and enforced before any card-rail authorization. Per-agent, per-merchant, per-time-window.

I've been building this as an open protocol called PayWire ([github.com/Paywire-dev](https://github.com/Paywire-dev)). v0.5.1 shipped this week with the first cryptographic attestation primitive working end-to-end. Architecture doc is in the repo. MIT licensed.

It's not done. It's alpha. The point isn't that PayWire is the answer — the point is that someone has to build the open layer, and right now nobody else is building it card-rail-first and protocol-open.

## The Visa parallel

In the 1970s, banks settled with each other through direct correspondent relationships. No shared format, no shared dispute mechanism, no shared rules. Visa was founded specifically to fix that — give every bank a common protocol for moving money.

Visa's value wasn't the rail. The rail existed. Visa's value was the *governance layer above the rail* — shared format, dispute mechanism, risk-sharing rules.

The same shape of problem is happening now for AI agents. The rails are being built (Mastercard, Visa, Stripe Issuing, Lithic). The governance layer above them isn't.

That's the next infrastructure layer. If it gets owned by a closed proprietary vendor, the AI agent economy gets built on tribal infrastructure choices. If it stays open, it becomes a neutral substrate everyone can build on.

## What's next

I'm 17, solo, in Dubai. PayWire is alpha. The mock issuer is a toy. There's no production deployment yet. v0.6 ships next week with multi-policy support and JWT key rotation.

This isn't a "PayWire wins" essay. It's a "the open governance layer for AI agent payments is going to exist, and right now there's a window where it can still be open neutral infrastructure" essay.

Mastercard validated the market last week. Visa and Stripe will follow with their own closed variants. Someone is going to build the open governance layer above them.

I'm building it. If you want to help, contribute, criticize, or fund it — [github.com/Paywire-dev](https://github.com/Paywire-dev). DM me on X at [@alexistheron](https://x.com/alexistheron).

---

*Alexis Ortiz-Bau. June 2026.*