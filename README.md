# Slack API Dummy Host (GitHub Pages)

A **static** Slack API simulator designed to run on GitHub Pages (no Python/pip/uvicorn).

## What changed

- Replaced the previous FastAPI backend with a pure front-end implementation.
- API simulation is now handled in-browser by JavaScript.
- The project is deployable as static files on GitHub Pages.

## Features

- Slack Web API-like dummy responses for common methods:
  - `auth.test`
  - `users.info`
  - `conversations.list`
  - `conversations.history`
  - `conversations.replies`
  - `chat.postMessage`
  - `search.messages`
  - `files.list`
- Generic fallback for any Slack-style method path.
- Interactive Swagger-like explorer with:
  - API list + descriptions.
  - Prefilled default parameters.
  - Execute API button with custom parameters.
- Message summarization API simulation:
  - `POST /api/slack/messages/summarize`
  - Supports channel-only, mixed channel+DM, and DM scope.
  - Supports `last_n_messages`, `since_last_n_days`, `since_last_n_hours`.
  - Returns `messages_processed`, `start_time`, `end_time`, `duration_ms`, and summary text.

## Run locally

Open `index.html` directly in your browser, or serve static files with any static server.

## GitHub Pages

1. Push this repository to GitHub.
2. In repository settings, enable **Pages** and set source to the main branch root (or `/docs` if preferred).
3. Open the deployed URL.

## Programmatic usage

You can call the simulator from browser JS:

```js
const response = await window.slackMockApi.handleRequest({
  method: 'POST',
  path: '/api/slack/messages/summarize',
  params: {
    channels: ['C123'],
    include_direct_messages: true,
    last_n_messages: 25
  }
});
console.log(response);
```
