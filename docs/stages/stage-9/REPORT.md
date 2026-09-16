# Stage 9 report — Qwen3-8B Base ≈ Instruct at 12W on completed cells

**Status.** Closed 2026-09-16. Scientific review **APPROVED WITH
CHANGES** ([`REVIEW.md`](REVIEW.md)); phrase blockers applied.
Human authorised `--no-ff` close. Overall: **PARTIAL**
on matrix completeness (E1/E2 empty-completion attrition, named
and kept); **PASS** on the runnable confirmatory contrast.

Headline, **two estimands**. On completed 12W trajectories, local
Qwen3-8B Base and Instruct both form an early-onset long-lived
repetition lock (\(\tau_{\mathrm{lock}}\in\{0.75,1.00\}\)), show no
confirmed escape through \(T=12W\), and have last-band \(G_t>0\) in
both embedding spaces. That last-band gap is seed-conditioned
separation of late registers / loop families, not recovered prompt
memory and not a metastable semantic state. That is the P8
**completer** finding, not a failed experiment. The second
estimand is completion under this P1 `raw_completion` mechanism:
Base is worse (NF4 9/40 empty-completion deaths vs Instruct 2/40;
`recipe` 0/4 completed vs Instruct `recipe` 4/4 locked). Failed
cells stay in the sample and are not unlocks. Selecting on
completers is part of the result, not only a threat.

Plan: [`PLAN.md`](PLAN.md). Branch: `stage-8`. Native-chat still
deferred. S10 not started. Hosted S9 ledger increment **$0.00**.

The lock is **not** absorbing and is **not** a semantic state.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | NF4 `raw_bytes` 80/80 `COMPLETED` at `T=49152`, or missing cells named | **PARTIAL** | 69/80 completed (Instruct 38/40, Base 31/40). 11 FAILED empty-completion cells named in [`empty_completions.csv`](../../../artifacts/stage-9/empty_completions/empty_completions.csv) |
| E2 | INT8 F2 20/20, or PARTIAL with recorded reason | **PARTIAL** | 17/20 completed (Instruct 9/10, Base 8/10). Same empty-completion reason; not OOM |
| E3 | Native-chat only after `build_request` distinguishes `native_chat` | **PASS** | not executed; YAML present, generate deferred |
| E4 | Degeneracy before any published \(G_t\) | **PASS** | four `s9-degeneracy-*` runs 2026-09-15; [`degeneracy_verdicts.csv`](../../../artifacts/stage-9/degeneracy/degeneracy_verdicts.csv) |
| E5 | Last-band \(G_t\) + seed-cluster CI + LOO in both spaces, NF4 `raw_bytes` | **PASS** | [`gt_last_band.csv`](../../../artifacts/stage-9/gt_last_band/gt_last_band.csv); [`persistence_loo_all.csv`](../../../artifacts/stage-9/loo/persistence_loo_all.csv) |
| E6 | F1 + `N_confirm=3`; language is *long-lived repetition lock* | **PASS** | [`persistence_locks_all.csv`](../../../artifacts/stage-9/locks/persistence_locks_all.csv); hash not used as headline |
| E7 | Every generate step `served_provider=local`; no `or-qwen3-8b` | **PASS** | [`generate_status.csv`](../../../artifacts/stage-9/generate_status/generate_status.csv) |
| E8 | Thinking = 0 on completed steps; round-trip failures named; fill and stop reported | **PASS** | reasoning 0; round-trip failures 0; quarters in [`protocol_by_quarter.csv`](../../../artifacts/stage-9/protocol_by_quarter/protocol_by_quarter.csv) |
| E9 | One GPU; no two `afterlife generate` coresident | **PASS** | sequential `scripts/s9_run_matrix.sh` / INT8 resume; no second generate launched this close |
| E10 | Generate + local BGE $0; hosted Qwen-embed cap $5 | **PASS** | S9 ledger prefix **$0.00**; hosted embed realised $0 (ADR-0027) |

---

## 2. Results

### Generate

| Cell | `run_id` | Completed | Failed | Reason for missing |
| --- | --- | ---: | ---: | --- |
| Instruct NF4 | `s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6` | 38 | 2 | 5 consecutive empty completions (`programming` s2, `surreal` s2) |
| Base NF4 | `s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc` | 31 | 9 | same; **all four `recipe` descendants** plus five others |
| Instruct INT8 | `s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498` | 9 | 1 | `programming` s1 (one `trajectory.finished` event was duplicated on resume; unique = 10) |
| Base INT8 | `s9-paperb-qwen-base-int8-20260914T091655Z-11069a87` | 8 | 2 | `biology` s2, `programming` s1 |

Failed cells stay in the sample. They do not enter \(G_t\) because
they have no 12W embedding. That is missing data, not an unlock.

### Protocol diagnostics (by quarter)

Within-trajectory step quarters, then mean across trajectories in
the cell ([`protocol_by_quarter.csv`](../../../artifacts/stage-9/protocol_by_quarter/protocol_by_quarter.csv)).
A run-level mean is not the claim.

| Cell | Q1 fill / stop | Q2 | Q3 | Q4 (final quarter) |
| --- | --- | --- | --- | --- |
| Instruct NF4 | 1.000 / 0.000 | 0.979 / 0.025 | 0.961 / 0.050 | **1.000 / 0.000** |
| Base NF4 | 0.773 / 0.266 | 0.977 / 0.054 | 0.916 / 0.120 | **0.975 / 0.052** |
| Instruct INT8 | 1.000 / 0.000 | 0.987 / 0.100 | 0.906 / 0.100 | **1.000 / 0.000** |
| Base INT8 | 0.840 / 0.200 | 1.000 / 0.000 | 1.000 / 0.000 | **1.000 / 0.000** |

Base Q1 fill 0.773 and stop 0.266 are the empty-completion deaths,
not a late-regime collapse. On trajectories that reach Q4, fill
stays ≥ 0.975. Instruct never drops below 0.96 in any quarter mean.
Thinking tokens = 0 on every completed step. Tokenizer round-trip
failures = 0. Served provider = `local`.

### Degeneracy, then lock

F1 first. Every completed NF4 and INT8 trajectory in the lock table
is a confirmed lock (`N_confirm=3`); confirmed escape **0/86**
completed embeddings (38+31+9+8). \(\tau_{\mathrm{lock}}\) is
**0.75** or **1.00** (unique values in the lock table): three or
four 1024-token chunks. The lock is confirmed **before or at** the
context horizon, then persists through 12W with no confirmed
escape.

Seed-level lock (seeds with ≥1 confirmed lock), BGE lock table
([`locks_by_seed.csv`](../../../artifacts/stage-9/locks_by_seed/locks_by_seed.csv)):

| Cell | Seeds with ≥1 lock / domain seeds present in the lock table |
| --- | --- |
| Instruct NF4 | 10/10 |
| Base NF4 | 9/9 completed seeds; **`recipe` has zero completed descendants** |
| Instruct INT8 | 5/5 F2 seeds (programming has one surviving descendant) |
| Base INT8 | 5/5 F2 seeds (biology and programming each lost one) |

### Last-band \(G_t\)

\(G_t = d_{\mathrm{between}} - d_{\mathrm{within}}\) on L2-normalised
embeddings. Interval = seed-cluster bootstrap, not Greenwood
(ADR-0025).

| Cell | Space | Last-band \(G_t\) | 95% CI | CI excludes 0 |
| --- | --- | ---: | --- | --- |
| Instruct NF4 | BGE-M3 | 0.1514 | [0.0871, 0.1590] | yes |
| Base NF4 | BGE-M3 | 0.1476 | [0.0692, 0.1580] | yes |
| Instruct NF4 | Qwen-embed | 0.3046 | [0.1917, 0.3152] | yes |
| Base NF4 | Qwen-embed | 0.2333 | [0.1172, 0.2442] | yes |
| Instruct INT8 | BGE-M3 | 0.1650 | [−0.0643, 0.1650] | no |
| Base INT8 | BGE-M3 | 0.1312 | [−0.0791, 0.1312] | no |
| Instruct INT8 | Qwen-embed | 0.3272 | [0.0049, 0.3389] | yes |
| Base INT8 | Qwen-embed | 0.2547 | [−0.0924, 0.3166] | no |

LOO-by-seed: no held-out seed flips last-band \(G_t\) to ≤ 0
([`persistence_loo_all.csv`](../../../artifacts/stage-9/loo/persistence_loo_all.csv)).

INT8 is concordance (P7), not a third headline. Same sign as the
matched NF4 cell; BGE INT8 intervals include 0 because
within-seed pairs are 3–4.

Figure: [`gt_last_band_figure`](../../../artifacts/stage-9/gt_last_band_figure/gt_last_band_figure.png).
Overlays: [`gt_overlay_bge`](../../../artifacts/stage-9/gt_overlay_bge/gt_overlay_bge.png),
[`gt_overlay_qwen`](../../../artifacts/stage-9/gt_overlay_qwen/gt_overlay_qwen.png).
Per-cell tidy frames under [`artifacts/stage-9/persistence/`](../../../artifacts/stage-9/persistence/).

Fingerprint agreement (exact-cycle hash) was the third name in the
confirmatory order. It was **not** computed as a headline. E6
already forbids treating the hash as the lock.

### What the completed text actually is

Late-window excerpts. Somebody looked.

Instruct NF4, `physics` s1 — boxed Higgs distinction, then the same
box again (`s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6`):

> The Higgs phases in lattice gauge theory and the Standard Model are
> distinct due to differences in symmetry type, Higgs field nature, and
> physical outcomes. *Note: The boxed conclusion is a concise summary
> of the key distinction between the two Higgs phases.*

Instruct NF4, `love` s2 — assistant-register loop:

> Let me know what you need! 😊
>
> Let me know what you need! 😊
>
> Let me know what you need! 😊

Base NF4, `biology` s1 — paper-ese that stays on the seed topic
(`s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc`):

> The authors speculate that it may be required for the proper
> positioning of the nascent peptide in the exit tunnel of the
> ribosome. The authors also tested whether the effect of the mutation
> could be overcome by a second mutation that would restore the charge
> of the nascent peptide.

Base INT8, `surreal` s1 — exact lexical cycle
(`s9-paperb-qwen-base-int8-20260914T091655Z-11069a87`):

> the interior of the interior of the interior of the interior of the
> interior of the interior of the interior of the interior of the
> interior of the interior of the interior of the interior

A positive \(G_t\) here is seed-conditioned persistence of these
late registers, including loops. It is not recovered prompt memory
and not a metastable semantic state.

---

## 3. Prediction vs. outcome

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | Instruct NF4: ≥8/10 domain seeds have ≥1 confirmed lock by 12W | 0.55 | **true** — 10/10 |
| P2 | Base NF4 seed-level lock rate is **lower** than Instruct | 0.60 | **numerically true, dynamically false** — 9/10 vs 10/10 only because `recipe` produced zero completed trajectories. Completed Base seeds lock 9/9 |
| P3 | Instruct last-band \(G_t > 0\) in both spaces | 0.50 | **true** — 0.1514 and 0.3046; both CIs exclude 0 |
| P4 | Sign of Instruct last-band \(G_t\) agrees across spaces | 0.55 | **true** — both positive |
| P5 | Thinking tokens remain 0 on all completed NF4 steps | 0.80 | **true** |
| P6 | Mean block fill on NF4 12W ≥ 0.95 | 0.70 | **true** at run level (Instruct 0.999, Base 0.963). Base Q1 is 0.773 because failed cells die there; final-quarter Base fill is 0.975 |
| P7 | INT8 vs NF4, Instruct, five F2 seeds: same sign of last-band \(G_t\) | 0.45 | **true** in both spaces. BGE INT8 CI includes 0 |
| P8 | If Base≈Instruct on lock rate and last-band \(G_t\) sign, that is a finding | — | **completer estimand, not the only estimand.** On completers: lock 31/31 vs 38/38; last-band sign +/+ in both spaces. Second estimand: Base completion worse (NF4 9/40 vs 2/40; `recipe` 0/4 vs 4/4). |

---

## 4. Surprises

1. **The lock is early.** \(\tau_{\mathrm{lock}} \in \{0.75, 1.00\}\).
   Repetition is confirmed before or as the seed leaves, then never
   unconfirms through 12W. This is not a late-onset afterlife lock.
2. **Base `recipe` is a protocol hole, not an unlocked seed.** Four
   of four descendants died on empty completion after 7–13 generated
   tokens. P2 must not be read as Base unlocking.
3. **Empty completion is the attrition mode**, not OOM and not a
   thinking storm. 14/100 planned cells. Worse on Base than Instruct.
4. **Qwen-embed last-band \(G_t\) is larger** than BGE-M3 (~0.23–0.30
   vs ~0.15). That is a scale difference between spaces, not a second
   scientific claim. Signs agree.
5. **Hosted Qwen-embed cost $0** at 4132 chunks / 4.23M tokens
   (ADR-0027). Do not treat that as a permanent price.
6. Persistence artifacts were first written into one directory per
   embedding and overwritten by the last cell. This close rebuilt
   per-cell + summary tables from the eight persistence `run_id`s.

---

## 5. Threats to validity

- **P1 re-prompt is not sliding attention.** The generator never
  sees a true `Tail_W` KV cache. A lock under `raw_completion` can
  be a continuation-mechanism artifact. Native-chat is still
  deferred (`build_request` still short-circuits to raw).
- **The lock is surface-form.** F1 flags 3-gram repetition. The
  love-s2 and surreal-s1 quotes are loops. \(G_t > 0\) can be
  “same loop family stays nearer than other loop families.”
- **Missing cells are not random.** Named as the second estimand in
  the lede and P8, not only here: Base NF4 9/40 vs Instruct 2/40;
  `recipe` 0/4 vs 4/4. Conditioning persistence on completers
  selects for free-running seeds.
- **INT8 CIs that include 0** are small-n (5 seeds, 1–2 descendants),
  not a sign flip. Do not promote INT8 to a third headline.
- **Two embedding spaces, one generator family.** Sign agreement
  here is not architecture-independence. S10/S11 are other families.
- **No fingerprint-agreement pass.** Confirmatory order named it
  third. Hash remains diagnostic only (E6). Do not invent a
  fingerprint table from this close.
- **NF4 ≠ hosted Paper A Instruct.** Local 4-bit Instruct is not
  `or-qwen3-8b`. Paper A 19/20 lock is a prior, not this cell.
- **Kaleido/Chrome missing** on the persistence plotly export.
  Print panels are the matplotlib last-band and overlay figures.

---

## 6. Cost actuals

| | Estimate | Actual |
| --- | ---: | ---: |
| Local generate | $0 | **$0** |
| Local BGE-M3 | $0 | **$0** |
| Hosted `qwen3-embed-8b` | cap $5 (ADR-0027) | **$0** |
| Stage 9 ledger prefix | — | **$0.00** |
| Project ledger (all stages) | ceiling $200 | **$10.54** ($189.46 left) |

Wall-clock was days of exclusive GPU, not the 44 h sketch: Base was
slower and INT8 was serialized after NF4. No second generate was
launched to “catch up.”

---

## 7. Implications for the plan

- **S10 may start after the human authorises `--no-ff` close**, not
  before. On **this Qwen3-8B pair, P1 `raw_bytes`, NF4, T=0.3**,
  the completer contrast did not show post-training reshaping the
  early-onset long-lived repetition lock that persists through 12W.
  That is not a claim about post-training as a class. Last-band
  \(G_t\) remains a late-window measurement of an already-locked
  register / loop-family. OLMo’s Base → SFT → DPO → RLVR ladder is
  the first place a post-training difference can appear. Do not
  pool with Qwen.
- **Empty-completion attrition travels.** S10/S11 must keep FAILED
  empty cells in the sample and must not retune sampling to remove
  them. Base `recipe` is a warning for other pretrained checkpoints.
- **Native-chat stays blocked** until `build_request` distinguishes
  `serialization: native_chat` from `raw_completion`.
- **F1 thresholds and `N_confirm=3` stay frozen.** This stage did
  not retune them after seeing 86/86 completed locks.
- Master plan S9 line: closed 2026-09-16. S10 waits on a new
  `stage-10` branch cut from `main`, not on this tree.

Index of artifacts: [`artifacts/stage-9/INDEX.md`](../../../artifacts/stage-9/INDEX.md).
