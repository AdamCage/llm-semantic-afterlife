"""Provider-client behaviours that Stage 0 measured the hard way.

Each test here corresponds to a real failure observed against RouterAI during
the S0 audits. They exist so that a refactor cannot quietly reintroduce a bug
that would only show up hours into a generation run.
"""

from __future__ import annotations

import pytest

from semantic_afterlife.providers.base import (
    ProviderError,
    RetryableProviderError,
    raise_for_embedded_error,
)
from semantic_afterlife.providers.routerai import _same_provider


class TestProviderIdentityMatching:
    @pytest.mark.parametrize(
        ("served", "pinned"),
        [
            ("Io Net", "io-net"),
            ("DeepInfra", "deepinfra"),
            ("Parasail", "parasail"),
            ("CoreWeave", "coreweave"),
            ("Mancer 2", "mancer"),
            ("Atlas Cloud", "atlas-cloud"),
        ],
    )
    def test_human_name_matches_its_slug(self, served: str, pinned: str) -> None:
        """The API reports a display name; we pin a slug. Measured in S0.2."""
        assert _same_provider(served, pinned)

    @pytest.mark.parametrize(
        ("served", "pinned"),
        [
            ("Alibaba", "deepinfra"),
            ("Fireworks", "together"),
            ("Baidu", "parasail"),
        ],
    )
    def test_genuinely_different_providers_do_not_match(self, served: str, pinned: str) -> None:
        assert not _same_provider(served, pinned)

    def test_unknown_served_provider_is_not_treated_as_a_violation(self) -> None:
        """Absent identity information is unknown, not a mismatch."""
        assert _same_provider("", "parasail")


class TestEmbeddedErrorDetection:
    """A router can wrap an upstream failure inside HTTP 200.

    Measured in S0.4: an upstream 429 arrived as 200 with an ``error`` field and
    no ``choices``, so the status-code checks passed and the retry loop never
    engaged. On a 256-step trajectory that turns a transient rate limit into a
    lost multi-hour run.
    """

    def _raise(self, body: object) -> None:
        raise_for_embedded_error("routerai", "/completions", body)

    def test_embedded_429_is_retryable(self) -> None:
        body = {
            "error": '{"error":{"message":"Provider returned error","code":429,'
            '"metadata":{"raw":"temporarily rate-limited upstream"}}}'
        }
        with pytest.raises(RetryableProviderError) as info:
            self._raise(body)
        assert info.value.status_code == 429

    def test_embedded_429_as_a_nested_object_is_retryable(self) -> None:
        with pytest.raises(RetryableProviderError):
            self._raise({"error": {"message": "rate limited", "code": 429}})

    def test_embedded_client_error_is_not_retried(self) -> None:
        """A 4xx that is not 429 cannot be fixed by waiting, and retrying costs money."""
        with pytest.raises(ProviderError) as info:
            self._raise({"error": {"message": "No allowed providers", "code": 404}})
        assert not isinstance(info.value, RetryableProviderError)

    def test_error_without_a_code_still_raises(self) -> None:
        with pytest.raises(ProviderError):
            self._raise({"error": "something opaque went wrong"})

    def test_a_normal_response_passes_through(self) -> None:
        self._raise({"choices": [{"text": "hello"}], "usage": {}})

    def test_an_error_alongside_choices_passes_through(self) -> None:
        """Some responses carry a warning-shaped `error` next to real content."""
        self._raise({"error": {"code": 429}, "choices": [{"text": "hi"}]})

    def test_embeddings_payload_passes_through(self) -> None:
        self._raise({"error": None, "data": [{"embedding": [0.1, 0.2]}]})

    def test_non_dict_body_is_ignored(self) -> None:
        self._raise([1, 2, 3])


class TestReasoningAccounting:
    """Reasoning tokens disqualify a step (ADR-0005), so they must be read reliably."""

    def _response(self, raw: dict[str, object]):  # type: ignore[no-untyped-def]
        from semantic_afterlife.ledger import Usage
        from semantic_afterlife.providers.base import CompletionResponse

        return CompletionResponse(
            text="x",
            finish_reason="length",
            usage=Usage(prompt_tokens=1, completion_tokens=1, cost_usd=0.0),
            served_provider=None,
            model_returned=None,
            latency_s=0.0,
            attempts=1,
            from_cache=False,
            raw=raw,
        )

    def test_reads_reasoning_tokens_from_usage(self) -> None:
        response = self._response(
            {"usage": {"completion_tokens_details": {"reasoning_tokens": 508}}}
        )
        assert response.reasoning_tokens == 508

    def test_absent_details_mean_zero(self) -> None:
        assert self._response({"usage": {}}).reasoning_tokens == 0
        assert self._response({}).reasoning_tokens == 0

    def test_malformed_value_does_not_raise(self) -> None:
        response = self._response(
            {"usage": {"completion_tokens_details": {"reasoning_tokens": "many"}}}
        )
        assert response.reasoning_tokens == 0

    def test_reasoning_text_is_found_in_either_shape(self) -> None:
        assert self._response({"choices": [{"reasoning": "trace"}]}).reasoning_text == "trace"
        assert (
            self._response({"choices": [{"message": {"reasoning": "trace"}}]}).reasoning_text
            == "trace"
        )
        assert self._response({"choices": [{}]}).reasoning_text is None
