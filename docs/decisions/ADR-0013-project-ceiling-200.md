# ADR-0013: Project spend ceiling raised from $50 to $200

Status: accepted
Date: 2026-09-03
Stage: S3 follow-up / S4 entry
Amends: [ADR-0004](ADR-0004-pilot-window-and-cost-law.md)

## Context

The approved pilot ceiling was $50 (ADR-0004). Ledger spend at this
decision is **$11.57**. The human authorised a new project ceiling of
**$200** on 2026-09-03, after OpenRouter credits returned (key monthly
limit remaining ~$47; account credits ~$202).

The written Stage 4 sketch in `docs/research-plan.md` still names a
≤ $120 `temperature × W` sweep on 2–3 models. That sketch is not
authorised by this ADR: H1 left `n_macro` unusable as an order
parameter, T=1.0 at `W = 256` on the 1B base model was a token lock
not diffusion, and input cost grows as `T · W / S`. A reduced S4
matrix still needs its own PLAN, estimate, and a separate generate
approval.

The immediate computation this ADR unblocks is not generation. It is
the deferred `$0` CPU geometry / seed-separation pass on
`s3-embed-local-base-embed-20260902T051805Z-2ce86473` (ADR-0012
follow-up). Raising the ceiling does not change that pass's cost.

## Decision

1. **`AFTERLIFE_BUDGET_USD_TOTAL = 200`.** The harness refuses any
   charge that would take ledger spend past this number. Per-run
   ceiling is unchanged (`AFTERLIFE_BUDGET_USD_PER_RUN` stays as set
   in the environment).
2. **This is not approval to generate the written S4 matrix.** S4
   still opens with PLAN + ADR for a reduced order-parameter set +
   `afterlife estimate` + an explicit generate yes.
3. **S3.0 geometry / separation run under the new ceiling** and are
   recorded as a dated follow-up, not a rewrite of the Stage 3
   opening (ADR-0012).

## Alternatives considered

- **Keep $50 and only run the $0 S3.0 analysis.** Possible, and the
  analysis does not need the raise. Rejected because the human
  authorised $200 so a later reduced S4 can be estimated against a
  real remaining budget rather than against a ceiling we already know
  will be lifted.
- **Treat $200 as approval of the $120 S4 sketch.** Rejected: the
  sketch's order parameters and window list are the ones Stage 3
  invalidated. Money does not repair that.

## Consequences

- `.env` / `.env.example` carry `AFTERLIFE_BUDGET_USD_TOTAL=200`.
- `docs/research-plan.md` and the Russian mirror state the new
  ceiling. Historical stage reports keep the `$11.57 of $50` figure
  they were written under.
- Remaining project budget at this decision: **$188.43** of $200.
  OpenRouter's monthly *key* limit (~$47 remaining) can still refuse
  a call before the project ceiling does. That is a provider cap, not
  this ADR.

## Reversal cost

Low. Lowering the env var again is enough; already-written ledger
rows do not change.
