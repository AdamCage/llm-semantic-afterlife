# ADR-0030: Append Paper B after the S13 gate

Status: accepted
Date: 2026-11-07
Stage: S13
Depends on: [ADR-0023](ADR-0023-paper-b-local-four-family.md),
[ADR-0025](ADR-0025-persistence-metrics-and-horizon-ladder.md)

## Context

S9–S11 are a closed family-wise record. S12 closed at 0/8 confirmed
escape through 4,999,168 original tokens and is not a pooled rate.
The research plan allowed `paper/main.tex` for this synthesis only
with a human yes. The human ordered the stage ladder finished.
The mechanical gate `afterlife review --stage s13` exited 0 before
any manuscript sentence was added. Paper A is the closed S0–S7 text
already in that file.

## Decision

1. Append a Paper B section to `paper/main.tex` and the Russian
   mirror. Do not rewrite Paper A paragraphs.
2. Every new quantitative sentence points at an artifact and a
   `run_id`. The assembly run is
   `s13-paperb-synthesis-20261107T085555Z-c0f6b853`.
3. S12 stays a separate censored count. It is not combined with
   12-turnover escape counts and it is not a permanence claim.
4. Gemma Base BGE remains an identified negative. The Qwen-embed
   sign remains not established. Do not claim the two spaces have
   opposite established signs. Do not license the S11
   necessary-condition sentence about attention on every layer.
5. There is no S14. L1 and L2-persistence-to-lock stay closed.

## Alternatives considered

- Replace `paper/main.tex` with a Paper B manuscript. Rejected:
  that would erase the closed Paper A record.
- Wait to write the section until a later stage. Rejected: the
  ladder ends at S13, and the human ordered it finished.
- Pool the four families into one instruct effect. Rejected by
  ADR-0023 and by the S13 exit criteria.

## Consequences

The manuscript now contains two programmes. Numbers in the Paper B
section are copies of published tables, not new estimates.
Limitations in that section name re-prompt versus native sliding
attention, embedding-space dependence, provider non-determinism,
and finite trajectory length.

## Reversal cost

Deleting the appended section restores the Paper A file. The
artifacts and the stage report would still stand.
