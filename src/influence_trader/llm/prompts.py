from __future__ import annotations

from influence_trader.domain.models import RelevantTweetCandidate
from influence_trader.llm.prompt_loader import MarketImpactPromptRenderer

# Backward-compatible shim kept temporarily while the codebase migrates
# to versioned prompt assets under `llm/prompt_assets/`.
_renderer = MarketImpactPromptRenderer(version="v1")

SYSTEM_PROMPT = _renderer.system_prompt


def build_user_prompt(candidate: RelevantTweetCandidate) -> str:
    return _renderer.render_user_prompt(candidate)
