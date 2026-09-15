# Stage 8 report — Paper B local harness is fit for S9

**Status.** Computations finished 2026-09-10. Overall: **PASS** on the
loading contract; **PARTIAL** on E6 (one Wave 2 coresidency) and E8
(physics-step tokenizer only). Protocol verdict for S9 Qwen 12W:
**fit**. This stage makes **no** \(G_t\) / lock / post-training claim.

Plan: [`PLAN.md`](PLAN.md). Operational record: [`SMOKE.md`](SMOKE.md).
Freeze: ADR-0023…0026. Branch: `stage-8` (working tree dirty; manifests
record `git_dirty`). Hosted Stage 8 spend **$0.00**.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | 10/10 NF4 smoke `T=32` `COMPLETED` with `hf_revision` + quant | **PASS** | [`SMOKE.md`](SMOKE.md); [`smoke_10x32.parquet`](../../../artifacts/stage-8/smoke/smoke_10x32.parquet) |
| E2 | Unload to ±10% of pre-load used VRAM | **PASS** | after each smoke unload, `nvidia-smi` used memory returned to ~0.9–1.0 GiB (desktop baseline); idle check 2026-09-11: 591 MiB, Xwayland only |
| E3 | Wave 1 tests + ruff/mypy on touched suite | **PASS** | `tests/test_wave1_paper_b_harness.py` + `tests/test_local_client.py` green (26) after the ConditionalGeneration loader |
| E4 | No scientific 12W generate in S8 | **PASS** | no S8 YAML with `target_tokens=49152`. Wave 2 microbench is `T=8192` (PLAN §4.7), not S9 |
| E5 | Hosted ledger increment $0.00 | **PASS** | local generate; `budget_usd: 0.0` |
| E6 | One CUDA generator; never two coresident | **PARTIAL** | sequential smoke was one-per-run. Wave 2 microbench once loaded OLMo + Ministral together (`…T222217…` / `…T222222…`); those tok/s are discarded |
| E7 | Census before Hub weight download | **PASS** | [`CENSUS.md`](CENSUS.md) existed; weights went to WSL `HF_HOME=/home/adam/hf-paperb` |
| E8 | Tokenizer round-trip on ten domain texts | **PARTIAL** | physics-step `tokenizer_roundtrip_ok=true` on all ten completed smokes. Standalone 10-domain sweep was not re-run as a separate pass |
| E9 | Gemma OOM → stop; no silent substitute | **PASS** | Gemma 12B NF4 loaded (peak 7381.7 MiB). IT microbench failed empty completions, not OOM. No E4B / `B` cut |
| E10 | Quant keys isolated from `generate()` | **PASS** | `_LOAD_KEYS` + `test_wave1_paper_b_harness.py` |

---

## 2. Results

S8 asked whether the local P1 path can load the ten Paper B
checkpoints. It can, after a loader fix.

**Loader.** First Ministral smokes (`…T210848…`, `…T210903…`) failed
in ~1 s: `AutoModelForCausalLM` cannot construct `Mistral3Config`.
WSL `transformers==5.17.0` already exports
`Mistral3ForConditionalGeneration`. Re-download was not the fix.
`providers/local.py` now binds `config.architectures[0]`, then
multimodal autos, then CausalLM only where that dispatch is valid.

**Smoke (`W=B=T=32`, physics × s1).** 10/10 `COMPLETED`. Fill 1.0,
stop 0, thinking 0, served provider `local`, quant NF4. Peak VRAM
4823–7382 MiB on a 16376 MiB GPU. Canonical `run_id`s in
[`SMOKE.md`](SMOKE.md).

Gemma IT smoke completed but the visible text is comma-degenerate.
Gemma Base repeated Polyakov-loop prose. Those are measurements, not
a reason to retune sampling.

**Microbench (`W=4096`, `T=8192`).** Exclusive-GPU family heads:

| Head | `run_id` | tok/s median | 12W h/traj | Valid |
| --- | --- | ---: | ---: | --- |
| Qwen Instruct | `s8-paperb-micro-qwen3-8b-instruct-20260910T221623Z-61c9ad74` | 25.053 | 0.550 | yes |
| Ministral Instruct | `s8-paperb-micro-ministral-8b-instruct-20260910T233421Z-e528749b` | 28.749 | 0.475 | yes |
| OLMo Base | `s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f` | 26.388 | 0.517 | yes |
| Gemma IT | `s8-paperb-micro-gemma4-12b-it-20260910T233125Z-f89a95a4` | — | — | **no** (5 empty completions) |

S9 exclusive-GPU sketch from Qwen Instruct: **80 × 0.550 h ≈ 44 h**.

### Protocol diagnostics

Smoke and exclusive micros: block fill **1.0**, stop **0**, reasoning
**0**, tokenizer round-trip **true** on the physics step. Qwen Base
smoke did not log decode tok/s (`local.generate.completed` missing
that field); do not invent it. Base 12W hours should be re-timed on
the first S9 Base run.

---

## 3. Prediction vs. outcome

| # | Prediction | Confidence | Observed |
| --- | ---: | ---: | --- |
| P1 | 10/10 NF4 checkpoints complete a 32-token P1 step | 0.55 | **true**, after the Ministral loader fix |
| P2 | Gemma 4 12B NF4 fits or OOMs; no silent replace | 0.80 | **true** (fits). IT then fails empty-completion at `W=4096` |
| P3 | Unload returns used VRAM to ±10% of baseline | 0.70 | **true** on sequential smoke |
| P4 | Hosted S8 spend is $0 | 0.95 | **true** |
| P5 | Qwen Instruct smoke has zero think tokens | 0.65 | **true** (0 on every completed step this wave) |
| P6 | Ministral and Gemma load text-only without vision | 0.60 | **true** (`Mistral3ForConditionalGeneration` / Gemma4 Unified; `input_ids` only) |
| P7 | `afterlife plan` on foundations YAML prints 10 traj / 320 tokens | 0.90 | not re-printed in this close; YAML still expands 10 × 32 |
| P8 | Generate before `_LOAD_KEYS` would mis-route quant kwargs | 0.85 | **true as a gate**: smoke waited for E10 |

---

## 4. Surprises

1. Ministral failed on **class**, not missing weights.
2. Two agents coresided OLMo + Ministral and hung the first OLMo
   microbench. `max_concurrent: 1` does not protect against two
   processes.
3. Gemma IT is not free-running at `W=4096` under this continuation
   (empty completions). Smoke at `W=32` completed with degenerate
   commas. Regime did not transfer.
4. Gemma Base smoke text was repetitive Polyakov continuation of the
   physics seed — recorded, not tuned away.

---

## 5. Threats to validity

- **S8 is not L0.** `T=32` and `T=8192` do not measure 12W occupancy.
- **E8 is incomplete.** Only the physics seed was round-tripped in
  the live smoke step. A silent tokenizer mismatch on another domain
  would void that seed’s `W`.
- **NF4 ≠ hosted Paper A.** Local Instruct is a controlled
  replication stack, not `or-qwen3-8b`.
- **Gemma IT at operating `W`.** Empty completion is a family-level
  risk for S11, not a licence to drop Gemma or cut `B`.
- **Dirty git.** Wave 1–2 code was not committed before smoke;
  manifests carry `git_dirty`.

---

## 6. Cost actuals

| | Estimate | Actual |
| --- | ---: | ---: |
| Hosted generate/embed | $0 | **$0.00** |
| Wall-clock (smoke + exclusive micro + retries) | “minutes–an hour after weights” (PLAN §7) | ~5.5 h sequential smoke after OLMo start + microbench retries the same night |
| Disk | weights on WSL `HF_HOME`, not Windows `C:` | as planned |

---

## 7. Implications for the plan

- **S9 Qwen 12W is authorised by this report** as protocol-fit: Qwen
  Instruct completed 2 turnovers at `W=4096`, `B=1024`, fill 1.0,
  think 0. Human yes 2026-09-11.
- Time S9 from the Instruct microbench (**~44 h** exclusive GPU for
  80 NF4 traj). Re-time Base on its first 12W run.
- S10/S11 sketches: OLMo ~83 h, Ministral ~38 h. Gemma 12W blocked
  on empty-completion until re-measured; no E4B substitute
  (ADR-0024).
- One `afterlife generate` on the GPU. Kill leftovers before the
  next exclusive run.
- Native-chat arm: `build_request` still short-circuits
  `raw_completion` to a raw prompt. Do not generate that arm until
  the serialization branch is independent. Primary S9 is `raw_bytes`.
- Do not start S10 until S9 REPORT says the 12W protocol is fit.
- No ADR. Frozen order unchanged.
