# Current decisions and evidence log

17 Oct 2026. [FINAL_PLAN](../FINAL_PLAN.md) is the current roadmap. All three main tracks are authorized/in progress; retrieval remains provisional for inspection. This documentation pass makes no application changes, new experiments, sessions or model requests.

| Axis | Decision / boundary |
|---|---|
|UI| React/TS + CopilotKit 1.79.1 self-hosted TS runtime + AG-UI + AntD 6.6.6/ECharts 6.1.0; compact reference JSON. Fixture renderer/protocol evidence, not main-app live answer proof |
|Optional grammar| OpenUI/json-render remain compatible tested extensions; A2UI tested a dashboard wrapper; no initial extra grammar solely for13 fixture output tokens |
|Memory| Canonical private facts/history/entity receipts + shared operational assertions + separate correction/rule authority. gbrain unadopted optional projection, not a failed-quality candidate |
|Workflow| Bounded stages; explicit/LangGraph 53/53 tie. Prior review favors LangGraph; active owner confirmation pending, not inferred from a dependency manifest |
|Retrieval| Injected versioned provider; provisional SQL/effective views + explicit source joins + FTS/sections/spans; user inspection and replacement-provider tests pending |
|Model| Gemma 4 31B only; temporary verified Google-compatible route; global 30 RPM; native500/OpenRouter429 retained observations |
|Context|5K content=2K long-term total+1K dialogue/summary+2K evidence; separately counted overhead/current request/output; always800+selected1200 long-term |
|Diagnostics| Normal scoped evidence viewer plus explicitly enabled/capability-gated admin private/shared history, provenance/compaction and query/table/evidence previews |

Current [memory contract](memory-operating-contract.md), [loading decision](long-term-memory-loading-decision.md), [retrieval contract](retrieval-operating-contract.md), [API seam](backend-api-contract.md) and AGENTS supersede old budget/provider/planning statements. Useful memory is considered every message; explicit save commits before acknowledgment. Accepted fact changes refresh projections;10/20/overflow compaction is short-term dialogue work. Shared operational claims cross challenge teams; private discussion sets do not.

## Raw receipts checked

Experiment HEADs below were independently read with git rev-parse; listed raw JSON was read without rerunning benchmarks or model requests. Worktrees are under `/home/harshsanghavi/orca/projects/asset-copilot-experiments/`.

| Worktree | Checked HEAD | Evidence |
|---|---|---|
|ui-copilotkit|0486915fb6f280c198b7e94a47990b6d68087831|results/validation-summary.json; synthetic chat/renderer checks |
|ui-openui|be402110eeaa3e6db284a3ce8e68f9d4015b8046|results/library-validation-summary.json:8 browser checks true, type/build passed, zero final axe violations with incomplete contrast retained |
|ui-json-render|b833e4a357917c15294786a7c6f982d67686f468| Matched peer report/branch; independent composition/production build, not every native widget tested |
|memory-explicit|1c72ac13a579865ecd87e2990785d4888d4cc53f|experiments/memory/results.json:53/53, zero model calls |
|memory-langgraph|d93f8f9876b740a41eee64b81f1574daa341cc69| Same53/53 synthetic state suite; tie |
|memory-gbrain|245b8a36f1368b4adc67f1cae549b575a306ceca|experiments/memory/results.json:17/17 exact engine projection checks |
|retrieval-fts|5088e7b7adce682fccac3aa05564dd25699a801b|results/comparison.json:9 exact checks,24-query recall@5=0.6667 |
|retrieval-hybrid|4288e544e06f1048162770fe3abdd059e06d79cc| Same exact checks, recall@5=0.8333; historical/ineligible MiniLM |

`ui-openui/results/gemma-token-comparison.json` records12 static requests: baseline input/output158/161; OpenUI818/148; wrapped845/173; json-render4254/242. Only fixed output specs are equally controlled. Inputs are unequally optimized; json-render default JSONL-patch prompt mismatches snapshot output. No total-efficiency/live-generation/latency winner is established. Native82/84/36 exports include helpers; seven custom entries were tested. [Measured UI report](ui-library-comparison.md), [memory results](memory-experiments.md), [retrieval results](retrieval-experiments.md).

[Google receipt](google-gemma-verification.json): metadata/count200, native generation500 twice, compatible plain200 with reasoning separated, clean JSON200 without markup. Provider-specific usage totals stay as returned; smoke timings are not app latency. [OpenRouter receipt](gemma-verification.json) retains valid auth/upstream429. These support the temporary transport, not universal schema enforcement or18-scenario quality. The original [scorecard](experiment-scorecard.md) is a pre-result rule, not current all-pending status.

Current frontend/backend manifests and source files exist but do not establish acceptance. Current map code labels its lat/lon pin plot “Coordinate view · no basemap”; Q7 geographic-map suitability stays pending. The main live implementation must never silently substitute fixture output on provider failure.

## Coordinator diagram brief

Show three compatible layers: React/CopilotKit enterprise shell + AntD/ECharts → AG-UI → Python bounded workflow → injected replaceable RetrievalProvider. Gemma emits compact ViewPlan references; server-owned ResultSet/EvidenceRef feed every panel. Optional OpenUI/json-render are composition adapters, not separate model stacks; label A2UI's wrapper test boundary. Mark main tracks “implementation in progress” and retrieval “provisional/user inspection pending.”

Draw immutable source/effective correction/rule authority and shared attributed operational assertions separately from private owner-scoped facts/exchanges/entity receipts. Canonical shared A→B reads work before index rebuild; no private transcript arrow enters shared context. Distinguish per-message admission, accepted-fact capsule refresh and10/20/overflow dialogue compaction. Long-term always600 private+200 shared header, selected400 private+800 shared=2K; short-term1K; fresh evidence2K. Show overhead/current request/output separately. gbrain is optional/unadopted; workflow engine remains pending owner reconciliation until this log is updated.

Add normal evidence viewer plus explicit-admin diagnostics with bounded memory/save/update/provenance/compaction and retrieval schema/tables/counts/query/selected-omitted previews. Badges53/53,17/17,9 exact and161/148/173/242 static output tokens must name the test boundary. Only Gemma/temporary Google-compatible route/global 30 RPM in the selected path; no MiniLM.

Current proposals: [10](../diagrams/10-architecture-and-evidence-for-review.png), [11](../diagrams/11-prompts-and-agent-flow.png), [12](../diagrams/12-contextual-retrieval-operating-flow.png), [13](../diagrams/13-memory-save-and-summary-flow.png), [14](../diagrams/14-long-term-compression-and-retrieval.png). Coordinator owns flat final PNG placement; editable sources remain in agent-memory/diagram-sources. Diagrams cannot resolve an unmeasured quality tie or imply finished functionality.

Documentation checks: all89 local links in the four owned documents and two updated skills resolved; all18 scenario rows are present; both skills passed the official skill-creator validator. Saved token/workflow/retrieval numbers and both library eight-check browser summaries matched their raw JSON receipts. The flat diagram directory contains only PNG files. Coordinator explicitly accepted leaving the workflow adapter pending owner confirmation; that does not block this documentation handoff and may receive a focused later update.
