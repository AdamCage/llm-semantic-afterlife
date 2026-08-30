# Stage 0 — Foundations and feasibility audit

**Status.** In progress. Opened 2026-08-30.

## 1. Question

Can this experiment be run reproducibly on this infrastructure, at a cost that
permits the full plan, and what are the *measured* facts about our providers as
opposed to the documented ones?

Stage 0 makes **no scientific claims**. Its deliverables are working
infrastructure and an honest capability audit. Every downstream stage's design
depends on facts that only measurement can supply: which models will actually
free-run, how deterministic the API really is, and what a token really costs.

## 2. Entry state

Nothing. This is the first stage. Known constraints:

- Hardware: 4-core Intel i7-1165G7, 16 GB RAM, **no GPU** ⇒ all generation and
  embedding via API; local compute for analysis only; protocol P2 infeasible at
  scale (ADR-0001).
- Provider: RouterAI key available; OpenRouter key not yet (ADR-0003).
- Approved pilot budget $50; Stage 0 ceiling $3.
- Protocol and cost law fixed by ADR-0001 and ADR-0004.

## 3. Computations

| ID | Pass | Command | Artifacts |
| --- | --- | --- | --- |
| S0.1 | Environment and key check | `afterlife doctor` | `artifacts/stage-0/doctor/` |
| S0.2 | Provider capability audit | `afterlife audit providers` | endpoint table, price table, availability figure |
| S0.3 | Continuation-mechanism audit | `afterlife audit continuation` | per-model mechanism matrix, sample outputs, stop-event rates |
| S0.4 | Determinism audit | `afterlife audit determinism` | exact/near-match rate table + figure |
| S0.5 | Embedding audit | `afterlife audit embeddings` | dimension/normalisation/cost table, latency figure |
| S0.6 | Tokenizer audit | `afterlife audit tokenizers` | round-trip pass rate, local-vs-API token count deltas |
| S0.7 | End-to-end micro-trajectory | `afterlife generate --config configs/stages/stage0_smoke.yaml` then `embed`, `analyze geometry` | trajectory figures, geometry tables |
| S0.8 | Replay reproduction | `afterlife reproduce <run_id> --level replay` | `REPRODUCTION.md` with hash comparison |
| S0.9 | Cost model calibration and S1 forecast | `afterlife estimate --config configs/stages/stage1_pilot.yaml` | predicted-vs-actual table, S1 forecast |

S0.7 configuration (deliberately tiny — it validates the pipeline, not a
hypothesis): `W = 2048`, `B = S = 512`, `T ≈ 16384` (8 turnovers),
`chunk_size = 512`, 1 model, 2 semantic seeds × 1 stochastic seed.

## 4. Exit criteria

| # | Criterion | Threshold |
| --- | --- | --- |
| E1 | Generators pass the continuation audit | ≥ 3 candidate models produce ≥ 512 tokens of coherent continuation with a documented mechanism |
| E2 | Representation spaces usable | ≥ 2 embedding models return vectors of the documented dimension within cost expectations |
| E3 | End-to-end pipeline completes | S0.7 finishes with `STATUS=COMPLETED`, full manifest, non-empty artifacts |
| E4 | Bit-exact replay | S0.8 reproduces every output hash with zero network calls |
| E5 | Determinism measured | exact-match rate reported per model with `n ≥ 5` repeats; number stated, whatever it is |
| E6 | Cost model calibrated | predicted vs. actual token counts within ±5%; USD within ±10% |
| E7 | S1 affordable | forecast for the Stage 1 matrix ≤ $25 |
| E8 | CLI surface green | `doctor`, `audit`, `plan`, `estimate`, `generate`, `embed`, `analyze`, `report`, `reproduce`, `ledger`, `verify` all run |
| E9 | Tests and typing clean | `pytest` green, `ruff` clean, `mypy` clean |
| E10 | Tokenizer integrity | round-trip pass rate = 100% on audited models, or the failing model is excluded with a recorded reason |

## 5. Pre-registered predictions

Written before execution, to be scored in the report.

| # | Prediction | Confidence | Observed |
| --- | --- | --- | --- |
| P1 | `/completions` (raw text continuation) is available for at least one base model on RouterAI | 0.5 | |
| P2 | At least one chat model supports assistant prefill, giving a near-unforced continuation mechanism | 0.6 | |
| P3 | Instruct models show a stop-event rate > 0.3 per step under unforced continuation | 0.7 | |
| P4 | Exact-match determinism with a fixed `seed` is **below** 50% on at least one model | 0.6 | |
| P5 | Embedding vectors are returned already L2-normalised by at least one of the two primary models | 0.5 | |
| P6 | Tokenizer round-trip (`decode(encode(x)) == x`) holds for all audited byte-level BPE tokenizers | 0.85 | |
| P7 | Local prompt-token count matches the API's within ±2 tokens for raw completions, and differs by a fixed template offset for chat | 0.7 | |
| P8 | Actual Stage 0 spend is under $1 | 0.8 | |
| P9 | Strict pinning (`provider.only` + `allow_fallbacks=false`) is honoured — served provider equals pinned provider in 100% of successful requests | 0.7 | |

`P4` and `P9` matter most: together they determine what reproducibility level
the paper can honestly claim.

## 6. Budget and wall-clock

- API spend ceiling: **$3**. Stop and ask if exceeded.
- Wall-clock: audits are minutes; S0.7 is ~32 sequential steps per trajectory,
  well under an hour.
- Per-run ceiling in `.env` set to $5 as a second safety net.

## 7. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| A candidate model is absent from RouterAI | the audit reports availability rather than assuming it; the model list is revised in the report, and the plan follows the audit |
| Base models unavailable through the aggregator | fall back to `assistant_prefill`; if neither exists, the "pure autoregressive" arm is dropped and this becomes a first-class limitation, decided in S0 rather than discovered in S3 |
| `/completions` unsupported | detected in S0.3; affects framing, not feasibility |
| Gated tokenizer (e.g. Llama) inaccessible | use an ungated mirror of the same tokenizer, verify vocabulary hash equality, and record the mirror in the manifest |
| Audit itself overspends | every audit call is capped in tokens and passes through the ledger |

## 8. Definition of done

- [ ] All nine passes executed with `run_id`s
- [ ] `artifacts/stage-0/INDEX.md` populated with figures, tables, captions
- [ ] `docs/stages/stage-0/REPORT.md` with a verdict per exit criterion and the
      prediction table scored
- [ ] Model and embedding lists in `docs/research-plan.md` revised to match the
      audit, with an ADR if a candidate is dropped
- [ ] `configs/stages/stage1_pilot.yaml` written with an approved forecast
- [ ] Spend reconciled in `runs/_ledger/spend.jsonl`
