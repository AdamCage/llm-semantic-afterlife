# Stage 9 — Does post-training change Qwen3-8B late-regime persistence at 12W?

**Status.** Opened 2026-09-11 after Stage 8 REPORT declared the local
P1 path fit for Qwen and the human authorised 12W generate. Decisions:
[ADR-0023](../../decisions/ADR-0023-paper-b-local-four-family.md),
[ADR-0024](../../decisions/ADR-0024-local-nf4-lifecycle.md),
[ADR-0025](../../decisions/ADR-0025-persistence-metrics-and-horizon-ladder.md),
[ADR-0026](../../decisions/ADR-0026-seed-bank-v1-rationale-not-identification.md).

If PLAN prose and YAML disagree, **YAML wins**. One local generator
per `afterlife generate` (ADR-0024). The expansion file with two
slugs is documentation only — `plan_trajectories` rejects two CUDA
models in one run.

This stage does **not** start S10. It does **not** use hosted
`or-qwen3-8b` as the Instruct cell. It does **not** call a lock
absorbing. Confirmatory order is frozen: \(G_t\) → \(\tau_{\mathrm{lock}}\)
→ fingerprint agreement.

## 1. Question

On local Qwen3-8B Base vs Instruct, under P1 `raw_completion`,
`serialization: raw_bytes`, `W=4096`, `B=1024`, T=0.3, 12 turnovers:
does seed-conditioned late-regime persistence (\(G_t\), time-to-confirmed-lock,
fingerprint agreement) differ between the pretrained checkpoint and
its instruction-tuned pair?

A Base≈Instruct outcome supports an autoregressive-dynamics reading.
A Base≪Instruct outcome supports post-training reshaping the
long-run regime. Either is a successful stage.

This stage does **not** ask whether H1 holds. It does **not** treat
a lock as a semantic state. It does **not** pool Qwen with OLMo.

## 2. Entry state

From [Stage 8 REPORT](../stage-8/REPORT.md) and [SMOKE.md](../stage-8/SMOKE.md):

- Ten NF4 checkpoints load; Qwen Instruct completed 2 turnovers at
  the S9 window (`W=4096`, `B=1024`, fill 1.0, think 0).
  `run_id`: `s8-paperb-micro-qwen3-8b-instruct-20260910T221623Z-61c9ad74`.
- Exclusive-GPU estimate: **0.550 h / 12W traj** ⇒ **~44 h** for 80
  NF4 trajectories. Base tok/s was not logged on smoke; re-time on
  the first Base 12W run.
- Hosted OpenRouter Qwen is **not** a matched Instruct cell
  (ADR-0023). Paper A 19/20 lock is a prior, not this matrix.
- F1 degeneracy thresholds and `N_confirm=3` are locked.
- F2 INT8 seeds locked: `physics, biology, love, programming, surreal`
  × `s1,s2`.
- Native-chat generate is **deferred**: `build_request` still
  short-circuits `continuation=raw_completion` to a raw prompt, so
  `serialization: native_chat` would silently be `raw_bytes`. YAML
  for that arm exists; it is not executed until the branch is
  independent.
- Twins stay out of the domain \(G_t\).
- Ledger: local generate **$0**. Project ceiling $200 unchanged.

## 3. Experiment matrix

Authoritative files under
[`configs/stages/stage9_qwen/`](../../../configs/stages/stage9_qwen/).
Shared knobs: [`_base.yaml`](../../../configs/stages/stage9_qwen/_base.yaml).

| # | Pass | Config | Trajectories | Output tokens (fill=1) |
| --- | --- | --- | ---: | ---: |
| S9.1 | Instruct NF4 `raw_bytes` | `pb-qwen3-8b-instruct.yaml` | 40 | 1,966,080 |
| S9.2 | Base NF4 `raw_bytes` | `pb-qwen3-8b-base.yaml` | 40 | 1,966,080 |
| S9.3 | Instruct INT8 F2 | `pb-qwen3-8b-instruct-int8.yaml` | 10 | 491,520 |
| S9.4 | Base INT8 F2 | `pb-qwen3-8b-base-int8.yaml` | 10 | 491,520 |
| S9.5 | Native-chat reduced | `pb-qwen3-8b-*-native.yaml` | 8 | deferred |

| knob | value |
| --- | --- |
| checkpoints | `Qwen/Qwen3-8B-Base`, `Qwen/Qwen3-8B` (local NF4 / INT8 twins) |
| `W` / `B` / `T` | 4096 / 1024 / 49152 (12 turnovers) |
| `chunk_size` | 1024 |
| protocol | `P1_reprompt` (`raw_completion`, unforced) |
| temperature / `top_p` | 0.3 / 1.0 |
| domain seeds | `physics, finance, biology, war, love, recipe, programming, philosophy, surreal, noise` |
| stochastic | `{1,2,3,4}` |
| embeddings (after unload) | `local-bge-m3` (local); `qwen3-embed-8b` hosted RouterAI, OpenRouter fallback ([ADR-0027](../../decisions/ADR-0027-s9-hosted-qwen-embed.md)) |
| `max_concurrent` | 1 |
| `budget_usd` | 0.0 |

Not in this opening: OLMo, Ministral, Gemma, L1 48W, L2 5M, Gemini
embed, P2, think-arm, twins in \(G_t\), hosted Instruct.

## 4. Computations

Ordered. Degeneracy before geometry. One GPU process.

1. `afterlife generate` S9.1 then S9.2 then S9.3 then S9.4
   (`scripts/s9_run_matrix.sh`). Resume with `--resume-run` only.
2. `python scripts/summarise_run.py <run_id>` per generate: block
   fill, stop rate, round-trip, reasoning=0, served provider `local`.
3. `afterlife embed` on each completed generate: local BGE-M3, then
   hosted `qwen3-embed-8b` (ADR-0027). Generator already unloaded.
4. `afterlife analyze degeneracy` before any \(G_t\).
5. Persistence / separation: \(G_t\) (seed-cluster bootstrap, LOO),
   prefix \(\tau_{\mathrm{lock}}\) (`N_confirm=3`), fingerprint
   agreement. No Greenwood on 40 iid traj. No headline MI.
6. INT8 vs NF4 on the five F2 seeds: same-sign last-band \(G_t\)
   check (limitations, not a third headline).
7. Score this PLAN’s predictions in `REPORT.md`. Do not start S10.

## 5. Exit criteria

Written before 12W data.

| # | Criterion | Threshold |
| --- | --- | --- |
| E1 | NF4 `raw_bytes` complete | 80/80 trajectories `STATUS=COMPLETED` at `target_tokens=49152`, or missing cells named with a reason |
| E2 | INT8 F2 complete | 20/20 completed, or PARTIAL with a recorded OOM / loader reason (no silent drop) |
| E3 | Native-chat | executed only after `build_request` distinguishes `native_chat` from `raw_completion`; otherwise **deferred** (not a silent `raw_bytes` rerun) |
| E4 | Degeneracy first | no \(G_t\) / lock table published from a run that skipped `analyze degeneracy` |
| E5 | \(G_t\) both spaces | last-band \(G_t\) + seed-cluster interval + LOO-by-seed in local BGE-M3 and hosted `qwen3-embed-8b`, NF4 `raw_bytes` only |
| E6 | Lock construct | F1 thresholds + `N_confirm=3` unchanged; hash is diagnostic only; language is *long-lived repetition lock* |
| E7 | No hosted Instruct | every S9 generate step `served_provider=local`; no `or-qwen3-8b` cell |
| E8 | Protocol | thinking tokens = 0 on completed steps; tokenizer round-trip failures named; fill and stop reported |
| E9 | One GPU | no two `afterlife generate` coresident |
| E10 | Spend | generate + local BGE **$0.00**; hosted Qwen-embed may increment the ledger, **cap $5** (ADR-0027) |

## 6. Pre-registered predictions

Empty `observed` is filled by the report.

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | Instruct NF4: ≥8/10 domain seeds have ≥1 confirmed lock (`N_confirm=3`) by 12W | 0.55 | |
| P2 | Base NF4 seed-level lock rate (seeds with ≥1 lock) is **lower** than Instruct | 0.60 | |
| P3 | Instruct last-band \(G_t > 0\) in **both** spaces (local BGE-M3 and hosted Qwen-embed) | 0.50 | |
| P4 | Sign of Instruct last-band \(G_t\) **agrees** across BGE-M3 and Qwen-embed | 0.55 | |
| P5 | Thinking tokens remain 0 on all completed NF4 steps | 0.80 | |
| P6 | Mean block fill on NF4 12W ≥ 0.95 (same `W`/`B` as the microbench) | 0.70 | |
| P7 | INT8 vs NF4, Instruct, five F2 seeds: **same sign** of last-band \(G_t\) (not a 0.01 numeric match) | 0.45 | |
| P8 | If Base≈Instruct on both lock rate and last-band \(G_t\) sign, that is a finding (autoregressive dynamics), not a failed contrast | — | |

P1 is deliberately below Paper A’s 10/10 / 19/20: different stack,
NF4, four descendants not two.

## 7. Budget and wall-clock

- **API / ledger:** generate + local BGE **$0**. Hosted Qwen-embed
  (ADR-0027) `budget_usd: 5.0`. Stop and ask before Gemini or before
  raising that $5 ceiling.
- **Wall-clock (measured Instruct microbench):** 80 × 0.550 h ≈
  **44 h** NF4 exclusive GPU. INT8 20 traj ≈ **11 h** if tok/s
  matches; re-measure. Native-chat deferred.
- **Stop-and-ask:** hosted $; INT8 OOM; thinking-storm; raising `T`
  above 12W; starting S10; changing F1; second GPU generate;
  swapping in OpenRouter Qwen as a *generator*.

## 8. Risks specific to this stage

| Risk | Mitigation |
| --- | --- |
| Two agents on one GPU | one orchestrator; check `nvidia-smi` before each generate |
| Treating Paper A 19/20 as this Instruct cell | E7; local slug only |
| Reading lock as absorbing | E6 language |
| 40 traj as iid Bernoulli | seed-cluster bootstrap (ADR-0025) |
| Native-chat silently equals raw_bytes | E3; do not generate yet |
| INT8 OOM at `W=4096` | stop that arm; record; do not cut `B` |
| Tuning sampling after seeing loops | degeneracy is data (F1) |
| Starting S10 from a red 12W protocol | S10 waits on this REPORT |
