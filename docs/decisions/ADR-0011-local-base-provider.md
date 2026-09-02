# ADR-0011: Local Hugging Face provider for the base-model existence check

Status: accepted
Date: 2026-09-01
Stage: harness (not S3)
Amends: [ADR-0006](ADR-0006-no-base-models-available.md)

## Context

ADR-0006 dropped the hosted base-model arm after Stage 0 found zero
pretrained LMs on RouterAI and OpenRouter. The escalation path was a
small local 1–3B base model. Stage 2 closed without running that check
(ADR-0010). A live catalogue probe on 2026-09-01 still finds **zero**
pretrained generators on either router (OpenRouter 418, RouterAI 466;
every `base` hit is an embedder).

The human asked to merge Stage 2 and then try a local Gemma 3 or Gemma 4
small model through the existing harness.

Hardware on the machine that first ran this path: 4-core CPU, 15 GB RAM,
no GPU.

| Checkpoint | Kind | Weights | Fits here? |
| --- | --- | --- | --- |
| `google/gemma-3-270m` | pretrained (not `-it`) | 0.54 GB | yes, smoke |
| `google/gemma-3-1b-pt` | pretrained | 2.0 GB | yes, S3.0-sized |
| `google/gemma-4-E2B` | pretrained, multimodal | 10.2 GB | tight / no, unquantized |

`google/gemma-4-E2B` is the small Gemma 4 the human named. It is a real
base model and it is ungated. On this 15 GB CPU box it *does* load in
bfloat16 via `AutoModelForCausalLM` (5.10B params,
`Gemma4ForConditionalGeneration`) and a 16-token probe returned in 8 s.
The continuation was degenerate (`<eos>` then `https://` spam). EOS ids
live on `text_config`, not the multimodal wrapper — the client now reads
both. E2B stays in the library and out of the default smoke: multimodal,
10 GB, and not a clean S3.0 object on this evidence.

## Decision

1. Add `api: local` as a first-class `InferenceClient`. Same
   `CompletionRequest` / cache / ledger / replay path as the routers.
   Generation cost is identically $0. Embeddings stay on the existing
   embedding providers so a local trajectory is still readable in BGE-M3
   and Qwen3-Embedding.
2. Encode the prompt with the project's `tokenizers` tokenizer (no BOS,
   `add_special_tokens=False`) and pass those ids to `model.generate`.
   Tail_W and the local sampler then share one tokenisation.
3. Do **not** apply a chat template on base models. Flattening `messages`
   is concatenation only.
4. Optional extra `local` (`torch`, `transformers`, `accelerate`). CI
   stays torch-free; tests inject a `LocalBackend`.
5. This change does **not** open Stage 3. The smoke config is
   `stage: harness`, two turnovers at `W=128`. S3.0 still needs its own
   `PLAN.md`, a matched turnover count, and a scientific report.

## Alternatives considered

- **Use `llama-3.2-1b-instruct` on OpenRouter.** Rejected: it is
  instruction-tuned. That is the confound S3.0 exists to isolate.
- **llama.cpp / GGUF.** Attractive on CPU. Rejected for the first
  implementation: one more tokeniser/quantisation surface. Can be added
  later as a second local backend without changing the client contract.
- **Default the smoke to Gemma 4 E2B.** Rejected on this machine: 10 GB
  weights plus runtime on 15 GB RAM, multimodal loader. The 1B-pt
  checkpoint is the S3.0-sized object.

## Consequences

- `GeneratorConfig.api` accepts `local`.
- `afterlife generate --config configs/stages/local_base_smoke.yaml`
  is the existence check.
- Every later claim can now say "a local pretrained Gemma 3 ran through
  P1" once S3.0 actually measures it — not on the strength of this smoke.
- Gemma 3 270M is below the 1–3B band. It validates the client. It does
  not close S3.0.

## Reversal cost

Low. If a hosted pretrained id appears, it is added as a generator
config (ADR-0006). The local client stays as the CPU control. Nothing
already collected on instruct models is invalidated.
