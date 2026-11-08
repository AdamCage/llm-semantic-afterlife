"""Scientific and provenance checks for the unified TMLR manuscript.

The paper is assembled from closed-stage artifacts. These tests catch
claim overruns and broken includes that a TeX compile would not.
English ``main.tex`` is canonical; ``main.ru.tex`` is a translation and
must carry the same quantitative claims, cite keys, and figure paths.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "main.tex"
PAPER_RU = ROOT / "paper" / "main.ru.tex"
BIB = ROOT / "paper" / "refs.bib"
RELATED = ROOT / "docs" / "literature" / "related-work.md"
NOTES = ROOT / "paper" / "notes"
ARTIFACTS = ROOT / "artifacts"

REQUIRED_CITE_KEYS = (
    "streamingllm2024",
    "zekri2024",
    "wang2025",
    "geng2026",
    "ko2026",
    "chen2026horizon",
    "wang2026random",
    "wu2020vampnets",
    "paul2019core",
    "perez2025",
    "mohamed2025",
    "xu2022",
    "holtzman2020",
    "shumailov2024",
)


def _tex() -> str:
    return PAPER.read_text(encoding="utf-8")


def _tex_ru() -> str:
    return PAPER_RU.read_text(encoding="utf-8")


def _papers() -> list[tuple[str, str]]:
    return [("en", _tex()), ("ru", _tex_ru())]


def _cite_keys(tex: str) -> set[str]:
    used: set[str] = set()
    for group in re.findall(r"\\cite[tp]?\{([^}]+)\}", tex):
        used.update(k.strip() for k in group.split(","))
    return used


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


def test_cite_keys_resolve() -> None:
    bib = BIB.read_text(encoding="utf-8")
    defined = set(re.findall(r"@\w+\{([^,]+),", bib))
    for name, tex in _papers():
        used = _cite_keys(tex)
        missing = used - defined
        assert not missing, f"{name}: {missing}"
        for required in REQUIRED_CITE_KEYS:
            assert required in defined, required
            assert required in used, f"{name}: missing cite {required}"


def test_bib_authors_match_verified_records() -> None:
    bib = BIB.read_text(encoding="utf-8")
    related = RELATED.read_text(encoding="utf-8")
    assert "Zekri, Oussama" in bib
    assert "Odonnat, Ambroise" in bib
    assert "Wang, Zhilin" in bib
    assert "Geng, Mingmeng" in bib
    assert "Ko, Ting-Wen" in bib
    assert "Chen, Mingguang" in bib
    assert "Wu, Hao" in bib
    assert "Paul, Fabian" in bib
    assert "Perez, J" in bib
    assert "Holtzman, Ari" in bib
    assert "Shumailov, Ilia" in bib
    assert "Mohamed, Amr" in bib
    assert "Qiu, Jielin" in bib
    assert "Wang, Heng" in bib
    assert "VERIFIED" in related
    for key in ("Holtzman", "Shumailov", "Perez", "Mohamed", "Xu"):
        assert key in related


def test_verified_citations_are_logged() -> None:
    related = RELATED.read_text(encoding="utf-8")
    for marker in (
        "When LLMs Play the Telephone Game",
        "LLM as a Broken Telephone",
        "Learning to Break the Loop",
        "The Curious Case of Neural Text Degeneration",
        "AI models collapse when trained on recursively generated data",
        "Random Attention",
    ):
        assert marker in related
        idx = related.index(marker)
        assert "VERIFIED" in related[max(0, idx - 400) : idx]


def _split_tex_comment(line: str) -> tuple[str, str]:
    """Split on a real TeX comment, ignoring escaped \\%."""
    i = 0
    while i < len(line):
        if line[i] == "%" and (i == 0 or line[i - 1] != "\\"):
            return line[:i], line[i + 1 :]
        i += 1
    return line, ""


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


def test_compile_script_supports_anonymous() -> None:
    script = (ROOT / "paper" / "compile.sh").read_text(encoding="utf-8")
    assert "anonymous" in script
    for name, text in _papers():
        assert r"\ifdefined\TMLRANON" in text, name


def test_russian_preamble_has_cyrillic_fonts() -> None:
    text = _tex_ru()
    assert "T2A" in text
    assert "babel" in text
    assert "russian" in text
    assert "lmodern" not in text


def _table_block(tex: str, label: str) -> str:
    marker = "\\label{" + label + "}"
    idx = tex.index(marker)
    start = tex.rfind(r"\begin{table}", 0, idx)
    end = tex.index(r"\end{table}", idx)
    return tex[start:end]


def _body(tex: str) -> str:
    return "\n".join(_split_tex_comment(line)[0] for line in tex.splitlines())


def _flat(tex: str) -> str:
    return " ".join(_body(tex).split()).lower()


def _between(tex: str, start: str, end: str | None = None) -> str:
    marker = rf"\label{{{start}}}"
    assert marker in tex, f"missing scientific section {start}"
    result = tex.split(marker, 1)[1]
    return result.split(rf"\label{{{end}}}", 1)[0] if end else result


def _abstract(tex: str) -> str:
    return tex.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0]


def _has_provenance(tex: str) -> bool:
    comments = " ".join(_split_tex_comment(line)[1] for line in tex.splitlines())
    paths = [
        ROOT / rel.rstrip(".)`")
        for rel in re.findall(r"(?:artifacts|configs|docs)/[^\s;,]+", comments)
    ]
    return (
        bool(paths)
        and all(path.is_file() for path in paths)
        and bool(re.search(r"s\d+-[a-z0-9-]+|ADR-\d{4}", comments))
    )


def _referenced_provenance(block: str, tex: str) -> bool:
    for label in re.findall(r"\\ref\{([^}]+)\}", _body(block)):
        if label.startswith("tab:"):
            target = _table_block(tex, label)
        elif label.startswith("sec:"):
            target = re.split(r"\\(?:sub)?section\{", _between(tex, label), maxsplit=1)[0]
        else:
            continue
        if _has_provenance(target):
            return True
    return False


def _quantitative_provenance_errors(tex: str) -> list[str]:
    """Associate wrapped result sentences with paragraph/table-row sources.

    The independent scientific reading judges meaning. This guard catches
    numerical observations without local evidence, while allowing formal
    horizon definitions, interval decision rules and typesetting dimensions.
    An explicit table/section reference may carry the cited measurement.
    """
    if r"\begin{document}" in tex:
        tex = tex.split(r"\begin{document}", 1)[1]
    quant = re.compile(r"\d+/\d+|(?<![\w])[-+]?\d+\.\d+|\$[-+]?\d+(?:\.\d+)?|\d+\\%")
    missing = []
    for block in re.split(r"\n\s*\n", tex):
        body = _body(block).strip()
        quantities = quant.findall(body)
        boundary_definition = (
            bool(quantities)
            and set(quantities) <= {"$0", "$1"}
            and not re.search(r"\d+/\d+|\d+\.\d+", body)
            and re.search(r"\$W\$|T/W|[Ff]ull eviction|[Пп]олное вытеснение", body)
            and re.search(r"turnover|оборот", body, re.I)
            and not re.search(r"validated|observed gap|измеренный зазор", body, re.I)
        )
        if (
            quantities
            and not boundary_definition
            and not (_has_provenance(block) or _referenced_provenance(block, tex))
        ):
            missing.append(" ".join(body.split())[:180])
    for line in tex.splitlines():
        body, _ = _split_tex_comment(line)
        if (
            "&" in body
            and re.search(r"\d+/\d+|[-+]?\d+\.\d+", body)
            and body.rstrip().endswith(r"\\")
            and not _has_provenance(line)
        ):
            missing.append("unsourced table row: " + body.strip())
    return missing


def test_quantitative_claims_have_local_provenance() -> None:
    for name, tex in _papers():
        assert not (missing := _quantitative_provenance_errors(tex)), (name, missing)


def test_provenance_guard_accepts_wraps_not_unsourced_new_results() -> None:
    source = "% artifacts/occupancy-replication/domain_separation_last_band.csv @ s5-lock-occupancy-repl-20260907T091450Z-e8452acb"
    claim = "The measured gap is $0.208$ with interval $[0.091, 0.314]$. "
    assert not _quantitative_provenance_errors(claim + source)
    assert not _quantitative_provenance_errors(claim.replace(" with ", "\nwith ") + source)
    assert _quantitative_provenance_errors(claim)
    assert _quantitative_provenance_errors("The reported value is $0.999$.")
    assert _quantitative_provenance_errors(claim + source + "\n\nThe measured gap is $0.999$.")
    assert not _quantitative_provenance_errors("Full eviction is turnover $1$.")


def test_protocol_and_block_size_are_explicit() -> None:
    for name, tex in _papers():
        methods = _between(tex, "sec:methods", "sec:results")
        assert r"B{=}1024" in methods and r"B{=}512" not in methods, name
        assert "0.25" in methods, name
        assert r"raw\_completion" in methods and "Alibaba" in methods, name
        assert "P1" in methods and "P2" in methods, name
        assert re.search(r"not measured|не измерялась", _flat(methods)), name
        assert re.search(r"same block|том же блоке", _flat(methods)), name


def test_unestablished_results_are_explicit_not_banned_words() -> None:
    for name, tex in _papers():
        negative = _flat(_between(tex, "sec:not", "sec:limitations"))
        assert re.search(r"h1.{0,140}unsupported|h1.{0,180}не поддержана", negative), name
        assert re.search(
            r"half-life.{0,200}not measured|полураспада.{0,200}не измерялось", negative
        ), name
        assert re.search(r"currents.{0,100}not obtained|токи.{0,100}не получены", negative), name
        assert re.search(r"not a temperature law|не является температурным законом", negative), name
        assert re.search(r"not a scaling law|не образуют закона масштабирования", negative), name
        head = _flat(_abstract(tex))
        assert re.search(
            r"establish neither.{0,130}metastable|не устанавливают ни.{0,160}метастабиль", head
        ), name
        assert not re.search(r"h1 is established|h5 is present", _flat(tex)), name


def test_abstract_gap_is_not_recovered_memory() -> None:
    for name, tex in _papers():
        head = _flat(_abstract(tex))
        assert re.search(r"last-band gap|зазор в последней полосе", head), name
        assert "replication" in head or "репликаци" in head, name
        assert re.search(
            r"neither recovered semantic memory|ни восстановление семантической памяти", head
        ), name
        assert "seed-domain identity" not in head and "carries seed-domain" not in head, name


def test_twins_are_underpowered_not_equivalent_or_one_lock() -> None:
    for name, tex in _papers():
        negative = _flat(_between(tex, "sec:not", "sec:limitations"))
        assert re.search(r"underpowered|низкую статистическую мощность", negative), name
        assert re.search(
            r"equivalence.{0,100}not claimed|эквивалентность.{0,100}не утверждается", negative
        ), name
        assert not re.search(r"collapsed(?: twins)? occupy one lock", _flat(tex)), name


def test_bernoulli_intervals_are_not_point_masses() -> None:
    for name, tex in _papers():
        assert not re.search(r"\[0,\s*0\]|\[1,\s*1\]", _body(tex)), name
        repetition = _between(tex, "sec:repetition", "sec:dependence")
        assert re.search(r"Clopper|Клоппера", repetition), name
        assert "19/20" in repetition and "[0.751, 0.999]" in repetition, name


def test_hosted_axis_remains_temperature_specific() -> None:
    for name, tex in _papers():
        repetition = _between(tex, "sec:repetition", "sec:dependence")
        assert r"n{=}4" in repetition, name
        assert "fixed_point_rates_by_temperature.csv" in repetition, name
        assert "0/4" in repetition and "4/4" in repetition, name
        assert not re.search(r"temperature.{0,30}0\.3.{0,80}0/8", _flat(repetition)), name


def test_primary_replication_and_archival_outputs_are_distinct() -> None:
    for name, tex in _papers():
        dependence = _flat(_between(tex, "sec:dependence", "sec:families"))
        assert re.search(
            r"primary evidence is the occupancy replication|основное доказательство --- репликация",
            dependence,
        ), name
        assert re.search(
            r"not the primary evidence|не служит основным доказательством", dependence
        ), name
        archival = _table_block(tex, "tab:archival")
        replication = _table_block(tex, "tab:repl")
        for value in ("0.201", "0.390", "0.150", "[0.065, 0.332]", "0.029"):
            assert value in archival, name
        for value in ("0.208", "0.400", "0.152", "[0.091, 0.314]"):
            assert value in replication and value not in archival, name
        assert r"n_{\mathrm{within}}{=}6" in replication, name
        loss = _flat(_between(tex, "sec:archival", "sec:results"))
        assert "ADR-0021" in _between(tex, "sec:archival", "sec:results"), name
        assert re.search(r"cannot be recomputed|нельзя пересчитать", loss), name
        assert re.search(
            r"new draw does not restore|новая стохастическая реализация их не восстанавливает", loss
        ), name


def test_family_completion_rows_match_artifacts_without_pooling() -> None:
    cases = [
        (9, "Qwen3-8B", "Base", "base-nf4"),
        (9, "Qwen3-8B", "Instruct", "instruct-nf4"),
        (10, "OLMo-3-7B", "Base", "base-nf4"),
        (10, "OLMo-3-7B", "SFT", "sft-nf4"),
        (10, "OLMo-3-7B", "DPO", "dpo-nf4"),
        (10, "OLMo-3-7B", "RLVR", "rlvr-nf4"),
        (11, "Ministral-3-8B", "Base", "ministral-base"),
        (11, "Ministral-3-8B", "Instruct", "ministral-instruct"),
        (11, "Gemma-4-12B", "Base", "gemma-base"),
        (11, "Gemma-4-12B", None, "gemma-it"),
    ]
    for name, tex in _papers():
        table = _body(_table_block(tex, "tab:completion"))
        rows = [line for line in table.splitlines() if "&" in line and "/" in line]
        assert len(rows) == len(cases), name
        for stage, family, checkpoint, cell in cases:
            path = ARTIFACTS / f"stage-{stage}/generate_status/generate_status.csv"
            with path.open(encoding="utf-8", newline="") as handle:
                record = next(row for row in csv.DictReader(handle) if row["cell"] == cell)
            row = next(
                line
                for line in rows
                if line.split("&")[0].strip() == family
                and (
                    (line.split("&")[1].strip() == checkpoint)
                    if checkpoint
                    else (line.split("&")[1].strip() != "Base")
                )
            )
            assert f"{record['n_completed']}/{record['n_planned']}" in row, (name, cell)
        families = _flat(_between(tex, "sec:families", "sec:long"))
        assert re.search(r"not a pooled frequency|не образуют объединённую частоту", families), name
        assert re.search(
            r"not a demonstrated equivalence|не доказывают эквивалентность", families
        ), name


def test_gemma_signs_do_not_become_cross_space_disagreement() -> None:
    for name, tex in _papers():
        families = _flat(_between(tex, "sec:families", "sec:long"))
        for value in (
            "-0.010628",
            "-0.0377395",
            "-0.00608505",
            "0.0141659",
            "-0.0208935",
            "0.0186512",
        ):
            assert value in families, name
        assert re.search(r"established negative gap|установленный отрицательный зазор", families), (
            name
        )
        assert re.search(r"sign is not established|знак не установлен", families), name
        assert re.search(
            r"common cross-space sign is not established|общий знак для двух пространств не установлен",
            families,
        ), name
        assert not re.search(
            r"cross-space disagreement|spaces do not agree|не согласуется между пространствами",
            _flat(tex),
        ), name
        assert re.search(
            r"nothing.{0,100}causal role for attention|не позволяет установить причинную роль устройства внимания",
            families,
        ), name


def test_s12_absolute_clock_selected_cohort_and_right_censoring() -> None:
    meta = json.loads((ARTIFACTS / "stage-12/tau_escape/tau_escape.meta.json").read_text())
    assert "4,999,168" in meta["caption"]
    for name, tex in _papers():
        long = _flat(_between(tex, "sec:long", "sec:not")).replace("{,}", ",")
        for value in ("0/8", "4,999,168", "0.75", "1220.5", "1219.75", "l0"):
            assert value in long, name
        assert re.search(r"first token|первого токена", long), name
        assert re.search(r"selected|отобран", long), name
        assert re.search(
            r"not.*mean time to escape|не устанавливает среднее время до выхода", long
        ), name
        assert re.search(
            r"does not show.{0,40}permanent|не показывает, что режим постоянен", long
        ), name
        assert re.search(
            r"not a proof of an absorbing state|не доказательство поглощающего состояния", long
        ), name
        assert re.search(r"rather than pooled into a rate|не объединяются в одну частоту", long), (
            name
        )


def test_required_limits_no_attention_necessity_claim() -> None:
    for name, tex in _papers():
        limits = _flat(_between(tex, "sec:limitations", "sec:discussion"))
        for pattern in (
            r"re-prompt",
            r"continuous.*cache|непрерывн.*кэш",
            r"nf4",
            r"provider non-determinism|недетерминизм провайдера",
            r"finite|конечен",
            r"two pipelines|два вычислительных конвейера",
            r"survivors|выжившим",
            r"style|стиль",
        ):
            assert re.search(pattern, limits), (name, pattern)
        assert not re.search(
            r"we (?:show|prove|establish).{0,80}full attention.{0,40}(?:unnecessary|dispensable)",
            _flat(tex),
        ), name


def test_figures_have_existing_artifact_sources_and_reproducers() -> None:
    script = (ROOT / "paper/compile.sh").read_text(encoding="utf-8")
    for name, tex in _papers():
        includes = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", _body(tex))
        assert includes, name
        for rel in includes:
            assert not Path(rel).is_absolute() and ".." not in Path(rel).parts, rel
            if rel.startswith("build/figures/"):
                match = re.search(r'FIGURE_SOURCE="\$\{ROOT\}/\.\./(artifacts/[^"\n]+)"', script)
                assert match, "derived include has no declared artifact source"
                source = ROOT / match.group(1)
                assert source.stem == Path(rel).stem and source.suffix == ".svg", rel
                assert f"${{FIGURE_BUILD}}/{Path(rel).name}" in script, rel
                assert "rsvg-convert --format=pdf" in script, rel
                assert 'sed -f "${ROOT}/figure-layout.sed" "${FIGURE_SOURCE}"' in script, rel
                assert (ROOT / "paper/figure-layout.sed").is_file()
            else:
                source = ARTIFACTS / rel
            assert source.is_file() and source.resolve().is_relative_to(ARTIFACTS.resolve()), rel
            stem = source.with_suffix("")
            assert Path(str(stem) + ".data.parquet").is_file(), rel
            assert Path(str(stem) + ".meta.json").is_file(), rel


def test_mirror_math_and_structural_reference_parity() -> None:
    en, ru = _tex(), _tex_ru()
    math = r"(?<!\\)\$(.*?)(?<!\\)\$"
    assert re.findall(math, _body(en), re.S) == re.findall(math, _body(ru), re.S)
    for command in ("label", "ref"):
        pattern = rf"\\{command}\{{([^}}]+)\}}"
        assert re.findall(pattern, _body(en)) == re.findall(pattern, _body(ru))
    assert _cite_keys(en) == _cite_keys(ru)
    assert re.findall(r"\\includegraphics[^\n]+", _body(en)) == re.findall(
        r"\\includegraphics[^\n]+", _body(ru)
    )


def test_all_structural_references_and_labels_resolve() -> None:
    for name, tex in _papers():
        labels = re.findall(r"\\label\{([^}]+)\}", _body(tex))
        assert len(labels) == len(set(labels)), name
        assert set(re.findall(r"\\ref\{([^}]+)\}", _body(tex))) <= set(labels), name
