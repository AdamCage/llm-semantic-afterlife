# ADR-0017: Stage 6 opens as third-space robustness of S5 occupancy

Status: accepted
Date: 2026-09-06
Stage: S6
Amends: [ADR-0016](ADR-0016-s5-lock-occupancy-on-seed-bank-v1.md)

## Context

Stage 5 closed APPROVED WITH CHANGES (`9cb2845`). On `or-qwen3-8b`
under P1 at `W=4096` T=0.3, ten domain seeds are
ensemble-distinguishable at the last band in `bge-m3` and
`qwen3-embed-8b`. Twin last-band Δ CIs include 0 (operational
collapsed); waterloo’s point Δ did not vanish. The claim is about
one process and two embedding spaces.

The master-plan S6 sketch was a kitchen sink: third space, chunk
`{512,1024,2048}`, PCA dimension, stride `S`, forced vs unforced,
cross-provider replication, local CPU, P1 vs true sliding attention,
budget ≤ $40. S5 implications forbid treating occupancy as recovered
semantic memory, opening T=1.0 / 200 seeds / T=1.5 / a second
generator, and putting `n_macro` on the headline. Mixing those parked
arms into one opening would confound the one question S5 left: **does
the occupancy *sign* survive a third representation of the same
text?**

`gemini-embed-001` is already in `configs/embeddings/embeddings.yaml`,
marked “Stage 6 sanity check only,” and was usable in S0 (dim 3072,
L2-normalised). It is a closed architecture, so it cannot carry an
“independent architecture” argument alone. Agreement of all three
spaces answers the embedding-artifact objection; disagreement scopes
the S5 claim.

## Decision

1. **Object.** Robustness of the S5 occupancy *signs* (F4 last-band
   domain gap excludes 0; F6 twins not last-band divergent) on the
   **same** 28 trajectories. Not a new occupancy map. Not H1.
2. **No generate in this opening.** Reuse
   `s5-lock-occupancy-20260905T164327Z-6780902f` (24) and the S2.2
   raw T=0.3 physics/surreal four from
   `s2-mechanism-20260901T071519Z-dfbb173a`. Do not mint a second
   generate `run_id`.
3. **Third space only:** `gemini-embed-001` via RouterAI. Do not
   re-embed `bge-m3` / `qwen3-embed-8b`. S0 dim 3072 is recorded as
   `expected_dim`.
4. **F4/F6 discipline unchanged.** Ten domain seeds vs two twin
   pairs; do not pool twins into domain `D_between`. Last-band
   collapsed ≠ occupancy of one lock. Degeneracy threshold 0.083 /
   Jaccard 0.0122 not moved; degenerate rows kept.
5. **Parked until a separate estimate and generate-yes:** provider
   replication, chunk-size ablation, stride `S`, forced vs unforced,
   local CPU, P1 vs sliding attention, T=1.0 occupancy, T=1.5
   residual, 200 seeds, a second generator, MSM / `n_macro`.
6. **The $40 sketch is not this opening’s spend.** YAML refuse is
   the embed ceiling. `afterlife estimate` on a config that lists
   generators still prints a *generate* forecast; that print is not
   a generate-yes.

## Alternatives considered

- **Run the kitchen-sink S6 sketch.** Rejected: several arms require
  new generation or a different scientific object; S5 just paid
  $1.34 to measure occupancy once.
- **Provider replication first.** Rejected for this opening: it is a
  new generate (~S5.1 cost again) and a different confound (Alibaba
  vs another pin). Third-space on the existing text is the cheaper
  test of “the gap is an embedding artifact.”
- **Open a fourth bidirectional encoder instead of gemini.**
  Rejected: gemini is the space the embedding library already named
  for S6; S0 already measured it. A second bidirectional encoder
  would not add an architecture kind beyond `bge-m3`.
- **F4 in gemini on the eight S5.1 domains only.** Rejected: that
  drops physics/surreal and is not the S5 F4 sample.

## Consequences

- `docs/research-plan.md` S6 entry matches this object.
- Stage config `configs/stages/stage6_third_space.yaml` is embed-only
  in intent; `afterlife generate` on it is forbidden.
- Occupancy assemble must grow a third space after the gemini
  parquets exist; until then it stays the S5 two-space script.

## Reversal cost

Low. Embedding gemini does not regenerate trajectories. A later
provider-replication stage reuses the same generate `run_id`s as
the source text.
