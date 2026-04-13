from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import APIRouter, FastAPI, HTTPException, Request, status

from influence_trader.core.config import Settings
from influence_trader.domain.models import FetchTweetsRequest, PipelineRunRequest, PipelineRunResult
from influence_trader.llm.client import LLMRateLimitError
from influence_trader.pipeline.service import PipelineService
from influence_trader.scraper.service import TwscrapeInfluencerScraper

router = APIRouter()


@dataclass(slots=True)
class AppContainer:
    app: FastAPI
    scraper: TwscrapeInfluencerScraper
    pipeline: PipelineService
    settings: Settings


def get_container(request: Request) -> AppContainer:
    return cast(AppContainer, request.app.state.container)


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    container = get_container(request)
    return {
        "status": "ok",
        "app": container.settings.app_name,
        "groq_model": container.settings.groq_model,
        "groq_configured": bool(container.settings.groq_api_key),
        "default_handles": container.settings.x_default_handles,
    }


@router.post("/tweets/fetch")
async def fetch_tweets(request: Request, payload: FetchTweetsRequest) -> dict[str, object]:
    container = get_container(request)
    if not payload.relevant_only:
        tweets = await container.scraper.fetch_recent_tweets(
            handles=payload.handles,
            limit_per_handle=payload.limit_per_handle,
        )
        return {"count": len(tweets), "items": tweets}

    try:
        tweets, candidates = await container.pipeline.fetch_relevant_tweets(
            handles=payload.handles,
            limit_per_handle=payload.limit_per_handle,
        )
    except LLMRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    if payload.relevant_only:
        return {"count": len(candidates), "items": candidates}
    return {"count": len(tweets), "items": tweets}


@router.post("/pipeline/run-once", response_model=PipelineRunResult)
async def run_pipeline(request: Request, payload: PipelineRunRequest) -> PipelineRunResult:
    container = get_container(request)

    try:
        return await container.pipeline.run_once(payload)
    except LLMRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
