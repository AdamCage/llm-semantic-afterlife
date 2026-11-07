# Manuscript

English source of record: [`main.tex`](main.tex) plus [`refs.bib`](refs.bib).
That file is the assembled narrative (repetition, seed dependence,
family heterogeneity; ADR-0030). [`main.ru.tex`](main.ru.tex) has not
been realigned to it. On disagreement, numbers and `run_id`s in the
English file win. A PDF built from the Russian file is not a
translation of the assembled paper.

Figures are included from `../artifacts/` (see `\graphicspath`).
Do not redraw them for the paper.

Compile both PDFs (TeX Live: `texlive-latex-recommended`,
`texlive-latex-extra`, `texlive-fonts-recommended`, `texlive-bibtex-extra`,
`texlive-lang-cyrillic`, `cm-super`, `lmodern`):

```bash
bash paper/compile.sh          # both
bash paper/compile.sh en       # English only
bash paper/compile.sh ru       # Russian only
```

Released PDFs (committed) predate the assembled `main.tex`:

- [`releases/semantic-afterlife-en.pdf`](releases/semantic-afterlife-en.pdf)
- [`releases/semantic-afterlife-ru.pdf`](releases/semantic-afterlife-ru.pdf)

The next English build needs the `underscore` package (`paper/compile.sh en`).
No engine was available in this workspace when the narrative was assembled,
so those release files were not regenerated.

Auxiliary files go to `paper/build/` (gitignored).

Every quantitative sentence in both TeX files carries a same-line
comment with an artifact path and `run_id`. Cite only `VERIFIED`
entries from `docs/literature/related-work.md`. Stage 7 minted no
generate `run_id`. `main.ru.tex` still tracks the pre-assembly ADR-0019 English
rewrite (blockwise kernel, `B=1024`, Clopper–Pearson intervals,
H1 unsupported / H5 absent / F6 not a headline). It is not the
assembled narrative.
