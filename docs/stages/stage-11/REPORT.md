# Stage 11 report — Ministral replicates the positive last-band gap; Gemma does not

**Status.** Closed 2026-09-26 after scientific review
**APPROVED WITH CHANGES** ([`REVIEW.md`](REVIEW.md)); the phrase
blocker is applied below. Human authorised the next stage.
Overall: **PASS** on the Ministral completer contrast;
**PARTIAL** on Gemma completeness (IT 0/40 completers, named and
kept). Native-chat still deferred. S12 not started.

Headline, **two estimands**. On local Ministral 3 8B, P1
`raw_bytes`, `W=4096`, T=0.3, 12 turnovers, **completion does not
differ**: Base and Instruct are both 40/40 at \(T=49152\), zero
empty-completion deaths. That is neither the S9 pattern (Base
worse) nor the S10 pattern (post-training kills completion). Do
not pool. Among lock-table trajectories (`min_chunks=8`; here
equal to the 40 completers), every trajectory locks
(`N_confirm=3`). Confirmed escape is **0/40** on Base and **4/40**
on Instruct (programming 3, biology 1), in both embedding spaces.
Last-band \(G_t\) is positive and the seed-cluster interval
excludes 0 in both spaces on both rungs (BGE Base 0.138 [0.063,
0.158], Instruct 0.150 [0.084, 0.158]; Qwen-embed Base 0.240
[0.127, 0.272], Instruct 0.224 [0.139, 0.228]). The Instruct sign
matches S9 Qwen Instruct (`+`). Magnitudes are not compared across
families. Where the interval excludes 0, \(G_t>0\) is
seed-conditioned separation of late registers / loop families, not
recovered prompt memory.

On Gemma 4 12B the positive gap **did not replicate**. Base
completers are 38/40 (2 empty deaths). Last-band BGE is **negative**
and the interval excludes 0 (−0.011 [−0.038, −0.006]). Last-band
Qwen-embed is a point `+` whose interval includes 0 (0.014
[−0.021, 0.019]); that \(G_t>0\) is **not established**. IT has
**0/40** completers (run `STATUS=FAILED`, empty completions, not
OOM). IT last-band is **unidentified** in both spaces (0 within, 0
between). The licensed sentence is *did not replicate in the Gemma
condition*. It is not a claim that full attention is unnecessary,
and it is not a causal claim about `sliding_window=1024`.

Plan: [`PLAN.md`](PLAN.md). Branch: `stage-11`.

The lock is **not** absorbing and is **not** a semantic state.
Confirmed escapes on Instruct and on Gemma Base are the evidence.

---

## 1. Verdict per exit criterion

| # | Criterion | Verdict | Evidence |
| --- | --- | --- | --- |
| E1 | Ministral NF4 80/80 at \(T=49152\), or missing cells named | **PASS** | Base 40/40, Instruct 40/40. [`generate_status.csv`](../../../artifacts/stage-11/generate_status/generate_status.csv) |
| E2 | Gemma NF4 80/80, or PARTIAL with a recorded empty / OOM reason | **PARTIAL** | Base 38/40; IT 0/40. 42 empty-completion cells named in [`empty_completions.csv`](../../../artifacts/stage-11/empty_completions/empty_completions.csv). Not OOM. No E4B swap |
| E3 | Native-chat deferred | **PASS** | no native YAML executed |
| E4 | Degeneracy before any published \(G_t\) | **PASS** | four `s11-degeneracy-*` runs finished 2026-09-23T05:19Z; persistence began 06:20Z. [`degeneracy_verdicts.csv`](../../../artifacts/stage-11/degeneracy/degeneracy_verdicts.csv) |
| E5 | Last-band \(G_t\) + CI + LOO in both spaces, or unidentified | **PARTIAL** | Ministral Base, Ministral Instruct, and Gemma Base have \(G_t\), CI, and LOO in both spaces ([`gt_last_band.csv`](../../../artifacts/stage-11/gt_last_band/gt_last_band.csv), [`persistence_loo_all.csv`](../../../artifacts/stage-11/loo/persistence_loo_all.csv)). Gemma IT last-band unidentified (0 pairs). IT LOO rows at band 8–9 have empty \(G\) |
| E6 | F1 + `N_confirm=3`; long-lived repetition lock | **PASS** | [`persistence_locks_all.csv`](../../../artifacts/stage-11/locks/persistence_locks_all.csv). Hash is not the headline |
| E7 | Every generate step `served_provider=local` | **PASS** | [`generate_status.csv`](../../../artifacts/stage-11/generate_status/generate_status.csv) |
| E8 | Thinking = 0; round-trip failures named; fill and stop by quarter | **PASS** | reasoning 0; round-trip 0; [`protocol_by_quarter.csv`](../../../artifacts/stage-11/protocol_by_quarter/protocol_by_quarter.csv) |
| E9 | One GPU | **PASS** | sequential matrix, then one resume of the same Gemma ids |
| E10 | Generate + local BGE $0; hosted Qwen-embed cap $5 | **PASS** | hosted ledger lines are `cost_usd=0.0` (ADR-0029) |
| E11 | Not pooled with S9 or S10 | **PASS** | no table averages families |
| E12 | Gemma reading is generalization, not a causal attention claim | **PASS** | this report uses *did not replicate in the Gemma condition* |
| E13 | Gemma OOM stops the family; no silent substitute | **PASS** | no OOM file; both Gemma slugs ran |

---

## 2. Results

### Generate (second estimand)

| Cell | `run_id` | Completed | Failed | Reason |
| --- | --- | ---: | ---: | --- |
| Ministral Base | `s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b` | 40 | 0 | — |
| Ministral Instruct | `s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2` | 40 | 0 | — |
| Gemma Base | `s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981` | 38 | 2 | empty completion (`recipe` s2, `programming` s2) |
| Gemma IT | `s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427` | 0 | 40 | empty completion; run `STATUS=FAILED` |

Failed cells stay in the sample. They do not enter last-band
\(G_t\). That is missing data, not an unlock.

Gemma Base recorded 58 `trajectory.finished` events and Gemma IT
63, on 40 unique trajectories each (pause/resume replay). Unique
counts above are the sample.

Lock-table \(n\) equals 12W completers on Ministral (40) and on
Gemma Base (38). On Gemma IT, lock-table \(n=8\) and completers
are 0. Those eight died after `min_chunks=8` and before
\(T=49152\). Last-band \(n\) for IT is 0 pairs.

### Last-band \(G_t\)

| Cell | Space | \(G\) | Interval | Excludes 0 |
| --- | --- | ---: | --- | --- |
| Ministral Base | BGE-M3 | 0.138 | [0.063, 0.158] | yes |
| Ministral Instruct | BGE-M3 | 0.150 | [0.084, 0.158] | yes |
| Ministral Base | Qwen-embed | 0.240 | [0.127, 0.272] | yes |
| Ministral Instruct | Qwen-embed | 0.224 | [0.139, 0.228] | yes |
| Gemma Base | BGE-M3 | −0.011 | [−0.038, −0.006] | yes (negative) |
| Gemma Base | Qwen-embed | 0.014 | [−0.021, 0.019] | no |
| Gemma IT | both | unidentified | — | no pairs |

Within-family edges do not flip an identified sign. Ministral is
`+/+` in both spaces. Gemma Base→IT is not a flip: IT is
unidentified. Gemma Base BGE is an identified negative. The
Qwen-embed sign is not established (0.014 [−0.021, 0.019] includes
0). Cross-space sign agreement is not identified.

### Locks and escapes

BGE lock table (the classifier is text-side; the same counts
appear in Qwen-embed):

| Cell | Seeds with ≥1 lock | Lock / lock-table \(n\) | Confirmed escape |
| --- | --- | --- | ---: |
| Ministral Base | 10/10 | 40/40 | 0 |
| Ministral Instruct | 10/10 | 40/40 | 4 |
| Gemma Base | 10/10 (programming and recipe have 3 completers) | 38/38 | 15 |
| Gemma IT | 5 seeds in the lock table | 8/8 | 4 |

Instruct escapes are biology 1/4 and programming 3/4. Gemma Base
escapes are spread across 9 of 10 seeds (programming 0/3). These
are confirmed escapes under F1 + `N_confirm=3`, not a claim that
the process then settled.

### Protocol by quarter

Final-quarter block fill on cells with 12W completers: Ministral
Base 1.00, Ministral Instruct 1.00, Gemma Base 0.996. Stop rate in
that quarter is 0, 0, and 0.004. Gemma IT has no 12W completer;
its quarter-4 fill is 0.60 and its stop rate is 0.55, which is the
death process, not a completed window. Reasoning tokens are 0.
Tokenizer round-trip failures are 0. Every generate step was
`local`.

### What the text is doing

Tails, not full trajectories. Ministral Base `physics` s1 is a
lexical loop on the seed's physics register:

> d with a Metropolis algorithm that samples the gauge field configurations with a probability proportional to the square of the Polyakov loop. The Polyakov loop is zero, and the configurations are generated with a Metropolis algorithm

Ministral Instruct `biology` s1 is a digit cycle, not a biology
paragraph:

> 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

Gemma Base `finance` s1 repeats one sentence:

> the spread would converge eventually, but the cost of funding would increase. The risk manager's note that morning made the point plainly: the spread would converge eventually, but the cost of funding would increase.

Gemma IT `biology` s3, the longest IT death, is commas:

> ,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

---

## 3. Prediction vs. outcome

| # | Prediction | Observed |
| --- | --- | --- |
| P1 | Instruct ≥8/10 seeds lock | **true** (10/10) |
| P2 | Base empty-completion rate higher than Instruct | **false**. Both 0/40. Not an OLMo-style inversion either |
| P3 | Instruct last-band CI excludes 0 in both spaces | **true** |
| P4 | Instruct sign agrees across spaces | **true** (`+`/`+`) |
| P5 | Thinking tokens 0 | **true** |
| P6 | Final-quarter fill ≥ 0.95 on completed 12W steps | **true** (1.00, 1.00, 0.996). IT has no such steps |
| P7 | Gemma does not OOM | **true** |
| P8 | IT empty rate ≥ 20/40 | **true** (40/40) |
| P9 | Instruct sign matches S9 Qwen Instruct `+` | **true**. Magnitudes not compared |
| P10 | Necessary-condition sentence only if both CIs exclude 0; otherwise did-not-replicate | **did not replicate in the Gemma condition**. The necessary-condition sentence is not licensed |
| P11 | Confirmed escape is 0 | **false**. Instruct 4/40, Gemma Base 15/38 |
| P12 | Point \(G_t>0\) with CI including 0 is not established | Gemma Base Qwen-embed is that case |

P2 and P11 are wrong on the record. The stage still answers the
question.

---

## 4. Surprises

1. Ministral completion is saturated on both sides. S9 and S10 had
   made empty-completion the place post-training showed up. Here it
   does not.
2. Confirmed escape is common on Gemma Base (15/38) and present on
   Ministral Instruct (4/40). A lock at this horizon is not
   automatically still locked at 12W.
3. Gemma Base BGE last-band is negative with an interval that
   excludes 0. Same-seed pairs are farther apart than different-seed
   pairs in that space. The other space does not establish the
   opposite sign.
4. Gemma IT dies the way the S8 microbench died, including a long
   comma tail (`biology` s3) that still never reaches \(T\).

---

## 5. Threats to validity

- **One family is not the other.** Ministral `+/+` does not transfer
  to Gemma. The report does not average them.
- **Gemma Base Qwen-embed sign is not established.** BGE last-band
  is an identified negative. The other space does not establish the
  opposite sign. Cross-space sign agreement is not identified. A
  sentence that picks one space is a sentence about that space.
- **Lock-table \(n\) is not last-band \(n\) on IT.** Eight IT
  trajectories enter the lock table. None supplies a last-band pair.
- **Resume replay.** Gemma finished-event counts exceed 40. Unique
  trajectory ids are the sample.
- **NF4 and P1 re-prompt.** This is not native chat and not sliding
  attention. Gemma's hybrid window is not isolated from family,
  size, or training.
- **Escapes are F1 surface-form exits.** They are not a validated
  macrostate transition and not a semantic-domain change.
- **Hosted Qwen-embed is the Paper A geometry** (ADR-0029), not a
  local NF4 twin of the generator.

---

## 6. Cost actuals

| | Estimate | Actual |
| --- | ---: | ---: |
| Local generate | $0 | **$0** |
| Local BGE-M3 | $0 | **$0** |
| Hosted `qwen3-embed-8b` | cap $5 (ADR-0029); 5840 chunks / 5.98M tokens | **$0.00** |
| Project ledger | ceiling $200 | **$10.54** / $200 |

Wall-clock was days of exclusive GPU, including two pauses of
Gemma. Empty IT deaths were short relative to a full 12W cell.
Analysis finished 2026-09-23T07:35:12Z.

---

## 7. Implications for the plan

- **S12 may not start** until this stage has a gate-green report
  and scientific sign-off. The finding to carry is: on this
  Ministral pair the completer gap is positive in both spaces and
  completion is saturated; on Gemma the positive gap did not
  replicate (Base BGE is an identified negative; the Qwen-embed
  sign is not established; IT produced no 12W completer).
  Confirmed escape is not zero.
- **Do not pool** Ministral or Gemma with S9 Qwen or S10 OLMo.
- **F1 and `N_confirm=3` stay frozen.**
- A CI that includes 0 is not “true on the point.” An unidentified
  last-band is not a sign flip.
- Native-chat stays blocked until `build_request` distinguishes
  `native_chat` from `raw_completion`.

Index: [`artifacts/stage-11/INDEX.md`](../../../artifacts/stage-11/INDEX.md).
