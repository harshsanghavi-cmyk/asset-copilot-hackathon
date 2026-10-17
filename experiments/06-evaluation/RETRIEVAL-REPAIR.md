# Retrieval repair — actual failures and tested boundary

17 Oct 2026. **Latest delivery is the replacement600-well dataset only**, source009e2b596782150f420021f9472ab37e3a2953ee, reference2027-01-15. The earlier200-well regression evidence below remains a separate historical test fixture, not a serving fallback. No model/API calls, prompt/chain/memory/evaluator/frontend edits, services, new sessions or original-data writes. Current model selection was left untouched.

## Replacement600 index and data semantics

Built **runtime/retrieval-test.sqlite** from only `dataset/test-data/dataset`, namespace **asset-field-test-2027-01-15**, revision **687ade729fe09c4d15c18a94ae102fcbcf8f4868fda89eaeb140ce54a7756716**. No sample/test merge: IDs overlap and older records changed. The atomic staging build completed in28.643s after adding source/path indexes. The first staging-only build was interrupted after identifying repeated unindexed per-source record counts; it never replaced the old serving index.

Verified counts:600 assets,7 areas,6 teams,27 users,3076 equipment,125198 inspections,17415 maintenance,328 regulator events,1887 notes,197 baseline corrections,7451 sources,44503 chunks,3612 extracted facts,3 production rules and **0 import issues**. Integrity GO/path/namespace/date were sent to root/backend before the serving switch; no service restart was performed here.

Owned changes now include ingestion/loader.py, ingestion/schema.py, retrieval/provider.py, temporal.py and their dedicated tests. Essential additions:

- All3 optional `data_correction` notes become typed effective overlays, with originals and source provenance retained;194 false-positive corrections plus3 field corrections=197. The two corrected temperatures and corrected volume are used in later calculations.
- Each inspection uses its event-date type history, not today's type. Actual WELL-0010:19Nov uses T200/15°C,26Nov uses T350/20°C. Team history is event-dated and well-owned team metadata takes priority over area ownership; current TEAM-NW count independently matches150.
- Source manuals supply T20015/T35020/T50025°C rules. T500 ESP RCA threshold2 is scoped to ESP; other equipment follows the declared T200 inheritance at3. No pump-jack movement inference is used to classify an ESP.
- OPS-3 is activated only when its supplied SOP exists and is effective. Later shut-in notes override an older inspection; later restart notes produce an explicit unconfirmed state until inspection confirmation. Gas/bypass/equipment notes do not become restart events. Plugged/decommissioned assets cannot be treated as currently producing merely because their last old inspection was hot.
- Current status exposes `inspection_producing`, `status_now`, `status_confirmed`, `status_source`, latest status-note ID/time/text/author and `status_note_disagrees`. A boolean status_note_disagrees filter enumerates matching assets before presentation pagination; evidence references include source notes/rules/corrections. This does not turn private conversations into source data.
- Team ID filtering/grouping and display names are available. Late-entered records remain ordered by actual observation/job date, not file position; recorded_at and original/revised cost audit fields are exposed while revised cost_usd remains effective.
- New manuals/SOPs/MOC/recall/letter documents are registered/chunked/searchable. Added records(source_id) and sources(path,kind) indexes avoid repeated scans during600-well rebuilds; no schema-column migration was necessary.

Validation: combined25 sample +5 replacement-data +4 pure timeline tests passed **34/34 in29.775s** after temporal/field/filter integration. Tests use temporary read-only index backups and separate synthetic fixtures. Current-status evidence additionally references original metadata for type/team/decommissioning provenance; that final metadata-evidence/status regression passed separately in13.180s. No new live-model or UI answer is claimed. Commands:

```sh
backend/.venv/bin/python -B -m unittest backend.retrieval.test_provider -v
backend/.venv/bin/python -B -m unittest backend.retrieval.test_final_dataset backend.retrieval.test_temporal -v
```

**Final11 capability limits:** no supplied measured reservoir-pressure/oil-produced-volume columns support finalQ1/Q2; do not substitute wellhead/flowline ratings or thermal deltas. Gas-response OPS-1, bypass/MOC validity, recalled-pump inventory, regulator-letter-specific scope, predictive ranking and area delay-reason aggregation are not implemented deterministic metrics in this patch. Their source prose is accessible, but lexical top-k cannot prove complete fleet enumeration or that those new duties are satisfied. Old SR/RC compliance is not a blanket OPS/letter assessment. Backend/coordinator received these gaps explicitly before final-query runs.

Safe rebuild if needed: `build_index([Path('dataset/test-data/dataset')], Path('runtime/retrieval-test.sqlite'), namespace='asset-field-test-2027-01-15')`; reload the injected provider after atomic publication. Generic dataset-wrapper discovery selects sample-data, so use the explicit replacement root. Keep final11 ordered multi-turn memory/reporting separate from the original18 sample fixtures.

## Original200-well failure repair (separate regression fixture)

## Diagnosed versus fixed

| Retained failure | Evidence and responsibility | Action |
|---|---|---|
| Q3:12 observations/no line | `result_588d2018ea8843db875a383296b1e802` requested24Jul–16Oct and correctly returned12;23Jul is excluded. Context3 + maintenance32 rows are separate results. | No provider padding or scenario branch. Tests prove23Jul→13 observations,24Jul→12 and down markers8/15Oct. Backend owns relative-week planning and visual completion. Root was told evaluator flattened all result rows; it reports fixing inspection-only dedup scoring. |
| Q8:48 heatmap cells, future Nov/Dec zeros | `result_7e8db03062e24bd78c98c11b57ffe64a` requested end31Dec although trusted reference is16Oct. The provider densified unobserved future months as zero. | **Fixed generically:** observed-data windows stop at reference date. Returns effective bounds plus original requested_bounds/warning; future-only observation requests fail explicitly. No future zero facts. |
| Q9:only2 duties narrated | `result_553327a8994e4f039968e80e8715d9f5` already contains all4 required findings: SR-01=41vs24h, SR-02=7vs4h, SR-03 due10Aug, RC-04 due30Jul/USD5000. It also contains October SR-02 met. | Not a missing-retrieval defect. Backend must preserve all duty coverage in packing/maker, distinguish supported breach/missing-record state and explain required open actions. Exact historical maker packet was not reconstructed or represented as retained. |
| Q2/Q12:known repair cause described as absent | Normal maintenance records had job type/equipment/time/cost but omitted issue/action text from their typed projection. Raw evidence still held it, so this was not absent original data. | **Fixed generic projection:** issue, action_taken, report_file and triggered_by_inspection_id now accompany maintenance records. Fields come from original job JSON/declared links through a one-to-one record-PK join, not inferred causes. |

The patches contain no example IDs, area counts, expected totals or question dispatch. Scenario IDs/values occur only in regression fixtures and this report. The `json_extract` function is explicitly admitted solely for compiler-owned fixed source paths; arbitrary model SQL remains rejected.

## Date semantics preserved

Observation queries use the trusted reference date; a2026 calendar-year spill query at16Oct now returns Jan–Oct, **40 cells**,141 effective spills. Every cell matches an independent raw JSON/JSONL oracle with formal false-positive exclusions, including the two Northeast8 zero cells.

An explicit31Dec request is disclosed in requested_bounds while effective bounds end16Oct; the warning explains exclusion. Planned maintenance is **not** clipped: a maintenance-record query ending31Dec retains that end, and the open bearing repair still has its future planned finish/in-progress state. Compliance deadlines such as23Nov remain future due dates; they are not future observed events and remain intact.

## Checks actually run

Command: `backend/.venv/bin/python -B -m unittest backend.retrieval.test_provider -v`.

FullSampleTests now creates a read-only SQLite backup of the serving/cached index inside a TemporaryDirectory; query manifests stay there. Synthetic contract tests use separate temporary raw fixtures. **25 tests passed** after the main patch; the final maintenance-field/planning-bound additions also passed their targeted regression. The original dataset Git tree remained clean. No canonical memory fixture was read or mutated by these tests.

New coverage: future source rows excluded at an earlier reference and available at a later one; future month bins excluded; requested/effective dates disclosed; all heatmap cells independently recomputed; exact series dates and markers; ordinary conflicting notes retained; typed repair causes/report links; cross-user effective-snapshot values without raw mutation. Existing checks retain complete aggregates before pagination, unknowns outside a page, containment spans, deadlines, scoped rules, source hashes/links and invalid-query rejection.

## Retrieval invariants mapped to all18 requirements

This is retrieval-layer evidence, **not18 live scenario passes**. Shared/private conversation admission, reference resolution, saved acknowledgments, maker accuracy and actual UI rendering are owned outside this patch.

| Scenario | Relevant checked invariant / remaining boundary |
|---|---|
| Q1 | Actual latest WELL-0001 status/3.2°C/Ryan and CTX-0001-003 plan/author/start are retrievable. Explanation and typed card binding still need live acceptance. |
| Q2 | Four expected down wells; typed bearing/flowline issue text is available. Correct known/unknown-cause narration remains maker-owned. |
| Q3 |13 exact readings and two down-marker dates for correct bounds; wrong24Jul plan returns12 rather than silently borrowing a reading. Line rendering is not tested here. |
| Q4 |6 effective spills/15.1bbl; baseline corrections retain originals. Runtime must cite corrections and list the actual events. |
| Q5 |21 observed days; job hours do not substitute. Full causal explanation still belongs to the answer layer. |
| Q6 |49/42/42 correct top-three values and full-population ranking before LIMIT. Requested bar remains UI/maker acceptance. |
| Q7 | Four expected well IDs with coordinates/volume columns and source-backed evidence. Actual map rendering is outside these tests. |
| Q8 | All40 Jan–Oct cells match raw-record oracle, including zeros; no future bins; totals remain35/43/37/26. |
| Q9 | All4 protocol findings/deadlines/fine available; current result may include met duties. Explain complete coverage, RCA and plan context rather than drop rows. |
| Q10 | Complete10-spill candidate coverage, report-only7.1/8.1h late containments, working breach filter and verified source spans. |
| Q11 | Three expected recorded costs25794/46942/5176USD and estimate warning. Private prior-three-well selection belongs to memory, not provider filters. |
| Q12 |41°C overlay changes effective production/area set; originals remain24°C. Formal write/author/reason/conflict acknowledgment needs backend acceptance. |
| Q13 |5.4bbl overlay reclassifies reportable; missing-notice state,25Sep15:30 written deadline and23Nov verification deadline computed; future deadline remains pending. |
| Q14 | T350 pump-jack2-repair override yields expected four, T2002-repair well excluded; scope and manual path remain independent. New-chat rule persistence is outside provider. |
| Q15 | Same supplied accepted correction snapshot gives41°C/producing to Jessica/Laura contexts at the same revision. This does not prove their actual memory fixture received the correction. |
| Q16 | Provider has no private-conversation store; shared remembered plans and negative private-history resolution require memory/API tests. No false claim of testing this whole sequence. |
| Q17 | Ordinary “running fine” shared claim does not overwrite WELL-0175's observed0.4°C/not-producing values. Claim retention/confirmation wording belongs to backend. |
| Q18 | Both ordinary CTX-0101-002/-003 are returned by asset; neither is a formal correction; inspection remains a1.0bbl detection. Maker must include both claims and repair context. |

## Handoff

Backend owner and root received the exact Q3/Q9 result IDs and responsibilities before edits. Reload the provider in the serving backend before fresh evaluation; no service restart was performed here. Old stored answers are unchanged. Root owns fresh run IDs/correction dependencies and evaluator scoring; backend owns relative windows, bounded evidence packing and complete explanations. No fresh live/e2e improvement is claimed until those outputs are generated and reviewed.
