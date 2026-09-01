# S1.0d — convergence to a textual fixed point is universal at 12 turnovers

**Run:** `s1-convergence-probe-20260830T151346Z-7655fa1d`
**Spend:** $0.33 (forecast $0.74; the difference is response-cache reuse from the
aborted core run)
**Completion:** 6 of 16 trajectories reached `T`. The other 10 are missing data
with two distinct causes, both reported below rather than excluded.

## Why this probe exists

The Stage 1 core arm was killed after 441 steps because all four in-flight
trajectories had converged to near-exact textual fixed points, which the
degeneracy diagnostic scored as clean. The diagnostic measured repetition *inside*
a chunk; a sequence of individually varied but mutually near-identical pages is
maximally healthy by that measure.

That also invalidated the model selection, because the viability sweep behind it
used the same diagnostic — and, more seriously, ran `T = 1.5W`. Convergence in the
killed run established itself around turnover 10, so at 1.5 turnovers the failure
mode was not mismeasured but outside the observation window entirely. Startup
behaviour was measured and long-run behaviour concluded: the fourth instance in
this project of trusting a number outside the regime it was taken in.

## Result at matched length

Only cells reaching the full 12 turnovers are comparable (see the length caveat
below). Natural English prose, chunked identically: novelty **0.97**, median
late-phase pairwise 5-gram Jaccard **0.000** (max 0.012 across sources).

| generator | T | seed | novelty | unproductive | late-pair median |
| --- | --- | --- | --- | --- | --- |
| llama-3.1-8b | 0.3 | physics | 0.0095 | 100% | **1.000** |
| qwen3-8b | 0.3 | physics | 0.0870 | 98% | **1.000** |
| muse-glimmer-30b | 0.3 | physics | 0.0974 | 98% | 0.564 |
| qwen3-8b | 0.3 | surreal | 0.1011 | 97% | 0.281 |
| qwen3-8b | 1.0 | physics | 0.2729 | 84% | 0.462 |
| qwen3-8b | 1.0 | surreal | **0.6754** | 69% | **0.007** |

**Every generator family converges.** At the common operating point
(`T = 0.3`, `physics`) all three families that survived to 12 turnovers sit at
0.0095–0.0974 novelty, roughly two orders of magnitude below natural prose. This
is not a property of one model.

**Temperature and seed both matter, strongly, and compound.** Within qwen3-8b,
moving from (0.3, physics) to (1.0, surreal) raises novelty 7.8-fold, from 0.087
to 0.675, and drops late-phase pairwise similarity from 1.000 to 0.007. The
aborted core arm ran the worst of the four available configurations.

**The best cell has no fixed point but is still not natural.** At (1.0, surreal)
the late-pair median of 0.007 is inside the natural range, so the trajectory keeps
moving; its novelty of 0.675 nonetheless means it reuses phrasing far more than
human writing does. The two measures disagree here, and the disagreement is
informative rather than a defect — see "the verdict rule needs splitting".

## Two failure classes among the missing 10

**muse-glimmer-30b cannot free-run at `W = 4096`.** Three of four cells died on
five consecutive empty completions — the model returns a bare stop token and
nothing else. This was previously observed at `W = 8192`, and
`HANDOFF.md` recorded it as *not* occurring at 4096. That note was wrong: it
generalised from a single window. A fifth regime-transfer error, this one mine.

**llama-3.1-8b and mistral-nemo-12b are unusable on this endpoint.** All seven of
their cells died on HTTP 429 after exhausting eight retries. This is
infrastructure, not science, and it means the llama row above is the only llama
observation at full length.

## The length caveat, which constrains how this table may be read

Novelty is computed against the trajectory's own accumulated history, so it falls
mechanically as a trajectory lengthens: a 9-chunk trajectory has less history to
repeat than a 129-chunk one. Cells that failed early therefore show *higher*
novelty for reasons that have nothing to do with their dynamics — mistral at
(1.0, physics) reads 0.759, but it only reached 1.1 turnovers.

Comparisons are valid only at matched turnover counts. This is a property of the
measure, stated here because the temptation to rank all sixteen cells by novelty
is strong and the ranking would be an artifact.

## The verdict rule needs splitting

`compute_degeneracy` currently fires `degenerate` when either intra-chunk looping
or inter-chunk unproductivity exceeds half the post-horizon chunks. On the
(1.0, surreal) cell that rule says degenerate on novelty 0.675, while the pairwise
measure says the process is still moving as freely as natural prose.

The two quantities answer different questions and should not share one boolean:

- **pairwise similarity** — has the process reached a fixed point or a short
  cycle? A dynamical question with a sharp natural reference (0.000, max 0.012).
- **novelty** — how productive is the process? A continuous order parameter, whose
  natural-prose reference is arguably the wrong yardstick, because a human writing
  a book is not conditioned on a sliding window of their own output and has no
  reason to recycle phrasing the way a self-conditioned process must.

Deliberately not changed yet. Tuning a threshold so that the data one wants to
keep passes is the failure mode this project's review contract exists to prevent,
and the change should be argued from the reference rather than from the result.

## S1.0e — temperature escapes the textual fixed point and tightens the semantic one

**Run:** `s1-regime-hunt-20260830T203115Z-6ea352c7`, 15 of 18 trajectories
complete, $1.10 against a $0.80 forecast (38% over; the cost model needs
re-checking at high temperature, where completions run longer).

Nine operating points on qwen3-8b, two stochastic replicates each, 12 turnovers.

| T | seed | late-pair | at fixed point | novelty | entropy | TTR |
| --- | --- | --- | --- | --- | --- | --- |
| 1.0 | surreal | 0.0073 / 0.0405 | no / **yes** | 0.68 / 0.54 | 7.35 / 7.42 | 0.52 / 0.48 |
| 1.0 | love | 0.0033 / 0.0763 | no / **yes** | 0.52 / 0.53 | 7.19 / 6.96 | 0.55 / 0.49 |
| 1.0 | noise | 0.0470 / 0.1050 | **yes / yes** | 0.58 / 0.57 | 6.57 / 6.85 | 0.47 / 0.49 |
| 1.3 | surreal | 0.0178 / 0.0842 | **yes / yes** | 0.89 / 0.26 | 7.01 / 5.07 | 0.45 / 0.76 |
| 1.3 | love | 0.0352 / 0.0185 | **yes / yes** | 0.80 / 0.75 | 6.75 / 7.30 | 0.50 / 0.48 |
| 1.3 | noise | 0.0214 / 0.0019 | **yes** / no | 0.85 / 0.85 | 6.85 / 7.93 | 0.48 / 0.62 |
| **1.6** | surreal | 0.0011 / 0.0009 | no / no | 0.95 / **0.97** | 6.81 / 7.29 | 0.55 / 0.48 |
| **1.6** | love | 0.0035 / 0.0013 | no / no | 0.96 / 0.96 | 7.05 / 7.17 | 0.51 / 0.48 |
| **1.6** | noise | 0.0000 / 0.0021 | no / no | 0.93 / 0.94 | 6.86 / 6.69 | 0.53 / 0.53 |

Natural prose reference: novelty 0.97, late-pair median 0.000, entropy 7.40,
TTR 0.41.

**At `T = 1.6` all six cells escape the textual fixed point**, across all three
seeds and both replicates, at novelty indistinguishable from natural prose. At
`T = 1.0` four of six are at a fixed point and at `T = 1.3` four of six. This is
the only clean regime found.

### Reading the text changed the conclusion

The metrics say `T = 1.6` is healthy. The text says something else, and this is
the second time in this stage that reading beat measuring.

The **reviewer register persists at every temperature**. Step 1 of the surreal
cell: "This passage is an imaginative and poetic exploration of a surreal
commission... Let's unpack it paragraph by paragraph." The seed ends mid-sentence
on "and"; the model still reframed it as a document to review. Temperature does
not touch this.

More importantly, **two trajectories from radically different seeds converged to
the same semantic register**. From cartographers surveying the interior of a
piano, and from a woman leaving a letter unopened on a windowsill, both arrive at:
"the sacred stillness within us all", "silence and sacred stillness", "communion",
"soul and soul", "breath and presence", "something ancient, profound, and
intimate". By turnover 16 and 21 respectively they are indistinguishable in
content while sharing almost no 5-grams.

**The novelty measure cannot see this.** It detects lexical fixed points; this is a
semantic one with lexical variation. The instrument built to catch the first
failure mode is blind to the second, which is the same structural mistake as the
original intra-chunk diagnostic, one level up.

### Embedding space confirms it, and inverts the naive expectation

Late-phase trajectory centroids in `bge-m3`, mean pairwise cosine distance:

| T | within-seed | between-seed |
| --- | --- | --- |
| 1.0 | 0.2360 | 0.2679 |
| 1.3 | 0.2219 | 0.2131 |
| 1.6 | **0.0649** | **0.1130** |

At `T = 1.6` the trajectories are three to four times *closer together* than at
`T = 1.0`. Escaping the textual fixed point costs semantic spread: more sampling
randomness drives the ensemble into a tighter region, not a broader one. Residual
seed structure survives inside that region — within-seed pairs are closer than
between-seed pairs at 0.065 against 0.113 — but the whole ensemble has collapsed
towards one place.

### The formal separation test, and why it says nothing yet

`afterlife analyze separation` on all 18 trajectories, `bge-m3`:
post-horizon mean gap **+0.0295**, trend **−0.0056 per turnover**, and at the last
band the 95% bootstrap interval is **[−0.037, +0.091]** — it contains zero.

Verdict: **no separation established**. This is the underpowered outcome the test
`test_the_contrast_is_underpowered_at_the_pilot_replicate_count` predicted at two
replicates, and it must be read as "cannot tell", not as "no effect". The negative
trend is the more suggestive number, and it is equally unresolved.

One confound in that pass: it pooled all three temperatures, whose geometries
differ by a factor of four. A per-temperature contrast is the right analysis and
needs more replicates than this probe has.

### Three trajectories lost to a new protocol guard

`WindowProtocolError: appending 2 characters produced 0 new tokens; re-tokenisation
collapsed the block` — the model returned a two-character completion which, once
appended and re-tokenised, added nothing to the window. The guard is correct to
fail rather than silently spin, and the event rate is a reportable property of the
high-temperature regime.

## What this means for the stage

The stage's question — does semantic information about the seed survive the
context horizon — presupposes a trajectory that keeps generating. Under protocol
P1 with instruction-tuned generators, at these operating points, it largely does
not: it converges to reprinting a page.

A confound must be named before this is read as a fact about language models. All
four families answer raw text in a **reviewer register** — the killed run's first
step began "Your passage is a deep and insightful discussion of lattice field
theory", and its fixed point was "Wow, what a remarkable and comprehensive piece
of work!". Commentary on commentary has a natural fixed point: praise plus
restatement. That is a property of instruction tuning under a re-prompt protocol,
not of autoregressive generation as such. ADR-0006 recorded the absence of base
models as a compromise; this result upgrades it to a possible obstruction to the
original question.

Open options, in increasing order of departure from the current plan: push the
sampling regime further (`T` above 1.0, at the cost of fluency); choose seeds that
give the reviewer register nothing to latch onto, as `surreal` partially did;
change the continuation mechanism so the model is told to continue rather than
left to infer what raw text means, which changes the protocol and must be declared;
or obtain a genuine base model, which no surveyed provider offers.
