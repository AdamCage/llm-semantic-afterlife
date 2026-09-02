# S3.0 follow-up — RouterAI embeddings (2026-09-02)

Dated addendum. It does **not** rewrite the Stage 3 opening
([`REPORT.md`](REPORT.md), ADR-0012). Geometry and seed-separation are
still unrun. `W = 256` still does not transfer to `W = 4096`.

## Decision that this executes

ADR-0012 deferred S3.0 embeddings until a hosted embedding balance
existed. The configured spaces (`bge-m3`, `qwen3-embed-8b`) are
`api: routerai` in `configs/embeddings/embeddings.yaml`. OpenRouter was
not called. RouterAI `/credits` was 597.69 at the pre-embed probe
(2026-09-02); a one-word `POST /embeddings` on `baai/bge-m3` returned
200.

## Estimate (before the call)

| quantity | value |
| --- | --- |
| source generation | `s3-local-base-20260901T184812Z-cc80633b` |
| chunks | 96 (8 trajectories × 12) |
| generator tokens | 24,576 per space (256 × 96) |
| spaces | `bge-m3`, `qwen3-embed-8b` |
| live catalog price | deepinfra / parasail / nebius ≈ $0.01404 / M tokens (`1.1229309e-6` RUB/token × `AFTERLIFE_USD_PER_RUB=0.0125`) |
| forecast | ≈ $0.00069 at 49,152 generator tokens; actual billed tokens can differ |
| hard ceiling | `$0.50` (`configs/stages/stage3_s30_embed.yaml`, `AFTERLIFE_BUDGET_USD_PER_RUN=0.50`) |
| project remaining | $38.43 of $50 before this run |

`afterlife estimate` on this YAML forecasts **generation**, not
embeddings. The table is from `chunks.parquet` plus live
`GET /models/…/endpoints`.

## Embed run

`run_id`: `s3-embed-local-base-embed-20260902T051805Z-2ce86473`

- config: `configs/stages/stage3_s30_embed.yaml`
- git SHA at start: `eff8e2c` (tree dirty: local `uv.lock` churn from
  `uv run`, not a scientific knob; recorded in the manifest)
- `STATUS`: COMPLETED
- cache: 0 hits / 96 misses in each space (new Gemma-3-1B-PT chunks)
- `bge-m3`: 96 × 1024, provider-normalised, 6 live batches
- `qwen3-embed-8b`: 96 × 4096, provider-normalised, 12 live batches
- no NaN; L2 norms in `[0.9999999, 1.0000001]`
- wall clock: 05:18:05–05:19:27 UTC (~82 s)
- `requests/` is empty on this embedding run (harness gap; cache holds
  the content-addressed responses)

## Spend

The ledger wrote **18** embedding rows, all `from_cache=false`, all
`cost_usd=0`. That is a pricing hole, not a free call: RouterAI
`usage.cost` was absent and `price_usd_per_m_input` is `null` in
`embeddings.yaml`, so `RouterAIClient._cost` returns 0.

Billed **prompt tokens** (embedder tokenizer, not generator tokens):

| space | batches | prompt tokens | implied USD at $0.01404/M |
| --- | ---: | ---: | ---: |
| `bge-m3` | 6 | 30,010 | $0.000421 |
| `qwen3-embed-8b` | 12 | 26,353 | $0.000370 |
| **both** | **18** | **56,363** | **$0.000791** |

RouterAI `/credits` after the run: **597.629**. Pre-embed probe was
**597.69**. Delta ≈ **0.061 RUB ≈ $0.00076**. That matches the
reconstructed catalog price to the precision of the rounded pre-embed
reading.

OpenRouter spend for this follow-up: **$0**.

Project ledger still shows **$11.57 of $50** because the embed rows
recorded $0. The reconstructed ~$0.0008 is below the $0.50 ceiling and
does not move the reported project total at the displayed cents.

## What this does not establish

- No geometry, MSD, half-life, or seed-separation. Those are a later
  `$0` CPU pass on this `run_id`, joined to
  `s3-degeneracy-20260901T193542Z-f76d2086` **before** any confinement
  sentence (8/8 trajectories are loops; a confined MSD of a loop is the
  Stage 1 trap).
- Not a measurement at `W = 4096`.
- Not a Stage 4 kickoff.
- Not a rewrite of F3 or of the Stage 3 PARTIAL verdict.

Tidy pointer: [`artifacts/stage-3/embed/s30_embed_summary.json`](../../../artifacts/stage-3/embed/s30_embed_summary.json).
