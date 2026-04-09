from __future__ import annotations

import re
from collections.abc import Sequence

from influence_trader.domain.models import ScrapedTweet


class TweetRelevanceFilter:
    def __init__(self, keywords: Sequence[str], min_length: int = 25) -> None:
        self._keywords = [keyword.lower() for keyword in keywords]
        self._min_length = min_length

    def evaluate(self, tweet: ScrapedTweet) -> tuple[bool, str]:
        text = self._normalize(tweet.text)

        if len(text) < self._min_length:
            return False, "Tweet too short to carry a stable macro signal."

        if self._looks_like_noise(text):
            return False, "Likely casual or promotional content."

        matched_keywords = [
            keyword
            for keyword in self._keywords
            if any(
                re.search(rf"\b{re.escape(variant)}\b", text)
                for variant in self._keyword_variants(keyword)
            )
        ]
        if matched_keywords:
            preview = ", ".join(matched_keywords[:4])
            return True, f"Matched high-impact keywords: {preview}."

        if self._looks_like_macro_signal(text):
            return True, "Detected broad macro or geopolitical signal pattern."

        return False, "No strong macro, policy or cross-asset trigger detected."

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", text.strip().lower())

    @staticmethod
    def _looks_like_noise(text: str) -> bool:
        noisy_patterns = [
            r"\bthank you\b",
            r"\bwatch tonight\b",
            r"\bjoin us\b",
            r"\bcongratulations\b",
            r"\bhappy birthday\b",
            r"\bi love\b",
            r"\bcheck out\b",
            r"\bnew video\b",
        ]
        return any(re.search(pattern, text) for pattern in noisy_patterns)

    @staticmethod
    def _looks_like_macro_signal(text: str) -> bool:
        signal_patterns = [
            r"\bwill impose\b",
            r"\bwe are announcing\b",
            r"\bnew policy\b",
            r"\binterest rates?\b",
            r"\btrade deal\b",
            r"\bsanctions?\b",
            r"\bceasefire\b",
            r"\btariffs?\b",
            r"\bexport controls?\b",
        ]
        return any(re.search(pattern, text) for pattern in signal_patterns)

    @classmethod
    def _keyword_variants(cls, keyword: str) -> set[str]:
        variants = {keyword}

        if " " in keyword:
            words = keyword.split()
            words[-1] = cls._pluralize(words[-1])
            variants.add(" ".join(words))
            return variants

        variants.add(cls._pluralize(keyword))
        return variants

    @staticmethod
    def _pluralize(word: str) -> str:
        if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            return f"{word[:-1]}ies"
        if word.endswith(("s", "x", "z", "ch", "sh")):
            return f"{word}es"
        return f"{word}s"
