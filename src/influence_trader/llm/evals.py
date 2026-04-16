from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import Field

from influence_trader.core.config import Settings
from influence_trader.domain.models import (
    MarketDirection,
    MarketImpactAnalysis,
    RelevanceLabel,
    RelevantTweetCandidate,
    SemanticRelevanceAssessment,
    StrictModel,
    TimeHorizon,
)
from influence_trader.llm.client import GroqMarketAnalysisClient
from influence_trader.llm.prompt_loader import (
    MarketImpactPromptRenderer,
    SemanticRelevancePromptRenderer,
)


class EvalFamily(StrEnum):
    semantic_relevance = "semantic_relevance"
    market_impact = "market_impact"


class SemanticRelevanceEvalExpectation(StrictModel):
    label: RelevanceLabel
    reason_focus: str


class SemanticRelevanceEvalCase(StrictModel):
    case_id: str
    prompt_family: str
    prompt_version: str
    tags: list[str] = Field(default_factory=list)
    candidate: RelevantTweetCandidate
    expected: SemanticRelevanceEvalExpectation


class MarketImpactEvalExpectation(StrictModel):
    market_direction: MarketDirection
    time_horizon: TimeHorizon
    minimum_confidence: float = Field(ge=0.0, le=1.0)
    impacted_assets_any: list[str]
    rationale_focus: str


class MarketImpactEvalCase(StrictModel):
    case_id: str
    prompt_family: str
    prompt_version: str
    tags: list[str] = Field(default_factory=list)
    candidate: RelevantTweetCandidate
    expected: MarketImpactEvalExpectation


@dataclass(frozen=True, slots=True)
class EvalCaseResult:
    case_id: str
    passed: bool
    details: str


@dataclass(frozen=True, slots=True)
class EvalRunSummary:
    prompt_family: EvalFamily
    prompt_version: str
    eval_version: str
    total_cases: int
    passed_cases: int
    case_results: tuple[EvalCaseResult, ...]

    @property
    def accuracy(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.passed_cases / self.total_cases


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def eval_cases_path(prompt_family: EvalFamily, eval_version: str) -> Path:
    return project_root() / "tests" / "evals" / prompt_family / eval_version / "cases.json"


def load_semantic_relevance_eval_cases(eval_version: str) -> list[SemanticRelevanceEvalCase]:
    raw_cases = json.loads(
        eval_cases_path(EvalFamily.semantic_relevance, eval_version).read_text(encoding="utf-8")
    )
    return [SemanticRelevanceEvalCase.model_validate(case) for case in raw_cases]


def load_market_impact_eval_cases(eval_version: str) -> list[MarketImpactEvalCase]:
    raw_cases = json.loads(
        eval_cases_path(EvalFamily.market_impact, eval_version).read_text(encoding="utf-8")
    )
    return [MarketImpactEvalCase.model_validate(case) for case in raw_cases]


def validate_semantic_relevance_eval_assets(
    *,
    eval_version: str,
    prompt_version: str,
) -> tuple[SemanticRelevancePromptRenderer, list[SemanticRelevanceEvalCase]]:
    renderer = SemanticRelevancePromptRenderer(version=prompt_version)
    cases = load_semantic_relevance_eval_cases(eval_version)
    case_ids: set[str] = set()

    for case in cases:
        if case.prompt_family != EvalFamily.semantic_relevance:
            msg = f"Unexpected prompt family in case {case.case_id}: {case.prompt_family}"
            raise ValueError(msg)
        if case.case_id in case_ids:
            msg = f"Duplicate eval case id detected: {case.case_id}"
            raise ValueError(msg)
        renderer.render_user_prompt(case.candidate)
        case_ids.add(case.case_id)

    return renderer, cases


def validate_market_impact_eval_assets(
    *,
    eval_version: str,
    prompt_version: str,
) -> tuple[MarketImpactPromptRenderer, list[MarketImpactEvalCase]]:
    renderer = MarketImpactPromptRenderer(version=prompt_version)
    cases = load_market_impact_eval_cases(eval_version)
    case_ids: set[str] = set()

    for case in cases:
        if case.prompt_family != EvalFamily.market_impact:
            msg = f"Unexpected prompt family in case {case.case_id}: {case.prompt_family}"
            raise ValueError(msg)
        if case.case_id in case_ids:
            msg = f"Duplicate eval case id detected: {case.case_id}"
            raise ValueError(msg)
        renderer.render_user_prompt(case.candidate)
        case_ids.add(case.case_id)

    return renderer, cases


def score_semantic_relevance_case(
    case: SemanticRelevanceEvalCase,
    assessment: SemanticRelevanceAssessment,
) -> EvalCaseResult:
    passed = assessment.label is case.expected.label
    details = (
        f"expected={case.expected.label.value} actual={assessment.label.value} "
        f"confidence={assessment.confidence:.2f}"
    )
    return EvalCaseResult(case_id=case.case_id, passed=passed, details=details)


def score_market_impact_case(
    case: MarketImpactEvalCase,
    analysis: MarketImpactAnalysis,
) -> EvalCaseResult:
    normalized_assets = [_normalize_text(asset.asset_name) for asset in analysis.impacted_assets]
    expected_assets = [
        _normalize_text(asset_name) for asset_name in case.expected.impacted_assets_any
    ]
    has_expected_asset = any(
        expected_asset in actual_asset or actual_asset in expected_asset
        for expected_asset in expected_assets
        for actual_asset in normalized_assets
    )
    has_disclaimer = bool(analysis.disclaimer.strip())
    passed = (
        analysis.market_direction is case.expected.market_direction
        and analysis.time_horizon is case.expected.time_horizon
        and analysis.confidence >= case.expected.minimum_confidence
        and has_expected_asset
        and has_disclaimer
    )
    details = (
        f"direction={analysis.market_direction.value} "
        f"horizon={analysis.time_horizon.value} "
        f"confidence={analysis.confidence:.2f} "
        f"matched_asset={has_expected_asset} "
        f"disclaimer={has_disclaimer}"
    )
    return EvalCaseResult(case_id=case.case_id, passed=passed, details=details)


async def run_semantic_relevance_eval(
    *,
    settings: Settings,
    eval_version: str,
    prompt_version: str,
) -> EvalRunSummary:
    _, cases = validate_semantic_relevance_eval_assets(
        eval_version=eval_version,
        prompt_version=prompt_version,
    )
    client = GroqMarketAnalysisClient(
        settings,
        semantic_relevance_prompt_version=prompt_version,
    )
    try:
        case_results = []
        for case in cases:
            assessment = await client.classify_relevance(case.candidate)
            case_results.append(score_semantic_relevance_case(case, assessment))
    finally:
        await client.close()

    passed_cases = sum(result.passed for result in case_results)
    return EvalRunSummary(
        prompt_family=EvalFamily.semantic_relevance,
        prompt_version=prompt_version,
        eval_version=eval_version,
        total_cases=len(case_results),
        passed_cases=passed_cases,
        case_results=tuple(case_results),
    )


async def run_market_impact_eval(
    *,
    settings: Settings,
    eval_version: str,
    prompt_version: str,
) -> EvalRunSummary:
    _, cases = validate_market_impact_eval_assets(
        eval_version=eval_version,
        prompt_version=prompt_version,
    )
    client = GroqMarketAnalysisClient(
        settings,
        market_impact_prompt_version=prompt_version,
    )
    try:
        case_results = []
        for case in cases:
            analysis = await client.analyze_tweet(case.candidate)
            case_results.append(score_market_impact_case(case, analysis))
    finally:
        await client.close()

    passed_cases = sum(result.passed for result in case_results)
    return EvalRunSummary(
        prompt_family=EvalFamily.market_impact,
        prompt_version=prompt_version,
        eval_version=eval_version,
        total_cases=len(case_results),
        passed_cases=passed_cases,
        case_results=tuple(case_results),
    )


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())
