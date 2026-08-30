# ADR-0001: Re-prompt (`Tail_W`) as the primary sliding-window protocol

Status: accepted
Date: 2026-08-30
Stage: S0

## Context

The object of study is `X_{t+1} = Tail_W(X_t ⊕ Y_t)`. Two mechanisms can
realise a finite window:

1. **P1 — re-prompt.** Each step sends the last `W` tokens as a *new* prompt.
   Position IDs restart at 0; no KV cache is carried across steps.
2. **P2 — true sliding attention.** One forward-running generation with KV-cache
   eviction beyond `W`, positions continuing to advance (or re-indexed by a RoPE
   scheme).

These are not equivalent. Position handling, RoPE phase, and cache contents
differ, and any of them could produce dynamics of its own. Conflating them
silently would be a serious methodological error — a reviewer who notices would
be entitled to discard the results.

Available hardware is a 4-core CPU laptop with 16 GB RAM and no GPU. P2 requires
local weights and a custom generation loop; at the model sizes of interest it is
not feasible here beyond a toy scale.

## Decision

**P1 is the primary protocol for all reported results.** It is named explicitly
in the paper's method section (not the appendix), the stride `S = B` is treated
as a first-class protocol parameter with a planned sensitivity ablation, and the
difference from P2 is listed first in the limitations.

P2 is retained as a small-`W`, small-`T` local control in Stage 6, on whatever
scale CPU-only inference permits, and its data are never pooled with P1.

## Alternatives considered

- **P2 as primary.** Scientifically preferable, infrastructurally impossible on
  this hardware for 8B–30B models at ~10^5–10^6 tokens per trajectory. Rented
  GPU time is in the backlog if the caveat becomes the dominant objection.
- **Both as equal arms.** Doubles cost and complexity for a comparison that a
  small control can address.
- **Not addressing the distinction.** Rejected: it is exactly the kind of
  unstated protocol choice that invalidates a paper.

## Consequences

- The measured process is `P_θ` under repeated re-encoding of its own tail. This
  is a well-defined stochastic dynamical system and matches the deployment
  reality of API-served models, which is a genuine (if secondary) argument in
  its favour.
- Cost follows `input ≈ T·W/S`, driving the whole budget structure (ADR-0004).
- Periodicity at the scale of `B` must be actively ruled out as a harness
  artifact: stride sensitivity, and chunk boundaries offset from step boundaries.
- Any claim of the form "LLMs with sliding attention behave thus" is out of
  bounds; claims are about free-running generation under repeated `Tail_W`
  re-prompting.

## Reversal cost

Low for the framing (a paragraph and a caveat), high for the data: switching to
P2 as primary invalidates every generated trajectory and requires GPU
infrastructure plus full regeneration.
