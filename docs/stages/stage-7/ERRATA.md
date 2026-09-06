# Errata (2026-09-06) — TMLR correctness pass (ADR-0019)

Closed `REPORT.md` records the Stage 7 writing contract. The manuscript
was rewritten in this pass; the closed verdicts (H1 unsupported, H5
absent, F4 = domain gap not H2) stand.

## What changed

- Title: *Long-Run Dynamics of Blockwise Self-Conditioned Language
  Generation After Prompt Eviction* (old title kept as subtitle).
- Occupancy $B=1024$, $B/W=0.25$, blockwise kernel named.
- Bernoulli CIs in the text match Clopper–Pearson (no `[0,0]` / `[1,1]`
  for $0/n$ and $n/n$).
- F6 demoted: no detected divergence / underpowered; not collapse.
- Related work: Perez et al. ICLR 2025; Mohamed et al. ACL 2025;
  Xu et al. NeurIPS 2022; Holtzman et al. ICLR 2020; Shumailov et al.
  Nature 2024 — all `VERIFIED` in
  [`docs/literature/related-work.md`](../../literature/related-work.md).
- Sequential-study wording replaces “pre-registered plan”.
- Russian translation [`paper/main.ru.tex`](../../../paper/main.ru.tex)
  and committed PDFs
  [`semantic-afterlife-en.pdf`](../../../paper/releases/semantic-afterlife-en.pdf) /
  [`semantic-afterlife-ru.pdf`](../../../paper/releases/semantic-afterlife-ru.pdf)
  track this rewrite (`bash paper/compile.sh all`). English remains
  canonical on numbers and `run_id`s.

## What did not change

- No Stage 7 generate. No `runs/s7`. Hosted spend $\$0$.
- Mechanical `afterlife review --stage s7` still fails `runs.complete`
  by ADR-0018.
