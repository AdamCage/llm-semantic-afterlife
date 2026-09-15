# Stage 8 — Can Paper B’s local harness load ten checkpoints?

**Status.** Opened 2026-09-09 on branch `stage-8`, after Stage 7 closed
APPROVED WITH CHANGES and ADR-0019…0022 finished the Paper A
correctness / occupancy-replication pass. Decisions:
[ADR-0023](../../decisions/ADR-0023-paper-b-local-four-family.md),
[ADR-0024](../../decisions/ADR-0024-local-nf4-lifecycle.md),
[ADR-0025](../../decisions/ADR-0025-persistence-metrics-and-horizon-ladder.md),
[ADR-0026](../../decisions/ADR-0026-seed-bank-v1-rationale-not-identification.md).

This stage makes **no scientific claim** about \(G_t\), lock, or
post-training. It is the Paper B analogue of S0: infrastructure and a
32-token smoke. The 12W matrix is S9–S11. This kickoff writes the
plan and configs; it does **not** generate, download weights, or
implement bitsandbytes.

If PLAN prose and YAML disagree, **YAML wins**.

## 1. Question

Can the local P1 path load the ten Paper B checkpoints under one NF4
recipe, emit 32 new tokens each, unload so VRAM returns, and keep the
test suite green — without spending hosted USD and without opening
the 12W experiment?

This stage does **not** ask whether Base and Instruct differ. It does
**not** measure \(G_t\). It does **not** start S9. It does **not**
download 200 GB until Wave 0 census says disk / VRAM / licences are
enough.

## 2. Entry state

From [Stage 7 REPORT](../stage-7/REPORT.md), [ADR-0018](../../decisions/ADR-0018-s7-manuscript-from-closed-stages.md),
[ADR-0019](../../decisions/ADR-0019-tmlr-correctness-pass.md),
[ADR-0022](../../decisions/ADR-0022-occupancy-replication-panel.md):

- Paper A S0–S7 is closed. Occupancy exists on hosted `or-qwen3-8b`
  P1 at `W=4096`, T=0.3, 12 turnovers. H1 unsupported. F4 is an
  ensemble domain gap, not recovered prompt memory.
- ADR-0019 rejected opening S8 *as a Paper A writing stage*. ADR-0023
  opens S8+ as **Paper B**. Closed S0–S7 claims are not rewritten.
- Hosted OpenRouter Qwen is **not** a matched Instruct cell for Paper B.
- Local generate exists ([ADR-0011](../../decisions/ADR-0011-local-base-provider.md))
  for CPU Gemma 3. No bitsandbytes, no unload, no local embed, no
  `serialization` field. `_LOAD_KEYS` does not include quant knobs.
- Degeneracy defaults (chunk=1024) are frozen for Paper B: ngram 3,
  loop 0.083 / 0.5, shingle 5, Jaccard 0.0122, novelty 0.872,
  cosine 0.98, `N_confirm=3` (ADR-0023 F1). S8 smoke uses
  `chunk_size=32` only because `T=32`; it does **not** recalibrate
  those thresholds.
- Ledger after Paper A: **$16.34 of $200**. S8 generate is $0.
- Wave 0 `CENSUS.md` may be written by a sibling. This plan does not
  invent hardware numbers and will not overwrite that file.

## 3. Experiment matrix

**Smoke only.** One window × one temperature × one semantic seed ×
one stochastic seed × **ten NF4 generators** = **10 trajectories** ×
**32 generated tokens** = **320 output tokens**. INT8 twins are in
the library and are **not** in this matrix.

Authoritative file:
[`configs/stages/stage8_paperb_foundations.yaml`](../../../configs/stages/stage8_paperb_foundations.yaml).

| # | Pass | Config / source | Trajectories | Generated tokens |
| --- | --- | --- | ---: | ---: |
| S8.0 | Wave 0 census | `docs/stages/stage-8/CENSUS.md` (sibling; do not overwrite) | 0 | 0 |
| S8.1 | Wave 1 harness | bitsandbytes, unload, scheduler, serialization, local embed, persistence (other agents) | 0 | 0 |
| S8.2 | NF4 smoke | `stage8_paperb_foundations.yaml` | 10 | 320 |
| S8.3 | Unload / doctor | `afterlife doctor` + VRAM events | 0 | 0 |

| knob | smoke value | later L0 (S9–S11), not this file |
| --- | --- | --- |
| `W` | 32 (`T ≥ W` validator) | 4096 |
| `B` | 32 | 1024 |
| `T` | 32 | 49152 (12 turnovers) |
| `chunk_size` | 32 | 1024 |
| protocol | `P1_reprompt` | `P1_reprompt` |
| temperature | 0.3 | 0.3 |
| seeds | `physics` × `s1` | 10 domains × `{1,2,3,4}` |
| generators | 10 NF4 slugs | same 10; INT8 / native-chat in S9/S11 YAMLs |
| embeddings listed | `local-bge-m3`, `local-qwen3-embed-8b` | same two; embed after Wave 1, not as S8 headline |
| `max_concurrent` | 1 | 1 |
| `budget_usd` | 0.0 | 0.0 generate |

Not in this opening: 12W matrix, INT8 20-traj control, native-chat
arm, L1 48W, L2 5M, Gemini embed, P2, Think-line OLMo, Ministral
Reasoning, Gemma E4B substitute, `paper/main.tex`.

Live smoke, when authorised, is **one generator per `run_id`** (or
strict A→unload→B). Expanding ten slugs in one YAML is for `afterlife
plan` / estimate only until Wave 1’s scheduler exists.

## 4. Computations

Ordered. This kickoff stops after (0) documentation. Later agents
execute 1–6. Degeneracy-first still applies if anyone embeds smoke
chunks — they must not read geometry as science.

0. **This kickoff (done here):** ADR-0023…0026, research-plan S8+,
   stage-8 PLAN/README, generator/embedding/stage YAML, `artifacts/stage-8/`.
   No generate. No weight download. No harness implementation.
1. Wave 0 census → `CENSUS.md` (sibling). Gate: no 200 GB download
   without VRAM / disk / licence rows.
2. Wave 1 harness (sequential): quant `_LOAD_KEYS`, unload + registry,
   one-generator-per-run, `raw_bytes` / thinking guard, local embed,
   persistence estimators (ADR-0025). CI stays torch-free.
3. `afterlife doctor` — CUDA, VRAM, HF auth, ten revision pins once
   census has them.
4. `afterlife plan` then `afterlife estimate` on
   `configs/stages/stage8_paperb_foundations.yaml` (must print 10
   trajectories, $0). Human yes before any live generate.
5. Smoke generate: 32 tokens × 10 checkpoints, `raw_completion`,
   record `hf_revision`, `quant_config`, peak VRAM. Fail-fast on first
   OOM or thinking-storm. Do not “try Gemma QAT”.
6. Unload check: VRAM after last unload within ±10% of the pre-load
   baseline. `pytest` / `ruff` / `mypy` green on the touched suite.
7. **Stop.** Do not start S9. Microbench (2 turnovers × 4 family
   heads) is Wave 2 after smoke, still not S9.

## 5. Exit criteria

Written before smoke data. Score in REPORT.

| # | Criterion | Threshold |
| --- | --- | --- |
| E1 | Ten-way load + 32 tokens | 10/10 checkpoints `STATUS=COMPLETED` at `target_tokens=32`; manifest records `hf_revision` and the NF4 (or documented) `quant_config` |
| E2 | Unload | after the last `local.model.unloaded`, used VRAM is within **±10%** of the process baseline measured before the first load |
| E3 | Suite | `pytest` green on the Wave 1 tests; `ruff` and `mypy` clean |
| E4 | No scientific generate | no S8 `run_id` with `target_tokens > 32`; no 12W YAML executed in this stage |
| E5 | Spend | hosted ledger increment **$0.00** for S8 generate/embed |
| E6 | Scheduler | live smoke used one generator per run **or** documented A→unload→B; two CUDA models never coresident |
| E7 | Census before download | `CENSUS.md` exists with VRAM budget, free disk, and licence/gate rows before Hub weights are fetched |
| E8 | Tokenizer identity | encode/decode round-trip on the ten `seed_bank_v1` domain texts is 10/10 per loaded tokenizer, or the failing checkpoint is stopped with a recorded reason (not skipped silently) |
| E9 | Gemma OOM policy | if Gemma 12B NF4 OOMs, the stage is PARTIAL and asks the human; no E4B / `B` cut / offload substitute |
| E10 | Quant keys isolated | unit test: bitsandbytes / `load_in_4bit` / `bnb_*` / `device_map` / `revision` do not appear in `generate()` kwargs |

## 6. Pre-registered predictions

Empty `observed` is filled by the report.

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | After Wave 1, 10/10 NF4 checkpoints complete a 32-token P1 step | 0.55 | |
| P2 | Gemma 4 12B NF4 either fits the measured VRAM budget or OOMs; we will not silently replace it | 0.80 | |
| P3 | Unload returns used VRAM to within ±10% of the pre-load baseline | 0.70 | |
| P4 | Hosted S8 spend is $0 | 0.95 | |
| P5 | Qwen Instruct 32-token smoke has zero think/reasoning tokens under `enable_thinking=false` | 0.65 | |
| P6 | Ministral and Gemma load on a text-only path (conditional-generation wrapper or equivalent) without invoking vision | 0.60 | |
| P7 | `afterlife plan` on this YAML prints **10** trajectories and **320** output tokens | 0.90 | |
| P8 | First attempted live generate *before* `_LOAD_KEYS` is extended would mis-route quant kwargs — therefore smoke is refused until E10 is green | 0.85 | |

P1 is the honest low one: Hub ids, gates, and 12 GB vs 16 GB are
Wave 0 facts, not this kickoff’s measurements.

## 7. Budget and wall-clock

- **API / ledger:** **$0**. YAML `budget_usd: 0.0`. Stop and ask
  before any hosted call (including optional Gemini).
- **Project ceiling:** $200 ([ADR-0013](../../decisions/ADR-0013-project-ceiling-200.md));
  remaining ≈ $183.66. Do not raise it. Local generate does not spend it.
- **Disk:** Wave 0 must record free space. Plan estimate is
  **≥250 GB** free on the HF cache volume *before* a full ten-way
  download. Download is not ledger USD; it still needs a human yes.
- **Wall-clock (guesses; replace after microbench):** census hours;
  Wave 1 code 2–5 calendar days; smoke 10×32 tokens is minutes–an hour
  after weights are local, not a multi-day generate.
- **Stop-and-ask:** any hosted $; Gemma OOM; Hub id mismatch vs
  census; raising `target_tokens` above 32; starting S9; changing
  F1 thresholds.

## 8. Risks specific to this stage

| Risk | Mitigation |
| --- | --- |
| Quant keys leak into `generate()` | E10; no live smoke until `_LOAD_KEYS` includes them (ADR-0024) |
| Ten slugs interleave on one GPU | one generator per run; `max_concurrent: 1` is not enough |
| Gemma 12B OOM on 12 GB | E9; stop; no silent substitute |
| Gated Gemma / Ministral without `HF_TOKEN` | E7 census; smoke does not start |
| Multimodal `AutoModelForCausalLM` failure | text-only path (ADR-0024); P6 |
| Qwen thinking in `raw_completion` | `enable_thinking=false` + per-step fail |
| Treating 32-token smoke as L0 | E4; YAML `T=32`; report says so |
| Recalibrating degeneracy because smoke `chunk_size=32` | F1 forbids; smoke is not a degeneracy study |
| Overwriting sibling `CENSUS.md` | this kickoff does not write that path |
| Downloading 200 GB on a full disk | E7 |
| Opening S9 from a red harness | stage discipline; S9 needs this REPORT |

## 9. Definition of done

- [x] ADR-0023…0026 written (this kickoff)
- [x] `PLAN.md` / `README.md` / stage-8 YAML / local model+embed libs
- [ ] `CENSUS.md` from Wave 0 (sibling)
- [ ] Wave 1 harness + E10
- [ ] Human yes on download, then on smoke generate
- [ ] E1–E10 scored in `REPORT.md`
- [ ] Hosted spend $0
- [ ] No 12W generate
