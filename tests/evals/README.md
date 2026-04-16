# Prompt Evals

This directory stores prompt-eval assets that mirror the production prompt families.

## Why this exists

Prompt renderer tests verify that prompt files load and interpolate correctly. Eval assets go one
step further: they define representative market cases so we can measure whether prompt changes
improve or degrade model behavior.

## Structure

```text
tests/evals/
  README.md
  semantic_relevance/
    v1/
      cases.json
      rubric.md
  market_impact/
    v1/
      cases.json
      rubric.md
```

## Design principles

- Keep evals task-specific and close to the real production distribution
- Include happy-path, edge-case, and false-positive-guard examples
- Prefer automated checks for deterministic fields
- Pair automation with periodic human review for nuanced output quality
- Version eval assets alongside the prompt version they are meant to validate

## Suggested workflow

1. Add or update prompt files under `src/influence_trader/llm/prompt_assets/...`
2. Add eval cases that cover the intended behavior change
3. Run the fixture validation tests
4. Compare model outputs on the eval set before promoting a new prompt version
5. Keep notable production failures as future eval cases

## Commands

Validate local assets without calling the model:

```bash
uv run python -m influence_trader.llm.eval_runner --family semantic_relevance --eval-version v1 --prompt-version v1 --mode validate
```

Run online evals for one prompt version:

```bash
uv run python -m influence_trader.llm.eval_runner --family semantic_relevance --eval-version v1 --prompt-version v1 --mode run
```

Compare two prompt versions on the same eval set:

```bash
uv run python -m influence_trader.llm.eval_runner --family semantic_relevance --eval-version v1 --prompt-version v1 --compare-to v2 --mode run
```

## Current scoring plan

### `semantic_relevance`

- Primary automated check: exact match on the expected `label`
- Secondary review: verify the model reason mentions the same transmission channel as the case note

### `market_impact`

- Primary automated checks: expected `market_direction`, `time_horizon`, and disclaimer presence
- Secondary review: verify impacted assets and rationale against the rubric

## References

- OpenAI evaluation best practices:
  https://platform.openai.com/docs/guides/evaluation-best-practices
- OpenAI prompt engineering:
  https://platform.openai.com/docs/guides/prompt-engineering
- Anthropic define success criteria:
  https://docs.anthropic.com/en/docs/test-and-evaluate/define-success
- Anthropic create strong empirical evaluations:
  https://docs.anthropic.com/en/docs/test-and-evaluate/develop-tests
- Anthropic prompt templates and variables:
  https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-templates-and-variables
