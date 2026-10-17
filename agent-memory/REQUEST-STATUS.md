# Recent request status

Coordinator checkpoint, 17 October 2026. A deployed feature and a correct generated answer are separate acceptance checks.

| Request | Verified status | Remaining work |
|---|---|---|
| Pull updated dataset | Complete: source revision `009e2b596782150f420021f9472ab37e3a2953ee`, clean upstream clone | None for acquisition |
| Use 600 wells throughout backend | Live API confirms 600 assets, reference 2027-01-15, namespace `asset-field-test-2027-01-15`; default composition also selects the final snapshot | Validate each new domain assessment through real answers |
| Save final 11 scenarios as UI sessions | Single API batch `final600-20261017-1153` running with two concurrent chains; all 14 sessions created, 21 turns scheduled; required same-session turns and Q8→Q9 dependency retained | Complete all turns, review failures, deploy repairs at an idle boundary, then rerun only affected stages/turns |
| Fix gas question's private-history rejection | Pre-planner data-local reference fix deployed | First final run still encountered provider500; post-planner reference interpretation needs further correction for fleet questions |
| Share 2023 data observation | Original fact moved to shared/unconfirmed with original ID, author, source quote and audit history; original sample namespace preserved | No blanket exclusion of 2023 data or cross-dataset copying without identified provenance |
| Correct diagonal coordinate heatmap | Frontend spatial numeric map and backend semantic guard implemented | Final deployed browser verification pending |
| Reliable suggestion pills | Separate genuine Gemma call has a persisted ready result; controls and initial API contract deployed | Fix stale/missing-job state and explicit retry; verify a fresh successful pill flow after dataset switch |
| Handle maker timeout and HTTP500 | Saved questions/stages remain durable; measured context caps deployed | One bounded transient-provider retry, explicit partial state, targeted recovery and real successful receipt still needed |
| Grid, readable text, Edit and Retry | Deployed; desktop grid/mobile stacking, 16px main text, edit/cancel/history preservation and actual branch API metadata verified | Verify live regenerated response and final partial-state presentation |
| QA and accurate scoring | First sample report retained; fresh final API answers and independent semantic review recorded separately | Current completed deliveries include semantic failures. No full final-suite pass is claimed |

Final run index: [RESULTS.md](../experiments/06-evaluation/final-sessions/final600-20261017-1153/RESULTS.md).
Independent review: [FINAL-RESULTS-REVIEW.md](../experiments/06-evaluation/FINAL-RESULTS-REVIEW.md).
Dataset inventory: [dataset-update-20261017.json](../docs/dataset-update-20261017.json).
