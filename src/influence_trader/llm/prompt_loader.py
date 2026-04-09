from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from string import Template

from influence_trader.domain.models import RelevantTweetCandidate


@dataclass(frozen=True, slots=True)
class PromptBundle:
    version: str
    system_prompt: str
    user_template: Template


class MarketImpactPromptRenderer:
    def __init__(self, version: str = "v1") -> None:
        self._bundle = self._load_bundle(version)

    @property
    def version(self) -> str:
        return self._bundle.version

    @property
    def system_prompt(self) -> str:
        return self._bundle.system_prompt

    def render_user_prompt(self, candidate: RelevantTweetCandidate) -> str:
        tweet = candidate.tweet

        return self._bundle.user_template.substitute(
            author_handle=tweet.author.handle,
            author_display_name=tweet.author.display_name,
            posted_at=tweet.created_at.isoformat(),
            tweet_url=tweet.url,
            filter_reason=candidate.filter_reason,
            tweet_text=tweet.text,
        ).strip()

    @staticmethod
    def _load_bundle(version: str) -> PromptBundle:
        base_path = files("influence_trader.llm").joinpath("prompt_assets", "market_impact", version)
        system_prompt = base_path.joinpath("system.md").read_text(encoding="utf-8").strip()
        user_template = Template(base_path.joinpath("user.md").read_text(encoding="utf-8"))
        return PromptBundle(
            version=version,
            system_prompt=system_prompt,
            user_template=user_template,
        )

