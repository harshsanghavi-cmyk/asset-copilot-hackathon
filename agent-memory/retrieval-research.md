# Ingestion, context and retrieval — research proposal

Track 3 · researched 17 Oct 2026 · **Planning and separately authorized isolated experiments; no main-app implementation.** Initial dataset measurements below were made with read-only Python; vendor capabilities are documented, and architecture/performance recommendations are inferences until tested. Later user authorization permits bounded branch experiments under `agent-memory/experiment-policy.md`; actual comparisons and any model use are recorded separately in `agent-memory/retrieval-experiments.md`. Dataset revision: `b8de8c9bd68f40334e5d06922126169e4f3bf3ca` (`docs/dataset-source.json`).

## Current decision — exclusive Gemma policy

Recommend **SQLite exact facts + shared correction/rule authority + direct source joins + deterministic section FTS5/BM25**. Parameterized tools calculate over every matching effective row; joins resolve linked reports and applicable manuals/SOPs; local parsing preserves spans, conflicts and coverage. Every copilot model operation uses **Gemma 4 31B Instruct only**. No MiniLM, alternative embedding model or separate model-based reranker is eligible. Historical experiment measurements remain unchanged in `retrieval-experiments.md`; their semantic candidate is **historical/ineligible**, not the selected integration.

The temporarily authorized provider route is Google's OpenAI-compatible base URL `https://generativelanguage.googleapis.com/v1beta/openai/`, model `gemma-4-31b-it`, as recorded in `agent-memory/model-policy.md`. Existing `google-gemma-verification.json` records successful generation and clean locally parsed JSON; native `generateContent` returned HTTP 500 in that verification. This is a smoke test, **not** universal schema enforcement, tool reliability or retrieval/answer accuracy. All copilot layers share the user-provided maximum **30 requests/minute**; retain local schema/evidence validation and bounded repair. No new calls were made for this policy update.

Optional **Gemma-only query expansion or ambiguous-prose extraction** remains proposed and **unmeasured** until a matched comparison earns adoption. Expansion can add lexical terms while preserving trusted scope, IDs/date filters and exact calculation authority; extraction must cite locally verified spans and explicit unknowns. Neither is a claim of semantic-vector retrieval, nor permission to process all reports through the model. Known lexical fallback misses remain acceptance work, addressed first through direct links, deterministic filters and neighboring-section expansion rather than assumed model improvement.

Postgres with native text search remains a deployment alternative for concurrent writes/larger hosting; DuckDB with FTS remains a batch-analytics alternative. Earlier pgvector/VSS/other-embedding comparisons below are documented historical alternatives whose model-dependent paths are currently ineligible. Libraries are adapters; prevent implicit alternate-model defaults. Main-app implementation still awaits final-plan review.

## Stable seams for peer tracks

Use `agent-memory/integration-contracts.md` as the canonical cross-track seam; this report provides data-specific detail beneath it, aligned with `agent-memory/memory-research.md` and `agent-memory/ui-research.md`: `EvidenceRef`, `ResultSet`, `dataset_revision`, `knowledge_revision`. Trusted request context supplies `dataset_namespace`, active user, reference date, timezone and normalized bounds; model arguments cannot choose identity or correction author. A request pins one dataset/knowledge snapshot for all narration and panels. Gemma selects a `ViewPlan`; the server assembles the authoritative `AnswerEnvelope` from validated result/evidence references.

`EvidenceRef` identifies a source revision and stable record/section/span, including `evidence_id`, `source_kind`, `source_id`, safe relative `path`, `content_hash`, optional JSONL `line` + JSON pointer or Markdown section + byte range, original/effective distinction, correction IDs, rule IDs, author and event time when present. A UI viewer resolves IDs through the server; raw filesystem paths are not arbitrary file-read arguments. Shared correction evidence exposes the relevant domain change, never the surrounding private chat.

`ResultSet` includes `result_set_id`, tool/version, normalized args, dataset/knowledge revisions, `reference_date`, `time_basis`, bounds with closure semantics, typed `columns` with units, immutable `rows` with stable row IDs, per-row evidence references, formula/rule references, coverage, warnings and evidence-manifest reference. Coverage reports the unit being counted, matching/evaluated/unknown/excluded counts, report-link/extraction coverage where applicable, and `complete | partial | unknown`. Pagination limits presentation, never the aggregation input. Each visual consumes this same result-set ID and columns; the model must not retype numeric arrays.

`commit_knowledge_change` belongs to memory's shared ledger transaction: validate typed target/field/value/scope/reason/validity, compare `expected_revision`, use an idempotency key, append without destroying originals, increment `knowledge_revision`, publish invalidation and return durable receipt. Retrieval must honor `minimum_knowledge_revision` on the next question. A mid-query correction causes recomputation or explicit historical-snapshot labeling, never mixed revisions.

Reconciled with `agent-memory/architecture-review.md`: every request reads the **server's committed head**, including another user's first request; a client watermark alone is insufficient. Materialize tool results in short consistent reads at revision R, close transactions before network model calls, and compare head while storing the publication receipt. Refresh affected data/narrative or publish the whole answer as historical if head advanced. Shared prose indexes expose a watermark; retrieve newer relevant subject claims directly from canonical storage while an index lags, and revalidate every ranked source ID's current visibility/supersession before prompt loading. Exact authority never depends on index completion. Audience, subject and authority are separate fields even when all challenge users share the same organization visibility.

## Measured sample shape

| Source | Actual count | Notes |
|---|---:|---|
| Wells | 200 | 119 T200; 81 T350 |
| Geographic areas / teams / people | 4 / 4 / 15 | Areas have 50 wells each; production ownership differs from maintenance/HSE roles |
| Inspections | 39,567 | Identical field sets across this sample; derive production, do not trust recorded status |
| Maintenance | 5,665 | 4,156 scheduled; 1,509 corrective |
| Linked Markdown repair reports | 1,509 | Every corrective row has a report link; 342–813 whitespace-delimited words per report |
| Regulatory events | 90 | Inspection foreign keys and protocol references |
| Context notes | 141 | 82 operator notes, 56 formal corrections, 3 operator feedback |
| Fleet manuals/SOPs | 5 | Both well manuals and all three SOPs read completely |

Measurements are inventory/structural analysis, not manual interpretation of every report or successful ingestion implementation. Full join, prose-extraction and rule details follow in this report.

## Diagram artifacts

All editable diagrams and the enhancement brief live in `agent-memory/diagram-sources/retrieval/`; only final PNGs belong in the **flat** `diagrams/` directory, with no subfolders, per the latest user direction. The coordinator alone renders/enhances PNGs. These are **proposed architectures**, never implementation claims.

## Storage choices and existing libraries

| Candidate | Verified mechanism | Project judgment and trigger |
|---|---|---|
| SQLite + exact authority/direct joins + FTS5/BM25, current recommendation | FTS5 supplies token/phrase/Boolean search, BM25 ranking and snippets; its build availability must be checked | Small complete relational dataset and low shared-write rate suit SQLite. Deterministic lexical retrieval is eligible; no alternate embedding/reranking model. Optional Gemma assistance is unmeasured. |
| Postgres + native text search; historical pgvector extension | GIN is a preferred text-search index; pgvector supports exact search, HNSW/IVFFlat and text/vector fusion | Native text search remains eligible for a larger deployment. The earlier vector path requires an embedding model and is not part of the Gemma-only recommendation. No Postgres runtime benchmark was run. |
| DuckDB + FTS; historical VSS extension | Analytical SQL, BM25 extension and an experimental VSS extension | Batch-analytics alternative; FTS refresh/writer ownership need design. Other-model vector paths are currently ineligible. No DuckDB runtime benchmark was run. |

Capability sources: [SQLite FTS5](https://sqlite.org/fts5.html), [Postgres text indexes](https://www.postgresql.org/docs/current/textsearch-indexes.html), [pgvector official repository](https://github.com/pgvector/pgvector), [DuckDB FTS](https://duckdb.org/docs/current/core_extensions/full_text_search), [DuckDB VSS](https://duckdb.org/docs/current/core_extensions/vss). No three-way runtime benchmark was run. Python's local SQLite reports version **3.45.1** with `ENABLE_FTS5=1`; this checks the available interpreter, not a future deployment artifact.

SQLite WAL allows readers alongside a writer but only one writer at a time and requires local-host access, so use one owned write path, short atomic transactions and an intentional busy/retry policy. Do not place its live WAL database on shared network storage. Pin a read transaction for a whole answer's tool batch. [SQLite WAL](https://sqlite.org/wal.html)

Postgres' default Read Committed can expose a different committed state to successive statements; use a consistent Repeatable Read transaction or a versioned projection for a multi-tool answer. More capable infrastructure does not remove the need for the dataset/knowledge revision contract. [Postgres isolation](https://www.postgresql.org/docs/current/transaction-iso.html)

Historical capability note for the currently ineligible vector path: pgvector's approximate indexes can lose filtered matches because filtering follows index scanning; iterative scans improve retrieval but do not establish complete recall. Hybrid rank fusion selects passages, never determines a fleet count; vector deployments also need model/version/dimension tracking. This is documented background, not an instruction to add embeddings. [pgvector filtering and hybrid search](https://github.com/pgvector/pgvector#filtering)

DuckDB's FTS index does not automatically track changes; rebuild it after document updates or use immutable indexed revisions. VSS persistent HNSW currently requires an experimental flag and documents crash-recovery risk; do not select that feature as the source of truth. The ordinary embedded concurrency model has a single read-write process, with multiple writer threads inside it. Current docs also describe beta remote Quack and DuckLake/catalog alternatives, which materially expand this project's scope. [FTS update caveat](https://duckdb.org/docs/current/core_extensions/full_text_search), [VSS persistence](https://duckdb.org/docs/current/core_extensions/vss#persistence), [DuckDB concurrency](https://duckdb.org/docs/current/connect/concurrency)

| Orchestration/retrieval library | Useful verified feature | Adoption boundary |
|---|---|---|
| Plain DB adapter + project tools | Application controls SQL, spans, transactions and output contracts | Recommended; more domain code to own, fewer hidden extraction/synthesis calls. SQLite is a storage choice, not a backend language mandate. |
| LlamaIndex | Ingestion transformations, cached node/transform hashes, document IDs/hashes, optional vector store and text-to-SQL engines | Optional reader/retriever adapter; cache is not authority. Disable embedding/default-provider stages. Any optional model extraction must use Gemma 4 31B only and earn adoption through testing. |
| Haystack | Composable retrievers; in-memory BM25 supports metadata filters and top-k | Useful comparative lexical baseline without embedding calls. A temporary DocumentStore is not a durable fact database, correction service or exact aggregation engine. |

LlamaIndex's ingestion guide permits a node-only pipeline without embeddings; its text-to-SQL guide warns about executing arbitrary SQL. Prefer application allowlisted typed queries over model SQL; an optional read-only exploratory SQL mode would require a separate safety/coverage design. Neither library supplies this challenge's effective-correction semantics. [LlamaIndex ingestion](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/), [text-to-SQL guide](https://developers.llamaindex.ai/python/examples/index_structs/struct_indices/sqlindexdemo/), [Haystack BM25](https://docs.haystack.deepset.ai/docs/inmemorybm25retriever)

Disable implicit embedding, title-extraction, reranking and generation defaults in any library adapter. Only Gemma 4 31B may make model-based decisions; the selected chat endpoint is not an embedding endpoint. Historical MiniLM results are recorded separately in `retrieval-experiments.md` and must not cause that dependency/index to enter the selected runtime. Gemma-only assistance requires its own measured acceptance evidence.

## Relational model, joins and ownership

Normalize one complete record table per JSONL kind, preserving raw JSON and source location. Suggested relations: `import_batch`, `source_document`, `source_record`, `team`, `person`, `area`, `well_type`, `asset`, `equipment`, `inspection_raw`, `maintenance_raw`, `regulatory_event_raw`, `context_note_raw`, `report_section`, `report_fact`, `rule_definition`, `rule_inheritance`, `knowledge_event`, `effective_field`, and immutable query/evidence manifests. These are proposed logical contracts, not migrations. The editable ER diagram is `04-entities-cardinalities.mmd`.

- Fleet area `team_id` and metadata `team_id` describe production ownership. Person/team joins identify inspector, technician, note author, lead and in-charge person separately; do not equate the repair crew with asset owner. Expose display names for people, areas and teams, well IDs for wells.
- An area has many assets; an asset has one declared type, area, production team and in-charge person, plus an equipment list. Read both metadata and area membership and flag disagreements rather than silently moving a well. Equipment kind is the maintenance join dimension for RCA; equipment IDs are not interchangeable with kinds.
- An asset has many inspections, maintenance rows, regulator events and notes. Select the latest actual inspection by `inspected_at` with a stable secondary ID order; use metadata `last_inspection` as an integrity check. If same-time observations disagree, surface ambiguity rather than claiming the ID proves chronology.
- An inspection can trigger zero or many maintenance records and regulatory events; both references are optional. Join on declared IDs **and validate asset consistency**. Do not join by date proximity when an explicit reference exists. A note's `inspection_id` is a formal target where supplied, not a general assumption about all notes.
- Each sample corrective maintenance row points to one report; scheduled rows do not. Model it as optional report association and document identity, retaining source versions. Always resolve `maintenance.report_file` under that asset's allowed directory. Do not synthesize a filename from `maintenance_id` or infer a path from glob rank.
- Notes/rules/corrections preserve author, recorded time, validity and subject. A user may discuss another team's asset; this challenge's picker is not an asset authorization matrix. Do not invent team-based access restrictions from ownership fields. Private chat authorization is a separate application boundary owned by the memory track.
- Avoid join multiplication: aggregate maintenance costs per maintenance ID before joining many inspections or regulator events. Aggregate spill metrics per effective inspection ID before expanding multiple repair/report spans. Fines belong to regulator event IDs, not every joined evidence row.

Complete cardinality and mismatch auditing belongs to `agent-memory/data-audit.md`; this track's inventory agrees with `docs/initial-findings.txt`. The data-audit report should refine import checks without forcing unsupported one-to-one assumptions.

## Report structure, extraction and provenance

Measured headings across all 1,509 reports: `What happened`, `Root cause`, `Safety and permits`, `Testing and return to service`, `Compliance check`, `Notes and recommendations` each appear 1,509 times. `Work done` and `Parts and cost` appear 1,500 times; **nine** reports use `Work done so far` and `Parts and cost (estimate; work in progress)`. `Spill clean-up and waste` appears **616** times; `Waste` appears **323** times. Unknown headings in test data must remain searchable rather than be dropped.

There are 1,507 filenames shaped like a maintenance ID, plus two custom descriptive filenames for WELL-0001. Its June report is linked as `MNT-0001-june-2026-flowline-spill.md`, while its content identifies MNT-0001-029. This proves why filename synthesis fails. Reports contain both detailed narrative and compact compliance tables; retrieve both for corroboration and contradictions.

A read-only exploratory extraction found numeric containment delay in **616** reports: the plain narrative pattern matched 615 reports, and the `Contained ... hours after discovery` compliance-table pattern matched all 616. The union had no conflicting numeric values under those two patterns; **211** extracted delays exceed 4 hours, with a sample maximum of 9.0 hours. These are measured pattern matches, **not independently annotated extraction accuracy** or a verified total of fleet breaches. One narrative uses Markdown emphasis/line wrapping (`contained about 7 hours after the inspection flight`) and is missed by the narrow narrative pattern; the table recovers it. A broad substring search for `contain` also matches `container` in gearbox work and is not a containment parser.

Read representative ordinary, unfinished, custom-name and query-linked reports. The June report describes delayed containment despite later completed repair; Q10's linked reports contain approximately 7.1 and 8.1-hour delays, and Q13's report contains 6.4 hours plus an old moderate-spill classification. These are source observations, not an evaluation pass. Treat original report classification as what the author said at the time; recompute classification and duties after volume correction.

Proposed extraction stages:

1. Read original UTF-8 bytes and record SHA-256, safe relative path, source revision and import timestamp. Parse headings, paragraphs and table rows with exact source offsets. Store both original bytes and a normalized text projection; normalization must retain an offset map. Whitespace/Markdown normalization can help parsing but cannot change citation coordinates.
2. Parse stable report metadata and protocol rows into attributed **report assertions**. Deterministic field parsers recognize numeric values, units, temporal qualifiers, statuses and negations. Preserve `about`/`estimated`, `in progress`, `action required`, `not applicable` and `not met`; do not coerce all non-`Met` values into a breach. Parse the narrative and table independently; disagreement becomes an extraction conflict.
3. Prioritize typed facts required by questions: containment elapsed hours or timestamp; report-written date; return-to-service statement with actual/planned status; soil sample count/highest TPH; pressure/MOP/hold duration; agency-verification requested/passing/closed; report's spill-class assertion; root-cause prose; RCA recommendation/status; safety checklist assertions; annual integrity-test evidence. Source maintenance costs remain authoritative structured job costs; the report's estimated parts table is separately attributed.
4. Store each candidate as `(subject_id, predicate, value, unit, time_basis, qualifier, status, extractor_id/version, source_hash, span_refs[], verification_state)`. Verification states: `deterministic_span_checked`, `model_candidate`, `source_conflict`, `unresolved`, `human_confirmed`; these indicate process, not probability of truth. An exact quote match proves text support, not that the report is correct. Do not invent a numeric confidence score. Keep multiple conflicting candidates and the originals.
5. For a report linked to a relevant spill, if required facts are still unresolved, optionally send only its relevant complete section(s) and neighboring context to a bounded extraction prompt. Require typed values, exact supporting excerpts, source IDs and an explicit unknown option. Validate every excerpt against original bytes; verify subject, units, negation, time basis and cross-section consistency. A model-only candidate cannot silently make an exact total complete. For decisive ambiguous breaches retain uncertainty or seek confirmation; human review can upgrade evidence state.
6. Cache by `(document_hash, parser_version, extraction_schema_version, optional model_id, prompt_hash)`. Cache summaries separately and never treat them as source truth. Corrections do not rewrite historical reports: invalidate dependent derived classifications/answers while preserving their extraction cache and old assertions. Recompute any derived report assessment using current knowledge revision.

Do deterministic parsing over the **whole corpus** at ingestion; it is inexpensive local text work at this scale and establishes which eligible reports lack facts. LLM extraction is lazy for relevant unresolved documents with a strict per-query batch/call budget and persisted results. A fleet-wide containment question first enumerates every matching spill and report, then evaluates fact coverage for each; it must not silently stop after the first few search hits or model-budget exhaustion. If unresolved evidence remains, return known results plus the unknown count and incomplete status.

For pre-existing context corrections, all 56 sample `correction` notes explicitly deny crude spills. Four measured prose templates cover them (shadow 23, produced water 17, wet soil 15, reference rainwater 1). Use explicit `note_type=correction` + target ID + a supported negated-crude parser to create an audited overlay; free text resembling the templates without formal correction type does not qualify. New ambiguous correction prose goes through validation/review; never extrapolate this sample's false-positive-only pattern into “every correction means false.” Runtime thermal/volume corrections require typed field/value edits.

## Effective values, rules and temporal semantics

Raw records are immutable. A shared `knowledge_event` stores event ID/kind, target record and field or typed rule, original value, replacement value, author, recorded-at, reason, applicability scope, valid-from/to, status, supporting evidence and optional supersedes/conflict links. Original value must be checked against raw/effective state at commit; retain both when correcting an already corrected value. Append retraction/supersession rather than editing history. Do not silently use last-writer-wins for conflicting formal corrections; keep prior accepted value and unresolved candidates visible until precedence is explicitly resolved.

An `effective_inspection` relation resolves eligible accepted corrections at the pinned knowledge revision before any production, spill, deadline, count, ranking or chart operation. Formal spill-detection reversal excludes the event from spill counts/volumes even if raw volume remains recorded; preserve raw volume and correction provenance instead of overwriting it with fictitious zero. A volume-only correction updates volume/classification; it does not invent a report, extra soil samples or regulatory response. Ordinary contextual claims never mutate fields. Source corrections are baseline shared knowledge; runtime scenario overlays are isolated per fixture.

Shared remembered operational knowledge is **broader than corrections**: planned work, confirmed field observations, recurring local operating constraints and attributed handover facts have durable asset/type subjects, validity and source provenance. Store them as shared domain facts/claims and retrieve them for every user's relevant query; keep private preferences and “we discussed” entity relationships in user-scoped memory. A shared fact can explain a thermal observation without changing the measured value. Unconfirmed or contradictory claims remain visible; acceptance of a contextual fact does not grant it authority to rewrite an inspection or a manual. This is part of the compatible relational-store + memory-ledger + retrieval combination, not a rival to it.

Maintain two time axes: the observation/rule validity time and the knowledge recorded/accepted time. `as_of_knowledge_revision` reproduces what was known, while current corrected answers about 2024 can use a subsequently recorded correction targeting that 2024 inspection. Do not exclude such a correction merely because it was authored later than the queried inspection. A finite validity interval is evaluated against its stated subject/event semantics, not automatically against machine-now. Notes describing planned work are evaluated by their interval; a future plan can be retrieved by overlap even before it starts.

Rule registry fields should include rule ID, predicate, threshold/unit/comparator, scope (type/equipment/protocol), effective interval, source document/revision/span and inheritance. T350 overrides T200 production and high-temperature limits and inherits T200 maintenance escalation; an explicit user T350 pump-jack RCA rule overrides only that predicate/type/equipment while retaining attribution and validity. A new unknown type with no usable manual gives unknown production, not the T200 default. Manuals are small: initially encode their typed rules through a reviewed parser/config with source spans and validation rather than trusting model arithmetic. New unsupported manual prose stays retrievable and flagged pending rule confirmation.

All five fleet documents were read. Required rule inventory for future implementation:

| Domain | Applicable rules and decisive boundaries |
|---|---|
| Production | T200 delta >=15 C (§9.3), T350 delta >=20 C (§3); alarms >85 C / >95 C need action within 24 h |
| Shut-in and escalation | Spill area >5%; planned shut-in recorded before work; >=3 corrective repairs of same equipment kind over preceding 12 months before next closure; consecutive downtime >14 days distinct from period totals |
| Spill class | Minor <1 bbl; moderate 1–<5; reportable 5–<25; major >=25 |
| SR-01/02 | Immediate phone duty separate from written notice 24 h / major 2 h; source stopped and contained <=4 h |
| SR-03/04 | <=1.0% TPH, >=4 samples for reportable/major, soil >5% hauled, passing agency verification <=60 days; every real spill recorded |
| RC-01–05 | Inspection interval <=14 days; annual flowline integrity test; report >14 consecutive days down; NOV response <=30 days and closure tracked; flowline maintenance program |
| WS-01–07 | Pre-job meeting; isolation; H2S stop >=10 ppm; hot-work permit and gas <10% LEL; flowline pressure >=1.25×MOP held >=4 h; waste manifest; report <=3 days after completion |

Rule evidence is the fictional dataset manual/SOP, **not external legal material**. The manuals' common failure-mode table suggests checks, not a proven cause for a specific stop. Lubrication, stroke/pressure limits and optional separator procedures remain searchable even when not required by Q1–Q18. Don't claim complete safety/compliance automation from a few implemented predicates.

Explicit temporal contract:

- Scenario reference date is 2026-10-16 unless its stated source/window says otherwise; DOCX's 17 Oct discrepancy is visible. `reference_date` is caller input, never implicit machine clock. Q6's explicit 16 Jun–16 Oct wins.
- Normalize date-based closed calendar windows into `[start_UTC, day_after_end_UTC)`; retain both human bounds and normalized bounds. Dataset timestamps are UTC, so benchmark date comparisons use UTC. User display timezone cannot silently change scenario membership. Date-only validity uses an explicit calendar convention.
- “Latest/right now” means latest observed inspection at or before the requested as-of date. Never synthesize a present reading. A completed-at value beyond reference date is planned/in-progress, not proof of completion.
- Repair costs use `started_at`; inspections/spills use `inspected_at`; notice response uses notice date; discovery drives spill deadlines. Apply exact elapsed hours for hour rules and the defined day addition for 60-/30-day rules. Return calculated deadline and reference time. For “last 90 days” choose and disclose interval closure; acceptance tests check exact boundary records instead of assuming 90 versus 91 inclusive dates are interchangeable.
- Downtime is `7 × count(observed effective non-producing inspections within window)`. No gap interpolation, no maintenance-hours substitution. Consecutive-day escalation is a separate predicate; missing weeks leave uncertainty about continuous downtime even while contributing zero to total downtime.
- Use decimal-safe values: parse JSON decimal tokens without binary rounding; store money as integer cents (or exact decimal), volumes/temperature with declared scale or validated decimal representation. Reject unsupported precision rather than silently round across thresholds. SQLite REAL arithmetic is approximate. [SQLite floating-point guidance](https://sqlite.org/floatingpoint.html)

## Routing, indexes and context packing

The planner selects typed semantic operations and normalized filters; application code executes approved query templates. This generalizes beyond named example questions without permitting arbitrary SQL. A question about an unfamiliar metric returns unsupported/clarification instead of a plausible invented query. Tool arguments can include asset/area/type/equipment/date filters from known catalogs; identity, visibility and snapshot are server-owned.

Suggested relational indexes: inspections `(dataset_namespace, asset_id, inspected_at, inspection_id)`; maintenance `(namespace, asset_id, started_at)` and `(namespace, equipment_kind, maintenance_type, started_at)` plus triggered inspection; regulator `(namespace, related_inspection_id, protocol_id, date)`; assets by area/type; notes/knowledge by target/field/validity/revision; report facts by subject/predicate/hash/version; documents/sections by declared link, source type, rule/protocol and asset. Confirm plans with actual query timings before adding more indexes.

Retrieval order:

1. Exact ID/alias resolution and user-authorized private entity receipts from memory (e.g. “the three wells”). Area/team/person names come from directories; ambiguous names return candidates.
2. Exact complete record filtering/aggregation with the effective-value layer. Retrieve source-member manifests, relevant corrections, unknown rows and rule dependencies.
3. For reports, follow matched maintenance links; for rules, resolve type/protocol and inheritance. Load required sections directly. A compliance search over all spills evaluates all eligible records/reports, independent of lexical similarity.
4. For open prose questions, metadata-filter section FTS/BM25, using a small declared domain synonym set (`not producing`, `down`, `shut in`; `containment`, `contained`, `berm`). SQL IDs stay exact; quote/escape FTS syntax because hyphenated IDs have syntax/tokenization implications. FTS rank selects evidence, not truth; more relevant source text cannot override a formal correction.
5. Deduplicate same source spans, expand adjacent paragraphs or full protocol row/table header, then pack bounded context. Use deterministic lexical ranking and current-source validation. Historical vector improvements do not authorize that now-ineligible model path; optional Gemma-only expansion must be tested separately. Do not silently interpret low recall as “no such event.”

Initial **proposed** evidence budget: <=6,000 tokens of fresh tool/document context, separate from the memory track's 3,000-token memory capsule budget. Reserve slots for exact result summary/schema, applicable rules/inheritance, decisive report spans, corrections/conflicts and coverage. Start open search at 8 sections and expand only if needed; required linked evidence is not removed because a top-k cap is reached. Cache/paginate long member lists server-side, expose lineage by manifest ID and keep all result rows available to visuals. When required evidence exceeds budget, split into a bounded follow-up tool batch or issue a partial answer; do not truncate unknowns/conflicts to fit. Measure actual tokens rather than use characters as a claimed token count.

## Proposed tool catalog and contracts

Tools return a common `ResultSet` envelope and typed errors (`ambiguous_entity`, `unsupported_metric`, `missing_rule`, `partial_import`, `missing_report`, `unresolved_fact`, `stale_revision`, `invalid_arguments`). They must not encode missing data as zero or an empty successful list. Each call records elapsed time, row counts, snapshot and query version for evaluation.

| Tool | Bounded inputs | Deterministic output/evidence |
|---|---|---|
| `resolve_entities` | IDs/names, kinds, explicit area/team hints | Exact IDs/display names or ambiguity, directory evidence |
| `get_well_status` | One or filtered set of assets, as-of date | Latest effective inspection, raw recorded status, thermal delta/threshold, applicable notes, reason evidence and conflicts |
| `get_temperature_series` | Assets, window | Every observed reading, delta/derived production, corrections and threshold refs; no inserted readings |
| `query_spills` | Assets/area, window, optional class/protocol | Effective real spill events, raw/effective volumes and classification, coordinates, relevant correction/protocol IDs |
| `aggregate_metrics` | Allowlisted metric, filters, group_by, window, optional rank/limit | Full-scope downtime/spill counts/volume/cost/fines, dimensional rows including known zero bins, tie policy and membership lineage |
| `get_maintenance_history` | Assets, window, kind/type | Jobs/costs/planned completion, triggered inspection and report link |
| `get_rca_requirements` | Asset scope, equipment kind, as-of | Complete corrective counts in 12-month window, applicable manual/inherited/user threshold, candidate RCA/open-work evidence |
| `get_compliance_assessment` | Assets/spill set, period, as-of, supported protocol list | Computed deadlines/statuses, observed facts, missing evidence, report assertions and stale assertions separately |
| `get_linked_report_facts` | Maintenance/inspection IDs, predicate list | Enumerates all links then exact span-backed facts, extraction state and per-subject coverage |
| `search_documents` | Text, allowed metadata filters, bounded top-k/cursor | Ranked source sections with full identity/spans; explicitly unsuitable for complete counts |
| `get_rule` / `get_evidence` | Validated IDs and snapshot | Full cited rule/record/report span, inheritance and correction provenance; safe viewer links |
| `get_shared_context` | Asset/type, time overlap, kinds | Attributed notes/claims/corrections/conflict state; no private conversation history |

`aggregate_metrics` metric definitions are reusable domain primitives, not Q-number switches. Support allowlisted groupings (asset/area/month/equipment) and deterministic filters. Stable ordering is value then asset ID; **ties are disclosed**. Return `rank_limit`, tie membership and chosen display order instead of pretending a tied top three has one mathematically unique ordering. Heatmaps use discovered area/month domains, zero only for completely covered empty bins and null for unknown coverage.

Illustrative contract shape (proposal; IDs are placeholders, not measured answer data):

```json
{
  "result_set_id": "result:opaque",
  "tool": "aggregate_metrics",
  "tool_version": "v1",
  "dataset_namespace": "field:opaque",
  "dataset_revision": "manifest-sha256",
  "knowledge_revision": 12,
  "reference_date": "2026-10-16",
  "time_basis": "inspection.inspected_at UTC date",
  "bounds": {"start": "2026-06-16", "end": "2026-10-16", "closure": "both"},
  "columns": [{"key": "asset_id", "type": "asset_id"}, {"key": "downtime_days", "type": "integer", "unit": "day"}],
  "rows": [{"row_id": "row:opaque", "asset_id": "WELL-placeholder", "downtime_days": 7, "evidence_refs": ["e:inspection", "e:rule"]}],
  "coverage": {"unit": "inspection", "matching": 1, "evaluated": 1, "unknown": 0, "status": "complete"},
  "formula_id": "observed_nonproducing_count_times_7",
  "rule_refs": ["e:manual", "e:dataset-guide"],
  "lineage_manifest_ref": "lineage:opaque",
  "warnings": []
}
```

Decimally scaled quantities may serialize as decimal strings plus scale/unit metadata; renderer validation must not sum or round them independently. Different coverage units are separate fields, not a misleading sum (e.g. inspections assessed versus linked reports missing). The UI owns its final component schema; retrieval owns factual rows/units/evidence. A broad answer may contain 4–5 components referencing multiple consistent result sets; a single fact can remain concise text.

Compliance statuses should distinguish `met`, `breach_supported`, `possible_breach_missing_record`, `pending_not_due`, `open_action`, `unknown`, `not_applicable`. Absence queries include searched source kinds and import completeness; “no written notice recorded” is different from “no notice was ever filed.” A report saying cleanup was performed is not a passing agency verification. Inspection-based discovery and a repair completion time cannot substitute for containment time.

## General ingestion, duplicate handling and caches

Accept a list of dataset roots with deterministic discovery of `fleet/` and `assets/*/`; never loop over a hardcoded well-number range, area count or manual list. Stage all JSON/JSONL with path/line/raw hash, schema/type/unit validation and an import manifest before publishing a dataset revision. Preserve unknown fields and searchable text. Validate references and report links after loading all roots to permit forward references. Block or mark partial affected queries when essential assets/types/joins fail; publish error counts rather than silently dropping malformed lines.

The same-format test root must augment the sample through this exact path. Namespaces identify one field/evaluation universe; a second unrelated root with colliding IDs must not merge just because IDs look alike. Within a universe: identical entity ID + canonical content hash is idempotent; same ID + different content is a source-version conflict requiring explicit revision semantics, never arrival-order overwrite. Retain every origin/path/version even when physical content is deduplicated. The same report bytes under different paths may share an extraction cache but still need separate subject linkage. Identical notes by different people are distinct authored events. A missing file is a coverage failure, not permission to borrow another well's report.

Use per-file SHA-256 for bytes and an explicitly versioned canonical-record hash for semantically identical JSON; do not deduplicate different IDs simply because boilerplate is identical. Link content hashes to import batches and keep removals/version changes visible. A manual/SOP change creates a new rule/index revision and invalidates applicable derived results; an unknown changed rule stays unconfirmed until parsed/reviewed. FTS indexes original evidence sections; an answer must attach effective corrections and stale-assertion warnings whenever an old report value is retrieved.

Publish raw records, rules, extracted facts and import/index state as one usable dataset revision. `dataset_revision` covers source manifest + loader/rule/parser projection versions; `knowledge_revision` covers accepted shared changes since that baseline. A query key contains those revisions, trusted scope/user when private context is involved, normalized args/bounds, tool version and output/prompt versions as applicable. Safe initial invalidation bumps the whole knowledge revision; selective dependency invalidation can follow after correctness. An extraction cache can survive a volume correction, but a compliance answer cache cannot. Do not reuse old private entity sets across users because the exact calculation cache happens to be shareable.

Dataset acquisition remains a packaging task: `dataset/` is ignored by the outer repository. Future README/bootstrap should clone the pinned repository revision and retain its MIT license, permit separately supplied test roots and verify a manifest. Do not ship only code that silently depends on this local clone.

## Small-model budget and benchmark plan

Default ingestion uses **zero LLM requests**. Calling once per existing report would require at least 1,509 requests before any user query. At the active user-provided shared cap of **30 RPM**, that alone takes over 50 minutes at the theoretical ceiling, before latency, retries or other layers' requests; it is not a measured throughput prediction. Use one global limiter across planning, extraction, memory and answering. The older OpenRouter-specific 20 RPM/daily allowances were historical provider research, not the current direct-Google allowance. [Historical OpenRouter limits source](https://openrouter.ai/docs/api_reference/limits)

Borrow the memory track's bounded plan + compose workflow; do not add per-document summarization/model reranking by default. Proposed Gemma-only ambiguous extraction or query expansion is optional and unmeasured, bounded by call/context budgets and the shared limiter, with one formatting repair only when necessary. If a full-scope question exceeds its evidence budget, preserve partial/unknown coverage or queue explicit remaining work rather than claim completeness. Trace all calls, tokens, cache hits and actual failures. Google's compatible endpoint has existing generation/clean-JSON smoke evidence, while retrieval-specific quality, strict schema enforcement and tool behavior remain unproven by that smoke test.

Benchmark **three independent layers** so a good final answer cannot hide incomplete retrieval:

1. **Ingestion and effective facts:** manifest totals, reference integrity, idempotent reload and new-root union; altered duplicate IDs, new well types, missing report, malformed numeric precision and unknown headings. Use read-only independent expected-value computations as an oracle during implementation, not the copilot's own SQL function. Run original-data Q1–Q10 independently, then isolated Q11–Q18 sequence fixtures.
2. **Evidence and extraction:** annotate a stratified set of ordinary, unusual-name, wrapped/Markdown-emphasized, unfinished, corrected-volume and conflicting reports. Evaluate containment numeric value/unit/qualifier/time basis, negation, exact source span and unknown handling. Count parser coverage separately from precision/recall against annotations; 616 matching reports is not an accuracy metric. Test paraphrased held-out prose where patterns fail and assert partial/unknown rather than false negative. For open search measure recall@k/MRR on manually identified report/SOP sections, including T350→T200 inheritance. Compare direct joins + FTS and optional Haystack BM25; a future matched test may assess Gemma-only expansion/extraction, which is currently unmeasured. Do not introduce an alternate embedding model; exact questions remain independent of top-k.
3. **End-to-end facts/UI/privacy/revisions:** compare exact values, evidence support, appropriate/explicit visual and snapshot consistency separately. Assert Q12 affects Q2/Q15 and all panels; Q13 changes reportability/deadlines while old report assertions remain; Q14 only T350 pump-jack; Q16 private reference absent for Jessica; Q17/Q18 claims remain visible and don't rewrite observations. Add distractor notes, changed names/IDs, equal ranks and date-boundary records.

Measure cold/full/incremental ingestion elapsed time, records/s, extraction coverage, index size, RAM peak; local tool p50/p95 on selective and fleet-wide queries, SQL plans, report evidence recall and source-viewer resolution; total model requests/tokens/cost and response p50/p95; stale-cache rate after correction and mixed-revision failures. **Proposed targets**, to be accepted or revised with measurements: zero incorrect exact totals, zero private leakage, all decisive claims with valid source/rule evidence, complete import before full-scope assertions; local sample queries p95 under 250 ms and first full import under 30 seconds on the actual demo machine. These latency targets are aspirations, not published benchmarks or completion claims.

## Failure modes and acceptance checks

| Failure | Observable acceptance criterion |
|---|---|
| Top-k report retrieval mistaken for a fleet scan | Add a violating spill outside search top-k; complete compliance tool still finds it or reports its unresolved evidence. |
| Missing containment treated as compliant | Remove numeric containment evidence; row becomes unknown and full-scope assessment partial; repair duration never fills the field. |
| Naive heading/regex parser misses custom prose | June custom-name report and nine unfinished variants retain relevant spans; synthetic paraphrase yields explicit unresolved state rather than zero. |
| SQL join multiplication | Two reports/regulator rows for one spill do not double count volume/cost/fines; lineage lists distinct contributing IDs. |
| Correction applied only in chat explanation | Exact status, spill classes, map pins, heatmap totals and next-user tool results all use the same committed effective values/revision. |
| Threshold or scope error | Tests at T200 15/T350 20 C, spill 1/5/25 bbl and containment 4 h; type/equipment/validity override affects only matching targets. |
| False completion from planned end date | Future completion and “work done so far” remain open/planned even if a parts table exists. |
| Source assertion frozen after correction | Old 4.5 bbl moderate/no-reporting prose is visible as historical; current 5.4 bbl classification uses current SOP and correction. |
| Ordinary note treated as correction | Opposing notes remain attributed/conflicted; raw/effective values are unchanged without a formal typed correction. |
| Time-window drift | Pin scenario dates; start/end boundary fixtures, timezone conversion and started-at cost assignment produce deterministic membership. |
| Missing/duplicate held-out records hidden | Reimport unchanged inputs changes no totals; changed duplicate ID is quarantined/conflicted; new valid roots contribute without renamed code. |
| Citation source mismatch | Hash/span/record pointers resolve to imported bytes, preserve raw/effective distinctions, and include applicable manual/SOP plus corrections. |
| Rate limit forces fabricated completion | Model 429/extraction cap returns retriable/partial state with known coverage; no automatic report-wide retry storm. |

## Phased implementation tasks for user review

1. **Contracts and fixture boundaries:** reconcile this report with memory/UI/data-audit, freeze EvidenceRef/ResultSet and revisions, explicit time/bounds/tie policies, source viewer safety and trusted user context. Check selected model compatibility only when implementation/API use is authorized. Define independent expected results without runtime dependence on the scenario answer text.
2. **Reproducible import and rules:** implement multi-root acquisition/import manifest, normalized immutable records, exact-decimal handling, joins and error coverage; read all fleet documents, add reviewed typed rule registry/inheritance and pre-existing correction overlay. Acceptance: measured baseline counts match, second import idempotent, held-out additions work, unsupported rules visible.
3. **Exact domain tools:** status/series/spills/downtime/cost/RCA/heatmap, stable row IDs and lineage, default snapshot transaction. Acceptance: independent Q1–Q8 and Q14 baseline match facts/evidence; altered IDs/types/dates and ties work. No vector dependence.
4. **Reports and compliance:** section store/FTS, deterministic extraction/span validation and coverage, direct report linkage, compliance timelines and absence semantics. Acceptance: Q9/Q10, custom filenames, unfinished reports, missing and ambiguous evidence. Add lazy LLM extraction only after measuring unresolved coverage and model budget.
5. **Shared updates and private integration:** integrate memory ledger atomic commits/idempotency, scoped rules/conflicts, revision invalidation and read-your-write across users; memory supplies resolved private entity IDs only. Acceptance: Q11–Q18 with isolated sequence fixtures, all affected UI result sets refresh together, no cross-user prompt/cache leak.
6. **Evaluate eligible retrieval assistance and deployment upgrades:** retain exact/direct/lexical authority, test optional Gemma-only expansion/extraction against matched fixtures before adoption, and profile real application load. Consider native Postgres text search if deployment/concurrency needs it or DuckDB FTS if batch analytics dominates. No alternate embedding/reranking model may enter integration. Record actual quality/latency/cost/failures; final images/write-up remain coordinator-owned and implementation awaits plan review.

Open decisions: backend language/driver, exact policy for competing formal corrections, whether unknown new manual rules require operator review or a validated extraction workflow, date-only validity closure, tied top-k presentation, and deployment concurrency. None justifies replacing complete facts with vector search or treating model output as source truth.

**Historical measured comparison, preserved but ineligible for integration:** `agent-memory/retrieval-experiments.md` records nine exact checks tying, full-scope linked containment/unknown handling tying, and MiniLM/RRF improving fixed prose macro recall@5 from 0.6667 to 0.8333. The sole OpenRouter synthesis attempt returned HTTP 429; later direct-Google generation/JSON smoke evidence is separate and does not supply a retrieval-answer-quality result. Commits remain `experiment/retrieval-fts` at `5088e7b` and `experiment/retrieval-hybrid` at `4288e54`. The former semantic integration preference is superseded by the current Gemma-only decision above; numerical records and historical alternatives are unchanged.

## Research and verification log

Read `AGENTS.md`, project skill, coordination README, the complete supplied brief extraction, all dataset guides/Q1–Q18, all five fleet manuals/SOPs, source pin and initial findings. Read memory/UI contracts, architecture review, canonical integration seam and coordinator capability notes; deeper integrity audit is assigned independently and will be incorporated by reference. Source capabilities were checked through official documentation/repositories on **17 Oct 2026**. DuckDB stable links redirected to current documentation; source links above identify the pages actually read. The initial research pass accessed no `.env`, private key, configured external memory DB or model API; subsequent expressly authorized experiment access is narrowly accounted for in the experiment report.

Initial local analysis used Python standard library only, in read-only loops; the only SQLite probe in that research pass was an in-memory compile-capability query. Later authorized experiments are isolated in the named experiment worktrees, with dependencies/artifacts and live-call accounting described in `retrieval-experiments.md`; they do not constitute the main app. Current vendor capabilities are verified documentation; proposed budgets/performance/architecture/behavior remain untested except where that experiment report gives actual measurements. The skill is a concise operational guardrail, not proof that a complete ingestion/retrieval service exists.

## Primary research informing the comparison

[BEIR (Thakur et al., 2021)](https://arxiv.org/abs/2104.08663) evaluates heterogeneous retrieval tasks and finds a robust BM25 baseline alongside stronger but more expensive reranking/late-interaction methods. Transferable lesson: retain a competent lexical baseline and test domain transfer; its corpora/results do not predict this synthetic field dataset's winner.

[MTEB (Muennighoff et al., 2023)](https://arxiv.org/abs/2210.07316) finds no embedding method dominates across all evaluated tasks. Transferable lesson: model selection and task-specific retrieval evaluation matter; a sentence-similarity model is a candidate, not a reliability guarantee.

[Reciprocal Rank Fusion (Cormack et al., SIGIR 2009)](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) combines ranked lists with reciprocal rank contributions, avoiding arbitrary raw-score scale mixing. The isolated hybrid comparison fixes `k=60` in advance and uses the same source corpus and filters. The paper's TREC improvements do not establish a local improvement.

[RAG (Lewis et al., 2020)](https://arxiv.org/abs/2005.11401) studies generation conditioned on retrieved non-parametric passages. It supports treating retrieved context as an evidence channel, but does not solve complete numerical aggregation, correction precedence or this application's user isolation. Our exact SQL layer is shared by both candidates rather than using a weak vector-only baseline.

[TAG (Biswal et al., CIDR 2025)](https://arxiv.org/abs/2408.14717) explicitly studies combining database execution with language-model reasoning beyond simple Text2SQL or point retrieval. Its [Berkeley project](https://sky.cs.berkeley.edu/project/tag-bench/) includes comparison, ranking and aggregate questions. This fits the need to combine exact calculations with report interpretation, while its world-knowledge tasks differ from our source-grounded fictional rules; do not let model parametric knowledge replace an applicable manual.

An official [Elastic worked hybrid-search case](https://www.elastic.co/search-labs/blog/elasticsearch-hybrid-search/) demonstrates complementary semantic descriptions and exact constraints in a housing example. Transferable lesson: preserve exact metadata/numerical filtering alongside prose similarity and measure relevance using explicit judgments. This is a vendor-authored demonstration, not independent proof of our dataset's winner, and does not justify adding Elasticsearch to this hackathon.
