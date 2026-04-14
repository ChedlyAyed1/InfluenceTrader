from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from twscrape import API

from influence_trader.core.config import Settings
from influence_trader.domain.models import ScrapedTweet, TweetAuthor

logger = logging.getLogger(__name__)


class TwscrapeInfluencerScraper:
    """Fetch and normalize tweets from configured X accounts via twscrape."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._api = API(str(settings.x_accounts_db_path))
        self._account_seed_attempted = False

    async def fetch_recent_tweets(
        self,
        handles: Sequence[str] | None = None,
        limit_per_handle: int | None = None,
    ) -> list[ScrapedTweet]:
        """Collect the newest accepted tweets for each requested handle."""

        await self._seed_account_if_needed()

        resolved_handles = list(handles or self._settings.x_default_handles)
        resolved_limit = limit_per_handle or self._settings.x_poll_limit_per_handle

        tweets: list[ScrapedTweet] = []
        seen_ids: set[int] = set()

        for handle in resolved_handles:
            normalized_handle = handle.lower().lstrip("@")
            user = await self._api.user_by_login(normalized_handle)
            if user is None:
                logger.warning("Unable to resolve X handle: %s", handle)
                continue

            fetch_window = min(max(resolved_limit * 5, 20), 40)
            handle_tweets: list[ScrapedTweet] = []
            async for tweet in self._api.user_tweets(user.id, limit=fetch_window):
                normalized = self._normalize_tweet(tweet)
                if normalized is None:
                    continue
                if normalized.author.handle.lower() != normalized_handle:
                    continue
                if normalized.is_repost or normalized.is_reply:
                    continue
                if normalized.tweet_id in seen_ids:
                    continue

                seen_ids.add(normalized.tweet_id)
                handle_tweets.append(normalized)

            handle_tweets.sort(key=lambda item: item.created_at, reverse=True)
            tweets.extend(handle_tweets[:resolved_limit])

        tweets.sort(key=lambda item: item.created_at, reverse=True)
        return tweets

    async def _seed_account_if_needed(self) -> None:
        """Bootstrap the local twscrape account pool once per app process."""

        if self._account_seed_attempted:
            return

        self._account_seed_attempted = True

        if not self._settings.x_account_username:
            return

        try:
            await self._api.pool.add_account(
                self._settings.x_account_username,
                self._settings.x_account_password or "",
                self._settings.x_account_email or "",
                self._settings.x_account_email_password or "",
                cookies=self._settings.x_account_cookies,
            )
            logger.info("Bootstrapped twscrape account for @%s", self._settings.x_account_username)
        except Exception as exc:  # pragma: no cover - dependent on external package state
            logger.info("Skipping twscrape account bootstrap: %s", exc)

    @staticmethod
    def _normalize_tweet(tweet: object) -> ScrapedTweet | None:
        """Convert a twscrape tweet object into the project's normalized model."""

        tweet_id = getattr(tweet, "id", None)
        text = getattr(tweet, "rawContent", None)
        user = getattr(tweet, "user", None)
        created_at = getattr(tweet, "date", None)

        if not tweet_id or not text or user is None or created_at is None:
            return None

        author = TweetAuthor(
            handle=getattr(user, "username", ""),
            display_name=(
                getattr(user, "displayname", "")
                or getattr(user, "displayName", "")
                or getattr(user, "username", "")
            ),
            user_id=getattr(user, "id", None),
        )

        return ScrapedTweet(
            tweet_id=int(tweet_id),
            url=getattr(tweet, "url", f"https://x.com/{author.handle}/status/{tweet_id}"),
            author=author,
            text=text.strip(),
            language=getattr(tweet, "lang", None),
            created_at=TwscrapeInfluencerScraper._coerce_datetime(created_at),
            like_count=int(getattr(tweet, "likeCount", 0) or 0),
            reply_count=int(getattr(tweet, "replyCount", 0) or 0),
            repost_count=int(getattr(tweet, "retweetCount", 0) or 0),
            quote_count=int(getattr(tweet, "quoteCount", 0) or 0),
            is_reply=bool(getattr(tweet, "inReplyToTweetId", None)),
            is_repost=bool(getattr(tweet, "retweetedTweet", None)),
            is_quote=bool(getattr(tweet, "quotedTweet", None)),
        )

    @staticmethod
    def _coerce_datetime(value: datetime) -> datetime:
        """Ensure normalized timestamps are timezone-aware UTC datetimes."""

        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
