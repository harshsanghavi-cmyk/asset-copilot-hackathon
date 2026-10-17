# Shared research and experiment workspace

The coordinator owns the final plan, AGENTS.md, integration contracts, submission/
and final images. The user authorized research and isolated candidate benchmarks
before the main application build. Read the latest AGENTS.md and experiment-policy.md.

| Track | Owned report | Source diagrams | Experiment branches |
|---|---|---|---|
| UI research (complete) | ui-research.md | diagram-sources/ui/ | none |
| Memory research (complete) | memory-research.md | diagram-sources/memory/ | none |
| Retrieval | retrieval-research.md, retrieval-experiments.md | diagram-sources/retrieval/ | retrieval-fts, retrieval-hybrid |
| Material data audit | data-audit.md, data-audit-inventory.json | diagram-sources/data-audit/ | none |
| Deep architecture review | architecture-review.md, memory-experiments.md | diagram-sources/review/ | memory-explicit, memory-langgraph |
| UI experiment session | ui-experiments.md | none | ui-agui, ui-copilotkit |

Workers edit only their assigned paths/worktrees. Read peer reports at natural
checkpoints and reuse shared findings. Final synthesis resolves contradictory
proposals; a checkpoint recommendation is not an empirically proven winner.

`diagrams/` is FLAT and contains ONLY final PNG files. No subfolders or source
files. Workers must not create anything there; keep Mermaid, briefs and drafts
under agent-memory/diagram-sources/<track>/. Coordinator owns PNG generation.

Research must include relevant primary papers, official interfaces and actual
case studies. Explain where their results transfer and where they do not. The
DOCX's two papers are GenUI-Harness (2610.11123) and GateMem (2606.18829); these
are directly relevant to generated UI and multi-principal memory, respectively.

Where credible candidates remain, use the isolated experiment/* worktrees in
experiment-branches.json. Keep fixtures/scoring comparable and preserve raw
results, commands, versions and commit IDs. Distinguish deterministic tests,
integration tests and live model evaluation; no forced winner from ties or blocked
runs. Do not turn vendor benchmark claims into this project's results.

Main backend/frontend code stays unchanged during this phase. No secrets in
reports/commits, no raw dataset mutation, no external publication. Install/run only
isolated experiment dependencies/services. Only the retrieval experiment owner
may use the selected free OpenRouter endpoint under experiment-policy.md's budget.

Important product requirements: 4–5 panels within one answer; practical domain
expert persona; ten-exchange summary; always-loaded bounded remembered-fact
representation; durable private history; shared asset/type/team/org knowledge;
explicit correction authority, conflicts, scope and source provenance; full-scope
exact numerical calculations; new-data ingestion without example-answer hardcoding.
