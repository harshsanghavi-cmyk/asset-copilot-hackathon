# Retrieval implementation review and 18-scenario coverage

17 Oct 2026 · provisional review of actively edited code. Read coordinator-implementation-review.md first; R1–R3 are verified below rather than re-reported. **No application edits, services, installs, model/API calls, new sessions, raw-data changes or runtime-index/memory changes.** Only this report was written. Findings were sent directly to retrieval owner ctx_4ae920d80c36 and coordinator as identified; fixes can land after this snapshot.

## Priority findings

No P0 failure of the tested sample numeric paths was found. The core sample checks listed below pass; they do not establish live question/evidence/visual correctness. Two new P1 cases affect malformed/unseen data; the other gaps need small local fixes or explicit unsupported behavior, not an architecture change.

| ID / priority | Concrete observation and reproduction | Required local action |
|---|---|---|
| A1 / P1 — cross-asset baseline correction activates | [loader.py](../backend/ingestion/loader.py:76) inserts a formal false-positive correction without checking target asset. Its post-import `correction_target` query around line237 checks only existence. In-memory fixture: a context note on ASSET-A names existing INS-B on ASSET-B and says “Not a crude spill.” Result: baseline_corrections contains `(INS-B, spill_detected, false)` and the target check returns no issue. | Join correction note asset to target inspection before activation; retain/quarantine an invalid claim and report the issue. Sample56 targets are valid; this is a future-data integrity bug, not corruption in the supplied originals. Test same-asset pass, missing target and cross-asset rejection. |
| A2 / P1 — missing spill volume reported complete | [provider.py](../backend/retrieval/provider.py:422) only computes unknowns for selected metrics; spill_volume_bbl falls through to unknown=0. A temporary synthetic fixture with spill_detected=true and volume_milli=NULL returns volume=None but matching=1/evaluated=1/unknown=0/status=complete. SUM would also silently omit one missing volume among known rows. | Count missing metric-required fields over the full matching population and mark partial/unknown; never turn incomplete volumes into a complete fleet sum. Validate source flag/null coherence at ingestion while preserving unsupported evidence. |
| A3 / P2 — accepted only_breaches argument ignored | Query allowlist accepts only_breaches, but compilation never consumes it. On sample Southwest24,18Jul–16Oct, `metric=containment, only_breaches=true` returns all10 events, including eight within limit, rather than the two late events. | Implement a deterministic late-containment predicate with rule evidence or reject the unsupported argument. The ordinary complete containment query itself returns correct hours. |
| A4 / integration gap — zero cells absent from Q8 | Complete area/month query has correct totals35/43/37/26, but emits no NE-08/2026-08 or NE-08/2026-10 row. Current heatmap presentation treats blank as missing, while official fixture requires explicit zero. Sparse SQL output alone is valid; interpreting it as missing observations is the gap. | From the complete known area×month domain, fill absent groups with zero before rendering; preserve unknown/partial distinctions. Do not hardcode area IDs or ask Gemma to invent numeric arrays. Add both zero-cell assertions. |
| A5 / unfinished required feature — deterministic compliance/class deadlines | Current metric catalog lacks an incident compliance/classification/deadline operation. Regulatory record reads and report containment are available, but Q9/Q13 require date arithmetic, passing verification versus cleanup, NOV response state and reclassification after volume correction. No backend retrieval/chain date-derivation implementation was found in this bounded inspection. | Expose safe computed fields or a reviewed domain derivation through the existing provider contract. Test discovery+24h/+60days, NOV+30days, missing written notice and late-but-closed agency verification. Mark unsupported portions until implemented; do not call this a demonstrated wrong generated answer. |

Validity caveat: provider `_corrections` and production `_threshold` do not independently inspect supplied validity intervals. A direct authority fixture with future valid_from is applied. The normal memory authority gateway filters some rule lifecycles, so this is a **boundary contract/test requirement**, not a proved current Q12/Q14 bug. Observation-target corrections must remain usable when learned later; do not confuse receipt date with explicit evaluation validity. Check nested/top-level validity and scoped user rules at the canonical boundary before extending capabilities.

## Fixes independently verified

`python3 -B -m unittest backend.retrieval.test_provider.ProviderContractTests -v` passed **6/6** at execution. This class uses temporary synthetic dataset roots/indexes and leaves runtime data untouched. The owner added more tests after this run; those additions were read, not claimed executed here.

- **R1:** indexed evidence_map lookup and30 repeated citation reads passed the existing bounded-time fixture.
- **R2:** unknown observation outside a one-row presentation page still yielded unknown=1/partial.
- **R3:** aggregate lineage handle resolved to member records and remained resolvable after closing/reopening the provider over the same index.
- Also passed typed correction versus original, ordinary claim not mutating measurement, SQL/scope/limit rejection, and same-source repeat import. These are six test methods with multiple checks, not six official scenarios.

The initial visual-schema observation was fixed concurrently by the owner: current `query()` calls `_result_columns(rows,fallback)`. Independent sample snapshot confirms both temperatures are declared for Q3, lat/lon for Q7, and scope-specific corrections/RCA values are returned. Do not report the older `_compile` fallback list as an open blocker.

## Isolated full-sample snapshot results

A SQLite `mode=ro` connection backed the current derived index up into a TemporaryDirectory. All query-generated manifests were written only beside that temporary copy and removed with it. No index rebuild or raw-source ingestion occurred. The snapshot contained200 assets,39567 inspections,5665 jobs,90 regulator events,141 notes,56 baseline corrections,2516 sources,15187 chunks,1232 containment facts,2 production rules and0 import issues.

The copied index preserved baseline exclusions; exact source values and query windows were compared against [official scenarios](../dataset/03-evaluation-queries.md) as **test oracles only**, with the raw guide/manual/report references below. No expected-answer document was passed into an application/model context.

| Official question | Deterministic review status | Full scenario status / remaining gate |
|---|---|---|
| Q1 | **PASS core:** INS-0001-0203, not producing,3.2°C, Ryan Brooks | **BLOCKED/unrun:** planned-shutdown explanation, source citations and live status card |
| Q2 | **PASS core:** WELL-0164/0170/0172/0175 returned | **BLOCKED/unrun:** source-linked reasons versus “no recorded reason,” complete table/narrative |
| Q3 | **PASS core:**13 readings, both temperature columns bindable | **BLOCKED/unrun:** exact series/marker dates and actual rendered line chart/evidence |
| Q4 | **PASS numeric:**6 effective spills/15.1bbl | **BLOCKED/unrun:** dated event table and correction/source-rule citations |
| Q5 | **PASS numeric:**21days in2025 | **BLOCKED/unrun:** causal records/hot-ambient explanation and final answer evidence |
| Q6 | **PASS numeric:** WELL-0121=49, WELL-0107=42, WELL-0138=42 in16Jun–16Oct | **BLOCKED/unrun:** tie explanation and real bar chart; either stable tie order acceptable |
| Q7 | **PASS core:** four expected well IDs and coordinate columns | **BLOCKED/unrun:** individual coordinate/volume assertions, real geographic map and citations |
| Q8 | **PASS totals; FAIL zero-cell completeness:**35/43/37/26, but two required zero rows absent | **BLOCKED/unrun:** all40 cells and actual heatmap; fix A4 |
| Q9 | **BLOCKED:** no deterministic incident compliance/deadline derivation exercised | **BLOCKED:** four breaches/USD5000, pending versus met/overdue, report-only containment and source support; A5 |
| Q10 | **PASS numeric:** two late pairs WELL-0082=7.1h, WELL-0100=8.1h across10 candidates | **BLOCKED/unrun:** final table/rule/report spans; accepted breach-only flag **FAILS** separately (A3) |
| Q11 | **PASS costs only:** WELL-0121=25794, WELL-0138=46942, WELL-0107=5176USD | **BLOCKED/unrun:** Michael's actual Q6 receipt across new chat/date and estimate-basis explanation |
| Q12 | **PASS provider overlay:** corrected area excludes WELL-0164, leaving three specified wells | **BLOCKED/unrun:** real durable write/original/author/reason, contrary note and save acknowledgment |
| Q13 | **BLOCKED:** full volume→class/deadline/old-report cascade not exercised | **BLOCKED:**5.4 versus4.5, reportability/missing notice,23Nov deadline and late containment; A5 |
| Q14 | **PASS override subset:** exact expected four wells under T350 pump-jack2 threshold | **BLOCKED/unrun:** independent baseline, actual saved rule across new chat, source attribution and all scope/validity boundaries |
| Q15 | **BLOCKED:** direct provider snapshots do not prove cross-user memory propagation | **BLOCKED:** Jessica/Laura see Q12/Q13 commits, conflicts and consistent panels |
| Q16 | **BLOCKED:** not an official memory-sequence test in this review | **BLOCKED:** Jake→Michael shared plan plus Jessica negative private-history case |
| Q17 | **BLOCKED:** ordinary-claim nonmutation temp unit test is only a subset | **BLOCKED:** both actual conflicting exchanges, unconfirmed status, retained authors and reply evidence |
| Q18 | **BLOCKED:** raw conflicting notes/report are present but complete response not exercised | **BLOCKED:** detection stands, both ordinary sources and repair cited; no false formal correction |

“BLOCKED/unrun” means this read-only review cannot claim the integrated answer/visual path was run; it is not a factual-accuracy zero. No live provider request was attempted. Do not total the passing subsets into an18-scenario pass rate.

## Correct evaluator state and raw oracles

Run Q1–Q10 independently against originals. Q11 first runs Q6 as Michael, then starts his new chat with a controlled “yesterday” conversation date; compute costs again from current records. Q12 starts an isolated correction fixture and repeats Q2. Q13 starts an isolated volume correction fixture. Q14 runs baseline, commits only its type/equipment rule, then a new chat. Q15 explicitly combines the Q12/Q13 corrections for Jessica/Laura. Q16 carries Michael's Q11 private receipt and its new shared Jake plan, while Jessica has no such receipt. Q17 carries the stated ordered contrary claims and baseline observations. Q18 uses the original ordinary notes; no prior unrelated mutation leaks in. Preserve only declared dependencies, not one globally mutated fixture for all questions.

| Query family | Independent raw oracle references |
|---|---|
| Production, latest status, series/downtime | `assets/*/metadata.json`, `inspections.jsonl`; [guide](../dataset/02-dataset-guide.md); [T200 §9.3/§10](../dataset/sample-data/fleet/well-types/T200.md), [T350 §3/§6](../dataset/sample-data/fleet/well-types/T350.md). Delta≥15/20;7days per observed down inspection; missed inspections add0 |
| Real spills, map, heatmap | All matching inspection detections minus named formal context corrections; area and location directories; no suppression from ordinary notes |
| Costs and RCA | Maintenance rows by started_at; corrective counts by same equipment kind/12months; inherited manual plus separately attributed valid type rule; future completed_at may be planned and costs estimates |
| Containment/compliance | Follow actual maintenance.report_file; [Spill SOP](../dataset/sample-data/fleet/sops/spill-response-sop.md), [Regulatory SOP](../dataset/sample-data/fleet/sops/regulatory-compliance-sop.md); incident-linked regulatory events, passing agency detail/status and explicit report spans. Job duration, written notice and containment are different clocks |
| Existing disagreement | [WELL-0101 context](../dataset/sample-data/assets/WELL-0101/context.jsonl), INS-0101-0197 and MNT-0101-029; both notes ordinary; repair supports standing detection |

The supplied dataset's actual corrections/joins are coherent per [data audit](data-audit.md); do not mislabel A1/A2 synthetic ingestion cases as preexisting raw defects. All sums/thresholds are computed on integer-scaled source values before final display conversion; no sample precision error was observed. Full-population SQL runs before LIMIT; rankings, area totals and containment coverage were independently checked. T350 scoped RCA worked on the sample; a generic changed/manual-version inheritance test was not run.

Reproduce safely: connect to the current index using SQLite URI mode=ro, `source.backup(temp_connection)`, construct provider over the temporary DB, and issue the plans above with reference_date2026-10-16. Use inclusive plan end dates and maintenance start-date grouping. Keep official scenario fixtures out of runtime sources. For A1 use an in-memory SCHEMA/parse_record fixture; for A2 modify only a temporary synthetic fixture volume to NULL. Never run full-sample test methods against the shared runtime index during a review because provider queries persist manifests there.

Existing code tests directly cover sample Q4/Q5/Q10 and Q12/Q14 subsets; newly added owner tests cover Q3/Q7 schema and Q6/Q8/Q11 calculations. Generic backend memory/API tests cover mechanics such as shared/private provenance, validity, reference ambiguity, compaction and resume but are not official real-data Q11–Q18 executions. Priorities: finish A1/A2 and zero/flag handling; add deterministic Q9/Q13 evidence states; run the independent18-scenario evaluator with separate facts/evidence/visual reporting. No framework overhaul is required by these findings.
