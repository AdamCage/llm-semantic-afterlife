# ADR-0028: S10 second space inherits hosted Qwen-embed (ADR-0027)

Status: accepted
Date: 2026-09-16
Stage: S10
Amends: [ADR-0023](ADR-0023-paper-b-local-four-family.md) §5 for S10
  (local-only primary spaces), same exception pattern as
  [ADR-0027](ADR-0027-s9-hosted-qwen-embed.md)
Does not rewrite: S9 REPORT; the ban on hosted generators; F1–F4

## Context

S9 closed with local BGE-M3 and hosted `qwen3-embed-8b` (RouterAI,
$0 realised, $5 cap). Local Qwen3-Embedding-8B still does not fit
comfortably beside a 16 GB generate/unload cycle. S10 is the OLMo
ladder on the same machine. Changing the second space back to a
local 8B embedder would make S9 and S10 incomparable.

## Decision

1. **S10 second space is hosted `qwen3-embed-8b`**, same `model_id`
   and RouterAI-first rule as ADR-0027. Local BGE-M3 stays first.
2. **Generate stays local and $0.** This exception is embed-only.
3. **Money.** YAML `budget_usd: 5.0` on the hosted embed pass. Stop
   and ask before Gemini or before raising that ceiling.
4. S11 may inherit this default; say so in that PLAN, do not assume.

## Alternatives considered

1. **Local Qwen3-Embedding-8B on the same 16 GB card.** Still does
   not fit comfortably beside the generate/unload cycle. Changing
   the second space would make S9 and S10 incomparable.
2. **BGE-M3 only.** Drops E5 / F4 confirmatory #3 geometry for this
   family. Not acceptable for the mechanistic figure.
3. **Hosted Gemini as the second space.** Different geometry from
   S9; would break the two-space comparison the programme already
   paid for.

## Consequences

- E5 still requires \(G_t\) in both spaces. The Qwen-embed space is
  the Paper A hosted geometry, not a local NF4 twin.
- Do not pool OLMo \(G_t\) with Qwen S9 numbers.

## Reversal cost

Switching S10's second space after the first embed run means
re-embedding every completed generate (~8.8k chunks at fill=1) and
recomputing \(G_t\). Do not do that to save the $5 cap.
