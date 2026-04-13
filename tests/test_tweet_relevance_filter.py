from datetime import UTC, datetime

from influence_trader.domain.models import ScrapedTweet, TweetAuthor
from influence_trader.scraper.filtering import TweetStructuralPreFilter


def build_tweet(
    text: str,
    *,
    handle: str = "elonmusk",
    is_reply: bool = False,
    is_repost: bool = False,
) -> ScrapedTweet:
    return ScrapedTweet(
        tweet_id=1,
        url="https://x.com/example/status/1",
        author=TweetAuthor(handle=handle, display_name="Example"),
        text=text,
        created_at=datetime(2026, 4, 9, 10, 0, tzinfo=UTC),
        is_reply=is_reply,
        is_repost=is_repost,
    )


def test_prefilter_accepts_long_original_tweet_from_target_author() -> None:
    filter_service = TweetStructuralPreFilter()

    is_relevant, reason = filter_service.evaluate(
        build_tweet(
            "We are meeting tomorrow to discuss a new federal framework for export controls and "
            "industrial permitting that could reshape domestic manufacturing."
        ),
        target_handles=["elonmusk"],
    )

    assert is_relevant is True
    assert "semantic relevance classification" in reason.lower()


def test_prefilter_allows_long_promotional_text_to_reach_semantic_classifier() -> None:
    filter_service = TweetStructuralPreFilter()

    is_relevant, reason = filter_service.evaluate(
        build_tweet("Thank you everyone, watch tonight and check out the new video."),
        target_handles=["elonmusk"],
    )

    assert is_relevant is True
    assert "semantic relevance classification" in reason.lower()


def test_prefilter_rejects_non_target_author() -> None:
    filter_service = TweetStructuralPreFilter()

    is_relevant, reason = filter_service.evaluate(
        build_tweet(
            "A detailed statement about national industrial policy and trade alignment.",
            handle="otheraccount",
        ),
        target_handles=["elonmusk"],
    )

    assert is_relevant is False
    assert "outside the requested account set" in reason.lower()
