# ADR-0026: Seed bank v1 rationale is not identification

Status: accepted
Date: 2026-09-09
Stage: S8 (documentation)
Does not amend: seed *texts*, seed ids, twin pairing, or bank version

## Context

[`configs/seeds/seed_bank_v1.yaml`](../../configs/seeds/seed_bank_v1.yaml)
constraint #2 said domains are “maximally far apart, so that a probe
distinguishing them past the horizon is measuring semantic content
rather than register.”

That sentence overclaims. The bank has **one continuation-shaped text
per domain**. Topic, register, style, lexical field, and any other
covariate that travels with that single text are entangled. A late
window that remains closer within a seed than between seeds is
**seed-conditioned ensemble persistence in representation space**. It
is not an identification of semantics versus register.

Paper A occupancy already had to say distinguishable ≠ recovered
semantic memory. Paper B confirmatory estimands
([ADR-0025](ADR-0025-persistence-metrics-and-horizon-ladder.md)) use
the same bank. Leaving the false identification claim in the YAML
would leak into PLAN/REPORT prose.

The bank is append-only. Editing texts would silently change the
object of every past `run_id`.

## Decision

1. **Rewrite constraint #2 in the comment block only.** The new text
   states the design intent (spread of initial conditions) and the
   non-identification (semantics vs register is not identified).
2. **Do not edit** any `text:`, `id:`, `domain:`, `twin_of:`, or the
   `version: v1` field.
3. Paper B copy (PLAN, REPORT, notes, README after S13) says
   seed-conditioned persistence, not semantic-domain memory, and
   names “one text per domain” as a limitation in every stage that
   uses the bank.
4. A bank that *would* identify semantics vs register (topic-fixed /
   style-varies, or several texts per domain) is a new
   `seed_bank_v2` plus ADR, not a silent edit of v1.

## Alternatives considered

- **Leave the comment; correct only in the manuscript.** Rejected:
   the YAML is what later agents quote.
- **Edit seed texts to “purify” semantics.** Rejected: append-only;
   would invalidate comparability with S5/S6.
- **Drop `love` / `recipe` as “register-heavy”.** Rejected: F2 already
   froze INT8 seeds; post-hoc dropping is the identification mistake
   in another costume.

## Consequences

- Constraint #2 in `seed_bank_v1.yaml` is corrected in the same
  change set as this ADR.
- Past stages that repeated the old sentence in comments are not
  silently rewritten; Paper B does not inherit the claim.

## Reversal cost

Trivial for the comment. Restoring the identification sentence would
reintroduce a false claim. Changing texts remains forbidden without
`seed_bank_v2`.
