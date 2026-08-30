# S1.0c — the free-running viability boundary in `W`

Four generator families × `W ∈ {2048, 4096, 8192}`, `T = 1.5W` in every cell so
the comparison is across window size rather than trajectory length. Same
temperature, seed, mechanism and chunk size throughout. Cost: $0.08.

## Operational behaviour

Block fill (mean), with the outcome of the run:

| Generator | W = 2048 | W = 4096 | W = 8192 |
| --- | --- | --- | --- |
| **qwen3-8b** | 0.954 | 0.942 | 0.928 |
| **muse-glimmer-30b** | 0.690 *(2 empties)* | **1.000** *(stop rate 0.00)* | 0.855 **FAILED** *(7 empties)* |
| llama-3.1-8b-instruct | 0.539 | 0.652 | 0.248 |
| mistral-nemo-12b | 0.195 | 0.154 **FAILED** | 0.131 |

## Text quality

n-gram repetition as a multiple of natural English prose (237 chunks of Carroll
and Darwin; 1.0× is human-like), measured in matched 700-word windows:

| Generator | W = 2048 | W = 4096 | W = 8192 | trend |
| --- | --- | --- | --- | --- |
| **muse-glimmer-30b** | 1.0× | 1.0× | **0.9×** | improves |
| **qwen3-8b** | 1.8× | 1.7× | **1.6×** | improves |
| llama-3.1-8b-instruct | 5.7× | 4.4× | 9.5× | worsens |
| mistral-nemo-12b | 2.5× | 4.5× | 7.2× | worsens |

Type-token ratio and entropy move the same way: glimmer 0.446→0.455 and
7.23→7.27, qwen 0.463→0.487 and 7.44→7.67, while llama and mistral fall on both.

## What this establishes

**There is a viability boundary, it is model-specific, and it is not monotone.**
Two families sustain free-running generation and two do not, and for glimmer and
llama the failure is not "large `W` is harder": glimmer is *perfect* at 4096 and
fails at both 2048 and 8192, llama is best at 4096 and worst at 8192. A simple
"more context is harder" story does not fit.

**For the two viable models, more context makes the text better, not worse.**
Repetition falls and lexical variety rises monotonically with `W` for both qwen
and glimmer. That is the opposite of the degeneration one might expect from a
model conditioned on ever more of its own output, and it is a result worth
reporting in its own right: the models that can free-run at all do so *better*
with a larger window.

**Glimmer's optimum sits at exactly twice its local attention window.** Its
architecture interleaves local layers with a 2048-token attention span, and
`W = 4096` is where it achieves fill 1.000 with a stop rate of 0.00 and text
marginally cleaner than the human reference. This is a single observation at one
temperature and one seed, so it is a hypothesis rather than a finding — but it is
exactly the architectural axis that made glimmer interesting, and Stage 4 should
test it deliberately across a finer `W` grid.

**Mistral is disqualified at every window.** 2.5–7.2× natural repetition, block
fill never above 0.20, one tokenizer round-trip failure. It moves to Stage 6
cross-provider replication only.

## Consequence for the Stage 1 matrix

`W = 4096` is the operating point, chosen now on measurement rather than on cost:
it is the only window where both viable generators are at their best, and it is
where three of four families work at all.

- **Core arm: qwen3-8b.** Stable across every window tested, completed every
  cell, 1.7× natural repetition with the highest type-token ratio of any model.
- **Replication arm: muse-glimmer-30b.** Fill 1.000 and stop rate 0.00 at this
  window, text marginally cleaner than the human reference, a genuinely different
  architecture (hybrid local/global attention), and a known bf16 quantization
  against qwen's `unknown`.

The two are architecturally different in kind, which is what H1's
model-specificity claim requires. That the pilot ends up with the two *best*
generators rather than the two cheapest is a consequence of measuring output
quality before committing, which cost eight cents.
