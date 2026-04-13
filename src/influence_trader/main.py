from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from influence_trader.api.routes import AppContainer, router
from influence_trader.core.config import get_settings
from influence_trader.core.logging import configure_logging
from influence_trader.llm.client import GroqMarketAnalysisClient
from influence_trader.pipeline.service import PipelineService
from influence_trader.scraper.filtering import TweetStructuralPreFilter
from influence_trader.scraper.service import TwscrapeInfluencerScraper
from influence_trader.scraper.twscrape_compat import apply_twscrape_workarounds


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    apply_twscrape_workarounds(settings)

    scraper = TwscrapeInfluencerScraper(settings)
    relevance_filter = TweetStructuralPreFilter()
    llm_client = GroqMarketAnalysisClient(settings) if settings.groq_api_key else None
    pipeline = PipelineService(
        scraper=scraper,
        relevance_filter=relevance_filter,
        llm_client=llm_client,
    )

    app.state.container = AppContainer(
        app=app,
        scraper=scraper,
        pipeline=pipeline,
        settings=settings,
    )

    yield

    if llm_client is not None:
        await llm_client.close()


app = FastAPI(
    title="InfluenceTrader",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def root_health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router, prefix=get_settings().api_prefix)
