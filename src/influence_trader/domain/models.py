from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MarketDirection(StrEnum):
    bullish = "bullish"
    bearish = "bearish"
    mixed = "mixed"
    uncertain = "uncertain"


class TimeHorizon(StrEnum):
    immediate = "immediate"
    intraday = "intraday"
    short_term = "short_term"
    medium_term = "medium_term"


class AssetClass(StrEnum):
    equities = "equities"
    crypto = "crypto"
    commodities = "commodities"
    fx = "fx"
    rates = "rates"
    indices = "indices"


class RelevanceLabel(StrEnum):
    market_relevant = "market_relevant"
    not_relevant = "not_relevant"


class TweetAuthor(StrictModel):
    handle: str
    display_name: str
    user_id: int | None = None


class ScrapedTweet(StrictModel):
    tweet_id: int
    url: str
    author: TweetAuthor
    text: str
    language: str | None = None
    created_at: datetime
    like_count: int = 0
    reply_count: int = 0
    repost_count: int = 0
    quote_count: int = 0
    is_reply: bool = False
    is_repost: bool = False
    is_quote: bool = False


class RelevantTweetCandidate(StrictModel):
    tweet: ScrapedTweet
    filter_reason: str


class SemanticRelevanceAssessment(StrictModel):
    label: RelevanceLabel
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class ImpactedAsset(StrictModel):
    asset_name: str = Field(
        description="Specific asset, ticker, index, currency or commodity name."
    )
    asset_class: AssetClass
    sector_or_theme: str
    expected_effect: str = Field(
        description="Short explanation of the likely directional impact."
    )
    confidence: float = Field(ge=0.0, le=1.0)


class MarketImpactAnalysis(StrictModel):
    executive_summary: str
    market_direction: MarketDirection
    time_horizon: TimeHorizon
    confidence: float = Field(ge=0.0, le=1.0)
    geopolitical_context: str
    economic_context: str
    rationale: str
    impacted_assets: list[ImpactedAsset]
    disclaimer: str


class AnalyzedTweet(StrictModel):
    candidate: RelevantTweetCandidate
    analysis: MarketImpactAnalysis


class FetchTweetsRequest(StrictModel):
    handles: list[str] | None = None
    limit_per_handle: int = Field(default=5, ge=1, le=50)
    relevant_only: bool = True


class PipelineRunRequest(StrictModel):
    handles: list[str] | None = None
    limit_per_handle: int = Field(default=5, ge=1, le=50)
    max_analyses: int = Field(default=5, ge=1, le=20)


class PipelineRunResult(StrictModel):
    fetched_count: int
    candidate_count: int
    analyzed_count: int
    analyzed_items: list[AnalyzedTweet]
