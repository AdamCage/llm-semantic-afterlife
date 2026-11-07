# Stage 13 report — Paper B read from closed artifacts

Assembly run `s13-paperb-synthesis-20261107T085555Z-c0f6b853`. No new generation.

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | One S13 run at $0 and no new generate | PASS | `s13-paperb-synthesis-20261107T085555Z-c0f6b853` |
| E2 | Published G_t rows, families not pooled | PASS | `artifacts/stage-13/gt_published/gt_published.data.parquet` |
| E3 | Gemma Base BGE identified negative; Qwen-embed sign not established | PASS | `artifacts/stage-13/gt_nf4/gt_nf4.data.parquet` |
| E4 | S12 0/8 on its own table | PASS | `artifacts/stage-13/tau_escape_s12/tau_escape_s12.data.parquet` |
| E5 | Figure bundles carry the published scalar and its interval | PASS | `artifacts/stage-13/INDEX.md` |
| E6 | S13 ledger spend $0 | PASS | `s13-paperb-synthesis-20261107T085555Z-c0f6b853` |
| E7 | Four threats named below | PASS | section 5 |

## 2. Results

S9–S11 are the Paper B story. Each family keeps its own rows. The plotted quantity is the published last-band G_t in the original embedding space, with the published interval. Open markers are rows whose published `ci_excludes_0` is false. Missing markers are unidentified last bands (OLMo DPO NF4 in both spaces; Gemma IT in both spaces) and are not drawn as zero.

| stage | family | checkpoint | quantization | space | last_band_G | G_lo | G_hi | ci_excludes_0 | n_within_pairs | n_between_pairs | n_confirmed_escape | generate_run_id | source_artifact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s9 | Qwen3-8B | Base NF4 | nf4 | BGE-M3 | 0.147591 | 0.0691844 | 0.158049 | yes | 40 | 425 | 0 | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc | artifacts/stage-9/gt_last_band/gt_last_band.csv |
| s9 | Qwen3-8B | Instruct NF4 | nf4 | BGE-M3 | 0.151367 | 0.0871001 | 0.159001 | yes | 54 | 649 | 0 | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6 | artifacts/stage-9/gt_last_band/gt_last_band.csv |
| s9 | Qwen3-8B | Base NF4 | nf4 | Qwen3-Embedding-8B | 0.233299 | 0.117225 | 0.244196 | yes | 40 | 425 | 0 | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc | artifacts/stage-9/gt_last_band/gt_last_band.csv |
| s9 | Qwen3-8B | Instruct NF4 | nf4 | Qwen3-Embedding-8B | 0.304616 | 0.191654 | 0.315201 | yes | 54 | 649 | 0 | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6 | artifacts/stage-9/gt_last_band/gt_last_band.csv |
| s10 | OLMo-3-7B | Base NF4 | nf4 | BGE-M3 | 0.0943909 | 0.0287692 | 0.107647 | yes | 31 | 320 | 0 | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3 | artifacts/stage-10/gt_last_band/gt_last_band.csv |
| s10 | OLMo-3-7B | DPO NF4 | nf4 | BGE-M3 | — | -0.0742006 | -0.0742006 | no | 3 | 0 | 0 | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f | artifacts/stage-10/gt_last_band/gt_last_band.csv |
| s10 | OLMo-3-7B | RLVR NF4 | nf4 | BGE-M3 | 0.201503 | -0.134183 | 0.201503 | no | 3 | 3 | 0 | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc | artifacts/stage-10/gt_last_band/gt_last_band.csv |
| s10 | OLMo-3-7B | SFT NF4 | nf4 | BGE-M3 | 0.10178 | -0.0069993 | 0.121757 | no | 20 | 151 | 0 | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e | artifacts/stage-10/gt_last_band/gt_last_band.csv |
| s10 | OLMo-3-7B | Base NF4 | nf4 | Qwen3-Embedding-8B | 0.189111 | 0.0861319 | 0.221421 | yes | 31 | 320 | 0 | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3 | artifacts/stage-10/gt_last_band/gt_last_band.csv |
| s10 | OLMo-3-7B | DPO NF4 | nf4 | Qwen3-Embedding-8B | — | -0.130936 | -0.130936 | no | 3 | 0 | 0 | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f | artifacts/stage-10/gt_last_band/gt_last_band.csv |
| s10 | OLMo-3-7B | RLVR NF4 | nf4 | Qwen3-Embedding-8B | 0.334629 | -0.147232 | 0.334629 | no | 3 | 3 | 0 | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc | artifacts/stage-10/gt_last_band/gt_last_band.csv |
| s10 | OLMo-3-7B | SFT NF4 | nf4 | Qwen3-Embedding-8B | 0.1757 | 0.0342047 | 0.205525 | yes | 20 | 151 | 0 | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e | artifacts/stage-10/gt_last_band/gt_last_band.csv |
| s11 | Gemma-4-12B | Base | nf4 | BGE-M3 | -0.010628 | -0.0377395 | -0.00608505 | yes | 54 | 649 | 15 | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981 | artifacts/stage-11/gt_last_band/gt_last_band.csv |
| s11 | Gemma-4-12B | IT | nf4 | BGE-M3 | — | — | — | no | 0 | 0 | 4 | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427 | artifacts/stage-11/gt_last_band/gt_last_band.csv |
| s11 | Ministral-3-8B | Base | nf4 | BGE-M3 | 0.138297 | 0.0633819 | 0.158376 | yes | 60 | 720 | 0 | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b | artifacts/stage-11/gt_last_band/gt_last_band.csv |
| s11 | Ministral-3-8B | Instruct | nf4 | BGE-M3 | 0.150187 | 0.0840649 | 0.158143 | yes | 60 | 720 | 4 | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 | artifacts/stage-11/gt_last_band/gt_last_band.csv |
| s11 | Gemma-4-12B | Base | nf4 | Qwen3-Embedding-8B | 0.0141659 | -0.0208935 | 0.0186512 | no | 54 | 649 | 15 | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981 | artifacts/stage-11/gt_last_band/gt_last_band.csv |
| s11 | Gemma-4-12B | IT | nf4 | Qwen3-Embedding-8B | — | — | — | no | 0 | 0 | 4 | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427 | artifacts/stage-11/gt_last_band/gt_last_band.csv |
| s11 | Ministral-3-8B | Base | nf4 | Qwen3-Embedding-8B | 0.239919 | 0.126587 | 0.271944 | yes | 60 | 720 | 0 | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b | artifacts/stage-11/gt_last_band/gt_last_band.csv |
| s11 | Ministral-3-8B | Instruct | nf4 | Qwen3-Embedding-8B | 0.224079 | 0.139027 | 0.228082 | yes | 60 | 720 | 4 | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 | artifacts/stage-11/gt_last_band/gt_last_band.csv |

Gemma Base BGE is an identified negative: G_t = -0.010628, interval [-0.0377395, -0.00608505], `ci_excludes_0` yes. Gemma Base Qwen-embed is 0.0141659 [-0.0208935, 0.0186512], `ci_excludes_0` no, so that sign is not established. Cross-space sign agreement for Gemma is not identified. Source: `artifacts/stage-11/gt_last_band/gt_last_band.csv`, copied to `artifacts/stage-13/gt_published/gt_published.data.parquet`.

Completion counts are the published `generate_status.csv` rows. A failed cell stays in the sample. It is missing data, not an unlock. Run-level block-fill means in that file are not the claim.

| stage | family | checkpoint | n_completed | n_failed | generate_run_id | source_artifact |
| --- | --- | --- | --- | --- | --- | --- |
| s9 | Qwen3-8B | Instruct NF4 | 38 | 2 | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6 | artifacts/stage-9/generate_status/generate_status.csv |
| s9 | Qwen3-8B | Base NF4 | 31 | 9 | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc | artifacts/stage-9/generate_status/generate_status.csv |
| s9 | Qwen3-8B | Instruct INT8 | 9 | 1 | s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498 | artifacts/stage-9/generate_status/generate_status.csv |
| s9 | Qwen3-8B | Base INT8 | 8 | 2 | s9-paperb-qwen-base-int8-20260914T091655Z-11069a87 | artifacts/stage-9/generate_status/generate_status.csv |
| s10 | OLMo-3-7B | Base NF4 | 27 | 13 | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3 | artifacts/stage-10/generate_status/generate_status.csv |
| s10 | OLMo-3-7B | SFT NF4 | 19 | 21 | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e | artifacts/stage-10/generate_status/generate_status.csv |
| s10 | OLMo-3-7B | DPO NF4 | 3 | 37 | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f | artifacts/stage-10/generate_status/generate_status.csv |
| s10 | OLMo-3-7B | RLVR NF4 | 4 | 36 | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc | artifacts/stage-10/generate_status/generate_status.csv |
| s10 | OLMo-3-7B | Base INT8 | 5 | 5 | s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8 | artifacts/stage-10/generate_status/generate_status.csv |
| s10 | OLMo-3-7B | RLVR INT8 | 0 | 10 | s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca | artifacts/stage-10/generate_status/generate_status.csv |
| s11 | Ministral-3-8B | Base | 40 | 0 | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b | artifacts/stage-11/generate_status/generate_status.csv |
| s11 | Ministral-3-8B | Instruct | 40 | 0 | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 | artifacts/stage-11/generate_status/generate_status.csv |
| s11 | Gemma-4-12B | Base | 38 | 2 | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981 | artifacts/stage-11/generate_status/generate_status.csv |
| s11 | Gemma-4-12B | IT | 0 | 40 | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427 | artifacts/stage-11/generate_status/generate_status.csv |

S12 is not in the G_t table. 0 of 8 cells have a confirmed escape through T_min = 4999168 original tokens. The clock is absolute turnovers from L0 token 0. The lock event is at 0.75. The L0 series ends at 12.0. Censoring time is 1220.5, which is 1219.75 turnovers after the lock. Families are counted, not pooled. Source: `artifacts/stage-12/tau_escape/tau_escape.data.parquet`.

| cell | family | run_id | absolute_tokens | absolute_turnovers | tau_escape | censored | confirmed_escape_through_tmin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mb-physics-s1 | Ministral-3-8B | s12-paperb-l2-mb-physics-s1-20260926T000516Z-6c25fa59 | 4999168 | 1220.5 | — | yes | no |
| mb-physics-s2 | Ministral-3-8B | s12-paperb-l2-mb-physics-s2-20260926T113312Z-7922c7f0 | 4999168 | 1220.5 | — | yes | no |
| mb-love-s1 | Ministral-3-8B | s12-paperb-l2-mb-love-s1-20260926T120115Z-87d89c22 | 4999168 | 1220.5 | — | yes | no |
| mb-love-s2 | Ministral-3-8B | s12-paperb-l2-mb-love-s2-20260926T122833Z-ce475f0c | 4999168 | 1220.5 | — | yes | no |
| qi-physics-s1 | Qwen3-8B | s12-paperb-l2-qi-physics-s1-20260926T125607Z-b0af1ba5 | 4999168 | 1220.5 | — | yes | no |
| qi-physics-s2 | Qwen3-8B | s12-paperb-l2-qi-physics-s2-20260926T132741Z-75a4c96c | 4999168 | 1220.5 | — | yes | no |
| qi-love-s1 | Qwen3-8B | s12-paperb-l2-qi-love-s1-20260926T135816Z-c9de2297 | 4999168 | 1220.5 | — | yes | no |
| qi-love-s2 | Qwen3-8B | s12-paperb-l2-qi-love-s2-20260926T140850Z-dd90cb82 | 4999168 | 1220.5 | — | yes | no |

### Block fill and stop rate by quarter

First and final quarter of each NF4 cell, copied from `protocol_by_quarter.csv`. All four quarters are in `artifacts/stage-13/protocol_by_quarter/protocol_by_quarter.data.parquet`. A run-level mean is not the claim.

| stage | family | checkpoint | quarter | n_trajectories | block_fill_mean | stop_rate_mean | generate_run_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| s10 | OLMo-3-7B | Base NF4 | 1 | 40 | 0.84326 | 0.301923 | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3 |
| s10 | OLMo-3-7B | Base NF4 | 4 | 28 | 0.964964 | 0.0357143 | s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3 |
| s10 | OLMo-3-7B | DPO NF4 | 1 | 40 | 0.927975 | 0.375 | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f |
| s10 | OLMo-3-7B | DPO NF4 | 4 | 11 | 0.630341 | 0.636364 | s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f |
| s10 | OLMo-3-7B | RLVR NF4 | 1 | 40 | 0.83455 | 0.475 | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc |
| s10 | OLMo-3-7B | RLVR NF4 | 4 | 8 | 0.771625 | 0.4375 | s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc |
| s10 | OLMo-3-7B | SFT NF4 | 1 | 40 | 0.788674 | 0.410256 | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e |
| s10 | OLMo-3-7B | SFT NF4 | 4 | 22 | 0.943199 | 0.0738636 | s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e |
| s11 | Gemma-4-12B | Base | 1 | 40 | 0.929111 | 0.0732372 | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981 |
| s11 | Gemma-4-12B | Base | 4 | 38 | 0.996397 | 0.00438596 | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981 |
| s11 | Gemma-4-12B | IT | 1 | 40 | 0.754025 | 0.415923 | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427 |
| s11 | Gemma-4-12B | IT | 4 | 19 | 0.597854 | 0.549952 | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427 |
| s11 | Ministral-3-8B | Base | 1 | 40 | 1 | 0 | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b |
| s11 | Ministral-3-8B | Base | 4 | 40 | 1 | 0 | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b |
| s11 | Ministral-3-8B | Instruct | 1 | 40 | 0.934494 | 0.0666176 | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 |
| s11 | Ministral-3-8B | Instruct | 4 | 40 | 1 | 0 | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 |
| s9 | Qwen3-8B | Base NF4 | 1 | 40 | 0.773112 | 0.265604 | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc |
| s9 | Qwen3-8B | Base NF4 | 4 | 31 | 0.975478 | 0.05244 | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc |
| s9 | Qwen3-8B | Instruct NF4 | 1 | 40 | 1 | 0 | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6 |
| s9 | Qwen3-8B | Instruct NF4 | 4 | 38 | 1 | 0 | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6 |

## 3. Prediction vs outcome

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | No pooled family row | 0.90 | true |
| P2 | Gemma Base BGE identified negative; Qwen-embed CI does not exclude 0 | 0.95 | true |
| P3 | S12 flag false on 8/8 and absent from the G_t table | 0.95 | true |
| P4 | This command does not generate or embed | 0.99 | true |
| P5 | New prose avoids the banned phrases in `forbidden_prose` | 0.90 | true |

## 4. Surprises

The assembly did not change a published flag. The negative Gemma Base BGE gap and the OLMo completion collapse were already in the closed reports. OLMo SFT NF4 is positive in both spaces as a point; the BGE interval includes 0, so that BGE gap is not established. That reading is the S10 table, not a new estimand.

## 5. Threats to validity

P1 reprompt of a tail, raw_bytes, local NF4. Native sliding attention was not measured. Last-band G_t is seed-conditioned ensemble persistence in one embedding space. The two spaces are not on a common scale and are not pooled. Families are not pooled. A CI that includes 0 is not an established sign. An unidentified last-band is not a sign flip and is not drawn as zero. INT8 rows are concordance, not a third headline. Provider non-determinism was not re-measured on these horizons. L0 is finite: 12 turnovers, 49152 tokens. S12 is a separate censored count through 4999168 original tokens, not a pooled rate and not a permanence claim. Gemma Base BGE is an identified negative. The Gemma Base Qwen-embed sign is not established. Cross-space sign agreement for Gemma is not identified. Lock-table n is not the 12W completer count.

Qwen-embed for S9–S11 was the hosted endpoint at realised cost $0 (ADR-0027, ADR-0028, ADR-0029). BGE-M3 was local. The two pipelines are not one embedding measurement.

## 6. Cost

Forecast $0. S13 ledger spend on `s13-paperb-synthesis-20261107T085555Z-c0f6b853` is $0. No GPU generate.

## 7. Implications for the plan

S13 closes the stage ladder. There is no S14. L1 and L2-persistence-to-lock stay closed. After the gate exited 0, a Paper B section was appended to `paper/main.tex` and `paper/main.ru.tex`. Paper A sections were not rewritten.

## Samples of generated text

These lines are quotations of the closed S12 report. This stage did not generate them. They are Ministral physics only (`mb-physics-s1`, `mb-physics-s2`).

> Quoted from docs/stages/stage-12/REPORT.md. Printed there as Ministral physics only.
> mb-physics-s1 early: loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The P
> mb-physics-s1 middle: and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop i
> mb-physics-s1 late: generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurati
> mb-physics-s2 early: is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not in a trivial vacuum. The Polyakov loop is a gauge-invariant observable, and its expectation value is nonzero, so the system is not 

