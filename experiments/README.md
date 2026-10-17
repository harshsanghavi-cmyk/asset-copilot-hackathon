# Experiment and implementation review pack

Start with [STATUS](STATUS.md), the root [implementation roadmap](../FINAL_PLAN.md) and [current decisions/evidence](../agent-memory/final-decisions.md). Research/comparisons are complete. Main frontend, backend and retrieval are **authorized and in progress**, with integrated correctness still to demonstrate. Retrieval remains provisional until its inspection viewer supports user review.

## Browse the evidence

| Folder | Review contents |
|---|---|
| [01 — Generative UI](01-generative-ui/README.md) | Real rich direct AG-UI/CopilotKit/A2UI fixture screenshots, wide/mobile changes, shared selection/evidence drawer |
| [New library comparison](01-generative-ui/library-comparison/README.md) / [full report](01-generative-ui/library-comparison/REPORT.md) | OpenUI/json-render independent composition/reordered/evidence screenshots; native catalogs, Gemma static counts and configuration caveats |
| [02 — Q&A/memory](02-qna-memory/README.md) | Shared/private authority, explicit/LangGraph state tie and fresh gbrain engine trial |
| [Memory operating contract](02-qna-memory/memory-operating-contract.md) / [selective loading](02-qna-memory/long-term-memory-loading-decision.md) | Per-message memory admission, commit-before-save,10-exchange summary,800 always+1200 selected long-term and canonical records |
| [03 — Data/retrieval](03-data-retrieval/README.md) / [operating contract](03-data-retrieval/retrieval-operating-contract.md) | Exact SQL, source/report evidence, four scoped tools, material audit, provisional replaceable candidate and ineligible historical MiniLM |
| [Project skills](SKILLS.md) | Reusable instructions; current memory/retrieval skills point to5K and provider contracts |
| [Submission drafts](../submission/README.md) | Two-page write-up,≤5-minute video, results template and portal checklist; no publication/submission |

The export hierarchy is preserved. The reports directory contains copied research/audit/paper/experiment snapshots, not another authoritative decision registry. They may retain older provider/budget/recommendation/planning-only text. Use [AGENTS](../AGENTS.md), [current model policy](../agent-memory/model-policy.md), [API seam](../agent-memory/backend-api-contract.md), operating contracts and FINAL_PLAN for current direction. Raw code/JSON receipts and exact commits remain in the isolated worktrees named by each report; copied PNGs do not replace those measurements.

## Current architecture images

- [10 — Composition/evidence overview](architecture-images/10-architecture-and-evidence-for-review.png)
- [11 — Prompt roles and updates](architecture-images/11-prompts-and-agent-flow.png)
- [12 — Contextual retrieval and compact budget](architecture-images/12-contextual-retrieval-operating-flow.png)
- [13 — Memory save/summary timing](architecture-images/13-memory-save-and-summary-flow.png)
- [14 — Long-term projection versus exact retrieval](architecture-images/14-long-term-compression-and-retrieval.png)
- [09 — Measured data/key overview](architecture-images/09-data-overview-and-keys.png)

Images00–08 preserve earlier exploration and may show superseded choices. Current images are explanatory proposals, not acceptance receipts. Coordinator owns final PNGs in flat diagrams/; editable sources stay in agent-memory/diagram-sources/.

## Result boundaries

Screenshots use synthetic fixture values, not final dataset/Gemma answers. OpenUI/json-render render the same AntD/ECharts panels, so similar appearance is expected; independent composition/guards were tested. Equivalent output specs measure161/148/173/242 Gemma tokens for baseline/OpenUI/wrapped/json-render, with no generation or latency ranking. Unequally optimized inputs and json-render default JSONL-versus-snapshot mismatch prevent an optimized total-efficiency claim.

Explicit/LangGraph 53/53 is a state-behavior tie; gbrain 17/17 is an exact projection probe, not a superior memory score. Nine exact retrieval checks/full linked-report coverage differ from top-k prose recall. Historical MiniLM gains remain historical measurements but integration is ineligible under Gemma-only. Google plain/clean-JSON smoke success proves limited transport compatibility, not strict schema or all 18-scenario correctness.

Main implementation/diagnostic pages are being built by assigned owners; this documentation pass changes no application code. Follow STATUS and the roadmap for remaining live integration, source support, privacy, budget, visual and unseen-data gates. Credentials, dependencies, caches, databases and raw dataset copies are excluded from this review pack/public-ready artifacts.
