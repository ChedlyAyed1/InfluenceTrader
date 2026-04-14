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
    pass


StructuredOutputT = TypeVar(
    "StructuredOutputT",
    MarketImpactAnalysis,
    SemanticRelevanceAssessment,
)


class GroqMarketAnalysisClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            msg = "GROQ_API_KEY is required to use the LLM client."
            raise ValueError(msg)

        self._model = settings.groq_model
        self._market_impact_prompt_renderer = MarketImpactPromptRenderer(version="v1")
        self._semantic_relevance_prompt_renderer = SemanticRelevancePromptRenderer(version="v1")
        self._client = httpx.AsyncClient(
            base_url=settings.groq_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            timeout=settings.groq_timeout_seconds,
        )

    async def analyze_tweet(self, candidate: RelevantTweetCandidate) -> MarketImpactAnalysis:
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
        await self._client.aclose()

    def _build_payload(
        self,
        *,
        messages: list[dict[str, str]],
        schema_model: type[StructuredOutputT],
        schema_name: str,
    ) -> dict[str, Any]:
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
