# Slack API Dummy Host

This project provides a local mock Slack API server for testing bot hooks.

## Features

- Hosts common Slack Web API-style endpoints with dummy responses.
- Includes a generic catch-all endpoint for unsupported Slack methods.
- Provides an interactive Swagger-like UI at `/ui` with:
  - API list and descriptions.
  - Prefilled default parameters.
  - Execute button for custom requests.
- Adds `POST /api/slack/messages/summarize` to summarize messages across:
  - Specific channels.
  - Combined channels + direct messages.
  - Direct messages across all conversations.
  - Time/message windows (`last_n_messages`, `since_last_n_days`, `since_last_n_hours`).
- Returns processing metadata including:
  - `messages_processed`
  - `start_time`
  - `end_time`
  - `duration_ms`

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Useful URLs

- Root: <http://localhost:8000/>
- Swagger docs: <http://localhost:8000/docs>
- OpenAPI: <http://localhost:8000/openapi.json>
- Custom UI explorer: <http://localhost:8000/ui>

