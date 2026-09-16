# Task — scientific supervisor, Stage 9

You are the **scientific supervisor**, not the executor. Skill:
`.cursor/skills/stage-review/SKILL.md`. Contract:
`.cursor/rules/70-roles-and-branches.mdc`. Chat with the human in
**Russian**; write `REVIEW.md` in **English**.

Do not re-derive what the mechanical gate checks. Do not start S10.
Do not write `paper/main.tex`. Do not edit
`.cursor/plans/paper_b_local_matrix_5105e6af.plan.md`. Do not change
F1 thresholds or `N_confirm=3`. Do not generate, embed, or rerun
persistence. Do not rewrite executor code; report and return.
Do not merge to `main` unless the verdict is APPROVED **and** the
human explicitly authorises the `--no-ff` close.

---

## 0. Gate first

```bash
# WSL Ubuntu, not docker-desktop
export UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife
export AFTERLIFE_BUDGET_USD_TOTAL=200
cd /mnt/c/projects/llm-semantic-afterlife
uv run afterlife review --stage s9 --json .cache/review-s9.json
```

Stage id is **`s9`**, not `9` (`runs/s9/` vs missing `runs/9/`).

If exit ≠ 0: **stop**. List the FAIL checks. Do not write scientific
prose. The executor already reported exit 0 on 2026-09-16; if you
see a fail, the tree changed.

If exit 0: treat plan / run completeness / hashes / artifact bundles
/ budget / scored predictions as settled.

---

## 1. Read in this order

1. [`PLAN.md`](PLAN.md) — **before** the report.
2. [`REPORT.md`](REPORT.md) §1 verdicts and §3 prediction table.
3. [`artifacts/stage-9/INDEX.md`](../../../artifacts/stage-9/INDEX.md),
   then the headline frames:
   - `artifacts/stage-9/gt_last_band/`
   - `artifacts/stage-9/gt_last_band_figure/`
   - `artifacts/stage-9/locks/` and `locks_by_seed/`
   - `artifacts/stage-9/protocol_by_quarter/`
   - `artifacts/stage-9/empty_completions/`
   - `artifacts/stage-9/degeneracy/`
4. The `.meta.json` **limitations** line on each of those.
5. ADR-0023, 0025, 0026, 0027 (not 0024 unless you need the loader).

Working tree: branch `stage-8` (S8+S9 live here). Executor REPORT and
persistence artifacts may be **uncommitted**. Review the files on
disk, not only `git log`.

---

## 2. Stage question (what you are deciding)

On local Qwen3-8B Base vs Instruct, P1 `raw_completion` /
`serialization: raw_bytes`, `W=4096`, `T=49152`, T=0.3:

does seed-conditioned late-regime persistence (\(G_t\), time-to-
confirmed-lock) differ between the pretrained checkpoint and its
instruction-tuned pair?

Either Base≈Instruct or Base≪Instruct is a successful stage.
This stage does **not** ask whether H1 holds. A lock is **not** a
semantic state and is **not** absorbing.

Executor headline (judge this sentence, do not rubber-stamp it):

> On completed 12W trajectories, Base and Instruct both form a
> long-lived repetition lock before or at the horizon, show no
> confirmed escape through 12W, and have positive last-band \(G_t\)
> in both embedding spaces. That is a Base≈Instruct finding (P8).

---

## 3. The seven questions

Any “no” is blocking. For each headline claim:

1. Does the conclusion follow from the evidence?
2. Is every threshold calibrated (F1 0.083 / 50% / `N_confirm=3`)?
3. Was the measurement taken in the regime it is applied to?
4. Is the claim generalised from one instance?
5. Is every confound named?
6. Do the artifacts say what they cannot establish?
7. Is a negative result being softened?

---

## 4. S9-specific things the executor cannot decide

Spend your attention here. These are not gate items.

1. **P2 vs P8.** Executor says P2 is “numerically true, dynamically
   false”: Base seed-level lock 9/10 vs Instruct 10/10 only because
   all four Base `recipe` cells died on empty completion. Completed
   Base seeds lock 9/9. Is “Base≈Instruct on completed cells” the
   right reading, or is selecting on completers the finding?
2. **Early lock.** \(\tau_{\mathrm{lock}} \in \{0.75, 1.00\}\) — lock
   confirmed *before or at* the horizon, then no escape through 12W.
   Does “late-regime persistence” still name this, or is it an early
   repetition lock that merely survives eviction?
3. **\(G_t > 0\) while the quotes are loops.** Love-s2 is
   “Let me know what you need!”; surreal-s1 is “interior of the
   interior…”. Does last-band \(G_t\) measure seed-conditioned
   register / loop-family separation, and does the REPORT say that
   loudly enough?
4. **Empty-completion attrition is unbalanced** (Base 9/40, Instruct
   2/40). Is E1/E2 PARTIAL enough, or does the contrast need a
   named selection model?
5. **Fingerprint agreement** was the third confirmatory name and was
   not computed. Is that a hole in E5/E6 or an allowed E6 choice
   (hash diagnostic only)?
6. **One family, one temperature, P1 raw_bytes, NF4.** May the
   REPORT speak of “post-training” as tested, or only of *this*
   Instruct pair on *this* stack?
7. **INT8 CIs that include 0.** Concordance (P7) vs a quiet third
   headline — is the wording tight enough?
8. **Hosted Qwen-embed $0** and larger \(G_t\) magnitude than BGE-M3.
   Sign agreement is claimed; magnitude is not. Confirm the REPORT
   does not smuggle a “Qwen-embed is stronger” claim.

---

## 5. Deliverable

Write [`REVIEW.md`](REVIEW.md) in this directory:

```
# Stage 9 review
Reviewer: <model/agent>   Date: YYYY-MM-DD
Gate: PASS (afterlife review --stage s9, exit 0)
Verdict: APPROVED | APPROVED WITH CHANGES | REJECTED

## Blocking findings
(numbered; claim + problem + what would resolve it)

## Non-blocking observations

## Claims I judge supported

## Claims I judge unsupported or overreaching
```

Be specific. “Needs more rigour” is not a finding.

- **APPROVED** — human may `--no-ff` merge when they ask. You still
  do not merge unless they say so.
- **APPROVED WITH CHANGES** — list the exact phrase or table edits;
  executor applies them; you do not edit REPORT yourself unless the
  human says to.
- **REJECTED** — stage stays open; S10 stays forbidden.

After writing `REVIEW.md`, tell the human the verdict in Russian,
in one paragraph, and stop.
