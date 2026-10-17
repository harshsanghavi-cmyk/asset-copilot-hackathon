# Current status — three implementation tracks

17 Oct 2026. **Research/comparisons are complete; the user has authorized all three main implementation tracks, now in progress.** This pack is experiment evidence, not a finished copilot. [FINAL_PLAN](../FINAL_PLAN.md) is the roadmap and acceptance matrix; [decisions](../agent-memory/final-decisions.md) records current choices and limits.

| Vertical | Completed evidence | Current direction | Still to verify |
|---|---|---|---|
| Generative UI | Real rich direct AG-UI/CopilotKit fixture tie; A2UI wrapper; independently composed OpenUI/json-render panels, controls/evidence/scope/revision/build checks | React + CopilotKit/AG-UI + Ant Design/ECharts + compact reference JSON; authorized frontend/session/admin routing and TS companion in progress | Live main backend/Gemma answers; all requested visuals/geographic-map suitability; full keyboard/screen-reader/contrast, errors/reconnect |
| Q&A / memory | Explicit and LangGraph 53/53 synthetic state checks; gbrain 17/17 exact engine probe; prompt/memory/5K contracts complete | Canonical private facts/history/receipts, shared operational assertions and separate authority ledger; bounded workflow; engine reconciliation pending | Live proposal/summarizer/compression fidelity, selective recall/privacy under caps,10/20/overflow/restart and integrated scenarios |
| Retrieval / data | Full measured audit;9 exact checks; full-area linked containment/unknown checks;24-query lexical comparison | **Provisional** injected RetrievalProvider: complete SQL/effective values + source joins + FTS; detailed inspection viewer in progress before user acceptance | Provider replacement, unseen imports, general prose/unknowns, Gemma-only assistance and factual/citation quality |

## UI library and token result

[New measured comparison/screenshots](01-generative-ui/library-comparison/README.md): compact JSON161, OpenUI148, JSON-wrapped OpenUI173, json-render snapshot242 fixed-output Gemma tokens. These are12 static counting requests and **zero generation requests**. OpenUI's13-token/about8.1% saving is not a transferred GPT-tokenizer vendor claim. Input/catalog counts158/818/845/4254 are separate: prompts are unequally optimized and json-render default JSONL-patch input mismatches snapshot output. No optimized total-efficiency, generation-quality or latency winner follows. Native82/84/36 exports include helpers; matched trials expose7 custom entries.

## Model and context

Gemma 4 31B only throughout, temporarily verified Google-compatible route, shared user-reported30RPM cap. Plain final generation and clean JSON smoke tests succeeded; native500/OpenRouter429 remain observations. Local schema/evidence validation is required. Historical MiniLM/RRF is **INELIGIBLE** regardless of recall gain.

User content cap: **5K=2K long-term TOTAL private+shared +1K historical dialogue/summary +2K fresh evidence**. Always load private capsule/index600 + shared header/index200, then selected exact private400 + shared800. Persona/tools/current request/output/framing are separately counted, with estimates disclosed. Original durable facts/chart arrays remain server-side. Useful memory admission is checked every message; ten-exchange summarization is different. [Loading decision](../agent-memory/long-term-memory-loading-decision.md), [retrieval contract](../agent-memory/retrieval-operating-contract.md).

## Data and diagnostics

No duplicate IDs, broken measured references or missing linked reports were found. Hazards include27 inferred shutdown-cause discrepancies,30 potentially compatible delays,21 stale statuses,56 formal false positives,9 interim estimates and6 late-but-closed verifications. [Audit](../agent-memory/data-audit.md) has exact spans; these are not all corrupt records.

Normal evidence viewing stays answer-scoped. A separate explicitly enabled/capability-gated admin page is being built for private/shared memory history/save/update/provenance/compaction plus retrieval query/schema/table/count/selected-omitted evidence previews. User picker/role does not grant admin. Retrieval is not accepted merely because this candidate has code.

## Completion gate

All 18 official scenarios, unseen same-format data, live model outputs, separate fact/evidence/visual scores and privacy/revision/budget tests remain the integrated gate. Nine arithmetic fixtures, synthetic dashboards,53 state checks and provider JSON smoke tests cannot be added into a copilot pass rate. [Pack navigation](README.md) and [roadmap](../FINAL_PLAN.md) identify current contracts; copied historical reports retain dated recommendations and are superseded where noted. Submission preparation follows actual results; publication/deployment/portal submission remain outside current scope.
