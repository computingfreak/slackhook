from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import Body, FastAPI, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Slack API Dummy Host",
    description=(
        "Mock Slack Web API server with dummy responses and an interactive API explorer. "
        "Use this for local Slack bot hook development."
    ),
    version="1.0.0",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


MESSAGES_BY_CONVERSATION: dict[str, list[dict[str, Any]]] = {
    "C123": [
        {
            "ts": "1710000000.000100",
            "user": "U111",
            "text": "Incident started around 7 AM. Investigating root cause.",
        },
        {
            "ts": "1710001800.000200",
            "user": "U222",
            "text": "DB failover done. Error rates are falling quickly.",
        },
        {
            "ts": "1710003600.000300",
            "user": "U111",
            "text": "All services stable now. Monitoring for 30 minutes.",
        },
    ],
    "C456": [
        {
            "ts": "1710200000.000100",
            "user": "U333",
            "text": "Sprint planning at 2 PM. Share blockers before then.",
        },
        {
            "ts": "1710201200.000200",
            "user": "U111",
            "text": "Blocked on design review, should clear by tomorrow.",
        },
    ],
    "D111-U222": [
        {
            "ts": "1710300000.000100",
            "user": "U111",
            "text": "Can you review the bot webhook change?",
        },
        {
            "ts": "1710300900.000200",
            "user": "U222",
            "text": "Reviewed. Looks good, only one minor comment.",
        },
    ],
}


class SummaryRequest(BaseModel):
    channels: list[str] | None = Field(
        default=None,
        description="List of channel IDs (public/private) or DM IDs to include.",
        examples=[["C123", "C456"]],
    )
    include_direct_messages: bool = Field(
        default=False,
        description="If true, include all DM conversations in addition to selected channels.",
    )
    last_n_messages: int | None = Field(
        default=50,
        ge=1,
        le=5000,
        description="Select the latest N messages after other time filters are applied.",
    )
    since_last_n_days: int | None = Field(
        default=None,
        ge=1,
        le=365,
        description="Limit to messages from the last N days.",
    )
    since_last_n_hours: int | None = Field(
        default=None,
        ge=1,
        le=24 * 30,
        description="Limit to messages from the last N hours.",
    )


class GenericSlackRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


API_CATALOG = [
    {
        "name": "auth.test",
        "method": "GET",
        "path": "/api/slack/auth/test",
        "description": "Validate auth context.",
        "default_params": {},
    },
    {
        "name": "users.info",
        "method": "POST",
        "path": "/api/slack/users/info",
        "description": "Return a dummy user profile.",
        "default_params": {"user": "U111"},
    },
    {
        "name": "conversations.list",
        "method": "GET",
        "path": "/api/slack/conversations/list",
        "description": "List channels and DMs.",
        "default_params": {"exclude_archived": True, "limit": 100},
    },
    {
        "name": "conversations.history",
        "method": "POST",
        "path": "/api/slack/conversations/history",
        "description": "Return message history for a channel.",
        "default_params": {"channel": "C123", "limit": 20},
    },
    {
        "name": "conversations.replies",
        "method": "POST",
        "path": "/api/slack/conversations/replies",
        "description": "Return a thread-style dummy reply list.",
        "default_params": {"channel": "C123", "ts": "1710000000.000100", "limit": 10},
    },
    {
        "name": "chat.postMessage",
        "method": "POST",
        "path": "/api/slack/chat/postMessage",
        "description": "Echo posted message with generated timestamp.",
        "default_params": {"channel": "C123", "text": "Hello from mock"},
    },
    {
        "name": "search.messages",
        "method": "POST",
        "path": "/api/slack/search/messages",
        "description": "Search dummy messages by substring.",
        "default_params": {"query": "incident", "count": 20},
    },
    {
        "name": "files.list",
        "method": "GET",
        "path": "/api/slack/files/list",
        "description": "Return static file metadata.",
        "default_params": {"channel": "C123", "count": 20},
    },
    {
        "name": "messages.summarize",
        "method": "POST",
        "path": "/api/slack/messages/summarize",
        "description": "Summarize channel and/or DM messages with window filters.",
        "default_params": {
            "channels": ["C123", "C456"],
            "include_direct_messages": True,
            "last_n_messages": 10,
            "since_last_n_days": 7,
            "since_last_n_hours": None,
        },
    },
]


@app.get("/api/catalog")
def api_catalog() -> dict[str, Any]:
    return {"ok": True, "apis": API_CATALOG}


@app.get("/api/slack/auth/test")
def auth_test() -> dict[str, Any]:
    return {
        "ok": True,
        "url": "https://mock.slack.local/",
        "team": "Dummy Team",
        "user": "dummy-bot",
        "team_id": "TMOCK",
        "user_id": "UBOT",
    }


@app.post("/api/slack/users/info")
def users_info(payload: dict[str, Any] = Body(default={"user": "U111"})) -> dict[str, Any]:
    user_id = payload.get("user", "U111")
    return {
        "ok": True,
        "user": {
            "id": user_id,
            "name": f"mock-{user_id.lower()}",
            "real_name": "Mock User",
            "is_bot": False,
            "tz": "UTC",
            "profile": {"email": f"{user_id.lower()}@example.com", "title": "Engineer"},
        },
    }


@app.get("/api/slack/conversations/list")
def conversations_list(
    exclude_archived: bool = Query(True), limit: int = Query(100, ge=1, le=1000)
) -> dict[str, Any]:
    channels = []
    for cid in list(MESSAGES_BY_CONVERSATION.keys())[:limit]:
        is_dm = cid.startswith("D")
        channels.append(
            {
                "id": cid,
                "name": f"conversation-{cid.lower()}",
                "is_archived": False,
                "is_im": is_dm,
                "is_channel": not is_dm,
            }
        )
    return {"ok": True, "exclude_archived": exclude_archived, "channels": channels}


@app.post("/api/slack/conversations/history")
def conversations_history(payload: dict[str, Any] = Body(default={"channel": "C123", "limit": 20})) -> dict[str, Any]:
    channel = payload.get("channel", "C123")
    limit = int(payload.get("limit", 20))
    messages = MESSAGES_BY_CONVERSATION.get(channel, [])[-limit:]
    return {"ok": True, "channel": channel, "messages": messages, "has_more": False}


@app.post("/api/slack/conversations/replies")
def conversations_replies(
    payload: dict[str, Any] = Body(
        default={"channel": "C123", "ts": "1710000000.000100", "limit": 10}
    )
) -> dict[str, Any]:
    channel = payload.get("channel", "C123")
    thread_ts = payload.get("ts", "1710000000.000100")
    limit = int(payload.get("limit", 10))
    base = MESSAGES_BY_CONVERSATION.get(channel, [])[:1]
    replies = [
        {
            "type": "message",
            "user": "U444",
            "text": f"Reply {i + 1} in thread {thread_ts}",
            "ts": f"1710005000.000{i}",
            "thread_ts": thread_ts,
        }
        for i in range(limit)
    ]
    return {"ok": True, "channel": channel, "messages": base + replies, "has_more": False}


@app.post("/api/slack/chat/postMessage")
def chat_post_message(payload: dict[str, Any] = Body(default={"channel": "C123", "text": "Hello from mock"})) -> dict[str, Any]:
    channel = payload.get("channel", "C123")
    text = payload.get("text", "")
    now_ts = f"{utc_now().timestamp():.6f}"
    new_message = {"ts": now_ts, "user": "UBOT", "text": text}
    MESSAGES_BY_CONVERSATION.setdefault(channel, []).append(new_message)

    return {
        "ok": True,
        "channel": channel,
        "ts": now_ts,
        "message": {"text": text, "bot_id": "BMOCK", "type": "message", "ts": now_ts},
    }


@app.post("/api/slack/search/messages")
def search_messages(payload: dict[str, Any] = Body(default={"query": "incident", "count": 20})) -> dict[str, Any]:
    query = str(payload.get("query", "")).lower()
    count = int(payload.get("count", 20))
    matches: list[dict[str, Any]] = []
    for channel, messages in MESSAGES_BY_CONVERSATION.items():
        for msg in messages:
            if query in msg.get("text", "").lower():
                matches.append({"channel": {"id": channel}, "text": msg["text"], "ts": msg["ts"]})

    return {"ok": True, "messages": {"matches": matches[:count], "total": len(matches)}}


@app.get("/api/slack/files/list")
def files_list(channel: str = Query("C123"), count: int = Query(20, ge=1, le=1000)) -> dict[str, Any]:
    files = [
        {
            "id": f"F{i:06d}",
            "name": f"report-{i}.txt",
            "title": "Dummy artifact",
            "mimetype": "text/plain",
            "url_private": f"https://mock.slack.local/files/F{i:06d}",
            "channels": [channel],
        }
        for i in range(min(count, 30))
    ]
    return {"ok": True, "files": files}


def parse_ts(ts: str) -> datetime:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc)


def format_summary(messages: list[dict[str, Any]], mode: Literal["channels", "direct_messages", "mixed"]) -> str:
    if not messages:
        return "No messages were found in the selected window."

    snippets = [msg.get("text", "") for msg in messages[:8]]
    highlights = "; ".join(snippets)
    return f"Summary ({mode}): {highlights[:500]}"


@app.post("/api/slack/messages/summarize")
def summarize_messages(req: SummaryRequest) -> dict[str, Any]:
    started = utc_now()

    selected_ids: set[str] = set(req.channels or [])
    if req.include_direct_messages:
        selected_ids.update([cid for cid in MESSAGES_BY_CONVERSATION if cid.startswith("D")])

    if not selected_ids:
        selected_ids = {cid for cid in MESSAGES_BY_CONVERSATION if cid.startswith("C")}

    cutoff: datetime | None = None
    if req.since_last_n_days is not None:
        cutoff = started - timedelta(days=req.since_last_n_days)
    if req.since_last_n_hours is not None:
        hour_cutoff = started - timedelta(hours=req.since_last_n_hours)
        cutoff = max(cutoff, hour_cutoff) if cutoff else hour_cutoff

    collected: list[dict[str, Any]] = []
    for cid in selected_ids:
        for msg in MESSAGES_BY_CONVERSATION.get(cid, []):
            msg_dt = parse_ts(msg["ts"])
            if cutoff and msg_dt < cutoff:
                continue
            collected.append({**msg, "conversation_id": cid, "datetime": msg_dt})

    collected.sort(key=lambda m: m["datetime"])

    if req.last_n_messages is not None:
        collected = collected[-req.last_n_messages :]

    ended = utc_now()
    duration_ms = int((ended - started).total_seconds() * 1000)

    mode: Literal["channels", "direct_messages", "mixed"] = "channels"
    has_channels = any(cid.startswith("C") for cid in selected_ids)
    has_dms = any(cid.startswith("D") for cid in selected_ids)
    if has_dms and has_channels:
        mode = "mixed"
    elif has_dms:
        mode = "direct_messages"

    if collected:
        start_time = collected[0]["datetime"]
        end_time = collected[-1]["datetime"]
    else:
        start_time = None
        end_time = None

    summary = format_summary(collected, mode=mode)

    return {
        "ok": True,
        "scope": {
            "channels": sorted([cid for cid in selected_ids if cid.startswith("C")]),
            "direct_message_ids": sorted([cid for cid in selected_ids if cid.startswith("D")]),
            "mode": mode,
        },
        "filters": {
            "last_n_messages": req.last_n_messages,
            "since_last_n_days": req.since_last_n_days,
            "since_last_n_hours": req.since_last_n_hours,
        },
        "messages_processed": len(collected),
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
        "duration_ms": duration_ms,
        "summary": summary,
    }


@app.api_route("/api/slack/{method_path:path}", methods=["GET", "POST"])
def generic_slack_method(method_path: str, payload: GenericSlackRequest | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "warning": "Using generic dummy response. Add a specific route for richer behavior.",
        "method": method_path,
        "params": payload.params if payload else {},
        "ts": utc_now().isoformat(),
    }


@app.get("/ui", response_class=HTMLResponse)
def api_explorer() -> str:
    return """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Slack Mock API Explorer</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; line-height: 1.4; }
    h1 { margin-bottom: 8px; }
    .small { color: #666; margin-bottom: 18px; }
    .grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 14px; }
    .meta { font-size: 12px; color: #444; margin-bottom: 8px; }
    textarea { width: 100%; min-height: 120px; font-family: monospace; }
    button { margin-top: 8px; padding: 8px 12px; cursor: pointer; }
    pre { background: #0e1116; color: #e5e7eb; padding: 10px; border-radius: 8px; overflow: auto; }
    .badge { display:inline-block; font-size:12px; padding:2px 8px; border-radius:12px; background:#eef; margin-right:8px; }
  </style>
</head>
<body>
  <h1>Slack Mock API Explorer</h1>
  <div class=\"small\">Swagger-like API catalog for local bot hook testing. You can edit parameters and execute each API directly.</div>
  <p><a href=\"/docs\" target=\"_blank\">Open OpenAPI Swagger UI</a></p>
  <div id=\"api-grid\" class=\"grid\"></div>

  <script>
    async function loadCatalog() {
      const res = await fetch('/api/catalog');
      const data = await res.json();
      const root = document.getElementById('api-grid');
      for (const api of data.apis) {
        const card = document.createElement('div');
        card.className = 'card';

        const bodyId = `body-${api.name}`;
        const outId = `out-${api.name}`;
        card.innerHTML = `
          <div><span class=\"badge\">${api.method}</span><strong>${api.path}</strong></div>
          <div class=\"meta\">${api.description}</div>
          <div>Parameters (editable JSON):</div>
          <textarea id=\"${bodyId}\">${JSON.stringify(api.default_params, null, 2)}</textarea>
          <button onclick=\"executeApi('${api.method}', '${api.path}', '${bodyId}', '${outId}')\">Execute</button>
          <pre id=\"${outId}\">(response will appear here)</pre>
        `;
        root.appendChild(card);
      }
    }

    async function executeApi(method, path, bodyId, outId) {
      const output = document.getElementById(outId);
      const raw = document.getElementById(bodyId).value;
      let params = {};
      try {
        params = raw ? JSON.parse(raw) : {};
      } catch (e) {
        output.textContent = `Invalid JSON: ${e.message}`;
        return;
      }

      try {
        let response;
        if (method === 'GET') {
          const url = new URL(path, window.location.origin);
          Object.entries(params || {}).forEach(([k,v]) => {
            if (v !== null && v !== undefined) {
              url.searchParams.set(k, String(v));
            }
          });
          response = await fetch(url.toString());
        } else {
          response = await fetch(path, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(params || {})
          });
        }
        const data = await response.json();
        output.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        output.textContent = `Request failed: ${err.message}`;
      }
    }

    loadCatalog();
  </script>
</body>
</html>
"""


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "ok": True,
        "message": "Slack API dummy host is running.",
        "ui": "/ui",
        "swagger": "/docs",
        "openapi": "/openapi.json",
    }
