# API Reference

This document describes the current HTTP API exposed by InfluenceTrader.

Base URL when running locally:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Overview

The application currently exposes four endpoints:

- `GET /health`
- `GET /api/v1/health`
- `POST /api/v1/tweets/fetch`
- `POST /api/v1/pipeline/run-once`

## 1. `GET /health`

Basic liveness probe.

### Request

```http
GET /health
```

### Response

```json
{
  "status": "ok"
}
```

### Errors

- usually none unless the app itself is not running

## 2. `GET /api/v1/health`

Application-level health and configuration summary.

### Request

```http
GET /api/v1/health
```

### Response

```json
{
  "status": "ok",
  "app": "InfluenceTrader",
  "groq_model": "openai/gpt-oss-20b",
  "groq_configured": true,
  "default_handles": [
    "realDonaldTrump",
    "elonmusk",
    "warrenbuffett",
    "jeromepowell"
  ]
}
```

### Notes

- `groq_configured=false` means `GROQ_API_KEY` is missing
- this endpoint is useful before testing any LLM-based path

## 3. `POST /api/v1/tweets/fetch`

Fetch tweets for one or more handles.

This endpoint supports two modes:

- raw scraped tweets only
- semantically filtered relevant candidates

### Request Body

```json
{
  "handles": ["KobeissiLetter", "financialjuice"],
  "limit_per_handle": 3,
  "relevant_only": true
}
```

### Fields

- `handles`
  - type: `list[str] | null`
  - optional
  - if omitted, the app uses `X_DEFAULT_HANDLES`
- `limit_per_handle`
  - type: `int`
  - default: `5`
  - minimum: `1`
  - maximum: `50`
  - meaning: newest accepted tweets kept per handle
- `relevant_only`
  - type: `bool`
  - default: `true`

### Mode A: `relevant_only=false`

Returns raw normalized scraped tweets.

#### Example Request

```json
{
  "handles": ["realDonaldTrump"],
  "limit_per_handle": 3,
  "relevant_only": false
}
```

#### Example Response

```json
{
  "count": 3,
  "items": [
    {
      "tweet_id": 123,
      "url": "https://x.com/example/status/123",
      "author": {
        "handle": "example",
        "display_name": "Example",
        "user_id": 1
      },
      "text": "Example tweet",
      "language": "en",
      "created_at": "2026-04-14T10:00:00Z",
      "like_count": 10,
      "reply_count": 2,
      "repost_count": 1,
      "quote_count": 0,
      "is_reply": false,
      "is_repost": false,
      "is_quote": false
    }
  ]
}
```

#### Behavior

- no Groq call
- useful for scraper debugging
- includes replies and reposts if the account feed contains them

### Mode B: `relevant_only=true`

Returns only the tweets that survived relevance filtering.

#### Example Request

```json
{
  "handles": ["financialjuice", "KobeissiLetter"],
  "limit_per_handle": 3,
  "relevant_only": true
}
```

#### Example Response

```json
{
  "count": 2,
  "items": [
    {
      "tweet": {
        "tweet_id": 456,
        "url": "https://x.com/KobeissiLetter/status/456",
        "author": {
          "handle": "KobeissiLetter",
          "display_name": "The Kobeissi Letter",
          "user_id": 3316376038
        },
        "text": "Example macro tweet",
        "language": "en",
        "created_at": "2026-04-14T11:00:00Z",
        "like_count": 500,
        "reply_count": 20,
        "repost_count": 80,
        "quote_count": 10,
        "is_reply": false,
        "is_repost": false,
        "is_quote": false
      },
      "filter_reason": "Clear macro transmission channel through sanctions, oil supply, and geopolitical risk."
    }
  ]
}
```

#### Behavior

- runs structural prefiltering first
- if `GROQ_API_KEY` is configured, runs semantic relevance classification
- if `GROQ_API_KEY` is not configured, only the structural prefilter is applied

### Possible Errors

- `429 Too Many Requests`
  - Groq rate limit reached during semantic relevance classification
- `422 Unprocessable Entity`
  - invalid request body
- `500 Internal Server Error`
  - unexpected runtime issue

## 4. `POST /api/v1/pipeline/run-once`

Run the full pipeline once:

- scrape tweets
- filter candidates
- analyze retained candidates
- return structured market analysis

### Request Body

```json
{
  "handles": ["KobeissiLetter"],
  "limit_per_handle": 3,
  "max_analyses": 2
}
```

### Fields

- `handles`
  - type: `list[str] | null`
  - optional
- `limit_per_handle`
  - type: `int`
  - default: `5`
  - minimum: `1`
  - maximum: `50`
- `max_analyses`
  - type: `int`
  - default: `5`
  - minimum: `1`
  - maximum: `20`
  - meaning: maximum number of relevant candidates sent to the full market-analysis prompt

### Example Response

```json
{
  "fetched_count": 3,
  "candidate_count": 3,
  "analyzed_count": 2,
  "analyzed_items": [
    {
      "candidate": {
        "tweet": {
          "tweet_id": 456,
          "url": "https://x.com/KobeissiLetter/status/456",
          "author": {
            "handle": "KobeissiLetter",
            "display_name": "The Kobeissi Letter",
            "user_id": 3316376038
          },
          "text": "Example macro tweet",
          "language": "en",
          "created_at": "2026-04-14T11:00:00Z",
          "like_count": 500,
          "reply_count": 20,
          "repost_count": 80,
          "quote_count": 10,
          "is_reply": false,
          "is_repost": false,
          "is_quote": false
        },
        "filter_reason": "Clear macro transmission channel."
      },
      "analysis": {
        "executive_summary": "Example summary",
        "market_direction": "mixed",
        "time_horizon": "intraday",
        "confidence": 0.65,
        "geopolitical_context": "Example geopolitical context",
        "economic_context": "Example economic context",
        "rationale": "Example rationale",
        "impacted_assets": [
          {
            "asset_name": "WTI Crude Oil",
            "asset_class": "commodities",
            "sector_or_theme": "Energy",
            "expected_effect": "price decline",
            "confidence": 0.7
          }
        ],
        "disclaimer": "This analysis is for informational purposes only and does not constitute investment advice."
      }
    }
  ]
}
```

### Response Fields

- `fetched_count`
  - number of scraped tweets after per-handle limiting
- `candidate_count`
  - number of tweets retained after relevance filtering
- `analyzed_count`
  - number of tweets actually analyzed by the final market-analysis prompt
- `analyzed_items`
  - list of analyzed tweet objects

### Possible Errors

- `400 Bad Request`
  - `GROQ_API_KEY` missing
- `429 Too Many Requests`
  - Groq rate limit reached during relevance classification or final analysis
- `422 Unprocessable Entity`
  - invalid request body
- `500 Internal Server Error`
  - unexpected runtime issue

## Operational Notes

### `limit_per_handle`

This means:

- inspect a bounded recent window per account
- normalize and filter accepted tweets
- keep the newest `N` accepted tweets for that handle

So:

- `limit_per_handle=1` means one newest accepted tweet per handle
- `limit_per_handle=3` means three newest accepted tweets per handle

### Raw Fetch vs Relevant Fetch

Use:

- `relevant_only=false` to debug scraping
- `relevant_only=true` to debug semantic selection
- `pipeline/run-once` to validate the whole end-to-end product

### Recommended Test Accounts

For market-heavy testing:

- `KobeissiLetter`
- `financialjuice`

These are often better validation targets than celebrity or general political
accounts.
