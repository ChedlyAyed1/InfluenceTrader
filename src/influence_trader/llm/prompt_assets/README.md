# Prompt Assets

This directory stores versioned prompt bundles used by the LLM layer.

## Structure

Each prompt family lives under its own directory:

```text
prompt_assets/
  <prompt_family>/
    <version>/
      metadata.json
      system.md
      user.md
```

Current families:

- `market_impact`
- `semantic_relevance`

## Contract

Each version directory is immutable once shipped.

- `system.md`: stable role, guardrails, and output rules
- `user.md`: input-specific template rendered at runtime
- `metadata.json`: documentation and validation contract for the bundle

## Versioning Rules

- Create a new directory such as `v2` for behavior changes
- Do not silently rewrite `v1` after code or evals depend on it
- Keep placeholder names in `user.md` aligned with `metadata.json`
- Prefer narrow prompt families with one responsibility each

## Authoring Guidelines

- Keep `system.md` policy-oriented and reusable across requests
- Keep `user.md` focused on task input and decision criteria
- Use descriptive placeholder names such as `tweet_text` or `prefilter_reason`
- Record the purpose of the prompt version in `metadata.json`

## Eval Pairing

Keep prompt versions paired with eval assets under `tests/evals/<prompt_family>/<version>/`.

- Add or update `cases.json` whenever prompt behavior changes
- Use `rubric.md` for review guidance that should not live inside individual test cases
- Treat prompt changes and eval changes as one review unit
