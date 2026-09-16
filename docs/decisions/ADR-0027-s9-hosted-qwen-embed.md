# ADR-0027: S9 Qwen3-Embedding-8B is hosted (RouterAI / OpenRouter)

Status: accepted
Date: 2026-09-15
Stage: S9
Amends: [ADR-0023](ADR-0023-paper-b-local-four-family.md) §5 (local-only
primary spaces), [docs/stages/stage-9/PLAN.md](../stages/stage-9/PLAN.md)
E10 and the `$0` embed line
Does not rewrite: S8 REPORT; local BGE-M3 as the other S9 space;
the ban on hosted `or-qwen3-8b` as an Instruct *generator*

## Context

S9 generate is closed on the local Qwen pair (86/100 full 12W). Local
BGE-M3 embed completed. Local Qwen3-Embedding-8B on a 16 GB card is
an 8B load (NF4 or not) that the human chose not to run. The human
authorised the Paper A hosted embedder instead:
`qwen/qwen3-embedding-8b` via RouterAI, OpenRouter as fallback.

## Decision

1. **S9 second space is the hosted slug `qwen3-embed-8b`**, same
   `model_id` as Paper A (`qwen/qwen3-embedding-8b`). Primary client
   is **RouterAI** (the only stack this repo has actually billed and
   dimension-checked for embeddings). **OpenRouter** is the fallback
   if RouterAI is unset or refuses; it inherits the same `/embeddings`
   client. Do not mix providers inside one embed run: the embedding
   cache is keyed by `model_id` alone.
2. **Local BGE-M3 is unchanged.** Gemini stays optional, not an exit
   criterion.
3. **Generate stays local and $0.** This exception is embed-only. It
   does not make `or-qwen3-8b` an Instruct cell (ADR-0023 §6 / S9 E7).
4. **Money.** Historical RouterAI embed `usage.cost` was $0 (S0 audit,
   S5 occupancy-repl). Forecast for ~4.1k chunks is **$0.00** on that
   schedule. YAML `budget_usd` for the hosted pass is a **$5** ceiling
   so a silent price change cannot run away. Ledger records whatever
   the provider returns. Do not raise the ceiling without asking.

## Consequences

- E5 still requires \(G_t\) in both spaces; the Qwen-embed space is
  now the Paper A hosted geometry, not a local NF4 twin. Say so in
  S9 REPORT limitations.
- E10 is narrowed: generate/local-BGE remain $0; hosted Qwen-embed
  may increment the ledger, capped at $5.
