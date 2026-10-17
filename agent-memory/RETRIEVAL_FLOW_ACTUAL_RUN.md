# Actual retrieval flow: saved Jake conversation

Captured 2026-10-17T11:17:55.900177+00:00. Read-only trace; no model calls. User `U-102` (Jake), session `4a788ab7-8b5e-4828-83e3-c5f96f973765`.

## What runs the query

Gemma chooses a typed collection/metric/filter plan. The application validates it, then the injected provider deterministically compiles SQL, applies effective corrections/rules, joins source records and reports, and returns a ResultSet with coverage and source handles. Lexical document search is a separate `read_evidence` action; it is not the SQL compiler and cannot establish fleet totals.

## Actual saved sequence

| Question | Run | Saved state | Result row counts |
|---|---|---|---|
| how many assests we have and where show me there states | `6008d885-f48d-40dc-9e98-d75184b3a514` | complete | 1, 200 |
| i don't like this viwe cna you show me in the single row instead  of single column | `bb9c55a5-9aab-4aca-8fd7-7349f3840524` | complete | 1, 200 |
| show me whole dashbaord where i can see the trend of the well 1 all the details of it | `39c2406f-fce5-46ee-90bb-75e411abf80e` | complete | none |
| well-1 | `902ab3a1-52bc-40c6-af84-29436adf02be` | partial | 0, 0, 0, 0, 0, 0 |
| i want a dasbhbaord | `44b89e8b-208a-47af-92e9-3de301c62fd3` | partial | 0, 0, 0, 0, 0, 0, 0 |
| try again | `786ba553-27e5-4f4e-973c-84159018d02d` | complete | 200, 50, 40, 50 |

## Run `6008d885-f48d-40dc-9e98-d75184b3a514`

**Raw question:** how many assests we have and where show me there states

**Saved outcome:** complete; provider_timeout

**Displayed narrative:** There are 200 total assets [result_7ccd3de9db9a452fa43294d7c146ac2b]. The following table displays the recorded status and location for the available asset records [app:pages:16d3a5fa-321e-40dc-863c-3f1c812612d3].

**Validated planner JSON retained in stage cache:**
```json
{
  "intent": "count_and_locate_assets",
  "title": "Asset Population and Status Overview",
  "clarification": null,
  "direct_response": null,
  "queries": [
    {
      "collection": "assets",
      "metric": "count"
    },
    {
      "collection": "assets",
      "metric": "status",
      "group_by": [
        "area_id"
      ]
    }
  ],
  "evidence_searches": [],
  "memory_proposals": [],
  "requested_visuals": [
    "bar",
    "table"
  ],
  "reference_text": null
}
```

- Result `result_7ccd3de9db9a452fa43294d7c146ac2b`: 1 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 200, "evaluated": 200, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 1, "displayed_rows": 1, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `app:pages:16d3a5fa-321e-40dc-863c-3f1c812612d3`: 200 returned rows; first asset IDs ["WELL-0001", "WELL-0002", "WELL-0003", "WELL-0004", "WELL-0005", "WELL-0006", "WELL-0007", "WELL-0008"]. Coverage: `{"unit": "matching_source_record", "matching": 200, "evaluated": 200, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 200, "displayed_rows": 200, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.

**Evidence-packet accounting recorded by this run:**
```json
{
  "method": "conservative_utf8_bytes_not_exact_tokens",
  "long_term": 274,
  "long_term_cap": 2000,
  "short_term": 478,
  "short_term_cap": 1000,
  "omitted_private": 0,
  "omitted_shared": 0,
  "omitted_dialogue": 0,
  "omitted_reference_handles": 0,
  "retrieved_context": 1906,
  "retrieved_cap": 2000,
  "omitted_evidence_or_rows": 402,
  "partial_evidence": true,
  "content_cap": 5000,
  "instructions_and_catalog_bytes": 9778,
  "current_request_bytes_separate": 55,
  "output_reserve": "Local bounded JSON/field limits; provider output limit unverified, observed usage recorded"
}
```

**ViewPlan panels:** `[{"type": "status", "result_set_id": "result_7ccd3de9db9a452fa43294d7c146ac2b", "encoding": {"label": "count", "value": "count"}}, {"type": "table", "result_set_id": "app:pages:16d3a5fa-321e-40dc-863c-3f1c812612d3", "encoding": {}}, {"type": "map", "result_set_id": "app:pages:16d3a5fa-321e-40dc-863c-3f1c812612d3", "encoding": {"latitude": "lat", "longitude": "lon", "label": "asset_id", "value": "producing"}}]`.

**Warnings generated during the run:** `["One or more requested visual kinds could not be validated; verified data remains available"]`.

## Run `bb9c55a5-9aab-4aca-8fd7-7349f3840524`

**Raw question:** i don't like this viwe cna you show me in the single row instead  of single column

**Saved outcome:** complete; no current error code

**Displayed narrative:** Rearranged the same verified results into one row.

**Validated planner JSON retained in stage cache:**
```json
{
  "intent": "reformat_presentation",
  "title": "Asset Status View Reformat",
  "clarification": "I understand you would like to change the layout of the asset status list from a vertical (single column) orientation to a horizontal (single row) orientation. To ensure I provide the correct data in the format you prefer, are you referring to a summary row of key metrics for all assets, or simply a different table layout for the existing asset list?",
  "direct_response": null,
  "queries": [
    {
      "collection": "assets",
      "metric": "status",
      "limit": 100
    }
  ],
  "evidence_searches": [],
  "memory_proposals": [
    {
      "kind": "preference",
      "scope": "private",
      "subject_kind": "user",
      "subject_ids": [
        "U-102"
      ],
      "statement": "User prefers data presentation in a single row format rather than a single column format.",
      "source_quote": "i don't like this viwe cna you show me in the single row instead of single column",
      "valid_from": null,
      "valid_to": null,
      "planned_start": null,
      "planned_end": null,
      "qualifier": "attributed",
      "target_record_id": null,
      "field": null,
      "value": null,
      "reason": null,
      "rule_id": null,
      "well_type": null,
      "equipment_kind": null,
      "threshold": null,
      "lookback_months": 12,
      "supersedes": null
    }
  ],
  "requested_visuals": [
    "horizontal_summary"
  ],
  "reference_text": null
}
```

- Result `result_7ccd3de9db9a452fa43294d7c146ac2b`: 1 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 200, "evaluated": 200, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 1, "displayed_rows": 1, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `app:pages:16d3a5fa-321e-40dc-863c-3f1c812612d3`: 200 returned rows; first asset IDs ["WELL-0001", "WELL-0002", "WELL-0003", "WELL-0004", "WELL-0005", "WELL-0006", "WELL-0007", "WELL-0008"]. Coverage: `{"unit": "matching_source_record", "matching": 200, "evaluated": 200, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 200, "displayed_rows": 200, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.

**Evidence-packet accounting recorded by this run:**
```json
{
  "method": "conservative_utf8_bytes_not_exact_tokens",
  "long_term": 274,
  "long_term_cap": 2000,
  "short_term": 478,
  "short_term_cap": 1000,
  "omitted_private": 0,
  "omitted_shared": 0,
  "omitted_dialogue": 0,
  "omitted_reference_handles": 0,
  "retrieved_context": 1906,
  "retrieved_cap": 2000,
  "omitted_evidence_or_rows": 402,
  "partial_evidence": true,
  "content_cap": 5000,
  "instructions_and_catalog_bytes": 9778,
  "current_request_bytes_separate": 55,
  "output_reserve": "Local bounded JSON/field limits; provider output limit unverified, observed usage recorded"
}
```

**ViewPlan panels:** `[{"type": "status", "result_set_id": "result_7ccd3de9db9a452fa43294d7c146ac2b", "encoding": {"label": "count", "value": "count"}}, {"type": "table", "result_set_id": "app:pages:16d3a5fa-321e-40dc-863c-3f1c812612d3", "encoding": {}}, {"type": "map", "result_set_id": "app:pages:16d3a5fa-321e-40dc-863c-3f1c812612d3", "encoding": {"latitude": "lat", "longitude": "lon", "label": "asset_id", "value": "producing"}}]`.

**Warnings generated during the run:** `["One or more requested visual kinds could not be validated; verified data remains available"]`.

## Run `39c2406f-fce5-46ee-90bb-75e411abf80e`

**Raw question:** show me whole dashbaord where i can see the trend of the well 1 all the details of it

**Saved outcome:** complete; no current error code

**Displayed narrative:** Your history contains several possible wells or incidents. Which well and incident do you mean?

**Planner JSON:** not available in the typed stage cache for this older execution; do not infer its exact JSON from the final answer.


**Evidence-packet accounting recorded by this run:**
```json
{}
```

**ViewPlan panels:** `[]`.

**Warnings generated during the run:** `["Private reference absent; another user's history was not searched."]`.

## Run `902ab3a1-52bc-40c6-af84-29436adf02be`

**Raw question:** well-1

**Saved outcome:** partial; invalid_narrative_citation

**Displayed narrative:** Partial answer: verified data is shown below. The explanation could not be completed because the generated response did not complete or pass its evidence checks.

**Validated planner JSON retained in stage cache:**
```json
{
  "intent": "provide_comprehensive_asset_dashboard",
  "title": "Well-1 Operational Trend & Detail Dashboard",
  "clarification": "I will generate a comprehensive dashboard for 'well-1'. Since 'well-1' is a name and not a confirmed ID, I will first search for the matching asset ID to ensure all subsequent telemetry and maintenance data is accurate.",
  "direct_response": null,
  "queries": [
    {
      "collection": "assets",
      "metric": "records",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "inspections",
      "metric": "temperature_series",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "maintenance",
      "metric": "corrective_count",
      "filters": {
        "asset_id": "well-1"
      },
      "group_by": [
        "equipment_kind"
      ]
    },
    {
      "collection": "maintenance",
      "metric": "maintenance_cost_usd",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "inspections",
      "metric": "compliance",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "inspections",
      "metric": "spills",
      "filters": {
        "asset_id": "well-1"
      }
    }
  ],
  "evidence_searches": [
    {
      "description": "Search for maintenance reports and RCA documents related to well-1 to provide context for downtime or corrective actions.",
      "source_types": [
        "maintenance",
        "context_notes"
      ]
    }
  ],
  "memory_proposals": [],
  "requested_visuals": [
    "line",
    "bar",
    "table",
    "table"
  ],
  "reference_text": ""
}
```

- Result `result_35b6ff70f64249519f69745663999311`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_3db9bd49aabf4b2a97d0fb6d1077b3fe`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_4d6ee6d8a2d9441eb9ef16a5aa46dc8e`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_8bb8642617ac4966ad802b2b71445175`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_701d41a34e1145f4979a6e345d181857`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "incident_protocol_requirement", "matching": 0, "evaluated": 0, "unknown": 0, "source_incidents": 0, "import_issues": 0, "status": "complete", "displayed_rows": 0, "output_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_1e2d3c9f0f2f432ba0e30a44de804971`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.

**Evidence-packet accounting recorded by this run:**
```json
{
  "method": "conservative_utf8_bytes_not_exact_tokens",
  "long_term": 600,
  "long_term_cap": 2000,
  "short_term": 553,
  "short_term_cap": 1000,
  "omitted_private": 2,
  "omitted_shared": 0,
  "omitted_dialogue": 3,
  "omitted_reference_handles": 1,
  "retrieved_context": 1623,
  "retrieved_cap": 2000,
  "omitted_evidence_or_rows": 10,
  "partial_evidence": true,
  "content_cap": 5000
}
```

**ViewPlan panels:** `[{"type": "table", "result_set_id": "result_35b6ff70f64249519f69745663999311", "encoding": {}}, {"type": "table", "result_set_id": "result_3db9bd49aabf4b2a97d0fb6d1077b3fe", "encoding": {}}, {"type": "table", "result_set_id": "result_4d6ee6d8a2d9441eb9ef16a5aa46dc8e", "encoding": {}}, {"type": "table", "result_set_id": "result_8bb8642617ac4966ad802b2b71445175", "encoding": {}}, {"type": "table", "result_set_id": "result_701d41a34e1145f4979a6e345d181857", "encoding": {}}, {"type": "table", "result_set_id": "result_1e2d3c9f0f2f432ba0e30a44de804971", "encoding": {}}]`.

**Warnings generated during the run:** `["Recorded costs can include estimates for in-progress work", "Assessment supports supplied SR-01 written notice, SR-02 elapsed containment, SR-03 agency verification and RC-04 response only; it is not an exhaustive safety/legal compliance audit", "Missing records are not independent proof of real-world inaction; same-day deadline time is not assumed passed from a calendar reference date", "Evidence search unavailable: Supply searchable text or a registered evidence handle", "Explanation unavailable: invalid_narrative_citation"]`.

## Run `44b89e8b-208a-47af-92e9-3de301c62fd3`

**Raw question:** i want a dasbhbaord

**Saved outcome:** partial; unsupported_narrative_number

**Displayed narrative:** Partial answer: verified data is shown below. The explanation could not be completed because the generated response did not complete or pass its evidence checks.

**Validated planner JSON retained in stage cache:**
```json
{
  "intent": "create_dashboard",
  "title": "Well-1 Operational Intelligence Dashboard",
  "clarification": "I am designing a comprehensive dashboard for 'well-1'. To ensure the dashboard is complete, I will aggregate its thermal trends, maintenance history, spill/compliance data, and production status. Please confirm if 'well-1' refers to a specific Asset ID (e.g., WELL-001) or if I should search for all assets matching that name.",
  "direct_response": null,
  "queries": [
    {
      "collection": "assets",
      "metric": "status",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "inspections",
      "metric": "temperature_series",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "maintenance",
      "metric": "corrective_count",
      "filters": {
        "asset_id": "well-1"
      },
      "group_by": [
        "equipment_kind"
      ]
    },
    {
      "collection": "maintenance",
      "metric": "maintenance_cost_usd",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "inspections",
      "metric": "spills",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "inspections",
      "metric": "compliance",
      "filters": {
        "asset_id": "well-1"
      }
    },
    {
      "collection": "inspections",
      "metric": "downtime_days",
      "filters": {
        "asset_id": "well-1"
      }
    }
  ],
  "evidence_searches": [
    {
      "description": "Search for any specific maintenance reports or RCA (Root Cause Analysis) documentation linked to well-1 to provide context for downtime or corrective actions.",
      "coverage": "maintenance, context_notes"
    }
  ],
  "memory_proposals": [],
  "requested_visuals": [
    "line",
    "bar",
    "bar",
    "table",
    "heatmap"
  ],
  "reference_text": null
}
```

- Result `result_8be8e48e93e5445ebcfed6a4faa2e536`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_d0c2edf8eab54993922edfc65b0dbb06`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_8aeaf418a972471aae0079b3d94e3d27`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_d2d67184cb1c4177b472f8264708678d`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_04d061bcfcef443985ebd466d8130f8b`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_7ef8b39e0647435a80a4b4fd0a684930`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "incident_protocol_requirement", "matching": 0, "evaluated": 0, "unknown": 0, "source_incidents": 0, "import_issues": 0, "status": "complete", "displayed_rows": 0, "output_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_067b0c2620584c86a27e65242da6d9cf`: 0 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 0, "evaluated": 0, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 0, "displayed_rows": 0, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.

**Evidence-packet accounting recorded by this run:**
```json
{
  "method": "conservative_utf8_bytes_not_exact_tokens",
  "long_term": 600,
  "long_term_cap": 2000,
  "short_term": 557,
  "short_term_cap": 1000,
  "omitted_private": 2,
  "omitted_shared": 0,
  "omitted_dialogue": 6,
  "omitted_reference_handles": 1,
  "retrieved_context": 1623,
  "retrieved_cap": 2000,
  "omitted_evidence_or_rows": 12,
  "partial_evidence": true,
  "content_cap": 5000
}
```

**ViewPlan panels:** `[{"type": "table", "result_set_id": "result_8be8e48e93e5445ebcfed6a4faa2e536", "encoding": {}}, {"type": "table", "result_set_id": "result_d0c2edf8eab54993922edfc65b0dbb06", "encoding": {}}, {"type": "table", "result_set_id": "result_8aeaf418a972471aae0079b3d94e3d27", "encoding": {}}, {"type": "table", "result_set_id": "result_d2d67184cb1c4177b472f8264708678d", "encoding": {}}, {"type": "table", "result_set_id": "result_04d061bcfcef443985ebd466d8130f8b", "encoding": {}}, {"type": "table", "result_set_id": "result_7ef8b39e0647435a80a4b4fd0a684930", "encoding": {}}, {"type": "table", "result_set_id": "result_067b0c2620584c86a27e65242da6d9cf", "encoding": {}}]`.

**Warnings generated during the run:** `["Recorded costs can include estimates for in-progress work", "Assessment supports supplied SR-01 written notice, SR-02 elapsed containment, SR-03 agency verification and RC-04 response only; it is not an exhaustive safety/legal compliance audit", "Missing records are not independent proof of real-world inaction; same-day deadline time is not assumed passed from a calendar reference date", "Evidence search unavailable: Supply searchable text or a registered evidence handle", "Explanation unavailable: unsupported_narrative_number"]`.

## Run `786ba553-27e5-4f4e-973c-84159018d02d`

**Raw question:** try again

**Saved outcome:** complete; no current error code

**Displayed narrative:** The asset dashboard for Southwest Block 23 shows 4 primary assets with varying operational statuses. WELL-0001 is recorded as active but is not producing, with an observation that the pump jack is not moving [app:pages:facfd9ce-2f09-42d9-814b-519216763944]. WELL-0002 is recorded as down despite producing [app:pages:facfd9ce-2f09-42d9-814b-519216763944]. WELL-0003 and WELL-0004 are both active and producing [app:pages:facfd9ce-2f09-42d9-814b-519216763944].

**Validated planner JSON retained in stage cache:**
```json
{
  "intent": "dashboard_request",
  "title": "Field Asset & Compliance Overview",
  "clarification": "The request 'try again' follows a previous request for a 'dashboard'. To provide a comprehensive operational dashboard, I will aggregate asset status, maintenance trends, spill metrics, and regulatory compliance. Please specify if you would like to filter this dashboard by a specific Area (e.g., Northeast Block 7) or Team.",
  "direct_response": null,
  "queries": [
    {
      "collection": "assets",
      "metric": "status",
      "filters": {},
      "limit": 100
    },
    {
      "collection": "maintenance",
      "metric": "maintenance_cost_usd",
      "group_by": [
        "asset_id"
      ],
      "start": "2026-01-01"
    },
    {
      "collection": "inspections",
      "metric": "spill_count",
      "group_by": [
        "area_id",
        "month"
      ],
      "start": "2026-01-01",
      "end": "2026-10-16"
    },
    {
      "collection": "inspections",
      "metric": "compliance",
      "start": "2025-10-16"
    }
  ],
  "evidence_searches": [
    {
      "description": "Search for regulatory SOPs and compliance requirements to validate compliance assessment results.",
      "coverage": "regulatory_events, context_notes"
    }
  ],
  "memory_proposals": [],
  "requested_visuals": [
    "table",
    "bar",
    "heatmap",
    "table"
  ],
  "reference_text": null
}
```

- Result `app:pages:facfd9ce-2f09-42d9-814b-519216763944`: 200 returned rows; first asset IDs ["WELL-0001", "WELL-0002", "WELL-0003", "WELL-0004", "WELL-0005", "WELL-0006", "WELL-0007", "WELL-0008"]. Coverage: `{"unit": "matching_source_record", "matching": 200, "evaluated": 200, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 200, "displayed_rows": 200, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_9a8f4540aea34aaeb6a260c392f4213a`: 50 returned rows; first asset IDs ["WELL-0123", "WELL-0069", "WELL-0013", "WELL-0183", "WELL-0092", "WELL-0199", "WELL-0160", "WELL-0138"]. Coverage: `{"unit": "matching_source_record", "matching": 1238, "evaluated": 1238, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 200, "displayed_rows": 50, "display_truncated": true, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_fc41908d3cba4ad18a562423ca71b00b`: 40 returned rows; first asset IDs []. Coverage: `{"unit": "matching_source_record", "matching": 141, "evaluated": 141, "unknown": 0, "import_issues": 0, "status": "complete", "output_rows": 40, "displayed_rows": 40, "display_truncated": false, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.
- Result `result_e9e72546b8fb4b63b27b66f16054ecc5`: 50 returned rows; first asset IDs ["WELL-0001", "WELL-0002", "WELL-0005", "WELL-0007", "WELL-0010", "WELL-0013", "WELL-0015", "WELL-0017"]. Coverage: `{"unit": "incident_protocol_requirement", "matching": 191, "evaluated": 191, "unknown": 0, "source_incidents": 165, "import_issues": 0, "status": "complete", "displayed_rows": 50, "output_rows": 191, "display_truncated": true, "aggregation_input_truncated": false}`.
Trace handle could not be opened: RetrievalError.

**Evidence-packet accounting recorded by this run:**
```json
{
  "method": "conservative_utf8_bytes_not_exact_tokens",
  "long_term": 600,
  "long_term_cap": 2000,
  "short_term": 557,
  "short_term_cap": 1000,
  "omitted_private": 2,
  "omitted_shared": 0,
  "omitted_dialogue": 8,
  "omitted_reference_handles": 1,
  "retrieved_context": 1979,
  "retrieved_cap": 2000,
  "omitted_evidence_or_rows": 715,
  "partial_evidence": true,
  "content_cap": 5000,
  "instructions_and_catalog_bytes": 9778,
  "current_request_bytes_separate": 9,
  "output_reserve": "Local bounded JSON/field limits; provider output limit unverified, observed usage recorded"
}
```

**ViewPlan panels:** `[{"type": "table", "result_set_id": "app:pages:facfd9ce-2f09-42d9-814b-519216763944", "encoding": {"asset_id": "asset_id", "recorded_status": "recorded_status", "producing": "producing"}}, {"type": "map", "result_set_id": "app:pages:facfd9ce-2f09-42d9-814b-519216763944", "encoding": {"latitude": "lat", "longitude": "lon", "label": "asset_id", "value": "producing"}}, {"type": "bar", "result_set_id": "app:pages:facfd9ce-2f09-42d9-814b-519216763944", "encoding": {"x": "asset_id", "y": "delta_c"}}, {"type": "heatmap", "result_set_id": "app:pages:facfd9ce-2f09-42d9-814b-519216763944", "encoding": {"x": "asset_id", "y": "area_name", "value": "delta_c"}}]`.

**Warnings generated during the run:** `["Recorded costs can include estimates for in-progress work", "Assessment supports supplied SR-01 written notice, SR-02 elapsed containment, SR-03 agency verification and RC-04 response only; it is not an exhaustive safety/legal compliance audit", "Missing records are not independent proof of real-world inaction; same-day deadline time is not assumed passed from a calendar reference date", "Evidence search unavailable: Supply searchable text or a registered evidence handle"]`.

## Where the scope went wrong

1. Earlier alias handling matched well-shaped text without resolving against the actual asset catalog. `well-1` could reach a literal `WELL-1` filter instead of canonical `WELL-0001`; an empty query result was then presented as several empty partial panels. The current workspace fix resolves case/spacing/hyphen/leading-zero aliases against catalog identities, accepts only unique matches, and clarifies unknown or ambiguous names before domain queries. This fix is not evidence that the older runs used it.
2. The later generic dashboard request could inherit the user’s older 200-well episode because explicit user focus was not retained when the earlier well request failed. The new private session focus records a resolved explicit user asset even on failure and carries the pending dashboard intent. It is never shared operational knowledge.
3. A preview is not the whole population. The saved ResultSet row counts/coverage above are the actual scope; prose such as “four primary assets” or “first five” can describe a preview while the table/map still contains many assets. That is a maker/scope explanation failure, not proof that SQL returned only those preview rows.
4. Layout-only instructions previously went through planning and explanation again. The repaired layout run preserves the original fleet ResultSets, evidence and all three panels, adds `layout.mode=single_row`, and makes no model or retrieval call. Its prior bad envelope is archived.

## Empty lexical searches and packet limits

A planner evidence-search object with `description/query_params` but no `terms` or `query` becomes an empty search string. Provider search rejects it with “Supply searchable text or a registered evidence handle”; the service adds an evidence-search-unavailable warning. This does not mean the SQL result is empty. Search uses lexical FTS ranking and asset/document-kind filters; record queries use validated typed filters and deterministic SQL.

The recorded budget objects above show actual preview/source omissions. Full ResultSets stay server-side. Current content packing uses conservative UTF-8 byte ceilings (2K long-term total,1K chat,2K fresh evidence), not a measured exact 2K-token capacity; this can underfill the model allowance. The exact old maker input packet is not retained as a separately named artifact for every run. An input hash or a reconstructed packet must not be called the exact historical packet.

## Source and interface references

- Runtime authority/history: `runtime/memory.sqlite`; scoped stage cache: `stage_results`; original failed/partial and layout revisions remain traceable.
- Provider manifest/traces: `runtime/retrieval.sqlite`, accessed here through `RetrievalProvider.trace`.
- SDK requests/usage/quota: `runtime/model-requests.sqlite`.
- Public application contract: [backend-api-contract.md](../../agent-memory/backend-api-contract.md).
- Compiler/provider implementation: `backend/retrieval/provider.py`; orchestration and packing: `backend/chains/service.py`, `backend/memory/budget.py`.

This document reports saved execution, not an all-scenarios success claim.
