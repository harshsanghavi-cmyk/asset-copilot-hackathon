# Acceptance plan — proposed, not executed

Evaluate each fact, citation and requested visual separately. Sample expected
answers are fixtures in the evaluation guide, never runtime retrieval content.
Use exact decimal semantics for quantities and explicit date windows.

| Scenario | Principal acceptance check |
|---|---|
| Q1 | Latest inspection, delta threshold, author, planned shut-in and stale status |
| Q2 | Four effective down wells; explain unknown causes; requested table |
| Q3 | Thirteen readings, two down markers; temperature and ambient series |
| Q4 | Six true spills/15.1 bbl; formal false-positive correction excluded |
| Q5 | 21 observed down days; hot absolute reading does not imply production |
| Q6 | Correct top three and 49/42/42 days; explicit window and bar chart |
| Q7 | Four correct map locations after correction filtering |
| Q8 | Correct area-by-month spill cells and totals, including zeros |
| Q9 | Four breaches/$5,000 fine; separate still-pending actions and met rule |
| Q10 | Report-only containment delays found across the requested area |
| Q11 | Same user's prior selected wells recovered across a new chat |
| Q12 | Original retained, corrected production used, conflicting note visible |
| Q13 | Volume correction recomputes class/deadlines and contradicting old report |
| Q14 | T350-only rule adds its qualifying well; T200 remains unchanged |
| Q15 | Both corrections propagate to different users with attribution |
| Q16 | Shared planned downtime visible; private prior-well list does not leak |
| Q17 | Contradictory claims persisted and surfaced as unconfirmed |
| Q18 | Ordinary conflicting notes do not silently override spill detection |

Additional user-requested checks:
- One question produces 4–5 coordinated blocks with consistent source revision,
  dates, units and source references, plus a concise problem-solving explanation.
- Explicit requested visuals are honored. A numeric scalar need not create a chart.
- A malformed block is rejected without executing model-generated code.
- Switching users clears visible chat state and scopes every private-memory read.
- Compaction boundary: exchanges 9, 10 and 11, restart, failed turn and duplicate
  request. Compaction never duplicates, drops unresolved tasks or loses entity IDs.
- Long-term budget: loaded memory stays within chosen cap while originals remain
  retrievable; explicit remember, expiry, conflict, supersession and forget policies.
- Correction racing a query yields one consistent revision or a clear refresh;
  cached charts cannot retain old values while prose uses corrected ones.
- New same-format dataset: duplicate identical records dedupe; divergent IDs
  produce a conflict; no record-count or hardcoded-well assumptions.
- Missing report, ambiguous extraction, unsupported model mode and rate limiting
  produce clear uncertainty/errors, never fabricated successful answers.

Record latency, token use, cost, request count, retrieval coverage and citation
resolution per run. Establish realistic targets after the compatibility spike;
there are no measured copilot benchmarks yet. Persist raw outputs for reproducibility.

Use original sample state for standalone Q1–Q10. Prepare explicit per-scenario
state for Q11–Q18 and the follow-on corrections. Tests that need prior events must
state their dependencies; resets must not erase the source dataset.
