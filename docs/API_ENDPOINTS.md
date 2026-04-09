# API Endpoints

Reference document for the current `InfluenceTrader` HTTP API.

## General Notes

- Base path for versioned endpoints: `/api/v1`
- Request body format: `application/json`
- Current endpoints do not use query parameters
- Validation errors are returned by FastAPI with HTTP `422 Unprocessable Entity`
- Unexpected internal failures are currently returned as HTTP `500 Internal Server Error`

## Error Format

Most framework-level errors follow this shape:

```json
{
  "detail": "Error message"
}
```

Validation errors from FastAPI usually look like this:

```json
{
  "detail": [
    {
      "type": "string_type",
      "loc": ["body", "handles", 0],
      "msg": "Input should be a valid string",
      "input": 123
    }
  ]
}
```

---

## `GET /health`

### Description

Simple root healthcheck.

Use this endpoint to verify that the FastAPI app is up and responding.

### Query Parameters

None.

### Body Parameters

None.

### Example HTTP Request

```http
GET /health HTTP/1.1
Host: localhost:8000
```

### Success Response

Status: `200 OK`

```json
{
  "status": "ok"
}
```

### Possible Errors

- `500 Internal Server Error`: unexpected server failure

---

## `GET /api/v1/health`

### Description

Detailed healthcheck for the InfluenceTrader API.

Use this endpoint to verify:

- the API is running
- which Groq model is configured
- whether a Groq API key is present
- which X handles are configured by default

### Query Parameters

None.

### Body Parameters

None.

### Example HTTP Request

```http
GET /api/v1/health HTTP/1.1
Host: localhost:8000
```

### Success Response

Status: `200 OK`

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

### Return Fields

- `status`: service health status
- `app`: application name
- `groq_model`: configured Groq model name
- `groq_configured`: `true` if `GROQ_API_KEY` is configured
- `default_handles`: default X handles used by the scraper when no handles are provided

### Possible Errors

- `500 Internal Server Error`: unexpected server failure

---

## `POST /api/v1/tweets/fetch`

### Description

Fetches recent tweets for one or more target X accounts and optionally filters them to keep only potentially market-relevant tweets.

This endpoint is useful for:

- testing the scraper
- validating the first-stage noise filter
- previewing what will be sent to the LLM later

### Query Parameters

None.

### Body Parameters

```json
{
  "handles": ["realDonaldTrump", "elonmusk"],
  "limit_per_handle": 5,
  "relevant_only": true
}
```

### Body Fields

- `handles`: optional list of X handles
  - type: `array[string] | null`
  - if omitted or `null`, the API uses the configured default handles
- `limit_per_handle`: max tweets fetched per handle
  - type: `integer`
  - allowed range: `1..50`
  - default: `5`
- `relevant_only`: whether to return only tweets accepted by the heuristic relevance filter
  - type: `boolean`
  - default: `true`

### Example HTTP Request

```http
POST /api/v1/tweets/fetch HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "handles": ["elonmusk"],
  "limit_per_handle": 3,
  "relevant_only": true
}
```

### Success Response When `relevant_only=true`

Status: `200 OK`

```json
{
  "count": 1,
  "items": [
    {
      "tweet": {
        "tweet_id": 123456789,
        "url": "https://x.com/elonmusk/status/123456789",
        "author": {
          "handle": "elonmusk",
          "display_name": "Elon Musk",
          "user_id": 44196397
        },
        "text": "We will impose new tariffs on imports...",
        "language": "en",
        "created_at": "2026-04-09T09:15:00Z",
        "like_count": 100,
        "reply_count": 12,
        "repost_count": 8,
        "quote_count": 4,
        "is_reply": false,
        "is_repost": false,
        "is_quote": false
      },
      "filter_reason": "Matched high-impact keywords: tariff."
    }
  ]
}
```

### Success Response When `relevant_only=false`

Status: `200 OK`

```json
{
  "count": 3,
  "items": [
    {
      "tweet_id": 123456789,
      "url": "https://x.com/elonmusk/status/123456789",
      "author": {
        "handle": "elonmusk",
        "display_name": "Elon Musk",
        "user_id": 44196397
      },
      "text": "Example tweet",
      "language": "en",
      "created_at": "2026-04-09T09:15:00Z",
      "like_count": 100,
      "reply_count": 12,
      "repost_count": 8,
      "quote_count": 4,
      "is_reply": false,
      "is_repost": false,
      "is_quote": false
    }
  ],
  "relevant_count": 1
}
```

### Return Fields

When `relevant_only=true`:

- `count`: number of relevant candidates returned
- `items`: list of `RelevantTweetCandidate` objects

When `relevant_only=false`:

- `count`: number of fetched tweets returned
- `items`: list of raw normalized `ScrapedTweet` objects
- `relevant_count`: number of tweets that passed the heuristic filter

### Possible Errors

- `422 Unprocessable Entity`: invalid request body
- `500 Internal Server Error`: scraper failure, X login issue, `twscrape` issue, or unexpected server error

---

## `POST /api/v1/pipeline/run-once`

### Description

Runs the current end-to-end proof-of-concept pipeline once:

1. fetch recent tweets
2. apply heuristic relevance filtering
3. analyze the selected tweets with the Groq LLM
4. return structured market-impact analyses

This is the main POC endpoint for the first pipeline version.

### Query Parameters

None.

### Body Parameters

```json
{
  "handles": ["realDonaldTrump", "elonmusk"],
  "limit_per_handle": 5,
  "max_analyses": 3
}
```

### Body Fields

- `handles`: optional list of X handles
  - type: `array[string] | null`
  - if omitted or `null`, the API uses the configured default handles
- `limit_per_handle`: max tweets fetched per handle
  - type: `integer`
  - allowed range: `1..50`
  - default: `5`
- `max_analyses`: max number of relevant tweets sent to the LLM
  - type: `integer`
  - allowed range: `1..20`
  - default: `5`

### Example HTTP Request

```http
POST /api/v1/pipeline/run-once HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "handles": ["realDonaldTrump"],
  "limit_per_handle": 5,
  "max_analyses": 2
}
```

### Success Response

Status: `200 OK`

```json
{
  "fetched_count": 5,
  "candidate_count": 2,
  "analyzed_count": 2,
  "analyzed_items": [
    {
      "candidate": {
        "tweet": {
          "tweet_id": 123456789,
          "url": "https://x.com/realDonaldTrump/status/123456789",
          "author": {
            "handle": "realDonaldTrump",
            "display_name": "Donald J. Trump",
            "user_id": 25073877
          },
          "text": "We will impose tariffs...",
          "language": "en",
          "created_at": "2026-04-09T09:15:00Z",
          "like_count": 100,
          "reply_count": 12,
          "repost_count": 8,
          "quote_count": 4,
          "is_reply": false,
          "is_repost": false,
          "is_quote": false
        },
        "filter_reason": "Matched high-impact keywords: tariff."
      },
      "analysis": {
        "executive_summary": "The statement may increase risk-off sentiment around trade-sensitive equities.",
        "market_direction": "bearish",
        "time_horizon": "short_term",
        "confidence": 0.76,
        "geopolitical_context": "Potential escalation in trade tensions.",
        "economic_context": "Tariffs may pressure import costs and margins.",
        "rationale": "Trade barriers often affect cyclicals, manufacturing and FX expectations.",
        "impacted_assets": [
          {
            "asset_name": "S&P 500 Industrials",
            "asset_class": "equities",
            "sector_or_theme": "industrial exporters",
            "expected_effect": "Negative short-term sentiment due to tariff risk.",
            "confidence": 0.74
          }
        ],
        "disclaimer": "This is an automated informational analysis, not personalized investment advice."
      }
    }
  ]
}
```

### Return Fields

- `fetched_count`: number of tweets fetched before filtering
- `candidate_count`: number of tweets accepted by the heuristic relevance filter
- `analyzed_count`: number of candidates actually sent to the LLM
- `analyzed_items`: list of analyzed tweet objects
  - each item includes:
  - `candidate`: the filtered tweet and its filter reason
  - `analysis`: the structured market-impact JSON generated by the LLM

### Possible Errors

- `400 Bad Request`: `GROQ_API_KEY` is missing, so the full pipeline cannot run
- `422 Unprocessable Entity`: invalid request body
- `500 Internal Server Error`: scraper failure, Groq upstream failure, invalid upstream response, or unexpected server error

---

## cURL Examples

### Root Healthcheck

```bash
curl http://localhost:8000/health
```

### Detailed Healthcheck

```bash
curl http://localhost:8000/api/v1/health
```

### Fetch Relevant Tweets

```bash
curl -X POST http://localhost:8000/api/v1/tweets/fetch \
  -H "Content-Type: application/json" \
  -d "{\"handles\":[\"elonmusk\"],\"limit_per_handle\":3,\"relevant_only\":true}"
```

### Run the Pipeline Once

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run-once \
  -H "Content-Type: application/json" \
  -d "{\"handles\":[\"realDonaldTrump\"],\"limit_per_handle\":5,\"max_analyses\":2}"
```

---

## Documentation Notes

This file describes the API as it exists now.

When new endpoints are added, update this file with:

- method and path
- description
- query parameters
- body parameters
- success response example
- possible errors
- one real request example
