# Semantic Relevance Rubric

Use this rubric when reviewing model outputs for `semantic_relevance/v1`.

## Pass criteria

- The predicted `label` matches the expected label in `cases.json`
- The reason is short and decision-useful
- The reason references the same transmission channel captured in the case note

## `market_relevant`

Use `market_relevant` only when there is a plausible transmission channel through one or more of:

- macro policy
- central banks and rates
- trade policy or sanctions
- war, conflict, or geopolitics
- energy supply and logistics
- regulation with broad market implications
- crypto policy with systemic relevance

## `not_relevant`

Use `not_relevant` for:

- generic product launches
- memes or personal chatter
- entertainment or promotion
- vague excitement without a concrete market mechanism
- narrow company updates with no clear macro spillover
