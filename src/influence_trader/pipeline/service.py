from __future__ import annotations

from influence_trader.domain.models import (
    AnalyzedTweet,
    PipelineRunRequest,
    PipelineRunResult,
    RelevantTweetCandidate,
    ScrapedTweet,
)
from influence_trader.llm.client import GroqMarketAnalysisClient
from influence_trader.scraper.filtering import TweetRelevanceFilter
from influence_trader.scraper.service import TwscrapeInfluencerScraper


class PipelineService:
    def __init__(
        self,
        scraper: TwscrapeInfluencerScraper,
        relevance_filter: TweetRelevanceFilter,
        llm_client: GroqMarketAnalysisClient | None,
    ) -> None:
        self._scraper = scraper
        self._relevance_filter = relevance_filter
        self._llm_client = llm_client

    async def fetch_relevant_tweets(
        self,
        handles: list[str] | None,
        limit_per_handle: int,
    ) -> tuple[list[ScrapedTweet], list[RelevantTweetCandidate]]:
        tweets = await self._scraper.fetch_recent_tweets(
            handles=handles,
            limit_per_handle=limit_per_handle,
        )

        candidates: list[RelevantTweetCandidate] = []
        for tweet in tweets:
            is_relevant, reason = self._relevance_filter.evaluate(tweet)
            if is_relevant:
                candidates.append(
                    RelevantTweetCandidate(
                        tweet=tweet,
                        filter_reason=reason,
                    )
                )

        return tweets, candidates

    async def run_once(self, request: PipelineRunRequest) -> PipelineRunResult:
        tweets, candidates = await self.fetch_relevant_tweets(
            handles=request.handles,
            limit_per_handle=request.limit_per_handle,
        )

        if self._llm_client is None:
            msg = "GROQ_API_KEY is missing. Configure it before running the full pipeline."
            raise RuntimeError(msg)

        analyzed_items: list[AnalyzedTweet] = []
        for candidate in candidates[: request.max_analyses]:
            analysis = await self._llm_client.analyze_tweet(candidate)
            analyzed_items.append(AnalyzedTweet(candidate=candidate, analysis=analysis))

        return PipelineRunResult(
            fetched_count=len(tweets),
            candidate_count=len(candidates),
            analyzed_count=len(analyzed_items),
            analyzed_items=analyzed_items,
        )
