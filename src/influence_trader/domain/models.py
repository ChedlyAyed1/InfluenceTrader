from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MarketDirection(StrEnum):
    """High-level directional bias expected for the market reaction.

    `bullish` means prices are more likely to rise, `bearish` means they are
    more likely to fall, `mixed` means effects may diverge across assets, and
    `uncertain` means the signal is too weak or ambiguous for a clear call.
    """

    bullish = "bullish"
    bearish = "bearish"
    mixed = "mixed"
    uncertain = "uncertain"


class TimeHorizon(StrEnum):
    """Expected time window over which the market impact may play out.

    `immediate` is the first reaction right after the news, `intraday` means
    within the same trading day, `short_term` spans the next several days, and
    `medium_term` covers a longer period such as weeks.
    """

    immediate = "immediate"
    intraday = "intraday"
    short_term = "short_term"
    medium_term = "medium_term"


class AssetClass(StrEnum):
    """Broad financial asset category used to group impacted instruments.

    These labels help classify whether the analysis is talking about stocks,
    crypto assets, commodities like oil or gold, currencies, interest-rate
    products, or market indices.
    """

    equities = "equities"
    crypto = "crypto"
    commodities = "commodities"
    fx = "fx"
    rates = "rates"
    indices = "indices"


class RelevanceLabel(StrEnum):
    """Binary decision for the semantic relevance filter.

    `market_relevant` means the tweet has a plausible path to move markets,
    while `not_relevant` means it is too vague, promotional, personal, or
    otherwise unlikely to matter for broader market analysis.
    """

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
    expected_effect: str = Field(description="Short explanation of the likely directional impact.")
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
