# Stage 10 — Does the OLMo 3 7B post-training ladder change 12W persistence?

**Status.** Opened 2026-09-16 after Stage 9 `--no-ff` close. Decisions:
[ADR-0023](../../decisions/ADR-0023-paper-b-local-four-family.md),
[ADR-0024](../../decisions/ADR-0024-local-nf4-lifecycle.md),
[ADR-0025](../../decisions/ADR-0025-persistence-metrics-and-horizon-ladder.md),
[ADR-0026](../../decisions/ADR-0026-seed-bank-v1-rationale-not-identification.md),
[ADR-0028](../../decisions/ADR-0028-s10-hosted-qwen-embed.md).

If PLAN prose and YAML disagree, **YAML wins**. One local generator
per `afterlife generate` (ADR-0024).

This stage does **not** start S11. It does **not** pool OLMo with
Qwen. It does **not** call a lock absorbing. It does **not** treat
last-band \(G_t>0\) as recovered semantics. Confirmatory order:
\(G_t\) → \(\tau_{\mathrm{lock}}\). Fingerprint agreement remains
confirmatory #3 in ADR-0023 F4 and is **not** an S10 exit criterion
(same allowed E6 choice as S9: hash is diagnostic only).

## 1. Question

On the local OLMo 3 7B Instruct line (Base → SFT → DPO → RLVR),
under P1 `raw_completion`, `serialization: raw_bytes`, `W=4096`,
`B=1024`, T=0.3, 12 turnovers: do seed-conditioned completer
persistence (\(G_t\), time-to-confirmed-lock) and completion under
this continuation mechanism differ across adjacent ladder edges?

Two estimands, both confirmatory for the stage (S9 REVIEW):

1. **Persistence among completers.** Last-band \(G_t\) and prefix
   lock on trajectories that reach \(T=49152\).
2. **Completion.** Empty-completion deaths kept in the sample; not
   unlocks. Selecting on completers is part of the result.

A flat ladder on completers (same last-band sign, saturated locks)
is a finding: this post-training line does not reshape the
early-onset repetition lock on this stack. A sign flip or
unsaturated lock on one adjacent edge is also a finding. Either
is a successful stage.

This stage does **not** ask whether H1 holds. It does **not** treat
a lock as a semantic state. Last-band \(G_t>0\) is seed-conditioned
separation of late registers / loop families. The lock, if it
appears, is an early-onset long-lived repetition lock that may
persist through 12W — not a “late lock.”

## 2. Entry state

From [Stage 9 REPORT](../stage-9/REPORT.md) and
[Stage 8 SMOKE](../stage-8/SMOKE.md):

- S9 Qwen completers were Base≈Instruct: lock at
  \(\tau\in\{0.75,1.00\}\), escape 0/86, last-band \(G_t>0\) in both
  spaces as register / loop-family separation. Completion was worse
  on Base (9/40 vs 2/40; `recipe` 0/4). That is **one family**, not
  a law. S10 is the first place a post-training *ladder* can appear.
- OLMo Base exclusive microbench: median 26.388 tok/s, **0.517 h /
  12W traj**, peak VRAM 7206 MiB.
  `run_id`: `s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f`.
  SFT / DPO / RLVR 12W hours are not measured; re-time on each
  first 12W run.
- Hybrid attention (`sliding_window=4096`) at imposed `W=4096` is
  **not** an architecture contrast.
- Think line (`Olmo-3-7B-Think*`) is parked.
- F1 thresholds and `N_confirm=3` stay frozen.
- F2 INT8 seeds stay
  `physics, biology, love, programming, surreal` × `s1,s2`.
  On this four-rung ladder INT8 is the **two ends** (Base, RLVR) =
  20 traj, not 40.
- Native-chat generate is **deferred** (`build_request` still raw).
- Twins stay out of domain \(G_t\).
- Ledger: local generate **$0**. Hosted Qwen-embed cap $5 (ADR-0028).
  Project ceiling $200 unchanged.

## 3. Experiment matrix

Authoritative files under
[`configs/stages/stage10_olmo/`](../../../configs/stages/stage10_olmo/).
Shared knobs: [`_base.yaml`](../../../configs/stages/stage10_olmo/_base.yaml).

| # | Pass | Config | Trajectories | Output tokens (fill=1) |
| --- | --- | --- | ---: | ---: |
| S10.1 | Base NF4 `raw_bytes` | `pb-olmo3-7b-base.yaml` | 40 | 1,966,080 |
| S10.2 | SFT NF4 `raw_bytes` | `pb-olmo3-7b-sft.yaml` | 40 | 1,966,080 |
| S10.3 | DPO NF4 `raw_bytes` | `pb-olmo3-7b-dpo.yaml` | 40 | 1,966,080 |
| S10.4 | RLVR NF4 `raw_bytes` | `pb-olmo3-7b-rlvr.yaml` | 40 | 1,966,080 |
| S10.5 | Base INT8 F2 | `pb-olmo3-7b-base-int8.yaml` | 10 | 491,520 |
| S10.6 | RLVR INT8 F2 | `pb-olmo3-7b-rlvr-int8.yaml` | 10 | 491,520 |
| S10.7 | Native-chat | — | 0 | **deferred** |

| knob | value |
| --- | --- |
| checkpoints | `allenai/Olmo-3-1025-7B`, `…-Instruct-SFT`, `…-Instruct-DPO`, `…-Instruct` (RLVR) |
| `W` / `B` / `T` | 4096 / 1024 / 49152 (12 turnovers) |
| `chunk_size` | 1024 |
| protocol | `P1_reprompt` (`raw_completion`, unforced) |
| temperature / `top_p` | 0.3 / 1.0 |
| domain seeds | ten `seed_bank_v1` domains (twins out) |
| stochastic | `{1,2,3,4}` NF4; `{1,2}` INT8 |
| embeddings | `local-bge-m3`; hosted `qwen3-embed-8b` (ADR-0028) |
| `max_concurrent` | 1 |
| `budget_usd` | 0.0 generate; 5.0 hosted embed |

Not in this opening: Qwen, Ministral, Gemma, L1 48W, L2 5M, Gemini
embed, P2, Think-line, twins in \(G_t\), SFT/DPO INT8, hosted
generate.

## 4. Computations

Ordered. Degeneracy before geometry. One GPU process.

1. `afterlife generate` S10.1 → S10.2 → S10.3 → S10.4 → S10.5 →
   S10.6 (`scripts/s10_run_matrix.sh`). Resume with `--resume-run`
   only. Check `nvidia-smi` before each pass.
2. `python scripts/summarise_run.py <run_id>` per generate: block
   fill, stop rate, round-trip, reasoning=0, served provider `local`.
   Report fill and stop **by quarter**.
3. `afterlife embed` on each completed generate: local BGE-M3, then
   hosted `qwen3-embed-8b` (ADR-0028). Generator already unloaded.
4. `afterlife analyze degeneracy` before any \(G_t\).
5. Persistence: \(G_t\) (seed-cluster bootstrap, LOO), prefix
   \(\tau_{\mathrm{lock}}\) (`N_confirm=3`). No Greenwood on 40 iid
   traj. No headline MI. No fingerprint headline table.
6. Adjacent-edge table (Base–SFT, SFT–DPO, DPO–RLVR) on last-band
   \(G_t\) sign and completer lock saturation. Not a monotone-ladder
   test.
7. INT8 vs NF4 on Base and RLVR, five F2 seeds: same-sign last-band
   \(G_t\) (limitations, not a third headline).
8. Score this PLAN’s predictions in `REPORT.md`. Name both
   estimands in the lede. Do not start S11.

## 5. Exit criteria

Written before 12W data.

| # | Criterion | Threshold |
| --- | --- | --- |
| E1 | NF4 `raw_bytes` complete | 160/160 trajectories `STATUS=COMPLETED` at `target_tokens=49152`, or missing cells named with a reason |
| E2 | INT8 F2 complete | 20/20 completed, or PARTIAL with a recorded OOM / loader reason (no silent drop) |
| E3 | Native-chat | **deferred** (not a silent `raw_bytes` rerun) |
| E4 | Degeneracy first | no \(G_t\) / lock table published from a run that skipped `analyze degeneracy` |
| E5 | \(G_t\) both spaces | last-band \(G_t\) + seed-cluster interval + LOO-by-seed in local BGE-M3 and hosted `qwen3-embed-8b`, NF4 `raw_bytes` only, all four rungs |
| E6 | Lock construct | F1 + `N_confirm=3` unchanged; hash diagnostic only; language is *long-lived repetition lock*; not “late lock”; not absorbing |
| E7 | Local generate | every S10 generate step `served_provider=local`; no hosted OLMo cell |
| E8 | Protocol | thinking tokens = 0 on completed steps; tokenizer round-trip failures named; fill and stop by quarter |
| E9 | One GPU | no two `afterlife generate` coresident |
| E10 | Spend | generate + local BGE **$0.00**; hosted Qwen-embed **cap $5** (ADR-0028) |
| E11 | Not pooled | no table or sentence averages OLMo with S9 Qwen |

## 6. Pre-registered predictions

Empty `observed` is filled by the report.

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | RLVR NF4: ≥8/10 domain seeds have ≥1 confirmed lock (`N_confirm=3`) by 12W | 0.50 | |
| P2 | Base NF4 empty-completion rate is **higher** than RLVR (second estimand) | 0.55 | |
| P3 | RLVR last-band \(G_t > 0\) in **both** spaces | 0.50 | |
| P4 | Sign of RLVR last-band \(G_t\) **agrees** across BGE-M3 and Qwen-embed | 0.55 | |
| P5 | Thinking tokens remain 0 on all completed NF4 steps | 0.80 | |
| P6 | Mean block fill on completed NF4 12W steps ≥ 0.95 (final-quarter, not Q1 deaths) | 0.65 | |
| P7 | INT8 vs NF4, Base and RLVR, F2 seeds: **same sign** of last-band \(G_t\) | 0.45 | |
| P8 | If all four rungs share last-band \(G_t\) sign and completer locks saturate, that is a finding (this line does not reshape the lock), not a failed contrast | — | |
| P9 | No adjacent-edge last-band \(G_t\) **sign flip** (S9 prior; a flip is the mechanistic result) | 0.45 | |
| P10 | Base `recipe`: ≥2/4 descendants empty-completion FAILED | 0.50 | |

P8 and P9 can both be true. A sign flip falsifies P9 and is still a
successful stage.

## 7. Budget and wall-clock

`afterlife estimate` on the six generate YAMLs (2026-09-16, fill=1,
`AFTERLIFE_BUDGET_USD_TOTAL=200`):

| pass | traj | input tok | output tok | USD |
| --- | ---: | ---: | ---: | ---: |
| S10.1 Base NF4 | 40 | 7,454,720 | 1,966,080 | 0.00 |
| S10.2 SFT NF4 | 40 | 7,454,720 | 1,966,080 | 0.00 |
| S10.3 DPO NF4 | 40 | 7,454,720 | 1,966,080 | 0.00 |
| S10.4 RLVR NF4 | 40 | 7,454,720 | 1,966,080 | 0.00 |
| S10.5 Base INT8 | 10 | 1,863,680 | 491,520 | 0.00 |
| S10.6 RLVR INT8 | 10 | 1,863,680 | 491,520 | 0.00 |
| **generate total** | **180** | **33,546,240** | **8,847,360** | **0.00** |

The CLI prints `stage budget not declared` because YAML
`budget_usd: 0.0` is falsy in the formatter. The generate ceiling
is **$0** by construction. Project remaining at kickoff:
**$189.46 / $200**. Hosted Qwen-embed (ADR-0028) is **not** in this
forecast; cap **$5**. Stop and ask before Gemini or before raising
that ceiling.

- **Wall-clock (OLMo Base microbench
  `s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f`):**
  0.517 h / 12W traj. NF4 160 × 0.517 ≈ **83 h**. INT8 20 × 0.517 ≈
  **10 h** if tok/s matches. Re-time SFT/DPO/RLVR on the first 12W
  run of each. Native-chat deferred. Exclusive-GPU sketch
  **~93 h**. Peak VRAM on that microbench: 7206 MiB.
- **Stop-and-ask:** hosted $; INT8 OOM; thinking-storm; raising `T`
  above 12W; starting S11; changing F1; second GPU generate; mixing
  Think-line ids; pooling with Qwen; cutting `B`.

## 8. Risks specific to this stage

| Risk | Mitigation |
| --- | --- |
| Two agents on one GPU | one orchestrator; refuse if `nvidia-smi` shows compute |
| Reading S9 Base≈Instruct as this ladder | E11; do not pool |
| Calling the lock late / absorbing | E6 language from S9 REVIEW |
| 40 traj as iid Bernoulli | seed-cluster bootstrap (ADR-0025) |
| Completer-only headline | two estimands in lede and P2 |
| Native-chat silently equals raw_bytes | E3; no native YAML in this tree |
| INT8 OOM at `W=4096` | stop that arm; record; do not cut `B` |
| Tuning sampling after seeing loops | degeneracy is data (F1) |
| Think checkpoint by typo | slug is `pb-olmo3-7b-rlvr` = `Olmo-3-7B-Instruct` |
