"""Generator tokenizers and exact ``Tail_W`` arithmetic.

The sliding window is defined in **generator** tokens (methodology.md §1.5), so
each generator's own tokenizer must be available locally. We download only
``tokenizer.json`` — no weights, no GPU — and fingerprint the file so that a
manifest records exactly which tokenization defined the window.

Special tokens are never added when encoding. A stray BOS would shift every
window boundary by one token and silently invalidate the ``W`` semantics.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .errors import TokenizerError
from .hashing import sha256_file, sha256_text
from .logging_utils import get_logger

logger = get_logger("tokenization")


class Tokenizer(abc.ABC):
    """Minimal tokenizer surface. Everything else in the package uses only this."""

    slug: str
    fingerprint: str

    @abc.abstractmethod
    def encode(self, text: str) -> list[int]: ...

    @abc.abstractmethod
    def decode(self, ids: list[int]) -> str: ...

    @property
    @abc.abstractmethod
    def vocab_size(self) -> int: ...

    def count(self, text: str) -> int:
        return len(self.encode(text))

    def roundtrip_ok(self, text: str) -> bool:
        """``decode(encode(x)) == x``.

        Holds for byte-level BPE. A failure means a window boundary is not where
        the manifest claims it is, which is why it is checked every step rather
        than once.
        """
        return self.decode(self.encode(text)) == text

    def tail(self, text: str, n_tokens: int) -> tuple[str, int]:
        """Last ``n_tokens`` tokens of ``text``, as text, plus the token count.

        The returned text *is* the prompt that will be sent, so the window is
        exactly what the manifest says it is.
        """
        ids = self.encode(text)
        if len(ids) <= n_tokens:
            return text, len(ids)
        return self.decode(ids[-n_tokens:]), n_tokens


class HFTokenizer(Tokenizer):
    """Hugging Face ``tokenizer.json``, loaded from a local cache."""

    def __init__(self, slug: str, path: Path, repo: str, revision: str | None) -> None:
        try:
            from tokenizers import Tokenizer as HFTok
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise TokenizerError("the `tokenizers` package is required") from exc
        self.slug = slug
        self.repo = repo
        self.revision = revision
        self.path = path
        self.fingerprint = f"sha256:{sha256_file(path)}"
        self._tok = HFTok.from_file(str(path))

    def encode(self, text: str) -> list[int]:
        return list(self._tok.encode(text, add_special_tokens=False).ids)

    def decode(self, ids: list[int]) -> str:
        return str(self._tok.decode(ids, skip_special_tokens=False))

    @property
    def vocab_size(self) -> int:
        return int(self._tok.get_vocab_size(with_added_tokens=True))


class WhitespaceTokenizer(Tokenizer):
    """Whitespace tokenizer for mock/offline runs.

    Not a serious tokenizer, and deliberately so: it exists to let the whole
    pipeline run in CI without network access. Real experiments must use the
    generator's own tokenizer, which the config validator enforces by requiring
    an explicit ``mock`` repo name here.
    """

    slug = "whitespace"

    def __init__(self) -> None:
        self.fingerprint = f"sha256:{sha256_text('whitespace-v1')}"
        self._vocab: dict[str, int] = {}
        self._inverse: dict[int, str] = {}

    def _id(self, token: str) -> int:
        if token not in self._vocab:
            index = len(self._vocab)
            self._vocab[token] = index
            self._inverse[index] = token
        return self._vocab[token]

    def encode(self, text: str) -> list[int]:
        # Whitespace is attached to the following token so that decode is exact.
        tokens: list[str] = []
        buffer = ""
        for char in text:
            if char.isspace():
                if buffer:
                    tokens.append(buffer)
                    buffer = ""
                tokens.append(char)
            else:
                buffer += char
        if buffer:
            tokens.append(buffer)
        return [self._id(token) for token in tokens]

    def decode(self, ids: list[int]) -> str:
        return "".join(self._inverse.get(i, "") for i in ids)

    @property
    def vocab_size(self) -> int:
        return len(self._vocab)


@dataclass(frozen=True, slots=True)
class TokenizerSpec:
    repo: str
    revision: str | None = None
    slug: str | None = None


def _download_tokenizer_json(repo: str, revision: str | None, cache_dir: Path) -> Path:
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import EntryNotFoundError

    try:
        path = hf_hub_download(
            repo_id=repo,
            filename="tokenizer.json",
            revision=revision,
            cache_dir=str(cache_dir),
        )
    except EntryNotFoundError as exc:
        raise TokenizerError(
            f"{repo} has no tokenizer.json. Slow (sentencepiece-only) tokenizers are not "
            "supported; use a repo that ships the fast tokenizer, and record the substitution "
            "in the run manifest."
        ) from exc
    except Exception as exc:
        raise TokenizerError(
            f"could not download tokenizer.json from {repo!r} "
            f"(revision={revision!r}): {exc}. Gated repos need HF_TOKEN in .env."
        ) from exc
    return Path(path)


@lru_cache(maxsize=32)
def load_tokenizer(repo: str, revision: str | None, cache_dir: str) -> Tokenizer:
    """Load and cache a generator tokenizer.

    ``repo == "mock"`` yields the whitespace tokenizer used by offline runs.
    """
    if repo == "mock":
        return WhitespaceTokenizer()
    path = _download_tokenizer_json(repo, revision, Path(cache_dir))
    tokenizer = HFTokenizer(slug=repo.replace("/", "__"), path=path, repo=repo, revision=revision)
    logger.debug("loaded tokenizer %s (vocab=%d)", repo, tokenizer.vocab_size)
    return tokenizer


def describe(tokenizer: Tokenizer) -> dict[str, object]:
    """Provenance record for a manifest."""
    record: dict[str, object] = {
        "slug": tokenizer.slug,
        "fingerprint": tokenizer.fingerprint,
        "vocab_size": tokenizer.vocab_size,
        "type": type(tokenizer).__name__,
    }
    if isinstance(tokenizer, HFTokenizer):
        record["repo"] = tokenizer.repo
        record["revision"] = tokenizer.revision
    return record
