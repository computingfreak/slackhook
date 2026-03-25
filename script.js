const MESSAGES_BY_CONVERSATION = {
  C123: [
    { ts: '1710000000.000100', user: 'U111', text: 'Incident started around 7 AM. Investigating root cause.' },
    { ts: '1710001800.000200', user: 'U222', text: 'DB failover done. Error rates are falling quickly.' },
    { ts: '1710003600.000300', user: 'U111', text: 'All services stable now. Monitoring for 30 minutes.' }
  ],
  C456: [
    { ts: '1710200000.000100', user: 'U333', text: 'Sprint planning at 2 PM. Share blockers before then.' },
    { ts: '1710201200.000200', user: 'U111', text: 'Blocked on design review, should clear by tomorrow.' }
  ],
  'D111-U222': [
    { ts: '1710300000.000100', user: 'U111', text: 'Can you review the bot webhook change?' },
    { ts: '1710300900.000200', user: 'U222', text: 'Reviewed. Looks good, only one minor comment.' }
  ]
};

const API_CATALOG = [
  { name: 'auth.test', method: 'GET', path: '/api/slack/auth/test', description: 'Validate auth context.', default_params: {} },
  { name: 'users.info', method: 'POST', path: '/api/slack/users/info', description: 'Return a dummy user profile.', default_params: { user: 'U111' } },
  { name: 'conversations.list', method: 'GET', path: '/api/slack/conversations/list', description: 'List channels and DMs.', default_params: { exclude_archived: true, limit: 100 } },
  { name: 'conversations.history', method: 'POST', path: '/api/slack/conversations/history', description: 'Return message history for a channel.', default_params: { channel: 'C123', limit: 20 } },
  { name: 'conversations.replies', method: 'POST', path: '/api/slack/conversations/replies', description: 'Return dummy thread replies.', default_params: { channel: 'C123', ts: '1710000000.000100', limit: 10 } },
  { name: 'chat.postMessage', method: 'POST', path: '/api/slack/chat/postMessage', description: 'Echo posted message with generated timestamp.', default_params: { channel: 'C123', text: 'Hello from mock' } },
  { name: 'search.messages', method: 'POST', path: '/api/slack/search/messages', description: 'Search dummy messages by substring.', default_params: { query: 'incident', count: 20 } },
  { name: 'files.list', method: 'GET', path: '/api/slack/files/list', description: 'Return static file metadata.', default_params: { channel: 'C123', count: 20 } },
  {
    name: 'messages.summarize',
    method: 'POST',
    path: '/api/slack/messages/summarize',
    description: 'Summarize channels and/or DMs with last N message/day/hour filters.',
    default_params: {
      channels: ['C123', 'C456'],
      include_direct_messages: true,
      last_n_messages: 10,
      since_last_n_days: 7,
      since_last_n_hours: null
    }
  }
];

function nowIso() {
  return new Date().toISOString();
}

function parseTs(ts) {
  return new Date(Number.parseFloat(ts) * 1000);
}

function summarizeTexts(messages, mode) {
  if (!messages.length) return 'No messages were found in the selected window.';
  return `Summary (${mode}): ${messages.slice(0, 8).map((m) => m.text).join('; ').slice(0, 500)}`;
}

function toInt(value, fallback) {
  const n = Number.parseInt(value, 10);
  return Number.isNaN(n) ? fallback : n;
}

function routeSlackApi(method, path, params = {}) {
  if (method === 'GET' && path === '/api/slack/auth/test') {
    return { ok: true, url: window.location.origin, team: 'Dummy Team', user: 'dummy-bot', team_id: 'TMOCK', user_id: 'UBOT' };
  }

  if (method === 'POST' && path === '/api/slack/users/info') {
    const user = params.user || 'U111';
    return {
      ok: true,
      user: {
        id: user,
        name: `mock-${String(user).toLowerCase()}`,
        real_name: 'Mock User',
        is_bot: false,
        tz: 'UTC',
        profile: { email: `${String(user).toLowerCase()}@example.com`, title: 'Engineer' }
      }
    };
  }

  if (method === 'GET' && path === '/api/slack/conversations/list') {
    const limit = toInt(params.limit, 100);
    const channels = Object.keys(MESSAGES_BY_CONVERSATION).slice(0, limit).map((id) => {
      const isDm = id.startsWith('D');
      return { id, name: `conversation-${id.toLowerCase()}`, is_archived: false, is_im: isDm, is_channel: !isDm };
    });
    return { ok: true, exclude_archived: params.exclude_archived ?? true, channels };
  }

  if (method === 'POST' && path === '/api/slack/conversations/history') {
    const channel = params.channel || 'C123';
    const limit = toInt(params.limit, 20);
    const messages = (MESSAGES_BY_CONVERSATION[channel] || []).slice(-limit);
    return { ok: true, channel, messages, has_more: false };
  }

  if (method === 'POST' && path === '/api/slack/conversations/replies') {
    const channel = params.channel || 'C123';
    const ts = params.ts || '1710000000.000100';
    const limit = toInt(params.limit, 10);
    const base = (MESSAGES_BY_CONVERSATION[channel] || []).slice(0, 1);
    const replies = Array.from({ length: limit }).map((_, i) => ({
      type: 'message',
      user: 'U444',
      text: `Reply ${i + 1} in thread ${ts}`,
      ts: `1710005000.000${i}`,
      thread_ts: ts
    }));
    return { ok: true, channel, messages: [...base, ...replies], has_more: false };
  }

  if (method === 'POST' && path === '/api/slack/chat/postMessage') {
    const channel = params.channel || 'C123';
    const text = params.text || '';
    const ts = `${(Date.now() / 1000).toFixed(6)}`;
    MESSAGES_BY_CONVERSATION[channel] ||= [];
    MESSAGES_BY_CONVERSATION[channel].push({ ts, user: 'UBOT', text });
    return { ok: true, channel, ts, message: { text, bot_id: 'BMOCK', type: 'message', ts } };
  }

  if (method === 'POST' && path === '/api/slack/search/messages') {
    const query = String(params.query || '').toLowerCase();
    const count = toInt(params.count, 20);
    const matches = [];
    Object.entries(MESSAGES_BY_CONVERSATION).forEach(([channel, messages]) => {
      messages.forEach((msg) => {
        if (String(msg.text).toLowerCase().includes(query)) {
          matches.push({ channel: { id: channel }, text: msg.text, ts: msg.ts });
        }
      });
    });
    return { ok: true, messages: { matches: matches.slice(0, count), total: matches.length } };
  }

  if (method === 'GET' && path === '/api/slack/files/list') {
    const channel = params.channel || 'C123';
    const count = Math.min(toInt(params.count, 20), 30);
    const files = Array.from({ length: count }).map((_, i) => ({
      id: `F${String(i).padStart(6, '0')}`,
      name: `report-${i}.txt`,
      title: 'Dummy artifact',
      mimetype: 'text/plain',
      url_private: `https://mock.slack.local/files/F${String(i).padStart(6, '0')}`,
      channels: [channel]
    }));
    return { ok: true, files };
  }

  if (method === 'POST' && path === '/api/slack/messages/summarize') {
    const startedAt = new Date();
    let selected = new Set(Array.isArray(params.channels) ? params.channels : []);
    if (params.include_direct_messages) {
      Object.keys(MESSAGES_BY_CONVERSATION).filter((id) => id.startsWith('D')).forEach((id) => selected.add(id));
    }
    if (!selected.size) {
      selected = new Set(Object.keys(MESSAGES_BY_CONVERSATION).filter((id) => id.startsWith('C')));
    }

    const now = new Date();
    let cutoff = null;
    if (params.since_last_n_days != null) {
      cutoff = new Date(now.getTime() - toInt(params.since_last_n_days, 0) * 24 * 60 * 60 * 1000);
    }
    if (params.since_last_n_hours != null) {
      const hourCutoff = new Date(now.getTime() - toInt(params.since_last_n_hours, 0) * 60 * 60 * 1000);
      cutoff = cutoff ? new Date(Math.max(cutoff.getTime(), hourCutoff.getTime())) : hourCutoff;
    }

    const collected = [];
    selected.forEach((id) => {
      (MESSAGES_BY_CONVERSATION[id] || []).forEach((msg) => {
        const dt = parseTs(msg.ts);
        if (cutoff && dt < cutoff) return;
        collected.push({ ...msg, conversation_id: id, datetime: dt });
      });
    });

    collected.sort((a, b) => a.datetime - b.datetime);
    const n = params.last_n_messages == null ? null : toInt(params.last_n_messages, 50);
    const trimmed = n == null ? collected : collected.slice(-n);

    const hasC = [...selected].some((id) => id.startsWith('C'));
    const hasD = [...selected].some((id) => id.startsWith('D'));
    const mode = hasC && hasD ? 'mixed' : hasD ? 'direct_messages' : 'channels';

    const endedAt = new Date();
    const start_time = trimmed.length ? trimmed[0].datetime.toISOString() : null;
    const end_time = trimmed.length ? trimmed[trimmed.length - 1].datetime.toISOString() : null;

    return {
      ok: true,
      scope: {
        channels: [...selected].filter((id) => id.startsWith('C')).sort(),
        direct_message_ids: [...selected].filter((id) => id.startsWith('D')).sort(),
        mode
      },
      filters: {
        last_n_messages: params.last_n_messages ?? 50,
        since_last_n_days: params.since_last_n_days ?? null,
        since_last_n_hours: params.since_last_n_hours ?? null
      },
      messages_processed: trimmed.length,
      start_time,
      end_time,
      duration_ms: endedAt.getTime() - startedAt.getTime(),
      summary: summarizeTexts(trimmed, mode)
    };
  }

  if (path.startsWith('/api/slack/')) {
    return {
      ok: true,
      warning: 'Using generic dummy response. Add explicit route for richer behavior.',
      method: path.replace('/api/slack/', ''),
      params,
      ts: nowIso()
    };
  }

  return { ok: false, error: 'Unknown path', path, method };
}

async function handleRequest({ method, path, params }) {
  const response = routeSlackApi(String(method || 'GET').toUpperCase(), path, params || {});
  return Promise.resolve(response);
}

window.slackMockApi = {
  catalog: API_CATALOG,
  handleRequest,
  routeSlackApi
};

function createApiCard(api) {
  const card = document.createElement('article');
  card.className = 'api-card';
  const payloadId = `payload-${api.name}`;
  const outId = `out-${api.name}`;

  card.innerHTML = `
    <div><span class="badge">${api.method}</span><strong>${api.path}</strong></div>
    <div class="meta">${api.description}</div>
    <label>Parameters (JSON)</label>
    <textarea id="${payloadId}">${JSON.stringify(api.default_params, null, 2)}</textarea>
    <button data-method="${api.method}" data-path="${api.path}" data-payload-id="${payloadId}" data-out-id="${outId}">Execute</button>
    <pre id="${outId}">(response appears here)</pre>
  `;

  const button = card.querySelector('button');
  button.addEventListener('click', async () => {
    const payloadRaw = document.getElementById(payloadId).value;
    const output = document.getElementById(outId);
    try {
      const params = payloadRaw ? JSON.parse(payloadRaw) : {};
      const res = await handleRequest({ method: api.method, path: api.path, params });
      output.textContent = JSON.stringify(res, null, 2);
    } catch (error) {
      output.textContent = `Invalid request JSON: ${error.message}`;
    }
  });

  return card;
}

function initExplorer() {
  const grid = document.getElementById('api-grid');
  API_CATALOG.forEach((api) => grid.appendChild(createApiCard(api)));

  document.getElementById('generic-run').addEventListener('click', async () => {
    const method = document.getElementById('generic-http-method').value;
    const path = document.getElementById('generic-path').value;
    const raw = document.getElementById('generic-body').value;
    const output = document.getElementById('generic-output');

    try {
      const params = raw ? JSON.parse(raw) : {};
      const res = await handleRequest({ method, path, params });
      output.textContent = JSON.stringify(res, null, 2);
    } catch (error) {
      output.textContent = `Invalid request JSON: ${error.message}`;
    }
  });
}

initExplorer();
