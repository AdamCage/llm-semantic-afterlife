# Stage 7 — scientific review brief

**Role.** Scientific supervisor. Follow
`.cursor/skills/stage-review/SKILL.md` and
`.cursor/rules/70-roles-and-branches.mdc`, with the **gate
exception** in §1 below. Chat with the human in Russian if you
reply in the conversation; write `REVIEW.md` in English.

**You are not the executor.** Do not rewrite `paper/main.tex`
during review. Do not generate, embed, retune thresholds, mint
`runs/s7`, add `configs/stages/stage7_*.yaml`, or merge.

Branch: `cursor/stage-7-6dce` (from `main` `ad1f244`).
HEAD at brief time: `ec85dda`. CI on that commit: 6/6 green.
Human yes on `paper/main.tex` already received.

---

## 1. Gate exception (read this first)

```bash
afterlife review --stage s7
```

This **exits 1**. The only FAIL is `runs.complete` (no
`runs/s7/`). That is by design: S7 is a writing stage
([ADR-0018](../../decisions/ADR-0018-s7-manuscript-from-closed-stages.md);
[`REPORT.md`](REPORT.md)). Do **not** return the work to the
executor for a dummy generate run. Do **not** stop the review.

Treat as already settled (do not re-derive):

| Check | Status | Meaning |
| --- | --- | --- |
| `plan.exists` | PASS | PLAN has exit criteria, predictions, budget |
| `runs.complete` | FAIL | expected; no generate directory |
| `artifacts.bundle` | PASS | S7 inventory bundle complete |
| `budget.reconciled` | PASS | stage $0.00; project $16.34 of $200 |
| `report.diagnostics_segmented` | PASS | fill/stop inherited from S5 last quarter |
| `report.quotes_text` | PASS | three last-chunk samples |
| `report.scores_predictions` | PASS | F1–F10 and Q1–Q8 scored |
| `literature.verified` | PASS | zero `` `LEAD` `` in related-work |

Occupancy **numbers** (F4/F6 CIs, 19/20 lock, 0.083 / 0.0122) were
already judged in S5 and S6 reviews. Do not re-bootstrap them.
Judge whether **`paper/main.tex` sentences** match those already-
closed artifacts.

---

## 2. Question this review answers

Can a TMLR-shaped manuscript be assembled from the closed S0–S6
record **without exceeding** what those artifacts establish,
including the negatives?

If yes: **APPROVED** or **APPROVED WITH CHANGES** (reword only).
If the paper sells H1, H5, architecture-independence, one lock,
a basin, or language models as a class: **REJECTED**.

Do not merge from this review. Stage close is a later human
command (`--no-ff` into `main`).

---

## 3. Read in this order

1. This brief.
2. [`PLAN.md`](PLAN.md) — **before** the paper. Predictions Q1–Q8
   and forbidden claims are the contract.
3. [`paper/notes/claims.md`](../../../paper/notes/claims.md) —
   allowed vs forbidden sentences, registered before TeX.
4. [`paper/notes/limitations.md`](../../../paper/notes/limitations.md).
5. **`paper/main.tex`** (the object). Then [`paper/refs.bib`](../../../paper/refs.bib).
6. [`REPORT.md`](REPORT.md) §1 and §3 (executor's self-score).
7. Figure `.meta.json` limitations for every
   `\includegraphics` in the paper (inventory:
   [`artifacts/stage-7/manuscript/figure_inventory.csv`](../../../artifacts/stage-7/manuscript/figure_inventory.csv)).
8. [ADR-0018](../../decisions/ADR-0018-s7-manuscript-from-closed-stages.md)
   and S6 [`REVIEW.md`](../stage-6/REVIEW.md) (the last scientific
   close; two blockers were reword, not a new run).

Do not start at the REPORT. Do not start at the abstract.

---

## 4. What to judge (the seven questions, applied to prose)

Spend attention only here. Any **no** is blocking.

1. **Does the sentence follow from the cited artifact?** Same-line
   `% artifacts/… @ run_id` is necessary, not sufficient. Read the
   sentence next to the CSV/figure and ask what else could produce
   that number. Example: last-band CI including 0 does not support
   “replicas occupy one lock.” Gemini lower CI 0.029 does not
   support “thick robustness” or architecture-independence.
2. **Are thresholds still the calibrated ones?** Degeneracy remains
   3-gram Jaccard **0.083** / late Jaccard **0.0122**. They must
   not have moved. F4 “separated” = last-band CI excludes 0 from
   above. F6 “collapsed” = last-band Δ CI includes 0. Those
   operational rules are not equivalence tests.
3. **Regime.** Occupancy sentences must stay on `or-qwen3-8b`, P1
   `raw_completion`, T=0.3, `W=4096`, 12 turnovers, 28 trajectories.
   S2 gemma 0/8 and S4 T=1.5 0/4 looping are **other regimes**. S3
   local `gemma-3-1b-pt` is `W=256`. None of those may be sold as
   the occupancy result.
4. **One instance.** The paper must not generalise to “instruct
   models” or “language models.” S2 already falsifies universality
   of the lock.
5. **Named confounds.** P1 vs sliding (parked, ADR-0017); degeneracy
   as the sample (19/20); P1 fill/stop in the last quarter (0.853 /
   0.359 on `domain_20`); provider non-determinism (qwen 60%
   exact-match in S2); physics s1 47 vs 48 chunks (last-band
   `D_within` NaN, `n_within_pairs=9`); love is **inside** the ten
   F4 domain seeds (1/2 lock), not a held-out class.
6. **Limitations vs captions.** Paper §Limitations must name
   alternatives the figures fail to exclude, not restate captions.
   Check each included figure's `.meta.json` `limitations` still
   bound the paper's caption.
7. **Negatives not softened.** H1 unsupported, H5 absent, gemini
   whisker, F6 ≠ one lock. Hedging (“suggests metastability”,
   “robust across architectures”, “collapsed onto a shared basin”)
   is worse than a plain negative.

---

## 5. Hunt list (blocking if present as a claim)

These sentences **cannot** appear as established findings:

- H1 established; “metastable semantic states” as a result
  (title/abstract especially; S3 `validated=0` is the record)
- H5 present; confinement→diffusion temperature transition
- Gemini proves architecture-independence
- Last-band collapsed = occupancy of one lock
- Gemini F4 is a thick robustness margin (lower bound **0.029**)
- A lock is a semantic basin; `n_macro` is an order parameter
- The result holds for language models as a class
- P1 vs sliding was measured
- MSM / half-life / probability currents / cross-model basins
  written as if measured (50-paper.mdc is a checklist to
  **confront**, not a ToC to fill — ADR-0018)
- Holtzman, Shumailov, or any non-VERIFIED citation
- Degenerate-row MSD α sold as confined semantic motion
- Cluster count or statistical claim from a 2-D projection
  (the gemini last-band matrix is pairwise distances, not k)

Q2 check: three-space **sign agreement** must be a results
subsection, not the title claim. Current title is lock occupancy
after eviction; gemini is §Stage 6. Judge whether the **abstract**
still over-weights the three-space sentence relative to the
whisker.

Q3 check: title/abstract must not present “metastable semantic
states” as a finding.

---

## 6. Headline numbers (do not re-derive; check the paper matches)

Same 28 `or-qwen3-8b` P1 traj, `W=4096`, T=0.3, 12 turnovers.
Generate: `s5-lock-occupancy-20260905T164327Z-6780902f`.
Gemini embeds: `s6-embed-third-space-20260906T082301Z-588eff8f`,
`s6-embed-third-space-20260906T082628Z-9077d587`.

F4 last-band, ten domain seeds, n=20, `n_within_pairs=9`:

| space | gap | 95% CI | separated |
| --- | ---: | --- | --- |
| `bge-m3` | 0.201 | [0.065, 0.332] | yes |
| `qwen3-embed-8b` | 0.390 | [0.151, 0.593] | yes |
| `gemini-embed-001` | 0.150 | [0.029, 0.266] | yes |

F6 last-band Δ (operational collapsed = CI includes 0):

- gemini all −0.012 [−0.286, 0.223]
- reactor 0.008 [−0.071, 0.087]
- waterloo gemini last −0.031 [−0.286, 0.223]
- waterloo gemini band 0 0.033 [0.001, 0.065] → sign flip

CSV: `artifacts/stage-6/occupancy/domain_separation_last_band.csv`,
`twin_last_band.csv`, `twin_per_band.csv`.

S3: `validated=0` every cell in
`artifacts/stage-3/dynamics/k_stability.md`.
S4: T≤1.0 both W 4/4 looping; T=1.5 `W=4096` 0/4; H5 absent.

---

## 7. Related work (honesty, not completeness)

Cite only VERIFIED entries in
`docs/literature/related-work.md`. The paper should:

- Treat Zekri et al. as the **unique stationary** null, not as
  licence for several token-level stationary measures.
- Not import Wang cycles or Ko & Geiping interlocutor attractors
  as findings about this P1 afterlife.
- Not claim novelty for “attractors in LLMs” or “tracking
  embeddings over time.”

Author lists in `paper/refs.bib` were checked against arXiv/ACL
records. Spot-check; invented authors are a defect.

---

## 8. What not to spend budget on

- Re-running generate/embed
- Recalculating CIs
- `ruff` / CI / same-line comment presence (lexical tests exist)
- Compiling PDF (`pdflatex` may be absent; source is the
  deliverable)
- Opening parked arms (T=1.0 occupancy, T=1.5 residual, 200 seeds,
  second generator, MSM, P1 vs sliding)
- Style, venue formatting, author affiliation taste — unless a
  sentence becomes a scientific claim

---

## 9. Deliverable

Write **`docs/stages/stage-7/REVIEW.md`** in the skill template:

```
# Stage 7 review
Reviewer: <model/agent>   Date: YYYY-MM-DD
Gate: FAIL runs.complete (expected writing-stage; see this brief §1)
Verdict: APPROVED | APPROVED WITH CHANGES | REJECTED
```

Include:

- Answer to the stage question in one paragraph
- Blocking findings (numbered; each names the **sentence**, the
  **problem**, and what would **resolve** it: reword / cut /
  cannot resolve without a new arm — and if the last, the arm is
  **not** S7)
- Non-blocking observations
- Claims judged supported (so the executor does not relitigate)
- Claims judged unsupported or overreaching

**Do not merge. Do not close the stage.** Return the REVIEW.md
and stop. APPROVED WITH CHANGES means executor rewords on this
branch; then human close.

---

## 10. Paste block for a new supervisor agent

```
You are the scientific supervisor for Stage 7 of llm-semantic-afterlife.
Follow docs/stages/stage-7/REVIEW-BRIEF.md exactly, then
.cursor/skills/stage-review/SKILL.md (seven questions), with the
gate exception in the brief: afterlife review --stage s7 FAILs
runs.complete by design — do not stop, do not mint runs/s7.

Object: paper/main.tex on branch cursor/stage-7-6dce.
Judge whether every sentence follows from closed S0–S6 artifacts.
Do not rewrite the paper. Do not generate. Do not merge.
Write docs/stages/stage-7/REVIEW.md and stop.
```
