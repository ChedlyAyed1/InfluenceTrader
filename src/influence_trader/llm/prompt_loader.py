from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from importlib.resources.abc import Traversable
from string import Template
from typing import Final

from influence_trader.domain.models import RelevantTweetCandidate


@dataclass(frozen=True, slots=True)
class PromptMetadata:
    """Document the contract for one prompt family/version pair."""

    prompt_family: str
    version: str
    purpose: str
    user_template_variables: tuple[str, ...]
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class PromptBundle:
    """Small immutable container for one versioned prompt family."""

    version: str
    system_prompt: str
    user_template: Template
    metadata: PromptMetadata


class BasePromptRenderer:
    """Load versioned prompt assets and expose shared bundle accessors."""

    prompt_family: str
    _SYSTEM_FILENAME: Final[str] = "system.md"
    _USER_FILENAME: Final[str] = "user.md"
    _METADATA_FILENAME: Final[str] = "metadata.json"

    def __init__(self, version: str = "v1") -> None:
        self._bundle = self._load_bundle(self.prompt_family, version)

    @property
    def version(self) -> str:
        return self._bundle.version

    @property
    def system_prompt(self) -> str:
        return self._bundle.system_prompt

    @property
    def metadata(self) -> PromptMetadata:
        return self._bundle.metadata

    @staticmethod
    def _load_bundle(prompt_family: str, version: str) -> PromptBundle:
        """Read the Markdown prompt assets for one prompt family and version."""

        base_path = files("influence_trader.llm").joinpath(
            "prompt_assets",
            prompt_family,
            version,
        )
        metadata = BasePromptRenderer._load_metadata(
            base_path.joinpath(BasePromptRenderer._METADATA_FILENAME)
        )
        BasePromptRenderer._validate_metadata_identity(
            metadata=metadata,
            prompt_family=prompt_family,
            version=version,
        )
        system_prompt = (
            base_path.joinpath(BasePromptRenderer._SYSTEM_FILENAME)
            .read_text(encoding="utf-8")
            .strip()
        )
        user_template_text = base_path.joinpath(BasePromptRenderer._USER_FILENAME).read_text(
            encoding="utf-8"
        )
        BasePromptRenderer._validate_template_variables(
            template_text=user_template_text,
            expected_variables=metadata.user_template_variables,
            prompt_family=prompt_family,
            version=version,
        )
        user_template = Template(user_template_text)
        return PromptBundle(
            version=version,
            system_prompt=system_prompt,
            user_template=user_template,
            metadata=metadata,
        )

    @staticmethod
    def _load_metadata(metadata_path: Traversable) -> PromptMetadata:
        """Load one prompt metadata file from JSON."""

        raw_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return PromptMetadata(
            prompt_family=raw_metadata["prompt_family"],
            version=raw_metadata["version"],
            purpose=raw_metadata["purpose"],
            user_template_variables=tuple(raw_metadata["user_template_variables"]),
            notes=raw_metadata.get("notes"),
        )

    @staticmethod
    def _validate_metadata_identity(
        *,
        metadata: PromptMetadata,
        prompt_family: str,
        version: str,
    ) -> None:
        """Ensure metadata matches the prompt bundle requested by the caller."""

        if metadata.prompt_family != prompt_family:
            msg = (
                "Prompt metadata family mismatch for "
                f"{prompt_family}/{version}: found {metadata.prompt_family}."
            )
            raise ValueError(msg)

        if metadata.version != version:
            msg = (
                "Prompt metadata version mismatch for "
                f"{prompt_family}/{version}: found {metadata.version}."
            )
            raise ValueError(msg)

    @staticmethod
    def _validate_template_variables(
        *,
        template_text: str,
        expected_variables: tuple[str, ...],
        prompt_family: str,
        version: str,
    ) -> None:
        """Keep prompt metadata and template placeholders in sync."""

        discovered_variables = BasePromptRenderer._extract_template_variables(template_text)
        expected_set = set(expected_variables)

        if discovered_variables != expected_set:
            missing = sorted(expected_set - discovered_variables)
            extra = sorted(discovered_variables - expected_set)
            details: list[str] = []
            if missing:
                details.append(f"missing={missing}")
            if extra:
                details.append(f"extra={extra}")
            msg = f"Template variables mismatch for {prompt_family}/{version}: " + ", ".join(
                details
            )
            raise ValueError(msg)

    @staticmethod
    def _extract_template_variables(template_text: str) -> set[str]:
        """Return the set of ``string.Template`` placeholders used by a template."""

        placeholders: set[str] = set()
        for match in Template.pattern.finditer(template_text):
            if match.group("invalid") is not None:
                msg = "Prompt template contains an invalid placeholder."
                raise ValueError(msg)

            named_placeholder = match.group("named")
            braced_placeholder = match.group("braced")
            placeholder = named_placeholder or braced_placeholder
            if placeholder is not None:
                placeholders.add(placeholder)

        return placeholders


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
