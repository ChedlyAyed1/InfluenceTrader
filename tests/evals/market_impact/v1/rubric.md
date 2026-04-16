# Market Impact Rubric

Use this rubric when reviewing model outputs for `market_impact/v1`.

## Pass criteria

- `market_direction` matches the expected directional bias or stays within a justified conservative interpretation
- `time_horizon` is plausible for the news flow
- `confidence` is not overstated for ambiguous signals
- The rationale names a real transmission channel instead of generic market commentary
- The disclaimer is present

## Review dimensions

- Transmission channel clarity: Does the output explain how the tweet could move markets?
- Asset specificity: Does it name plausible impacted assets or sectors?
- Conservatism: Does it avoid overstating weak signals?
- Time alignment: Does the chosen horizon fit the event described?
- Schema fidelity: Does the output remain fully valid JSON?
