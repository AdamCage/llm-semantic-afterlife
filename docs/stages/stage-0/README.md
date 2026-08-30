# Stage 0 — dashboard

**Question.** Can this experiment be run reproducibly on this infrastructure, at
a cost that permits the full plan, and what are the *measured* facts about our
providers?

Full plan: [`PLAN.md`](PLAN.md) · Report (after execution): `REPORT.md`
Ceiling: **$3** API spend. Hardware: 4-core CPU, 16 GB RAM, no GPU.

## Progress

| ID | Pass | Command | Status | run_id |
| --- | --- | --- | --- | --- |
| S0.0 | Repository, harness, library, CLI | — | done | — |
| S0.1 | Environment check | `afterlife doctor` | done | — |
| S0.7a | Offline end-to-end micro-trajectory | `afterlife generate/embed/analyze --config configs/stages/stage0_smoke.yaml` | done | `s0-smoke-*`, `s0-embed-smoke-*`, `s0-geometry-mock-hash-*` |
| S0.2 | Provider capability audit | `afterlife audit providers` | pending — needs `ROUTERAI_API_KEY` | |
| S0.6 | Tokenizer round-trip audit | `afterlife audit tokenizers` | pending — needs `HF_TOKEN` for gated repos | |
| S0.3 | Continuation-mechanism audit | `afterlife audit continuation` | pending | |
| S0.4 | Determinism audit | `afterlife audit determinism` | pending | |
| S0.5 | Embedding audit | `afterlife audit embeddings` | pending | |
| S0.7b | Live micro-trajectory | `afterlife generate --config configs/stages/stage0_live_smoke.yaml` | pending — after S0.2 fills in prices | |
| S0.8 | Replay reproduction | `afterlife reproduce <run_id> --level replay` | pending | |
| S0.9 | Cost calibration + S1 forecast | `afterlife estimate --config configs/stages/stage1_pilot.yaml` | pending | |

## What the offline pass already established

Not scientific findings — infrastructure facts, plus two things worth recording:

- The full pipeline runs end to end and emits the complete artifact bundle
  (figure + `.data.parquet` + `.meta.json` + caption) for every figure.
- The offline fixture (a five-topic hidden Markov chain with a non-reversible
  transition matrix) produces visible metastable switching in the semantic
  velocity trace, and the geometry pass detects it. The analysis therefore has a
  known-ground-truth regression target, which is what Stage 3's Markov-state
  estimators will be validated against.
- 88 unit and property tests pass, including exhaustive sliding-window invariants
  (window never exceeds `W`, prompt is exactly the detokenised tail, chunks are
  contiguous and non-overlapping, resume replays without duplicating work) and
  estimator recovery on synthetic spherical processes with known MSD exponents.

## Two bugs the tests caught, worth remembering

1. `difflib.SequenceMatcher` enables `autojunk` by default, which reports two
   nearly identical long strings as ~0.19 similar. This silently affected the
   determinism audit's near-match rate. Fixed by `autojunk=False`, and the
   reason is recorded in the code.
2. Editing UTF-8 sources with a tool that assumes a legacy code page corrupted
   mathematical notation in two files, which showed up as mojibake in a rendered
   figure axis. `scripts/check_encoding.py` now guards against BOMs and
   mojibake in pre-commit and CI.

## Blocked on

- `ROUTERAI_API_KEY` in `.env` — required for S0.2–S0.5, S0.7b.
- `HF_TOKEN` in `.env` — required to download tokenizers for gated repos
  (Llama). Ungated mirrors are configured where available; S0.6 verifies
  vocabulary equivalence.

Everything else can proceed offline.
