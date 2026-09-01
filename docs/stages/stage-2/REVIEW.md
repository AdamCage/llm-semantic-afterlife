# Stage 2 review
Reviewer: Cursor Grok 4.6 (scientific supervisor)   Date: 2026-09-01
Gate: PASS (`afterlife review --stage s2`, exit 0; WARN: 1 LEAD citation)
Verdict: APPROVED

The stage is PARTIAL on its own exit criteria (F8 FAIL, F4 PARTIAL). That
is the correct stage verdict. This review does not upgrade it.

Do not merge to `main` from this review. The standing instruction is that
the human closes the branch.

## Blocking findings

None.

## Non-blocking observations

1. **Published `geometry_scalars` tables carry `n_chunks_x` / `n_chunks_y`.**
   The join of degeneracy onto geometry suffixed colliding columns. The
   report names this; the two counts agree; the CLI now drops the overlap
   before joining. Regenerating the four geometry runs just to rename
   columns would not change a number. Leave the tables; do not cite
   `n_chunks_x` in the manuscript.

2. **S2.1 seed-separation is a mixed-generator contrast.** The report
   refuses to read its decaying gap as a half-life. Keep that refusal in
   any later prose. A per-generator gap on gemma alone does not exist as
   a run and must not be invented from the pooled figure.

3. **Prefill α = 0.80 on one physics cell** against −0.07 on its pair.
   Mechanism medians hide it; the report names it. Do not quote a prefill
   median α without that pair.

4. **Later analysis manifests record a dirty tree** because artifacts
   were written between geometry runs. The first S2.1 geometry run is
   clean at `54f052e`. The scientific content does not depend on those
   diffs.

5. **One LEAD citation** remains in `docs/literature/related-work.md`.
   The gate warns; `paper/main.tex` is still empty. Fine for this stage.

## Claims I judge supported

- **Convergence past the horizon is not a property of language models as
  a class.** Gemma 0/8 long (CI 0–0) versus gpt-oss-120b 8/8 almost-`T`
  (CI 1–1) and qwen3-8b 8/8 (S2.2 raw). F2's "disagreement is the
  result" clause is what the numbers do. The published S2.1 rate figure
  that includes short fragments is not this claim; the report says so.

- **`assistant_prefill` is not a lever on the qwen attractor.** Fixed-point
  8/8 vs 7/8, difference CI [−0.375, 0.0]. Step-1 register 6/8 vs 4/8
  does not meet Q3's "more than half," and the CI on the difference
  includes zero. Prefill surreal falling into the register by mid-run is
  the text, not a metric. Q4 holds; Q3 is false. n = 8 is below the
  pre-registered bar of 20, which is why F4 is PARTIAL rather than a
  precise rate.

- **The Stage 1 sentence survives as a claim about qwen3-8b under P1.**
  S2.2 seed-separation stays positive through band 12 in both embedding
  spaces, CIs excluding 0 (bge-m3 0.232 [0.157, 0.312]; qwen3-embed-8b
  0.455 [0.330, 0.580]). Combined with 8/8 (raw) / 7/8 (prefill)
  fixed-point, this is "freezes while still carrying the seed" at 12
  turnovers on this generator.

- **Gemma's long-run fate is silence, not self-review.** Quoted text,
  0/8 fixed-point, looping-degenerate physics vs non-degenerate surreal.
  Calling the surreal α (0.11–0.30 in bge-m3) semantic confinement would
  be the S1.0 error without the loop. The report refuses that reading.

- **Q6 is false on gemma.** Exact-match 20%, not >90%. No arm except
  glimmer may claim seeded determinism.

- **F8 failed and is not being walked back.** 11/40 on S2.1. 120b
  almost-`T` is counted as missing for F8 and used, with that limitation,
  for the long-trajectory rate. Those two uses are consistent because
  they are named.

- **Spend is the ledger.** $2.54 / $6; project $11.57 / $50. Embeddings
  and geometry $0.

## Claims I judge unsupported or overreaching

- **Any sentence that treats "the models" as the subject of
  convergence.** Three of five long-trajectory generators disagree; the
  fifth (gpt-oss-20b) is missing. One instance is one instance.

- **A half-life, or a decaying seed memory, from S2.1 separation.**
  Pooled across gemma silence, 120b fixed points, qwen fragments, and
  empty-EOS deaths. The last band is 25 within-pairs and the bge-m3 CI
  includes 0. The report does not make this claim; nothing else should.

- **A prefill register rate of 0.50 as a number the paper can carry.**
  n = 8, bar was 20, difference CI includes 0. PARTIAL is the claim.

- **MSD α as evidence of semantic confinement on any degenerate row.**
  120b 8/8, qwen S2.2 raw 8/8, glimmer physics 2/2, gemma physics 4/4.
  Those exponents measure repetition. They corroborate the degeneracy
  label; they do not add a dynamical fact.

- **Instruction tuning as the demonstrated cause of the register.**
  Prefill was the cheap lever and it failed. The base-model check of
  ADR-0008 was not run. The confound is open. ADR-0010 is right to
  park it as S3.0.

## The seven questions

1. **Does the conclusion follow?** Yes. "Not universal" follows from
   gemma vs 120b/qwen, not from a mean. "Prefill is not a lever" follows
   from a difference CI that does not exclude zero and from quoted
   mid-run register on prefill surreal. "Stage 1 about qwen under P1"
   follows from S2.2 separation plus the qwen fixed-point rate, not from
   the model axis.

2. **Thresholds calibrated?** The n ≥ 40 chunk cut is ~10 turnovers at
   this `W` and chunk size — the regime F1/F2 asked for, not an
   intuition about "long." F4's n = 20 was pre-registered and was not
   quietly lowered. Degeneracy and fixed-point thresholds are the
   Stage 1 calibrations, reused in-regime. `too_short_for_msd` is the
   estimator's n < 4 refusal, not a scientific cut.

3. **Regime?** `W = 4096`, `T = 49152`, both temperatures, both seeds.
   Prefill was remeasured at this window rather than imported from the
   28-token probe. Determinism remains a short probe and is not treated
   as trajectory reproducibility except for glimmer (100% on that
   probe). 120b is scored as almost-`T`, not as `T`.

4. **One instance?** The report generalises from five generators to
   "not a class property" — that is the one generalisation the
   disagreement supports. Everything else is named as qwen, or gemma,
   or 120b, or two glimmer cells.

5. **Confounds named?** Degeneracy, empty EOS, last-short-block guard,
   Alibaba 429s, re-prompt vs sliding attention, forced continuation
   past stop (gemma stop 0.83–0.99), provider pin, non-zero tokenizer
   round-trip, bounded reasoning, cached qwen cells, mixed-generator
   separation, instruction-tuning still open. I do not see a hidden one
   that would invert a headline sentence.

6. **Artifacts state what they cannot?** Gate: 59/59 have limitations.
   Geometry scalars refuse degenerate exponents. Separation limitations
   still mention "the Stage 2 probe" in leftover Stage 1 wording; they
   also say a positive gap is not a mechanism and not recoverability.
   PCA is labelled illustration. Adequate.

7. **Negative result softened?** No. Q1, Q3, Q5, Q6, Q7 scored wrong.
   F8 FAIL. F4 PARTIAL. "The hypothesis did not hold" is the Q1
   sentence. Prefill is not being sold as a healthier protocol that
   almost worked.

## Sign-off

The mechanical gate is green. The scientific claims that the report
actually makes are supported by the runs it cites. The claims it does
not make — class-wide convergence, a prefill rate, a mixed-generator
half-life, instruction tuning as cause — must stay unmade.

Stage 3 proceeds under ADR-0010: no default prefill, MSM only on arms
that reached ~12 turnovers, base-model check first or the
instruct-under-P1 confound stays open.
