# Stage 0 — dashboard

**Status: CLOSED** 2026-08-30. Spend **$0.0128** of a $3 ceiling.

**Question.** Can this experiment be run reproducibly on this infrastructure, at
a cost that permits the full plan, and what are the *measured* facts about our
providers?

Plan: [`PLAN.md`](PLAN.md) · **Report: [`REPORT.md`](REPORT.md)** ·
Artifacts: [`artifacts/stage-0/`](../../../artifacts/stage-0/)

## Passes

| ID | Pass | Status | run_id |
| --- | --- | --- | --- |
| S0.0 | Repository, harness, library, CLI | done | — |
| S0.1 | Environment check (`afterlife doctor`) | done | — |
| S0.2 | Provider capability audit | done | `s0-audit-providers-20260830T072055Z-9787b3d3` |
| S0.3 | Continuation-mechanism audit | done | `s0-audit-continuation-20260830T072553Z-9787b3d3` |
| S0.3b | Reasoning-suppression audit *(added in response to S0.3)* | done | `s0-audit-reasoning-20260830T072812Z-9787b3d3` |
| S0.4 | Determinism audit, unpinned then pinned | done | `s0-audit-determinism-20260830T073948Z-ffb8e887`, `…074258Z-ffb8e887` |
| S0.5 | Embedding audit | done | `s0-audit-embeddings-20260830T073440Z-9dcb0ef0` |
| S0.6 | Tokenizer audit | done | `s0-audit-tokenizers-20260830T071933Z-9787b3d3` |
| S0.7a | Offline end-to-end micro-trajectory | done | `s0-smoke-…67a42230` → `s0-embed-smoke-…e99d7975` → `s0-geometry-mock-hash-…45f7e4b9` |
| S0.7b | Live end-to-end micro-trajectory | done | `s0-live-smoke-…a395a78c` → `s0-embed-live-smoke-…fc3e80ed` → `s0-geometry-bge-m3-…0589329e` |
| S0.8 | Bit-exact replay verification | done | `compare s0-live-smoke-…081709Z s0-live-smoke-…081713Z` → L3 confirmed |
| S0.9 | Cost calibration + S1 forecast | done | input error −0.6% after correction; S1 forecast $17.70 |

Three live trajectories were attempted; the first two failed at step 4 on a
throttled endpoint and are recorded as such rather than deleted.

## Headline results

- **No base models exist on RouterAI** (468 models, zero). The primary arm is
  dropped; the paper studies instruction-tuned models driven through a
  raw-completion interface. ([ADR-0006](../../decisions/ADR-0006-no-base-models-available.md))
- **`/completions` works on every model** although nothing advertises it, and
  adds 1–8 template tokens against 27–107 for chat.
- **Three of four models emit hidden reasoning tokens**, and
  `include_reasoning: false` is accepted while doing nothing (qwen3-8b still
  produced 508). Suppression is configured per model and the zero-reasoning
  invariant is asserted every step. ([ADR-0005](../../decisions/ADR-0005-reasoning-tokens-disqualify.md))
- **Provider pinning raised exact-match reproducibility from 20% to 100%** on two
  of three models. deepseek stays at 20% even pinned, so its claims must be
  distributional.
- **Throughput, not price, binds.** The cheapest endpoint throttles after ~4
  steps; the next one up completed the trajectory.
- **Cost model was 20.7% low on input** until block fill was measured (0.88
  mean, 0.04–1.00 range). Now −0.6%. The stride `S` is not constant.
- **Four of our own bugs found**, each of which would have produced confident
  wrong numbers: off-by-one token accounting, false pinning violations, retries
  that never fired on 429s wrapped in HTTP 200, and `difflib` autojunk corrupting
  similarity scores. All now covered by tests.

## Tooling added because Stage 0 demanded it

| Command / script | Why |
| --- | --- |
| `afterlife audit reasoning` | S0.3 found hidden reasoning tokens; seven suppression switches had to be tested per model |
| `afterlife compare A B` | file-hash comparison reports false failures on replay, since telemetry legitimately differs; this compares the scientific content |
| `scripts/probe_endpoints.py` | endpoint choice is empirical: a `status: 0` endpoint can still throttle |
| `scripts/probe_catalog.py` | answering "what *is* available" after the base-model discovery |
| `scripts/check_encoding.py` | a UTF-8 file edited under a legacy code page corrupted figure labels silently |
| `scripts/repair_mojibake.py` | reversing that corruption byte-exactly |

## Next

Stage 1 is open. Two prerequisites from the report before its matrix locks:

1. Audit OpenRouter for a base model — finding F1 may be RouterAI-specific, and
   an available base model would restore the cleanest arm outright.
2. Re-probe endpoints, since availability and throttling both drift.
