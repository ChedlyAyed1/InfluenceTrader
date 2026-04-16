from __future__ import annotations

import argparse
import asyncio

from influence_trader.core.config import get_settings
from influence_trader.llm.evals import (
    EvalFamily,
    EvalRunSummary,
    run_market_impact_eval,
    run_semantic_relevance_eval,
    validate_market_impact_eval_assets,
    validate_semantic_relevance_eval_assets,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or validate prompt eval assets.")
    parser.add_argument(
        "--family",
        required=True,
        choices=["semantic_relevance", "market_impact"],
        help="Prompt family to validate or run.",
    )
    parser.add_argument(
        "--eval-version",
        default="v1",
        help="Version of the eval dataset under tests/evals/<family>/<version>/.",
    )
    parser.add_argument(
        "--prompt-version",
        default="v1",
        help=(
            "Prompt version to load from "
            "src/influence_trader/llm/prompt_assets/<family>/<version>/."
        ),
    )
    parser.add_argument(
        "--compare-to",
        help="Optional second prompt version to compare on the same eval dataset.",
    )
    parser.add_argument(
        "--mode",
        default="validate",
        choices=["validate", "run"],
        help="Validate local assets only or run online evals against the configured model.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    family = EvalFamily(args.family)

    if args.mode == "validate":
        _validate_once(
            family=family, eval_version=args.eval_version, prompt_version=args.prompt_version
        )
        if args.compare_to:
            _validate_once(
                family=family,
                eval_version=args.eval_version,
                prompt_version=args.compare_to,
            )
        return

    asyncio.run(
        _run_and_maybe_compare(
            family=family,
            eval_version=args.eval_version,
            prompt_version=args.prompt_version,
            compare_to=args.compare_to,
        )
    )


def _validate_once(*, family: EvalFamily, eval_version: str, prompt_version: str) -> None:
    if family is EvalFamily.semantic_relevance:
        case_count = len(
            validate_semantic_relevance_eval_assets(
                eval_version=eval_version,
                prompt_version=prompt_version,
            )[1]
        )
    else:
        case_count = len(
            validate_market_impact_eval_assets(
                eval_version=eval_version,
                prompt_version=prompt_version,
            )[1]
        )

    print(
        "Validated "
        f"{case_count} {family.value} eval cases with prompt version {prompt_version} "
        f"against eval set {eval_version}."
    )


async def _run_and_maybe_compare(
    *,
    family: EvalFamily,
    eval_version: str,
    prompt_version: str,
    compare_to: str | None,
) -> None:
    primary = await _run_once(
        family=family,
        eval_version=eval_version,
        prompt_version=prompt_version,
    )
    _print_summary(primary)

    if compare_to is None:
        return

    secondary = await _run_once(
        family=family,
        eval_version=eval_version,
        prompt_version=compare_to,
    )
    _print_summary(secondary)
    delta = secondary.accuracy - primary.accuracy
    print(f"Accuracy delta ({compare_to} - {prompt_version}): {delta:+.2%}")


async def _run_once(
    *,
    family: EvalFamily,
    eval_version: str,
    prompt_version: str,
) -> EvalRunSummary:
    settings = get_settings()
    if family is EvalFamily.semantic_relevance:
        return await run_semantic_relevance_eval(
            eval_version=eval_version,
            settings=settings,
            prompt_version=prompt_version,
        )
    return await run_market_impact_eval(
        settings=settings,
        eval_version=eval_version,
        prompt_version=prompt_version,
    )


def _print_summary(summary: EvalRunSummary) -> None:
    print(
        f"{summary.prompt_family.value} prompt={summary.prompt_version} "
        f"evals={summary.eval_version} "
        f"passed={summary.passed_cases}/{summary.total_cases} accuracy={summary.accuracy:.2%}"
    )
    for case_result in summary.case_results:
        status = "PASS" if case_result.passed else "FAIL"
        print(f"  [{status}] {case_result.case_id}: {case_result.details}")


if __name__ == "__main__":
    main()
