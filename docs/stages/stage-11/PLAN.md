# Stage 11 — Does Ministral replicate the Qwen 12W pair, and does Gemma generalize?

**Status.** Opened 2026-09-19 after Stage 10 `--no-ff` close.
Decisions:
[ADR-0023](../../decisions/ADR-0023-paper-b-local-four-family.md),
[ADR-0024](../../decisions/ADR-0024-local-nf4-lifecycle.md),
[ADR-0025](../../decisions/ADR-0025-persistence-metrics-and-horizon-ladder.md),
[ADR-0026](../../decisions/ADR-0026-seed-bank-v1-rationale-not-identification.md),
[ADR-0029](../../decisions/ADR-0029-s11-hosted-qwen-embed.md).

If PLAN prose and YAML disagree, **YAML wins**. One local generator
per `afterlife generate` (ADR-0024).

This stage does **not** start S12. It does **not** pool Ministral or
Gemma with S9 Qwen or S10 OLMo. It does **not** call a lock absorbing.
It does **not** treat last-band \(G_t>0\) as recovered semantics.
Gemma is architectural **generalization**, not a causal attention
ablation. Confirmatory order: \(G_t\) → \(\tau_{\mathrm{lock}}\).
Fingerprint agreement remains confirmatory #3 in ADR-0023 F4 and is
**not** an S11 exit criterion (same allowed choice as S9/S10).

## 1. Question

On local Ministral 3 8B Base vs Instruct and local Gemma 4 12B Base
vs IT, under P1 `raw_completion`, `serialization: raw_bytes`,
`W=4096`, `B=1024`, T=0.3, 12 turnovers: (i) does the Ministral pair
replicate the *sign* of the S9 Qwen completer contrast, and
(ii) does a last-band seed-conditioned gap appear on Gemma 4 12B
(hybrid sliding / full attention) at all?

Two estimands, both confirmatory for the stage (S9/S10 REVIEW):

1. **Persistence among completers.** Last-band \(G_t\) and prefix
   lock on trajectories that reach \(T=49152\). Lock-table \(n\)
   (`min_chunks=8`) is not identical to completer \(n\) and is not
   last-band \(n\).
2. **Completion.** Empty-completion deaths kept in the sample; not
   unlocks. Selecting on completers is part of the result.

A Ministral Base≈Instruct completer reading (same last-band sign,
saturated locks) is a finding: this matched pair does not reshape
the early-onset repetition lock on this stack. A sign disagreement
with Qwen Instruct is also a finding — stop family-level
generalization; do not average. Either is a successful stage.

If Gemma last-band \(G_t\) CI excludes 0 in both spaces: *full
attention on every layer is not a necessary condition* for
persistence in this P1 protocol. If Gemma has no identified
last-band: *did not replicate in the Gemma condition*. Those two
sentences are not interchangeable, and neither is a causal claim
about `sliding_window=1024`.

This stage does **not** ask whether H1 holds. It does **not** treat
a lock as a semantic state. Last-band \(G_t>0\) is seed-conditioned
separation of late registers / loop families.

## 2. Entry state

From [Stage 10 REPORT](../stage-10/REPORT.md),
[Stage 9 REPORT](../stage-9/REPORT.md), and
[Stage 8 SMOKE](../stage-8/SMOKE.md):

- S9 Qwen completers were Base≈Instruct: lock at
  \(\tau\in\{0.75,1.00\}\), escape 0, last-band \(G_t>0\) in both
  spaces as register / loop-family separation. Completion was worse
  on Base (9/40 vs 2/40). That is **one family**.
- S10 OLMo inverted the completion estimand: empty-completion
  deaths rose Base→DPO and floored at DPO≈RLVR (13/40 → 21/40 →
  37/40 → 36/40). Completer locks that existed saturated; escape 0.
  RLVR last-band \(G_t>0\) was **not established** (CI includes 0;
  LOO skipped). DPO last-band was unidentified, not a flip. Do not
  pool with Qwen.
- Empty-completion attrition travels and can invert. S11 keeps
  FAILED empty cells and does not retune sampling.
- Ministral Instruct exclusive microbench: median 28.749 tok/s,
  **0.475 h / 12W traj**, peak VRAM 6941 MiB.
  `run_id`: `s8-paperb-micro-ministral-8b-instruct-20260910T233421Z-e528749b`.
  Ministral Base 12W hours are not measured; re-time on the first
  12W run.
- Gemma IT microbench at `W=4096` **FAILED** (5 consecutive empty
  completions, 222 tokens, not OOM, peak 7700.9 MiB).
  `run_id`: `s8-paperb-micro-gemma4-12b-it-20260910T233125Z-f89a95a4`.
  Family skipped for wall-clock. Smoke at `W=32` loaded both Gemma
  checkpoints (peak 7381.7 MiB). OOM → stop; no E4B / `B` cut.
- F1 thresholds and `N_confirm=3` stay frozen.
- INT8 F2 is **not** in this opening (Qwen and OLMo ends only).
- Native-chat generate is **deferred** (`build_request` still raw
  when `continuation=raw_completion`). No native YAML in this tree.
- Twins stay out of domain \(G_t\).
- Ledger: local generate **$0**. Hosted Qwen-embed cap $5
  (ADR-0029). Project ceiling $200 unchanged. Remaining at kickoff:
  **$189.46 / $200**.

## 3. Experiment matrix

Authoritative files under
[`configs/stages/stage11_ministral_gemma/`](../../../configs/stages/stage11_ministral_gemma/).
Shared knobs: [`_base.yaml`](../../../configs/stages/stage11_ministral_gemma/_base.yaml).

| # | Pass | Config | Trajectories | Output tokens (fill=1) |
| --- | --- | --- | ---: | ---: |
| S11.1 | Ministral Base NF4 `raw_bytes` | `pb-ministral-8b-base.yaml` | 40 | 1,966,080 |
| S11.2 | Ministral Instruct NF4 `raw_bytes` | `pb-ministral-8b-instruct.yaml` | 40 | 1,966,080 |
| S11.3 | Gemma 4 12B Base NF4 `raw_bytes` | `pb-gemma4-12b-base.yaml` | 40 | 1,966,080 |
| S11.4 | Gemma 4 12B IT NF4 `raw_bytes` | `pb-gemma4-12b-it.yaml` | 40 | 1,966,080 |
| S11.5 | Native-chat | — | 0 | **deferred** |

| knob | value |
| --- | --- |
| checkpoints | `mistralai/Ministral-3-8B-Base-2512`, `…-Instruct-2512-BF16`, `google/gemma-4-12B`, `google/gemma-4-12B-it` |
| `W` / `B` / `T` | 4096 / 1024 / 49152 (12 turnovers) |
| `chunk_size` | 1024 |
| protocol | `P1_reprompt` (`raw_completion`, unforced) |
| temperature / `top_p` | 0.3 / 1.0 |
| domain seeds | ten `seed_bank_v1` domains (twins out) |
| stochastic | `{1,2,3,4}` |
| embeddings | `local-bge-m3`; hosted `qwen3-embed-8b` (ADR-0029) |
| `max_concurrent` | 1 |
| `budget_usd` | 0.0 generate; 5.0 hosted embed |

Not in this opening: Qwen, OLMo, INT8, L1 48W, L2 5M, Gemini embed,
P2, Ministral Reasoning-2512, FP8 Instruct, Gemma E4B, twins in
\(G_t\), hosted generate, native-chat.

## 4. Computations

Ordered. Degeneracy before geometry. One GPU process.

1. `afterlife generate` S11.1 → S11.2 → S11.3 → S11.4
   (`scripts/s11_run_matrix.sh`). Resume with `--resume-run` only.
   Check `nvidia-smi` before each pass. Gemma last. Gemma OOM on a
   pass stops that family; do not start the other Gemma slug after
   an OOM; do not swap E4B or cut `B`.
2. `python scripts/summarise_run.py <run_id>` per generate: block
   fill, stop rate, round-trip, reasoning=0, served provider `local`.
   Report fill and stop **by quarter**.
3. `afterlife embed` on each completed generate: local BGE-M3, then
   hosted `qwen3-embed-8b` (ADR-0029). Generator already unloaded.
4. `afterlife analyze degeneracy` before any \(G_t\).
5. Persistence: \(G_t\) (seed-cluster bootstrap, LOO), prefix
   \(\tau_{\mathrm{lock}}\) (`N_confirm=3`). No Greenwood on 40 iid
   traj. No headline MI. No fingerprint headline table.
6. Ministral Base vs Instruct last-band sign table, both spaces.
   Record whether the Instruct sign agrees with S9 Qwen Instruct.
   Do not average magnitudes across families.
7. Gemma last-band: identified vs unidentified vs no completers.
   Language from §1 only.
8. Score this PLAN’s predictions in `REPORT.md`. Name both
   estimands in the lede. Do not start S12.

## 5. Exit criteria

Written before 12W data.

| # | Criterion | Threshold |
| --- | --- | --- |
| E1 | Ministral NF4 `raw_bytes` complete | 80/80 trajectories `STATUS=COMPLETED` at `target_tokens=49152`, or missing cells named with a reason |
| E2 | Gemma NF4 `raw_bytes` complete | 80/80 completed, or PARTIAL with a recorded empty-completion / OOM / loader reason (no silent drop, no E4B swap) |
| E3 | Native-chat | **deferred** (not a silent `raw_bytes` rerun) |
| E4 | Degeneracy first | no \(G_t\) / lock table published from a run that skipped `analyze degeneracy` |
| E5 | \(G_t\) both spaces | last-band \(G_t\) + seed-cluster interval + LOO-by-seed in local BGE-M3 and hosted `qwen3-embed-8b`, NF4 `raw_bytes`, every cell that has ≥3 last-band seeds; otherwise named **unidentified** / skipped LOO, not a sign flip |
| E6 | Lock construct | F1 + `N_confirm=3` unchanged; hash diagnostic only; language is *long-lived repetition lock*; not “late lock”; not absorbing |
| E7 | Local generate | every S11 generate step `served_provider=local`; no hosted Ministral / Gemma / `or-qwen3-8b` cell |
| E8 | Protocol | thinking tokens = 0 on completed steps; tokenizer round-trip failures named; fill and stop by quarter |
| E9 | One GPU | no two `afterlife generate` coresident |
| E10 | Spend | generate + local BGE **$0.00**; hosted Qwen-embed **cap $5** (ADR-0029) |
| E11 | Not pooled | no table or sentence averages Ministral or Gemma with S9 Qwen or S10 OLMo |
| E12 | Gemma reading | Gemma sentences use only the §1 pair (necessary-condition vs did-not-replicate); no causal sliding-window claim |
| E13 | Gemma OOM | OOM → stop that family; recorded; no silent substitute |

## 6. Pre-registered predictions

Empty `observed` is filled by the report.

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | Ministral Instruct NF4: ≥8/10 domain seeds have ≥1 confirmed lock (`N_confirm=3`) by 12W | 0.45 | |
| P2 | Ministral Base NF4 empty-completion rate is **higher** than Instruct (second estimand; S9 prior, S10 inverted) | 0.40 | |
| P3 | Ministral Instruct last-band \(G_t\) **CI excludes 0** in **both** spaces | 0.40 | |
| P4 | Sign of Ministral Instruct last-band \(G_t\) **agrees** across BGE-M3 and Qwen-embed (identified cells only) | 0.50 | |
| P5 | Thinking tokens remain 0 on all completed NF4 steps | 0.80 | |
| P6 | Mean block fill on completed NF4 12W steps ≥ 0.95 (final-quarter, not Q1 deaths) | 0.65 | |
| P7 | Gemma 4 12B NF4 does **not** OOM at `W+B=5120` on this 16 GB card | 0.75 | |
| P8 | Gemma IT empty-completion rate ≥ 20/40 of the planned cell (S8 microbench at the same `W`) | 0.55 | |
| P9 | If Ministral Instruct last-band is identified, its sign matches S9 Qwen Instruct (`+`). Magnitudes are not compared | 0.45 | |
| P10 | If Gemma last-band is identified and the CI excludes 0 in both spaces: *full attention on every layer is not necessary* for persistence in P1. If Gemma last-band is unidentified or has no completers: *did not replicate in the Gemma condition* — not a sliding-window causal claim | — | |
| P11 | Confirmed escape through 12W is 0 among lock-table trajectories that lock | 0.50 | |
| P12 | Point \(G_t>0\) with a CI that includes 0 is **not established**, not “true on the point” (S10 REVIEW) | — | |

P2 can be false (OLMo-style inversion) and the stage still succeeds.
P3 false with a point `+` and CI including 0 is scored via P12, not
softened to “true on the point.”

## 7. Budget and wall-clock

`afterlife estimate` on the four generate YAMLs (2026-09-19, fill=1,
`AFTERLIFE_BUDGET_USD_TOTAL=200`):

| pass | traj | input tok | output tok | USD |
| --- | ---: | ---: | ---: | ---: |
| S11.1 Ministral Base | 40 | 7,454,720 | 1,966,080 | 0.00 |
| S11.2 Ministral Instruct | 40 | 7,454,720 | 1,966,080 | 0.00 |
| S11.3 Gemma Base | 40 | 7,454,720 | 1,966,080 | 0.00 |
| S11.4 Gemma IT | 40 | 7,454,720 | 1,966,080 | 0.00 |
| **generate total** | **160** | **29,818,880** | **7,864,320** | **0.00** |

The CLI prints `stage budget not declared` because YAML
`budget_usd: 0.0` is falsy in the formatter. The generate ceiling
is **$0** by construction. Project remaining at kickoff:
**$189.46 / $200**. Hosted Qwen-embed (ADR-0029) is **not** in this
forecast; cap **$5**. Stop and ask before Gemini or before raising
that ceiling.

- **Wall-clock (Ministral Instruct microbench
  `s8-paperb-micro-ministral-8b-instruct-20260910T233421Z-e528749b`):**
  0.475 h / 12W traj. Ministral 80 × 0.475 ≈ **38 h** if fill=1 and
  every traj completes. S10 actual generate was ~42 h against an
  83–93 h sketch because empty-completion deaths are short. Re-time
  Ministral Base and both Gemma slugs on the first 12W run of each.
- **Gemma wall-clock is unknown.** IT failed at `W=4096` in S8.
  If empty deaths dominate, GPU hours are small. If both Gemma
  cells complete at smoke-scale ~8 tok/s, 80 × 49152 / 8 / 3600 ≈
  **136 h** is the pessimistic ceiling, not a forecast.
- **Exclusive-GPU sketch:** Ministral ~38 h + Gemma unknown.
  Native-chat deferred.
- **Stop-and-ask:** hosted $; Gemma OOM; thinking-storm; raising
  `T` above 12W; starting S12; changing F1; second GPU generate;
  E4B / `B` cut; pooling families; executing native-chat;
  retuning sampling; mixing FP8 Instruct or Reasoning-2512.

## 8. Risks specific to this stage

| Risk | Mitigation |
| --- | --- |
| Two agents on one GPU | one orchestrator; refuse if `nvidia-smi` shows compute |
| Reading S9 Base≈Instruct as this pair | E11; do not pool magnitudes |
| Reading Gemma as a causal attention test | E12; §1 language only |
| Calling the lock late / absorbing | E6 language from S9/S10 REVIEW |
| 40 traj as iid Bernoulli | seed-cluster bootstrap (ADR-0025) |
| Completer-only headline | two estimands in lede and P2 |
| “True on the point” when CI includes 0 | P12; S10 REVIEW |
| Native-chat silently equals raw_bytes | E3; no native YAML in this tree |
| Gemma OOM | E13; stop that family; no E4B |
| Tuning sampling after empty completions | degeneracy / death is data (F1) |
| Lock-table \(n\) ≠ completer \(n\) ≠ last-band \(n\) | name all three; S10 REVIEW |
| FP8 Instruct / Reasoning-2512 by typo | slugs are `pb-ministral-8b-*` BF16 pins |
