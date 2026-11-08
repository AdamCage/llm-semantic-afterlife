# Evidence and storytelling

## Read the final state

Find the research plan, methodology, final reports, corrective decisions,
published tables/figures and existing scientific review. Check dates and status.
Understand which results were superseded. Read source metadata, not just a
manuscript abstract. Do not use disconnected numbers from an older draft.

Before narration, write `evidence.json`. Sources have stable IDs, paths relative
to `research_root`, exact locators, verification status and run IDs when the
research uses them. A locator can identify table/row/column, report section,
figure, dataset slice, DOI-backed local literature note or page. A filename alone
is usually too vague. Keep sources accessible to another reviewer.

Claims have IDs, explicit wording, kind (`empirical`, `interpretation`,
`practical`, `explanation`), source IDs and limitations. For practical advice,
set `tested_in_this_study` explicitly. Avoid inferred causality, pooling groups
or treating failure to detect a difference as equivalence. Verify denominators,
time origin, censoring and units against the original estimator.

The mechanical validator checks references exist and keys connect; it cannot
tell whether a cited table entails a sentence. Read and judge that yourself.
If an observation does not support the proposed line, revise the line.

## Build a story the viewer can follow

Start with a concrete question or surprising observation. Explain why answering
it matters, show the mechanism, then define the comparison that discriminates
between explanations. Walk through a few decisive results. Finish with the
supported conclusion and practical implications at their actual strength.

For a broad audience, introduce quantities through questions before symbols:
what is compared, why that control exists, what a positive/negative result means.
Show an explicit counterexample when similar-sounding properties differ.
Do not omit the experimental forcing because it interrupts an elegant metaphor.

Write spoken language, not a journal abstract. Resolve pronouns, expand acronyms,
and prepare pronunciations for names, units and numbers. Scientific limitations
must be spoken near the associated claim; tiny footer text is not enough.
Translate the meaning of terms consistently rather than mechanically.

Duration is a planning variable, not a fact measured from word count. A useful
starting estimate is roughly 110–150 spoken Russian words/minute; use actual
voice durations for final timing. The user may prefer a faster or slower pace.
No fixed scene count is required. Give a dense result breathing room; split a
scene when the viewer must attend to two different things.

## Reusable evidence example

```json
{
  "sources": [{
    "id": "primary-table",
    "path": "artifacts/final/estimate.csv",
    "locator": "row condition=control; columns estimate, ci_low, ci_high",
    "status": "verified",
    "run_ids": ["actual-run-from-the-study"]
  }],
  "claims": [{
    "id": "effect-control",
    "kind": "empirical",
    "statement": "Write the precise supported claim here.",
    "sources": ["primary-table"],
    "limitations": "Name the conditions, uncertainty and confounds that constrain it."
  }]
}
```

The strings above illustrate the schema; they are not valid evidence for a new
project. Never ship placeholders or invented runs in the finished video.
