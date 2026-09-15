# ADR-0025: Persistence metrics and the horizon ladder

Status: accepted
Date: 2026-09-09
Stage: S8+ (estimators); L2 confirmatory only at S12
Depends on: [ADR-0023](ADR-0023-paper-b-local-four-family.md) Freeze F1–F4

## Context

Paper A last-band F4 is an ensemble domain gap on 12 turnovers. The
library has no `P(lock by t)`, no semantic-half-life CLI, and no
prefix lock/escape machine. Naive extension to \(T = 5\times 10^6\)
breaks late-window Jaccard, pooled recurrence, and
`pairwise_distances`. A last band at turnover 1220 is a different
estimand than band 12 of 12.

Paper B’s headline is not “19/20 locks” and not MSM. This ADR freezes
the dependent quantities and the three horizon levels **before** S9
generate. Wave 1 implements them (`persistence.py`,
`afterlife analyze persistence`). Formulas land in
[`methodology.md`](../methodology.md) with the code, not in this
kickoff’s harness pass.

## Decision

### 1. Observation hierarchy

```
seed → descendant → chunk
```

- \(\binom{4}{2}=6\) within-seed distances are **not** six independent
  observations. They share four trajectories.
- Headline uncertainty: **seed-cluster bootstrap** — resample seeds;
  inside a chosen seed, resample descendants with multiplicity. Do
  not resample chunks. Do not treat 40 trajectories as iid Bernoulli.
- Kaplan–Meier / hazard: descriptive (no CI) or seed-cluster
  bootstrap. Greenwood on “40 iid traj” is forbidden.
- LOO-by-seed remains headline robustness for \(G_t\).
- Pair-cell randomization is calibration, not an inferential p-value.
- Plug-in MI seed↔fingerprint is **not** headline. At 40 trajectories
  and nearly unique fingerprints it is upward-biased. Exploratory
  only, with permutation / finite-sample correction, appendix.

Do not call the result semantic-domain memory. The object is
**seed-conditioned ensemble persistence in representation space**.

### 2. Confirmatory estimands (order is part of the claim)

Locked in ADR-0023 F4. Restated so analysis code cannot invert them.

**L0 (S9–S11), confirmatory, in this order:**

1. \(G_t = d_{\mathrm{between}}(t) - d_{\mathrm{within}}(t)\)
   versus turnover, in both primary local spaces, seed-cluster
   bootstrap, LOO.
2. \(\tau_{\mathrm{lock}}\) / prefix lock dynamics (time to confirmed
   lock; counts by seed: 4/4, 3/4; fraction of seeds with ≥1 and ≥3
   locks). Not a population binomial on 40 “iid” trajectories.
3. Fingerprint agreement: recurrent-fingerprint counts; how a seed’s
   descendants sit on fingerprints; within-seed vs between-seed
   agreement. A fingerprint is **not** a semantic state.

**L2 (S12 only), confirmatory:**

1. \(\tau_{\mathrm{escape}}\) — time from confirmed lock to confirmed
   escape, censored at the common token horizon \(T_{\min}\).

L2-persistence-to-lock (\(\tau_{\mathrm{lock}}\) on a long unlocked
arm) is optional and separate. It does not promote F4. It does not
share a survival table with \(\tau_{\mathrm{escape}}\).

### 3. Prefix lock/escape state machine

One construct on the way in and the way out (ADR-0023 F1):

```
unlocked → locked → escaped
```

- **Lock:** the L0 degeneracy classifier (looping / late Jaccard /
  entropy — not a new hash test). Confirm: ≥ `N_confirm=3` consecutive
  turnovers `degenerate=true`.
- **Escape:** the same classifier is `degenerate=false` for ≥ 3
  consecutive turnovers after a confirmed lock. Not one turnover and
  not a `sha256` change.
- **Exact-cycle hash** (window sha256 / period-k fingerprint):
  diagnosis of *exact-cycle mutation* only. If the hash changes and
  degeneracy still locks, that is a cycle mutation, not an escape.

No column, figure title, or report sentence may call the lock
**absorbing**. Forbidden language: “absorbing state”,
\(P(\mathrm{escape})=0\), “the lock is absorbing”. Allowed: *no
confirmed escape through \(T\) tokens / \(T/W\) turnovers*; term:
**long-lived repetition lock**.

Sparse embed after confirmed lock: 1 chunk per turnover plus a full
dump when the period-hash changes (diagnosis). Do not embed thousands
of near-identical lock chunks.

### 4. Horizon ladder (token horizon is the scientific axis)

Three levels, fixed before generate:

| Level | Horizon | Who | Confirmatory? |
| --- | --- | --- | --- |
| **L0** | \(R=12\), \(T=49152\) | all 10 conditions | \(G_t\), \(\tau_{\mathrm{lock}}\), fingerprint agreement |
| **L1** | \(R=48\), \(T\approx 196608\) | only if L0 justifies; Qwen Base+Instruct and at most one other family | exploratory unless a later ADR promotes it |
| **L2-escape** | up to \(T=5\times 10^6\) on a tiny locked cohort | after S9–S11; F3 seed rule; ≤ 2 ckpt × 2 locked seeds × 2 descendants = 8 | \(\tau_{\mathrm{escape}}\) only |
| **L2-persistence-to-lock** | same long \(T\), unlocked process | only if L0 has almost no locks on that checkpoint | \(\tau_{\mathrm{lock}}\); own PLAN paragraph, own table, own `run_id` |

L1 is a supervisor decision after S9, not an executor default.

**Censoring.** The scientific axis is the achieved **token** horizon.
A wall-clock cap may stop the machine; the report is then PARTIAL at
\(T_{\min}\). Forbidden: “14 days, whoever finished”. Within a
contrast, compare groups only up to the common achieved \(T_{\min}\).
Inside a checkpoint, run L2 round-robin by steps/blocks so no
trajectory races ahead.

L2 analysis is two survival tables, not a last-band at turnover 1220.
For comparison with L0, recompute turnover 12 on the same L2 ids
(internal replication). Do not treat L2 last-band as S5 band 12.

### 5. Log-turnover bands

Default `turnover_bin = 2.0` at 1220 turnovers would invent ~610
bands. Forbidden on L2. Use **log-spaced** turnover bands (and
lock-relative time) before any L2 code path. L0 may keep the 12-step
comparable grid; do not silently reuse `turnover_bin=2` on long \(T\).

### 6. L2-safe geometry (implementation constraints)

When Wave 1 writes the pass:

- No pooled recurrence across all chunks × all trajectories.
- Late Jaccard on L2: prefix lock-time plus a subsampled late window
  (e.g. 64 chunks), not the full half-series on 4883 chunks.
- Separation: log-bands + last-band only; do not join L2 pairs into
  the L0 400-trajectory parquet.
- MSM / VAMP / pooled Leiden: do not reopen H1 on an L2 locked
  subset. MSM only if degeneracy rate < 50% on that checkpoint.
- No `afterlife analyze half-life` promise. Headline is \(G_t\) and
  lock hazard, not \(T_{1/2}\).
- Ultra-long response cache: `steps_only`. JSONL is enough to resume.

### 7. What is not confirmatory (until a new ADR *before* analysis)

Native-chat Δ; INT8 vs NF4 concordance (report in limitations);
period-hash mutations; MI; MSM; MSD α; L1 48W; L2-persistence-to-lock;
Gemma “sliding 1024 caused it”.

## Alternatives considered

- **5M as the primary horizon for all ten checkpoints.** Rejected:
  wall-clock (~years) and incomparable to S5/S6.
- **One L2 cohort mixing locked Instruct and unlocked Base.**
  Rejected: \(\tau_{\mathrm{escape}}\) and \(\tau_{\mathrm{lock}}\)
  are different estimands.
- **Greenwood CI on 40 trajectories.** Rejected: descendants are not
  iid.
- **Headline MI.** Rejected: finite-sample bias.
- **Absorbing-state language from 12W locks.** Rejected: 12W cannot
  establish \(P(\mathrm{escape})=0\); ADR-0019 already parked
  EOS-as-absorbing.

## Consequences

- S9–S11 PLAN files must score F4 estimands in the F4 order. Extra
  figures are exploratory.
- S12 PLAN has a \(\tau_{\mathrm{escape}}\) table and, only if
  opened, a separate persistence-to-lock table.
- Column names and captions may not contain `absorbing`.
- Seed-bank rationale must not claim identification of semantics vs
  register ([ADR-0026](ADR-0026-seed-bank-v1-rationale-not-identification.md)).

## Reversal cost

Changing \(G_t\), the state machine, `N_confirm`, or the L2 seed rule
after seeing S9–S12 is a new ADR and exploratory reclassification.
Reverting before S9 generate is cheap.
