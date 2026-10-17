# Layer-by-layer QA scoring

This is our engineering acceptance rubric, not the organizer's points. Evaluate actual run receipts and raw source oracles. Never infer correctness from valid JSON, an HTTP200, or a rendered card.

| Layer | Weight | Required evidence |
|---|---:|---|
| Planner | 15 | Correct intent, entities, date window, user scope, operations and required evidence sources; no default-status substitute for report questions |
| Retrieval | 20 | Correct eligible records/passages, applicable rules, report joins, relevant conflicting claims; complete population when needed; source IDs and coverage/gaps |
| Calculations | 20 | Exact expected values, units, rankings/ties, corrections and deadlines; no truncated population or duplicate joins |
| Answer grounding | 25 | Every required finding/explanation present, supported citations, no contradiction with result rows, calibrated uncertainty, useful domain guidance |
| Memory | 10 | Correct private/shared scope, durable save receipt, original/author/reason preserved, later recall and correction propagation, negative isolation cases |
| UI | 10 | Requested visual type, correct result/column bindings, exact displayed data/units, usable evidence links; actual render verified separately from ViewPlan validity |

For each applicable criterion use PASS=1, PARTIAL=0.5, FAIL=0. Record expected, actual, evidence/run ID and responsible owner. Score is 100 × earned weighted points / applicable weighted points. Split each layer weight equally over its explicitly listed scenario criteria. Do not invent criteria after seeing an answer. Mark non-applicable criteria N/A and exclude them from the denominator.

## Hard failure gates

Any private-data leakage, wrong formal correction/scope, wrong critical numeric answer, unsupported operational claim, narrative/result contradiction, or incorrect semantic visual binding (for example spill_detected labeled as production) makes the scenario FAIL regardless of numeric score. Missing required answer/visual means incomplete, not an overall PASS. An overall PASS requires all applicable required criteria passed and no hard gate.

## Availability and incomplete evidence

Provider HTTP/transport failures are recorded separately with stage/code/attempt. A missing answer has overall BLOCKED/FAILED-DELIVERY and semantic score NOT SCORED; do not call it a hallucination or an accuracy pass. Report completion coverage (completed live scenarios / 18), semantic full-pass count / 18, scored-case average, and untested UI count separately. Never inflate the average by hiding blocked cases. Fixture/unit results are a separate table, not live scenario passes.

## Required execution discipline

- Q1–Q10: independent original-data fixtures, explicit reference date/window.
- Q11–Q18: only dependencies stated in the official scenarios; correct users, new chats and controlled dates. Q11 needs Michael's Q6 history; Q15 needs declared Q12/Q13 corrections; Q16 tests shared knowledge and a negative private-reference case.
- Include the user's exact fleet question as an extra regression: "how many assests we have and where show me there states". Do not change its spelling or interpret a generic status query as a complete answer without scope/count/location evidence.
- Preserve original failed runs and label targeted reruns. Track code/prompt/model revisions and replayed checkpoints; a cached answer is not a new model generation.
- Runtime model is Google AI Studio gemma-4-26b-a4b-it through ChatGoogleGenerativeAI. Luna only orchestrates/scorers tests; it must not generate copilot answers.
- Use the shared request ledger, 30RPM and 16KTPM discipline, current150-attempt integration guard. Do not duplicate active evaluator processes.

## Report format

Write `QA_REPORT.md` beside this file. Lead with timestamp/model/revision, delivery coverage, full semantic passes and outstanding P0/P1 issues. Include all18 rows plus the fleet regression: question, delivery, planner/retrieval/calculation/answer/memory/UI statuses, score or NOT SCORED, root-cause layer, evidence paths, assigned fix. Put provider failures in their own section. Link reviewer findings and raw receipts. For each fix include before/after outcome and targeted retest evidence. Publish partial results immediately and update incrementally; do not wait for the whole batch.
