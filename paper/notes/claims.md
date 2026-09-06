# Claim inventory (S7 notes)

Registered before `paper/main.tex`. Allowed = may appear in the
paper with the named artifact and `run_id`. Forbidden = a sentence
that would exceed the record.

## Allowed

| Claim | Stage | Artifact | `run_id` |
| --- | --- | --- | --- |
| P1 re-prompt is the protocol; not true sliding attention | S0 | `docs/stages/stage-0/REPORT.md`; ADR-0001 | `s0-live-smoke-*` (protocol, not a result) |
| No hosted base models on RouterAI | S0 | stage-0 REPORT E-findings | provider audit |
| Three embedders usable, L2-normalised: bge-m3 1024, qwen3-embed-8b 4096, gemini-embed-001 3072 | S0 | `s0_embeddings.csv` | S0 embedding audit |
| Seed identity past the horizon on the S1 ensemble, with 94% textual fixed point | S1 | `artifacts/stage-1/` | S1 generate/embed `run_id`s in stage-1 REPORT |
| Convergence past the horizon is not universal; gemma-4-31b dies into silence | S2 | stage-2 REPORT | `s2-model-axis-20260901T015457Z-ab59afc8` |
| Prefill does not remove the reviewer register on qwen | S2 | stage-2 REPORT | `s2-mechanism-20260901T071519Z-dfbb173a` |
| `validated_macrostates = 0` on the S3.1 sample; H1 unsupported there | S3 | stage-3 REPORT | S3.1 dynamics `run_id`s in that REPORT |
| Local gemma-3-1b-pt at W=256: 8/8 degenerate, 0/8 reviewer | S3 | `artifacts/stage-3/surface/` | `s3-local-base-20260901T184812Z-cc80633b` |
| T≤1.0 is 4/4 lock at W=4096 and W=8192 on or-qwen3-8b P1; H5 absent | S4 | `artifacts/stage-4/grid/` | `s4-w4096-new-temps-20260904T103121Z-589c8eb1`, `s4-w8192-20260904T120057Z-ce82ce55` |
| T=1.5 is the only clean-α band and is subdiffusive | S4 | stage-4 geometry artifacts | S4 embed/geometry ids in stage-4 REPORT |
| Ten domain seeds last-band gap 0.201 [0.065, 0.332] (bge-m3), 0.390 [0.151, 0.593] (qwen) | S5 | `artifacts/stage-5/occupancy/domain_separation_last_band.csv` | `s5-lock-occupancy-20260905T164327Z-6780902f` + S5 embeds |
| Domain lock 19/20 traj, 10/10 seeds; love 1/2 kept; 0.083 / 0.0122 unmoved | S5 | `artifacts/stage-5/occupancy/lock_rate_by_seed.csv` | `s5-degeneracy-20260906T030145Z-deb4c3bd` |
| Twin last-band Δ CI includes 0, both S5 spaces; waterloo bge-m3 point Δ ~0.05 | S5 | `artifacts/stage-5/occupancy/twin_last_band.csv` | same occupancy assemble |
| Gemini F4 0.150 [0.029, 0.266], separated; n=20, n_within_pairs=9; physics s1 last-band NaN | S6 | `artifacts/stage-6/occupancy/domain_separation_last_band.csv` | `s6-embed-third-space-20260906T082301Z-588eff8f`, `s6-embed-third-space-20260906T082628Z-9077d587` |
| Gemini F6 last-band Δ: all −0.012 [−0.286, 0.223]; reactor 0.008; waterloo −0.031; all CI∋0 | S6 | `artifacts/stage-6/occupancy/twin_last_band.csv` | same gemini embeds |
| Gemini waterloo band 0 Δ 0.033 [0.001, 0.065] → band 12 −0.031 (sign flip) | S6 | `artifacts/stage-6/occupancy/twin_per_band.csv` | same |
| Hosted project spend $16.34 of $200; S6 hosted $0 | ledger | `runs/_ledger/spend.jsonl` | — |

## Forbidden (do not write)

| Sentence that would exceed the record | Why |
| --- | --- |
| H1 is established; the model occupies a finite set of metastable semantic states | S3: no validated macrostate |
| H5: a temperature boundary separates confinement from diffusion | S4: H5 absent on the grid |
| Gemini proves architecture-independence of occupancy | closed model; F8 |
| Last-band collapsed twins occupy one lock | S5/S6: CI∋0 is operational collapsed |
| Gemini F4 is a thick robustness margin | lower bound 0.029; n_within_pairs=9 |
| A lock is a semantic basin; n_macro is an order parameter | S3–S6 law |
| The result holds for language models as a class | one instruct process, P1, Alibaba |
| P1 vs sliding was measured in S6 | parked (ADR-0017) |

Fill the Observed column of PLAN Q1–Q8 when the manuscript exists.
