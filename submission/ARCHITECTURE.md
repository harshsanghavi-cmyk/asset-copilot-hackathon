Asset Intelligence Copilot
Gemini 3.5 Flash Lite · 600 wells · Reference date: 15 January 2027

Approach and architecture
The copilot turns an operator’s question into scoped data queries, an evidence-backed explanation, and inline visual components. It combines structured inspections and work orders with maintenance reports, operator notes, manuals and SOPs. Numerical results are computed by tools; the model selects the investigation and explains what the records support. Missing measurements stay missing rather than being replaced with an unrelated proxy.

The active application uses React, CopilotKit and AG-UI, with Ant Design tables, ECharts charts and Leaflet maps. The backend is FastAPI with a bounded LangGraph workflow and Google AI Studio’s Gemini 3.5 Flash Lite through the official LangChain Google integration. A response can contain several coordinated panels, not just one component. Sessions, answers, source references and result sets are saved so the same response can be reopened in the UI.

Diagram 10 — Overall copilot architecture

The system separates the conversation interface, the reasoning workflow and the data provider. The planner resolves the requested assets, time window and analysis, then proposes typed operations. The application validates those operations, executes them against the effective records, and supplies a bounded context to the answer maker. The maker returns prose and a UI plan referencing server-owned results. Local checks validate source handles, numerical values and visual encodings before the trusted React component catalog renders the answer.

Diagram 12 — Source-to-context retrieval flow

Ingestion streams the dataset folders into an indexed SQLite representation while preserving source files, record IDs and report links. Typed fields support exact totals, rankings, time windows and joins; lexical source search locates relevant prose and SOP sections. Corrections overlay the originals rather than deleting them. Type and team histories are resolved at the relevant event date, late-entered records are ordered by their observation dates, and operator notes retain their timestamps. Dedicated assessments join the relevant records with the supplied gas-response, bypass, recall and regulatory rules. Full result arrays stay on the server; the model receives compact evidence and scope summaries.

Diagram 13 — Memory writes and conversation summaries

Gemini proposes remembered facts from the current user’s own statement. The application checks the quoted source, subject, scope, validity dates and conflicts before a transactional save. Shared asset observations, plans and corrections are available to other users; personal preferences and private conversation references stay user-scoped. A save is acknowledged only after a commit receipt exists. Firsthand reports, hearsay and contradictory claims remain distinguishable. Raw user and assistant messages are stored privately, and a rolling summary is scheduled after ten completed exchanges or earlier context overflow.

Diagram 14 — Bounded context without deleting the record

The admitted content budget is 2,000 long-term-memory tokens in total, 1,000 conversation tokens and 2,000 retrieved-evidence tokens. Long-term context includes a compact user/shared view and relevant facts; recent dialogue and a versioned summary provide short-term continuity. The canonical facts, original conversation and source evidence remain durable when items are omitted from the prompt. Google token counting measures admission, and compaction removes whole optional items rather than silently changing facts. Instructions, tool schemas, the current question and generated output are accounted for separately.

Implementation notes
The four figures above are the original requested diagrams. Earlier model labels or research-check counts inside those design images are historical; the active runtime is Gemini 3.5 Flash Lite and the active dataset contains 600 wells. Research comparisons are not claimed as final scenario accuracy.

Production status uses corrected wellhead-minus-ambient readings and the applicable type manual, including historical type changes. Recorded metadata can be stale. Source documents define the relevant regulatory windows and deadlines; the publication date of a letter is not automatically the period of the incidents it covers. A statement about absent reservoir pressure or produced-oil volumes does not authorize using equipment ratings, temperature or spill barrels as substitutes.

Results — all 11 scenarios
Each question below will be followed by the actual saved response JSON. Multi-turn scenarios retain their separate users and sessions. Complete, partial and unavailable-data outcomes remain distinct; successful model delivery alone is not a claim of factual correctness.

