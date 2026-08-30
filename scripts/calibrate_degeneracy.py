"""Calibrate the degeneracy threshold against natural prose.

The n-gram repetition rate of a 1024-token chunk is not zero for healthy text:
ordinary English at that length repeats plenty of trigrams. So an absolute
threshold picked by intuition is worthless, and the first measurement on real
data showed why -- non-degenerate chunks scored ~0.46 against a threshold of
0.50.

This script establishes what the metric does on human-written prose, chunked by
the *same tokenizer* at the *same chunk size* as the experiment, and proposes a
threshold as a high quantile of that reference distribution. Two registers are
used, narrative and expository, because the metric is register-sensitive and a
single reference would bake one register's habits into the threshold.

No API, no cost. Reference texts are public-domain and cached locally.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from semantic_afterlife.analysis.degeneracy import (
    ngram_repetition_rate,
    tokenize_words,
    type_token_ratio,
    unigram_entropy,
)
from semantic_afterlife.config import get_settings
from semantic_afterlife.tokenization import load_tokenizer

#: Project Gutenberg wraps its texts in licence boilerplate that would otherwise
#: contribute highly repetitive chunks and bias the reference downwards.
_START = re.compile(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG[^\n]*\*\*\*", re.I)
_END = re.compile(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG[^\n]*\*\*\*", re.I)


def strip_boilerplate(text: str) -> str:
    if (match := _START.search(text)) is not None:
        text = text[match.end() :]
    if (match := _END.search(text)) is not None:
        text = text[: match.start()]
    return text.strip()


def chunk_by_tokenizer(text: str, tokenizer, chunk_size: int) -> list[str]:  # type: ignore[no-untyped-def]
    """Cut into exactly `chunk_size` generator tokens, as the experiment does."""
    ids = tokenizer.encode(text)
    return [
        tokenizer.decode(ids[start : start + chunk_size])
        for start in range(0, len(ids) - chunk_size + 1, chunk_size)
    ]


def profile(chunks: list[str], label: str, ngram: int) -> pd.DataFrame:
    rows = []
    for index, chunk in enumerate(chunks):
        words = tokenize_words(chunk)
        rows.append(
            {
                "source": label,
                "chunk": index,
                "n_words": len(words),
                "ngram_repetition": ngram_repetition_rate(words, ngram),
                "type_token_ratio": type_token_ratio(words),
                "unigram_entropy_bits": unigram_entropy(words),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, default=Path(".cache/reference-texts"))
    parser.add_argument("--chunk-size", type=int, default=1024)
    parser.add_argument("--ngram", type=int, default=3)
    parser.add_argument(
        "--tokenizer",
        default="NousResearch/Meta-Llama-3.1-8B",
        help="must match the generator whose chunks the threshold will be applied to",
    )
    parser.add_argument(
        "--compare-run",
        default=None,
        help="optional generation run_id, to overlay the model's own distribution",
    )
    parser.add_argument(
        "--compare-text",
        nargs="*",
        default=(),
        help="raw trajectory .text files to compare; usable while a run is still in "
        "flight, since chunks.parquet is only written when the whole batch finishes",
    )
    args = parser.parse_args()

    settings = get_settings()
    tokenizer = load_tokenizer(args.tokenizer, None, str(settings.paths.tokenizer_cache))

    files = sorted(args.reference_dir.glob("*.txt"))
    if not files:
        raise SystemExit(f"no reference texts in {args.reference_dir}")

    frames = []
    for path in files:
        text = strip_boilerplate(path.read_text(encoding="utf-8", errors="replace"))
        chunks = chunk_by_tokenizer(text, tokenizer, args.chunk_size)
        frames.append(profile(chunks, path.stem, args.ngram))
        print(f"{path.stem:24s} {len(chunks):4d} chunks of {args.chunk_size} tokens")

    reference = pd.concat(frames, ignore_index=True)

    pd.set_option("display.width", 170)
    print("\nreference distribution by source:")
    print(
        reference.groupby("source")
        .agg(
            chunks=("chunk", "size"),
            repetition_mean=("ngram_repetition", "mean"),
            repetition_p95=("ngram_repetition", lambda s: float(np.quantile(s, 0.95))),
            repetition_max=("ngram_repetition", "max"),
            type_token_mean=("type_token_ratio", "mean"),
            entropy_mean=("unigram_entropy_bits", "mean"),
        )
        .to_string()
    )

    values = reference["ngram_repetition"].to_numpy()
    print("\npooled reference quantiles for ngram_repetition:")
    for q in (0.5, 0.9, 0.95, 0.99, 0.999, 1.0):
        print(f"  p{q * 100:>5.1f}  {float(np.quantile(values, q)):.4f}")

    suggested = float(np.quantile(values, 0.99))
    print(
        f"\nsuggested loop_repetition_threshold = {suggested:.3f}"
        f"  (99th percentile of natural prose; 1% false-positive rate by construction)"
    )

    if args.compare_text:
        rows = []
        for pattern in args.compare_text:
            for path in sorted(Path().glob(pattern)) or [Path(pattern)]:
                if not path.is_file():
                    continue
                # Chunked with the reference tokenizer so the comparison is
                # like-for-like; the generators' own tokenizers differ in
                # vocabulary but not enough to move a word-level statistic.
                chunks = chunk_by_tokenizer(
                    path.read_text(encoding="utf-8", errors="replace"),
                    tokenizer,
                    args.chunk_size,
                )
                if chunks:
                    rows.append(profile(chunks, path.stem.split("__")[0], args.ngram))
        if rows:
            models = pd.concat(rows, ignore_index=True)
            summary = models.groupby("source").agg(
                chunks=("chunk", "size"),
                repetition=("ngram_repetition", "mean"),
                repetition_max=("ngram_repetition", "max"),
                type_token=("type_token_ratio", "mean"),
                entropy=("unigram_entropy_bits", "mean"),
            )
            summary["x_natural"] = summary["repetition"] / float(values.mean())
            summary["pct_above_p99"] = models.groupby("source")["ngram_repetition"].apply(
                lambda s: float((s >= suggested).mean())
            )
            print("\nmodel trajectories against the reference:")
            print(summary.to_string())

    if args.compare_run:
        run = settings.paths.find_run(args.compare_run)
        chunks = pd.read_parquet(run.chunks())
        model = profile(chunks["text"].tolist(), "model", args.ngram)
        model["turnover"] = chunks["turnover"].to_numpy()
        above = float((model["ngram_repetition"] >= suggested).mean())
        print(
            f"\nmodel run {args.compare_run}: {len(model)} chunks, "
            f"mean repetition {model['ngram_repetition'].mean():.4f}, "
            f"{above:.1%} above the suggested threshold"
        )
        print("  by turnover band:")
        model["band"] = (model["turnover"] // 4) * 4
        print(
            model.groupby("band")
            .agg(
                chunks=("chunk", "size"),
                repetition=("ngram_repetition", "mean"),
                above_threshold=("ngram_repetition", lambda s: float((s >= suggested).mean())),
            )
            .to_string()
        )


if __name__ == "__main__":
    main()
