# PDF releases

These PDFs are compiled from the unified publication manuscripts under
[ADR-0031](../../docs/decisions/ADR-0031-publication-assembly.md).
English is canonical; Russian is the complete mirror of the same study.

- `semantic-afterlife-en.pdf`: identified English, TMLR preprint style.
- `semantic-afterlife-ru.pdf`: identified Russian, TMLR preprint layout.
- `semantic-afterlife-anonymous.pdf`: anonymous English, TMLR submission style.

Rebuild all releases after any manuscript or bibliography change:

```bash
bash paper/compile.sh all
bash paper/compile.sh anonymous
```

See [`../PUBLICATION_REVIEW.md`](../PUBLICATION_REVIEW.md) for the final
scientific reading, source checks, and rendered-page verification.
Preparing the anonymous file does not submit or publish the paper.
