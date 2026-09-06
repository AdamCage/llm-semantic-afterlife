"""Lexical and path checks for the Stage 7 manuscript.

The paper is assembled from closed-stage artifacts. These tests catch
claim overruns and broken includes that a TeX compile would not.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "main.tex"
PAPER_RU = ROOT / "paper" / "main.ru.tex"
BIB = ROOT / "paper" / "refs.bib"
RELATED = ROOT / "docs" / "literature" / "related-work.md"
NOTES = ROOT / "paper" / "notes"
ARTIFACTS = ROOT / "artifacts"


def _tex() -> str:
    return PAPER.read_text(encoding="utf-8")


def _tex_ru() -> str:
    return PAPER_RU.read_text(encoding="utf-8")


def _papers() -> list[tuple[str, str]]:
    return [("en", _tex()), ("ru", _tex_ru())]


def test_manuscript_exists() -> None:
    assert PAPER.is_file()
    assert PAPER.stat().st_size > 1000
    assert PAPER_RU.is_file()
    assert PAPER_RU.stat().st_size > 1000


def test_notes_exist_before_tex_contract() -> None:
    for name in ("claims.md", "figure-shortlist.md", "limitations.md"):
        assert (NOTES / name).is_file(), name


def test_no_stage7_generate_yaml() -> None:
    configs = ROOT / "configs" / "stages"
    matches = list(configs.glob("stage7_*.yaml")) + list(configs.glob("stage_7_*.yaml"))
    assert matches == []


def test_related_work_has_no_lead_backticks() -> None:
    text = RELATED.read_text(encoding="utf-8")
    assert "`LEAD`" not in text


def test_gemini_whisker_and_not_thick_robustness() -> None:
    for name, text in _papers():
        assert "0.029" in text, name
        assert "whisker" in text.lower(), name
        assert re.search(r"not\s+thick robustness|не\s+толстая robustness", text, re.I), name


def test_h1_not_claimed_established() -> None:
    for name, text in _papers():
        assert re.search(r"H1.*unsupported|unsupported.*H1|H1.*не поддержан", text, re.I | re.S), (
            name
        )
        assert not re.search(r"H1 is established", text), name
        abstract = text.split(r"\begin{abstract}")[1].split(r"\end{abstract}")[0]
        title = text.split(r"\begin{document}")[0]
        head = title + abstract
        assert "metastable semantic states" not in head.lower(), name


def test_h5_absent() -> None:
    for name, text in _papers():
        assert re.search(r"H5.{0,200}(absent|отсутств)", text, re.I | re.S), name
        assert not re.search(r"H5 is present", text), name


def test_architecture_independence_only_negated() -> None:
    for name, text in _papers():
        for match in re.finditer(r".{0,80}architecture-independen[ct]e.{0,80}", text, re.I):
            window = match.group(0).lower()
            assert any(tok in window for tok in ("not", "cannot", "no ", "не ")), (
                f"{name}: {window}"
            )


def test_collapsed_is_not_one_lock() -> None:
    for name, text in _papers():
        lowered = text.lower()
        assert "operational" in lowered, name
        assert "not occupancy of one" in lowered or "не occupancy одного" in lowered, name
        assert not re.search(r"collapsed(?: twins)? occupy one lock", text, re.I), name


def test_no_unverified_citations() -> None:
    text = _tex() + _tex_ru() + BIB.read_text(encoding="utf-8")
    for banned in ("Holtzman", "Shumailov", "nucleus sampling"):
        assert banned not in text, banned


def test_cite_keys_resolve() -> None:
    bib = BIB.read_text(encoding="utf-8")
    defined = set(re.findall(r"@\w+\{([^,]+),", bib))
    for name, tex in _papers():
        keys = set(re.findall(r"\\cite[tp]?\{([^}]+)\}", tex))
        used: set[str] = set()
        for group in keys:
            used.update(k.strip() for k in group.split(","))
        missing = used - defined
        assert not missing, f"{name}: {missing}"
    for required in (
        "zekri2024",
        "wang2025",
        "geng2026",
        "ko2026",
        "chen2026horizon",
        "wu2020vampnets",
        "paul2019core",
    ):
        assert required in defined, required


def test_bib_authors_match_verified_records() -> None:
    bib = BIB.read_text(encoding="utf-8")
    assert "Zekri, Oussama" in bib
    assert "Odonnat, Ambroise" in bib
    assert "Wang, Zhilin" in bib
    assert "Geng, Mingmeng" in bib
    assert "Ko, Ting-Wen" in bib
    assert "Chen, Mingguang" in bib
    assert "Wu, Hao" in bib
    assert "Paul, Fabian" in bib


def test_includegraphics_paths_exist_under_artifacts() -> None:
    for name, tex in _papers():
        paths = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex)
        assert paths, f"{name}: no figures included"
        for rel in paths:
            assert not rel.startswith("/"), rel
            assert "artifacts" not in rel.split("/")[0], rel
            target = ARTIFACTS / rel
            assert target.is_file(), f"{name}: {rel}"
            stem = target.with_suffix("")
            data = list(stem.parent.glob(stem.name + ".data.parquet"))
            meta = Path(str(stem) + ".meta.json")
            assert data, f"{name}: missing tidy data for {rel}"
            assert meta.is_file(), f"{name}: missing meta for {rel}"


def _split_tex_comment(line: str) -> tuple[str, str]:
    """Split on a real TeX comment, ignoring escaped \\%."""
    i = 0
    while i < len(line):
        if line[i] == "%" and (i == 0 or line[i - 1] != "\\"):
            return line[:i], line[i + 1 :]
        i += 1
    return line, ""


def test_quantitative_lines_have_same_line_comments() -> None:
    """PLAN F1: every quantitative sentence carries artifact path + run_id."""
    quant = re.compile(r"(\$\d|\d+/\d+|0\.\d{2,}|\d+\\%|\$T\{=\}1\.5|n_\{?\\mathrm\{within\}\}?)")
    skip = re.compile(
        r"^(\\documentclass|\\usepackage|\\graphicspath|\\setstretch|"
        r"\\author|\\title|\\date|\\label|\\begin|\\end|\\toprule|"
        r"\\midrule|\\bottomrule|\\centering|\\includegraphics|"
        r"\\bibliographystyle|\\bibliography|\\item Stage|\\item Этап)"
    )
    missing: list[str] = []
    for name, tex in _papers():
        for i, raw in enumerate(tex.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("%") or skip.search(line):
                continue
            body, comment = _split_tex_comment(line)
            if "&" in body and body.rstrip().endswith(r"\\"):
                continue
            if not quant.search(body):
                continue
            if not comment:
                missing.append(f"{name} L{i}: no comment: {line[:120]}")
                continue
            if not (
                "artifacts/" in comment
                or "docs/stages" in comment
                or "docs/decisions" in comment
                or re.search(r"s[0-9]-", comment)
            ):
                missing.append(f"{name} L{i}: comment lacks path/run_id: {line[:140]}")
    assert not missing, "\n".join(missing[:20])


def test_no_dummy_s7_run_directory() -> None:
    runs = ROOT / "runs" / "s7"
    assert not runs.exists()


def test_release_pdfs_exist() -> None:
    """Committed pdflatex outputs of paper/compile.sh."""
    rel = ROOT / "paper" / "releases"
    for name in ("semantic-afterlife-en.pdf", "semantic-afterlife-ru.pdf"):
        path = rel / name
        assert path.is_file(), name
        assert path.stat().st_size > 50_000, name
        assert path.read_bytes()[:5] == b"%PDF-"


def test_abstract_f4_is_domain_gap_not_recovered_memory() -> None:
    """S7 review blocker 1: F4 is ensemble gap, not recovered identity."""
    for name, text in _papers():
        abstract = text.split(r"\begin{abstract}")[1].split(r"\end{abstract}")[0]
        lowered = abstract.lower()
        assert "seed-domain identity" not in lowered, name
        assert "carries seed-domain" not in lowered, name
        assert re.search(r"domain gap|distinguishability", abstract, re.I), name
        assert re.search(r"not recovered prompt memory", abstract, re.I), name
        assert "H2" in abstract, name
        before_whisker = re.split(r"whisker|волосок", abstract, flags=re.I)[0].lower()
        assert "three embedding spaces" not in before_whisker, name
        assert "трёх пространствах" not in before_whisker, name


def test_occupancy_protocol_names_raw_completion_and_alibaba() -> None:
    """S7 review blocker 2: P1 is not the continuation mechanism."""
    for name, text in _papers():
        protocol = text.split(r"\label{sec:p1}")[1].split(r"\label{sec:cost}")[0]
        assert re.search(r"raw\\_completion", protocol), name
        assert "Alibaba" in protocol, name
        assert "P1" in protocol, name
        assert (
            "glossary" in protocol.lower()
            or "глоссарий" in protocol.lower()
            or "distinct" in protocol.lower()
            or "разные оси" in protocol.lower()
        ), name
        limitations = text.split(r"\label{sec:limitations}")[1].split(r"\label{sec:discussion}")[0]
        assert re.search(r"raw\\_completion", limitations), name
        assert "Alibaba" in limitations, name
        assert "not synonyms" in limitations.lower() or "не синонимы" in limitations.lower(), name
