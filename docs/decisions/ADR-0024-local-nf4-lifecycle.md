# ADR-0024: Local NF4 lifecycle (load, unload, one generator per run)

Status: accepted
Date: 2026-09-09
Stage: S8 (harness)
Amends: [ADR-0011](ADR-0011-local-base-provider.md) (extends; does not
replace the local client contract)

## Context

ADR-0011 added `api: local` for a CPU Gemma 3 existence check. That
path knows `device` / `dtype` / `attn_implementation`. It does not
know bitsandbytes. `_LOAD_KEYS` in
[`local.py`](../../src/semantic_afterlife/providers/local.py) will
forward unknown extra keys into `model.generate`. A 12 GB–16 GB
desktop cannot keep ten 7–12B checkpoints resident. Ministral 3 and
Gemma 4 12B are multimodal wrappers. The factorial planner expands
`generators × windows × …` and will interleave models if one YAML
lists ten slugs.

Paper B requires one quantization algorithm on official BF16 weights,
explicit unload, and a text-only generate path that uses the same
tokenizer as `Tail_W`. This ADR freezes that protocol. Wave 1
implements it. This file does not ship the code.

## Decision

### 1. One NF4 recipe for all ten checkpoints

Load official BF16 (or BF16-equivalent) Hub weights through
**bitsandbytes NF4**, not GGUF, not QAT, not FP8 Instruct, not LM
Studio / Ollama. The same knobs go in `extra_body` and into the run
manifest:

- `load_in_4bit: true`
- `bnb_4bit_quant_type: nf4`
- `bnb_4bit_use_double_quant: true`
- `bnb_4bit_compute_dtype: bfloat16`
- `device_map: cuda`
- `attn_implementation: sdpa` (default; `flash_attention_2` only if a
  later microbench shows a win *and* stability — that swap is a
  recorded amendment, not a silent default change)
- `revision` / `tokenizer_revision`: pinned Hub commits after Wave 0
  census, before first smoke that counts

INT8 control is **Qwen only**: `load_in_8bit: true`, no `load_in_4bit`,
same `device_map` / `attn_implementation` / `serialization`. Slugs:
`pb-qwen3-8b-base-int8`, `pb-qwen3-8b-instruct-int8`. INT8 seeds are
F2 in [ADR-0023](ADR-0023-paper-b-local-four-family.md). INT8 is not
in the S8 smoke matrix.

`bitsandbytes` is added to the `local` extra. CI stays torch-free.
Tests inject a backend and assert quant keys never reach `generate()`.

### 2. Quant keys are load keys

Wave 1 **must** add every quant / map / revision field to `_LOAD_KEYS`
before the first smoke. Until that lands, the YAML knobs are
documentation of the contract; executing generate with them would
mis-route `BitsAndBytesConfig` into sampler kwargs. S8 smoke does not
run until that gate is green.

### 3. Unload and registry

One CUDA-resident generator at a time. After a checkpoint’s
trajectories finish:

1. `unload(model_id)` / `aclose()` of the local client
2. clear the process-wide client registry
3. `torch.cuda.empty_cache()`
4. log `local.model.loaded` / `local.model.unloaded` with peak VRAM

Two models in `_resolved` on `cuda` is an error. `max_concurrent: 1`
is required and **not sufficient** if one run lists ten slugs.

### 4. One generator per generate run

Preference: **one checkpoint = one `afterlife generate` run_id**. An
orchestrator concatenates analysis. Alternative, if a single YAML must
expand several slugs: the planner emits all cells of model A, a
barrier unload, then model B — never A/B interleaving on one GPU.

S8 smoke YAML lists ten slugs so `afterlife plan` can expand the cell
list. That file is **not** a licence to load ten models in one live
process until the scheduler exists.

### 5. Multimodal checkpoints, text-only path

Ministral 3 and Gemma 4 12B may load as
`*ForConditionalGeneration`. Paper B generate is **text-only**:

- the project tokenizer (`add_special_tokens=False`) still defines
  `Tail_W` and encode/decode
- vision / image towers are not invoked
- `AutoModelForCausalLM` failure is a loader bug to fix, not a reason
  to skip the family
- tokenizer round-trip on `seed_bank_v1` domain texts is 10/10 or the
  checkpoint is stopped with a recorded reason

### 6. Serialization and thinking (contract; code in Wave 1)

Primary `serialization: raw_bytes`: Base and Instruct receive the same
`encode(seed)` bytes. `native_chat` is a documented secondary arm;
template bytes go in the request record. Qwen:
`enable_thinking=false` (or equivalent); a step with reasoning / think
tokens > 0 fails (same spirit as [ADR-0005](ADR-0005-reasoning-tokens-disqualify.md)).
Think-line OLMo and Ministral Reasoning are not in the matrix.

Until `GeneratorConfig` grows an explicit `serialization` field, the
knob lives in `extra_body` and must be treated as protocol, not as a
generate() sampler argument (`_LOAD_KEYS` or a dedicated field).

### 7. Local embeddings after unload

BGE-M3 and Qwen3-Embedding-8B run locally. Qwen-embed NF4 is sequential
and only after the generator is unloaded. Content-addressed cache
`sha256(model_id ‖ text)` stays. Paper B stage configs do not call
RouterAI for those two spaces. Vector provenance:
[ADR-0021](ADR-0021-occupancy-record-not-recoverable.md) — parquet plus
per-trajectory vectors, not runs-only.

### 8. Hardware stop rules

- Gemma 12B NF4 OOM: stop. No `gemma-4-E4B`, no KV-offload that
  changes dynamics, no unannounced `B_max` cut (that breaks
  comparability).
- Do not download ~150–200 GB of weights until Wave 0 census records
  free disk ≥250 GB, VRAM budget, and licence / `HF_TOKEN` gates.
- `cache: steps_only` for ultra-long L2 (S12); full prompt cache is
  forbidden there.

## Alternatives considered

- **GGUF / llama.cpp / Ollama.** Rejected: a second quantisation
  surface; Paper B’s NF4↔INT8 control would not be the same algorithm.
- **Native Windows bitsandbytes as the specified lane.** Allowed if
  Wave 0 finds WSL2 blocked; the quant recipe stays identical.
- **Keep models resident and swap KV only.** Rejected on 12 GB.
- **`max_concurrent: 1` without unload.** Rejected: the registry and
  `_resolved` would still pin the first 8B forever.
- **BF16 primary on 8B/12B.** Rejected: does not fit the stated card.

## Consequences

- [`configs/models/generators_local_paperb.yaml`](../../configs/models/generators_local_paperb.yaml)
  carries the ten NF4 slugs plus two Qwen INT8 twins with the knobs
  above, even before Wave 1 wires them.
- S8 exit includes: 10/10 load+32 tokens; unload frees VRAM to within
  ±10% of the pre-load baseline; ruff / mypy / pytest green; no
  generate beyond smoke.
- A generate that spends hosted USD is out of contract for this
  programme unless a later estimate + human yes names Gemini.

## Reversal cost

Low before first smoke: delete the extra and the YAML knobs. After
S9, changing quant algorithm invalidates Δ and concordance. That is a
new ADR, not a mid-run flag.
