from __future__ import annotations

import json
from typing import Any, cast

import httpx

from influence_trader.core.config import Settings
from influence_trader.domain.models import MarketImpactAnalysis, RelevantTweetCandidate
from influence_trader.llm.prompt_loader import MarketImpactPromptRenderer


class GroqMarketAnalysisClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            msg = "GROQ_API_KEY is required to use the LLM client."
            raise ValueError(msg)

        self._model = settings.groq_model
        self._prompt_renderer = MarketImpactPromptRenderer(version="v1")
        self._client = httpx.AsyncClient(
            base_url=settings.groq_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            timeout=settings.groq_timeout_seconds,
        )

    async def analyze_tweet(self, candidate: RelevantTweetCandidate) -> MarketImpactAnalysis:
        response = await self._client.post(
            "chat/completions",
            json=self._build_payload(candidate),
        )
        response.raise_for_status()

        payload = response.json()
        content = payload["choices"][0]["message"]["content"]

        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))

        return MarketImpactAnalysis.model_validate_json(content)

    async def close(self) -> None:
        await self._client.aclose()

    def _build_payload(self, candidate: RelevantTweetCandidate) -> dict[str, Any]:
        return {
            "model": self._model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": self._prompt_renderer.system_prompt},
                {
                    "role": "user",
                    "content": self._prompt_renderer.render_user_prompt(candidate),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "market_impact_analysis",
                    "strict": True,
                    "schema": self._json_schema(),
                },
            },
        }

    @staticmethod
    def _json_schema() -> dict[str, Any]:
        schema = MarketImpactAnalysis.model_json_schema()
        schema["additionalProperties"] = False
        return cast(dict[str, Any], json.loads(json.dumps(schema)))
