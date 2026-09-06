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
5. **Metastability vs fixed points.** S3 found no validated MSM
   macrostate. A lock (surface-form degeneracy) is not a semantic
   basin. Prefer “lock” and “last-band occupancy contrast.”
6. **One generator, one protocol, one lock operating point.**
   `or-qwen3-8b`, P1 `raw_completion`, T=0.3, `W=4096` for S5–S6.
   S2 already showed other generators disagree.
7. **n=2 per seed.** Twin last-band CIs are two pairs per family.
   Including 0 is not an equivalence test.
8. **F4 whisker and physics s1.** Gemini last-band gap 0.150
   [0.029, 0.266] on n=20, `n_within_pairs=9`. Reused S2.2 physics
   s1 has 47 chunks vs 48; last-band `D_within` diagonal is NaN.
9. **F6 collapsed ≠ one lock.** Gemini waterloo sign-flips from
   0.033 at band 0 to −0.031 at band 12. Do not narrate the S5
   `bge-m3` point-Δ≈0.05 story as gemini’s.
10. **Degeneracy is the sample.** Thresholds 0.083 / Jaccard
    0.0122 were calibrated earlier and not moved. love s1 is kept.
11. **No hosted base model.** S0/ADR-0006. S3.0 local gemma-3-1b-pt
    at `W=256` does not transfer to `W=4096`.
