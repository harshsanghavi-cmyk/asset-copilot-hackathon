# What actually happened to the “well 1” dashboard

Read-only review,17Oct2026. This is the saved conversation, not an architecture proposal.
User: Jake/U-102; session `4a788ab7-8b5e-4828-83e3-c5f96f973765`.
No model/API calls, code changes or runtime writes were made for this document.
For retained JSON payloads, see [the detailed trace](RETRIEVAL_FLOW_ACTUAL_RUN.md).

## The short answer

The original “well 1” request was not resolved to canonical **WELL-0001**.
One turn stopped at a false ambiguous-history clarification; the next sent literal
`well-1` filters to six record queries, which all returned zero rows.
A later retry lost the intended one-well scope and retrieved fleet data instead.
The maker then described its few preview rows as if they were the whole scope.
That is why a small Southwest23 narrative could accompany a map of many wells.

## Saved turns: requested scope versus actual scope

| Run | Request | Actual saved outcome |
|---|---|---|
| `bb9c55a5-9aab-4aca-8fd7-7349f3840524` | Same fleet results, single row | Original answer said “first five assets in Southwest Block23,” had one panel but200 data rows. Archived original remains; saved answer was later repaired to three reused panels, count+200 rows, `layout.mode=single_row`. |
| `39c2406f-fce5-46ee-90bb-75e411abf80e` | Whole dashboard/trend for “well1” | False ambiguous-history clarification; zero panels, no data results. Only read_context is retained for this execution; do not invent a planner call. |
| `902ab3a1-52bc-40c6-af84-29436adf02be` | “well-1,” clarifying that same well | Six typed queries used literal well-1; six zero-row results. Final status partial, error invalid_narrative_citation, six fallback tables. |
| `44b89e8b-208a-47af-92e9-3de301c62fd3` | “i want a dasbhbaord” | Seven queries still used well-1; seven zero-row results. Partial answer, unsupported_narrative_number, seven fallback tables. |
| `786ba553-27e5-4f4e-973c-84159018d02d` | “try again,” following that request | Fleet-status query with empty filters; results200/50/40/50 rows. Narrative says “4 primary assets” in Southwest23, but table/map/bar/heatmap all bind the200-row fleet-status result. |

The saved “four primary assets” wording belongs to retry `786ba553…`, not to
the seven-empty-result `44b89e8b…` answer. A screenshot alone cannot distinguish them.

## The actual retrieval sequence

1. **Identify scope before planning.** The failed old path used private conversation
   references without first establishing that well1 uniquely meant WELL-0001.
   Today the code builds aliases from the actual asset catalog, compares normalized
   IDs/names, and stores explicit private session focus plus pending dashboard intent.
   These are code fixes; they were not present in the old saved executions.
2. **Gemma proposes the typed plan.** For `902ab3a1…`, the retained planner says it
   will find the matching ID, but its actual queries already use the unresolved text:
   ```json
   {"collection":"assets","metric":"records","filters":{"asset_id":"well-1"}}
   ```
   The other five operations were temperature_series, corrective_count grouped by
   equipment_kind, maintenance_cost_usd, compliance, and spills—with that same filter.
3. **Application validates; provider compiles and executes.** These are deterministic
   typed record queries, not Gemma-generated SQL. The ID filter matches no canonical
   asset, so results contain0/0/0/0/0/0 rows. Existing WELL-0001 data was not absent.
   Result IDs start `result_35b6ff…`, `result_3db9bd…`, `result_4d6ee6…`,
   `result_8bb864…`, `result_701d41…`, `result_1e2d3c…` respectively.
4. **Reports/rules and search are separate.** Normal source resolution follows
   record/report handles and manual/SOP evidence. Optional lexical FTS search then
   reads terms/query plus allowed asset/kind filters. This run instead supplied:
   ```json
   {"description":"Search for maintenance reports and RCA documents related to well-1 to provide context for downtime or corrective actions.","source_types":["maintenance","context_notes"]}
   ```
   There is no terms or query field. The service passed an empty string; the provider
   rejected it before FTS execution. This is a failed search argument, not zero hits.
5. **Pack evidence for the maker.** Full results stay server-side; the model sees a
   bounded selection. This run records retrieved_context1623,10 omitted items/rows,
   partial_evidence=true. Retry `786ba553…` records1979 and715 omitted items/rows.
   These are conservative UTF-8-byte accounting units, not measured Gemma tokens.
6. **Gemma makes prose/ViewPlan; application checks it.** For `902ab3a1…`, citation
   validation failed, so the saved UI payload became an explicit partial explanation
   with six empty tables. For `786ba553…`, the maker's narrative narrowed the scope
   to four Southwest23 preview wells while the200-row result still covered the fleet.
7. **UI renders the referenced results.** In retry `786ba553…`, table/map/bar/heatmap
   all reference `app:pages:facfd9ce-2f09-42d9-814b-519216763944`. Its200 rows, not
   the four wells named in prose, drive those panels. No well-specific trend was shown.

Historical provider trace handles have expired; exact executed SQL could not be
opened. Typed plans, stage results, coverage and final envelopes are retained.
The exact old maker input pack is not separately retained for every run; recorded
omission counts do not reconstruct its exact text. No invented SQL/packet is quoted here.

## What the four warnings mean

| Warning | Actual meaning |
|---|---|
| Costs may include estimates | The plan requested job costs. In-progress repairs can hold estimated recorded costs; they are not necessarily invoiced/paid amounts. This warning is not proof of a cost error or the cause of empty rows. |
| SR/RC assessment is limited | The compliance operation covers SR-01 written notice, SR-02 containment, SR-03 passing agency verification and RC-04 NOV response. It does not certify every safety/legal duty. |
| Missing records do not prove inaction | No recorded notice/response is not independent proof none happened. A date-only reference also does not establish an exact same-day deadline hour passed. |
| Evidence search unavailable | The planner's description/source_types object lacked terms/query. The empty search string was rejected. Record-query execution is independent of that failed FTS request. |

## Fixed in code versus proved by this conversation

- **Present in code:** catalog-backed alias resolution; owner-scoped focus/pending
  intent; layout-only reuse without new retrieval/model calls. The repaired layout
  answer is saved with three panels and the original200-row fleet scope.
- **Still an old failed answer:** the zero-row well-1 turns and four-primary-assets
  retry remain as recorded; code edits do not retroactively make them correct.
- **Still unverified here:** a fresh well1 dashboard must resolve WELL-0001, keep that
  scope through clarification/failure/retry, retrieve its actual trend/details, and
  make prose agree with all displayed panels. A preview must never redefine scope.

Sources inspected: owner/session-scoped rows in runtime/memory.sqlite (runs,
stage_results, answer_revisions); declared result/manifests and the linked detailed
export; backend/chains/service.py (asset_references, focus, query/search/maker flow),
backend/retrieval/provider.py (typed compiler/FTS/warnings), backend/ingestion/loader.py
(immutable source indexing). Current model is Gemma26B via Google SDK. No private
history outside the named session, credentials or complete history dump is included.
