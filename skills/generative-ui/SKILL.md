---
name: generative-ui
description: Plan, implement or evaluate evidence-backed multi-panel chat answers for Asset Intelligence Copilot using typed component plans, exact result references, citations and revision-consistent updates. Use for this project's inline visual rendering and streaming contracts.
---

# Evidence-backed generative UI

Honor the current planning/implementation scope in `../../AGENTS.md`. Read
`../../agent-memory/ui-research.md` for the proposed architecture, component
contract, reference code paths and acceptance checks. Read the memory/retrieval
reports when changing their shared interfaces; preserve `EvidenceRef`, `ResultSet`,
`dataset_revision` and `knowledge_revision` rather than inventing parallel stores.
Use `../../agent-memory/integration-contracts.md` as the canonical shared seam.

## Compose one answer from several blocks

Use one versioned answer envelope with ordered `blocks[]`, narrative claims,
evidence registry and immutable result references. Support one response containing
4–5 panels when requested. Honor explicit visual requests; otherwise use a status
card for one well, table for a list, line chart for time, bar chart for comparison,
map for locations and heatmap for two dimensions. A scalar may remain text.

Let the model choose allowlisted components, result IDs, column keys and bounded
layout hints. Server tools own values, totals, rankings, rules and coverage. Do
not ask the model to regenerate chart data arrays or execute generated React,
JavaScript, chart callbacks, CSS or HTML. Diagram graphs also need typed nodes,
edges, evidence and a controlled renderer.

## Validate before publishing facts

Treat the selected Gemma endpoint's JSON output as untrusted. Check actual
endpoint capabilities before using `response_format`; JSON-object output does
not imply schema enforcement. Parse with closed discriminated unions, resolve
every result/column/evidence reference, and check numeric claims against tool
receipts. Bound formatting repair to one attempt; then return a factual supported
fallback with explicit missing-panel information. Repair cannot invent evidence.

Keep Python orchestration in `backend/chains/`, parsers in
`backend/output_parsers/` and single-source Markdown prompt prose referenced by
YAML with `input:`/`prompt:` in `backend/prompts/`. The browser validates the wire
envelope again. Prefer server-resolved source links over model-generated URLs.

## Preserve lifecycle and scope

Publish complete validated blocks, with stable run/message/block IDs and monotonic
event/block revisions. Skeletons may appear earlier; half-parsed JSON must not
become a factual chart. Handle duplicate events idempotently and EOF without a
terminal event as interruption. Persist envelopes and immutable references for
authorized restore, not model regeneration.

Pin one dataset/knowledge revision across narrative and every panel. Recompute
affected results after a shared correction or explicitly retain a historical
snapshot; never combine old chart data with newly corrected prose. Apply peer
track scope/validity rules. Use well IDs and person/area/team display names;
show missing causes, conflicts, coverage and source/rule evidence.

Identity comes from the application boundary. Authorize result, evidence and
replay reads; clear private state and abort old streams on user switching.
Expose shared correction provenance without the surrounding private conversation.
Keep raw prompts, model reasoning and internal tool payloads out of chat.

## Keep failures usable

Use a boundary per panel, an inspectable data table for charts/maps, visible
units/windows and a mobile reading order. Unknown data differs from zero.
Retain valid sibling panels when one fails; explicitly label unavailable requested
visuals. Test five-panel composition, source resolution, correction propagation,
reload/disconnect, user isolation and invalid plans against independent fixtures.
Report actual measured behavior separately from proposed architecture.

## Use the measured enterprise combination

Read `../../agent-memory/ui-experiments.md` and its pinned branch artifacts before
changing the stack. The measured recommendation for this conversational product
is **Python AG-UI + self-hosted CopilotKit TypeScript runtime + React/CopilotChat +
an application-owned typed Ant Design/ECharts catalog**, with wide rich responses.
Keep direct browser HttpAgent + the same rich catalog as a credible baseline.
The functional fixture tied; do not choose a minimal renderer merely for fewer
packages or assume the transport determines visual richness.

Use actual enterprise components for sortable/filterable tables, coordinated
selection, evidence drawers, loading/error/empty states and responsive cards.
The tested catalog uses Ant Design and Apache ECharts. These are the measured
combination, not a claim that untested open-source libraries are inferior.
The tested CopilotKit default 768px message column reduced dashboard scan density;
the wide-answer customization restores a three-column desktop answer while
keeping prose and the standard composer readable. Verify the pinned chat
slot/DOM styling hooks on upgrades and retest mobile stacking and accessibility.

AG-UI carries interaction events; A2UI describes declarative UI. Neither replaces
domain validation. A maintained A2UI React custom EvidenceDashboard catalog
component was tested with the same typed renderer, incremental data updates and
surface deletion. That single wrapper does **not** prove independently composable
A2UI cards/charts/layouts or arbitrary model-generated UI. Treat richer independent
catalog composition as untested until its own bounded fixture demonstrates it.
Do not conflate the maintained renderer with CopilotKit's bundled older adapter.

The tested independent CopilotKit route uses a self-hosted TypeScript runtime
with a Python AG-UI agent and no Intelligence service key. The native Python
runtime has different hosting requirements. Recheck actual versions and endpoint
capabilities before adoption; Python-agent support does not imply a Python-only
runtime. Align SDK versions with the runtime's exact pins and the catalog's Zod
requirements rather than casting away incompatible private types or suppressing
schema checks. A custom wire protocol remains a contingency, not a silent
replacement for the standard protocol.

## Report the validation boundary

Use the same validated fixed envelope to isolate UI/protocol behavior across
candidates. Test five panels, one rejected block with valid siblings retained,
actual sort/filter and coordinated chart selection, evidence inspection, terminal
event interruption, replay, revision updates and user switching. Exercise the
real protocol SDK, actual chat/render integration and chosen component library;
package installation or counting placeholder panels is insufficient evidence.
Retain raw commands/results and matched desktop/mobile screenshots, including
selection and evidence states. Separate default styling from tested customization.

The local experiments passed TypeScript/build and bounded browser checks. Fixed
fixture replay is not evidence of model answer quality, durable corrections,
authentication, real fleet coverage or saved event-offset recovery. Scripted
waits/build times are not runtime latency rankings. Zero axe violations still
leave incomplete SVG contrast/manual screen-reader checks; retain that limit.
The current fixtures' map boundary and source records are explicitly synthetic.

Keep editable architecture sources/briefs in
`agent-memory/diagram-sources/ui/`; the coordinator alone places final PNGs in
the flat `diagrams/` directory. Main application implementation still requires
the user's plan review; these experiment results do not remove that boundary.
