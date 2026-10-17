# Candidate experiment policy

User authorized separate branches and real comparisons where multiple candidates
are credible. Scope: isolated experiments, not main-app implementation.

| Pair | Owner | What to compare |
|---|---|---|
| ui-agui / ui-copilotkit | UI track | Same five-panel payload, actual protocol/runtime, errors and user isolation |
| retrieval-fts / retrieval-hybrid | Retrieval track | Same corpus/query fixtures, exact SQL + FTS vs exact SQL + hybrid semantic retrieval |
| memory-explicit / memory-langgraph | Architecture reviewer | Same shared/private ledger policy, explicit workflow vs checkpointed LangGraph |

Paths/branches are in experiment-branches.json. Main root has uncommitted research
artifacts, so workers read them by absolute path; do not expect them in base HEAD.
Each pair must use the same fixture corpus, scoring definitions and model outputs
where isolating transport/state behavior. Distinguish deterministic harness tests,
real integration tests and real model evaluations. Never call a mocked model run
proof of answer quality. A tie or blocked test is a valid result.

Primary papers and actual documented case studies inform design; vendor benchmarks
are not local results. Report transferable lessons, limitations and mismatches.
Avoid straw-man baselines and thresholds chosen after seeing candidate results.
Record versions, commands, git commits, elapsed time, failures and raw results.
Keep .env, API credentials, raw dataset copies, packages/caches and generated DBs
out of commits. No paid cloud services, model substitutions or publishing.

Only retrieval track may make bounded live calls to the already-selected free
OpenRouter Gemma model, if the existing root key is configured. Maximum 12 calls
for the initial pair, no secret logging. On provider/quota failure, report blocked
live evaluation and preserve deterministic results; no retry storm. All other
tracks use fixed or replayed valid/invalid payloads and identify that boundary.

Experiments may change recommendations only within what they actually measure.
A few fixtures do not establish production readiness or universal superiority.

Additional shortlisted contender: experiment/memory-gbrain, owned by architecture
reviewer, tests a fresh gbrain shared-knowledge adjunct with the same canonical
ledger/privacy policy. Never use an existing personal brain. Raw/lexical integration
without embeddings must not be labeled semantic quality validation. If an extractor
or embedding capability needs unavailable provider access, document that boundary.
