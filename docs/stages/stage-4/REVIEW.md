# Stage 4 review
Reviewer: Cursor Grok 4.6 (scientific supervisor)   Date: 2026-09-05
Gate: **FAIL on this reviewer VM** (`afterlife review --stage s4`, exit 1).
Cause: `runs/s4` is absent. Raw runs are git-ignored; this environment
has `runs/s0`, `runs/s1`, and a ledger truncated at Stage 1 ($9.0270 of
the old $50 ceiling). Same limitation as the Stage 3 review.

Checks that still PASS on the committed record: `plan.exists`,
`artifacts.bundle` (60/60 with data, captions, limitations),
`budget.reconciled` (stage $0.00 here — see observation 14),
`report.diagnostics_segmented`, `report.quotes_text`,
`report.scores_predictions`.
SKIPPED: `runs.complete`, `runs.integrity`,
`analysis.degeneracy_labelled`, `budget.ledger_matches_events`.
WARN: 1 LEAD citation (same leftover as Stages 2–3).

Executor attested `afterlife review --stage s4` exit 0 on a machine
that has `runs/s4`. Latest GitHub CI on `cursor/stage-4-6dce` is
**success** (`33958640430`, 2026-09-05T09:40:54Z). This review is of
the committed PLAN / REPORT / artifacts — the record a remote reader
has. I have not re-hashed generation manifests.

Verdict: **APPROVED**

The stage verdict PASS is the right stage verdict. This review does
not upgrade it, does not reopen generate, and does not merge.

Do not merge to `main` from this review. The standing instruction is
that the human closes the branch. S5 generate is not authorised.

---

## Blocking findings

None.

The headline sentences the report actually writes follow from the
tidy grid. Q4 and Q6 are scored **Wrong** in the open. “Clean ≠ left
the register” is an existence claim with a quoted counterexample, not
a hedged upgrade of T=1.5 into diffusion. The 0.083 bar is the Stage 1
calibration, reused at the calibration chunk size, and is not
load-bearing for the T≤1.0 cells. One process is named as one process.

---

## Non-blocking observations

Each is a constraint on later prose, not a reason to reopen the stage.

### 1. H5 “absent” is the F6 branch; the scientific contrast is untestable

Master-plan H5 is a confinement-versus-diffusion *region*: low-T
clean-`α` (and dwell / state count) versus high-T `α → 1`. F6’s
operational score is: name a band where the high-T clean-`α` CI
excludes the low-T clean-`α` in both spaces at one `W`, **or** say
the transition is absent.

Every T≤1.0 cell has `n_clean = 0`. There is no low-T clean-`α`.
Q5 pre-registered the absent branch. REPORT §5 says the right
sentence: “H5 is absent because the comparison is undefined, not
because we measured two clean-`α`s and they overlapped.”

Keep that qualifier wherever “H5 absent” is reused. Do not write
“we tested the temperature transition and found none.” A later grid
that produces a clean low-T cell can still show a transition. The
high-T *diffusion limb* is independently rejected where clean
(`α` CIs exclude 1). That is a different sentence.

Master-plan H5 also mentioned “few states, long dwell.” `n_macro`
was correctly kept off the headline (F9). Do not back-fill dwell or
state count from this stage.

### 2. Per-cell looping CI `[1, 1]` is a collapsed bootstrap

`looping_rate_by_cell.csv`: six T≤1.0 cells are 4/4, CI `[1, 1]`;
T=1.5 `W=4096` is 0/4, CI `[0, 0]`; T=1.5 `W=8192` is 2/4, CI `[0, 1]`.
The percentile trajectory-bootstrap cannot emit a value that is not
in the sample. Four identical Bernoulli draws produce a zero-width
interval. Clopper–Pearson for 4/4 is approximately `[0.40, 1]`.

The scientific weight is the **joint** count: 24/24 degenerate at
T≤1.0 (6 cells × 4). That interval is tight. The report’s “the 4/4
lock at T≤1.0 does [decide a direction]” is true of the joint count,
not of six ceremonial `[1, 1]`s.

Do not carry “CI `[1, 1]`” into the manuscript as a precision claim.
The T=1.5 `W=8192` interval `[0, 1]` is the honest one; the report
already calls it a coin flip.

### 3. “Lock” is degeneracy, not one mechanism

Glossary has no “lock.” The operational object is
`degenerate = (looping_fraction ≥ 0.5) OR (late shingle Jaccard median ≥ 0.0122)`.
At cell level, T≤1.0 is 4/4 on that flag at both `W`. At trajectory
level, 23/24 T≤1.0 rows are `at_fixed_point = 1`. The exception is
`or-qwen3-8b__W8192__T0p7__surreal__s2`: mode 1, `looping_fraction = 0.793`,
Jaccard median `0.0078`. Still degenerate. Still counted in “4/4 lock.”

The two T=1.0 cells are not the same *protocol* object. Quarter-4
stop at `W=4096` T=1.0 is `0.954 [0.931, 0.972]`; at `W=8192` T=1.0
it is `0.450 [0.050, 0.850]`. Fill is `0.434` versus `0.745` (Q4).
One cell is stop-saturated forced continuation; the other is still
generating. Both are surface-degenerate. Do not write “the same lock”
as a dynamical identification. Surprise #1 (“`W = 8192` is the same
lock”) is true as a looping-rate sentence only.

Eight T≤1.0 trajectories have `looping_fraction < 0.5` and are
degenerate via the fixed-point arm, including the named S4.1 T=0.7
physics s1 (`looping_fraction = 0.0465`, Jaccard `0.751`). The
0.083 n-gram bar is not what labelled those rows.

### 4. 0.083 is calibrated and in-regime; it is not the load-bearing cut here

Exact statistic: per-chunk 3-gram repetition rate
(`1 − |unique 3-grams| / |3-grams|`) on word tokens. Chunk flagged
if rate ≥ `0.083`. Trajectory looping-arm if ≥ 50% of post-horizon
chunks are flagged. Second arm: median late-half 5-shingle Jaccard
≥ `0.0122`. Final verdict is the OR (`degeneracy.py`).

`0.083` is the 99th percentile of 237 × 1024-token chunks of
Carroll + Darwin (mean `0.033`, p95 `0.063`, max `0.149`). It
replaced an intuition `0.50` that was six times too high and scored
an 18×-natural loop as “partly” degenerate. `0.0122` is the 99.9th
percentile of 20,730 natural chunk-pairs (reference median `0.000`,
including a single-topic Darwin book). Both are Stage 1 calibrations.
Stage 4 did not move them.

Regime: Stage 4 `chunk_size = 1024`, same as the calibration.
Stage 3’s 256-token mismatch does not apply. `W` and T are not in
the reference; they only set the post-horizon slice. Tokenizer
alignment is the residual gap: `scripts/calibrate_degeneracy.py`
defaults to Llama-3.1-8B; `or-qwen3-8b` chunks with Qwen3-8B. The
script claims word-level rates are insensitive; chunk *boundaries*
are tokenizer-defined. Not re-measured here. Not a reason to change
the bar: published scalars are not near the n-gram edge for any
cell count.

Sensitivity on published trajectory scalars (no per-chunk parquet
on this VM): moving only `loop_repetition_threshold` to `0.05` or
`0.15` would not flip any (W, T) cell. T≤1.0 is already 4/4 on the
fixed-point arm. T=1.5 `W=4096` max `looping_fraction` is `0.093`.
T=1.5 `W=8192` degeneracy is mode 2, not the 0.083 bar.

Near-edge Jaccard, for the record, not for a retune:

- clean, close from below: `W4096 T=1.5 physics s1` late median
  `0.00948` (threshold `0.0122`).
- degenerate, close from above: `W8192 T=1.5 physics s2` late median
  `0.0229`.

Flipping the first would take that cell from 0/4 to 1/4 degenerate;
`n_clean` would stay ≥ 2. Flipping the second would take `W=8192`
T=1.5 from 2/4 to 1/4. Neither inverts T≤1.0 4/4, F6 absent, or
“CIs exclude `α = 1`” at `W=4096`. Do not touch the threshold.

`degeneracy_verdicts.meta.json` (CLI dump) still describes only
0.083 + 50%. `looping_rate_vs_T.meta.json` states the OR. Before
the paper, make the degeneracy-table caption match the code. Not a
stage-reject: the REPORT and the headline figure already name mode 2.

### 5. T=1.5 “subdiffusive” is justified at `W=4096`; weaker at `W=8192`

From `clean_alpha_by_cell.csv`, recomputed from per-trajectory
`msd_alpha` on `degenerate = false` rows:

| space | W | n_clean | `α` | 95% CI | vs `α = 1` |
| --- | ---: | ---: | ---: | ---: | --- |
| bge-m3 | 4096 | 4 | 0.1485 | [0.140, 0.158] | excludes |
| bge-m3 | 8192 | 2 | 0.1463 | [0.086, 0.207] | excludes |
| qwen3-embed-8b | 4096 | 4 | 0.2772 | [0.241, 0.318] | excludes |
| qwen3-embed-8b | 8192 | 2 | 0.2470 | [0.172, 0.322] | excludes |

`W=4096` T=1.5 bge-m3 per-trajectory `α` is tight: 0.138, 0.142,
0.151, 0.164. That is a real subdiffusive cluster. `W=8192` T=1.5
clean bge-m3 is `0.207` (physics s1) and `0.086` (surreal s2). The
published CI is exactly `[min, max]` — a two-point bootstrap. It
excludes 1; it does not characterise a single exponent, and it does
not license a cross-`W` comparison. The report already says so.

Cross-space at `W=4096` T=1.5: CIs **do not overlap** (0.15 vs 0.28).
They agree on the sign (both exclude 1) and on F6. Do not average
them. A one-space result is not a result; a two-space disagreement
on *level* is a result about the spaces.

No cell reports `α` with `n_clean < 2`. T≤1.0 rows are
`alpha_defined = False`. F3/F4 held.

### 6. Two `α` estimands sit in `INDEX.md`

`clean_alpha_by_cell` is the F4 object. CLI `msd_loglog` at `W=8192`
reports ensemble `α = 0.205 ± 0.164` on **n = 16**, including the
14 degenerate trajectories. That is the Stage 1.0 trap in the
artifact index. The REPORT does not cite 0.205. The `msd_loglog`
limitations name finite lag and do **not** say the ensemble mixes
loops.

Do not cite the unprefixed `geometry-*/msd_loglog` exponent as a
Stage 4 result. The grid figure is the result. Same for s41
`α = 0.171 ± 0.086` (n = 8 = four T=0.7 locks + four T=1.5 clean).

### 7. Q4 is wrong, measured in-regime, and not softened

Quarter-4 fill from `protocol_by_quarter_cell.csv`:

| W | T=0.3 | T=1.0 |
| ---: | ---: | ---: |
| 4096 | 0.903 [0.753, 0.998] | 0.434 [0.241, 0.651] |
| 8192 | 0.980 [0.952, 1.000] | 0.745 [0.392, 0.981] |

Δ T=0.3 = 0.077 (inside 0.10). Δ T=1.0 = 0.311 (outside). Matches
REPORT §3. Each number is measured at its own `W`. The failed
object is the *transfer prediction*, which the plan flagged as the
mistake this project has already made. Scoring **Wrong** at T=1.0,
and calling the W-effect on fill “not a semantic result,” is the
correct pair of sentences.

Cell means hide a collapsed replicate (T=1.0 physics s2: Q4 fill
0.175 at 4096, 0.201 at 8192, 605 steps, $0.62 of $3.00). Named.
Do not quote the T=1.0 `W=8192` cell mean as “healthier fill”
without that row.

### 8. Q6 is wrong and not softened; T=1.5 `W=8192` is exactly on the F4 knife-edge

`n_clean = 4` at `W=4096` T=1.5; `n_clean = 2` at `W=8192` T=1.5.
Q6 predicted at least one cell with `n_clean < 2`. **Wrong.**
`n_clean = 2` is the minimum at which F4 calls `α` defined. The
report does not pretend otherwise.

### 9. “Clean ≠ left the register” is an existence proof, not a band census

Quoted T=1.5 late chunk (`W8192 T=1.5 physics s1`, chunk 94,
`degenerate = false`): product-pitch assistant, Polyakov-loop
toolkit, ZIP file. That one trajectory is still the help-assistant
register. Degeneracy is a surface-form verdict. The methodological
sentence holds.

Implication §7.3 and ADR-0015 write the stronger sentence: “the
T=1.5 residual is still the reviewer register.” Six clean
trajectories exist (four at 4096, two at 8192). One is quoted.
W=4096’s 4/4 clean band has no sample in the report. Do not put
the band-level wording in the manuscript until at least one more
T=1.5 late chunk is quoted, preferably a `W=4096` clean row.

The three required quotes are the right three *kinds* (lock,
mode-2 below the n-gram bar, clean-but-assistant). They are not a
register rate.

### 10. Seed-separation last-band excludes 0 in all 16 (W, T, space) cells

Including Q7’s `W=8192` T=0.3 cell (bge-m3 0.256 [0.249, 0.262];
qwen3-embed-8b 0.694 [0.693, 0.695]). Pairing is same-(W, T) only.
The tight intervals on locked cells are expected: within-seed
copies of a loop sit on top of each other. A positive gap on a
lock is “the seed still shapes the frozen page,” which is what
Stage 2 already said about qwen. The report refuses recovery and
refuses “semantic state.” Keep that refusal.

CLI `separation_per_band` under `separation-*/` pools four
temperatures inside one embed run. Band-12 bge-m3 gap `0.290` is
not any grid row. REPORT §2 already warns. Do not read the CLI
figure as Q7.

S4.1 T=0.7 last band is 10, not 12; S4.2 T=1.5 last band is 10.
Named. Weakest excluding-0 cell: `W=8192` T=1.5 bge-m3 gap 0.112
`[0.022, 0.224]`.

### 11. S2.2 reuse is the same protocol, two epochs

Eight raw cells from `s2-mechanism-20260901T071519Z-dfbb173a`,
T ∈ {0.3, 1.0}, `W=4096`. Prefill excluded. Matched: generator,
P1, `raw_completion`, `B = S = chunk = 1024`, 12 turnovers, seeds,
Alibaba pin, `reasoning_effort: none`, both embedders. ADR-0014
forbade regeneration. Correct.

Residual: S2.2 is 2026-09-01; S4.1/S4.2 are 2026-09-04/05. Same
pin, different days. Mild provenance confound. Not in §5. Not
enough to reopen those cells.

### 12. One process is named; do not let the shorthand drop it

PLAN §1, REPORT lede, ADR-0014, ADR-0015, threats §5: every
number is `or-qwen3-8b` under P1 `raw_completion`, Alibaba. Stage 2
already showed gemma-4-31b and gpt-oss-120b disagree with qwen.
No class-level sneak in the report or in ADR-0015.

Dangerous shortenings to refuse: “T=1.0 is a lock,” “temperature
does not unlock diffusion,” “qwen converges.” The subject is this
instruct process at these two windows.

ADR-0015’s S5 object (a) is phrased “surface-form attractor
occupancy.” Glossary: “Attractor” only with demonstrated timescale
separation. When the S5 PLAN is written, call it lock occupancy /
textual-fixed-point occupancy. Do not import H1 language onto a
surface loop.

### 13. Confounds: named set is enough to protect the headlines; a few are thin

Named and adequate: one process; n=4 / `[0, 1]` at T=1.5 `W=8192`;
n=2 bootstrap; H5 comparison undefined; degeneracy = surface form;
P1 re-prompt vs sliding attention; same-(W, T) pairing; two
tokenizer round-trip fails (S4.2 T=1.0 surreal s2 step 117; T=1.5
physics s2 step 36); provider non-determinism; `git_dirty` on
`s4-embed-w8192-20260905T090901Z-15172d14`; fill collapse as a
trajectory; stop-driven fill; embedding-space level disagreement;
reasoning tokens 0 on every completed step; F8 provider = Alibaba.

Under-weighted, not hidden enough to invert a headline:

- **`continuation_instruction`** on `/completions` (generator
  config: continue, don’t address the reader). Not in §5. Mild
  external force on a protocol that calls itself `unforced`.
- **Instruction-tuning confound** still open (S3.0 was a different
  family / scale / `W` / stack). S4 does not claim a cause.
- **Hand register not re-counted.** S2’s step-1 reviewer-register
  rate is not remeasured on the new cells.
- **Two semantic seeds only** (physics, surreal).
- **S4.2 resume / PID-kill operational history.** One `run_id`;
  twenty-odd sessions. Science is the checkpoints. Do not treat
  wall-clock mess as a second sample.

Forced continuation past stop is named where it is loud
(`W=4096` T=1.0 Q4 stop 0.954). That is the confound that has
already contaminated a result in this project. It does not create
the T≤1.0 degeneracy by itself: `W=8192` T=0.3 is 4/4 degenerate
at Q4 fill 0.980 and stop 0.327.

### 14. Spend cannot be reconciled on this VM

REPORT F10: hosted **$3.4383** (S4.1 $0.4379 + S4.2 $3.0004),
+$0.11 over the fill=0.65 authorised $3.33, under $7/run and $14
YAML. Project **$15.00 of $200**. This VM’s ledger is $9.0270
(s0+s1 only; zero `s4-*` rows). Same situation as Stage 3. I
accept F10 on the executor’s ledger. Do not let the project total
drift between reports without a ledger citation that exists on the
machine that writes the report. No third config. No ceiling raise.
S5 is not a generate-yes.

### 15. Q1 and Q3 are scored on intent, and that is fine

Q1 predicted “undefined **or** CI includes the T=0.3 value.”
Observed: defined, T=0.3 arm missing, CIs exclude `α = 1`.
“**Right as not-diffusion**” is the scientific reading, and the
unavailable arm is named. Do not upgrade it to “Q1 held literally.”

Q3 predicted overlapping looping CIs at matched T. T≤1.0: both
`[1, 1]`. T=1.5: `[0, 0]` overlaps `[0, 1]`. Procedurally **Right**.
The T=1.5 comparison has no power. The report’s “coin flip” clause
is what prevents Q3 from being read as “no W-effect at T=1.5.”

Q2 (T=0.3 fraction ≥ T=1.5) is trivially true (1 ≥ 0 and 1 ≥ 0.5).
Q8 (F6 same in both spaces) is true because both spaces have no
low-T clean-`α`.

### 16. Reserved words

REPORT does not call the loops attractors, does not say the
process “converges,” and refuses “semantic state” on the
separation gap. “Lock” is informal shorthand for the degeneracy
flag. Acceptable in the stage report; prefer *degenerate* /
*textual fixed point* in the manuscript, with the OR criterion
and a CI on the joint 24/24.

PCA/UMAP are labelled illustration. No cluster count from 2-D.

### 17. Master plan and ADR-0015 match the evidence

`docs/research-plan.md` S4 is current, S5 is **not opened**, and
the $200 ceiling is not a generate-yes. ADR-0015’s two objects —
(a) lock occupancy vs seed, (b) T=1.5 residual — follow from F5
and F4. Mixing them would be a new confound. Do not open S5 at
T=1.0 expecting a semantic basin. Do not jump to T=1.5 and call
it diffusion. Do not add a second generator because qwen loops
(Stage 2: gemma is silence). `n_macro` stays off.

---

## Claims I judge supported

- **On `or-qwen3-8b` under P1 `raw_completion`, T≤1.0 is 4/4
  degenerate at `W = 4096` and at `W = 8192`.** Six cells, 24/24,
  F5. Temperature does not unlock the surface loop until T=1.5,
  and at `W=8192` T=1.5 the looping rate is 2/4 with CI `[0, 1]`.
  `W` is not a lever on lock *rate* at T≤1.0.

- **Clean-`α` is defined only at T=1.5.** Both spaces, both
  windows. CIs exclude free diffusion (`α = 1`). At `W=4096`
  (n=4) the bge-m3 cluster is tight around 0.15. That is
  subdiffusion in the glossary sense (`α < 1`), not a confinement
  *mechanism*, and not diffusion. The report refuses the
  confinement reading (threats: “would need a different
  instrument”).

- **H5 is absent on this grid as F6’s undefined-comparison
  branch.** No low-T clean-`α`. Q5 **Right**. A later clean
  low-T cell can still show a transition.

- **Q4 is false at T=1.0.** Fill does not transfer across `W` at
  the temperature that already collapses fill. Measured at both
  windows. Not a semantic result.

- **Q6 is false.** Both T=1.5 cells have `n_clean ≥ 2`. Useful
  because it lets the stage *state* an `α` that is still not
  diffusion.

- **Clean is not “left the register,” as an existence claim.**
  Degeneracy missed the assistant/product-pitch register on at
  least `W8192 T=1.5 physics s1`. Surface-form ≠ semantics. This
  is why T=1.5 must not be sold as a healthy semantic regime.

- **Seed identity still shapes the locked trajectory after 12
  turnovers at `W=8192` T=0.3**, both spaces, CIs exclude 0.
  Not recovery. Not a semantic state. Q7 **Right**.

- **Protocol integrity on the completed steps that were
  summarised.** Reasoning tokens 0; served provider Alibaba;
  two isolated round-trip fails counted. F8.

- **`n_macro` is not a Stage 4 order parameter.** F9.

- **S2.2 raw eight reused, not regenerated.** F2.
  `s2-mechanism-20260901T071519Z-dfbb173a`.

- **ADR-0015 follows.** S5 must not open at T=1.0 as a semantic
  operating point. Pick (a) or (b) in an S5 PLAN, estimate, wait
  for a generate-yes. This stage does not open S5.

- **One instance.** The supported claims are about this process
  at these two windows and four temperatures.

---

## Claims I judge unsupported or overreaching

- **Any sentence whose subject is “language models,” “instruct
  models,” or “qwen” as a family.** One generator, one provider,
  one protocol, two seeds.

- **“We measured H5 and it is absent.”** We could not form the
  low-T clean-`α` contrast. High-T diffusion is rejected where
  clean. Those are two sentences.

- **T=1.5 as a diffusion regime, an unlock, or a departure from
  the assistant register as a band.** `α` excludes 1; the one
  quoted clean chunk is still a toolkit pitch; `W=8192` looping
  CI is `[0, 1]`.

- **A W-effect, or no W-effect, on looping rate at T=1.5.**
  `[0, 0]` vs `[0, 1]`. No power.

- **Cross-`W` equality of clean-`α`.** n=2 at 8192; two-point
  CI; spaces disagree on level at 4096.

- **Ensemble MSD exponents in `INDEX.md` / `msd_loglog`
  (`0.205 ± 0.164` on 16 mixed trajectories; `0.171 ± 0.086` on
  8 mixed).** Those measure a mixture of loops and residual
  motion. They are not F4.

- **“The same lock” as a mechanism at T=1.0 across `W`.** Same
  degeneracy rate; different stop/fill. Forced continuation is
  the loud confound at `W=4096`.

- **Per-cell looping rate known to be exactly 1 (or exactly 0)
  because the bootstrap CI has width zero.**

- **A register *rate* at T=1.5, or a claim that all six clean
  trajectories were read.** One quote.

- **Instruction tuning as the cause of the register.** Not this
  stage; still open.

- **H1 / H4 / semantic states / basins.** Not measured. F9 held.
  ADR-0015 object (a) is occupancy of a *surface* lock if S5
  picks it, and must say so.

- **S5 generate, 16k/32k, a second generator, or a threshold
  change.** All parked or forbidden.

---

## The seven questions

1. **Does the conclusion follow?** Yes, for the sentences the
   report should be judged on. “T≤1.0 is 4/4 degenerate at both
   `W` on this process” follows from
   `looping_rate_by_cell.csv` (24/24), not from `[1, 1]`.
   “T=1.5 is the only defined clean-`α` and it is not diffusion”
   follows from `clean_alpha_by_cell.csv` (four defined cells,
   all `ci_high < 1`; twelve cells undefined). “H5 absent”
   follows from F6’s pre-registered undefined branch, not from
   an overlapping pair of clean exponents. “Q4/Q6 wrong” follows
   from the fill table and the `n_clean` column. “Clean ≠ left
   the register” follows from one quoted T=1.5 chunk as
   existence, not as a census. What would *not* follow: T=1.5
   as health, T=1.0 as a semantic basin, `W` as a semantic lever,
   a class-level lock.

2. **Thresholds calibrated?** `0.083` is p99 of 237 × 1024-token
   Carroll+Darwin chunks; `0.0122` is p99.9 of 20,730 natural
   pairs; `loop_chunk_fraction = 0.5` was raised after the
   per-chunk calibration. Stage 4 is at the calibration chunk
   size. The bar was not moved. It is not load-bearing for
   T≤1.0 (fixed-point arm). Tokenizer Llama-vs-Qwen is the
   residual, not a reason to retune. The collapsed bootstrap
   `[1, 1]` is an uncalibrated *interval*, not an uncalibrated
   threshold; treat it as presentation (observation 2). F4’s
   `n_clean < 2` rule is pre-registered and was not quietly
   lowered (`W=8192` T=1.5 sits on it).

3. **Regime?** The grid is the target regime: `or-qwen3-8b`, P1
   raw, `W ∈ {4096, 8192}`, T ∈ {0.3, 0.7, 1.0, 1.5}, 12
   turnovers, chunk 1024, both spaces. Fill at `W=8192` was
   measured, not imported from `W=4096` (Q4 failed). S3.0’s
   `W=256` / 1B base token-lock was not transferred. S2.2 reuse
   is the same protocol at the same `W` and T, different day.
   Degeneracy labels were joined before `α` is reported.
   Cross-`W` `α` comparison is at matched turnover, not matched
   token count — named in `clean_alpha_vs_T` limitations.
   Prefill was not imported from the 28-token probe.

4. **One instance?** Yes, and the report says so. Two windows,
   four temperatures, two semantic seeds, two stochastic ids,
   two embedding spaces, one generator, one provider. The one
   generalisation the design allows is “not a class property”
   by pointing at Stage 2’s disagreement. Everything else is
   this process.

5. **Confounds named?** Degeneracy, surface-form vs register,
   P1 vs sliding attention, same-(W, T) pairing, n=4 / n=2,
   fill collapse as a trajectory, stop-forced continuation,
   two round-trip fails, provider non-determinism, dirty embed
   tree, band truncation, one process, embedding-space level
   disagreement, reasoning tokens absent. Unnamed or thin:
   `continuation_instruction`, instruction-tuning still open,
   hand-register not re-counted on new cells, Llama-vs-Qwen
   calibration tokenizer, S2.2 epoch mixing, CLI ensemble MSD
   mixing loops. None of the thin ones invert a headline if
   the supported list above is what gets cited.

6. **Do the artifacts state what they cannot?** Gate: 60/60
   have a limitations line. Headline grid figures name real
   alternatives (wide CI; surface-form; finite lag; matched
   turnover ≠ matched tokens; fill is protocol not semantics).
   `looping_rate_vs_T` names the mode-2 path below 0.083.
   Degeneracy-table caption is incomplete (observation 4).
   `msd_loglog` limitations omit the degenerate mix
   (observation 6). CLI `seed_separation` limitations omit
   T-pooling (observation 10). PCA is illustration-only.
   Adequate for approval; fix the three caption leftovers
   before the manuscript, not by regenerating S2.2 or S4.

7. **Negative result softened?** No. Q4 **Wrong**. Q6 **Wrong**.
   “Clean is not left the register” is stated in the lede of
   the quotes section and again as surprise #2. F6 is the
   absent branch and §5 refuses to dress it up as a measured
   overlap. Q1 is not marked simply “Right.” The useful part
   of being wrong (fill transfer failed; T=1.5 produced an
   `α` that is still not diffusion) is named as useful, which
   is not hedging. Softening, if it appears later, will be
   upgrading T=1.5 into “the residual semantic regime” or
   T=1.0 into “standard sampling.” ADR-0015 exists to stop
   that. This review does too.

---

## Sign-off

The mechanical gate cannot pass on this VM (`runs/s4` missing).
The committed artifact bundles are self-contained, the
predictions are scored, Q4 and Q6 are not walked back, and the
scientific payload is supported by the tidy grid and the
quoted text:

On `or-qwen3-8b` under P1 `raw_completion`, T and `W` do **not**
move T≤1.0 off a surface lock (4/4 degenerate at both
`W ∈ {4096, 8192}`). T=1.5 is the only cell with a defined
clean-`α`; that exponent is subdiffusive in both spaces and
the one quoted clean chunk is still the assistant register.
H5 is absent because there is no low-T clean-`α`. The 0.083
bar stays. S5 does not open at T=1.0 as a semantic point, and
does not open at all from this review.

That is an APPROVED stage. A successful negative on the
temperature × window question for one instruct process. Merge
is the human’s, after `afterlife review --stage s4` exit 0 on a
machine that has the runs, and not from this file.
