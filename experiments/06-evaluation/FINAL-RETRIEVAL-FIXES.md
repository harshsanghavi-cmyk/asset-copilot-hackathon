# Final600 retrieval operations repair

Implemented against the replacement snapshot `dataset/test-data/dataset`, reference **15 Jan 2027**, source revision `009e2b596782150f420021f9472ab37e3a2953ee`. The existing typed `query` tool now exposes eight additional metrics; there are no new tools, model calls, hardcoded answer lists, raw-data changes, live-index rebuilds or service restarts in this work. New code requires the coordinator's safe-boundary backend restart before the next live batch.

## Interface and changes

- `backend/retrieval/final_operations.py`: fixed parameterized population reads, source-rule parsing, same-asset event joins, interval assessments, report-section inspection, transparent ranking and thermal aggregates.
- `backend/retrieval/provider.py`: catalog/description registration, dispatch through the existing query boundary, and correct typed-result lineage replay. Prior lineage logic converted every derived metric into unrelated inspection records; these operations now replay their actual typed rows under the saved authority revision.
- `backend/retrieval/test_final_operations.py`: independent raw-file oracles and language/authority boundary tests. All fixture indexes/manifests live in temporary directories.

Every operation returns existing ResultSet revisions, source/evidence handles, bounds, full-population `summary`, `assessment_counts`, pagination coverage and durable lineage. Presentation limits do not limit calculation inputs. Unsupported filters/groupings fail explicitly. Declared unavailable/truncated report evidence makes coverage partial rather than proving absence. Current supplied maintenance reports are all fully available in previews; no top-k search establishes any count.

| Metric | Rule and temporal semantics | Measured local result before runtime memory |
|---|---|---|
| `gas_response` | SOP-OPS Rev2 OPS-1; positive operator observation; earliest **strictly later** same-well maintenance start or manual inspection; drones excluded. Deadline24h before1Jan2027,12h from that date. No concentration inferred from odor or a stop-work threshold. | Since1Nov2026: **26 reports,17 met,9 missed**. Exact response IDs/times, elapsed hours and due timestamps included. |
| `bypass_intervals` | OPS-2; ordered positive installation/removal notes; only named, effective MOCs authorize an interval; explicit extension replaces original expiry. Expiry includes its last calendar day. | **12 intervals**, **3 currently in place**, **5 violations** (3expired,2unapproved). Current intervals and violations sort before retired allowed intervals. |
| `recall_inventory` | Supplier notice's recalled lot list, `Parts installed` serial/lot lines and latest completed installation; future completion does not prove replacement. Later recorded replacement ambiguity stays unknown. | **9 documented recalled pumps** in four areas before user claims. Installation job/total cost, current corrected status and last non-cleanup corrective repair date included. |
| `letter_compliance` | Letter's named areas and1Jun2026 start; reportable effective volumes from Spill SOP; false-positive corrections excluded. Exact affirmative lab sentence must occur in the linked report's `Spill clean-up and waste` section; Markdown bullets accepted, negated/quoted statements rejected. | **6 covered spills:3 compliant,3 not compliant** under the letter's internal evidence criterion. |
| `freeze_checks` | OPS-5: winter producing readings with corrected ambient<=-5C; event-time type threshold; earliest later Heat trace check start within7days. Non-producing cold readings excluded. | December2026: **9 duties,5 met,4 missed**. Through reference date:17duties. |
| `repair_candidates` | Last-month equipment-symptom notes with no subsequent recorded corrective non-cleanup repair. Quotes, repair dates and actual readings retained. Adds manual ESP four-reading declining-delta warning when unreconciled by a later drive/insulation check. | **133 candidates** for15Dec2026–15Jan2027; every candidate is assessed before ranked pagination. Score is an explicit heuristic, never a calibrated90-day probability. |
| `wait_reasons` | Report-attributed extra wait **beyond repair**, jobs by start date. Reasons grouped by area; medians/shares use observed extra-wait prose, not downtime-hours subtraction. Nearby differing note attributions are exposed. |2026: **472 observed jobs**, **2 separate future estimates**, **28 area/reason groups**, **10 differing note attributions**.168reports mention waiting without a recognized quantitative extra-wait sentence; these do not become fabricated durations. |
| `temperature_profile` | Full-population corrected wellhead/ambient/delta means by area and observation-time type, producing-only delta, well/reading counts, and within-type monthly hottest counts with ties. Comparisons require another area of that type/month. | Entire **125,198-inspection** population is evaluated before profile pagination. Different type/weather/operating-state coverage is explicit. |

## Concrete source anchors

Rules: `dataset/test-data/dataset/fleet/sops/operations-sop-rev2.md` OPS-1/2/5; `moc-2026-031.md`, `moc-2026-036.md`, `moc-2026-044.md`; `supplier-recall-notice-2026-12-01.md`; `regulator-letter-2026-11-20.md`; `spill-response-sop.md` spill classes; `fleet/well-types/T500.md` early warning section. Rules are parsed from registered supplied documents, not expected scenario answers.

Letter evidence examples (all six are returned, not a sample used as a runtime oracle):

| Inspection | Assessment |
|---|---|
| INS-0119-0209 | Compliant: linked cleanup report contains affirmative lab sentence in required section. |
| INS-0123-0093 | Not compliant: required section evidence absent. |
| INS-0168-0190 | Compliant. |
| INS-0182-0208 | Not compliant. |
| INS-0262-0218 | Not compliant. |
| INS-0277-0205 | Compliant. |

Future wait wording is explicit in `assets/WELL-0404/maintenance-reports/MNT-0404-034.md:13` (expected21extra days) and `assets/WELL-0496/maintenance-reports/MNT-0496-033.md:13` (expected37extra days). These are estimates, not corrupt dates or completed measured waits. Absolute paths for these anchors begin at `dataset/test-data/dataset/`.

## Shared recall claim authority

`AuthoritySnapshot.shared_claims` is the trusted canonical boundary. Inventory retains documented serial/lot/cost evidence. A **direct, attributed, explicit operational count-as-replaced instruction** changes `included_in_operational_recall_list` and `summary.operational_in_ground`, while `documented_in_ground` and `work_order_verified=false` preserve the evidence gap. The author's statement and validity dates remain in `replacement_claims`. Hearsay (`told me`, attributed secondhand qualifier), conflict-pending/candidate/retracted facts and negated replacements do not remove a pump from the operational count. No ordinary claim changes temperatures or becomes a verified physical work order. A source-confirmed later installation supersedes older claims about the preceding pump.

A synthetic public claim on a dynamically selected recalled asset verifies9documented/8operational; the same update phrased as hearsay verifies9operational. No scenario-specific well/user IDs are embedded in implementation. Actual cross-session saving, private sort/cost preferences and final model attribution are backend-memory integration work and require the live ordered batch.

## Final-question retrieval coverage

| Question class | Retrieval support / honest boundary |
|---|---|
| Reservoir pressure; measured oil production | No invented proxy: no reservoir-pressure or produced-oil-volume operation added. Thermal deltas, pressure ratings and spill volumes cannot answer these requests. |
| Gas; bypass; letter | Complete relevant population and typed per-event evidence above. Letter compliance is its stipulated report-evidence test, not independent laboratory timestamp verification or general legal closure. |
| Inspection/operator status disagreement | Existing OPS-3 `status` plus `status_note_disagrees` and event-time rules retained. |
| Repair judgement | Ranked, sourced heuristic with evidence; no unsupported probability claim. Remaining manual symptoms/targeted follow-up obligations are not claimed exhaustive. |
| Recall and remembered replacement | Physical/operational inventory explicitly separated; private/shared sequence must be checked end to end. |
| Topic changes, team directory, cold weather, missing H2S reading, recall/down-status/repair follow-up | Existing directory/count/status plus new freeze/recall/gas metrics. Conversation reference resolution remains backend responsibility. Odor note does not supply a numeric H2S measurement. |
| Delay reasons | Exact observed denominator, estimates separated, conflicting note attribution visible; missing numeric durations remain excluded/declared. |
| Consistently hotter regions | Full thermal profile with type/weather/operating-state controls and monthly comparison coverage; cannot establish geological reservoir pressure or oil yield. |

## Validation and handoff

Reproducible local command (no runtime model):

```sh
backend/.venv/bin/python -B -m unittest backend.retrieval.test_provider backend.retrieval.test_final_dataset backend.retrieval.test_temporal backend.retrieval.test_final_operations -q
```

The raw-file oracles independently enumerate all relevant context notes/inspections/jobs, check earliest eligible responses and deadline revision, current serial/lot/cost after later installations, corrected letter scope and section evidence, winter producing duties, area/reason shares and medians, future-estimate separation, candidate evidence/no later repair, and thermal means with historical type assignment. Unit cases cover negated gas/bypass language and direct/hearsay/conflicting replacement claims. Typed lineage replay and unsupported argument rejection are tested. Final expanded validation: **47tests passed in43.223s** (34existing +13new). After the final recall supplier/model exclusion and compact summary refinements, all13new tests passed again in12.229s. No live answer accuracy is inferred from these checks.

**Coordinator/backend integration:** catalog now lists all eight names; planner must select them. Root-owned `backend/memory/budget.py` needs metric-first field projection: gas `note_id` must not trigger generic-note stripping of responses/deadlines; recall/risk `producing` must not trigger generic-status stripping of serial/lot/claims/ranking. Include `summary`/`assessment_counts`; `row_count` and a preview cannot establish population totals. Render charts/tables from full ResultSet handles, not maker excerpts. `wait_reasons.share` is a fraction; costs areUSD source job totals. Runtime policy labels now acknowledge the user's latest Google AI Studio Gemini3.5FlashLite instruction; backend owns the verified API model ID. No generation was performed here.

**Still unverified:** safe-boundary reload, planner choice, compact evidence projection, actual maker facts/citations, table/chart bindings and ordered cross-session recall updates in the next coordinator-owned live batch. Local retrieval success is not a live-answer accuracy score. New/reworded rule documents that fail a recognized rule shape fail explicitly; unknown/truncated report evidence remains partial.

## Urgent follow-up: direct recall updates and complete OPS-3 grammar

The retained shared observation `memory:6f72ff2e-f14e-4db1-9d26-6e5b1f30b765` is `unconfirmed`, `qualifier=attributed`, with `firsthand=false` because the current public projector only recognizes an `I/we` verb. Its passive wording and explicit count-as-replaced instruction are still a direct operational report. `replacement_override` now honors that instruction without upgrading physical evidence: `unconfirmed` is allowed, while hearsay/inferred qualifiers, actual conflicts, retracted facts, negation and speculative replacements remain excluded. A plain passive statement without a direct instruction or explicit firsthand metadata is not silently promoted.

The operational recall **table rows**, as well as its count, now exclude an honored direct replacement update. `summary.documented_in_ground` retains physical inventory, `summary.operational_in_ground` carries the operational count, and `summary.excluded_replacement_updates` retains serial/lot, installation job, author/statement/qualifiers and `work_order_verified=false`. A source-shaped unconfirmed passive report on a dynamically chosen recalled asset verifies **9 documented / 8 operational / 8 table rows**; hearsay keeps **9 operational / 9 rows**. The test calls the real `MemoryStore.public_fact` projector without constructing a store or writing memory.

**Additional live-memory blocker, escalated to the memory owner:** that retained fact also has a conflict edge to `memory:f8da1d07-fc0c-4989-93c7-24de35ec18ca`, a same-author agreeing observation that the same pump was replaced on14Jan2027 pending documentation. Reading the actual current canonical projection still yields9operational because of this spurious conflict. Retrieval deliberately preserves conflict protection; the memory owner must normalize compatible additive observations before replay of this already-saved snapshot can prove8operational. This worker did not rewrite canonical facts or discard arbitrary conflict edges.

An independent full-source status audit also disproved the provisional119-disagreement count. `temporal.py` recognized `shut-in` / `shut in` but missed `shut the well in` (21supplied operator notes). With the coordinator's explicit single-file handoff, the parser now accepts that generic shutdown wording with matching negative/future-plan guards. Four latest-note selections change: `CTX-0281-004`, `CTX-0479-004`, `CTX-0203-003`, `CTX-0355-004`. The material added disagreement is **WELL-0479**: its14Jan2027 15:35shutdown note follows its11:45producing inspection, so current status is **Not producing oil**. The other three cases repair latest-note provenance even where final status/membership agrees.

Correct full-population disagreement membership is **120**: **10 latest actual status notes are newer than the inspection**, while **110 earlier actual status notes disagree with a newer inspection**. For the latter, the newer inspection governs current status; historical disagreement does not make an obsolete shutdown current. The93notes saying a weather-delayed restart was pushed back are not actual restart events and remain excluded. `recorded_status` never defines this predicate. Source-grounded tests independently reconstruct all600latest inspections, corrected/type-specific deltas and latest actual operator events, verify exact note IDs/current status/confirmation state, and compare the entire paginated disagreement population.

Validation after both fixes: **20 focused tests passed in33.620s** (`backend.retrieval.test_final_operations` + `backend.retrieval.test_temporal`), including a regression that failed on the prior parser. The previous47-test result above remains historical; the focused follow-up count is not an accuracy score. No API/model requests, serving restart, live-index changes or raw-data writes were performed. Reload and actual ordered-answer validation remain coordinator-owned, along with the compatible-memory-conflict repair.

Final follow-up regression run: **50tests passed in62.855s** using the combined command above after the recall operational-table fix and authorized `backend/retrieval/temporal.py` grammar patch. Current local evidence is retrieval correctness, not an11-question live score. During the user's status request, bounded inspection of `final-sessions/gemini600-20261017-repaired/manifest.json` found `status=stopped_invalid_provider_schema`; that saved rerun cannot establish the requested80–90% answer quality. Provider-schema recovery, compatible shared-memory conflict normalization and the next complete live semantic/visual evaluation remain outside this worker's edits.
