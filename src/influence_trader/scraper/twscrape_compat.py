from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import cast

from influence_trader.core.config import Settings

logger = logging.getLogger(__name__)

_PATCH_APPLIED = False


def apply_twscrape_workarounds(settings: Settings) -> None:
    global _PATCH_APPLIED

    if _PATCH_APPLIED or not settings.x_twscrape_enable_xclid_workaround:
        return

    try:
        import twscrape.xclid as xclid
    except Exception as exc:  # pragma: no cover - depends on optional runtime state
        logger.warning("Unable to import twscrape.xclid for workaround patch: %s", exc)
        return

    original_parse_anim_idx = cast(Callable[[str], Awaitable[list[int]]], xclid.parse_anim_idx)
    fallback_script_url = settings.x_twscrape_ondemand_script_url

    async def patched_parse_anim_idx(text: str) -> list[int]:
        try:
            return await original_parse_anim_idx(text)
        except Exception as exc:
            message = str(exc)
            should_retry_with_fallback = (
                isinstance(exc, IndexError)
                or "list index out of range" in message
                or "Failed to parse scripts" in message
                or "Couldn't get XClientTxId scripts" in message
            )
            if not should_retry_with_fallback:
                raise

            logger.warning(
                "Applying twscrape xclid fallback using static ondemand script: %s",
                fallback_script_url,
            )
            script_text = await xclid.get_tw_page_text(fallback_script_url)
            items = [int(match.group(2)) for match in xclid.INDICES_REGEX.finditer(script_text)]
            if not items:
                raise
            return items

    xclid.parse_anim_idx = patched_parse_anim_idx
    _PATCH_APPLIED = True
