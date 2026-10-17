# Asset Intelligence Copilot

## Current scope

The user authorizes supervised GPT-6.1-sol research sessions (medium/high effort),
architecture comparisons, diagrams, skills, and a final action plan. Complete this
planning phase for user review before application implementation. Use agent-memory/
for shared findings and diagrams/ for reviewable artifacts; do not edit another
worker's assigned files. See agent-memory/README.md for coordination.
The objective is a strong hackathon entry: reliable evidence-based answers,
correctly scoped learning and memory, and appropriate inline visuals.

## Read before future work

- Original supplied brief: `FlytBase AHC SWE Hackathon#17Oct.docx`.
- Searchable full extraction: `docs/hackathon-brief.txt`.
- Challenge: `dataset/01-problem-statement.md`.
- Schema and joins: `dataset/02-dataset-guide.md`.
- All 18 scenarios: `dataset/03-evaluation-queries.md`.
- Setup guidance: `dataset/04-prerequisites.md`.
- Project skill: `skills/asset-intelligence-copilot/SKILL.md`.
- Source revision: `docs/dataset-source.json`.

The dataset is an independent local clone in `dataset/`, ignored by the outer Git
repository. Preserve its originals and MIT license. Future repository packaging
must make dataset acquisition reproducible; do not assume the ignored clone ships.

## User's architecture choices

- `skills/`: reusable project instructions.
- `backend/chains/`: LLM orchestration and OpenRouter integration.
- `backend/prompts/`: YAML with top-level `input:` and `prompt:`; prompt prose
  lives in Markdown. Establish a single source of truth rather than duplicate text.
- `backend/output_parsers/`: validation and bounded output-fixing parsers.
- `frontend/`: React; no implementation or framework dependencies chosen yet.
- Copilot model: `google/gemma-4-31b-it:free` through OpenRouter.
- Use OpenRouter JSON output capabilities, checked against the actual endpoint;
  validate locally and never claim schema enforcement the endpoint lacks.

## Invariants

1. Derive production from corrected wellhead minus ambient temperature using the
   applicable manual: T200 >=15 C, T350 >=20 C. Recorded status can be stale.
2. Downtime is 7 days per observed non-producing weekly inspection in the period.
   Missed inspections add zero; maintenance downtime_hours is a different metric.
3. Follow maintenance.report_file; report names vary. Containment and other facts
   may exist only in report prose. Cite both source records and applicable rules.
4. Formal corrections retain originals, author, timestamp, reason and scope.
   Every later answer, aggregate and visual must use the effective corrected values.
5. Shared asset knowledge and corrections reach all users. Private conversation
   memory is keyed by user and persists across their sessions without leaking.
6. Type-wide overrides apply only to that type and are attributed to the user,
   distinct from the original manual. Preserve validity periods.
7. Conflicting claims remain visible and unconfirmed where appropriate. An ordinary
   note is not automatically a formal correction. Do not silently pick a user.
8. Use deterministic calculations for totals, rankings and deadlines; the LLM
   explains results. A top-k document search cannot establish a fleet-wide total.
9. Generalize ingestion and reasoning to additional same-format test data.
   Never hardcode example answers, well IDs, area counts or report filenames.
10. Honor explicit visual requests. Support status cards, tables, line/bar charts,
    maps and heatmaps inline. Use well IDs and person/area/team display names.

## Known source discrepancies

The supplied DOCX uses 17 Oct 2026 as today; the cloned guide and scenarios use
16 Oct 2026. Its Q6 explicitly specifies 16 Jun–16 Oct. Make the reference date and
query bounds explicit; evaluate each scenario with its stated window. Do not let
the machine clock or an implicit default silently change the answer.

The DOCX requires a maximum two-page write-up; the repo says 2–3 pages. Use the
stricter two-page target unless organizers clarify. Video maximum: five minutes.
Public repository and an open-source license are required for submission; neither
publishing nor submitting is part of the current task.

## Future acceptance criteria

Evaluate Q1–Q10 independently against original data. Run Q11–Q18 in their stated
sequence with isolated memory fixtures; verify corrections propagate and private
history does not. Evaluate factual values, evidence and visual choice separately.
Record actual failures and model usage/cost. Unknown causes and missing evidence
must stay explicit. Do not claim a complete copilot from scaffolding alone.

## Diagram artifact rule

The user requires diagrams/ to contain final PNG files only. Put editable Mermaid
and image briefs under agent-memory/diagram-sources/<track>/ instead.

Latest user rule: diagrams/ is a FLAT folder of final .png images only. No
subfolders, Mermaid, README, briefs or other files. Workers must not create
anything in diagrams/; coordinator owns final image placement there.

## Authorized experiment phase

The user's latest instruction permits isolated candidate prototypes and benchmarks
on separate experiment/* branches before choosing a winner. Locations and owners
are recorded in agent-memory/experiment-branches.json and experiment-policy.md.
Main backend/frontend implementation still waits for final-plan review. Workers
may implement, install isolated dependencies, run tests and commit their own
experiment branch artifacts only. Raw dataset and root secrets remain untouched.

## Recommendation standard

The user requires deeper primary-paper/case-study research, explicit cross-user
shared remembered knowledge, and separate-branch experiments for credible rival
approaches. Recommend complete compatible combinations, not unrelated frameworks
as if mutually exclusive. Findings must distinguish documented capabilities,
local measured results, inference, ties and untested options. Shared operational
facts are broader than corrections; private conversation references stay private.

## Session cap and enterprise UI priority

After an app crash, the user imposed a maximum of FIVE concurrent Codex sessions
including the main coordinator. Resume existing work rather than duplicate tasks;
reuse/release completed workers before any additional task. Preserve experiments.

The user explicitly rejects choosing a minimal UI merely because it is simpler.
Prioritize rich enterprise components, standard protocols, composable multi-panel
answers, interactions, accessibility and consistent design. Evaluate CopilotKit +
AG-UI, A2UI combinations and suitable free open-source component libraries. Direct
AG-UI remains a baseline, not the preferred option by default. Keep every claimed
capability tied to real tests, including the component library/catalog integration.

Session-cap clarification: the five-session limit applies to THIS PROJECT only,
including its coordinator. Other user projects are independent and must be left alone.

## Exclusive copilot model and immediate priority

The user now requires google/gemma-4-31b-it:free as the ONLY model in every
copilot layer, including extraction, chunking decisions, retrieval assistance,
memory and answering. Do not use MiniLM or any other embedding/reranking/model.
Deterministic splitting, SQL and lexical text search are allowed. Historical
comparison artifacts may remain as evidence, but other-model candidates are no
longer eligible for integration. Coding-agent GPT-6.1-sol sessions are orchestration
tools, not copilot runtime models. Pause unrelated experiments while coordinator
confirms the newly supplied Gemma key/provider behavior. Never expose secrets.

## Temporary direct Google provider, verified

User authorized their Google AI Studio key for the same Gemma 4 31B model. Use
model gemma-4-31b-it with Google's OpenAI-compatible base URL for now; successful
plain generation and locally validated clean JSON were observed. Native
generateContent returned HTTP 500 in this run. Evidence is in
agent-memory/google-gemma-verification.json. Enforce a shared maximum 30 RPM
(user-provided quota) across all copilot requests. No other runtime model is allowed.
User asks to resume planning/diagrams and compare actual rich UI appearance and
flexibility. Current experiment scope remains isolated branches, not main app.

## Latest context budget and memory timing

User replaces the prior16K proposal with a5K content cap:2K long-term memory total(private+shared),1K short-term summary plus user/assistant text,and2K retrieved evidence. Persona/tool schemas,current request and output are separately counted and disclosed; no silent budget expansion. Original durable records remain outside this loaded-context cap. Check useful long-term memory proposals on every user message; validate explicit remembers/corrections and commit before acknowledgement. Ten-exchange summarization is a separate short-term trigger, with earlier overflow compaction. See the memory-operating-contract.md and retrieval-operating-contract.md in agent-memory/ for current details.

## UI implementation authorized

The user now authorizes main frontend implementation by the existing UI worker: CopilotKit+AG-UI,AntDesign/ECharts, asset theme drawn from /home/harshsanghavi/Desktop/copilot-revive,session sidebar/search/automatic titles and polished animated multi-panel chat. UI worker owns frontend/,agent-memory/ui-implementation.md and experiments/04-ui-implementation/. Backend implementation remains pending architecture review. Frontend fixtures must not be represented as liveGemma/backendbehavior; no secrets or modelcalls inbrowser.

## All three implementation tracks authorized

User now explicitly approves main Q&A/memory backend, deterministicSQL ingestion/retrieval, liveGemma wiring to frontend, and detailed storage/retrieval viewer. Earlier planning-only restrictions are superseded for these tracks. UI worker owns frontend except frontend/src/retrieval-viewer/. Q&A worker owns backend application/chains/prompts/output_parsers/memory/API integration. Retrieval worker owns backend/retrieval/,backend/ingestion/,frontend/src/retrieval-viewer/ and data-viewer evidence/docs. Coordinate API contracts before concurrent edits; do not modify another owner files. Inspect referenceCodexsession01a13a2d-e330-76e2-9bd0-6f05fd55ba5b only with bounded streaming/chunk reads; avoid launchinganotherCodexsession or unbounded transcript/JSONloads. KeepGemma-only policy and shared30RPM quota. No publishing/submission authorized.

## Retrieval remains provisional and replaceable

The user explicitly has not accepted the current retrieval approach as final. Implement it behind an injected RetrievalProvider with versioned typed queries, ResultSet/EvidenceRef/coverage/revision outputs. Q&A, memory and chat must not depend on SQLite tables, FTS internals or ingestion layout. The detailed viewer must make source-to-storage mappings, enrichment, effective values, query traces and selected/omitted evidence inspectable before user review. Keep ingestion/index rebuild replaceable and preserve raw sources.

## Admin diagnostic page authorized

User requests separate admin HTML/page showing private/shared long-term memory, save/update times, provenance and compaction status; plus query-driven retrieval traces, searched tables/schema/counts and short row/evidence previews. Retrieval worker owns viewer components in frontend/src/retrieval-viewer/; UI worker owns admin.html entry/routing/theme and frontend/server/ self-hosted CopilotKit runtime; backend worker owns scoped read-only admin memory endpoints. Keep administrative inspection explicit and separate from normal chat identity. Paginate/limit previews; no secrets, complete-table browser dumps or arbitrary SQL execution.

## Latest provider override: Google AI Studio only

The user explicitly says to discard OpenRouter and use the supplied Google AI Studio credential. This supersedes all earlier authorization to probe or use OpenRouter. Active runtime must use Google AI Studio with gemma-4-31b-it only; no OpenRouter selection, requests or fallback. The credential provider change does not authorize a different Gemini model. Preserve historical receipts as history; never expose credentials.

## Required Google integration

The user explicitly requires langchain-google-genai ChatGoogleGenerativeAI (https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai) inside the existing LangGraph workflow, replacing the hand-built HTTP transport. Use Google AI Studio/Developer API explicitly, gemma-4-31b-it only, no Vertex/OpenRouter/other models. Backend owner owns the SDK migration; stop independent custom HTTP probing. Retain shared rate limiting, prompt input validation, bounded local output parsing and accurate failure receipts. Verify a real greeting and dataset answer through UI before claiming repaired.

## Latest selected model: Gemma 4 26B

The user explicitly authorizes replacing Gemma4 31B with Gemma4 26B. Active runtime model is now `gemma-4-26b-a4b-it` through Google AI Studio using ChatGoogleGenerativeAI. This supersedes previous31B-only restrictions in every runtime layer. No OpenRouter or automatic model fallback. Keep31B test receipts as historical evidence. Shared30RPM limiter and explicit token accounting remain.

## Final dataset release — 17 Oct update

The user explicitly authorized pulling the new dataset and running its final questions.
Current source revision: `009e2b596782150f420021f9472ab37e3a2953ee`.
Read `dataset/test-data/README.md` and `dataset/test-data/final-questions.md`.
The final snapshot is `dataset/test-data/dataset`: 600 wells, seven areas, reference
15 Jan 2027. It replaces the sample snapshot; never union their overlapping IDs.
Preserve `dataset/sample-data` and its 18-question regression separately.

The coordinator configures a separate test index and dataset namespace. Do not
silently mix sample memories, dates, results or goldens into the final snapshot.
Optional type/team histories, late-entered records, data corrections, T500/ESP rules,
new operator notes and revised SOP/MOC/recall documents must retain their provenance.
Missing pressure or production-volume measurements must remain missing; temperature
is not reservoir pressure or measured oil production.

Latest execution instruction: run the final 11 scenarios through the backend API,
saving full answer envelopes in the actual app DB as separate named sessions visible
in the UI. Do not use browser automation to generate this batch. Independent cases
may run concurrently under the shared Gemma limiter; preserve ordered turns and
cross-session dependencies. The selected runtime remains Google AI Studio Gemma26B.

## Latest runtime and submission instruction

The user now explicitly requires **Gemini 3.5 Flash Lite** through Google AI Studio
and the official LangChain Google SDK. This supersedes every prior Gemma-only rule
above and in project skills. Use the actual model ID verified from the provider.
Do not continue generating with Gemma. Keep model-specific quotas, usage and attempts
explicit; no other runtime model is authorized.

Run all 11 final scenarios (21 prescribed turns), repair failures and retest until
measured quality reaches at least 80–90%, with facts, evidence, memory and visuals
assessed separately. Preserve hard failures and source provenance; do not count mere
successful delivery or unverifiable claims as accuracy. Store full answers in real
app DB sessions visible in the UI. The coordinator owns the single backend batch.

After quality validation, create the required two-page submission document: page one
explains the approach with review diagrams 10, 12, 13 and 14; page two presents actual
results. Update diagrams to match the selected runtime and final implementation.
Do not publish or submit externally without a separate user instruction.

## Final user-accepted delivery

The latest explicit user choice is Gemini 3.5 Flash Lite via Google AI Studio, superseding earlier Gemma-only requirements. All 11 final scenarios (21 turns, 14 sessions) have completed delivery: 10 complete replies, 11 partial replies, zero fatal request errors. The user accepted current partials and requested completion, UI persistence, Google Doc update and source publication. Do not claim an established 80–90% semantic pass rate. The final renderer contract validates all 21 saved envelopes; two empty unverified payloads received audited presentation-only repairs. The authoritative submission includes existing diagrams 10, 12, 13 and 14 only, all 11 questions and answer JSON code blocks, no tables, and no strict page limit.
