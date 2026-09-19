# Stage 10 report — OLMo 3 7B post-training ladder kills completion, not the lock

**Status.** Computations complete 2026-09-18. Mechanical gate
**passed**. Scientific review **APPROVED WITH CHANGES**
([`REVIEW.md`](REVIEW.md)); two phrase blockers applied below.
Overall: **PARTIAL** on matrix completeness (E1/E2 empty-completion
attrition, named and kept) and on E5 identification (DPO last-band
unidentified; RLVR LOO skipped); **PASS** on the runnable confirmatory
contrast that exists. S11 not started. Native-chat still deferred.
Do not merge until the human authorises `--no-ff`.

Headline, **two estimands**. On this local OLMo 3 7B Instruct line
(Base → SFT → DPO → RLVR), P1 `raw_bytes`, `W=4096`, T=0.3, 12
turnovers, **completion collapses from Base through DPO and floors
at DPO ≈ RLVR**: NF4 empty-completion deaths 13/40 → 21/40 → 37/40
→ 36/40. That is the opposite of S9 Qwen (Base worse). Selecting
on completers is part of the result. Among trajectories that enter
the lock table (`min_chunks=8`; not identical to 12W completers),
every trajectory is a confirmed early-onset long-lived repetition
lock (`N_confirm=3`); confirmed escape is **0** in both embedding
spaces. Last-band \(G_t\): Base NF4 CIs exclude 0 in both spaces
(BGE 0.0944 [0.029, 0.108]; Qwen 0.189 [0.086, 0.221]); SFT BGE
includes 0, SFT Qwen excludes 0; RLVR point `+` in both spaces
(0.202 / 0.335), both CIs include 0, LOO skipped (`<3` seeds;
lock-table \(n=5\) is not last-band \(n\)); DPO last-band
**unidentified** (3 within, 0 between — the `noise` family), not
a sign flip. Last-band \(G_t>0\), where the interval excludes 0,
is seed-conditioned separation of late registers / loop families,
not recovered prompt memory. Do not pool with S9 Qwen.

Plan: [`PLAN.md`](PLAN.md). Branch: `stage-10`.

The lock is **not** absorbing and is **not** a semantic state.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | NF4 `raw_bytes` 160/160 `COMPLETED` at \(T=49152\), or missing cells named | **PARTIAL** | 53/160 completed (Base 27, SFT 19, DPO 3, RLVR 4). 107 FAILED empty-completion cells named in [`empty_completions.csv`](../../../artifacts/stage-10/empty_completions/empty_completions.csv) |
| E2 | INT8 F2 20/20, or PARTIAL with recorded reason | **PARTIAL** | 5/20 completed (Base 5/10, RLVR 0/10). Same empty-completion reason; not OOM. RLVR INT8 generate `STATUS=FAILED` is the only incomplete non-SUPERSEDED run |
| E3 | Native-chat deferred | **PASS** | no native YAML executed |
| E4 | Degeneracy before any published \(G_t\) | **PASS** | six `s10-degeneracy-*` runs 2026-09-18 before persistence; [`degeneracy_verdicts.csv`](../../../artifacts/stage-10/degeneracy/degeneracy_verdicts.csv) |
| E5 | Last-band \(G_t\) + seed-cluster CI + LOO in both spaces, NF4 `raw_bytes`, four rungs | **PARTIAL** | Both spaces in [`gt_last_band.csv`](../../../artifacts/stage-10/gt_last_band/gt_last_band.csv). DPO last-band unidentified (0 between pairs) in both spaces. RLVR LOO skipped (`<3` seeds) in both spaces. Base and SFT have \(G_t\) + CI + LOO in both spaces |
| E6 | F1 + `N_confirm=3`; language is *long-lived repetition lock* | **PASS** | [`persistence_locks_all.csv`](../../../artifacts/stage-10/locks/persistence_locks_all.csv); hash not used as headline |
| E7 | Every generate step `served_provider=local`; no hosted OLMo | **PASS** | [`generate_status.csv`](../../../artifacts/stage-10/generate_status/generate_status.csv) |
| E8 | Thinking = 0; round-trip failures named; fill and stop by quarter | **PASS** | reasoning 0; round-trip 0; [`protocol_by_quarter.csv`](../../../artifacts/stage-10/protocol_by_quarter/protocol_by_quarter.csv) |
| E9 | One GPU; no two `afterlife generate` coresident | **PASS** | sequential `s10_run_matrix.sh`; analysis after `MATRIX DONE` |
| E10 | Generate + local BGE $0; hosted Qwen-embed cap $5 | **PASS** | generate + BGE **$0**; hosted `qwen3-embed-8b` ledger **$0.00** (ADR-0028 cap $5) |
| E11 | Not pooled with S9 Qwen | **PASS** | no table averages OLMo with Qwen |

---

## 2. Results

### Generate (second estimand)

| Cell | `run_id` | Completed | Failed | Reason for missing |
| --- | --- | ---: | ---: | --- |
| Base NF4 | `s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3` | 27 | 13 | 5 consecutive empty completions |
| SFT NF4 | `s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e` | 19 | 21 | same |
| DPO NF4 | `s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f` | 3 | 37 | same |
| RLVR NF4 | `s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc` | 4 | 36 | same |
| Base INT8 | `s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8` | 5 | 5 | same; not OOM |
| RLVR INT8 | `s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca` | 0 | 10 | same; run-level STATUS=FAILED |

Failed cells stay in the sample. They do not enter last-band \(G_t\)
when they have no last-band pairs. That is missing data, not an unlock.

The lock table is not identical to the 12W completer set.
Persistence admits any trajectory with `min_chunks=8`. Lock-table
\(n\) exceeds 12W completers on SFT (20 vs 19), DPO (5 vs 3), RLVR
(5 vs 4), and Base INT8 (6 vs 5). Those extras died after eight
chunks and before \(T=49152\). Last-band \(G_t\) still uses only the
last integer turnover band.

Base NF4 recorded 55 `trajectory.finished` events on 40 unique
trajectories (host power-off resume). Unique counts above are the
sample.

### Protocol diagnostics (by quarter)

Within-trajectory step quarters, then mean across trajectories that
reach that quarter
([`protocol_by_quarter.csv`](../../../artifacts/stage-10/protocol_by_quarter/protocol_by_quarter.csv)).
A run-level mean is not the claim.

| Cell | Q1 fill / stop | Q2 | Q3 | Q4 |
| --- | --- | --- | --- | --- |
| Base NF4 | 0.843 / 0.302 | 1.000 / 0.000 | 0.933 / 0.069 | 0.965 / 0.036 |
| SFT NF4 | 0.789 / 0.410 | 0.982 / 0.023 | 0.798 / 0.259 | 0.943 / 0.074 |
| DPO NF4 | 0.928 / 0.375 | 0.953 / 0.063 | 0.622 / 0.593 | 0.630 / 0.636 |
| RLVR NF4 | 0.835 / 0.475 | 1.000 / 0.000 | 0.620 / 0.571 | 0.772 / 0.438 |
| Base INT8 | 0.891 / 0.325 | 1.000 / 0.000 | 0.999 / 0.143 | 0.862 / 0.190 |
| RLVR INT8 | 0.886 / 0.500 | 0.818 / 0.250 | 0.390 / 0.833 | 0.964 / 0.500 |

Q1 stop is empty-completion death, not a late-regime collapse. On
**completed** 12W NF4 trajectories, `summarise_run.py --target-steps 48`
reports block fill **1.000** and stop **0.000**. Thinking tokens = 0
on every completed step. Tokenizer round-trip failures = 0. Served
provider = `local`.

### Degeneracy, then lock (first estimand, completers)

F1 first. Every trajectory that entered the lock table, in either
space, is a confirmed lock; confirmed escape **0**. The lock is
confirmed early and persists through 12W with no confirmed escape.
Language: early-onset long-lived repetition lock — not “late lock”,
not absorbing.

Seed-level lock (seeds with ≥1 confirmed lock), BGE lock table
([`locks_by_seed.csv`](../../../artifacts/stage-10/locks_by_seed/locks_by_seed.csv)):

| Cell | Seeds with ≥1 lock / domain seeds in the lock table |
| --- | --- |
| Base NF4 | 10/10 present (recipe has one surviving descendant) |
| SFT NF4 | 7/7 present |
| DPO NF4 | 3 present (`finance`, `love`, `noise`); last-band \(G_t\) unidentified |
| RLVR NF4 | **2/10** (`noise`, `recipe`) — P1 false |
| Base INT8 | 4 F2 seeds present |
| RLVR INT8 | none (0 completers); persist SUPERSEDED (`min_chunks=8`) |

### Last-band \(G_t\) (both spaces)

\(G_t = d_{\mathrm{between}} - d_{\mathrm{within}}\) on L2-normalised
embeddings. Interval = seed-cluster bootstrap, not Greenwood
(ADR-0025).

| Cell | Space | Last-band \(G_t\) | 95% CI | CI excludes 0 |
| --- | --- | ---: | --- | --- |
| Base NF4 | BGE-M3 | 0.0944 | [0.0288, 0.1076] | yes |
| Base NF4 | Qwen-embed | 0.1891 | [0.0861, 0.2214] | yes |
| SFT NF4 | BGE-M3 | 0.1018 | [−0.0070, 0.1218] | no |
| SFT NF4 | Qwen-embed | 0.1757 | [0.0342, 0.2055] | yes |
| DPO NF4 | BGE-M3 | **undefined** | — | last band: 3 within, 0 between |
| DPO NF4 | Qwen-embed | **undefined** | — | last band: 3 within, 0 between |
| RLVR NF4 | BGE-M3 | 0.2015 | [−0.1342, 0.2015] | no |
| RLVR NF4 | Qwen-embed | 0.3346 | [−0.1472, 0.3346] | no |
| Base INT8 | BGE-M3 | 0.0982 | [−0.2271, 0.2198] | no |
| Base INT8 | Qwen-embed | 0.1445 | [−0.2943, 0.3277] | no |

Source: [`gt_last_band.csv`](../../../artifacts/stage-10/gt_last_band/gt_last_band.csv).
LOO-by-seed for Base and SFT, both spaces:
[`persistence_loo_all.csv`](../../../artifacts/stage-10/loo/persistence_loo_all.csv).
RLVR LOO is absent (`<3` seeds); the CLI records \(G_t\) and skips LOO
instead of dropping the rung.

Adjacent edges
([`adjacent_edges.csv`](../../../artifacts/stage-10/adjacent_edges/adjacent_edges.csv)):
Base–SFT same sign `+` / `+` in both spaces; locks saturate. SFT–DPO
and DPO–RLVR are **not** sign flips: DPO last-band \(G_t\) is
unidentified in both spaces.

INT8 vs NF4, Base, both spaces: same sign `+`
([`int8_vs_nf4.csv`](../../../artifacts/stage-10/int8_vs_nf4/int8_vs_nf4.csv)).
RLVR INT8 has no completers.

Figures:
[`gt_last_band_figure`](../../../artifacts/stage-10/gt_last_band_figure/gt_last_band_figure.png),
[`gt_overlay_bge`](../../../artifacts/stage-10/gt_overlay_bge/gt_overlay_bge.png),
[`gt_overlay_qwen`](../../../artifacts/stage-10/gt_overlay_qwen/gt_overlay_qwen.png).

A hung BGE embed of RLVR INT8 (14 chunks, ~44 min idle after weight
load) was killed and retried in 45 s
(`s10-embed-paperb-olmo-embed-bge-20260918T172254Z-60d02d30`
SUPERSEDED). Analysis-resume re-ran BGE persist; the earlier COMPLETED
siblings are SUPERSEDED in favour of the later ones. RLVR INT8 persist
in both spaces is SUPERSEDED (`min_chunks=8`, 0 completers) — recorded
skip, not a silent drop.

### What the completed text actually is

Late-window excerpts. Somebody looked.

Base NF4, `physics` s1 — lattice-QCD register that reprints the same
claim (`s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3`):

> The deconfinement transition is therefore a phase transition that
> is not driven by the lattice spacing, and the lattice spacing is
> not a good measure of the correlation length in the deconfined
> phase. The deconfinement transition is therefore a phase
> transition that is not driven by the lattice

SFT NF4, `love` s2 — assistant-register loop
(`s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e`):

> I want to make sure you're ready to move on, and I want to make
> sure you're ready to move on, and I want to make sure you're
> ready to move on, and I want to make sure you're ready to move on

DPO NF4, `noise` s2 — last-band 12W completer, ordinal loop (one of
the three `noise` descendants that make last-band \(G_t\)
unidentified; `s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f`).
Not `finance` s1, which is a FAILED lock-table extra (16 297 tokens).

> seventh of the seventh of the seventh of the seventh of the
> seventh of the seventh of the seventh of the seventh of the
> seventh of the seventh of the seventh of the seventh of the
> seventh of the seventh of the seventh of the seventh of the

RLVR NF4, `noise` s1 — ordinal loop
(`s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc`):

> of the seventy seventh of the seventy eighth of the seventy ninth
> of the eightieth of the eighty first of the eighty second of the
> eighty third of the eighty fourth of the eighty fifth of the
> eighty sixth of the eighty seventh of the eighty eighth

Base INT8, `surreal` s1 — exact lexical cycle
(`s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8`):

> They were not allowed to look at the register, except to say that
> they were not allowed to look at the register. They were not
> allowed to look at the register, except to say that they were not
> allowed to look at the register.

Where the last-band interval excludes 0, a positive \(G_t\) is
seed-conditioned persistence of these late registers, including
loops. It is not recovered prompt memory and not a metastable
semantic state. DPO last-band \(G_t\) stays unidentified because
the three 12W completers are one seed family.

---

## 3. Prediction vs. outcome

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | RLVR NF4: ≥8/10 domain seeds have ≥1 confirmed lock by 12W | 0.50 | **false** — 2/10 (`noise`, `recipe`) |
| P2 | Base NF4 empty-completion rate is **higher** than RLVR | 0.55 | **false** — 13/40 vs 36/40. Opposite of S9 Qwen |
| P3 | RLVR last-band \(G_t > 0\) in **both** spaces | 0.50 | **not established** — BGE 0.2015 [−0.134, 0.202]; Qwen 0.3346 [−0.147, 0.335]. Both CIs include 0; upper bounds equal the point; LOO skipped. Lock-table \(n=5\) is not last-band \(n\) (3 within / 3 between = 4 traj, 2 seeds) |
| P4 | Sign of RLVR last-band \(G_t\) agrees across spaces | 0.55 | **true** — `+` / `+` |
| P5 | Thinking tokens remain 0 on all completed NF4 steps | 0.80 | **true** |
| P6 | Mean block fill on completed NF4 12W steps ≥ 0.95 (final-quarter) | 0.65 | **true** on completed 12W steps (fill 1.000). Cell-level Q4 means include dying trajs |
| P7 | INT8 vs NF4, Base and RLVR, F2: same sign of last-band \(G_t\) | 0.45 | **partial** — Base same sign `+` in both spaces. RLVR INT8 has 0 completers |
| P8 | If all four rungs share last-band sign and completer locks saturate, that is a finding | — | **locks saturate where a lock table exists; last-band sign is not identified on DPO.** Completer lock is not a failed contrast. Completion collapse from Base through DPO, then a **floor** at DPO ≈ RLVR (37 vs 36 empty), is the second estimand |
| P9 | No adjacent-edge last-band \(G_t\) **sign flip** | 0.45 | **not falsified** — Base–SFT `+`/`+` in both spaces. DPO last-band undefined, not a flip |
| P10 | Base `recipe`: ≥2/4 descendants empty-completion FAILED | 0.50 | **true** — 3/4 (`s1`,`s2`,`s4`) |

SFT is the one place the two spaces disagree on a CI: BGE includes 0,
Qwen excludes 0. The sign is `+` in both. That is not a P4 failure
(P4 is RLVR sign agreement).

---

## 4. Surprises

1. **The ladder is a completion collapse-then-floor, not a lock
   ladder.** Post-training on this line makes free-running under P1
   rarer (13 → 21 → 37 → 36 / 40). DPO → RLVR is a floor, not a
   further collapse. Completers still lock.
2. **P2 is backwards relative to S9 Qwen.** OLMo Base completes more
   than RLVR. One family is not a law (E11).
3. **DPO last-band \(G_t\) is unidentified in both spaces.** Three
   last-band completers are one seed family (`noise`) (3 within, 0
   between).
4. **P1 is badly false.** RLVR locks on 2/10 seeds because only those
   seeds produce long-enough trajectories.
5. **A 14-chunk BGE embed hung** after weight load (GPU idle,
   `wait_woken`). Retry after kill finished in 45 s. Recorded as
   SUPERSEDED, not dropped.
6. **Hosted Qwen-embed cost $0.00** on the RouterAI ledger, under the
   $5 cap. SFT CI excludes 0 in Qwen-embed and includes 0 in BGE-M3;
   sign still agrees.

---

## 5. Threats to validity

- **P1 re-prompt is not sliding attention.** A lock or an empty
  completion under `raw_completion` can be a continuation-mechanism
  artifact. Native-chat is still deferred.
- **The lock is surface-form.** The quotes are loops and assistant
  registers. \(G_t>0\) can be “same loop family stays nearer than
  other loop families.”
- **Missing cells are not random.** They *are* the second estimand.
  Conditioning persistence on completers selects for free-running
  seeds; that selection gets stronger down the ladder.
- **Lock-table \(n\) is not 12W completer \(n\).** `min_chunks=8`
  admits mid-horizon deaths. Last-band \(G_t\) is still the last
  integer band.
- **DPO/RLVR last-band CIs and NaNs are small-n**, not a mechanistic
  sign change. Do not promote a NaN to a flip.
- **One generator family.** Do not pool with S9 Qwen.
- **Hung BGE / dirty git / duplicate persist.** The hang and the
  analysis-resume duplicates are SUPERSEDED. Manifests note a dirty
  tree (HANDOFF/README edits after generate start).
- **INT8 concordance is one rung.** RLVR INT8 is 0/10.
- **`runs.complete` WARN.** The only incomplete non-SUPERSEDED run is
  RLVR INT8 generate. That is recorded empty-completion attrition, not
  a dropped cell.

---

## 6. Cost actuals

| | Estimate | Actual |
| --- | ---: | ---: |
| Local generate | $0 | **$0** |
| Local BGE-M3 | $0 | **$0** |
| Hosted `qwen3-embed-8b` | cap $5 (ADR-0028) | **$0.00** (2972 chunks / 3.04M tokens; RouterAI unit $0) |
| Project ledger | ceiling $200 | **$10.54** / $200 |

Wall-clock generate was ~42 h exclusive after a host power-off
resume, not the 93 h sketch (empty deaths are short). INT8 was
~2–3× slower per step (~130 s vs ~35 s). Analysis (degeneracy, BGE,
hosted Qwen-embed, persistence) finished 2026-09-18T18:57:20Z.

---

## 7. Implications for the plan

- **S11 may not start** until this stage closes with a gate-green
  REPORT and scientific sign-off. The OLMo finding to carry is:
  on **this line**, post-training did not unlock completers; it
  reduced the number of completers. Do not pool with Qwen.
- **Empty-completion attrition travels and can invert.** S11 must
  keep FAILED empty cells and must not retune sampling.
- **Native-chat stays blocked** until `build_request` distinguishes
  `native_chat` from `raw_completion`.
- **F1 thresholds and `N_confirm=3` stay frozen.**
- Last-band \(G_t\) on a rung with one completing seed is not a
  contrast. Say “unidentified”, not “flat” or “flipped.”

Index of artifacts: [`artifacts/stage-10/INDEX.md`](../../../artifacts/stage-10/INDEX.md).
