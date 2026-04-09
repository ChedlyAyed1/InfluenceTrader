# InfluenceTrader

A clean proof of concept for monitoring high-impact macro and geopolitical tweets,
filtering noise, and producing structured market analysis that can later feed a
real-time trading intelligence pipeline.

## Why FastAPI Instead of Django 6.0?

For this project, `FastAPI` is the better fit:

- the core of the product is an asynchronous I/O-bound pipeline (`twscrape`,
  HTTP calls to Groq, a scheduler, and Telegram webhooks)
- we want a lightweight API that is easy to test and evolve
- Django 6.0 is still an excellent framework, but it is a better fit when the
  priority is a rich admin panel, server-rendered pages, and a full back-office
  from day one

A `Streamlit` dashboard can still be added later without coupling the whole
application to Django.

## Selected Groq Model

As of April 9, 2026, Groq documentation still lists
`llama-3.3-70b-versatile` as a production model, but strict structured JSON
outputs (`strict: true`) are officially supported by `openai/gpt-oss-20b` and
`openai/gpt-oss-120b`.

For this project, the default choice is:

- `openai/gpt-oss-20b`

Why:

- better fit for a strict JSON schema
- faster and more affordable than `openai/gpt-oss-120b`
- more reliable than a best-effort JSON mode when automating a pipeline

## What Phase 1 Includes

- a `twscrape` scraper that normalizes tweets into domain objects
- a heuristic relevance filter that removes part of the noise before any LLM call
- a Groq client that produces strict JSON analysis
- a FastAPI app exposing proof-of-concept endpoints for fetching and analyzing tweets

## Structure

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

## Installation

```bash
uv sync --group dev
cp .env.example .env
```

## Run Locally

```bash
uv run uvicorn influence_trader.main:app --reload
```

## Docker

Build the image:

```bash
docker build -t influence-trader .
```

Run directly:

```bash
docker run --rm -p 8000:8000 --env-file .env -v $(pwd)/data:/app/data influence-trader
```

Run with Compose:

```bash
docker compose up --build
```

Stop:

```bash
docker compose down
```

## Quality Checks

```bash
uv run ruff check .
uv run mypy src tests
uv run pytest
uv run pre-commit install
uv run pre-commit run --all-files
```

## POC Endpoints

- `GET /health`
- `POST /api/v1/tweets/fetch`
- `POST /api/v1/pipeline/run-once`

## Important Notes

- `twscrape` requires at least one authenticated X/Twitter account.
- X scraping is not guaranteed to remain stable over time, so the next phases
  should include retries, account rotation, proxies, and observability.
- The project is not truly "100% free" in a durable production setting if you
  want resilience: X may require multiple accounts or proxies, and Groq's free
  developer plan should not be treated as unlimited guaranteed capacity.
