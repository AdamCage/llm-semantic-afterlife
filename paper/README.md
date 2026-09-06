# Manuscript

English source of record: [`main.tex`](main.tex) plus [`refs.bib`](refs.bib).
Russian translation: [`main.ru.tex`](main.ru.tex). On disagreement,
numbers and `run_id`s in the English file win.

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

Released PDFs (committed):

- [`releases/semantic-afterlife-en.pdf`](releases/semantic-afterlife-en.pdf)
- [`releases/semantic-afterlife-ru.pdf`](releases/semantic-afterlife-ru.pdf)

Auxiliary files go to `paper/build/` (gitignored).

Every quantitative sentence in both TeX files carries a same-line
comment with an artifact path and `run_id`. Cite only `VERIFIED`
entries from `docs/literature/related-work.md`. Stage 7 minted no
generate `run_id`.
