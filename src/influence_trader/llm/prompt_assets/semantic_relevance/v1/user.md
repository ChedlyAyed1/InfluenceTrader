<task>
Classify whether this tweet is relevant for full market impact analysis.
</task>

<tweet_context>
author_handle: @$author_handle
author_display_name: $author_display_name
posted_at: $posted_at
tweet_url: $tweet_url
prefilter_reason: $prefilter_reason
</tweet_context>

<tweet_text>
$tweet_text
</tweet_text>

<decision_criteria>
- Choose "market_relevant" only if there is a plausible macro, policy,
  geopolitical, regulatory, or broad risk-sentiment transmission channel.
- Choose "not_relevant" for vague, personal, promotional, entertainment, or
  low-signal commentary.
- Keep the reason short and decision-useful.
</decision_criteria>

