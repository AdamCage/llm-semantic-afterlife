# Manuscript

Source of record: [`main.tex`](main.tex) plus [`refs.bib`](refs.bib).
Figures are included from `../artifacts/` (see `\graphicspath`).
Do not redraw them for the paper.

Compile from this directory (TeX Live with `natbib`, `graphicx`, `booktabs`, `hyperref`):

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Every quantitative sentence in `main.tex` carries a same-line comment
with an artifact path and `run_id`. Cite only `VERIFIED` entries from
`docs/literature/related-work.md`. Stage 7 minted no generate `run_id`.
