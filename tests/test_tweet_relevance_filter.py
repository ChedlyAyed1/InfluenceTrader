from datetime import UTC, datetime

from influence_trader.domain.models import ScrapedTweet, TweetAuthor
from influence_trader.scraper.filtering import TweetRelevanceFilter


def build_tweet(text: str) -> ScrapedTweet:
    return ScrapedTweet(
        tweet_id=1,
        url="https://x.com/example/status/1",
        author=TweetAuthor(handle="example", display_name="Example"),
        text=text,
        created_at=datetime(2026, 4, 9, 10, 0, tzinfo=UTC),
    )


def test_filter_accepts_macro_tweet() -> None:
    filter_service = TweetRelevanceFilter(["tariff", "sanction", "inflation"])

    is_relevant, reason = filter_service.evaluate(
        build_tweet("We will impose new tariffs next week to protect domestic manufacturing.")
    )

    assert is_relevant is True
    assert "tariff" in reason


def test_filter_rejects_promotional_noise() -> None:
    filter_service = TweetRelevanceFilter(["tariff", "sanction", "inflation"])

    is_relevant, reason = filter_service.evaluate(
        build_tweet("Thank you everyone, watch tonight and check out the new video.")
    )

    assert is_relevant is False
    assert "promotional" in reason.lower()
