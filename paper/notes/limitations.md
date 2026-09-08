# Limitations draft (S7 notes)

Order follows `.cursor/rules/50-paper.mdc`, then occupancy-
specific items from S5–S6 review.

1. **Re-prompt vs true sliding attention.** Protocol P1 re-encodes
   the last `W` tokens each step; positions restart. This is not
   KV-cache eviction under a sliding mask (ADR-0001). A local
   P1 vs sliding control was parked (ADR-0017), not measured in
   S6.
2. **Representation dependence.** Occupancy *signs* agree in
   `bge-m3`, `qwen3-embed-8b`, and `gemini-embed-001`. Gemini is
   closed and cannot prove architecture-independence. Gap *levels*
   differ (0.201 / 0.390 / 0.150). PCA is illustration only.
3. **Provider non-determinism and unknown quantization.**
   Generator pin is Alibaba for the occupancy process. Exact-match
   determinism in S2 was not 100% on qwen. Embed `cost_usd=0`
   because RouterAI usage/yaml price were empty.
4. **Finite trajectories.** Occupancy is 12 turnovers at `W=4096`.
   Asymptotic claims are out of scope.
5. **Metastability vs lock.** S3 found no validated MSM
   macrostate. A textual repetition lock is not a semantic basin.
6. **One generator, one protocol, one lock operating point.**
   `or-qwen3-8b`, P1 `raw_completion`, Alibaba, T=0.3, `W=4096`,
   `B=1024` for S5–S6. S2 already showed other generators disagree.
7. **n=2 per seed.** F6 is underpowered. Twins are not one-fact
   pairs. Published twin CIs are not bootstrap intervals (ADR-0019).
8. **F4 lower bound and physics s1.** Gemini last-band gap 0.150
   [0.029, 0.266] on n=20, `n_within_pairs=9`. Reused S2.2 physics
   s1 has 47 chunks vs 48; last-band `D_within` diagonal is NaN.
9. **F6 no detected divergence ≠ one lock.** Point Δ only; CIs
   withheld. Do not narrate the S5 `bge-m3` point-Δ≈0.05 story as
   gemini’s.
10. **Degeneracy is the sample.** Thresholds 0.083 / Jaccard
    0.0122 from Carroll+Darwin. love s1 is kept.
11. **No hosted base model.** S0/ADR-0006. Instruction-tuning
    and register/persona remain alternative accounts of F4.
12. **Forced continuation.** Externally sustained self-conditioning
    after repeated termination attempts. EOS-as-absorbing is Paper B.
13. **Occupancy replication (ADR-0022).** A new 28-trajectory generate
    is not a restore of the named S5/S6 run directories. Last-band
    `n_within_pairs=6` (four domain trajectories have 47 chunks). Sign
    agrees with archival `0.201 [0.065, 0.332]`; do not replace that
    interval. Band 10 (80/1440) is not the pre-registered F4 number.
