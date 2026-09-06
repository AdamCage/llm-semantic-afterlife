# Stage 6 — Does the occupancy sign survive a third embedding space?

**Status.** Opened 2026-09-06 on branch `cursor/stage-6-6dce`, after
Stage 5 closed APPROVED WITH CHANGES (`9cb2845`). Decision:
[ADR-0017](../../decisions/ADR-0017-s6-third-space-occupancy-robustness.md).
No generate. Embed **authorised and executed 2026-09-06**. REPORT
written. Scientific review: **APPROVED WITH CHANGES**. Sidecar prose
aligned; waiting on human `--no-ff` close.

## 1. Question

On the same 28 `or-qwen3-8b` P1 trajectories Stage 5 used (`W=4096`,
T=0.3, 12 turnovers), do the S5 occupancy *signs* hold in a third
embedding space: last-band domain gap CI excludes 0 (F4), and twin
last-band Δ CI includes 0 (F6 operational collapsed)?

This stage does **not** ask whether H1 holds. It does **not** treat
a lock as a semantic basin. It does **not** treat last-band collapsed
as occupancy of one lock. It does **not** regenerate. It does **not**
claim architecture-independence from gemini alone (closed model).
Degenerate rows stay the sample. Thresholds 0.083 / Jaccard 0.0122
are not moved.

## 2. Entry state

From [Stage 5 REPORT](../stage-5/REPORT.md),
[Stage 5 REVIEW](../stage-5/REVIEW.md), [ADR-0017](../../decisions/ADR-0017-s6-third-space-occupancy-robustness.md):

- F4: ten-domain last-band gap 0.201 [0.065, 0.332] (`bge-m3`) and
  0.390 [0.151, 0.593] (`qwen3-embed-8b`). Ensemble, not ten point
  attractors. `D_within` rose; `D_between` stayed high.
- F5: 19/20 domain traj, 10/10 seeds with ≥1 lock; love 1/2 kept.
- F6: last-band Δ CI includes 0 per family and pooled, both spaces.
  Waterloo point Δ stayed ~0.05; reactor never excluded 0.
- Reuse, do not regenerate:
  `s5-lock-occupancy-20260905T164327Z-6780902f` (24, $1.3385),
  `s2-mechanism-20260901T071519Z-dfbb173a` raw T=0.3 physics/surreal
  ×4. Embeddings already on disk: `bge-m3`, `qwen3-embed-8b`.
  Degeneracy: `s5-degeneracy-20260906T030145Z-deb4c3bd` plus S2.2
  labels.
- `gemini-embed-001` usable in S0 (dim 3072, L2-normalised,
  `cost_usd` 0 on the probe). Closed architecture.
- Project ledger **$16.34 of $200**.

## 3. Experiment matrix

**Zero new trajectories.** If PLAN prose and YAML disagree, **YAML
wins** for the embed config; generate from that YAML is forbidden.

| # | Pass | Config / source | What it adds | Trajectories | New tokens |
| --- | --- | --- | --- | ---: | --- |
| S6.0 | Reuse S5 grid | S5.1 + S2.2 T=0.3 four | text + two spaces + degeneracy | 28 existing | 0 generate |
| S6.1 | Third space | `configs/stages/stage6_third_space.yaml` | `gemini-embed-001` on those chunks | 28 (embed) | ~2.0M embed-in |

`B = S = 1024`, `chunk_size = 1024`, protocol P1, `forcing = unforced`.
F4 = ten domain seeds only. F6 = two twin pairs only.

S6.1 embed CLI reads **all** chunks on `--run`. S2.2 generate contains
16 cells (raw + prefill × T ∈ {0.3, 1.0} × physics/surreal × 2). Extra
gemini rows are unused by occupancy assemble, which still filters to
raw T=0.3 four. Do not regenerate S2.2 to avoid that surplus.

Not in this opening: provider replication, chunk `{512,2048}`, stride
`S`, forced vs unforced, local CPU, P1 vs sliding, T=1.0, T=1.5, 200
seeds, a second generator, MSM / `n_macro`.

## 4. Computations

Ordered. No generate. Degeneracy labels reused, not retuned.

1. **Do not** `afterlife generate --config configs/stages/stage6_third_space.yaml`.
2. After embed-yes: `afterlife embed --config configs/stages/stage6_third_space.yaml --run s5-lock-occupancy-20260905T164327Z-6780902f`.
   New embed `run_id` is expected (CLI has no resume). Do not mint a
   sibling if this one is still RUNNING.
3. Same config `--run s2-mechanism-20260901T071519Z-dfbb173a`. Second
   embed `run_id`. Occupancy assemble will keep only the four raw
   T=0.3 physics/surreal rows.
4. Extend `scripts/assemble_stage5_occupancy.py` (or a Stage 6 sibling)
   to join gemini as a third space. F4/F6 split unchanged. F6
   limitations: last-band CI∋0 is not occupancy of one lock.
5. Do not headline geometry `α`. Do not retune 0.083 / 0.0122.
6. `afterlife review --stage s6` must exit 0 before scientific review.

## 5. Exit criteria

Falsifiable, quantitative, fixed before any Stage 6 gemini vector
exists.

| # | Criterion | Threshold |
| --- | --- | --- |
| F1 | **No new generate** | zero new generate `run_id`s for this stage. Source ids named |
| F2 | **Gemini on S5.1** | embed COMPLETED; 24/24 S5.1 traj present in `gemini-embed-001` parquet |
| F3 | **Gemini on S2.2 four** | occupancy grid still 20 domain + 8 twin traj after join; physics/surreal present in gemini |
| F4 | **Domain last-band gap, third space** | `D_between − D_within` at last band on the ten domain seeds, trajectory-bootstrap 95% CI, `gemini-embed-001` — or marked undefined if `D_within` is missing |
| F5 | **Sign vs S5** | F4 separated? (CI excludes 0 from above) stated for gemini **and** compared to the two S5 spaces. Agreement of sign is the robustness claim; level may differ |
| F6 | **Twin last-band Δ, third space** | per family and pooled, gemini, same F6 rule as S5. Families split in prose. Collapsed ≠ sameness |
| F7 | **Thresholds unchanged** | 0.083 / late Jaccard 0.0122; degenerate rows kept; love s1 kept |
| F8 | **Closed architecture named** | report states gemini cannot alone prove architecture-independence |
| F9 | **No basin / `n_macro` / H1 / generate** | report does not call a lock a basin, does not headline MSM, does not regenerate |
| F10 | **Spend** | Stage 6 hosted spend ≤ YAML `budget_usd` ($2). Stop and ask before a second config or any generate |

A gemini F4 that *agrees in sign* with both S5 spaces is a robustness
result, not a recovered semantic state. A gemini F4 that *flips sign*
is a successful negative: the occupancy claim is representation-tied.

## 6. Pre-registered predictions

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| Q1 | Gemini last-band domain gap CI excludes 0 (same sign as both S5 spaces) | 0.60 | **Right.** 0.150 [0.029, 0.266]. See REPORT |
| Q2 | Gemini last-band twin Δ CI includes 0 for **reactor** (never excluded 0 in S5) | 0.55 | **Right.** 0.008 [−0.071, 0.087] |
| Q3 | Gemini last-band twin Δ CI includes 0 for **waterloo** (operational collapsed; point Δ need not be 0) | 0.50 | **Right** on last-band NHST. Point −0.031 |
| Q4 | Gemini F4/F6 last-band *signs* agree with both S5 spaces (Q1–Q3 jointly) | 0.50 | **Right.** |
| Q5 | Gemini gap *level* differs from both S5 spaces by > 0.05 (closed embedder, different dim) | 0.55 | **Right.** vs bge 0.051; vs qwen 0.240 |
| Q6 | Waterloo gemini point Δ at band 12 is within 0.10 of band 0 (contrast does not vanish) | 0.40 | **Right.** \|0.033 − (−0.031)\| = 0.064 |
| Q7 | Embed ledger cost is $0 because RouterAI `usage.cost` / yaml price are empty, as in S5 embed | 0.60 | **Right.** `$0.0000` |
| Q8 | No new generate `run_id` is minted | 0.90 | **Right.** Two embed ids only |

Q1 wrong is the interesting wrong: then S5 F4 is space-tied and S6
must say so. Q4 can fail while Q1 holds if only twins flip.

## 7. Budget and wall clock

`afterlife estimate` on 2026-09-06 printed **generate $1.06** /
stage budget $2 / project remaining $183.66
([`estimate-20260906.log`](estimate-20260906.log)). That print is
the cost of accidentally regenerating S5.1. **It is not authorised.**

Hand embed forecast (chunk_size 1024, fill irrelevant):

| source | chunks (approx) | tokens in | notes |
| --- | ---: | ---: | --- |
| S5.1 | 1152 | 1.180M | 24 traj × 48 |
| S2.2 full run | ~768 | 0.786M | 16 cells; assemble keeps 4 |
| **total gemini** | ~1920 | **~2.0M** | one space |

S0 gemini probe `cost_usd` was 0. Google catalogue embedding is often
~$0.15 / M; 2.0M × $0.15 ≈ **$0.30**. YAML refuse **$2**. Project
remaining **~$183.66 of $200**.

Wall clock: S5.1 bge+qwen embed was ~15 min with RouterAI 503s. One
space, ~1920 chunks, batch 16 → tens of minutes if the endpoint holds.
Stop and ask if wall > 4 h or empty embeddings.

Embed **authorised 2026-09-06**. The generate print remains
unauthorised.

## 8. Stage-specific risks

| Risk | Mitigation |
| --- | --- |
| Accidental `afterlife generate` on the YAML | F1, HANDOFF, YAML comment; estimate print is not a yes |
| Minting a second gemini embed `run_id` | inspect STATUS; CLI has no resume |
| Embedding S2.2 surplus as if it were F4 | assemble filter `is_raw_lock_trajectory`; F3 checks physics/surreal |
| Reading gemini agreement as architecture-independence | F8; closed model |
| Selling F6 collapsed as sameness | S5 REVIEW law; limitations line names the alternative |
| Pooling twins into domain `D_between` | F4 vs F6 split, same as S5 |
| Moving 0.083 because gemini disagrees | F7 |
| Kitchen-sink creep (provider, chunk, forced) | ADR-0017; backlog |

## 9. Definition of done

- [x] Human yes on the embed forecast (not the generate print)
- [x] Zero new generate `run_id`s
- [x] Gemini embed COMPLETED on S5.1 and S2.2 source runs
- [x] Occupancy assemble has three spaces; F4/F6 split held
- [x] `REPORT.md` scores F1–F10 and Q1–Q8
- [x] `afterlife review --stage s6` exits 0
- [x] Spend ≤ $2 hosted

