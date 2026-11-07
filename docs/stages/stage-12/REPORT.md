<!-- s12-research-draft -->
# Stage 12 report

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | Eight continuation runs, each named | PASS | `artifacts/stage-12/tau_escape/tau_escape.data.parquet` |
| E2 | Comparisons use T_min | PASS | T_min = 4999168 tokens (1220.5000 turnovers) |
| E3 | Round-robin within one 48-step slice | PASS | step spread 0 |
| E4 | Estimand is tau_escape with a censoring flag | PASS | `artifacts/stage-12/tau_escape/tau_escape.meta.json` |
| E5 | No confirmed escape through T where none was observed | PASS | table column `confirmed_escape_through_tmin` |
| E6 | Every generate step served locally | PASS | `providers` column |
| E7 | F1 looping flag, N_confirm=3 | PASS | same classifier as the L0 degeneracy runs |
| E8 | L1 not run; persistence-to-lock not run; families not pooled | PASS | this report |
| E9 | Generate spend $0 | PASS | summed `cost_usd` on completed steps |

## 2. Results

The clock is absolute turnovers from L0 token 0. The lock event is at 0.75. The L0 series ends at 12.0. The continuation series is joined at 12.25 through 1220.5. Censoring time is 1220.5 absolute, which is 1219.75 turnovers after the lock (4,996,096 tokens). T_min = 4,999,168 original tokens. All eight cells reached the same target (4834 steps, 4,950,016 additional tokens, absolute 4,999,168). T_min equals each cell's length. censored=True is right-censoring at that common stop. 0 of 8 cells have a confirmed escape through T_min. 8 of 8 have no confirmed escape through T_min. P1 reprompt, raw_bytes, local NF4. Native sliding attention was not measured. The label is the F1 chunk looping flag. Embedding geometry was not run. Eight cells only: Ministral 3 8B Base NF4 and Qwen3 8B Instruct NF4, temperature 0.3, W=4096. Families are counted, not pooled. physics and love are the F3 tie-break after every qualifying seed tied at tau_lock=0.75, not a domain sample. s1 and s2 are two L0 descendants, one new stochastic draw each. Every continuation chunk is looping (4834/4834, max non-looping run 0). Minimum 3-gram repetition is 0.9378 on qi-physics-s1 and at least 0.9528 on the other seven. The frozen 3-gram cut is unchanged. Printed quotes are Ministral physics only (mb-physics-s1 and mb-physics-s2). The counter is the unchanged L0 chunk-row rule (three chunk rows, not three integer windows of W). The non-looping run length is 0 on every joined series, so a blank tau_escape is not a hidden shorter break. N_confirm=3 is unchanged.

| cell | run_id | status | additional tokens | tau_escape | censored | escape through T_min |
| --- | --- | --- | ---: | ---: | --- | --- |
| mb-physics-s1 | `s12-paperb-l2-mb-physics-s1-20260926T000516Z-6c25fa59` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| mb-physics-s2 | `s12-paperb-l2-mb-physics-s2-20260926T113312Z-7922c7f0` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| mb-love-s1 | `s12-paperb-l2-mb-love-s1-20260926T120115Z-87d89c22` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| mb-love-s2 | `s12-paperb-l2-mb-love-s2-20260926T122833Z-ce475f0c` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| qi-physics-s1 | `s12-paperb-l2-qi-physics-s1-20260926T125607Z-b0af1ba5` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| qi-physics-s2 | `s12-paperb-l2-qi-physics-s2-20260926T132741Z-75a4c96c` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| qi-love-s1 | `s12-paperb-l2-qi-love-s1-20260926T135816Z-c9de2297` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |
| qi-love-s2 | `s12-paperb-l2-qi-love-s2-20260926T140850Z-dd90cb82` | COMPLETED | 4950016 |  | True | no confirmed escape through T_min |

## 3. Prediction vs outcome

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | A majority have no confirmed escape through T_min | 0.55 | True (8/8) |
| P2 | Thinking tokens stay 0 on completed steps | 0.80 | True (sum 0) |
| P3 | An empty-completion death is kept and is not relabelled as escape | — | 0 death(s); the escape flag comes from the looping series, not from the failure |
| P4 | L2-persistence-to-lock stays closed on these two checkpoints | 0.90 | not run |

## 4. Surprises

The continuations are flat loops, not near-misses at N_confirm.
E3's final step spread is 0 because every cell reached the target; earlier, mb-physics-s1 ran 1237 steps ahead before the rotator fix. That history does not change 0/8.

## 5. Threats to validity

The continuation is a reprompt of a tail, not native sliding attention. F1 is a surface-form looping flag, so a lexically varied but semantically static stretch counts as an escape. Degeneracy of the continuation is a separate run from the L0 degeneracy runs, joined only by the turnover clock. All eight cells reached the same target, so T_min equals each cell's length and censored=True is right-censoring at that common stop. Provider non-determinism was not re-measured on this horizon. Families are not pooled.

## 6. Cost

Forecast $0. Sum of per-step cost_usd = 0.0000.

## 7. Implications for the plan

S13 is not opened by this report. L1 and L2-persistence-to-lock stay closed.

## Diagnostics by segment

Block fill and stop rate by quarter of completed steps, not as a run-level mean.

### mb-physics-s1

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### mb-physics-s2

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### mb-love-s1

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### mb-love-s2

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### qi-physics-s1

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### qi-physics-s2

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### qi-love-s1

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

### qi-love-s2

| quarter | steps | block fill | stop rate |
| --- | ---: | ---: | ---: |
| 1 | 1208 | 1.0 | 0.0 |
| 2 | 1209 | 1.0 | 0.0 |
| 3 | 1208 | 1.0 | 0.0 |
| 4 | 1209 | 1.0 | 0.0 |

## Samples of generated text

Printed quotes are Ministral physics only (mb-physics-s1 and mb-physics-s2).

> mb-physics-s1 early: loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The P

> mb-physics-s1 middle: and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop i

> mb-physics-s1 late: generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurati

> mb-physics-s2 early: is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not 

> mb-physics-s2 middle: observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observa

> mb-physics-s2 late: trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial
