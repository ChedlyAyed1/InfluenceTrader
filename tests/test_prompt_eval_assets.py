from influence_trader.domain.models import (
    AssetClass,
    ImpactedAsset,
    MarketDirection,
    MarketImpactAnalysis,
    RelevanceLabel,
    SemanticRelevanceAssessment,
    TimeHorizon,
)
from influence_trader.llm.evals import (
    load_market_impact_eval_cases,
    load_semantic_relevance_eval_cases,
    score_market_impact_case,
    score_semantic_relevance_case,
    validate_market_impact_eval_assets,
    validate_semantic_relevance_eval_assets,
)


def test_semantic_relevance_eval_cases_validate_and_render() -> None:
    renderer, cases = validate_semantic_relevance_eval_assets(
        eval_version="v1",
        prompt_version="v1",
    )

    case_ids: set[str] = set()
    for case in cases:
        assert case.case_id not in case_ids

        prompt = renderer.render_user_prompt(case.candidate)

        assert case.candidate.tweet.text in prompt
        assert case.candidate.filter_reason in prompt
        assert case.expected.reason_focus

        case_ids.add(case.case_id)


def test_market_impact_eval_cases_validate_and_render() -> None:
    renderer, cases = validate_market_impact_eval_assets(
        eval_version="v1",
        prompt_version="v1",
    )

    case_ids: set[str] = set()
    for case in cases:
        assert case.case_id not in case_ids
        assert case.expected.impacted_assets_any

        prompt = renderer.render_user_prompt(case.candidate)

        assert case.candidate.tweet.text in prompt
        assert case.candidate.filter_reason in prompt
        assert case.expected.rationale_focus

        case_ids.add(case.case_id)


def test_semantic_relevance_case_scoring_passes_on_expected_label() -> None:
    case = load_semantic_relevance_eval_cases("v1")[0]
    assessment = SemanticRelevanceAssessment(
        label=RelevanceLabel.market_relevant,
        confidence=0.72,
        reason="Trade policy signal with a clear market transmission channel.",
    )

    result = score_semantic_relevance_case(case, assessment)

    assert result.passed is True


def test_market_impact_case_scoring_requires_direction_horizon_asset_and_disclaimer() -> None:
    case = load_market_impact_eval_cases("v1")[0]
    analysis = MarketImpactAnalysis(
        executive_summary="Tariffs could pressure semiconductor supply chains.",
        market_direction=MarketDirection.bearish,
        time_horizon=TimeHorizon.short_term,
        confidence=0.61,
        geopolitical_context="Trade tensions are rising.",
        economic_context="Tariffs may lift costs and hurt risk appetite.",
        rationale="The signal points to supply-chain stress and weaker sentiment.",
        impacted_assets=[
            ImpactedAsset(
                asset_name="US semiconductor equities",
                asset_class=AssetClass.equities,
                sector_or_theme="Semiconductors",
                expected_effect="price decline",
                confidence=0.6,
            )
        ],
        disclaimer=(
            "This analysis is for informational purposes only and does not "
            "constitute investment advice."
        ),
    )

    result = score_market_impact_case(case, analysis)

    assert result.passed is True
