"""``afterlife`` — the only supported entry point.

Every command that can spend money prints an estimate and the remaining budget
first, and refuses to cross a ceiling. Every command that produces a result
creates a run with a manifest.
"""

from __future__ import annotations

import asyncio
import platform
from pathlib import Path
from typing import Annotated, Any

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
from .provenance import read_manifest
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


def _print_frame(frame: pd.DataFrame, title: str, *, max_rows: int = 40) -> None:
    if frame.empty:
        console().print(f"[yellow]{title}: no rows[/yellow]")
        return
    table = Table(title=title, title_justify="left", header_style="bold")
    for column in frame.columns:
        table.add_column(str(column), overflow="fold", max_width=42)
    for _, row in frame.head(max_rows).iterrows():
        table.add_row(*[("" if pd.isna(v) else str(v)) for v in row.tolist()])
    console().print(table)
    if len(frame) > max_rows:
        console().print(f"[dim]… {len(frame) - max_rows} more rows[/dim]")


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


def _save_audit(context: Any, frame: pd.DataFrame, name: str, caption: str) -> None:
    from .reporting.tables import save_table
    from .viz.export import FigureMeta

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
            audit_providers(
                client,
                list(experiment.generators),
                usd_per_rub=settings.afterlife_usd_per_rub,
                events=context.events,
            )
        )
        _print_frame(frame, "provider endpoints")
        _save_audit(
            context,
            frame,
            "s0_provider_endpoints",
            "Measured per-endpoint capabilities and prices for every candidate generator, as "
            "reported by the router. Availability, quantization and supported APIs are facts "
            "that later stage designs depend on; nothing here is taken from documentation.",
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
        display = frame.drop(columns=["sample"], errors="ignore")
        _print_frame(display, "continuation mechanisms")
        _save_audit(
            context,
            frame,
            "s0_continuation_mechanisms",
            "For each candidate generator, all three continuation mechanisms are attempted: raw "
            "text completion, assistant prefill, and instruction-framed chat. Records whether the "
            "model continues the text, its finish reason, the local-vs-API prompt token delta "
            "(which reveals a server-side chat template), and whether the output looks like "
            "meta-commentary rather than continuation.",
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
        _print_frame(frame, "determinism")
        _save_audit(
            context,
            frame,
            "s0_determinism",
            f"Exact-match and similarity rates over {repeats} identical seeded requests per model "
            f"at temperature {temperature}. This number, and not an assumption, determines the "
            "reproducibility level the paper may claim.",
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
        _print_frame(frame, "embedding models")
        _save_audit(
            context,
            frame,
            "s0_embeddings",
            "Measured dimension, whether the provider returns L2-normalised vectors, latency, "
            "cost, and the cosine similarity between three probe texts from unrelated domains. "
            "A space that cannot separate the probes cannot support anything downstream.",
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
        _print_frame(frame, "tokenizers")
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

    from .generation.trajectory import collect_chunks, plan_trajectories, run_trajectories
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

        summary = pd.DataFrame([r.as_dict() for r in results])
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
                    "chunk observations)."
                ),
                run_ids=[run, context.run_id],
                git_sha=git_sha,
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
