# QA score and dependency review addendum

Coordinator review of the available receipts; no new model calls. Read with QA_REPORT.md and SCORING.md. These are engineering scores, not organizer scores. A numeric score never overrides a hard failure or means the app is accepted.

| Available answer | Planner15 | Retrieval20 | Calculation20 | Grounding25 | Memory10 | UI10 | Weighted result | Overall |
|---|---:|---:|---:|---:|---|---|---|---|
| Original Q1 envelope |7.5|10|20|0|N/A|0 (wrong semantic binding)|37.5/90 = **41.7/100**|FAIL: missing required explanations and spill flag used as production |
| Original Q2 envelope |7.5|0|20|0|N/A|Not rendered/reviewed|27.5/80 tested points = **34.4/100 provisional**;10 applicable UI points untested|FAIL: narrative says two versus four rows; known repair causes missed |
| Recovered Q5 envelope |7.5|10|20|12.5|N/A|N/A (no visual required)|50/80 = **62.5/100**|PARTIAL: correct21days and result lineage, but missing three weekly-inspection explanation and specified causal context |

PASS=1, PARTIAL=0.5, FAIL=0 for each assessed layer. Q2 calculation is corrected here: the deterministic four-row result is correct; the false count is in answer generation. Original report's calculation failure label must not be read as a SQL arithmetic defect. UI render checks remain distinct from schema/binding review. Scores for undelivered answers are NOT SCORED, with failure stage reported separately.

## Q15 setup dependency matters

The current isolated `runtime/evaluation-memory/corrections.sqlite` contains one accepted shared correction for WELL-0151. It contains **no accepted WELL-0164 temperature correction** at this review checkpoint. Q15 explicitly follows Q12 and Q13. Therefore Jessica receiving an uncorrected WELL-0164 answer in that fixture does **not by itself prove a cross-user memory propagation bug**: the Q12 prerequisite was not successfully committed. Classify this branch as **BLOCKED_DEPENDENCY (Q12)** until a valid correction is committed and replayed. Do not silently seed a successful correction and claim the original live sequence passed. The separate WELL-0151 branch must be checked against its actual committed correction and source evidence.

## Q5 recovery evidence

`runtime/live-evaluation-q5-minimal.json` contains a completed recovered envelope: narrative reports21days in2025, result covers52 matching/evaluated inspections with unknown0 and no aggregation truncation, and has an aggregate lineage reference. It was recovered from durable successful model receipts with **zero new generation** during the validation fix. The original failure remains in attempt_history. The answer does not explain the three weekly observations, hot ambient conditions or the referenced maintenance causes required in the official expected answer. It is a real partial answer, not an unrun case and not a full semantic pass.

## Prioritized fixes

1. Backend: complete the exact fleet question with complete counts/location/status scope and trustworthy bindings; honor the16K input-token quota before generation.
2. Backend: retrieve applicable active notes and repair records for requested operational explanations; do not infer “no known cause” from a truncated evidence pack.
3. Backend/UI: production cards must bind production, not a generic boolean spill flag. Keep raw tool results and narrative cardinality consistent.
4. Backend: repair Q12 live correction setup, then retest Q15 under its declared dependencies.
5. UI: finish readable typography and chronological actual-progress rendering; inspect real answer data against the envelope.

All other unavailable live answers remain failed-delivery/blocked and NOT SCORED semantically. There is no verified18/18 pass claim.
