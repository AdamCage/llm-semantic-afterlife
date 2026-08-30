# ADR-0007: OpenRouter/DeepInfra as the primary path; Groq as a throughput arm; Llama replaces Mistral as the wide arm

Status: accepted
Date: 2026-08-30
Stage: S0 → S1
Supersedes the endpoint choices in ADR-0003 (which stands as to *why* we pin;
this changes *what* we pin to).

## Context

Stage 0 selected RouterAI's `io-net` endpoint for mistral-nemo because it was the
only configuration that completed a trajectory. Once the OpenRouter key arrived,
every candidate was re-measured with the *same* multi-step trajectory — because
S0's finding F8 established that single-call probes do not predict in-trajectory
behaviour. Full table in
[`stages/stage-0/ENDPOINT-SELECTION.md`](../stages/stage-0/ENDPOINT-SELECTION.md).

The measurement that decided it:

| Endpoint | Model | Quant. | Latency | h/trajectory | Block fill (mean/min) | Stop rate | Prompt-token delta | USD/M in·out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `deepinfra/fp8` | llama-3.1-8b-instruct | fp8 | 18.2 s | 1.29 | **1.000 / 1.000** | **0.000** | **0** | **0.020 · 0.040** |
| `groq` | llama-3.1-8b-instruct | unknown | **0.87 s** | **0.06** | 0.932 / 0.607 | 0.278 | 35 | 0.050 · 0.080 |
| RouterAI `io-net` | mistral-nemo-12b | fp16 | 14.5 s | 1.03 | 0.877 / 0.045 | 0.263 | 3 | 0.061 · 0.223 |
| OpenRouter `io-net/fp16` | mistral-nemo-12b | fp16 | 33.6 s | 2.39 | 0.758 / 0.064 | 0.478 | 3 | 0.044 · 0.160 |

Three properties of `deepinfra/fp8` are not merely better numbers but remove a
stated limitation:

- **Block fill 1.000 with minimum 1.000 and stop rate 0.000** means the stride is
  exactly `S = B`. Methodology §0.1 — that `S` is model-determined within
  `[0, B]` and only its distribution can be reported — does not apply here. A
  constant stride restores the clean cost law, exact step/chunk alignment, and
  every claim that assumed a fixed stride.
- **Prompt-token delta 0** means no server-side template is added to what we
  send. The window is exactly the window. For a paper about *unforced*
  continuation this is a provenance property, not a convenience.
- **Known fp8 quantization**, and the cheapest endpoint on either provider.

Against that, `groq` is 21× faster — the difference between a 4-minute and a
78-minute trajectory, and therefore between a feasible and an infeasible Stage 4
(temperature × `W` sweep) or Stage 5 (200+ seeds per model) on this hardware. But
it prepends 35 constant tokens of unseen scaffolding to a nominally raw
completion, reports quantization as `unknown`, and restores a 0.278 stop rate.

Separately, the reasoning audit was repeated against OpenRouter and reproduced
the ADR-0005 trap on a second provider: `include_reasoning: false` is accepted by
qwen3-8b and still leaves 575 reasoning tokens. `reasoning_effort: none` is the
only switch that suppresses generation on *both* providers. Llama-3.1-8b emits
zero reasoning tokens under every configuration on both endpoints.

## Decision

1. **`deepinfra/fp8` llama-3.1-8b-instruct is the primary generator for Stages
   1–3**, where per-trajectory cleanliness decides what the paper may claim.
2. **`groq` llama-3.1-8b-instruct is a high-throughput arm for Stages 4–5**,
   where trajectory count matters more than per-trajectory purity. Its 35-token
   scaffolding and unknown quantization are stated wherever its data appear, and
   an overlapping configuration is run on both endpoints as a consistency check.
   Groq data are never pooled with DeepInfra data without that check.
3. **Llama-3.1-8b-instruct becomes the wide arm, replacing mistral-nemo.** It is
   cheaper, cleaner, faster, and adds the Llama family that ADR-0006 removed when
   the base model proved unavailable.
4. **qwen3-8b (Alibaba, OpenRouter) remains the replication arm**, with
   `reasoning_effort: none` and the per-step guard.
5. **Mistral-nemo is retained but demoted** to a Stage 6 cross-family and
   cross-provider replication generator. Its RouterAI `io-net` pin stays
   configured, which also keeps RouterAI as the second provider for S6.
6. `S = B` is treated as constant **only for endpoints measured to have block
   fill 1.000**, and that measurement is repeated per stage rather than assumed
   to persist.

## Alternatives considered

- **Groq everywhere.** 21× faster and the whole programme finishes in an
  afternoon. Rejected as primary: 35 tokens of unseen server-side text in a study
  whose central claim is unforced continuation is a weakness a reviewer would be
  right to press, and `unknown` quantization compounds it. Kept where its
  strength is decisive and its weakness tolerable.
- **Stay on RouterAI/mistral (the Stage 0 choice).** Costs 4× more, runs slower,
  has a worse block fill (min 0.045 — near-total collapse on some steps) and a
  higher stop rate. Retained only for S6 replication.
- **`parasail/fp8`, the cheapest endpoint of all.** Throttles through both
  routers (12 steps via OpenRouter after ten retries, ~4 via RouterAI), so the
  upstream pool, not the aggregator, is the constraint. Unusable at any price.
- **Keep mistral as the wide arm and add llama as a third family.** Better for
  H1, but the pilot's job is to establish that the effect exists; a third family
  belongs in Stage 4 once it does.

## Consequences

- Stage 1 forecast falls from $9.68 to roughly $2.5 for the 48-trajectory core
  arm, and the whole pilot to about $5.
- Wall clock for the core arm is ~62 h sequential, ~31 h at concurrency 2. That
  is the real cost of choosing provenance over speed, and it is accepted
  deliberately.
- Because block fill is 1.000, Stage 1 can report a *constant* stride and does
  not need the variable-stride caveat — but it must verify that the measurement
  holds at `W = 8192`, since it was taken at `W = 2048`.
- The paper gains a methodological warning worth stating: a provider parameter
  named `include_reasoning` can be accepted and still not prevent reasoning. That
  now has two-provider evidence.

## Reversal cost

Low. Both endpoints are configured; switching the primary is a one-line change in
the stage config. Data already collected under one endpoint would not be pooled
with the other without the consistency check that point 2 requires anyway.
