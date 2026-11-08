# Manuscript

The canonical manuscript is [`main.tex`](main.tex), with bibliography
[`refs.bib`](refs.bib). [`main.ru.tex`](main.ru.tex) is its complete Russian
mirror: the same sections, equations, tables, figures, claims, and sources.
The publication assembly is [ADR-0031](../docs/decisions/ADR-0031-publication-assembly.md).
It is editorial work on closed stages, with no new generation or estimates.

The paper separates textual repetition, reaching the planned horizon,
and initial-text dependence. Families remain separate. The independent
occupancy replication is the primary occupancy evidence; the earlier
panel is explicitly archival because its source vectors are not recoverable.
The selected long continuations remain a separate censored observation.

## Build

Use TeX Live with `texlive-latex-extra`, `texlive-fonts-recommended`,
`texlive-lang-cyrillic`, `cm-super`, `lmodern`, and `librsvg2-bin`. On Windows, the same
commands can run in WSL from this checkout.

```bash
bash paper/compile.sh all        # identified English and Russian
bash paper/compile.sh anonymous  # anonymous English
```

Individual builds use `en` or `ru`. Auxiliary files go to the ignored
`paper/build/` directory. Rebuild after changing a source or bibliography.

The releases are:

- [`English`](releases/semantic-afterlife-en.pdf)
- [`Russian`](releases/semantic-afterlife-ru.pdf)
- [`Anonymous English`](releases/semantic-afterlife-anonymous.pdf)

Identified versions use the TMLR `preprint` option. The anonymous version
uses the official submission option and contains no author identity in
its visible text or PDF author metadata. Preparing it is not a submission
to a venue.

## Style provenance

The unmodified `tmlr.sty`, `tmlr.bst`, and `fancyhdr.sty` come from
[JmlrOrg/tmlr-style-file](https://github.com/JmlrOrg/tmlr-style-file/tree/7bf90efe3a0debbba703c05c43f3ff7e4d4a2992),
revision `7bf90efe3a0debbba703c05c43f3ff7e4d4a2992`.
The upstream licence is retained as [`tmlr-LICENSE`](tmlr-LICENSE).
Do not modify the venue style to force a layout.

## Evidence and verification

Figures use the closed bundles in `../artifacts/`. The family plot is
included directly. The S12 SVG is composed into a vector PDF under
`paper/build/figures/` by [`figure-layout.sed`](figure-layout.sed): only
the complete legend group is translated into empty space so that it does
not cover markers. No plotted values, paths, labels, or experimental
artifacts are changed. `compile.sh` reproduces this display-only copy.
Quantitative findings retain artifact paths and run
identifiers in their LaTeX source comments. Experiment configurations
supply protocol settings. Cite verified primary sources from
[`related-work.md`](../docs/literature/related-work.md).

The final publication reading and build checks are recorded in
[`PUBLICATION_REVIEW.md`](PUBLICATION_REVIEW.md). The existing
`afterlife review --stage s13` gate checks the synthesis record; it
does not certify scientific validity or recover the archival vectors.
