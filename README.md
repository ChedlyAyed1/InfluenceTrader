# InfluenceTrader

A FastAPI proof of concept for:

- scraping tweets from selected X accounts
- normalizing them into domain models
- filtering obvious noise with a structural prefilter
- classifying semantic market relevance with Groq
- generating strict structured market analysis JSON

The project is built as a pipeline, not a single prompt call.

## Current Pipeline

The application currently works like this:

1. scrape recent tweets from one or more X handles
2. normalize them into `ScrapedTweet`
3. apply a lightweight structural prefilter
4. if Groq is configured, classify each remaining tweet as:
   - `market_relevant`
   - `not_relevant`
5. run full market-impact analysis only on the retained candidates

## Why FastAPI

`FastAPI` is a strong fit here because the product is mostly:

- asynchronous I/O
- external API calls
- structured JSON APIs
- background/pipeline style work

## Current Stack

- `FastAPI` for the HTTP API
- `twscrape` for X scraping
- `Groq` for semantic relevance classification and final analysis
- `Pydantic` for strict domain and response validation
- `Docker` / `docker compose` for local runtime

## Project Structure

```text
src/influence_trader/
  api/
  core/
  domain/
  llm/
    prompt_assets/
  pipeline/
  scraper/
tests/
```

## What Phase 1 Includes

- authenticated X scraping through `twscrape`
- a local compatibility workaround for the known `twscrape xclid` issue
- strict internal tweet normalization
- structural prefiltering before any expensive LLM call
- semantic relevance classification with Groq
- full market-impact analysis with strict JSON schema output
- Swagger UI for manual testing

## Environment

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Main settings:

- `GROQ_API_KEY`
- `GROQ_MODEL`
- `X_ACCOUNT_USERNAME`
- `X_ACCOUNT_COOKIES`
- `X_DEFAULT_HANDLES`

Notes:

- `twscrape` requires at least one authenticated X account
- cookies are generally more stable than login/password
- do not commit real cookies or API keys

## Installation

```bash
uv sync --group dev
```

## Run Locally

```bash
uv run uvicorn influence_trader.main:app --reload
```

Then open:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker

Build and run with Compose:

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

The app will be available at:

- `http://localhost:8000`

## Quality Checks

```bash
uv run ruff check .
uv run mypy src tests
uv run pytest
uv run pre-commit install
uv run pre-commit run --all-files
```

## Endpoints

The current API exposes:

- `GET /health`
- `GET /api/v1/health`
- `POST /api/v1/tweets/fetch`
- `POST /api/v1/pipeline/run-once`

Detailed request/response documentation lives in [API.md](/c:/Work/InfluenceTrader/API.md).

## Fetch Modes

`POST /api/v1/tweets/fetch` has two useful modes:

### Raw scrape mode

```json
{
  "handles": ["realDonaldTrump"],
  "limit_per_handle": 3,
  "relevant_only": false
}
```

Behavior:

- no Groq call
- returns normalized scraped tweets only
- useful for debugging the scraper itself

### Relevant tweets mode

```json
{
  "handles": ["financialjuice", "KobeissiLetter"],
  "limit_per_handle": 3,
  "relevant_only": true
}
```

Behavior:

- scrape tweets
- run structural prefilter
- if Groq is configured, run semantic relevance classification
- return only retained candidates

## Full Pipeline Example

```json
{
  "handles": ["KobeissiLetter"],
  "limit_per_handle": 3,
  "max_analyses": 2
}
```

Typical flow:

- fetch `3` tweets
- keep `3` semantically relevant candidates
- analyze only `2` because `max_analyses=2`

This is the cleanest endpoint for validating the whole product end to end.

## Current Behavior Notes

- `limit_per_handle` now means: keep the newest accepted `N` tweets per handle
- `relevant_only=false` does not spend Groq quota
- `relevant_only=true` may call Groq for semantic classification
- `pipeline/run-once` requires `GROQ_API_KEY`
- Groq `429` errors are surfaced as HTTP `429` instead of a generic `500`

## Example Accounts For Testing

These are useful for macro / market-heavy tests:

- `KobeissiLetter`
- `financialjuice`

They usually produce much better test cases for this project than celebrity or
general political accounts.

## Important Caveats

- X scraping remains inherently fragile over time
- `twscrape` behavior can change when X changes internals
- Groq free or developer quotas are not unlimited
- semantic filtering is much better than keyword matching, but still not perfect

## Next Logical Steps

- improve retry / backoff behavior around Groq rate limits
- batch or cap semantic classification more aggressively
- persist analyzed events
- add scheduling and alerting
- add a downstream delivery channel such as Telegram

## License

This project is released under the [MIT License].
