# Shared integration contracts — planning proposal

These contracts reconcile the three tracks. They are design guidance, not API
implementations. Final dependency versions follow a compatibility spike.

## Trusted request context

The application supplies dataset_namespace, user_id, thread_id, exchange_id,
request_id, reference_date, timezone, normalized date bounds and the minimum
knowledge_revision the request must observe. The model does not select identity,
permission scope or the author of a correction. A user picker is sufficient for
the hackathon demo; it is not production authentication.

## EvidenceRef

A stable evidence_id resolves through a source registry to source_kind, source_id,
dataset_revision, safe relative path, content_hash, record ID/JSON pointer or
Markdown section and span. Include source time/author where present. Derived
claims additionally reference their formula, rule, corrections and effective
values. The viewer exposes scoped evidence, not arbitrary filesystem paths.

Shared correction receipts disclose the domain change and author. They do not
grant access to the private conversation that produced the correction.

## ResultSet

A typed domain tool returns result_set_id, tool/version, normalized arguments,
dataset_revision, knowledge_revision, date window with explicit closure/time basis,
columns and units, stable row IDs, immutable values, evidence references, formula
and rule references, coverage, warnings and an evidence manifest.

Coverage counts matching, evaluated, unknown and excluded records with a stated
unit. Pagination limits displayed rows, never the population used for an aggregate.
A large aggregate's complete evidence manifest may be fetched on demand; its
headline provenance must still resolve to source records and rules.

## ViewPlan and AnswerEnvelope

Gemma proposes a ViewPlan: narrative/claim references plus an ordered blocks[]
array. Each block selects a trusted component, result_set_id, allowed column
encodings, title and bounded layout. It must not re-author numeric data arrays,
user IDs, source URLs, arbitrary React/HTML or chart JavaScript.

The server assembles AnswerEnvelope from validated plans and tool results:
schema_version, run/message/exchange IDs, dataset namespace and revisions,
reference date/window, narrative claims, blocks[], result references, evidence,
warnings and complete/partial state. Python and TypeScript share one generated
or checked discriminated-union schema. Fact claims resolve values from result
references; inference and suggested checks remain explicitly distinguished.

One answer may contain a status card, table, line/bar chart, heatmap, map and
relationship diagram in a useful combination. Four or five components must work
within one message. Simple answers may have no panels. Requested visual types
remain explicit, including unavailable states where evidence is insufficient.

## Streaming boundary

Use the selected standard UI protocol for run/text/state/tool lifecycle. Its
transport does not replace the domain AnswerEnvelope schema. Agent reasoning,
private prompt context and raw internal tools are never user-facing answer text.
Only complete validated factual blocks enter the renderer; partial model JSON can
at most describe a loading skeleton. Replay/cancel/user switches recheck scope.

One answer pins one (dataset_revision, knowledge_revision). If a write arrives
mid-query, recompute affected results before current-state publication, or label
the full older snapshot and offer refresh. Never mix revision values across text
and charts. Later requests require the committed revision.

## Shared knowledge writes

Explicit correction -> validate target/field/value/scope/validity -> compare expected
revision -> append durable change with idempotency key -> increment knowledge
revision -> invalidate dependent results -> return save receipt. Preserve original
and previous effective values, author, reason (or not supplied), timestamp and
source IDs. Do not say saved before commit or retry a write through text repair.

Ordinary claims/notes are attributed records, not automatic field corrections.
Conflicting formal corrections need explicit supersession or resolution; a clear
first correction can apply while a contradictory ordinary note remains visible.
Well-type rules apply only to matching subjects/time and keep user attribution.

## Private continuity

Persist raw exchanges and exact entity-set receipts by user/thread. Long-term
facts stay durable by user across threads. Load the user's bounded static-fact
capsule every turn; retrieve relevant archive detail when needed. Per-thread
summaries carry source coverage/watermarks and are replaceable projections.
The ten-exchange periodic counter and token-overflow trigger are independent.

## Validation boundary

Validation checks schema, IDs, columns, scope, revision, units, formulas and cited
values. It cannot prove unrestricted prose is true merely because a citation
exists. Use deterministic headline facts and bounded narrative grounded in exact
results; reject unsupported assertions. Allow one formatting repair per stage,
a bounded contextual replan if useful, then a transparent partial/failure state.

## Ownership for implementation after plan review

- Data worker: import/source registry, normalized facts, effective views, FTS and
  extraction, typed query tools and evidence/result contracts.
- Agent/memory worker: prompts/chains, bounded model planning/composition, private
  memory, shared knowledge transaction interface and compaction jobs.
- UI worker: protocol adapter, typed renderers, answer assembly integration,
  citations/source viewer, multi-panel layout and lifecycle state.
- Coordinator: contract reconciliation, integration review, independent acceptance
  evidence, release packaging and submission preparation.

## Deeper-review additions: shared semantic knowledge

Shared knowledge includes remembered plans, operational observations, field/team
context and well-type guidance, not just numeric corrections. Store each assertion
with subject, applicability, visibility, author, source, valid time, status and
knowledge revision. In the hackathon all users can read shared domain facts;
team ownership is not an invented access-control restriction. Applicability and
visibility are independent dimensions.

A clear asset-domain remember request commits a minimal shared assertion with a
receipt before acknowledgement. A personal preference stays private. A private
conversation reference is never published as shared knowledge. Ambiguous subject
or scope gets a focused clarification. Automatic extracted facts retain candidate
status unless supported; repeated confidence does not promote a claim to truth.

The read gateway composes always-loaded scoped summaries and relevant shared/private
retrieval. It does not copy a shared fact into every user profile. Exact correction
and rule application remains mandatory in domain queries even when a semantic
retriever would rank the correction below its cutoff. A cached memory capsule is
a revisioned projection, not another source of authoritative truth.

Implementation framework and authority storage are separate choices: a LangGraph
workflow can call the same application-owned ledger. Branch experiments compare
those complete compositions while holding domain behavior constant.
