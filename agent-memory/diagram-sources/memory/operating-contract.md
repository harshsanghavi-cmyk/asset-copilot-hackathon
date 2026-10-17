# Memory operating flow — final PNG brief

Coordinator owns final PNG generation and placement in flat `diagrams/`. This is
an image brief only; no app implementation or new model evaluation is claimed.

Make a readable landscape enterprise architecture image titled **“How the copilot
remembers and answers”**. The main story must be operational flow, not a row of
framework logos. Use short labels, clear arrows and generous spacing.

1. **Every exchange:** user + trusted identity/reference date → durable private
   message → Gemma planner with memory proposals → deterministic scope/evidence
   validation. Clear remembers/corrections commit before “saved”; ordinary useful
   assertions stay attributed claims. Do not draw an autonomous model directly
   writing authoritative truth.
2. **Three durable stores inside application-owned SQLite:** violet private
   preferences/transcript/exact entity receipts; green shared asset/type/team/org
   claims/plans with authors, validity and conflicts; amber structured correction
   and rule authority with originals and revision. All authorized users see shared
   facts; A's conversation/entity set never flows to B. Source records/manuals/SOPs
   are immutable evidence beside these stores, not squeezed into private memory.
3. **Four capabilities:** `read_context`, `query_records`, `read_evidence`,
   `write_knowledge`. Exact calculations and applicable corrected/rule values feed
   immutable results at one revision. Query evidence includes SOP text and report
   spans; shared claim text appears once in long-term context. Gemma answer + visual plan → local validation →
   coordinated panels with citations. ViewPlan is chain output, not a fifth tool.
4. **After completion:** exact entity/result receipts saved every exchange. At
   completed exchange 10/20, background compaction covers 1–7/1–17 and retains the
   newest three; raw archive is preserved. Overflow can trigger earlier; failed
   summary uses prior version + deterministic receipts and scoped retrieval.
5. **USER CONTENT CAP: 5,000 tokens = LONG-TERM 2,000 + SHORT-TERM 1,000 + RETRIEVED
   CONTEXT 2,000.** Proposed long-term split: private1,000 (capsule600 + relevant
   archive400), shared1,000 (applicable claims/rules/corrections800 + provenance/
   validity/conflict pointers200). Short-term: rolling summary400 + recent user/
   assistant dialogue500 + compact reference handles100; no tool dumps/reasoning.
   Retrieved: results600 + rule/SOP excerpts650 + report spans550 + coverage/
   citations200. Show shared facts only once, in long-term, with references from
   evidence as needed. Persona/tool instructions, the current request, output and
   framing are separately counted overhead, not a hidden former larger budget.
   No silent increase: a targeted fetch REPLACES context inside its cap; otherwise
   clarify or return supported partial evidence. These splits are proposed, not
   measured optimal sizes or a universal sufficiency result.
6. **Honest evidence corner:** explicit journal and actual LangGraph each53/53
   fixed-proposal state checks; isolated gbrain projection17/17. Draw gbrain only
   as an optional dashed shared projection, labelled **“tested, not adopted;
   semantic benefit untested”**. It never owns corrections or private history.

Use the only runtime model label **Gemma 4 31B**. Default ordinary exchanges use
two logical model calls (plan and answer); persona/extraction instructions are
included in those calls. A background compaction call runs per10 completed
exchanges, not an extra extraction call every turn. All calls share30RPM.
No other encoder, embedding model or reranker may be shown as selected.

Keep source registry, rule/correction authority and shared claims visually distinct.
Show the small cross-user example: **A/Jake saves WELL-0007 planned work → shared
claim → B/Michael retrieves it with Jake attribution**. Beside it, show a blocked
arrow for **A's “three wells yesterday” → B**. Cross-team operational sharing is
allowed; team ownership is applicability, not an invented access restriction.

The detailed contract is `agent-memory/memory-operating-contract.md`; token values
are proposed ceilings, state/projection check counts are measured, and live memory
extraction/summary quality remains untested. Avoid claims of a completed copilot.
The 5K content cap is the user's requirement; internal splits are engineering
proposals. Full raw archives/entity receipts/result arrays stay server-side.
