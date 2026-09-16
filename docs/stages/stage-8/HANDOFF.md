# Stage 8 — HANDOFF

Operational status for Paper B continuation. Scientific contract:
[`PLAN.md`](PLAN.md). Freeze: ADR-0023…0026. Census: [`CENSUS.md`](CENSUS.md).
Wave 2 record: [`SMOKE.md`](SMOKE.md).

## Phase 1 — freeze + census

| Item | Status |
| --- | --- |
| ADR-0023…0026 | **on disk** under `docs/decisions/` |
| Research plan S8+ | **amended** (Paper B open; S9→S10→S11→S12→S13 frozen) |
| `docs/stages/stage-8/PLAN.md` + README | **present** |
| `CENSUS.md` | **present** (VRAM **16 GB** measured; WSL2 preferred) |
| Configs | `configs/models/generators_local_paperb.yaml`, `configs/embeddings/embeddings_local.yaml`, `configs/stages/stage8_paperb_foundations.yaml` |
| Seed-bank rationale (ADR-0026) | comment block updated; **texts unchanged** |

## Wave 1 — harness

| Item | Status |
| --- | --- |
| bitsandbytes NF4/INT8 load + `_LOAD_KEYS` isolation | **done** |
| `unload` + CUDA cache clear + `forget_client("local")` | **done** |
| One local generator per generate config | **done** |
| `serialization: raw_bytes \| native_chat` | **done** |
| Thinking leak guard | **done** |
| Text-only multimodal loader (`architectures[0]`) | **done** this wave (Ministral / Gemma 4) |
| Local embed client | **done** |
| `analysis/persistence.py` | **done** |

## Wave 2 — smoke + microbench (this continuation)

| Item | Status |
| --- | --- |
| 10/10 NF4 smoke `T=32` | **done** — see [`SMOKE.md`](SMOKE.md) |
| Microbench 2 turnovers × 4 family heads | **3/4** — Gemma IT failed empty completions at `W=4096` |
| Artifacts | `artifacts/stage-8/smoke/smoke_10x32.parquet`, `microbench.parquet` |
| S9 12W | **opened** 2026-09-11 — [`../stage-9/HANDOFF.md`](../stage-9/HANDOFF.md) |

Canonical completed smoke `run_id`s are in `SMOKE.md`. Exclusive
microbench ids:

- `s8-paperb-micro-qwen3-8b-instruct-20260910T221623Z-61c9ad74`
- `s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f`
- `s8-paperb-micro-ministral-8b-instruct-20260910T233421Z-e528749b`
- Gemma IT micro `…T233125…` **FAILED** (empty completions, not OOM)

Ignore `…T222217…` / `…T222222…` (coresident) and `…T233347…` (cache hit).

S9 exclusive-GPU estimate from Qwen Instruct microbench: **~44 hours**
(80 traj × 0.550 h).

## Do not (next agent)

- Start a second `afterlife generate` while S9 is on the GPU
- Edit `.cursor/plans/paper_b_local_matrix_5105e6af.plan.md`
- Swap Gemma for E4B / cut `B` / offload KV
- Load `mistralai/Ministral-3-8B-Instruct-2512` (FP8)
- Launch a second `afterlife generate` while one is on the GPU
- Commit unless the human asks
- Write `paper/main.tex`

## Next

S9 Qwen 12W opened 2026-09-11. Gemma at `W=4096` remains a recorded
skip for wall-clock, not a licence to drop the family from S11.

WSL env: `UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife`,
`HF_HOME=/home/adam/hf-paperb`, `transformers==5.17.0`. One checkpoint
per `wave2_run_one.sh`.

## Return contract

- `status: ok` (Wave 2 done; S8 REPORT drafted; S9 opened)
- `run_ids:` listed in `SMOKE.md`
- `blockers:` Gemma IT empty-completion at `W=4096` (S11)
- `next_agent: S9 generate` — see [`../stage-9/HANDOFF.md`](../stage-9/HANDOFF.md)
- `do_not: S10; plan-file edit; E4B swap; dual GPU jobs`
