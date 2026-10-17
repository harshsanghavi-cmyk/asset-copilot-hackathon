# Asset Intelligence Copilot — implementation roadmap

17 Oct 2026. **All three main implementation tracks are authorized and in progress.** This document consolidates decisions and acceptance work; it does not add another plan-approval gate or claim a finished copilot. Retrieval remains provisional until the user can inspect its storage, enrichment and query/evidence behavior. Publishing, deployment and submission are outside the current authorization.

## Decisions

| Vertical | Selected composition | Rationale and evidence boundary |
|---|---|---|
| Enterprise generative UI | React 19.2.4 + TypeScript/Vite; CopilotKit 1.79.1 self-hosted TypeScript runtime; AG-UI client 1.0.2/Python events; Ant Design 6.6.6 + ECharts 6.1.0 via echarts-for-react 3.0.6; compact reference JSON ViewPlan | Actual rich fixture chat, five-panel interactions, wide/mobile rendering and evidence controls work. Direct AG-UI is a rich functional tie; CopilotKit supplies the selected conversational shell. Main live integration remains in progress. |
| Q&A / memory | Python≥3.11, FastAPI/Uvicorn, Pydantic v2; application-owned SQLite private/shared records and structured authority; bounded staged workflow; Gemma planner/proposer then composer | Authority and audience policy stay outside model memory. Explicit journal and LangGraph tied 53/53 synthetic state checks. Bounded LangGraph is the prior reviewed proposal; final engine reconciliation with the active owner is pending, not inferred from a manifest. |
| Retrieval / ingestion | Injected versioned RetrievalProvider; **provisional** SQLite complete effective-record calculations + direct report/manual/SOP joins + deterministic section/span extraction + FTS5/BM25 | Nine frozen exact checks and full-scope linked-report checks passed. Lexical recall@5 was0.6667 on24 hand-authored questions, so discovery remains imperfect. Viewer review and replacement-provider tests precede acceptance. |
| All runtime model work | Only gemma-4-31b-it, temporarily Google AI Studio OpenAI-compatible endpoint; server-side credentials; one persistent shared maximum 30 RPM limiter | Plain final text and clean JSON smoke requests succeeded. Native generation500 and OpenRouter429 remain dated observations, not quality/provider rankings. No alternative embedding, reranker or fallback model is eligible. |

UI pins come from tested experiments/current manifest, not proof the full application is compatible. Backend ranges/lock and schema versions remain owner-controlled. Latest AGENTS.md, [model policy](agent-memory/model-policy.md), [backend API v1](agent-memory/backend-api-contract.md) and operating contracts supersede historical planning-only, larger-budget and MiniLM recommendations.

### UI comparison and component mixing

Retain CopilotKit + AntD/ECharts + reference JSON: conversational shell, broad enterprise controls and specialist analytics are complementary. Keep a small configurable domain catalog; a library's entire export list need not enter every prompt. OpenUI and json-render both passed real independently registered/reordered panel, layout, shared selection, evidence, scope/revision and production-build checks with the same seven-entry custom catalog. They are compatible optional composition layers; the same components look alike. The earlier A2UI trial wrapped one dashboard component and did not prove independent arbitrary panel composition. assistant-ui remains an untested alternative shell, not another catalog to stack onto CopilotKit.

| Static Gemma countTokens representation | Catalog/instruction input | Equivalent fixed output | Interpretation |
|---|---:|---:|---|
| Compact reference JSON |158|161| Hand-compressed task schema |
| OpenUI Lang |818|148|13 fewer output tokens, about8.1%; input not equally optimized |
| JSON-wrapped OpenUI |845|173| Wrapper removes this fixture's saving and retains a second grammar |
| json-render snapshot |4254|242| Default input describes JSONL patches; **not a fair optimized snapshot total** |

Exactly12 counting requests and zero generation requests were used. Only the fixed outputs form a controlled like-for-like encoding comparison. Inputs are unequally optimized; no live generation reliability, latency, billing or optimized total-efficiency winner follows. Do not transfer a GPT-tokenizer vendor saving to Gemma. Inventoried native catalogs contain OpenUI General82/Chat84 and json-render shadcn36 entries including helpers; only seven custom entries were exercised. Neither native catalog supplies this entire evidence/map/heatmap system automatically. Reconsider json-render if a general JSON component tree becomes necessary, or OpenUI if a broad DSL catalog earns measured benefit; neither is justified by13 fixture tokens alone. [Report](agent-memory/ui-library-comparison.md), [screenshots](experiments/01-generative-ui/library-comparison/README.md).

### Ties and untested alternatives

Explicit journal and actual LangGraph/SqliteSaver each passed 53/53 identical fixed-proposal storage/scope/restart checks. Live extraction, summary fidelity and answer quality were not tested. gbrain's fresh PGLite projection passed 17/17 exact engine checks; semantic recall, compression, remember/context_pack and remote authorization were not established. **Do not require gbrain initially**: retain atomic canonical facts and bounded projections with exact/scoped lexical retrieval. This is an adoption judgment, not a measured memory-quality victory. [Memory results](agent-memory/memory-experiments.md), [loading decision](agent-memory/long-term-memory-loading-decision.md).

Historical MiniLM/RRF improved recall@5 from0.6667 to0.8333 with four improving questions and20 ties; exact checks tied. That candidate is **ineligible**. Preserve its evidence without using its gain to endorse untested Gemma expansion. FTS is lexical, not vector semantics. [Retrieval experiment](agent-memory/retrieval-experiments.md), [current operating contract](agent-memory/retrieval-operating-contract.md).

## Runtime boundaries and owners

Browser → frontend-owned self-hosted CopilotKit runtime → Python `/api/agent` on8000. Standard AG-UI lifecycle/text/tool events carry validated `answer_dashboard` envelopes. Partial factual JSON, reasoning and internal prompt/tool dumps never render as answers. Fixture mode stays visibly marked and cannot replace a failed live response.

Four model capabilities: `read_context`, `query_records`, `read_evidence`, `write_knowledge`. They expose bounded reference resolution, general filter/group/metric record queries, linked/lexical evidence and typed knowledge writes. They expose neither arbitrary SQL nor one hardcoded tool per scenario. Trusted code stamps identity, author, namespace, dates and revisions, and reauthorizes handles on source-view, cache, cursor, replay and resume.

`RetrievalProvider.catalog/query/evidence/search` is injected. Only the composition root selects the factory. Q&A/memory/chat must not import candidate SQL tables, FTS internals or ingestion layout. Provider consumes accepted corrections/rules and attributed shared claims in AuthoritySnapshot; returns versioned ResultSet/EvidenceRef, units, bounds, formulas, lineage and complete/evaluated/unknown coverage. A different independent provider stub must pass the same consumer contract before replaceability is claimed.

Gemma proposes intent, memory drafts and a compact ViewPlan; server registries own numeric values, sources and AnswerEnvelope assembly. All narrative/panels use one dataset/knowledge snapshot. Read the committed shared head even on another user's first request; materialize short consistent reads before network calls and recheck at publication. Recompute affected results or label the whole answer historical. Formatting repair cannot change facts or replay a write.

| Owner | Boundary |
|---|---|
| Q&A/memory worker | Backend application/API, chains, prompts, output_parsers, authority/private/shared memory, scoped admin memory endpoints |
| Retrieval worker | backend/ingestion, backend/retrieval, data/query/source inspection, frontend/src/retrieval-viewer |
| UI worker | Remaining frontend, self-hosted TS companion, session/sidebar/search/automatic titles, theme/animation, admin.html routing/theme |
| Coordinator | Contract reconciliation, independent integrated acceptance, final PNG placement and submission-pack review |

Use `/home/harshsanghavi/Desktop/copilot-revive` only as the authorized design/reference source and project skills as relevant guidance; no wholesale code/personal-state import. No new sessions are needed. Motion respects reduced-motion preferences.

## Memory and context

Persist raw exchanges and exact discussed-entity receipts under trusted user/thread ownership across sessions. Shared operational plans/claims are stored once with audience, subject, source, author, assertion/conflict status, validity and revision. They cross challenge teams; private preferences and “the three wells we discussed” do not. Formal field corrections/scoped user rules are separate authority, retaining original/previous/effective values, reason, time, scope and supersession. Ordinary disagreement cannot acquire that authority automatically.

Check useful memory proposals **every message**, normally within the planner call. Clear explicit saves/corrections/rules commit before acknowledgment and before response calculation. Ambiguous proposals stay pending. Accepted fact changes refresh manifests/capsules deterministically; optional Gemma rewriting runs only when needed. Exact canonical shared lookup works before an index/rewrite finishes. A dated plan's end is not proof of completed work or production restart.

Short-term compaction is a different trigger: at completed exchanges 10/20 summarize1–7/1–17, preserving newest three durably; their loaded text still fits its slot. Failed/interrupted requests, chunks and retries do not increment the counter. Earlier overflow compaction does not reset periodic timing. Source coverage, exact receipts and compare-and-swap versions preserve recovery. [Memory operating contract](agent-memory/memory-operating-contract.md).

| User content category | Cap | Proposed initial suballocation, not measured optimal |
|---|---:|---|
| Long-term private + shared TOTAL |2000| Always private capsule/index600 + shared header/index200; selected exact private400 + shared800 |
| Short-term summary + historical dialogue |1000| Summary400 + recent dialogue500 + handles100 |
| Fresh retrieved context |2000| Result summary600 + rule excerpts650 + report spans550 + coverage/manifest200 |
| **Content total** |**5000**| Full durable originals/results/chart arrays stay server-side |

Follow-up reads replace optional content within the category, never append hidden batches. Do not relabel old dialogue or SOP prose as overhead/long-term facts. Pool subslots only within each category. Separately count/disclose persona, stage/tool schemas, current request, framing and output reserve. Exact compatible-message Gemma counting remains an acceptance task; conservative estimates must be labeled. If indispensable evidence/conflicts cannot fit, narrow, clarify or return supported partial results. Advertised model capacity does not permit a larger user content cap.

Keep prompt prose once in `backend/prompts/*.md`, referenced by YAML with top-level `input:` and `prompt:`. Orchestration belongs in `backend/chains/`; validation/one bounded formatting repair in `backend/output_parsers/`. Logical prompts: persona/core; planner+memory proposer; answer+ViewPlan; optional evidence-gap/span assistance; short-term summarizer; optional capsule rewriting. These are responsibilities, not separate mandatory agents/calls. Normal flow is one planner + one composer; at most one evidence assistance and one formatting repair, **four foreground completion attempts including retries**. Two evidence rounds/eight read calls are proposed initial bounds. Background work shares30RPM with lower priority; no per-report model loop.

## Phased tasks and acceptance

Phases1–4 are authorized parallel work behind the agreed interfaces. Existing source files do not prove the exit gates passed. Phase5 is integrated acceptance; phase6 prepares concrete submission artifacts without publication.

| Phase / dependencies | Owner and deliverable | Exit evidence |
|---|---|---|
|0. Contracts/configuration | All owners: schema1.0, user/session/time/revision, provider injection, four tools, prompt registry, persistent limiter, token telemetry; reconcile workflow engine | Python/TS fixture agreement, spoofed scope/refs rejected, alternate provider stub works; count method visible; no browser key |
|1. Sources/effective tools; depends0 | Retrieval: reproducible pinned dataset acquisition/license; dynamic discovery/keys/FKs/hash/spans; repeat import/conflicts; correction/rule views; full-population status/downtime/cost/spill/RCA/deadline algebra | Counts reconcile; unknown type/report/rule explicit; custom filenames work; no runtime expected-answer lookup; frozen nine fixtures rerun against new code; raw data preserved |
|2. Memory/workflow; depends0, provider stub enables parallelism | Backend: sessions, planner/proposer, idempotent authority/shared claims/private facts/receipts, bounded stages, summary/capsule jobs, strict parser, explicit provider errors | Shared A→B remember before rebuild, private negative cases,10/20/overflow/restart/duplicate/stale-job/conflict checks; no false save; budget/model policy enforced |
|3. Enterprise UI; depends0, fixtures enable parallelism | UI: polished chat/session sidebar/search/title/user switch; wide4–5 panels; filters/sort/shared selection; charts/location display; source/data drawer; partial/error/loading/reconnect/reduced-motion | Real runtime/protocol + valid envelope, atomic panel/narrative refresh, keyboard/screen-reader/mobile checks; display filters/export distinct from aggregate recomputation |
|4. Inspection; depends1/2/3 contracts | Retrieval+UI+backend: normal evidence viewer; separate admin memory/retrieval page with source→storage, schemas/counts, enrichment/effective values, query tables/filters/trace, selected/omitted evidence and bounded row previews | Enabled mode + server capability required; role/user picker does not grant admin; no arbitrary SQL, complete-table dump or secrets; user can review provisional retrieval strategy |
|5. Integrated acceptance; depends1–4 | Coordinator+owners: all 18 scenarios, same-format unseen root, live Gemma plans/composition, evidence/privacy/revision/budget/error tests | Separate factual/evidence/visual scores, actual traces/usage/errors; no mock/scaffold pass; no known private leak or mixed revision; limitations explicit |
|6. Submission preparation; depends real phase5 results | Coordinator:≤2-page write-up,≤5-minute own-voice video, final-results table, public-ready repository/license/acquisition review, optionalZIP≤150MB | Concrete artifacts accurately describe results/failures; sanitized/reproducible package. No repository publication, deployment or portal submission without separate user instruction |

The model smoke test is only a configuration checkpoint. An endpoint returning JSON, a page rendering or a small fixture suite passing does not complete phase5. [API contract](agent-memory/backend-api-contract.md) requires explicit local-admin enablement plus server-validated `X-Admin-Token`; this is diagnostics, not production authentication. Normal answer evidence stays separately user-scoped.

### Official 18-scenario gate

[Source scenarios](dataset/03-evaluation-queries.md) are evaluation fixtures, never runtime evidence. Run Q1–Q10 independently on original data; Q11–Q18 preserve only their stated dependencies in isolated fixtures. Score facts, source/rule evidence and visual choice separately.

| Scenario | Acceptance |
|---|---|
|Q1| Latest inspection/inspector/method,3.2°C delta, attributed planned shutdown/stale status; status card |
|Q2| Four specified Northeast8 wells, correct deltas/known or unknown causes; table; no invented reason |
|Q3|13 observations23Jul–15Oct, ambient/wellhead line series,8/15Oct down markers; no invented missed reading |
|Q4| Six spills/15.1bbl; seven raw detections with formal false-positive exclusion; table and correction evidence |
|Q5|21 observed down days in2025;51.6°C absolute reading still down at8.5°C delta; cited concise result |
|Q6| Explicit16Jun–16Oct bounds,49/42/42days and required wells; tie disclosed, bar chart |
|Q7| Four correct real spill pins/coordinates/volumes; geographic-map request honored. Current coordinate-pin/no-basemap view is a baseline, not a validated geographic-map pass |
|Q8| Entire area×month matrix including zeros;35/43/37/26 row totals; heatmap from effective spills |
|Q9| Four supplied-rule breaches/USD5000 open fine; report-only containment and overdue closure/response; pending actions/met annual test distinguished |
|Q10| Complete eligible-spill/report enumeration;7.1h/8.1h late containments with spans; job/report hours not substituted |
|Q11| Michael's new chat resolves his Q6 exact entity receipt; recorded costs25794/46942/5176USD with applicable estimate basis |
|Q12|41.0°C correction retains original24.0/author/reason;21.1°C delta produces oil; contrary note visible; repeated Q2 has three wells |
|Q13|5.4bbl retains4.5; reportable class, possible missing written notice, old moderate report superseded;23Nov verification deadline and containment breach |
|Q14| Baseline three wells; T350-only2-repair pump-jack rule adds WELL-0120, excludes T200 WELL-0102; user attribution |
|Q15| Jessica/Laura see both committed corrections immediately; all classification/deadlines/narrative/panels share revision |
|Q16| Jake's shared plan reaches Michael; Jessica never inherits Michael's private three-well history |
|Q17| Contrary ordinary claims preserved/unconfirmed and compared with observations; no silent measurement overwrite |
|Q18| Both ordinary notes and repair cited; crude detection stands without formal correction; conflict visible |

Also test unique/ambiguous/absent SOP antecedents across sessions/users; prescribed versus recorded versus assessed procedure; exact/over cap and large requests; unsupported SQL/metrics; missing reports/uncertain extraction; duplicate/conflicting imports; type/inheritance/date boundaries; pending/expired plans; correction races/index lag; session search/delete/resume ownership; admin isolation. Retain sanitized raw prompts/results/source/provider receipts, versions, count method, actual calls/tokens/latency/cost when returned, and failures. Experiments establish no universal app speed/cost target.

## Data and navigation

Measured source: 200 wells,39567 inspections,5665 jobs,1509 reports,90 regulator events,141 notes. Structural links are coherent. Material hazards:27 opposed shutdown accounts associated by asset/date,30 potentially compatible delays,21 stale statuses,56 formal spill exclusions,9 interim estimates and6 late-but-closed verifications. Preserve attribution/time/uncertainty; do not call all of them corrupt data. [Audit](agent-memory/data-audit.md), [inventory](agent-memory/data-audit-inventory.json).

[Current status](experiments/STATUS.md), [pack index](experiments/README.md), [decision evidence](agent-memory/final-decisions.md). Current explanatory PNGs: [10 overview](diagrams/10-architecture-and-evidence-for-review.png), [11 prompts](diagrams/11-prompts-and-agent-flow.png), [12 retrieval](diagrams/12-contextual-retrieval-operating-flow.png), [13 memory timing](diagrams/13-memory-save-and-summary-flow.png), [14 selective loading](diagrams/14-long-term-compression-and-retrieval.png). They are proposals, not acceptance receipts; diagrams/ stays flat PNG-only. Submission starting points: [write-up](submission/write-up-template.md), [video](submission/video-outline.md), [results](submission/final-results-template.csv), [portal checklist](submission/portal-checklist.md).
