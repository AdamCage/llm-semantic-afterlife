# Stage 8 / Wave 2 — NF4 smoke + microbench

Live local generate on WSL2 Ubuntu, `HF_HOME=/home/adam/hf-paperb`,
bitsandbytes NF4, `attn_implementation: sdpa`, `serialization: raw_bytes`.
Hosted ledger increment **$0.00**. This file is an operational record.
It does **not** measure \(G_t\), lock, or 12W occupancy. It is **not** S9.

Tidy tables: [`artifacts/stage-8/smoke/smoke_10x32.parquet`](../../../artifacts/stage-8/smoke/smoke_10x32.parquet),
[`artifacts/stage-8/smoke/microbench.parquet`](../../../artifacts/stage-8/smoke/microbench.parquet).

## Verdict

| Gate | Result |
| --- | --- |
| 10/10 smoke `STATUS=COMPLETED` at `T=32` | **yes** (Ministral after loader fix) |
| Family-head microbench `T=8192` / `W=4096` | **3/4** (Qwen Instruct, Ministral Instruct, OLMo Base). Gemma IT **failed** |
| Thinking tokens | **0** on every completed step |
| Stop events (completed smokes / exclusive micros) | **0** |
| Block fill (those runs) | **1.0** |
| S9 12W matrix | **not started** |

## Loader fix

First Ministral smokes
(`…T210848…`, `…T210903…`) failed instantly:
`AutoModelForCausalLM` cannot load `Mistral3Config`.
WSL `transformers==5.17.0` already exports
`Mistral3ForConditionalGeneration` and
`Gemma4UnifiedForConditionalGeneration`. The bug was the loader, not
missing weights (Instruct cache was empty; Base had a 5.1 GB incomplete
blob). Re-download was not the fix.

`providers/local.py` now picks `config.architectures[0]` (with a
`transformers.models.*` bind), then ImageTextToText / MultimodalLM autos,
then CausalLM only for Gemma/Unified. Ministral without a class raises
instead of falling through to CausalLM. Quant keys stay in `_LOAD_KEYS`.
Text-only `generate` sends `input_ids` + `attention_mask` only. CI tests
are torch-free fakes in `tests/test_wave1_paper_b_harness.py`.

## 10-model smoke (`W=B=T=32`, physics × s1)

| Slug | `run_id` | Loader | `hf_revision` | Peak VRAM | tok/s | fill | stop | think | Notes |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| pb-qwen3-8b-base | `s8-paperb-smoke-qwen3-8b-base-20260910T200925Z-28827fb7` | AutoModelForCausalLM / `Qwen3ForCausalLM` | `49e3418fbbbc…` | 5887.6 | — | 1.0 | 0 | 0 | `local.generate.completed` tok/s not logged on this run |
| pb-qwen3-8b-instruct | `s8-paperb-smoke-qwen3-8b-instruct-20260910T202114Z-c1a44453` | same | `b968826d9c46…` | 5887.6 | 13.638 | 1.0 | 0 | 0 | |
| pb-olmo3-7b-base | `s8-paperb-smoke-olmo3-7b-base-20260910T203216Z-a08dbea4` | AutoModelForCausalLM / `Olmo3ForCausalLM` | `a81bae42db39…` | 4822.9 | 14.805 | 1.0 | 0 | 0 | |
| pb-olmo3-7b-sft | `s8-paperb-smoke-olmo3-7b-sft-20260910T204127Z-e446abc8` | same | `e1452fc572d5…` | 4822.9 | 14.692 | 1.0 | 0 | 0 | |
| pb-olmo3-7b-dpo | `s8-paperb-smoke-olmo3-7b-dpo-20260910T205044Z-1d237e73` | same | `b33130b7de49…` | 4822.9 | 15.304 | 1.0 | 0 | 0 | |
| pb-olmo3-7b-rlvr | `s8-paperb-smoke-olmo3-7b-rlvr-20260910T205941Z-2fc2def8` | same | `6e5971d9eba4…` | 4822.9 | 15.428 | 1.0 | 0 | 0 | |
| pb-ministral-8b-base | `s8-paperb-smoke-ministral-8b-base-20260910T215816Z-42f29e6e` | `Mistral3ForConditionalGeneration` | `d4883f9b36aa…` | 6425.2 | 13.419 | 1.0 | 0 | 0 | retry; T210848 FAILED |
| pb-ministral-8b-instruct | `s8-paperb-smoke-ministral-8b-instruct-20260910T220441Z-1c1fd482` | same | `f6fae9795746…` | 5923.7 | 14.746 | 1.0 | 0 | 0 | retry; T210903 FAILED; sibling dup T220451 |
| pb-gemma4-12b-base | `s8-paperb-smoke-gemma4-12b-base-20260910T210919Z-2cf3ff6d` | CausalLM auto → `Gemma4UnifiedForConditionalGeneration` | `023679ed352d…` | 7381.7 | 8.129 | 1.0 | 0 | 0 | repetitive Polyakov text |
| pb-gemma4-12b-it | `s8-paperb-smoke-gemma4-12b-it-20260910T213805Z-58e90177` | `Gemma4UnifiedForConditionalGeneration` | `707f0a3b8a3c…` | 7381.7 | 8.820 | 1.0 | 0 | 0 | 3 steps; first 80 chars are commas |

Tokenizer round-trip on the physics smoke step: **true** on all ten
completed runs. Served provider: **local**. Quant: **nf4**. After unload,
`nvidia-smi` used memory returned to ~0.9–1.0 GiB (desktop baseline).

Gemma IT smoke `STATUS=COMPLETED` but the visible text is degenerate
commas. That is a measurement, not a reason to retune sampling.

## Microbench (`W=4096`, `B=1024`, `T=8192`, 2 turnovers, physics × s1)

| Family head | `run_id` | tok/s mean | tok/s median | Peak VRAM | fill | stop | think | 12W h/traj (48 steps) | Valid? |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen Instruct | `s8-paperb-micro-qwen3-8b-instruct-20260910T221623Z-61c9ad74` | 24.635 | 25.053 | 6816.5 | 1.0 | 0 | 0 | 0.550 | yes |
| Ministral Instruct | `s8-paperb-micro-ministral-8b-instruct-20260910T233421Z-e528749b` | 28.765 | 28.749 | 6941.3 | 1.0 | 0 | 0 | 0.475 | yes (exclusive re-run) |
| OLMo Base | `s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f` | 26.431 | 26.388 | 7206.3 | 1.0 | 0 | 0 | 0.517 | yes (exclusive re-run) |
| Gemma IT | `s8-paperb-micro-gemma4-12b-it-20260910T233125Z-f89a95a4` | — | — | 7700.9 | — | — | 0 | — | **no** |

Gemma IT failed after 2 steps / 222 tokens:
`5 consecutive empty completions; the model is not free-running under
this continuation mechanism`. Not OOM (peak 7700.9 MiB of 16376).
Family skipped for wall-clock. Do not cut `B` or swap E4B.

Do **not** use `…T222222…` (Ministral) or `…T222217…` (OLMo) for
tok/s: two agents loaded both checkpoints at once (ADR-0024 violation).
`…T233347…` is a response-cache hit, not a measurement.

## S9 wall-clock (measured, Qwen only)

S9 is Qwen Base + Instruct, 10 domains × 4 stochastic seeds, `W=4096`,
`T=49152` (12 turnovers), `B=1024`, fill 1.0 ⇒ **80** trajectories ×
**48** steps.

From exclusive Qwen Instruct microbench (median step 41.232 s, prefill
included):

\[
80 \times 0.550\,\mathrm{h} \approx \mathbf{44\ hours}
\]

exclusive GPU, one generator at a time. Decode-only check:
\(80 \times 49152 / 24.635 / 3600 \approx 44.3\,\mathrm{h}\).

Later-stage sketches from the other exclusive heads (not S9):

| Stage | Cells | h/traj | Exclusive GPU |
| --- | ---: | ---: | ---: |
| S10 OLMo ladder (4 ckpts × 40) | 160 | 0.517 | ~83 h |
| S11 Ministral pair (2 × 40) | 80 | 0.475 | ~38 h |
| S11 Gemma pair | 80 | unknown | **blocked** until empty-completion at `W=4096` is understood |

## Remaining blockers

1. **Human yes before S9 12W.** This wave does not start it.
2. **One GPU agent.** A sibling race coresided OLMo + Ministral and hung
   the first OLMo microbench. Kill leftover `afterlife generate` before
   the next exclusive run.
3. **Gemma IT at `W=4096`.** Empty completions abort the trajectory.
   Smoke at `W=32` completed but looked degenerate. No silent substitute.
4. **Qwen Base smoke tok/s** missing from events (load-dominated latency
   only). Use Instruct microbench for S9 hours; Base should be re-timed
   on the first S9 run, not guessed from Instruct.
5. **E8 10-domain tokenizer sweep** was not re-run as a standalone pass;
   physics-step `tokenizer_roundtrip_ok` was true on all ten smokes.
6. **INT8 Qwen twins** are still out of the smoke matrix (ADR-0023 F2).
