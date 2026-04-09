from datetime import UTC, datetime

from influence_trader.domain.models import RelevantTweetCandidate, ScrapedTweet, TweetAuthor
from influence_trader.llm.prompt_loader import MarketImpactPromptRenderer


def test_market_impact_prompt_renderer_loads_versioned_prompt_files() -> None:
    renderer = MarketImpactPromptRenderer(version="v1")

    assert renderer.version == "v1"
    assert "<role>" in renderer.system_prompt


def test_market_impact_prompt_renderer_injects_candidate_values() -> None:
    renderer = MarketImpactPromptRenderer(version="v1")
    candidate = RelevantTweetCandidate(
        tweet=ScrapedTweet(
            tweet_id=1,
            url="https://x.com/example/status/1",
            author=TweetAuthor(handle="elonmusk", display_name="Elon Musk"),
            text="We may impose tariffs on imports.",
            created_at=datetime(2026, 4, 9, 10, 0, tzinfo=UTC),
        ),
        filter_reason="Matched high-impact keywords: tariff.",
    )

    prompt = renderer.render_user_prompt(candidate)

    assert "@elonmusk" in prompt
    assert "Matched high-impact keywords: tariff." in prompt
    assert "We may impose tariffs on imports." in prompt
