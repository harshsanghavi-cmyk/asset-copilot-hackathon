# Backend

Run from the repository root with the original dataset acquired as documented
under `dataset/` and a server-only `GOOGLE_API_KEY` in the ignored root `.env`:

```sh
uv sync --project backend
ASSET_GENERATION_LIMIT=150 uv run --project backend python -m backend
```

API: `http://127.0.0.1:8000`. `/api/health` reports data/model configuration;
it does not prove a successful generation. `/api/agent` emits AG-UI SSE and
requires a known `X-User-Id` and an owner-scoped conversation. Select users through
`/api/users`. The frontend-owned CopilotKit companion proxies these requests.

Only Google AI Studio Gemma `gemma-4-31b-it` is enabled, through the official
`ChatGoogleGenerativeAI.ainvoke` adapter with `vertexai=False`. The persistent request
ledger shares the30RPM/2.2s limit across serving and background work. The150-call
setting is the current authorized total integration allowance, including failed
attempts. Do not run live evaluation concurrently without coordinating ownership.
`ASSET_LIVE_ENABLED=0` pauses generation while preserving data/session/admin APIs.

```sh
uv run --project backend pytest backend/tests -q
```

Tests use explicit fixed proposals or mocked HTTP; actual dataset tests rebuild a
temporary index. They never call a model or claim live model quality. For current
results and limitations see [backend-implementation.md](../agent-memory/backend-implementation.md)
and [backend-api-contract.md](../agent-memory/backend-api-contract.md).

Persistent files live under ignored `runtime/`. Conversation identities are a
demo selector, not production authentication. The local launcher creates an
operator-only admin capability file; no credential belongs in a browser bundle.
Retrieval is injected through a public Protocol and remains replaceable.
