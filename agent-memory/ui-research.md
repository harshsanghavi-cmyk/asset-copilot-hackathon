# Generative UI research — planning proposal

Track 1 · researched 17 Oct 2026 · no app implementation, model calls, dependency installs or service execution. Findings marked **verified** come from official sources or inspected local code; **proposed/inferred** choices require implementation and acceptance checks. Runtime integration is **untested**.

## Recommendation

Use **AG-UI Python events over HTTP/SSE with an application-owned typed multi-block `AnswerEnvelope` and React renderer** for the hackathon. This follows the user's requested AG-UI/CopilotKit/A2UI direction while keeping deployment to a Python API plus React frontend: the AG-UI client SDK connects directly to the Python endpoint. One answer can contain narrative and 4–5 coordinated panels; data values come from immutable `ResultSet` references, not model-created chart arrays. CopilotKit + AG-UI is the preferred richer-shell alternative when its existing chat features justify a self-hosted TypeScript runtime next to Python. A2UI adds portable declarative composition but is not itself an agent transport. A wholly custom SSE protocol remains an explicitly discussed contingency, not the primary plan.

The official `HttpAgent` connects to an AG-UI HTTP endpoint using the client SDK, and official guidance permits custom clients while recommending a full-featured client such as CopilotKit for production. For this hackathon we infer that a focused renderer is viable; it still needs a bounded integration spike and does not claim equivalent production completeness. [HttpAgent reference](https://docs.ag-ui.com/sdk/js/client/http-agent), [client guidance](https://docs.ag-ui.com/quickstart/clients)

**Verified current integration caveat:** CopilotKit's current Python runtime requires a CopilotKit Intelligence project/key; its TypeScript runtime can operate without Intelligence and connect to a Python AG-UI agent. Thus “Python agent supported” does not establish a Python-only, platform-independent CopilotKit runtime. [Official runtime guide](https://docs.copilotkit.ai/backend/copilot-runtime)

There is also a direct CopilotKit-provider path: current docs reserve `selfManagedAgents` for Enterprise Intelligence production use and expose `agents__unsafe_dev_only` for local prototypes. Do not confuse our independent **AG-UI SDK client** with that CopilotKit provider option, or silently ship the development-only option as the hosted architecture. The TS runtime is the documented platform-independent CopilotKit route considered here. [Self-managed agent guidance](https://docs.copilotkit.ai/backend/self-managed-agents)

AG-UI standardizes interaction events; A2UI specifies UI structures. The protocols can be combined. [AG-UI introduction](https://docs.ag-ui.com/introduction) A2UI current docs list v0.9.1 as current and maintained React support, with v1.0 planned; the repository still labels the overall project an early public preview. Pin protocol and renderer versions rather than using old v0.8 examples or assuming v1.0 support. [Renderer matrix](https://a2ui.org/reference/renderers/), [official repository](https://github.com/a2ui-project/a2ui)

Editable diagrams and briefs live under `agent-memory/diagram-sources/ui/`; the flat `diagrams/` directory is reserved for coordinator-produced final PNGs, following the user's updated artifact rule. Do not create source files or subfolders there.

## What the options actually provide

**Verified:** AG-UI is an interaction/event protocol, not a library of chart components. Its event vocabulary covers runs, text, tool calls, state snapshots/deltas and custom payloads. The Python SDK provides typed models; its encoder emits SSE. This can wrap an ordinary Python chain without adopting LangGraph or a hosted agent service. [Python SDK](https://docs.ag-ui.com/sdk/python/core/overview), [encoder source](https://github.com/ag-ui-protocol/ag-ui/blob/main/sdks/python/ag_ui/encoder/encoder.py)

**Verified:** CopilotKit supplies the React chat/hooks/rendering integration above that protocol. Its registered backend-tool renderers expose in-progress/executing/complete states and partial argument parsing. Rendering a tool call is still application-authored React: a dashboard renderer can render five children in one call, but the library does not decide their factual correctness. Suppress default/raw tool rendering for internal queries so snippets, arguments and private memory do not appear accidentally. [Tool renderer reference](https://docs.copilotkit.ai/reference/hooks/useRenderToolCall)

**Verified:** A2UI supplies a declarative UI protocol with surfaces, component IDs and separate data bindings, transported by another mechanism. v0.9.1 uses `createSurface`, `updateComponents`, `updateDataModel`, `deleteSurface`; creation precedes updates, component `root` is required and the catalog is fixed per surface. Replacing a data-model path is not an arbitrary React execution facility. [v0.9.1 specification](https://a2ui.org/specification/v0.9.1-a2ui/)

**Verified:** Its basic catalog contains layout, text/media and input controls, but no domain status card, analytical table, heatmap, chart or geographic map. Those require custom catalog components/wrappers and evidence behavior. Native composition therefore does not remove the renderer work this challenge needs. [Actual basic catalog](https://github.com/a2ui-project/a2ui/blob/main/specification/v0_9_1/catalogs/basic/catalog.json)

**Inference:** A typed block catalog is sufficient generative UI for this challenge: the assistant selects components, fields, grouping and layout for the question rather than selecting a hardcoded screen. It is deliberately narrower than arbitrary UI-tree generation. The task needs accurate changing data and combined panels more than unbounded visual novelty. Neither JSON validation nor a declarative protocol by itself establishes factual grounding, authorization or a safe custom component implementation.

| Architecture | Python and hosting | Benefits for this task | Costs and adoption condition |
|---|---|---|---|
| **AG-UI Python + focused typed React renderer — recommend** | Python emits standard AG-UI events; browser `HttpAgent`/client SDK; no separate UI runtime/vendor service | Meets protocol choice with direct control over citation registry, corrections, multi-panel layout, privacy and a small model-facing schema | Own renderer/replay integration and prove SDK compatibility. Best minimal deployment for the central data/memory demo. |
| **CopilotKit + AG-UI + typed dashboard** | Python agent; self-hosted TS runtime for platform-independent CopilotKit path | Existing chat and streaming conventions; one `AnswerDashboard` renderer can own all blocks; broad integration ecosystem | Additional TS service/runtime and version coordination. Choose if an early spike proves shell savings outweigh integration effort; retain same answer contract. |
| **A2UI + direct SSE** | Python emits JSON/surface messages; React renderer; no hosted UI service inherent in protocol | Portable declarative composition and data binding; multiple catalog components per surface | Still owns transport/chat/persistence plus custom analytic catalog; larger validation space for Gemma. Choose for real multi-client portability requirement. |
| **CopilotKit + AG-UI carrying A2UI** | Python agent → TS runtime → CopilotKit/A2UI integration | Standard interaction plus standard declarative surfaces; good ecosystem demonstration | Most moving parts: two protocol versions, catalog adapter, binding and hydration semantics. Choose after a successful five-panel/reconnect/privacy spike, not solely for logos. |
| **Small custom SSE + typed renderer — contingency** | Python API and React, application-owned wire protocol | Fewest protocol dependencies and useful comparison baseline | Reimplements lifecycle/client tooling and diverges from the user's preferred protocol direction; use only if explicitly selected after compatibility findings. |

The combined path is officially documented, but its end-to-end fit with this Gemma endpoint is **untested**. Use the maintained CopilotKit A2UI integration instead of inventing an allegedly standard custom event name; pin its exact payload wrapper after a compatibility spike. [CopilotKit A2UI integration](https://docs.copilotkit.ai/generative-ui/a2ui)

## Version, stability and license snapshot

Official repositories/manifests and release endpoints inspected 17 Oct 2026; these are discovery observations, not a tested dependency lock. Do not use a monorepo's generic “latest release” as the version of every package.

| Item | Verified snapshot | Implication / primary evidence |
|---|---|---|
| CopilotKit React core/UI | 1.79.1; MIT; release 15 Oct 2026 | Current docs use `/v2` imports within the 1.x package line. Do not mix older `useCopilotAction` tutorials with current hooks without checking. [Core manifest](https://github.com/CopilotKit/CopilotKit/blob/main/packages/react-core/package.json), [release](https://github.com/CopilotKit/CopilotKit/releases/tag/v1.79.1) |
| AG-UI | Python `ag-ui-protocol` 1.0.0, protocol 1.0; TS `@ag-ui/core` 1.0.3; MIT | CopilotKit core currently pins AG-UI client/core 1.0.2. Use its supported graph; newest standalone SDK need not be the compatible choice. [Python manifest](https://github.com/ag-ui-protocol/ag-ui/blob/main/sdks/python/pyproject.toml), [TS core manifest](https://github.com/ag-ui-protocol/ag-ui/blob/main/sdks/typescript/packages/core/package.json) |
| A2UI protocol | v0.9.1 current; v1.0 candidate; v0.8 legacy; Apache-2.0 | Maintained renderer matrix calls React v0.9.1 stable, while README calls overall project early preview and retains older roadmap prose. Prefer explicit version matrix/spec over stale “React planned” wording. [Renderer matrix](https://a2ui.org/reference/renderers/), [license/README](https://github.com/a2ui-project/a2ui) |
| A2UI packages | `@a2ui/react` and `@a2ui/web_core` source manifests 0.14.0 | Package and protocol versions are separate. CopilotKit A2UI renderer 1.79.1 pins `@a2ui/web_core` 0.10.4, so do not override it with latest blindly. [React manifest](https://github.com/a2ui-project/a2ui/blob/main/typescript/renderers/react/package.json), [CopilotKit adapter manifest](https://github.com/CopilotKit/CopilotKit/blob/main/packages/a2ui-renderer/package.json) |
| ECharts | 6.1.0 release; Apache-2.0 | Recommended analytics renderer candidate, requires a small React lifecycle wrapper. [Official release](https://github.com/apache/echarts/releases/tag/6.1.0) |
| Mermaid | 12.2.0 package; MIT | Candidate for inline flow/relationship diagrams, lazy loaded. [Manifest](https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/package.json) |
| Leaflet | Stable v1.9.4 release; BSD-2-Clause | Small geographic pin-map candidate; a tile source remains separate. [Release](https://github.com/Leaflet/Leaflet/releases/tag/v1.9.4), [license](https://github.com/Leaflet/Leaflet/blob/main/LICENSE) |

No library here requires OpenAI/Gemini as the model merely to render locally authored components. Demo quickstarts often use a provider-specific agent; that does not verify OpenRouter/Gemma integration. UI service independence also does not imply offline operation: the chosen model calls OpenRouter, and a default basemap may fetch external tiles. Licenses above describe the named OSS projects; optional CopilotKit Intelligence services are a separate product with separate terms. Review final dependency notices during packaging.

## Recommended message contract and ownership

**Proposed interface; no app code implemented.** Align with `agent-memory/memory-research.md` and `agent-memory/retrieval-research.md`: use exactly `EvidenceRef`, `ResultSet`, `dataset_revision`, `knowledge_revision`. A correction revision is the shared `knowledge_revision`, not a competing UI-only counter. Request context supplies authenticated/demo-selected user, dataset namespace, thread/exchange/run IDs, reference date and timezone. The model cannot set identity or evidence ownership.

Final reconciliation: read the coordinator's `agent-memory/integration-contracts.md` as the canonical shared seam. This report supplies the UI-specific component/lifecycle detail beneath it. Peer reports were rechecked before completion: immutable result pages/manifests, coverage, `minimum_knowledge_revision`, private entity receipts and correction commit boundaries align. Their internal event labels are payload projections, not replacements for the selected AG-UI event vocabulary. No peer-owned file was edited.

The server owns the full envelope and result registry. Gemma returns only a `ViewPlan`: catalog component choices, references to supplied result IDs/columns/claims, titles, order and a bounded layout hint. It does not author result rows, totals, rule applicability, source URLs, user scope or correction receipts.

```typescript
// Proposed wire shape; ResultSet and EvidenceRef definitions belong to peer contracts.
type Component = "status_card" | "table" | "line_chart" | "bar_chart"
  | "heatmap" | "map" | "diagram";
type Claim = {
  claim_id: string;
  kind: "fact" | "inference" | "suggested_check";
  text: string;
  evidence_refs: string[];
  value_refs: Array<{ result_set_id: string; row_id: string; column: string }>;
};
type PanelMeta = {
  block_id: string;
  component: Component;
  title: string;
  evidence_refs: string[];
  caption_claim_ids: string[];
  layout: { span: "half" | "full" };
};
type Panel = PanelMeta & (
  | { state: "ready"; result_set_id: string;
      encoding: object } // Real schema is a closed union by component, below.
  | { state: "unavailable" | "error"; reason_code: string;
      message: string; retryable: boolean }
);
type AnswerEnvelope = {
  schema_version: "asset-answer.v1";
  message_id: string; run_id: string; exchange_id: string;
  dataset_namespace: string;
  dataset_revision: string; knowledge_revision: number;
  reference_date: string; timezone: string;
  bounds: { start: string; end: string; closure: string } | null;
  narrative: Claim[];
  blocks: Panel[];
  result_sets: Record<string, ResultSet>; // Bounded inline result pages + manifest.
  evidence: Record<string, EvidenceRef>;
  warnings: Array<{ code: string; text: string; block_ids: string[] }>;
  completion: "complete" | "partial";
};
```

The abbreviated `encoding: object` above is explanatory, **not** permission for arbitrary properties in implementation. Pydantic discriminated unions and a matching JSON Schema/TypeScript validator must close each branch (`extra=forbid` / `additionalProperties:false`). Generate or verify one canonical schema across Python and TS; avoid hand-maintaining subtly different unions. Validate structural input again at the browser boundary.

| Component | Allowed encoding and semantic checks | Display and evidence |
|---|---|---|
| status_card | One stable row; fields selected from a server-defined domain field allowlist | Effective observed production, timestamp, inspector display name; raw recorded status labeled separately, applicable threshold, context/conflict and citations |
| table | Explicit column keys and server row order; safe format enum; cursor handle | Units, stable IDs, per-row evidence links, truncation/coverage label; sorting never silently changes aggregate population |
| line_chart | Time column plus numeric series columns, units, optional server-derived `not_producing` mask | Preserve missed inspections as missing; no invented/interpolated observations; show non-producing markers and threshold rule evidence |
| bar_chart | Category key, numeric measure, supplied rank/order and tie metadata | Well IDs or area display names; totals/ranking already calculated server-side |
| heatmap | Two dimension keys, numeric measure, explicit category domains, missing/zero encoding | All required months/areas; zero count differs from incomplete coverage; count versus bbl clearly labeled |
| map | Latitude/longitude keys, entity label and marker status keys; valid coordinate bounds | Well-ID pins, source-backed popups, fit bounds; inspect table remains available; missing positions disclosed |
| diagram | Server-validated graph ID with typed nodes/edges/labels and evidence refs | Mermaid produced by deterministic graph-to-syntax adapter, not arbitrary JSX/HTML or freeform executable directives; causal inference styled and labeled |

One answer carries an ordered **array** of blocks, not a single `visualization` discriminator. Example dashboard request: “Summarize this area's current production, spill trend, spill distribution and locations.” The plan can select five panels: current status summary, non-producing-well table, spill trend, area-by-month heatmap, spill map, plus a short evidence-linked narrative. All five reference compatible snapshots; each can reference a distinct `ResultSet`. The server must preserve explicit requested visuals even if a different one seems more convenient. A simple answer such as Q5 may have `blocks: []`.

Layout is a small semantic choice, not model CSS: desktop uses a two-column grid, full-width table/map when needed, and mobile stacks in reading order. Suggested initial budget: at most eight panels per message, 50 table rows per page and a 1 MB total event cap; tune from real data/performance. Paginate full result sets server-side without changing the aggregate population, and state when a visual is sampled or incomplete. Do not silently reduce a 4–5 panel request to one component. For insufficient evidence, retain the requested panel shell with an explicit unavailable state and explanation.

Large result manifests expose opaque page handles resolved through an authorized server endpoint; they are not arbitrary URLs or permission-bearing IDs. The initial wire type above contains bounded inline pages. If adding lazy handles, define a separate explicit `inline | handle` union with dataset/knowledge revisions rather than putting a URL in a field typed as `ResultSet`.

Keep the reference date/window visible in answer chrome and panel captions: the supplied DOCX says 17 Oct 2026 while local guide/scenarios say 16 Oct, and Q6 explicitly uses 16 Jun–16 Oct. The UI must echo the normalized scenario/query bounds rather than substitute the browser clock. Use a calm field-domain expert voice: answer first, explain the observed basis and rule, distinguish inference, and suggest a targeted check when cause/evidence is absent. Avoid claiming operational certainty beyond the synthetic evidence.

For narrative, resolve exact numeric facts from `value_refs`; compare any model-written number/date/entity with its tool receipt before publication. A citation's existence alone cannot validate the accompanying claim. Initially favor deterministic sentence templates for headline figures/status/deadlines; permit model prose for bounded explanations/inferences and preserve missing-cause language. Claims need record **and applicable rule** evidence when a conclusion depends on both. Do not claim a complete semantic verifier for unrestricted prose.

## Streaming, partial state and persistence

**Proposed primary AG-UI transport:** use standard event schemas and `RunAgentInput` at the Python endpoint. Browser `@ag-ui/client` `HttpAgent` consumes the stream; Python SDK models and `EventEncoder` produce it. Validate trusted user/thread context independently of client-sent messages/state. No CopilotKit runtime is necessary for this direct AG-UI client path. The bounded spike must exercise event decoding and same-origin/CORS/auth behavior with the exact SDK pair.

Application domain projections use schema version, `run_id`, `message_id`, monotonically increasing `seq`, and server event ID inside a namespaced custom payload or answer state subtree. Per-block updates also carry `block_id` and revision. `block_validated` atomically inserts/replaces a complete validated block; `answer_complete` supplies the authoritative final envelope/manifest. These names are **application payload kinds**, not invented AG-UI top-level event types. Use safe `STEP_STARTED/STEP_FINISHED` or registered progress payloads instead of leaking internal tool results. Memory's `knowledge_changed` is a separate application invalidation notification, not a model instruction.

Allow five blocks to arrive in one answer independently. Render skeletons immediately, then publish only complete validated block payloads. Do not parse half a Gemma JSON object into a factual chart; partial model arguments may describe layout skeletons only. First slice can wait for a complete bounded view-plan object, then emit the validated panels progressively. Later per-block composition is optional and must not pretend it is token-by-token schema enforcement.

Reducer rules: reject wrong-run/scope events; ignore duplicated sequence IDs; reject stale block revisions; buffer/recover gaps through authorized replay/snapshot; mark EOF without a terminal event as interrupted. A replay request uses the last received cursor, and the server rechecks thread ownership. Persist answer envelope plus immutable result/evidence references and manifest, rather than reconstructing old charts by asking the model again. Unknown schema/catalog versions show an explicit compatibility state. Release chart/map resources when blocks unmount; cancellation stops writes to the live message while a durable run status records what finished.

Emit `RUN_STARTED`, text events where applicable, safe step/progress events, `STATE_SNAPSHOT/STATE_DELTA` or a namespaced `CUSTOM` payload for the answer, then exactly one terminal `RUN_FINISHED`/`RUN_ERROR`. The application's block schema remains its own contract. Patch paths and payloads stay inside the answer subtree; never accept model-generated arbitrary store patches. Mapping application cancellation/partial states onto AG-UI outcomes must be explicit and tested against selected SDK versions. Serialize sequence/replay metadata inside the application payload (and HTTP SSE cursor where supported), not arbitrary additions to closed SDK models. [AG-UI event semantics](https://docs.ag-ui.com/concepts/events)

A2UI adaptation should be server-side from the same domain view plan: register trusted domain components, create one surface per answer, construct component IDs/bindings deterministically and apply updates in its protocol order. Do not ask Gemma to emit both custom block JSON and unrelated A2UI trees. Default `sendDataModel` off so actions do not echo entire table/map payloads back unnecessarily; allowlist action fields and reauthorize every action. Version-specific wire semantics come from the pinned spec, not old `beginRendering` examples.

## Corrections, errors and privacy

Each answer pins one `(dataset_revision, knowledge_revision)`. If a correction commits during generation, recompute affected results/claims before final publication, or clearly present the complete older snapshot with refresh; never mix old bars with a new headline. Later queries require at least the committed knowledge revision. Historical answers retain as-of labels; a refresh creates a new consistent revision and cannot update only one panel. Invalidation scope comes from the shared ledger dependency receipts. Shared accepted corrections are shown with author/reason/scope/validity; ordinary contradictory notes remain attributed and unconfirmed.

User switching aborts the old stream, clears private state/caches and loads the selected user's thread. Cache/result/evidence authorization includes dataset namespace, trusted user, revision and run scope. A guessed `result_set_id`, `evidence_id` or replay cursor must not grant access. The demo picker is sufficient identity selection per brief, but should not be described as production authentication. Shared correction receipts expose only shared domain content, not the private chat in which the correction was supplied. UI events, browser storage, errors and telemetry must not retain another user's history. Model reasoning tokens and raw prompt/tool traces are not narrative.

| Failure | Required visible behavior / boundary |
|---|---|
| Invalid JSON/schema, unknown component or column | At most one bounded formatting repair; then server-composed supported text/table fallback with evidence and unavailable-panel warning |
| Unsupported requested visual | Explicit limitation; no false claim that plain text is a map/heatmap |
| Correct JSON, unsupported claim or unknown evidence | Reject offending claim/block; do not repair by manufacturing a source/value |
| Tool missing report, partial fleet coverage or unknown cause | Preserve partial/unknown, show denominator/coverage, cite available evidence; no confident total or invented cause |
| Chart/map/diagram renderer throws | Per-panel boundary keeps sibling panels and narrative; accessible table/data fallback plus retry |
| Model/provider timeout or stream disconnect | Terminal partial/error/interrupted state; keep validated panels and say which remain missing; bounded authorized retry |
| External map tiles fail | Pins/coordinates remain inspectable on a neutral coordinate view or table; state basemap unavailable |
| Malicious report text or title | Render as data, sanitized text; no raw HTML, eval, dynamic import, model URLs or executable chart formatter strings |
| Correction changes spill class/deadline | Recompute narrative, chart, totals and compliance together; show superseded versus current values |

## Chart, map and diagram renderer choices

**Recommendation/inference:** ECharts for line/bar/heatmap, a plain semantic HTML table, locally authored status cards, Leaflet for geographic pins, Mermaid for explanatory diagrams. ECharts exports all three chart types and supports importing only the needed modules/renderers; use one application-owned React wrapper with resize/dispose handling and declarative prop validation. The server supplies data/encodings; client code builds safe ECharts options, so the model never emits arbitrary `option`, JavaScript formatter, data URL or transform expressions. [Official chart exports](https://github.com/apache/echarts/blob/master/src/export/charts.ts), [modular imports](https://echarts.apache.org/handbook/en/basics/import/)

ECharts accessibility support must be explicitly imported/enabled, and color/pattern encodings should accompany text and an inspectable table. Do not claim ARIA configuration alone proves keyboard or screen-reader accessibility. [Accessibility guide](https://echarts.apache.org/handbook/en/best-practices/aria/) Keep chart titles, units, selected window and missing-data definitions visible outside the plot; share formatting functions with narrative templates.

**Alternative:** Recharts for familiar React line/bar components plus a CSS/SVG heatmap. Official current release is 3.10.1; the reference project uses the 2.x line, so its wrapper is a pattern rather than a drop-in tested 3.x integration. ECharts reduces the need for a separate heatmap implementation, while Recharts can be simpler if the team already knows it. Actual bundle/interaction cost remains unmeasured. [Recharts release](https://github.com/recharts/recharts/releases/tag/v3.10.1)

Leaflet provides markers/popups/bounds without a 3D globe. Use server-resolved well metadata for positions and sanitized labels; a basemap URL/token is application configuration, not model output. Do not assume public tile servers allow unlimited production use or make the app offline. For this demo, a configured permitted basemap and explicit failure fallback suffice. [Leaflet reference](https://leafletjs.com/reference.html)

Mermaid `strict` encodes HTML and disables click functionality; retain application-controlled security settings and reject embedded directives/links. Prefer a typed graph → deterministic Mermaid adapter, bound graph size and catch parse/render errors; the renderer is still a dependency to test. An evidence-backed sequence/timeline or relationship diagram can clarify inspection → repair/report → regulator dependencies, with inferred causal links explicitly distinguished. [Mermaid security configuration](https://mermaid.js.org/config/schema-docs/config.html#securitylevel)

## Gemma/OpenRouter validation boundary

The coordinator's saved `openrouter-capabilities.json` reports `response_format` and tools/tool_choice but no `structured_outputs`; the checked Gemma page advertises JSON without schema enforcement. This is **public metadata verification**, not a successful authenticated model response. Use `json_object` only after the endpoint smoke check; never claim it guarantees the discriminated union. Strict `json_schema` is conditional on endpoint support and provider routing. [Selected model](https://openrouter.ai/google/gemma-4-31b-it:free), [structured output guide](https://openrouter.ai/docs/guides/features/structured-outputs)

Keep the model plan shallow: selected result IDs, approved enum components/column keys and concise claims. Supply compact result receipts, not five complete data arrays or a giant A2UI catalog. Python parses and validates with bounded output fixing in `backend/output_parsers/`; the retry receives validation errors and the original fact receipts and may repair syntax/references only. Server assembly then resolves values/citations. On repeated failure, use deterministic factual fallback; no third “creative” recovery. Keep orchestration in `backend/chains/`, YAML `input:`/`prompt:` references plus single-source Markdown prose in `backend/prompts/`. No model/API calls were made in this track.

## Read-only reference inspection: exact reusable paths

Base `/home/harshsanghavi/Desktop/copilot-revive/` inspected on disk, including workspace/frontend/backend `AGENTS.md`; no reference files changed. Its top-level guidance overrides stale nested source-of-truth paths and says active runtime is the live chat path, not legacy Flow Builder. Paths below are current working-tree references, not claims about history or production behavior. Reuse ideas selectively after checking licensing/ownership; do not migrate whole trees, FlytBase auth, drone actions or proprietary assets into a public hackathon repo automatically.

| Exact file relative to base | Observed pattern worth reusing | Required adaptation |
|---|---|---|
| `fb-copilot/src/ui/components/chat/types.ts` | Discriminated typed server frames and message variants | Introduce one dashboard message with `blocks[]`, stable evidence/result references and schema version; its existing status is execution status, not well production |
| `fb-copilot/src/ui/components/chat/ChatMessage.tsx` | Small renderer dispatch and shared agent row/feedback wrapper | Iteration over multiple analytic blocks under one answer; file currently handles text/plan/ask/confirm/status/waiting/media, not analytic charts |
| `fb-copilot/src/api/chat.ts` | POST `fetch` + ReadableStream, AbortSignal, stream buffering, session-resume calls | Existing parser handles a narrow single-data-line protocol, silently skips malformed JSON and accepts EOF; use real frame validation, robust line endings/limits and explicit terminal-event handling |
| `fb-copilot/src/ui/stores/chatStore.ts` | Stream reducer, abort, persistence/restore coordination | Split focused per-run answer reducer; scope caches to selected user and add sequence/revision handling; do not copy its drone plan state |
| `fb-copilot/src/ui/components/chat/MarkdownRenderer.tsx` | App-controlled text rendering and URL filtering | It is a small handwritten parser, lacks analytic tables/Mermaid and uses a broad URL allowlist; add structured citations rather than assuming full Markdown or source safety |
| `fb-copilot/src/components/ui/chart.tsx` | Responsive Recharts container and shared legend/tooltip formatting | Theme/configuration must be trusted code; its CSS injection must never receive model-controlled colors/keys. Not an ECharts adapter |
| `fb-copilot/src/ui/components/site-context/SiteContextCesiumMap.tsx` | Map boundary/lifecycle context pattern | 3D Cesium/site/drone coupling is unnecessary for the well pin map; use lightweight geographic renderer |
| `fb-copilot-backend/src/services/chat/transport/types.ts` | Backend typed transport seam | One canonical schema and Python contracts rather than TS duplicate drift |
| `fb-copilot-backend/src/services/chat/transport/sse.ts` | No-buffer SSE headers; records logical frames even after browser disconnect | Python implementation needs authorized saved snapshots/replay, event IDs and bounded payload/backpressure handling |
| `fb-copilot-backend/src/api/routes/chat.routes.ts` | Session ownership/context, snapshot persistence and resume endpoint organization | Build minimal user-scoped hackathon boundary; retain explicit error completion but avoid unrelated action/approval flows |

Inspection found useful chat infrastructure, **not a verified existing multi-component analytics answer implementation**. No reference build/tests/services were run. The reusable architectural idea is typed transport → reducer → trusted component dispatch, which fits the recommended renderer independently of that project's dependencies.

## Phased implementation plan and handoff

1. **Compatibility and contract spike:** after implementation authorization, freeze canonical `EvidenceRef`/`ResultSet`/`AnswerEnvelope`, verify selected OpenRouter endpoint JSON/tool behavior and locally reject malformed plans. First prove Python AG-UI SDK → HTTP/SSE → browser `HttpAgent` → five-panel renderer with lifecycle/restore/isolation. Time-box this spike to roughly 60–90 minutes (planning estimate). If evaluating CopilotKit, prove Python agent → TS runtime → registered five-panel renderer without Intelligence; separately test the pinned A2UI adapter only if adopting it. Report actual blockers before selecting the custom-wire contingency; do not silently abandon the user's protocol direction.
2. **Deterministic vertical slice:** one user, Q1 status card and Q6 ranking with record/rule citations; backend results are the single source for narrative and visuals. Implement safe source viewer and data inspect table before decoration.
3. **Full visual catalog:** Q2/Q4 tables, Q3 line/markers, Q7 pin map, Q8 heatmap and one evidence-backed diagram. Add explicit-visual routing and a custom five-panel dashboard request with shared revision/window.
4. **Lifecycle and correction integration:** persist/replay one answer envelope, test duplicates/EOF/cancel, then apply shared corrections across every panel; hook memory receipts and user-switch isolation to peer contracts.
5. **Evaluation and demo polish:** Q1–Q10 independent facts/evidence/visual checks; Q11–Q18 stated sequence with isolated fixtures; responsive/accessibility and failure-mode tests; log actual usage, latency, validation repairs and limitations. Finish the visible end-to-end demo before optional A2UI portability or animation.

Retrieval track owns effective snapshot queries, full-population math, report links, immutable result/manifest authorization and coverage. Memory track owns trusted context, private reference resolution, shared ledger transactions and revision/invalidation semantics. UI owns component unions/layout, view-plan validation, answer assembly integration, safe presentation/citations, stream reducer and visual tests. Chain/prompt owners must not fork an independent numeric result for narration. Source viewer and event endpoints should be agreed jointly; names here are proposed, not implemented APIs.

## Acceptance criteria and remaining unknowns

- A single user request produces one answer with narrative plus **five distinct usable inline panels**, stable block IDs and citations; test mobile stacking and reload restoration. It must not be five fixed routes or five separate assistant turns.
- Q1/Q2/Q3/Q4/Q6/Q7/Q8 named visuals render as requested; Q5 may remain text. Q9/Q10 show record plus report/SOP evidence and keep missing causes/actions explicit. Data/visual assertions use independent expected calculations, not the renderer's own transformation.
- Every displayed numeric value equals the referenced effective `ResultSet` value at the answer's revision, with unit/date semantics. Heatmap zeros are distinguishable from unknown/missing cells; map contains all matching geolocated wells and names missing coordinates.
- Corrected temperatures/volumes and type-specific rules update later text, totals, rankings and visuals for both users; historical snapshot disclosure and correction-mid-run behavior are consistent. A type-wide override cannot alter another type.
- User B cannot retrieve A's message/result/evidence/replay/history by guessing an ID; stale stream events after a user switch cannot populate B's screen. Shared correction provenance remains visible without private transcript leakage.
- Partial JSON, nonexistent column/source, unsupported component, injection strings, oversized graph, duplicate/out-of-order frames, disconnect and renderer failure all reach explicit recoverable states. Sibling validated panels remain usable and no unknown value becomes zero.
- A failed schema repair never becomes fabricated data; explicit unsupported visuals stay visible as limitations. No arbitrary React/JS execution, raw HTML, model-controlled imports/URLs or chart callbacks are accepted.
- Record actual model/schema success rate, repairs, fallback frequency, token usage and time to first useful panel/final answer. No claimed performance target or framework compatibility is measured yet.

Open decisions for review: direct AG-UI client versus a bounded CopilotKit shell spike; choose exact UI dependency pins after runtime tests; define a permitted map tile source; set practical panel/payload limits after real sizing; choose production identity/retention separately from the demo picker. A2UI renderer availability is verified in docs, but direct AG-UI end-to-end behavior, custom domain catalog behavior, CopilotKit adapter compatibility, Gemma multi-block reliability, mobile readability and accessibility remain untested. The coordinator produces final PNGs from the editable diagrams and the three-option `image-brief.txt`; this track generates no images.

## Artifact verification

`skill-creator/scripts/quick_validate.py skills/generative-ui` passed. A read-only path check confirmed every listed reference code file exists; all seven `.mmd` files have expected diagram headers. No Mermaid executable was installed, so syntax rendering is delegated to the coordinator's existing rendering workflow and is not claimed as tested here. The original provisional hypothesis is retained as `00-provisional.mmd`; final recommendations use `01-recommended.mmd` and subsequent alternatives, with `06-custom-sse-contingency.mmd` explicitly secondary. No application tests, model benchmarks or reference-project builds were run in this planning-only task.
