# Latest accepted delivery — 17 Oct 2026

All 11 final scenarios finished in `final-sessions/all11-final-accepted/`: 21 replies across 14 sessions. Actual serving API: Gemini 3.5 Flash Lite, final 600-well snapshot, reference 15 Jan 2027. **10 complete replies, 11 partial replies, zero fatal request errors.** These are delivery counts; the final batch has not established an 80–90% semantic pass rate. The user accepted these current results for presentation.

All answers are saved in the application database and exported unchanged to `submission/results/all11/`. The updated Google Doc includes all questions and saved renderer JSON. Earlier failed provider experiments below are historical and do not describe the final delivery.

---

# Live QA report — incremental

Updated: 2026-10-17 12:15 UTC · This document preserves two separate dataset revisions; the legacy Q1–Q18 results below remain sample-release evidence. Historical sample model: Google AI Studio `gemma-4-26b-a4b-it`; final-data retry model: Google AI Studio `gemini-3.5-flash-lite`. Luna only inspected/scored actual receipts. Current persisted sample-data revision: `73efe30ac34f41cac36c031a3656e4b928bee4f2539eaee27e0ffb3329f3005e`.

## New 600-well final-data release status

The final-data source release is separate: clone commit `009e2b596782150f420021f9472ab37e3a2953ee`; root reported the indexed API namespace `asset-field-test-2027-01-15`, dataset revision `687ade729fe09c4d15c18a94ae102fcbcf8f4868fda89eaeb140ce54a7756716`, and reference date `2027-01-15`. Root-owned Gemini batch `gemini600-20261017-final` finished all21 turns in14 persisted sessions using `gemini-3.5-flash-lite`. Independent review finds **0/11 full scenario passes**: one individual turn (Q8.2 preference save) passes; seven turns are partial; twelve fail; one is blocked by a failed prerequisite. The first Gemma26B batch is archived separately below. No HTTP500 provider errors occurred in the Gemini batch, but many common questions still use the irrelevant private-reference fallback and seven outputs are partial due schema/grounding validation. Actual browser rendering remains untested. See [GEMINI-FINAL-RESULTS-REVIEW.md](GEMINI-FINAL-RESULTS-REVIEW.md) for the complete turn-level review and session mappings. Do not blend either final-data batch with the earlier 200-well sample QA.

| Final question | Turns | Gemini run semantic outcome |
|---|---:|---|
| Q1 Reservoir pressure | 1 | FAIL — irrelevant private-reference fallback |
| Q2 Best producer | 1 | FAIL — same fallback; no volume limitation |
| Q3 Gas reports | 1 | PARTIAL — 26-row table/calculations verified, explanation incomplete |
| Q4 Temporary flowline bypasses | 1 | PARTIAL — 12-row table and MOC statuses supported, explanation incomplete |
| Q5 Regulator letter | 1 | FAIL — private-reference fallback |
| Q6 Status disagreements | 1 | PARTIAL —119 complete result rows, no validated explanation |
| Q7 Operator warning notes | 2 | FAIL / BLOCKED_DEPENDENCY — no ranked first answer, dependent turn unavailable |
| Q8 Recall knowledge/corrections | 5 | FAIL overall — one private preference save passes, recall scope/filter/preference not correctly applied |
| Q9 Multi-topic conversation | 6 | FAIL overall — private fallback and cross-topic entity substitution; two partial turns |
| Q10 Shut-in delays | 1 | FAIL — private-reference fallback |
| Q11 Regional temperature | 1 | PARTIAL — area/type statistics, no supported region conclusion |

## Latest repaired Gemini attempt — provider schema blocked

The next root-owned run `gemini600-20261017-repaired` stopped with manifest status `stopped_invalid_provider_schema`. It recorded14 HTTP400 `INVALID_ARGUMENT` failures from `ChatGoogleGenerativeAI`/`gemini-3.5-flash-lite`; Q08.5 remained running at stop. This is an integration failure and is NOT SCORED for answer accuracy. The full first Gemini run above remains the latest complete 21-turn quality assessment, while these repaired-run errors are retained separately under `final-sessions/gemini600-20261017-repaired/`. A working Gemini request configuration and another root-owned run are still required.

## Archived first final-data attempt — Gemma 4 26B (stopped on model switch)

Batch `final600-20261017-1153` is retained as a separate historical attempt. It stopped after17 turns when the user requested Gemini3.5 Flash Lite; it is not the current score. Its HTTP500 and `run_failed` receipts remain under that batch directory.

| Final question | Turns | Current delivery | Semantic status |
|---|---:|---|---|
| Q1 Reservoir pressure | 1 | Delivered | FAIL |
| Q2 Best producer | 1 | Delivered | FAIL |
| Q3 Gas reports | 1 | HTTP500 error | NOT SCORED |
| Q4 Temporary flowline bypasses | 1 | HTTP500 error | NOT SCORED |
| Q5 Regulator letter | 1 | HTTP500 error | NOT SCORED |
| Q6 Status disagreements | 1 | Delivered | FAIL |
| Q7 Operator warning notes | 2 | One `run_failed`, one blocked fallback | BLOCKED_DEPENDENCY overall |
| Q8 Recall knowledge/corrections | 5 | Turn1 partial; turn2 running; remaining turns pending | Incomplete / pending |
| Q9 Multi-topic conversation | 6 | NOT RUN | NOT SCORED |
| Q10 Shut-in delays | 1 | HTTP500 error | NOT SCORED |
| Q11 Regional temperature | 1 | Partial answer; explanation invalid JSON | FAIL / partial delivery |

Per-turn evidence requirements and failure gates are in [FINAL-DATA-QA-PLAN.md](FINAL-DATA-QA-PLAN.md). Root owns `scripts/run-final-sessions.py` and live execution; this worker owns independent semantic review/reporting from the persisted JSON/session manifest once results are written. No additional calls were made by this evaluator while preparing the plan.

## Historical sample-data baseline — 17 Oct 2026

Latest all-18 evaluator pass completed at `2026-10-17T11:25:06Z`: **15/18 had an answer envelope** (some were explicitly incomplete fallback answers); Q4, Q10 and Q14 had no final answer. Six results reused workflow checkpoints with zero new generations (Q1, Q2, Q5, Q15, Q17, Q18), so they are cached evidence, not fresh model retests. Independent semantic assessment: **2/18 full passes (Q11,Q16), 3 partial (Q5,Q7,Q8), 10 fail, 3 NOT SCORED**. Actual browser-rendered UI checks: **0/18**. This is the baseline only; no fixed-code fresh run has been authorized or started. The shared request guard is already144/150. At the latest dispatch check (11:35 UTC), root directed HOLD while backend recovers a request interrupted by reload; no `runtime/live-evaluation-repair-a.json` receipt exists yet. The tagged harness compiles and its dry-run used0 generations, but no runtime semantic review is available for that version.

### Prioritized failing layers (SCORING.md)

| Priority / layer | Status | Verified failures and passing evidence | Assigned fix area |
|---|---|---|---|
| P0 — Answer grounding (25%) | **FAIL** | Q1 omits shutdown/rule/stale status; Q2 says2 despite4 rows; Q9 says2 breaches, omits SR-02/SR-03; Q13 misses reportability/deadline; Q15 returns old value; Q17 fails to mark Tyler's claim unconfirmed; Q18 misses both opposing notes. | Backend Q&A + Retrieval |
| P0 — Memory (10%) | **FAIL** | Q15 fails cross-user effective correction propagation (hard gate); Q12 write/result set updates but output omits attribution/conflict. Q11 prior-well continuity and Q16 shared-plan/private-history isolation pass. | Backend memory/Q&A + Retrieval |
| P0 — UI contract (10%) | **FAIL; browser render untested** | Q1 status block semantically binds `spill_detected` as production; Q3 requested line and Q6 requested bar absent. Q7 map and Q8 heatmap typed plans exist, but no browser screenshots. | UI + Backend output contract |
| P1 — Retrieval (20%) | **FAIL** | Q1 misses CTX-0001-003; Q2 misses MNT-0170-031/-0172-028; Q5 lacks contributing inspections/rule trace; Q9/Q13 lack complete SOP/report findings; Q18 misses CTX-0101-002/-003. | Retrieval + Backend |
| P1 — Calculations (20%) | **PARTIAL** | Exact values pass for Q5 (21), Q6 ranking data (though answer incomplete), Q8 area totals, Q11 costs, Q12 set, Q13 corrected5.4. Failures include Q3 missing one observation, Q9 breach count/coverage, and Q15 stale corrected value. | Retrieval + Backend deterministic query/effective values |
| P1 — Planner (15%) | **PARTIAL / insufficiently isolated** | Many scopes/windows are correct; Q4/Q10 fail before usable plan due malformed `requested_visuals` field; Q3 period coverage is short. Intent-routing and plan quality need fresh receipts after fixes. | Backend evaluator/application contract |

Hard-gate order: correct Q15 shared correction first; correct Q1 production card and Q2/Q9 narrative/result contradictions next; restore full record/report retrieval for Q1/Q2/Q5/Q9/Q13/Q18; then visual-plan completeness and actual browser render. No weighted numeric score is published because the rubric currently defines layer weights but does not enumerate precommitted per-layer scenario criteria/denominators; categorical layer outcomes above avoid inventing post-hoc weights.

### Historical first-batch matrix (10:29 UTC; superseded by latest baseline above)

| Case | Live delivery / semantic status | Planner | Retrieval | Calculation | Answer grounding | Memory | UI | Primary issue / evidence |
|---|---|---|---|---|---|---|---|---|
| Q1 | Delivered; **FAIL** | PARTIAL | PARTIAL | PASS core delta | FAIL completeness + hard-gate semantic binding | N/A | FAIL binding; render untested | Omits CTX-0001-003 planned shut-in, 15°C rule, stale status; status block binds spill flag as production. `runtime/live-evaluation.json`, `agent-memory/live-answer-review.md` |
| Q2 | Delivered; **FAIL** | PARTIAL | FAIL explanation coverage | FAIL narrative says two vs four | FAIL, misses MNT-0170-031/-0172-028 | N/A | Declared table only; render untested | Four matching result rows contradict narrative and repairs absent. Same evidence paths. |
| Q3 | Failed delivery/validation; NOT SCORED | — | — | — | — | N/A | — | See result error in runtime report; no final answer. |
| Q4 | Failed delivery/validation; NOT SCORED | — | — | — | — | N/A | — | See result error in runtime report; no final answer. |
| Q5 | Failed initial delivery; separate minimal rerun harness PASS, semantic NOT SCORED | — | — | — | — | N/A | N/A | Initial failure preserved in `runtime/live-evaluation.json`; recovery receipt `runtime/live-evaluation-q5-minimal.json`. |
| Q6 | Failed delivery/validation; NOT SCORED | — | — | — | — | N/A | — | `runtime/live-evaluation.json` |
| Q7 | Failed delivery/validation; NOT SCORED | — | — | — | — | N/A | — | `runtime/live-evaluation.json` |
| Q8 | Failed delivery/validation; NOT SCORED | — | — | — | — | N/A | — | `runtime/live-evaluation.json` |
| Q9 | Failed delivery/validation; NOT SCORED | — | — | — | — | N/A | — | `runtime/live-evaluation.json` |
| Q10 | Failed delivery/validation; NOT SCORED | — | — | — | — | N/A | — | `runtime/live-evaluation.json` |
| Q11 | Failed delivery/validation; NOT SCORED | — | — | — | — | FAIL/unverified | N/A | Dependency sequence did not produce a reviewed final answer; `runtime/live-evaluation.json` |
| Q12 | Failed delivery/validation; NOT SCORED | — | — | — | — | FAIL/unverified | N/A | Correction sequence did not produce a reviewed final answer; `runtime/live-evaluation.json` |
| Q13 | Pending resumed run | — | — | — | — | — | — | Resume command confirmed by backend owner; fixture group shares correction sequence. |
| Q14 | Pending resumed run | — | — | — | — | — | — | Resume command confirmed by backend owner. |
| Q15 | Pending resumed run | — | — | — | — | — | — | Depends on Q12/Q13 shared corrections. |
| Q16 | Pending resumed run | — | — | — | — | — | — | Shared plan and Jessica private-history isolation. |
| Q17 | Pending resumed run | — | — | — | — | — | — | Contradictory user claims sequence. |
| Q18 | Pending resumed run | — | — | — | — | — | — | Preserve detection and both unconfirmed notes. |
| Fleet regression | Existing delivery reviewed separately | FAIL | FAIL | NOT SCORED | FAIL/incomplete | N/A | N/A | User exact question “how many assests we have and where show me there states”; run `6008d885-f48d-40dc-9e98-d75184b3a514`, shared with backend/coordinator. |

Full answer receipt, per-attempt usage and isolated fixture locations: `runtime/live-evaluation.json`, `runtime/evaluation-model-replies.jsonl`, `runtime/evaluation-memory/`; request-level receipts: `runtime/model-requests.sqlite` (inspect without secret values). Scenario oracle and rules: `dataset/03-evaluation-queries.md`.

## Provider failures and attempt accounting

At the handoff the shared ledger recorded 73 attempt rows against the currently configured 150-attempt guard. Row 69 was in-flight, so the backend owner waited for settlement and confirmed evaluator PID 1287564 exited before this worker launched the remaining cases. Q1–Q12 status history remains in the primary report. Earlier 400/500/transport/model-JSON/numeric-grounding errors are recorded there and must not be relabeled as semantic answer failures. The shared ledger enforces 30 RPM / 2.2s minimum spacing; exact 16K TPM scheduling is not implemented, so token use must be monitored from actual usage receipts. Current runner is executing only Q13–Q18 under the authorized 150-attempt total cap.

## Assigned fixes / unresolved

- Backend: improve retrieval of active repair records and context notes for operational explanations; require narrative cardinality to match complete deterministic result sets; preserve failed run receipts and route validation failures clearly. Q1/Q2 evidence review is linked above.
- Backend/UI: validate semantic panel bindings, not only whether a selected field exists; production status must bind `producing` with an asset ID and relevant temperature delta, never `spill_detected`.
- Backend: test Q1 planned shutdown and Q2 repair causes after fixes; do not count old answers as repaired.
- Evaluation: finish and independently review Q13–Q18 outputs; explicitly score evidence, factual values, memory scope and visual separately. Retest only after owner supplies a concrete fix/version; no unchanged retries.
- UI: inspect an actual rendered dashboard and compare data/units to the answer envelope. No screenshot or browser check has been performed in this evaluation worker checkpoint.

## Historical incremental checkpoint (10:33 UTC; superseded by later retries)

All18 official slots now have an evaluator status. The resumed Q13–Q18 sequence finished; Q16–Q18 are provider-blocked (HTTP429) and no longer being retried. Final completion coverage is **3/18 with delivered answers** (Q1, Q2, Q15); **0/18 full semantic passes** after independent review; **15/18 have no complete answer suitable for semantic scoring**. Q5 has a separate minimal recovery receipt but no final semantic review; do not count it as a full pass. UI rendering was not inspected for any scenario.

| Case | Delivery | Independent semantic outcome | Primary root cause / handoff |
|---|---|---|---|
| Q1 | Answer delivered | FAIL | Missing planned-shutdown note and threshold reasoning; status card binds spill flag as production. Reviewer findings above. |
| Q2 | Answer delivered | FAIL | Narrative says two instead of four and misses two open repair explanations; reviewer findings above. |
| Q3 | Failed `provider_error` | NOT SCORED | No final answer. Backend/provider. |
| Q4 | Failed `provider_error` | NOT SCORED | No final answer. Backend/provider. |
| Q5 | Failed `empty_model_response`; separate minimal rerun harness PASS | NOT SCORED | Recovery is recorded separately and has zero-new-generation status per backend handoff; request targeted semantic review after the provider-bounds change. |
| Q6 | Failed `provider_error` | NOT SCORED | No final answer. Backend/provider. |
| Q7 | Failed `provider_error` | NOT SCORED | No final answer. Backend/provider. |
| Q8 | Failed `invalid_model_json` | NOT SCORED | Model output did not parse; no unchanged retry. |
| Q9 | Failed `invalid_model_json` | NOT SCORED | Model output did not parse; no unchanged retry. |
| Q10 | Failed `unsupported_narrative_number` | NOT SCORED | Grounding validator rejected unsupported numeric prose; no unchanged retry. |
| Q11 | Failed `unsupported_narrative_number` | NOT SCORED | Grounding validator rejected unsupported numeric prose; dependency answer unavailable. |
| Q12 | Failed `provider_error` | NOT SCORED | Correction scenario did not complete; Q15 consequently cannot pass its declared dependency. |
| Q13 | Failed `invalid_model_json` (2 generation attempts) | NOT SCORED | Correction workflow maker returned invalid JSON. |
| Q14 | Failed `invalid_narrative_citation` (3 attempts) | NOT SCORED | RCA override answer cited a source handle absent from the evidence registry. |
| Q15 | Answer delivered; evaluator checks failed | FAIL | Jessica received original not-producing status rather than Michael's corrected 41°C effective value; no correction attribution evidence. |
| Q16 | Failed `provider_rate_limited` (HTTP429) | NOT SCORED | Google free-tier input-token quota reached; current attempt failed before an answer. |
| Q17 | Failed `provider_rate_limited` (HTTP429) | NOT SCORED | Same provider quota block. |
| Q18 | Failed `provider_rate_limited` (HTTP429) | NOT SCORED | Same provider quota block. |
| Fleet regression | Earlier delivered answer | FAIL | `agent-memory/live-answer-review.md`: generic request returned an incomplete fleet response with no grounded count/location/state coverage. Backend owner has receipt run ID. |

### Runtime accounting and provider limits

The shared ledger now has **87 attempt rows**, including one non-evaluation greeting during the coordinated project run. Across ledger receipts with returned usage metadata, measured totals are **69,121 input tokens and 21,575 output tokens**; failed HTTP429 calls report no usage. Cost is not available in the Google AI Studio receipts. Several attempts before and during this evaluator batch received HTTP400/500/transport errors or model output validation errors; see each case and raw ledger for IDs/timing. Q16–Q18 explicitly report Google's free-tier `generate_content_free_tier_input_token_count` limit of16,000 with retry-after around51–58s. The local shared limiter only enforced30 RPM /2.2s between starts and did **not** meter TPM; thus it allowed token demand beyond the provider's actual TPM quota. No more calls were made after these failures.

### Fix state

No application fixes were made by this evaluation worker. Q1/Q2 defects were already sent to backend and UI owners through the independent review handoff. Q13–Q15 outcomes and Q16–Q18 quota evidence were sent to the backend owner immediately. No “after” retest is claimed because no verified code/prompt revision and retest receipt was provided during this run. Prior failed results remain preserved; the evaluator's shallow Q1/Q2 checks are not treated as semantic acceptance.

## Historical quota retry checkpoint (10:43 UTC; superseded by full suite run)

Per user direction, retried Q16–Q18 after an initial10-second wait and let the existing evaluator apply its bounded stage attempts. The retry batch delivered Q16 after4 attempts and Q17 after6 attempts; Q18 delivered after2 attempts but failed a content check. The earlier HTTP429 results remain in `attempt_history`; the latest result replaces only the current `results` entry. No application code or prompts changed.

| Case | Retry delivery / harness check | Independent semantic review | Current overall |
|---|---|---|---|
| Q16 | Main negative private-history answer passed. Its extra shared-fact answer for Michael was incomplete: `Partial answer... explanation could not be completed`; required Jake-attributed Oct17 10-day workover narrative was not delivered. | Private memory isolation PASS; shared knowledge recall FAIL. | **FAIL / partial** |
| Q17 | Harness checks for inspection non-production and visible disagreement passed. | Correctly cites Michael's and Tyler's conflicting claims and the inspection's0.4°C delta in result rows, but narrative omits the delta and does not label Tyler's claim unconfirmed or ask him to confirm. | **PARTIAL / FAIL overall** |
| Q18 | Delivered; retained inspection spill detection, but `both_disagreeing_notes` is false. | Omits CTX-0101-002 and CTX-0101-003, their opposing water/crude claims, and the non-correction/repair context. It does not establish the expected confirmed-crude conclusion. | **FAIL** |

Quota recovery is delivery only, not an acceptance pass. Across the full ledger at this update:112 rows,99 generation attempts against the150 attempt cap, with usage-bearing generation receipts totaling95,941 input and28,265 output tokens (cached-token-count rows excluded from these sums). Cost is unavailable. The retry introduced no new HTTP429s, but no additional retries were performed after these three outcomes: Q16/Q17 now have semantic defects rather than rate-limit errors, and Q18 has a content/evidence failure. Full suite semantic-pass count remains **0/18**.

## Full 18-case rerun update (17 Oct 2026 11:26 UTC)

The user requested another complete run. The evaluator processed Q1 through Q18 in order after a10-second wait, using the shared ledger and existing synthetic fixtures. It did **not** issue fresh model calls for every case: stable LangGraph run IDs/checkpoints reused prior outputs for Q1, Q2, Q5, Q15, Q17 and Q18 (0 attempts). Q1/Q2/Q15/Q17/Q18 therefore have no new answer generation in this batch; their old answer hashes/results remain the evidence and their prior defects persist. Q5 also reused its earlier recorded answer. The runner stopped normally at Q18. The ledger was at144/150 generation attempts after the run, so no remaining attempt budget was used for further calls.

| Case | Current harness result | Fresh generation this pass | Independent scenario outcome |
|---|---|---:|---|
| Q1 | shallow PASS (cached) | 0 | **FAIL** — previously reviewed output omits CTX planned shutdown/rule reasoning and status binding uses spill_detected for production. |
| Q2 | shallow PASS (cached) | 0 | **FAIL** — narrative says2 while four result rows exist; omits open repair causes and invents cause from observation. |
| Q3 | FAIL: 12 readings, no line chart; answer fallback | 3 | **FAIL** — expected13 readings and line visualization; output has12 and only tables. |
| Q4 | BLOCKED: `repair_budget` on invalid `requested_visuals` type | 1 | NOT SCORED — no final answer. |
| Q5 | shallow PASS (cached; 21-day scalar) | 0 | **PARTIAL** — correct number, but explanation lacks three source inspections/rule trace and emits an unnecessary bar chart; evidence-search warning remains. |
| Q6 | FAIL: correct three rank values/set, bar missing; answer fallback | 2 | **FAIL** — requested bar missing and explanation incomplete. |
| Q7 | shallow PASS: four expected wells + map | 2 | **PARTIAL** — four correct pins/coordinates and map, but narrative is fallback/incomplete and map's `value` binds unrelated `producing`. |
| Q8 | shallow PASS: totals + heatmap | 2 | **PARTIAL** — correct four area totals and 2026 values; 48 cells include Nov/Dec zero columns despite expected Jan–Oct scope. Visual renders as a heatmap by typed plan; browser render not inspected. |
| Q9 | FAIL: only SR-01/RC-04 narrative, two instead of four breaches | 2 | **FAIL** — SR-02 and SR-03 findings omitted; SR-01/RC-04 supported, $5,000 present. |
| Q10 | BLOCKED: `repair_budget` on invalid `requested_visuals` type | 1 | NOT SCORED — no final answer. |
| Q11 | harness PASS | 5 | **PASS** — Michael's three prior wells recalled in new chat; three USD costs match expected; includes table/bar, current-year framing and in-progress cost caveat. |
| Q12 | shallow PASS: three expected wells | 4 | **FAIL** — count/set correct after effective correction, but explanation misses correction attribution/conflict and falsely says WELL-0170 has no recorded cause; does not surface open maintenance records. |
| Q13 | FAIL: corrected5.4 appears, reportability check false; answer fallback | 2 | **FAIL** — corrected value applied, but no reportable threshold, overdue SR-01 notice or SR-03 deadline explanation. |
| Q14 | provider HTTP500 after6 generation attempts | 6 | NOT SCORED — no final answer. |
| Q15 | FAIL (cached; correction not propagated) | 0 | **FAIL** — Jessica sees original24°C/not-producing state; no Michael attribution or effective41°C correction. |
| Q16 | harness PASS | 2 | **PASS** — private-history negative answer does not leak Michael's well list; separate Michael answer states Jake's shared Oct17 10-day workover plan with attribution. Both subchecks delivered in this fresh fixture sequence. |
| Q17 | shallow PASS (cached; no new generation) | 0 | **FAIL** — old answer surfaces both claims and not-producing record, but omits0.4°C in narrative, does not label Tyler's claim unconfirmed or ask confirmation. |
| Q18 | FAIL (cached; no new generation) | 0 | **FAIL** — old answer retains detection but omits both opposing context notes and the repair evidence. |

**Scoring summary:** 2/18 full semantic passes (Q11,Q16); three partial answers (Q5,Q7,Q8); ten semantic failures (Q1,Q2,Q3,Q6,Q9,Q12,Q13,Q15,Q17,Q18); and three cases without a score because no final answer was produced (Q4,Q10,Q14). No rendered-browser/UI verification was performed. The previously completed harness passes are not semantic accuracy claims.

New answers and usage remain in `runtime/live-evaluation.json`, synthetic model replies in `runtime/evaluation-model-replies.jsonl`, isolated fixtures in `runtime/evaluation-memory/`, and all request attempts in `runtime/model-requests.sqlite`. Across generation rows, usage-bearing receipts sum to188,782 input and48,013 output tokens; failed attempts without provider usage are excluded. Attempt count is144/150. Q4/Q10 invalid-visual-plan and repair-slot failures, Q14 HTTP500, and Q13 incomplete reportability were sent as concrete outcomes through this QA record. No code, prompts, raw data or secrets were modified.
