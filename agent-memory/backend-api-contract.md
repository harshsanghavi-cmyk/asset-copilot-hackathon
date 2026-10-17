# Backend integration contract v1

Implementation-owned seam, 17 Oct 2026. Python FastAPI at `127.0.0.1:8000`.
UI self-hosted CopilotKit TypeScript companion is frontend-owned; it forwards
`X-User-Id` and `X-Session-Id` to Python. No model key enters the browser.

## Replaceable retrieval

`backend.retrieval.contracts.RetrievalProvider` is injected into the Q&A service.
Its public synchronous methods are `catalog()`, `query(plan,context,authority)`,
`evidence(handle,context)` and `search(terms,context,**filters)`. Composition root
alone imports the current candidate factory; chains/memory never inspect SQL,
FTS, source directory layouts or ingestion tables. Provider replacement tests use
an independent stub implementing this Protocol.

Context includes schema_version `1.0`, dataset_namespace, user_id, thread_id,
run_id, reference_date, timezone, dataset_revision and knowledge_revision.
AuthoritySnapshot contains accepted `corrections`, `rule_overrides` and attributed
`shared_claims`. Correction entries expose inspection_id/record_id, field,
value/effective_value, original_value, author_user_id, reason, validity, status and
revision. Rule entries expose rule_id, well_type, equipment_kind, threshold/value,
lookback_months, validity, author_user_id, status and revision. Shared claims never
change fields just by appearing here. Provider returns schema_version `1.0`,
result_set_id, columns, rows, evidence refs, coverage, source/knowledge revisions,
bounds/time basis, warnings and lineage handles. Backend normalizes to UI schema
without deriving numbers itself. Missing/unsupported fields produce errors.

## Identity and sessions

This is the challenge's demo user selector, not production authentication.
Normal routes require `X-User-Id`; IDs are checked against provider user catalog.
`X-Session-Id` must agree with path/body threadId. Every session read/write is
owner-scoped, including history, search, resume and answer/evidence lookup.

- `GET /api/health`: public readiness/provider/model configuration flags, no secrets.
- `GET /api/users`: `{users:[{user_id,name,role,team_id}]}`.
- `GET /api/sessions?q=&limit=50&offset=0`: `{sessions:[{id,title,user_id,created_at,updated_at,message_count}],total}`.
- `POST /api/sessions`: `{id?:UUID,title?:string}`; returns session, status201.
- `GET /api/sessions/{id}`: session object.
- `PATCH /api/sessions/{id}`: `{title:string}`; returns session.
- `DELETE /api/sessions/{id}`: deletes this conversation/history, status204;
  private durable memories/shared audit records are separate from session deletion.
- `GET /api/sessions/{id}/messages`: `{messages:[{id,role,content,created_at,envelope?,status,run_id,run_status?}],session}`.
  User rows expose canonical run_status so reconnects can show an active run;
  history polling never starts generation.
- `GET /api/answers/{answer_id}`: owner-authorized envelope.
- `GET /api/evidence/{evidence_id}?answer_id=`: authorized source detail associated
  with that user's answer, not an arbitrary filesystem read.

Session title initially uses the first user text (bounded); the planner may return
a concise title in that same existing call. Explicit user rename wins.

## AG-UI and answer envelope

`POST /api/agent` accepts AG-UI RunAgentInput (`threadId`, `runId`, `messages`,
optional `forwardedProps`) or a compact `{message,session_id,run_id}`. The latest
user text is the current request; client-supplied old history is not trusted.
Server emits SSE standard AG-UI events: RUN_STARTED, safe progress/tool lifecycle,
TEXT_MESSAGE_START/CONTENT/END, TOOL_CALL_START/ARGS/END for `answer_dashboard` with
`{"envelope":...}`, TOOL_CALL_RESULT, then RUN_FINISHED or RUN_ERROR. Never stream
reasoning, private prompt context, raw internal tools or partial factual JSON.

Envelope matches `frontend/src/lib/contracts.ts`: schema_version `1.0`, answer_id,
thread_id,user_id,dataset_namespace,dataset_revision,knowledge_revision,
reference_date,window?,narrative,blocks[],results{},evidence{},warnings[],sample=false.
Block `{id,type,status|table|line|bar|heatmap|map|diagram,title,result_set_id,
evidence_ids,encoding,span?}` uses existing result columns and source IDs only.
Result `{result_set_id,dataset_revision,knowledge_revision,columns:[{key,label,
unit?}],rows:[record],evidence_ids,coverage?}`. Evidence `{id,title,source_kind,
source_id,excerpt?,path?,author?,source_time?}`. Numbers are provider-owned.
Structured model ViewPlan contains narrative, blocks/result/column/source handles;
server resolves actual results and validates every reference before publication.

## Budget/model policy

Gemma `gemma-4-26b-a4b-it`, Google AI Studio through the official
`ChatGoogleGenerativeAI.ainvoke` adapter with explicit `vertexai=False`; ignored
root `.env` is read server-side. Health reports `model_adapter` so the running
transport is inspectable. Current generation does not use a custom HTTP request
body or REST `extra_body`; prompted JSON is validated locally. One persistent
process-safe limiter enforces at least2.2s
between starts,30RPM global across foreground/background. The coordinator raised
the initial20 live generation-attempt allowance first to100 and then150 total, including errors.
Counting calls are cached and logged
separately. API errors remain explicit; no fixture substitutes for live answers.
Content caps:2K long-term TOTAL private/shared +1K conversation/summary +2K fresh
evidence. Persona/tool schemas,current request,output/framing are separately counted.
The current packing implementation counts serialized UTF-8 bytes and enforces
2000/1000/2000 byte ceilings, deliberately underfilling the token budget; it is
not exact Gemma tokenizer accounting or a proven optimal allocation. Omitted
cards/rows/spans are flagged, full results remain server-side, and shared facts
already in long-term context are not duplicated into fresh evidence. Model
request usage is recorded separately. `ASSET_LIVE_ENABLED=0` pauses generation
without disabling data/session/admin routes; health exposes
`model_generation_enabled` and `data_ready` separately. Enabled health proves
configuration/data liveness, not model success. Runtime inference is Google AI
Studio only; historical failed requests remain in the audit ledger.

The workflow uses the actual LangGraph functional entrypoint/tasks and persistent
SQLite checkpoints, with synchronous stage receipts. Application run ownership
is checked before any resume. Deleted conversations retain minimal run-ID
tombstones so an old checkpoint cannot be reopened by reusing an ID. Failed runs
return `RUN_ERROR` and persist a synthetic assistant error row in session history,
including `status:error`, `error_code` and `error_message`. Retries using the
original client message ID resume the canonical run without duplicating the user
message. There is one bounded schema repair, not an unbounded retry loop.

## Explicit local admin diagnostics

Admin memory routes additionally require `ASSET_ADMIN_ENABLED=1` and
`X-Admin-Token` matching server `ASSET_ADMIN_TOKEN`. Neither is inferred from
X-User-Id or a user's dataset role. Disabled/unconfigured mode fails closed.
Tokens remain server/local operator configuration, never in bundles or reports.
This is a local diagnostic capability, not a production authentication system.

- `GET /api/admin/memory?scope=private|shared&user_id=&kind=&q=&limit=25&offset=0`
  returns `{items:[{id,scope,owner_user_id,author_user_id,kind,subject_ids,preview,
  created_at,updated_at,valid_from,valid_to,status,knowledge_revision}],total}`.
- `GET /api/admin/memory/changes?limit=&offset=` returns paginated audit events.
- `GET /api/admin/memory/status?user_id=` returns capsule versions, token estimates,
  pending deltas and summary/compaction jobs; no prompts/keys.
- `GET /api/admin/memory/{id}` returns the canonical memory/provenance/version
  detail. Bounded previews, no complete-table browser dumps or arbitrary SQL.
- Retrieval owner router mounts at `/api/retrieval`; its admin operations must
  use the same injected admin capability guard, while regular evidence is scoped.

This contract may receive additive fields during integration; breaking changes
require a schema_version bump and coordinated UI/provider update.

## Latest execution additions

Structured asset_progress carries stage_id,stage,status,timestamp,attempt_id,
canonical run_id,tool_name,operation and optional result_count. Quota waits add
queue_state,retry_at,reason and priority. History user.stages retains bounded
real events; no cached stage creates fictional execution events. RUN_ERROR
metadata includes an actual retry_after_seconds when supplied by the provider.

The shared queue enforces16000 input tokens/minute using cached SDK counts plus
64 framing tokens, reconciled measured usage, foreground priority and provider
cooldowns. Context-content packing remains the disclosed conservative byte
profile; these are different accounting tasks.

Generation.status=partial means actual verified provider results/panels exist but
no validated explanation is available. verified_tool_data,explanation_error_code
and retry_after describe that state. RUN_FINISHED.result.status and tool result
status are partial, not ready. Failed maker checkpoints remain resumable; same-run
concurrent requests attach instead of scheduling duplicate generation.

Application-combined typed pages use app:pages evidence handles, whose authorized
source details include original page result IDs. Counts/maps never use preview
row counts as complete population totals.
