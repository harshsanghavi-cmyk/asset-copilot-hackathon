# Final accepted freeze —17 Oct2026,12:39UTC

The user accepted the current results and stopped further tests/fixes. No80–90%
or seven-success claim is made without the coordinator's actual review. All11
outcomes, including partial/error cases, remain available for the requested UI
and document. ROOT owns final deployment/model module, results publication,
Google Doc and authorized repository push.

The final active configuration is the600-well replacement dataset with Jan15
2027 reference date and isolated namespace, using the user-selected
`gemini-3.5-flash-lite` through official ChatGoogleGenerativeAI. Historical Gemma
and200-well results below are archives. This worker froze app files after final
syntax compilation; no new API/model requests or restarts were made.

Latest targeted test receipts:18 API/scope tests passed4.14s;26 API/memory checks
passed5.39s;14 API checks including one bounded grounding repair passed4.67s;
16 memory/private-presentation checks passed2.31s. Explicit fixture checks are
not semantic acceptance of all questions. Remaining known limits include uneven
generated prose/visual coverage, incomplete or failed explanations preserved as
partial data, and local demo identity rather than production authorization.
Suggestions can return honest pending/error states and have no canned fallback.

The latest generic fixes include global-scope precedence over “not just my
area”, status-only context enrichment, exact prior ranked-cohort follow-ups,
source-only validated completion, scoped data/display reuse and strict typed
claim references. Their final targeted runtime outcomes are coordinator-owned;
this report does not silently upgrade old failures to passes.

---

# Latest controlling state —17 Oct2026,12:37UTC

The selected runtime is now **`gemini-3.5-flash-lite` through the official
ChatGoogleGenerativeAI SDK**, following the user's explicit model switch. ROOT
exclusively owns `backend/chains/gemma.py`, its adapter tests and deployment.
Historical Gemma26/31 receipts below are preserved experiments, not the active
model. Native JSON format plus local Pydantic validation is used; a native schema
experiment returned400 and was rolled back, so endpoint schema enforcement is
not claimed.

The active source is the replacement600-well dataset, namespace
`asset-field-test-2027-01-15`, reference date2027-01-15, source revision
`687ade729fe09c4d15c18a94ae102fcbcf8f4868fda89eaeb140ce54a7756716`.
There is no active200-well fallback. The old namespace's histories and facts
remain archived and are not mixed into overlapping new asset IDs.

Current UI APIs include owner-scoped edit/regenerate branches, stable retry,
layout-only reuse, and separate background suggestion generation from only the
question/displayed text/visible conversation. Missing and orphaned suggestion
states are honest errors; explicit POST can retry, historical GET never generates.
The actual retrieval trace is in `agent-memory/RETRIEVAL_FLOW_ACTUAL_RUN.md` and
its experiments reader copy; it marks historical/missing trace evidence.

Latest patches add typed model-stage cache identity, canonical asset aliases,
private focus/ordinal entity receipts, explicit global-versus-personal scope,
actual SDK2K/1K/2K token-slot fitting, full provider summaries, strict nested
claim/value references, one bounded grounding repair, validated source-only
completion, meaningful partial data, and private deterministic sort/currency
projections. Compatible same-author replacement statements are reconciled with
an audit while contradictions remain visible.

The coordinator reports the first four current questions reviewed as good and is
running targeted Q5/Q6/Q7 retests. **No seven-success or80–90% acceptance claim
is made in this worker report before actual semantic review.** All11 original
question outputs, including failures/partials, must remain in the requested
write-up. Code is frozen during that targeted batch; this worker issues no
model requests or restarts.

Latest targeted checks:14 API tests (including one grounding repair),16 memory/
private-projection tests, and source-only completion checks pass. These explicit
fixture tests do not substitute for the real semantic assessment. The remainder
of this document is the earlier implementation history and must be read as such.

---

# Backend implementation handoff

Updated17 Oct2026,10:52UTC. The active runtime is **Gemma4 26B
`gemma-4-26b-a4b-it` through `ChatGoogleGenerativeAI.ainvoke`, Google AI Studio,
`vertexai=False`**. The user explicitly selected26B after31B diagnostics; no
automatic model fallback exists. Historical31B successes,500/503 failures and
failed initial configurations remain in the request ledger and diagnostic reports.

## Concrete current outcome

The exact saved request **“how many assests we have and where show me there
states”** now has a COMPLETE real26B answer for Jake Morales (`U-102`), canonical
run `6008d885-f48d-40dc-9e98-d75184b3a514`, conversation
`4a788ab7-8b5e-4828-83e3-c5f96f973765`.

- Actual provider count:200 assets; complete status/location dataset:200 distinct
  assets with200 valid coordinate pairs,185 effective producing and15 not
  producing. These values were verified read-only against the saved result.
- Actual panels: count card,200-row table and200-point map. The map's value role
  is effective `producing`, with asset IDs and actual lat/lon columns.
- Count and paged-status evidence endpoints both returnedHTTP200. History has
  one user message and one completed assistant message despite retries.
- Planner114 and maker117 are genuine SDK generations; maker117 reused durable
  planner/tool results after maker116 timed out. Earlier partial data and failure
  events remain in the ledger. The final saved envelope is
  `runtime/fleet-request-replay.json`; the database is authoritative.

This demonstrates a working concrete fleet path, not a claim that all18
scenarios or all generated explanations are correct. Q1/Q2 basic automated
checks passed, but independent semantic review found missing operational context,
incorrect prose cardinality and status binding problems. See the evaluation
review/addendum under `experiments/06-evaluation/`. Q5's21-day result recovered
without another generation after a source-bound grounding fix, but its short
explanation remained semantically incomplete. FailedQ12 setup meansQ15 cannot be
called a proven cross-user propagation failure. The separate evaluation worker
owns final scenario scoring; no all18-pass claim is made here.

## Runtime and integration

Run from the repository root:

```sh
uv sync --project backend
ASSET_LIVE_ENABLED=1 ASSET_GENERATION_LIMIT=150 uv run --project backend python -m backend
```

The API is loopback port8000. Health reports active model/adapter/data readiness;
configuration liveness is not a generation-success guarantee. Root ignored.env
is read server-side for `GOOGLE_API_KEY`; secrets never enter browser payloads.
`runtime/` holds persistent memory, workflow checkpoints, source cache, request
ledger and local admin capability. The frontend/CopilotKit companion and retrieval
adapter are separately owned. `backend-api-contract.md` specifies the shared seam.
This is a demo user selector plus explicit local admin capability, not production
authentication or organization authorization.

## Implemented architecture

- Four logical capabilities: scoped context, typed record queries, exact/search
  evidence reads, and validated knowledge writes. Q&A imports the provider
  Protocol, never ingestion tables,SQL or FTS internals. Current SQL/FTS adapter
  remains replaceable. Complete map/status populations are assembled through
  public typed paging, capped at1000 rows, with page lineage; no fleet count comes
  from top-k document search.
- Actual LangGraph tasks/checkpoints are used. Legacy untyped positional receipts
  caused a real cross-stage replay defect during rapid code changes. A typed-v2
  checkpoint namespace and app-owned stage/input-hash cache now prevent wrong
  result interpretation. Prompt and memory revisions are part of cache identity.
  Old ambiguous receipts remain preserved; refreshing them once is intentional.
- Private preferences and episodic entity/event receipts are owner-scoped. Clear
  shared operational facts retain author/source/validity and remain attributed.
  Formal corrections/rules are distinct, deterministic commits with originals,
  idempotency, conflicts and explicit supersession. Authority facts/revision use
  one transaction. Shared changes invalidate context; a change during generation
  marks the entire dashboard historical. Canonical manifests refresh on writes.
- A misleading extraction label cannot publish a private conversational entity
  set. Missing/ambiguous private references require clarification. Scoped lexical
  matching runs only over authorized facts; no embedding model or gbrain runtime
  is used. Small status investigations additionally load actual operating notes
  and maintenance records through the same provider seam; semantic quality of
  the latest context enhancement is not yet claimed as live-validated.
- Periodic summaries schedule after10,20,... completed exchanges and can run
  earlier on overflow. Original messages and exact receipts remain durable.
  Failed background work retains the prior summary; oversized source chunks are
  explicit failures rather than hidden prompt expansion.
- Markdown persona/planner/maker/greeting/summary/repair prose is referenced by
  YAML `input:`/`prompt:`. Required/optional payload keys are centrally checked.
  The initial ignored-input-declaration bug is repaired; YAML was never sent as
  model text. JSON examples validate against application schemas. One bounded
  formatting repair is allowed; local neutral null/visual-descriptor parsing
  avoids needless model calls.
- Narrative/source/value references are checked. Decimal and ISO time formatting
  preserve source values; unsupported numbers remain rejected. Production cards
  bind asset ID,delta and effective producing status; status maps use effective
  producing rather than spill detection. A numeric/source validator does not
  prove general semantic entailment; the scenario reviewer remains necessary.

## Quota, progress and partial results

A single process-safe admission queue covers every SDK purpose. It enforces
30requests/minute and minimum2.2s starts, plus model-specific16000 INPUT tokens/min.
Official SDK countTokens was verified on26B and is cached by model/text hash;
generation reserves the count plus64 framing tokens, then reconciles actual
reported usage. Unavailable counting uses a conservative UTF-8 upper bound.
Foreground requests precede queued evaluation and summary work. Provider429
RetryInfo creates a bounded cooldown; no immediate retry loop or hidden SDK
retries exists. Installed4.4.2 maps max_retries to SDK total attempts, and zero
would restore the SDK default five attempts, so the adapter explicitly uses1.
Current authorized total generation allowance is150. At the10:52 checkpoint,
104 generation starts and17 counting starts were recorded.

Real stage events include attempt/run IDs, timestamps, operation/tool, result
count and actual started/completed/failed states. Quota wait events carry queued/
admitted state,retry_at,reason and priority. History retains bounded stages and
actual terminal errors/retry metadata. Concurrent retries attach to one in-flight
run; disconnecting a stream does not fabricate a failed server run.

If planner/tool results are valid but the maker fails, the API returns explicitly
PARTIAL verified tables/status/map panels and an explanation-failure code. No
sample data or unsupported model narrative is substituted. A subsequent retry
resumes the failed maker and updates the same history row without another user
message or repeated successful planner/tool calls. A complete answer clears stale
terminal error metadata; historical failures remain in stage/request receipts.

The requested content allocation remains2K long-term TOTAL(private+shared),1K
conversation/summary and2K fresh context. **Packing still uses conservative UTF-8
byte ceilings rather than exact Gemma token allocation**, and can substantially
underfill those token allowances. Containers,IDs,bounds and coverage are counted
inside their slots; full rows remain server-side. Static instructions/catalog,
current request and output are separately disclosed. Quota input counting is
exact SDK measurement plus framing headroom; it does not make the content packer's
byte accounting an exact tokenizer measurement. No hidden16K content buffer exists.

## Verification and remaining limits

Earlier full suite:41 passed before the latest quota/coalescing changes. Latest
targeted checks cover14–15 API/quota cases plus SDK/memory checks, including
foreground admission priority, input-window enforcement, cancelled queue budget,
partial-maker resume, stable retry identity, source/number rejection, privacy,
real AG-UI events/history and independent provider replacement. These tests use
explicit mocks/fixed proposals and never claim live model quality. Fresh actual
source tests cover corrections/original retention/cross-user effective values.

Final targeted API/quota/coalescing checks:15 passed in3.47s. The fresh actual
dataset correction/cross-user regression passed1 test in32.21s after the latest
context enhancement. Final safe reload was performed with zero active serving
requests, leaving the26B SDK service running.

Pending at handoff: read-only browser confirmation of the final saved fleet
panels;
full semantic acceptance of Q1–Q18; richer exact token packing; and production
auth/organization policy if deployment moves beyond the local challenge demo.
No frontend or raw dataset was modified by this worker. The only retrieval-owner
edit was the coordinator-transferred active model label.

Primary SDK references:
[LangChain Google integration](https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai),
[Google Gemma API](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api).
