from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from string import Template

from influence_trader.domain.models import RelevantTweetCandidate


@dataclass(frozen=True, slots=True)
class PromptBundle:
    """Small immutable container for one versioned prompt family."""

    version: str
    system_prompt: str
    user_template: Template


class BasePromptRenderer:
    """Load versioned prompt assets and expose shared bundle accessors."""

    prompt_family: str

    def __init__(self, version: str = "v1") -> None:
        self._bundle = self._load_bundle(self.prompt_family, version)

    @property
    def version(self) -> str:
        return self._bundle.version

    @property
    def system_prompt(self) -> str:
        return self._bundle.system_prompt

    @staticmethod
    def _load_bundle(prompt_family: str, version: str) -> PromptBundle:
        """Read the Markdown prompt assets for one prompt family and version."""

        base_path = files("influence_trader.llm").joinpath(
            "prompt_assets",
            prompt_family,
            version,
        )
        system_prompt = base_path.joinpath("system.md").read_text(encoding="utf-8").strip()
        user_template = Template(base_path.joinpath("user.md").read_text(encoding="utf-8"))
        return PromptBundle(
            version=version,
            system_prompt=system_prompt,
            user_template=user_template,
        )


class MarketImpactPromptRenderer(BasePromptRenderer):
    """Render the final analysis prompt from a retained tweet candidate."""

    prompt_family = "market_impact"

    def render_user_prompt(self, candidate: RelevantTweetCandidate) -> str:
        """Inject candidate fields into the market-impact user prompt template."""

        tweet = candidate.tweet

        return self._bundle.user_template.substitute(
            author_handle=tweet.author.handle,
            author_display_name=tweet.author.display_name,
            posted_at=tweet.created_at.isoformat(),
            tweet_url=tweet.url,
            filter_reason=candidate.filter_reason,
            tweet_text=tweet.text,
        ).strip()


class SemanticRelevancePromptRenderer(BasePromptRenderer):
    """Render the lighter prompt used for semantic relevance classification."""

    prompt_family = "semantic_relevance"

    def render_user_prompt(self, candidate: RelevantTweetCandidate) -> str:
        """Inject candidate fields into the semantic relevance user template."""

        tweet = candidate.tweet

        return self._bundle.user_template.substitute(
            author_handle=tweet.author.handle,
            author_display_name=tweet.author.display_name,
            posted_at=tweet.created_at.isoformat(),
            tweet_url=tweet.url,
            prefilter_reason=candidate.filter_reason,
            tweet_text=tweet.text,
        ).strip()
