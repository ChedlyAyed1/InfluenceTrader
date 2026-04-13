from __future__ import annotations

import re
from collections.abc import Sequence

from influence_trader.domain.models import ScrapedTweet


class TweetStructuralPreFilter:
    def __init__(
        self,
        min_length: int = 25,
        allowed_languages: Sequence[str] | None = None,
    ) -> None:
        self._min_length = min_length
        self._allowed_languages = {language.lower() for language in allowed_languages or ["en"]}

    def evaluate(
        self,
        tweet: ScrapedTweet,
        target_handles: Sequence[str] | None = None,
    ) -> tuple[bool, str]:
        text = self._normalize(tweet.text)
        normalized_target_handles = {handle.lower().lstrip("@") for handle in target_handles or []}

        if normalized_target_handles and tweet.author.handle.lower() not in normalized_target_handles:
            return False, "Tweet author is outside the requested account set."

        if tweet.is_reply:
            return False, "Replies are excluded from the market-impact pipeline."

        if tweet.is_repost:
            return False, "Reposts are excluded from the market-impact pipeline."

        if len(text) < self._min_length:
            return False, "Tweet too short to carry a stable standalone claim."

        if not self._is_allowed_language(tweet):
            return False, "Tweet language is outside the current supported set."

        if self._looks_like_sparse_statement(text):
            return False, "Tweet is too sparse or context-poor for semantic classification."

        return True, "Passed structural prefilter and requires semantic relevance classification."

    def _is_allowed_language(self, tweet: ScrapedTweet) -> bool:
        if tweet.language is None:
            return True
        return tweet.language.lower() in self._allowed_languages

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    @staticmethod
    def _looks_like_sparse_statement(text: str) -> bool:
        if text.count(" ") < 4:
            return True
        if len(re.sub(r"[\W_]+", "", text)) < 20:
            return True
        if re.fullmatch(r"[\W_]+", text):
            return True
        return False
