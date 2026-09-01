"""``afterlife`` — the only supported entry point.

Every command that can spend money prints an estimate and the remaining budget
first, and refuses to cross a ceiling. Every command that produces a result
creates a run with a manifest.
"""

from __future__ import annotations

import asyncio
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import orjson
import pandas as pd
import typer
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .config import (
    ExecutionMode,
    ExperimentConfig,
    GeneratorConfig,
    get_settings,
    load_experiment_config,
    load_seed_bank,
)
from .costs import estimate_experiment, summarise
from .errors import AfterlifeError
from .hashing import sha256_obj
from .logging_utils import configure_logging, get_console, get_logger
from .provenance import git_state, read_manifest
from .runctx import run_context

app = typer.Typer(
    name="afterlife",
    help="Long-run semantic dynamics of LLMs beyond the context horizon.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_show_locals=False,
)
audit_app = typer.Typer(help="Stage 0 capability audits (measure, do not assume).")
app.add_typer(audit_app, name="audit")

logger = get_logger("cli")
console = get_console

ConfigOpt = Annotated[Path, typer.Option("--config", "-c", help="experiment config YAML")]


def _print_frame(
    frame: pd.DataFrame,
    title: str,
    *,
    columns: list[str] | None = None,
    max_rows: int = 40,
) -> None:
    """Print a frame for a human.

    ``columns`` selects a readable subset: audit frames carry 15-20 columns, and
    rich wraps every one of them into an unreadable ribbon. The full frame always
    goes to the artifact, so nothing is lost by narrowing the console view.
    """
    if frame.empty:
        console().print(f"[yellow]{title}: no rows[/yellow]")
        return
    view = frame[[c for c in columns if c in frame.columns]] if columns else frame
    hidden = len(frame.columns) - len(view.columns)
    table = Table(title=title, title_justify="left", header_style="bold")
    for column in view.columns:
        table.add_column(str(column), overflow="fold", max_width=30)
    for _, row in view.head(max_rows).iterrows():
        table.add_row(*[("" if pd.isna(v) else str(v)) for v in row.tolist()])
    console().print(table)
    notes: list[str] = []
    if len(frame) > max_rows:
        notes.append(f"{len(frame) - max_rows} more rows")
    if hidden > 0:
        notes.append(f"{hidden} more columns in the artifact")
    if notes:
        console().print(f"[dim]... {', '.join(notes)}[/dim]")


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------


@app.command()
def doctor() -> None:
    """Check the environment, credentials and paths. Costs nothing."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    paths = settings.paths.ensure()

    table = Table(title="afterlife doctor", title_justify="left", header_style="bold")
    table.add_column("check")
    table.add_column("value", overflow="fold")
    table.add_column("status")

    def row(name: str, value: Any, ok: bool | None) -> None:
        mark = (
            "[green]ok[/green]" if ok else ("[red]missing[/red]" if ok is False else "[dim]—[/dim]")
        )
        table.add_row(name, str(value), mark)

    row("version", __version__, None)
    row("python", platform.python_version(), None)
    row("platform", platform.platform(), None)
    row("repo root", paths.root, paths.root.is_dir())
    row("execution mode", settings.afterlife_execution_mode, None)
    row(
        "ROUTERAI_API_KEY",
        "set" if settings.has_key("routerai") else "not set",
        settings.has_key("routerai"),
    )
    row("OPENROUTER_API_KEY", "set" if settings.has_key("openrouter") else "not set", None)
    row("HF_TOKEN", "set" if settings.hf_token else "not set", None)
    row("runs dir", paths.runs, paths.runs.is_dir())
    row("artifacts dir", paths.artifacts, paths.artifacts.is_dir())
    row("cache dir", paths.cache, paths.cache.is_dir())
    row("budget per run", f"${settings.afterlife_budget_usd_per_run:.2f}", None)
    row("budget total", f"${settings.afterlife_budget_usd_total:.2f}", None)
    row("usd per rub", settings.afterlife_usd_per_rub, None)

    from .ledger import read_ledger

    entries = read_ledger(paths.ledger)
    spent = sum(float(e.get("cost_usd", 0.0)) for e in entries)
    row("spent so far", f"${spent:.4f} over {len(entries)} charges", None)

    for module in ("numpy", "pandas", "plotly", "seaborn", "tokenizers", "httpx"):
        try:
            imported = __import__(module)
            row(module, getattr(imported, "__version__", "?"), True)
        except ImportError:
            row(module, "not installed", False)
    for module in ("deeptime", "igraph", "leidenalg", "umap"):
        try:
            imported = __import__(module)
            row(f"{module} (dynamics extra)", getattr(imported, "__version__", "?"), True)
        except ImportError:
            row(f"{module} (dynamics extra)", "not installed (needed from Stage 3)", None)
    for module in ("torch", "transformers"):
        try:
            imported = __import__(module)
            row(f"{module} (local extra)", getattr(imported, "__version__", "?"), True)
        except ImportError:
            row(f"{module} (local extra)", "not installed (needed for api: local)", None)

    console().print(table)

    if not settings.has_key("routerai") and settings.afterlife_execution_mode is ExecutionMode.LIVE:
        console().print(
            Panel(
                "ROUTERAI_API_KEY is not set and the execution mode is `live`.\n"
                "Either fill in .env, or run offline:\n"
                '    $env:AFTERLIFE_EXECUTION_MODE="mock"',
                title="[yellow]action needed[/yellow]",
                border_style="yellow",
            )
        )


# ---------------------------------------------------------------------------
# plan / estimate
# ---------------------------------------------------------------------------


@app.command()
def plan(config: ConfigOpt) -> None:
    """Expand an experiment matrix without contacting any API."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    experiment, _resolved, config_sha = load_experiment_config(config)
    seed_bank = load_seed_bank(experiment.seed_bank)

    console().print(
        Panel(
            f"[bold]{experiment.stage}/{experiment.name}[/bold]  config {config_sha[:8]}\n"
            f"{experiment.description.strip()}",
            border_style="blue",
        )
    )
    frame = pd.DataFrame(experiment.cells)
    frame["turnovers"] = (frame["target_tokens"] / frame["W"]).round(1)
    _print_frame(
        frame.groupby(
            ["generator", "W", "block_size", "target_tokens", "turnovers"], as_index=False
        )
        .size()
        .rename(columns={"size": "n_trajectories"}),
        "matrix",
    )
    console().print(
        f"[bold]{experiment.n_trajectories}[/bold] trajectories, "
        f"{len(experiment.generators)} generator(s), "
        f"{len(experiment.embeddings)} representation space(s), "
        f"{len(experiment.semantic_seeds)} semantic seeds "
        f"x {len(experiment.stochastic_seeds)} stochastic seeds"
    )
    missing = [s for s in experiment.semantic_seeds if s not in {x.id for x in seed_bank.seeds}]
    if missing:
        raise typer.BadParameter(f"semantic seeds not in the seed bank: {missing}")


@app.command()
def estimate(config: ConfigOpt) -> None:
    """Forecast tokens, cost and wall-clock for an experiment matrix."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    experiment, _resolved, _sha = load_experiment_config(config)
    estimates = estimate_experiment(experiment)
    frame = pd.DataFrame([e.as_dict() for e in estimates])
    _print_frame(frame, "cost forecast (protocol P1: input = T x W / S)")

    total = summarise(estimates)
    from .ledger import read_ledger

    spent = sum(float(e.get("cost_usd", 0.0)) for e in read_ledger(settings.paths.ledger))
    remaining = settings.afterlife_budget_usd_total - spent

    unpriced = [
        g.slug
        for g in experiment.generators
        if g.price_usd_per_m_input is None and g.price_usd_per_m_output is None
    ]
    lines = [
        f"trajectories       {total['n_trajectories']:,}",
        f"input tokens       {total['input_tokens']:,}",
        f"output tokens      {total['output_tokens']:,}",
        f"forecast cost      ${total['total_usd']:.2f}  ({total['input_share']:.0%} of it input)",
        "stage budget       "
        + (f"${experiment.budget_usd:.2f}" if experiment.budget_usd else "not declared"),
        f"project remaining  ${remaining:.2f} of ${settings.afterlife_budget_usd_total:.2f}",
    ]
    console().print(Panel("\n".join(lines), title="forecast", border_style="blue"))

    if unpriced:
        console().print(
            Panel(
                "No prices configured for: " + ", ".join(unpriced) + ".\n"
                "Their forecast contribution is $0, which is a visible gap rather than a wrong "
                "number. Run `afterlife audit providers` and copy the measured prices into "
                "configs/models/generators.yaml before approving a spend.",
                title="[yellow]incomplete forecast[/yellow]",
                border_style="yellow",
            )
        )
    if experiment.budget_usd and total["total_usd"] > experiment.budget_usd:
        console().print(
            Panel(
                f"Forecast ${total['total_usd']:.2f} exceeds the declared stage budget of "
                f"${experiment.budget_usd:.2f}. Reduce the matrix rather than raising the budget, "
                "and say in the stage plan what statistical power was given up.",
                title="[red]over budget[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(code=2)


# ---------------------------------------------------------------------------
# audits
# ---------------------------------------------------------------------------


def _audit_setup(config: Path) -> tuple[Any, ExperimentConfig, dict[str, Any], str]:
    experiment, resolved, config_sha = load_experiment_config(config)
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    return settings, experiment, resolved, config_sha


def _run_async(coro: Any) -> Any:
    from .providers import close_clients

    async def wrapper() -> Any:
        try:
            return await coro
        finally:
            await close_clients()

    return asyncio.run(wrapper())


def _save_audit(
    context: Any,
    frame: pd.DataFrame,
    name: str,
    caption: str,
    *,
    suffix: str = "",
) -> None:
    """Write an audit table into the stage artifacts.

    ``suffix`` distinguishes the same audit run against different providers.
    Without it a cross-provider audit silently overwrites the first one's table,
    which is how a stage report ends up citing numbers from a provider it does
    not name.
    """
    from .reporting.tables import save_table
    from .viz.export import FigureMeta

    if suffix:
        name = f"{name}__{suffix}"
    out_dir = context.artifacts_dir / "audit"
    save_table(
        frame,
        out_dir,
        FigureMeta(
            name=name,
            caption=caption,
            run_ids=[context.run_id],
            git_sha=context.manifest.git.get("sha"),
            config_sha256=context.manifest.config_sha256,
            limitations=(
                "Audit tables are measured on short probes, not on the stage's generation "
                "regime. A passing tokenizer probe does not certify in-trajectory W "
                "arithmetic; an exact-match rate at 128 tokens and T=0.7 is the "
                "reproducibility the paper may claim for that probe, not for a 12-turnover "
                "trajectory."
            ),
        ),
    )
    frame.to_parquet(context.paths.data_dir / f"{name}.parquet", index=False)


@audit_app.command("providers")
def audit_providers_cmd(
    config: ConfigOpt = Path("configs/stages/stage0_audit.yaml"),
) -> None:
    """Per-endpoint capabilities, quantization and prices for every candidate model."""
    settings, experiment, resolved, sha = _audit_setup(config)
    from .audits import audit_providers
    from .providers import build_client

    with run_context(
        stage=experiment.stage,
        slug="audit-providers",
        config_resolved=resolved,
        config_sha256=sha,
        settings=settings,
        stage_budget_usd=experiment.budget_usd,
    ) as context:
        client = build_client(experiment.generators[0].api, settings, events=context.events)
        frame = _run_async(
            audit_providers(client, list(experiment.generators), events=context.events)
        )
        _print_frame(
            frame,
            "provider endpoints",
            columns=[
                "generator",
                "available",
                "provider_tag",
                "quantization",
                "context_length",
                "max_completion_tokens",
                "completions_advertised",
                "supports_seed",
                "price_usd_per_m_input",
                "price_usd_per_m_output",
                "status",
                "error",
            ],
        )
        _save_audit(
            context,
            frame,
            "s0_provider_endpoints",
            "Measured per-endpoint capabilities and prices for every candidate generator, as "
            "reported by the router. Availability, quantization and supported APIs are facts "
            "that later stage designs depend on; nothing here is taken from documentation. "
            "Prices are converted to USD with the provider's own currency multiplier.",
            suffix=client.name,
        )
        context.finish(n_rows=len(frame))


@audit_app.command("continuation")
def audit_continuation_cmd(
    config: ConfigOpt = Path("configs/stages/stage0_audit.yaml"),
    max_tokens: int = typer.Option(160, help="tokens per probe"),
) -> None:
    """Which continuation mechanisms actually work per model (raw / prefill / instructed)."""
    settings, experiment, resolved, sha = _audit_setup(config)
    from .audits import audit_continuation
    from .providers import build_client

    with run_context(
        stage=experiment.stage,
        slug="audit-continuation",
        config_resolved=resolved,
        config_sha256=sha,
        settings=settings,
        stage_budget_usd=experiment.budget_usd,
    ) as context:
        client = build_client(experiment.generators[0].api, settings, events=context.events)
        frame = _run_async(
            audit_continuation(
                client,
                list(experiment.generators),
                settings=settings,
                events=context.events,
                ledger=context.ledger,
                max_tokens=max_tokens,
            )
        )
        _print_frame(
            frame,
            "continuation mechanisms",
            columns=[
                "generator",
                "mechanism",
                "ok",
                "completion_tokens",
                "finish_reason",
                "prompt_tokens_api",
                "prompt_tokens_local",
                "prompt_token_delta",
                "looks_like_meta",
                "error",
            ],
        )
        _save_audit(
            context,
            frame,
            "s0_continuation_mechanisms",
            "For each candidate generator, all three continuation mechanisms are attempted: raw "
            "text completion, assistant prefill, and instruction-framed chat. Records whether the "
            "model continues the text, its finish reason, the local-vs-API prompt token delta "
            "(which reveals a server-side chat template), and whether the output looks like "
            "meta-commentary rather than continuation.",
            suffix=client.name,
        )
        context.finish(n_rows=len(frame))


@audit_app.command("reasoning")
def audit_reasoning_cmd(
    config: ConfigOpt = Path("configs/stages/stage0_audit.yaml"),
    max_tokens: int = typer.Option(96, help="tokens per probe"),
) -> None:
    """Can reasoning be switched off? A model that keeps reasoning is unusable here."""
    settings, experiment, resolved, sha = _audit_setup(config)
    from .audits import audit_reasoning
    from .providers import build_client

    with run_context(
        stage=experiment.stage,
        slug="audit-reasoning",
        config_resolved=resolved,
        config_sha256=sha,
        settings=settings,
        stage_budget_usd=experiment.budget_usd,
    ) as context:
        client = build_client(experiment.generators[0].api, settings, events=context.events)
        frame = _run_async(
            audit_reasoning(
                client,
                list(experiment.generators),
                events=context.events,
                ledger=context.ledger,
                max_tokens=max_tokens,
            )
        )
        _print_frame(
            frame,
            "reasoning suppression",
            columns=[
                "generator",
                "switch",
                "accepted",
                "reasoning_tokens",
                "completion_tokens",
                "max_tokens_respected",
                "overshoot_ratio",
                "visible_chars",
                "usable",
                "error",
            ],
            max_rows=60,
        )
        _save_audit(
            context,
            frame,
            "s0_reasoning_suppression",
            "For each generator, several candidate ways of switching reasoning off are attempted "
            "and the resulting reasoning-token count, visible output length and max_tokens "
            "compliance recorded. Reasoning tokens are disqualifying here: the block appended to "
            "the window would be only the visible part of what the model generated, max_tokens "
            "would stop bounding the block, and the reasoning text is meta-commentary rather "
            "than free continuation.",
            suffix=client.name,
        )
        context.finish(n_rows=len(frame))


@audit_app.command("determinism")
def audit_determinism_cmd(
    config: ConfigOpt = Path("configs/stages/stage0_audit.yaml"),
    repeats: int = typer.Option(5, help="identical seeded requests per model"),
    temperature: float = typer.Option(0.7),
) -> None:
    """Measure, do not assume, the reproducibility of seeded requests."""
    settings, experiment, resolved, sha = _audit_setup(config)
    from .audits import audit_determinism
    from .providers import build_client

    with run_context(
        stage=experiment.stage,
        slug="audit-determinism",
        config_resolved=resolved,
        config_sha256=sha,
        settings=settings,
        stage_budget_usd=experiment.budget_usd,
    ) as context:
        client = build_client(experiment.generators[0].api, settings, events=context.events)
        frame = _run_async(
            audit_determinism(
                client,
                list(experiment.generators),
                events=context.events,
                ledger=context.ledger,
                n_repeats=repeats,
                temperature=temperature,
            )
        )
        _print_frame(
            frame,
            "determinism",
            columns=[
                "generator",
                "n_responses",
                "exact_match_rate",
                "mean_similarity",
                "min_similarity",
                "distinct_outputs",
                "served_providers",
                "errors",
            ],
        )
        _save_audit(
            context,
            frame,
            "s0_determinism",
            f"Exact-match and similarity rates over {repeats} identical seeded requests per model "
            f"at temperature {temperature}. This number, and not an assumption, determines the "
            "reproducibility level the paper may claim.",
            suffix=client.name,
        )
        context.finish(n_rows=len(frame))


@audit_app.command("embeddings")
def audit_embeddings_cmd(
    config: ConfigOpt = Path("configs/stages/stage0_audit.yaml"),
) -> None:
    """Dimension, normalisation, latency and cross-domain separation per embedding model."""
    settings, experiment, resolved, sha = _audit_setup(config)
    from .audits import audit_embeddings
    from .providers import build_client

    if not experiment.embeddings:
        raise typer.BadParameter("this config declares no embeddings")

    with run_context(
        stage=experiment.stage,
        slug="audit-embeddings",
        config_resolved=resolved,
        config_sha256=sha,
        settings=settings,
        stage_budget_usd=experiment.budget_usd,
    ) as context:
        client = build_client(experiment.embeddings[0].api, settings, events=context.events)
        frame = _run_async(
            audit_embeddings(
                client,
                list(experiment.embeddings),
                events=context.events,
                ledger=context.ledger,
            )
        )
        _print_frame(
            frame,
            "embedding models",
            columns=[
                "embedding",
                "architecture",
                "available",
                "dim",
                "dim_matches_expected",
                "provider_normalised",
                "mean_cross_domain_cosine",
                "max_cross_domain_cosine",
                "latency_s",
                "cost_usd",
                "error",
            ],
        )
        _save_audit(
            context,
            frame,
            "s0_embeddings",
            "Measured dimension, whether the provider returns L2-normalised vectors, latency, "
            "cost, and the cosine similarity between three probe texts from unrelated domains. "
            "A space that cannot separate the probes cannot support anything downstream.",
            suffix=client.name,
        )
        context.finish(n_rows=len(frame))


@audit_app.command("tokenizers")
def audit_tokenizers_cmd(
    config: ConfigOpt = Path("configs/stages/stage0_audit.yaml"),
) -> None:
    """Round-trip integrity of every generator tokenizer. A gate, not a diagnostic."""
    settings, experiment, resolved, sha = _audit_setup(config)
    from .audits import audit_tokenizers

    with run_context(
        stage=experiment.stage,
        slug="audit-tokenizers",
        config_resolved=resolved,
        config_sha256=sha,
        settings=settings,
    ) as context:
        frame = audit_tokenizers(
            list(experiment.generators), settings=settings, events=context.events
        )
        _print_frame(
            frame,
            "tokenizers",
            columns=[
                "generator",
                "tokenizer_repo",
                "loaded",
                "vocab_size",
                "roundtrip_all_ok",
                "n_roundtrip_failures",
                "tail_exact",
                "probe_tokens",
                "error",
            ],
        )
        _save_audit(
            context,
            frame,
            "s0_tokenizers",
            "Round-trip integrity (decode(encode(x)) == x) for every generator tokenizer across "
            "ASCII, Unicode, whitespace and long-repetition probes, plus exactness of the tail "
            "operation the sliding window relies on. A failure invalidates W for that model.",
        )
        context.finish(n_rows=len(frame))


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------


@app.command()
def generate(
    config: ConfigOpt,
    yes: bool = typer.Option(False, "--yes", "-y", help="skip the cost confirmation"),
) -> None:
    """Generate trajectories. Prints a forecast and waits for confirmation first."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    experiment, resolved, sha = load_experiment_config(config)
    seed_bank = load_seed_bank(experiment.seed_bank)

    estimates = estimate_experiment(experiment)
    total = summarise(estimates)
    console().print(
        Panel(
            f"{total['n_trajectories']} trajectories, {total['input_tokens']:,} input + "
            f"{total['output_tokens']:,} output tokens, forecast "
            f"[bold]${total['total_usd']:.2f}[/bold]",
            title=f"about to run {experiment.stage}/{experiment.name}",
            border_style="blue",
        )
    )
    if settings.afterlife_execution_mode is ExecutionMode.LIVE and not yes:
        typer.confirm("proceed?", abort=True)

    from .generation.trajectory import (
        collect_chunks,
        plan_trajectories,
        results_to_frame,
        run_trajectories,
    )
    from .providers import build_client
    from .tokenization import describe, load_tokenizer

    with run_context(
        stage=experiment.stage,
        slug=experiment.name,
        config_resolved=resolved,
        config_sha256=sha,
        settings=settings,
        stage_budget_usd=experiment.budget_usd,
    ) as context:
        tokenizers: dict[str, Any] = {}

        def tokenizer_for(generator: GeneratorConfig) -> Any:
            if generator.slug not in tokenizers:
                tokenizers[generator.slug] = load_tokenizer(
                    generator.tokenizer_repo,
                    generator.tokenizer_revision,
                    str(settings.paths.tokenizer_cache),
                )
                context.manifest.endpoints.setdefault("tokenizers", {})[generator.slug] = describe(
                    tokenizers[generator.slug]
                )
            return tokenizers[generator.slug]

        def client_for(generator: GeneratorConfig) -> Any:
            return build_client(generator.api, settings, events=context.events)

        planned = plan_trajectories(experiment, seed_bank)
        context.manifest.seeds = {
            "semantic": {s.id: {"domain": s.domain, "chars": len(s.text)} for s in seed_bank.seeds},
            "stochastic": list(experiment.stochastic_seeds),
            "seed_bank": experiment.seed_bank,
        }
        context.manifest.write(context.paths)

        results, runners = _run_async(
            run_trajectories(
                planned,
                settings=settings,
                paths=context.paths,
                events=context.events,
                ledger=context.ledger,
                client_for=client_for,
                tokenizer_for=tokenizer_for,
                max_concurrent=experiment.max_concurrent,
            )
        )

        chunks = pd.DataFrame(collect_chunks(runners))
        if not chunks.empty:
            chunks.to_parquet(context.paths.chunks(), index=False)

        summary = results_to_frame(results)
        summary.to_parquet(context.paths.data_dir / "trajectories.parquet", index=False)
        context.manifest.trajectories = {r.trajectory_id: r.as_dict() for r in results}
        _print_frame(
            summary[
                [
                    "trajectory_id",
                    "status",
                    "generated_tokens",
                    "n_steps",
                    "n_chunks",
                    "stop_event_rate",
                    "roundtrip_failures",
                    "cost_usd",
                ]
            ],
            "trajectories",
        )

        n_ok = int((summary["status"] == "COMPLETED").sum())
        console().print(
            f"[bold]{n_ok}/{len(summary)}[/bold] trajectories completed; "
            f"{len(chunks)} chunks; spent ${context.ledger.run_spend_usd:.4f}"
        )
        if n_ok < len(summary):
            console().print(
                "[yellow]failed trajectories are recorded in the manifest and must be reported as "
                "missing data, not silently excluded[/yellow]"
            )

        context.finish(
            status="COMPLETED" if n_ok else "FAILED",
            n_trajectories=len(summary),
            n_completed=n_ok,
            n_chunks=len(chunks),
        )
        console().print(f"run_id: [bold]{context.run_id}[/bold]")


# ---------------------------------------------------------------------------
# embed
# ---------------------------------------------------------------------------


@app.command()
def embed(
    run: Annotated[str, typer.Option("--run", "-r", help="generation run_id")],
    config: ConfigOpt,
) -> None:
    """Embed a generation run's chunks in every configured representation space."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    experiment, resolved, sha = load_experiment_config(config)
    source = settings.paths.find_run(run)
    chunks = pd.read_parquet(source.chunks())

    from .embeddings import Embedder
    from .providers import build_client

    with run_context(
        stage=experiment.stage,
        slug=f"embed-{experiment.name}",
        config_resolved={**resolved, "source_run_id": run},
        config_sha256=sha_with_source(sha, run),
        settings=settings,
        stage_budget_usd=experiment.budget_usd,
    ) as context:
        context.note(f"embedding source run {run}")
        texts = chunks["text"].tolist()
        for embedding_config in experiment.embeddings:
            embedder = Embedder(
                embedding_config,
                client=build_client(embedding_config.api, settings, events=context.events),
                cache_root=settings.paths.embedding_cache,
                events=context.events,
                ledger=context.ledger,
                tokens_per_text_estimate=int(chunks["n_tokens"].mean()) if len(chunks) else 1024,
            )
            matrix = _run_async(embedder.embed(texts))
            frame = chunks.drop(columns=["text"]).copy()
            for index in range(matrix.shape[1]):
                frame[f"e{index}"] = matrix[:, index]
            target = context.paths.embeddings(embedding_config.slug)
            frame.to_parquet(target, index=False)
            context.manifest.endpoints.setdefault("embeddings", {})[embedding_config.slug] = (
                embedder.stats()
            )
            console().print(
                f"{embedding_config.slug}: {matrix.shape[0]} x {matrix.shape[1]} -> {target.name}"
            )
        context.finish(n_chunks=len(chunks), source_run_id=run)
        console().print(f"run_id: [bold]{context.run_id}[/bold]")


def sha_with_source(config_sha: str, run_id: str) -> str:
    return sha256_obj({"config": config_sha, "source_run": run_id})


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

analyze_app = typer.Typer(help="Analysis passes over stored trajectories.")
app.add_typer(analyze_app, name="analyze")


def _source_chunks(run: Any) -> pd.DataFrame | None:
    """Chunk texts for an embedding run, found via its manifest's source run.

    Geometry needs them to label degenerate trajectories: a looping trajectory
    occupies one point in representation space and will report a confined MSD for
    reasons that have nothing to do with semantics. Reporting an exponent without
    that label is the mistake S1.0 made by hand.
    """
    manifest = read_manifest(run.manifest)
    source_id = (manifest.get("config_resolved") or {}).get("source_run_id") or (
        manifest.get("totals") or {}
    ).get("source_run_id")
    if not source_id:
        return None
    try:
        source = get_settings().paths.find_run(str(source_id))
    except FileNotFoundError:
        return None
    return pd.read_parquet(source.chunks()) if source.chunks().is_file() else None


def _degeneracy_labels(chunks: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-trajectory degeneracy verdicts and per-chunk diagnostics."""
    from .analysis.degeneracy import DegeneracyParams, compute_degeneracy

    params = DegeneracyParams()
    per_chunk: list[pd.DataFrame] = []
    verdicts: list[dict[str, Any]] = []
    for trajectory_id, block in chunks.groupby("trajectory_id", sort=True):
        block = block.sort_values("chunk_index")
        result = compute_degeneracy(
            block["text"].tolist(),
            trajectory_id=str(trajectory_id),
            token_ends=block["token_end"].to_numpy(),
            W=int(block["W"].iloc[0]),
            params=params,
        )
        per_chunk.append(result.per_chunk)
        verdicts.append(
            {
                "trajectory_id": str(trajectory_id),
                "degenerate": bool(result.is_degenerate),
                **{k: v for k, v in result.scalars.items() if k != "degenerate"},
            }
        )
    return pd.DataFrame(verdicts), pd.concat(per_chunk, ignore_index=True)


@analyze_app.command("geometry")
def analyze_geometry(
    run: Annotated[str, typer.Option("--run", "-r", help="run_id holding the embeddings")],
    embedding: Annotated[str, typer.Option("--embedding", "-e")] = "",
    burn_in_turnovers: float = typer.Option(1.0, help="1.0 = discard up to the context horizon"),
) -> None:
    """Displacement, drift, MSD, autocorrelation and recurrence, with figures."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    source = settings.paths.find_run(run)
    manifest = read_manifest(source.manifest)

    candidates = sorted(source.data_dir.glob("embeddings_*.parquet"))
    if not candidates:
        raise typer.BadParameter(f"run {run} has no embeddings; run `afterlife embed` first")
    chosen = source.embeddings(embedding) if embedding else candidates[0]
    if not chosen.is_file():
        raise typer.BadParameter(f"{chosen.name} not found in run {run}")
    slug = chosen.stem.removeprefix("embeddings_")

    from .analysis import GeometryParams, aggregate_msd, compute_geometry
    from .reporting.tables import save_table
    from .viz.export import FigureMeta, save_matplotlib_figure, save_plotly_figure, write_index
    from .viz.figures import (
        geometry_summary_panel,
        msd_figure,
        projection_figure,
        recurrence_figure,
        trajectory_series_figure,
    )

    frame = pd.read_parquet(chosen)
    embedding_columns = [c for c in frame.columns if c.startswith("e") and c[1:].isdigit()]
    params = GeometryParams(burn_in_turnovers=burn_in_turnovers)
    config_resolved = {
        "analysis": "geometry",
        "source_run_id": run,
        "embedding": slug,
        "params": params.model_dump(),
    }

    with run_context(
        stage=str(manifest.get("stage", "s0")),
        slug=f"geometry-{slug}",
        config_resolved=config_resolved,
        config_sha256=sha256_obj(config_resolved),
        settings=settings,
    ) as context:
        per_chunk_frames: list[pd.DataFrame] = []
        msd_frames: list[pd.DataFrame] = []
        acf_frames: list[pd.DataFrame] = []
        scalar_rows: list[dict[str, Any]] = []
        results = []

        for trajectory_id, block in frame.groupby("trajectory_id", sort=True):
            block = block.sort_values("chunk_index")
            Z = block[embedding_columns].to_numpy(dtype="float64")
            W = int(block["W"].iloc[0])
            result = compute_geometry(
                Z,
                trajectory_id=str(trajectory_id),
                token_positions=block["token_end"].to_numpy(),
                token_starts=block["token_start"].to_numpy(),
                W=W,
                params=params,
            )
            labels = {
                "semantic_seed": block["semantic_seed"].iloc[0],
                "generator": block["generator"].iloc[0],
                "temperature": float(block["temperature"].iloc[0]),
                "stochastic_seed": int(block["stochastic_seed"].iloc[0]),
                "W": W,
            }
            result.per_chunk = result.per_chunk.assign(**labels)
            per_chunk_frames.append(result.per_chunk)
            msd_frames.append(result.msd)
            acf_frames.append(result.autocorrelation)
            scalar_rows.append({"trajectory_id": trajectory_id, **labels, **result.scalars})
            results.append(result)
            context.events.event(
                "analysis.geometry.trajectory",
                trajectory_id=str(trajectory_id),
                scalars={k: float(v) for k, v in result.scalars.items()},
            )

        per_chunk = pd.concat(per_chunk_frames, ignore_index=True)
        msd_all = pd.concat(msd_frames, ignore_index=True)
        acf_all = pd.concat(acf_frames, ignore_index=True)
        scalars = pd.DataFrame(scalar_rows)
        aggregate = aggregate_msd(results)

        # Degeneracy labels are joined here, not left to the reader. An MSD
        # exponent from a looping trajectory measures the loop; publishing it
        # unlabelled is how a repetition artifact becomes a claim about
        # semantic confinement.
        chunks_source = _source_chunks(source)
        if chunks_source is not None:
            verdicts, degeneracy_chunks = _degeneracy_labels(chunks_source)
            # Degeneracy scalars reuse names (n_chunks, …). Drop the overlap so
            # the geometry columns keep their names; a merge suffix of
            # n_chunks_x / n_chunks_y made the published table unreadable.
            overlap = [c for c in verdicts.columns if c in scalars.columns and c != "trajectory_id"]
            scalars = scalars.merge(verdicts.drop(columns=overlap), on="trajectory_id", how="left")
            per_chunk = per_chunk.merge(
                degeneracy_chunks[["trajectory_id", "chunk_index", "ngram_repetition", "looping"]],
                on=["trajectory_id", "chunk_index"],
                how="left",
            )
            degeneracy_chunks.to_parquet(
                context.paths.data_dir / "degeneracy_per_chunk.parquet", index=False
            )
            n_degenerate = int(scalars["degenerate"].fillna(False).sum())
            context.events.event(
                "analysis.geometry.degeneracy_joined",
                n_trajectories=len(scalars),
                n_degenerate=n_degenerate,
                mirror=f"{n_degenerate}/{len(scalars)} trajectories flagged degenerate",
            )
            if n_degenerate:
                console().print(
                    f"[yellow]{n_degenerate} of {len(scalars)} trajectories are degenerate. "
                    "Their MSD exponents measure repetition, not semantics, and are labelled "
                    "as such in geometry_scalars and in every figure caption.[/yellow]"
                )
                context.note(
                    f"{n_degenerate}/{len(scalars)} trajectories degenerate; exponents from "
                    "those trajectories are not evidence about semantic dynamics"
                )
        else:
            scalars["degenerate"] = pd.NA
            console().print(
                "[yellow]source chunk texts not found, so trajectories could not be checked "
                "for degeneracy. Any confinement result from this run is unqualified and must "
                "not be reported.[/yellow]"
            )
            context.note("degeneracy labels unavailable: source chunks not found")

        for name, table in (
            ("per_chunk", per_chunk),
            ("msd_per_trajectory", msd_all),
            ("autocorrelation", acf_all),
            ("scalars", scalars),
            ("msd_ensemble", aggregate),
        ):
            table.to_parquet(context.paths.data_dir / f"geometry_{name}.parquet", index=False)

        out_dir = context.artifacts_dir / f"geometry-{slug}"
        W = int(scalars["W"].iloc[0])
        chunk_size = int(frame["chunk_size"].iloc[0])
        git_sha = context.manifest.git.get("sha")

        def export_plotly(bundle: tuple[Any, Any, FigureMeta]) -> None:
            figure, data, meta = bundle
            meta.git_sha = git_sha
            meta.config_sha256 = context.manifest.config_sha256
            save_plotly_figure(figure, out_dir, meta, data=data)

        export_plotly(
            trajectory_series_figure(
                per_chunk,
                value_column="step_displacement",
                W=W,
                title="Semantic velocity along free-running generation",
                y_title="1 − cos(z_k, z_{k+1})",
                caption=(
                    f"Per-step cosine displacement between consecutive {chunk_size}-token chunks, "
                    f"for each trajectory (thin) with the per-seed ensemble mean and 95% CI "
                    f"(thick). W={W:,} generator tokens; the context horizon and its multiples are "
                    "marked. A rising curve means the trajectory is moving faster through "
                    "representation space; a flat one means a steady rate of semantic change."
                ),
                run_ids=[run, context.run_id],
                name="semantic_velocity",
                limitations=(
                    "Displacement rate alone cannot distinguish a confined trajectory that moves "
                    "quickly within a small region from one that drifts steadily away."
                ),
            )
        )
        export_plotly(
            trajectory_series_figure(
                per_chunk,
                value_column="distance_from_origin",
                W=W,
                title="Drift away from the trajectory's own origin",
                y_title="1 − cos(z_k, z_0)",
                caption=(
                    "Cosine distance from each trajectory's first chunk. Saturation indicates a "
                    "bounded semantic region; continued growth indicates directed drift. The "
                    "context horizon t = W is where the seed has fully left the model's input."
                ),
                run_ids=[run, context.run_id],
                name="drift_from_origin",
                limitations=(
                    "Distance from a single reference chunk is not a measure of the number or "
                    "separation of semantic states."
                ),
            )
        )
        export_plotly(
            msd_figure(
                msd_all,
                aggregate,
                scalars,
                chunk_size=chunk_size,
                W=W,
                run_ids=[run, context.run_id],
            )
        )
        export_plotly(
            projection_figure(
                frame[embedding_columns].to_numpy(dtype="float64"),
                frame[["trajectory_id", "chunk_index", "semantic_seed", "turnover"]],
                W=W,
                chunk_size=chunk_size,
                run_ids=[run, context.run_id],
            )
        )

        for result in results[:4]:
            if result.recurrence is None:
                continue
            rqa = {
                k: v
                for k, v in result.scalars.items()
                if k.startswith(
                    ("recurrence", "determinism", "mean_diagonal", "max_diagonal", "trapping")
                )
            }
            export_plotly(
                recurrence_figure(
                    result.recurrence,
                    trajectory_id=result.trajectory_id,
                    chunk_size=chunk_size,
                    W=W,
                    epsilon=result.scalars.get("recurrence_epsilon", float("nan")),
                    rqa=rqa,
                    run_ids=[run, context.run_id],
                )
            )

        figure, data, meta = geometry_summary_panel(
            per_chunk, scalars, W=W, run_ids=[run, context.run_id]
        )
        meta.git_sha = git_sha
        save_matplotlib_figure(figure, out_dir, meta, data=data)

        save_table(
            scalars.drop(columns=["burn_in_applied"], errors="ignore"),
            out_dir,
            FigureMeta(
                name="geometry_scalars",
                caption=(
                    "Per-trajectory geometry summary: post-horizon displacement statistics, fitted "
                    "MSD exponent with its standard error and fit quality, plateau level, and "
                    "integrated autocorrelation time (the effective spacing between independent "
                    "chunk observations). The `degenerate` column carries the calibrated "
                    "degeneracy verdict for the same trajectory."
                ),
                run_ids=[run, context.run_id],
                git_sha=git_sha,
                limitations=(
                    "An MSD exponent from a trajectory marked `degenerate` measures repetition, "
                    "not semantic motion, and is not evidence of confinement. Exponents are "
                    "fitted over a lag range bounded by the observed turnover count, so they "
                    "cannot establish asymptotic behaviour. Where `burn_in_applied` is 0 the "
                    "trajectory was too short to separate the post-horizon regime and the "
                    "statistics mix forced and free segments."
                ),
            ),
        )

        write_index(
            context.artifacts_dir,
            stage=str(manifest.get("stage", "s0")),
            title=f"Stage {manifest.get('stage', 's0')} artifacts",
        )
        console().print(f"artifacts -> {out_dir}")
        context.finish(
            n_trajectories=int(scalars.shape[0]),
            mean_msd_alpha=float(scalars["msd_alpha"].mean()),
        )
        console().print(f"run_id: [bold]{context.run_id}[/bold]")


@analyze_app.command("degeneracy")
def analyze_degeneracy(
    run: Annotated[str, typer.Option("--run", "-r", help="generation run_id holding chunks")],
) -> None:
    """Repetition, lexical variety and entropy per chunk, with a per-trajectory verdict.

    Degeneracy is measured and labelled, never filtered: a repetition loop is a
    dynamical state, and its rate is an order parameter. But it also invalidates
    any confinement claim drawn from the same trajectory, so it has to be known
    before the geometry is read.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    source = settings.paths.find_run(run)
    manifest = read_manifest(source.manifest)
    if not source.chunks().is_file():
        raise typer.BadParameter(f"run {run} has no chunks.parquet")

    from .analysis.degeneracy import DegeneracyParams
    from .reporting.tables import save_table
    from .viz.export import FigureMeta

    params = DegeneracyParams()
    config_resolved = {
        "analysis": "degeneracy",
        "source_run_id": run,
        "params": params.model_dump(),
    }
    with run_context(
        stage=str(manifest.get("stage", "s1")),
        slug="degeneracy",
        config_resolved=config_resolved,
        config_sha256=sha256_obj(config_resolved),
        settings=settings,
    ) as context:
        chunks = pd.read_parquet(source.chunks())
        verdicts, per_chunk = _degeneracy_labels(chunks)
        verdicts.to_parquet(context.paths.data_dir / "degeneracy_verdicts.parquet", index=False)
        per_chunk.to_parquet(context.paths.data_dir / "degeneracy_per_chunk.parquet", index=False)

        _print_frame(
            verdicts,
            "degeneracy verdicts",
            columns=[
                "trajectory_id",
                "degenerate",
                "looping_fraction",
                "mean_ngram_repetition",
                "mean_type_token_ratio",
                "mean_entropy_bits",
                "entropy_trend_per_turnover",
            ],
        )
        n_bad = int(verdicts["degenerate"].sum())
        console().print(
            f"[bold]{n_bad}/{len(verdicts)}[/bold] trajectories degenerate "
            f"(threshold {params.loop_repetition_threshold:.3f} = 99th percentile of natural "
            "prose; see scripts/calibrate_degeneracy.py)"
        )

        save_table(
            verdicts,
            context.artifacts_dir / "degeneracy",
            FigureMeta(
                name="degeneracy_verdicts",
                caption=(
                    "Per-trajectory degeneracy diagnostics. A chunk counts as looping when its "
                    f"{params.ngram}-gram repetition rate exceeds "
                    f"{params.loop_repetition_threshold:.3f}, the 99th percentile of natural "
                    "English prose chunked by the same tokenizer at the same size. A trajectory "
                    f"counts as degenerate when at least {params.loop_chunk_fraction:.0%} of its "
                    "post-horizon chunks are looping."
                ),
                run_ids=[run, context.run_id],
                git_sha=context.manifest.git.get("sha"),
                limitations=(
                    "Degeneracy is a surface-form measure. A trajectory can be lexically varied "
                    "and still semantically static, which is what the frozen-embedding check and "
                    "the geometry pass are for."
                ),
            ),
        )
        context.finish(n_trajectories=len(verdicts), n_degenerate=n_bad)
        console().print(f"run_id: [bold]{context.run_id}[/bold]")


@analyze_app.command("separation")
def analyze_separation(
    run: Annotated[str, typer.Option("--run", "-r", help="run_id holding the embeddings")],
    embedding: Annotated[str, typer.Option("--embedding", "-e")] = "",
    turnover_bin: float = typer.Option(2.0, help="width of the turnover bands reported"),
) -> None:
    """Does seed identity survive the context horizon? The Stage 1 verdict pass.

    Reports `D_between - D_within` per turnover band with a bootstrap CI over
    trajectories. `D_within` -- same semantic seed, different stochastic seed --
    is the control that makes the contrast interpretable; without it the pass
    refuses to run.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    source = settings.paths.find_run(run)
    manifest = read_manifest(source.manifest)

    candidates = sorted(source.data_dir.glob("embeddings_*.parquet"))
    if not candidates:
        raise typer.BadParameter(f"run {run} has no embeddings; run `afterlife embed` first")
    chosen = source.embeddings(embedding) if embedding else candidates[0]
    if not chosen.is_file():
        raise typer.BadParameter(f"{chosen.name} not found in run {run}")
    slug = chosen.stem.removeprefix("embeddings_")

    from .analysis.separation import SeparationParams, compute_separation, trajectories_from_frame
    from .reporting.tables import save_table
    from .viz.export import FigureMeta, save_plotly_figure
    from .viz.figures import separation_figure

    params = SeparationParams(turnover_bin=turnover_bin)
    config_resolved = {
        "analysis": "separation",
        "source_run_id": run,
        "embedding": slug,
        "params": params.model_dump(),
    }
    with run_context(
        stage=str(manifest.get("stage", "s1")),
        slug=f"separation-{slug}",
        config_resolved=config_resolved,
        config_sha256=sha256_obj(config_resolved),
        settings=settings,
    ) as context:
        frame = pd.read_parquet(chosen)
        trajectories = trajectories_from_frame(frame)
        result = compute_separation(trajectories, params=params)

        result.per_band.to_parquet(
            context.paths.data_dir / "separation_per_band.parquet", index=False
        )
        result.pairs.to_parquet(context.paths.data_dir / "separation_pairs.parquet", index=False)

        _print_frame(
            result.per_band,
            f"seed separation ({slug})",
            columns=[
                "band",
                "d_within",
                "d_between",
                "gap",
                "gap_ci_low",
                "gap_ci_high",
                "separated",
                "n_within_pairs",
                "n_between_pairs",
            ],
        )
        verdict = (
            "seed identity persists past the horizon"
            if result.scalars["separated_at_last_band"]
            else "no separation detected at the last observed band"
        )
        console().print(
            f"[bold]{verdict}[/bold]  |  post-horizon mean gap "
            f"{result.scalars['gap_post_horizon_mean']:.4f}, trend "
            f"{result.scalars['gap_trend_per_turnover']:+.5f} per turnover"
        )

        W = int(frame["W"].iloc[0])
        figure, tidy, meta = separation_figure(
            result.per_band,
            W=W,
            embedding=slug,
            scalars=result.scalars,
            run_ids=[run, context.run_id],
        )
        meta.git_sha = context.manifest.git.get("sha")
        save_plotly_figure(figure, context.artifacts_dir / f"separation-{slug}", meta, data=tidy)

        save_table(
            result.per_band,
            context.artifacts_dir / f"separation-{slug}",
            FigureMeta(
                name="separation_per_band",
                caption=(
                    "Seed-separation contrast per turnover band. `d_within` is the mean cosine "
                    "distance between trajectories sharing a semantic seed and differing only in "
                    "their stochastic seed; `d_between` is the same across different semantic "
                    "seeds. `gap` is their difference, with a 95% bootstrap interval resampled "
                    "over trajectories rather than over pairs."
                ),
                run_ids=[run, context.run_id],
                git_sha=context.manifest.git.get("sha"),
                limitations=(
                    "A positive gap shows the seed still shapes the trajectory; it does not say "
                    "through what mechanism, nor that the information is recoverable. The probe "
                    "in Stage 2 answers that. At the pilot's replicate count the contrast "
                    "resolves a strong effect and not a marginal one, so a small gap should be "
                    "read as underpowered rather than absent."
                ),
            ),
        )
        context.finish(separation={k: float(v) for k, v in result.scalars.items()})
        console().print(f"run_id: [bold]{context.run_id}[/bold]")


@analyze_app.command("rates")
def analyze_rates(
    run: Annotated[str, typer.Option("--run", "-r", help="degeneracy or generation run_id")],
    group_by: Annotated[str, typer.Option(help="comma-separated grouping columns")] = "generator",
) -> None:
    """Fixed-point rate with a trajectory-level bootstrap CI.

    Reads ``at_fixed_point`` from a degeneracy run, or computes degeneracy from
    a generation run's chunks. The replicate unit is the trajectory.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    source = settings.paths.find_run(run)
    manifest = read_manifest(source.manifest)
    groups = [part.strip() for part in group_by.split(",") if part.strip()]

    from .analysis.rates import grouped_rates, parse_trajectory_id
    from .reporting.tables import save_table
    from .viz.export import FigureMeta, save_plotly_figure
    from .viz.figures import rate_bar_figure

    verdicts_path = source.data_dir / "degeneracy_verdicts.parquet"
    if verdicts_path.is_file():
        verdicts = pd.read_parquet(verdicts_path)
    elif source.chunks().is_file():
        verdicts, _ = _degeneracy_labels(pd.read_parquet(source.chunks()))
    else:
        raise typer.BadParameter(
            f"run {run} has neither degeneracy_verdicts.parquet nor chunks.parquet"
        )
    if "at_fixed_point" not in verdicts.columns:
        raise typer.BadParameter("verdicts have no at_fixed_point column")
    parsed = pd.DataFrame(verdicts["trajectory_id"].map(parse_trajectory_id).tolist())
    frame = verdicts.merge(parsed, on="trajectory_id", how="left")
    for column in groups:
        if column not in frame.columns:
            raise typer.BadParameter(f"unknown group column {column!r}")

    config_resolved = {
        "analysis": "rates",
        "source_run_id": run,
        "group_by": groups,
    }
    with run_context(
        stage=str(manifest.get("stage", "s2")),
        slug="rates",
        config_resolved=config_resolved,
        config_sha256=sha256_obj(config_resolved),
        settings=settings,
    ) as context:
        rates = grouped_rates(frame, flag_column="at_fixed_point", group_columns=groups)
        rates.to_parquet(context.paths.data_dir / "fixed_point_rates.parquet", index=False)
        _print_frame(rates, "fixed-point rates")
        figure, tidy, meta = rate_bar_figure(
            rates,
            group_column=groups[0],
            run_ids=[run, context.run_id],
            caption=(
                "Fraction of trajectories at a textual fixed point, with a 95% bootstrap "
                "CI over trajectories. The dashed line is 0.5, the Stage 2 direction "
                "threshold (F2). A cell whose interval includes 0.5 does not decide a "
                "direction."
            ),
            limitations=(
                "The verdict is the calibrated late-phase shingle Jaccard, not a semantic "
                "state. Eight trajectories per generator make the interval wide on purpose. "
                "Incidence is not reproducible across seed derivations (S1.2); only the rate is."
            ),
        )
        meta.git_sha = context.manifest.git.get("sha")
        save_plotly_figure(figure, context.artifacts_dir / "rates", meta, data=tidy)
        save_table(
            rates,
            context.artifacts_dir / "rates",
            FigureMeta(
                name="fixed_point_rates",
                caption=meta.caption,
                run_ids=[run, context.run_id],
                git_sha=context.manifest.git.get("sha"),
                limitations=meta.limitations,
            ),
        )
        context.finish(n_groups=len(rates), n_trajectories=len(frame))
        console().print(f"run_id: [bold]{context.run_id}[/bold]")


@analyze_app.command("protocol")
def analyze_protocol(
    run: Annotated[str, typer.Option("--run", "-r", help="generation run_id")],
) -> None:
    """Block fill and stop rate by quarter of the run, per generator.

    Refuses a run-level mean. Stage 1 hid monotone drift behind one number;
    this pass exists so that cannot recur.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    source = settings.paths.find_run(run)
    manifest = read_manifest(source.manifest)
    events_path = source.events
    if not events_path.is_file():
        raise typer.BadParameter(f"run {run} has no events.jsonl")

    from .analysis.rates import quarter_diagnostics
    from .reporting.tables import save_table
    from .viz.export import FigureMeta, save_plotly_figure
    from .viz.figures import quarter_protocol_figure

    rows: list[dict[str, Any]] = []
    with events_path.open("rb") as handle:
        for raw in handle:
            if b"generation.step.completed" not in raw:
                continue
            payload = orjson.loads(raw)
            if payload.get("event") != "generation.step.completed":
                continue
            rows.append(
                {
                    "trajectory_id": payload["trajectory_id"],
                    "generated_tokens": payload["generated_tokens"],
                    "block_fill_ratio": payload["block_fill_ratio"],
                    "finish_reason": payload.get("finish_reason"),
                    "reasoning_tokens": payload.get("reasoning_tokens") or 0,
                    "tokenizer_roundtrip_ok": payload.get("tokenizer_roundtrip_ok"),
                    "served_provider": payload.get("served_provider"),
                }
            )
    if not rows:
        raise typer.BadParameter(f"run {run} has no completed generation steps")

    config_resolved = {"analysis": "protocol", "source_run_id": run}
    with run_context(
        stage=str(manifest.get("stage", "s2")),
        slug="protocol",
        config_resolved=config_resolved,
        config_sha256=sha256_obj(config_resolved),
        settings=settings,
    ) as context:
        per_traj = quarter_diagnostics(pd.DataFrame(rows))
        per_traj.to_parquet(
            context.paths.data_dir / "protocol_per_traj_quarter.parquet", index=False
        )
        figure, tidy, meta = quarter_protocol_figure(per_traj, run_ids=[run, context.run_id])
        tidy.to_parquet(context.paths.data_dir / "protocol_by_quarter.parquet", index=False)
        meta.git_sha = context.manifest.git.get("sha")
        save_plotly_figure(figure, context.artifacts_dir / "protocol", meta, data=tidy)
        save_table(
            tidy,
            context.artifacts_dir / "protocol",
            FigureMeta(
                name="protocol_by_quarter",
                caption=meta.caption,
                run_ids=[run, context.run_id],
                git_sha=context.manifest.git.get("sha"),
                limitations=meta.limitations,
            ),
        )
        _print_frame(tidy, "protocol by quarter")
        context.finish(n_trajectories=int(per_traj["trajectory_id"].nunique()))
        console().print(f"run_id: [bold]{context.run_id}[/bold]")


@analyze_app.command("dynamics")
def analyze_dynamics(
    run: Annotated[str, typer.Option("--run", "-r", help="run_id holding the embeddings")],
    embedding: Annotated[str, typer.Option("--embedding", "-e")] = "",
    config: Annotated[Path, typer.Option("--config")] = Path("configs/analysis/dynamics.yaml"),
    stage: Annotated[
        str,
        typer.Option(
            "--stage",
            "-s",
            help="stage directory for this analysis run (default: the source run's stage)",
        ),
    ] = "",
) -> None:
    """VAMP → k-means → non-reversible MSM → Leiden, restricted sample.

    k-means cells are microstates. Macrostates are interpreted only after
    implied timescales are flat and the Chapman–Kolmogorov test passes.
    Degeneracy labels are joined first: a looping trajectory's timescales
    measure the loop.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    source = settings.paths.find_run(run)
    manifest = read_manifest(source.manifest)

    candidates = sorted(source.data_dir.glob("embeddings_*.parquet"))
    if not candidates:
        raise typer.BadParameter(f"run {run} has no embeddings; this pass does not call an API")
    chosen = [source.embeddings(embedding)] if embedding else candidates
    missing = [path for path in chosen if not path.is_file()]
    if missing:
        raise typer.BadParameter(f"missing embedding files: {[p.name for p in missing]}")

    from .analysis.dynamics import (
        DynamicsParams,
        compute_dynamics,
        compute_k_stability,
        filter_eligible,
        series_from_frame,
    )
    from .errors import AnalysisError
    from .reporting.tables import save_table
    from .viz.export import FigureMeta, save_plotly_figure, write_index
    from .viz.figures import (
        agreement_figure,
        ck_error_figure,
        current_norm_figure,
        implied_timescales_figure,
        occupancy_vs_turnover_figure,
    )

    params = DynamicsParams.from_yaml(config)
    stage_name = stage or str(manifest.get("stage", "s3"))
    config_resolved = {
        "analysis": "dynamics",
        "source_run_id": run,
        "embedding": embedding or "all",
        "stage": stage_name,
        "params": params.model_dump(),
    }

    chunks_source = _source_chunks(source)
    degenerate: dict[str, bool] = {}
    if chunks_source is not None:
        verdicts, _per_chunk = _degeneracy_labels(chunks_source)
        degenerate = {
            str(row.trajectory_id): bool(row.degenerate) for row in verdicts.itertuples(index=False)
        }

    with run_context(
        stage=stage_name,
        slug="dynamics",
        config_resolved=config_resolved,
        config_sha256=sha256_obj(config_resolved),
        settings=settings,
    ) as context:
        results = []
        k_stability_frames: list[pd.DataFrame] = []
        skipped: list[str] = []
        for parquet in chosen:
            slug = parquet.stem.removeprefix("embeddings_")
            frame = pd.read_parquet(parquet)
            eligible = filter_eligible(frame, params)
            if eligible.empty:
                skipped.append(f"{slug}: no eligible trajectories")
                continue
            for generator, block in eligible.groupby("generator", sort=True):
                series = series_from_frame(
                    block, embedding=slug, params=params, degenerate=degenerate
                )
                group = f"{generator}/{slug}"
                if not series:
                    skipped.append(f"{group}: no post-horizon frames")
                    continue
                try:
                    result = compute_dynamics(series, params=params, group=group)
                except AnalysisError as exc:
                    skipped.append(f"{group}: {exc}")
                    continue
                results.append(result)
                try:
                    k_stability_frames.append(
                        compute_k_stability(series, params=params, group=group)
                    )
                except AnalysisError as exc:
                    skipped.append(f"{group} k-stability: {exc}")
                context.events.event(
                    "analysis.dynamics.group",
                    group=group,
                    scalars={k: float(v) for k, v in result.scalars.items()},
                    notes=result.notes,
                )
                for note in result.notes:
                    context.note(f"{group}: {note}")

        if not results:
            raise typer.BadParameter(
                "no eligible process produced an MSM. " + "; ".join(skipped[:8])
            )

        scalars = pd.DataFrame(
            [
                {
                    "group": item.group,
                    "generator": item.generator,
                    "embedding": item.embedding,
                    **item.scalars,
                }
                for item in results
            ]
        )
        its = pd.concat([item.its for item in results], ignore_index=True)
        ck = pd.concat([item.ck for item in results], ignore_index=True)
        currents = (
            pd.concat([item.currents for item in results if len(item.currents)], ignore_index=True)
            if any(len(item.currents) for item in results)
            else pd.DataFrame()
        )
        occupancy = pd.concat([item.occupancy for item in results], ignore_index=True)
        agreement = pd.concat([item.agreement for item in results], ignore_index=True)
        vamp_scores = pd.concat([item.vamp_scores for item in results], ignore_index=True)
        k_stability = (
            pd.concat(k_stability_frames, ignore_index=True)
            if k_stability_frames
            else pd.DataFrame()
        )

        for name, table in (
            ("scalars", scalars),
            ("implied_timescales", its),
            ("chapman_kolmogorov", ck),
            ("currents", currents),
            ("occupancy", occupancy),
            ("agreement", agreement),
            ("vamp_scores", vamp_scores),
            ("k_stability", k_stability),
        ):
            if table.empty and not len(table.columns):
                continue
            table.to_parquet(context.paths.data_dir / f"dynamics_{name}.parquet", index=False)

        out_dir = context.artifacts_dir / "dynamics"
        git_sha = context.manifest.git.get("sha")
        run_ids = [run, context.run_id]

        def export(bundle: tuple[Any, Any, FigureMeta]) -> None:
            figure, data, meta = bundle
            meta.git_sha = git_sha
            meta.config_sha256 = context.manifest.config_sha256
            save_plotly_figure(figure, out_dir, meta, data=data)

        export(
            implied_timescales_figure(
                its,
                run_ids=run_ids,
                caption=(
                    "Implied timescales t_i = −τ / ln|λ_i| from the non-reversible MSM "
                    "transition matrix, not from VAMP singular values. A usable model "
                    "needs a region where the slowest real timescale is flat in τ. "
                    f"Source embeddings: {run}."
                ),
                limitations=(
                    "A singular value of the Koopman operator is not a relaxation "
                    "time. Reading a timescale off VAMP would be a category error. "
                    "A looping trajectory produces a long timescale that measures "
                    "the loop. Cells with n_macro=1 have no validated semantic state."
                ),
            )
        )
        export(
            ck_error_figure(
                ck,
                run_ids=run_ids,
                threshold=params.ck_max_error,
                caption=(
                    "Chapman–Kolmogorov max |T(kτ) − T(τ)^k| at the primary lag. "
                    "Each bar is labelled micro (k-means assignment, pre-registered "
                    f"F6 bar {params.ck_max_error}) or macro (spectral coarse-graining). "
                    "A micro-MSM above the dashed line fails F6. That is a sparse "
                    "count-matrix test, not a claim that the process is non-Markov."
                ),
                limitations=(
                    "F6 is scored on the K-state micro-MSM only. Unused microstates "
                    "get a self-loop; a single empty-versus-occupied discrepancy "
                    "drives the max toward 1. The 0.15 bar is pre-registered, not "
                    "calibrated to this K / n_frames regime, and is not scale-aware. "
                    "Methodology's VAMP-reduced CK was not run. Macro CK is reported "
                    "beside the micro bar and does not inherit the F6 interpretation."
                ),
            )
        )
        export(
            current_norm_figure(
                scalars,
                run_ids=run_ids,
                caption=(
                    "Frobenius norm of the K×K *microstate* current "
                    "J_ij = π_i T_ij − π_j T_ji, with a 95% trajectory-bootstrap "
                    "CI. This is not H4 (macrostate currents). An interval that "
                    "includes 0 is consistent with a near-zero microstate current "
                    "on that cell; it is not a claim that 'qwen is at equilibrium'."
                ),
                limitations=(
                    "‖J‖_F summarises a K×K micro-MSM. A sliding loop chopped into "
                    "k-means cells can carry a small directed current that is not "
                    "semantic circulation. The point estimate can sit above the "
                    "CI upper bound (frozen-label bootstrap pathology). Bootstrap "
                    "is over trajectories, not chunks."
                ),
            )
        )
        export(
            agreement_figure(
                agreement,
                run_ids=run_ids,
                caption=(
                    "Adjusted Rand index between Leiden communities (time-blind "
                    "mutual-kNN on PCA of raw embeddings) and MSM macrostate "
                    "assignments, with a 95% CI from resampling trajectories. "
                    "High agreement can mean both methods found the same states "
                    "or that both collapsed to one region — read next to n_macro."
                ),
                limitations=(
                    "The CI resamples trajectories on frozen labels; it is not a "
                    "refit CI. Leiden is not run in VAMP coordinates. UMAP is not "
                    "used for any number on this figure."
                ),
            )
        )
        save_table(
            scalars,
            out_dir,
            FigureMeta(
                name="dynamics_scalars",
                caption=(
                    "Per-process MSM summary. validated_macrostates=1 only when "
                    "implied timescales are flat, the *microstate* CK passes, "
                    "n_macro≥2, and not every trajectory is degenerate. "
                    "ck_max_error is the micro-MSM; ck_macro_max_error is the "
                    "spectral coarse-graining. n_macro=1 means H1 is unsupported "
                    "on that cell."
                ),
                run_ids=run_ids,
                git_sha=git_sha,
                limitations=(
                    "Instruct-under-P1 only this opening (ADR-0012). Glimmer is "
                    "underpowered by construction. K is capped at n_frames/3. "
                    "mean_dwell_chunks drops unvisited self-loop states. "
                    "VAMP-2 out-of-sample CV for n_pca / n_vamp / K was not run."
                ),
            ),
        )
        if not k_stability.empty:
            save_table(
                k_stability,
                out_dir,
                FigureMeta(
                    name="k_stability",
                    caption=(
                        "n_macro at every K allowed by the plan's n_frames/3 cap. "
                        "F7 is this table: instability across K or across spaces "
                        "is the result when no process keeps the same n_macro."
                    ),
                    run_ids=run_ids,
                    git_sha=git_sha,
                    limitations=(
                        "Each row is a full refit at that K, produced by "
                        "afterlife analyze dynamics, so reproduce regenerates it. "
                        "A changing n_macro under a failed micro-CK is not a "
                        "disagreement about semantic states — there are no "
                        "validated semantic states to disagree about."
                    ),
                ),
            )
        if not occupancy.empty:
            export(
                occupancy_vs_turnover_figure(
                    occupancy,
                    run_ids=run_ids,
                    caption=(
                        "Occupancy of the spectral coarse-graining versus window "
                        "turnover. Bins are floor(t/W). This is the occupancy "
                        "curve promised in the Stage 3 plan; it is not a "
                        "validated macrostate trajectory."
                    ),
                    limitations=(
                        "Assignments come from the same fit as n_macro. On a "
                        "looping series the coarse-graining is a partition of "
                        "the loop. Do not read a dwell or a basin from this "
                        "figure when validated_macrostates=0."
                    ),
                )
            )
        if skipped:
            context.note("skipped: " + "; ".join(skipped))
            console().print("[yellow]skipped groups:[/yellow] " + "; ".join(skipped))
        _print_frame(
            scalars,
            "dynamics scalars",
            columns=[
                "generator",
                "embedding",
                "n_trajectories",
                "n_frames",
                "K",
                "n_macro",
                "its_flat",
                "ck_pass",
                "validated_macrostates",
                "j_norm",
                "agreement_ari",
            ],
        )
        write_index(
            context.artifacts_dir,
            stage=stage_name,
            title=f"Stage {stage_name.lstrip('sS')} artifacts",
        )
        context.finish(n_groups=len(results), n_skipped=len(skipped))
        console().print(f"run_id: [bold]{context.run_id}[/bold]")


# ---------------------------------------------------------------------------
# report / verify / ledger / reproduce
# ---------------------------------------------------------------------------


@app.command()
def report(stage: Annotated[str, typer.Option("--stage", "-s")]) -> None:
    """Regenerate ``artifacts/stage-N/INDEX.md`` from the figure metadata on disk."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    from .viz.export import write_index

    out_dir = settings.paths.stage_artifacts(stage)
    if not out_dir.is_dir():
        raise typer.BadParameter(f"no artifacts directory for stage {stage} at {out_dir}")
    path = write_index(out_dir, stage=stage, title=f"Stage {stage} artifacts")
    console().print(f"wrote {path}")


snapshot_app = typer.Typer(
    help="Move runs/ and cache/ between machines, so a fresh clone is not a blank slate."
)
app.add_typer(snapshot_app, name="snapshot")


@snapshot_app.command("create")
def snapshot_create(
    out: Annotated[Path, typer.Option("--out", "-o", help="where to write the archives")] = Path(
        ".cache/snapshot"
    ),
    part: Annotated[
        str | None, typer.Option("--part", help="build only this part (runs, cache)")
    ] = None,
) -> None:
    """Archive runs/ and the response cache into verifiable tarballs.

    Archives are deterministic -- sorted entries, zeroed timestamps -- so an
    unchanged tree yields a byte-identical file. That is what makes the recorded
    sha256 a statement about contents rather than about when it was built.
    """
    from .snapshot import PARTS, create_snapshot

    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    root = settings.paths.root
    selected = {part: PARTS[part]} if part else None
    if part and part not in PARTS:
        raise typer.BadParameter(f"unknown part {part!r}; known: {', '.join(PARTS)}")

    console().print(f"archiving from [bold]{root}[/bold] -> {out}")
    manifest = create_snapshot(
        root,
        out,
        created_utc=datetime.now(UTC).isoformat(timespec="seconds"),
        git_sha=git_state(root).get("sha"),
        parts=selected,
    )

    table = Table(title="snapshot", title_justify="left", header_style="bold")
    for column in ("part", "files", "size", "sha256"):
        table.add_column(column)
    for info in manifest.parts:
        table.add_row(
            info.name,
            f"{info.n_files:,}",
            f"{info.size_bytes / 1e6:.1f} MB",
            info.sha256[:12] + "…",
        )
    console().print(table)
    console().print(f"total [bold]{manifest.total_bytes / 1e6:.1f} MB[/bold] in {out}")


@snapshot_app.command("restore")
def snapshot_restore(
    source: Annotated[
        Path, typer.Option("--from", "-f", help="directory holding the archives + manifest")
    ] = Path(".cache/snapshot"),
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="replace files that already exist locally")
    ] = False,
    part: Annotated[str | None, typer.Option("--part", help="restore only this part")] = None,
    root: Annotated[
        Path | None,
        typer.Option("--root", help="tree to restore into; defaults to the detected repo root"),
    ] = None,
) -> None:
    """Verify and extract a snapshot into a working tree.

    Every archive is checked against its recorded digest before anything is
    written: restoring a truncated archive would put unattributable data under
    runs/, which is worse than having no data at all. Existing files are kept
    unless ``--overwrite``, so a restore cannot silently replace a local run
    with a stale copy.

    The target is stated rather than inferred whenever ``--root`` is given.
    Detection walks up from the installed package, which resolves to the wrong
    tree when the command is invoked from another checkout's virtualenv — and
    writing hundreds of run directories into an unintended repository is not a
    mistake worth leaving implicit.
    """
    from .snapshot import restore_snapshot

    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    target = (root or settings.paths.root).resolve()
    console().print(f"restoring into [bold]{target}[/bold]")
    written = restore_snapshot(source, target, overwrite=overwrite, only=part)
    for name, count in written.items():
        console().print(f"{name}: [bold]{count:,}[/bold] files written")
    if not any(written.values()):
        console().print(
            "[yellow]nothing written — every file already existed. Pass --overwrite if the "
            "snapshot is meant to replace local state.[/yellow]"
        )


@app.command()
def supersede(
    run_id: Annotated[str, typer.Argument(help="run to retire")],
    reason: Annotated[str, typer.Option("--reason", "-m", help="why it is superseded")],
    by: Annotated[str, typer.Option("--by", help="run_id that replaces it")] = "",
) -> None:
    """Retire a run explicitly, without deleting it.

    Results get superseded — a bug is fixed, a threshold is calibrated, an
    estimator is corrected — and the record should say so. Deleting the old run
    destroys the evidence of what was tried; letting the review gate silently
    prefer the newest run hides the retirement. This writes a ``SUPERSEDED``
    marker and a manifest note, so the run stays on disk, stops counting towards
    the gate, and carries its own explanation.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    run = settings.paths.find_run(run_id)
    manifest = read_manifest(run.manifest)
    if not reason.strip():
        raise typer.BadParameter("a reason is required; an unexplained retirement is deletion")

    stamp = datetime.now(UTC).isoformat(timespec="seconds")
    marker = f"superseded_at: {stamp}\nreason: {reason}\n" + (
        f"superseded_by: {by}\n" if by else ""
    )
    (run.root / "SUPERSEDED").write_text(marker, encoding="utf-8")

    notes = list(manifest.get("notes") or [])
    notes.append(f"SUPERSEDED {stamp}: {reason}" + (f" (replaced by {by})" if by else ""))
    manifest["notes"] = notes
    manifest["superseded"] = {"at": stamp, "reason": reason, "by": by or None}
    run.manifest.write_bytes(
        orjson.dumps(manifest, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
    )

    console().print(
        Panel(
            f"{run_id}\nreason: {reason}" + (f"\nreplaced by: {by}" if by else ""),
            title="superseded",
            border_style="yellow",
        )
    )
    console().print(
        "[dim]The run stays on disk and keeps its manifest. It no longer counts towards the "
        "review gate, and the stage report should mention why it was retired.[/dim]"
    )


@app.command()
def review(
    stage: Annotated[str, typer.Option("--stage", "-s")],
    json_out: Annotated[
        Path | None, typer.Option("--json", help="write the report as JSON")
    ] = None,
) -> None:
    """Run the mechanical review gate for a stage.

    Everything this checks is objectively decidable: plan present with
    pre-registered predictions, runs complete, output hashes intact, artifact
    bundles self-contained, degeneracy labelled wherever confinement is claimed,
    budget reconciled, report scoring its own predictions, no unverified
    citations in the manuscript.

    An executing agent runs this and fixes what it reports. A reviewing agent's
    judgement is then spent only on what no tool can decide -- whether the
    conclusion follows from the evidence, whether a threshold is defensible,
    whether a claim overreaches. Exit code 1 means not ready for review.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    from .reporting.stage_review import review_stage

    report = review_stage(settings, stage)
    frame = report.to_frame()

    table = Table(title=f"stage {stage} review gate", title_justify="left", header_style="bold")
    table.add_column("check")
    table.add_column("verdict")
    table.add_column("detail", overflow="fold", max_width=80)
    styles = {"PASS": "green", "FAIL": "red", "WARN": "yellow", "SKIP": "dim"}
    for _, row in frame.iterrows():
        style = styles.get(row["verdict"], "")
        table.add_row(row["check"], f"[{style}]{row['verdict']}[/{style}]", row["detail"])
    console().print(table)

    for check in report.failed:
        console().print(
            Panel(
                f"{check.detail}\n\n[dim]Why this matters:[/dim] {check.why_it_matters}",
                title=f"[red]FAIL {check.name}[/red]",
                border_style="red",
            )
        )
    for check in report.warned:
        console().print(f"[yellow]WARN {check.name}:[/yellow] {check.detail}")

    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_bytes(orjson.dumps(report.as_dict(), option=orjson.OPT_INDENT_2))
        console().print(f"wrote {json_out}")

    if report.ready_for_review:
        console().print(
            "[green]gate passed — ready for scientific review.[/green] What remains is "
            "judgement a tool cannot supply: does the conclusion follow, is each threshold "
            "defensible, does any claim exceed its evidence."
        )
    else:
        console().print(
            f"[red]{len(report.failed)} blocking issue(s) — not ready for review.[/red]"
        )
        raise typer.Exit(code=1)


@app.command()
def verify(stage: Annotated[str, typer.Option("--stage", "-s")]) -> None:
    """Check every run in a stage: status, manifest completeness, output integrity."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    from .hashing import sha256_file

    stage_dir = settings.paths.runs / stage
    if not stage_dir.is_dir():
        raise typer.BadParameter(f"no runs for stage {stage} at {stage_dir}")

    rows: list[dict[str, Any]] = []
    for run_dir in sorted(p for p in stage_dir.iterdir() if p.is_dir()):
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.is_file():
            rows.append({"run_id": run_dir.name, "status": "NO MANIFEST", "integrity": "n/a"})
            continue
        manifest = read_manifest(manifest_path)
        integrity = manifest.get("integrity") or {}
        mismatched = [
            rel
            for rel, digest in integrity.items()
            if not (run_dir / rel).is_file() or sha256_file(run_dir / rel) != digest
        ]
        rows.append(
            {
                "run_id": run_dir.name,
                "status": manifest.get("status"),
                "git_dirty": (manifest.get("git") or {}).get("dirty"),
                "has_diff": bool((manifest.get("git") or {}).get("diff")),
                "n_files": len(integrity),
                "integrity": "ok" if not mismatched else f"{len(mismatched)} mismatched",
                "cost_usd": (manifest.get("totals") or {}).get("run_spend_usd"),
            }
        )
    frame = pd.DataFrame(rows)
    _print_frame(frame, f"stage {stage} runs")
    bad = frame[(frame["status"] != "COMPLETED") | (frame["integrity"] != "ok")]
    if not bad.empty:
        console().print(
            "[yellow]runs above that are not COMPLETED with intact integrity must be either "
            "re-run or declared as missing data in the stage report[/yellow]"
        )


@app.command()
def ledger(stage: str = typer.Option("", "--stage", "-s", help="filter by stage prefix")) -> None:
    """Spend, by kind and by model."""
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    from .ledger import read_ledger

    entries = read_ledger(settings.paths.ledger)
    if not entries:
        console().print("[yellow]no spend recorded yet[/yellow]")
        return
    frame = pd.DataFrame(entries)
    if stage:
        frame = frame[frame["run_id"].astype(str).str.startswith(stage)]
    grouped = (
        frame.groupby(["kind"], dropna=False)
        .agg(
            charges=("cost_usd", "size"),
            prompt_tokens=("prompt_tokens", "sum"),
            completion_tokens=("completion_tokens", "sum"),
            cost_usd=("cost_usd", "sum"),
        )
        .reset_index()
    )
    _print_frame(grouped, "spend by kind")
    total = float(frame["cost_usd"].sum())
    console().print(
        f"total [bold]${total:.4f}[/bold] of ${settings.afterlife_budget_usd_total:.2f} "
        f"({total / max(settings.afterlife_budget_usd_total, 1e-9):.1%})"
    )


@app.command()
def compare(
    run_a: Annotated[str, typer.Argument(help="baseline run_id")],
    run_b: Annotated[str, typer.Argument(help="run_id to compare against it")],
) -> None:
    """Compare two runs on their scientific content.

    Deliberately not a file-by-file hash comparison. A replayed run legitimately
    differs in per-call telemetry -- cost is zero, latency is zero, ``from_cache``
    is true -- so comparing every file would report a failure for a run that
    reproduced perfectly. What must match is the generated text, the chunking,
    and the embeddings; that is what any published number rests on.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    a = settings.paths.find_run(run_a)
    b = settings.paths.find_run(run_b)
    ma, mb = read_manifest(a.manifest), read_manifest(b.manifest)

    console().print(
        Panel(
            f"A  {run_a}\n   mode={ma.get('execution_mode')} status={ma.get('status')} "
            f"config={str(ma.get('config_sha256'))[:12]} git={str((ma.get('git') or {}).get('sha'))[:12]}\n"
            f"B  {run_b}\n   mode={mb.get('execution_mode')} status={mb.get('status')} "
            f"config={str(mb.get('config_sha256'))[:12]} git={str((mb.get('git') or {}).get('sha'))[:12]}",
            title="runs",
            border_style="blue",
        )
    )
    if ma.get("config_sha256") != mb.get("config_sha256"):
        console().print(
            "[yellow]configs differ, so any difference below may simply be the config "
            "change rather than a reproducibility failure[/yellow]"
        )

    from .hashing import sha256_file

    rows: list[dict[str, Any]] = []

    def add(kind: str, name: str, verdict: str, detail: str = "") -> None:
        rows.append({"kind": kind, "name": name, "match": verdict, "detail": detail})

    texts_a = {p.name: p for p in sorted((a.data_dir / "trajectories").glob("*.text"))}
    texts_b = {p.name: p for p in sorted((b.data_dir / "trajectories").glob("*.text"))}
    for name in sorted(set(texts_a) | set(texts_b)):
        if name not in texts_a or name not in texts_b:
            add("trajectory text", name, "MISSING", "present in only one run")
        else:
            identical = sha256_file(texts_a[name]) == sha256_file(texts_b[name])
            add(
                "trajectory text",
                name,
                "exact" if identical else "DIFFERS",
                f"{texts_a[name].stat().st_size} vs {texts_b[name].stat().st_size} bytes",
            )

    for label, path_a, path_b in (
        ("chunks", a.chunks(), b.chunks()),
        *(
            (f"embeddings:{p.stem.removeprefix('embeddings_')}", p, b.data_dir / p.name)
            for p in sorted(a.data_dir.glob("embeddings_*.parquet"))
        ),
    ):
        if not path_a.is_file() or not path_b.is_file():
            add(label, path_a.name, "MISSING", "not present in both runs")
            continue
        fa, fb = pd.read_parquet(path_a), pd.read_parquet(path_b)
        if fa.shape != fb.shape:
            add(label, path_a.name, "DIFFERS", f"shape {fa.shape} vs {fb.shape}")
            continue
        common = [c for c in fa.columns if c in fb.columns]
        mismatched = [c for c in common if not fa[c].equals(fb[c])]
        add(
            label,
            path_a.name,
            "exact" if not mismatched else "DIFFERS",
            f"rows={len(fa)}" if not mismatched else f"columns differ: {mismatched[:6]}",
        )

    frame = pd.DataFrame(rows)
    _print_frame(frame, "scientific content comparison")
    failures = frame[frame["match"] != "exact"] if not frame.empty else frame
    if frame.empty:
        console().print("[yellow]nothing comparable found in these runs[/yellow]")
    elif failures.empty:
        console().print(f"[green]L3: all {len(frame)} scientific outputs are bit-identical[/green]")
    else:
        console().print(f"[red]{len(failures)} of {len(frame)} outputs differ[/red]")
        raise typer.Exit(code=1)


@app.command()
def reproduce(
    run_id: Annotated[str, typer.Argument(help="run to re-derive")],
    level: Annotated[
        str, typer.Option("--level", "-l", help="replay | analysis | fresh")
    ] = "replay",
) -> None:
    """Re-derive a run and diff it against the original.

    ``replay`` serves every response from the cache and must be bit-exact.
    ``analysis`` re-runs the analysis on stored trajectories. ``fresh`` costs
    money and only reproduces the *conclusion*, within CI.
    """
    settings = get_settings()
    configure_logging(settings.afterlife_log_level)
    source = settings.paths.find_run(run_id)
    manifest = read_manifest(source.manifest)

    console().print(
        Panel(
            f"run_id      {run_id}\n"
            f"stage       {manifest.get('stage')}\n"
            f"status      {manifest.get('status')}\n"
            f"git         {(manifest.get('git') or {}).get('sha')}"
            f"{' (dirty)' if (manifest.get('git') or {}).get('dirty') else ''}\n"
            f"config sha  {manifest.get('config_sha256')}\n"
            f"command     {manifest.get('command')}",
            title="original run",
            border_style="blue",
        )
    )
    if level == "replay":
        console().print(
            "Re-run the original command with `AFTERLIFE_EXECUTION_MODE=replay` and compare:\n"
            f'    $env:AFTERLIFE_EXECUTION_MODE="replay"\n'
            f"    {manifest.get('command')}\n"
            "Then `afterlife verify --stage <stage>` and diff the manifests' integrity blocks.\n"
            "A cache miss in replay mode is an error by design: it means the config differs from "
            "the original run, or the cache is incomplete."
        )
    elif level == "analysis":
        console().print(
            "Re-run the analysis pass against the same source run and compare "
            "`data/geometry_*.parquet` column by column. Any deviation means analysis code "
            "changed; decide explicitly whether the original number is superseded."
        )
    elif level == "fresh":
        console().print(
            "[yellow]Fresh reproduction costs money.[/yellow] Run `afterlife estimate` on the "
            "config recorded in the manifest, get approval, then generate with a new stochastic "
            "seed set and compare distributions rather than exact outputs."
        )
    else:
        raise typer.BadParameter("level must be one of: replay, analysis, fresh")


@app.command()
def version() -> None:
    """Print the package version."""
    console().print(__version__)


def main() -> None:
    try:
        app()
    except AfterlifeError as exc:
        get_console().print(f"[red]{type(exc).__name__}[/red]: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
