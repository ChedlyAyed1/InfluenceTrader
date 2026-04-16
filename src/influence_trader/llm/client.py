from __future__ import annotations

import json
from typing import Any, TypeVar, cast

import httpx

from influence_trader.core.config import Settings
from influence_trader.domain.models import (
    MarketImpactAnalysis,
    RelevantTweetCandidate,
    SemanticRelevanceAssessment,
)
from influence_trader.llm.prompt_loader import (
    MarketImpactPromptRenderer,
    SemanticRelevancePromptRenderer,
)


class LLMRateLimitError(RuntimeError):
    """Raised when Groq rejects a request because the caller hit a rate limit."""

    pass


StructuredOutputT = TypeVar(
    "StructuredOutputT",
    MarketImpactAnalysis,
    SemanticRelevanceAssessment,
)


class GroqMarketAnalysisClient:
    """Wrap Groq structured-output calls for relevance classification and analysis."""

    def __init__(
        self,
        settings: Settings,
        *,
        market_impact_prompt_version: str = "v1",
        semantic_relevance_prompt_version: str = "v1",
    ) -> None:
        if not settings.groq_api_key:
            msg = "GROQ_API_KEY is required to use the LLM client."
            raise ValueError(msg)

        self._model = settings.groq_model
        self._market_impact_prompt_renderer = MarketImpactPromptRenderer(
            version=market_impact_prompt_version
        )
        self._semantic_relevance_prompt_renderer = SemanticRelevancePromptRenderer(
            version=semantic_relevance_prompt_version
        )
        self._client = httpx.AsyncClient(
            base_url=settings.groq_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            timeout=settings.groq_timeout_seconds,
        )

    async def analyze_tweet(self, candidate: RelevantTweetCandidate) -> MarketImpactAnalysis:
        """Run the full market-impact prompt and validate the structured response."""

        return await self._request_structured_output(
            schema_model=MarketImpactAnalysis,
            messages=[
                {
                    "role": "system",
                    "content": self._market_impact_prompt_renderer.system_prompt,
                },
                {
                    "role": "user",
                    "content": self._market_impact_prompt_renderer.render_user_prompt(candidate),
                },
            ],
            schema_name="market_impact_analysis",
        )

    async def classify_relevance(
        self,
        candidate: RelevantTweetCandidate,
    ) -> SemanticRelevanceAssessment:
        """Run the lighter semantic relevance prompt before full analysis."""

        return await self._request_structured_output(
            schema_model=SemanticRelevanceAssessment,
            messages=[
                {
                    "role": "system",
                    "content": self._semantic_relevance_prompt_renderer.system_prompt,
                },
                {
                    "role": "user",
                    "content": self._semantic_relevance_prompt_renderer.render_user_prompt(
                        candidate
                    ),
                },
            ],
            schema_name="semantic_relevance_assessment",
        )

    async def close(self) -> None:
        """Close the reusable async HTTP client during app shutdown."""

        await self._client.aclose()

    def _build_payload(
        self,
        *,
        messages: list[dict[str, str]],
        schema_model: type[StructuredOutputT],
        schema_name: str,
    ) -> dict[str, Any]:
        """Build a Groq chat-completions payload with strict JSON schema output."""

        return {
            "model": self._model,
            "temperature": 0.1,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": self._json_schema(schema_model),
                },
            },
        }

    @staticmethod
    def _json_schema(
        schema_model: type[StructuredOutputT],
    ) -> dict[str, Any]:
        """Generate a plain JSON-serializable schema from a Pydantic model class."""

        schema = schema_model.model_json_schema()
        schema["additionalProperties"] = False
        return cast(dict[str, Any], json.loads(json.dumps(schema)))

    async def _request_structured_output(
        self,
        *,
        schema_model: type[StructuredOutputT],
        messages: list[dict[str, str]],
        schema_name: str,
    ) -> StructuredOutputT:
        """Send a structured-output request and validate the returned JSON payload."""

        response = await self._client.post(
            "chat/completions",
            json=self._build_payload(
                messages=messages,
                schema_model=schema_model,
                schema_name=schema_name,
            ),
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                msg = "Groq rate limit reached. Reduce request volume and retry in a moment."
                raise LLMRateLimitError(msg) from exc
            raise

        payload = response.json()
        content = payload["choices"][0]["message"]["content"]

        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))

        return schema_model.model_validate_json(content)
