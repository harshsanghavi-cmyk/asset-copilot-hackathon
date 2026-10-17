# Inspect the current replaceable retrieval candidate

This is a working deterministic candidate and diagnostic viewer, **not the final user-selected retrieval architecture**. Gemma enrichment/query expansion is not configured or tested here. No other runtime model, embedding or reranker is used.

Open the running frontend at `http://localhost:5190/admin.html`. Its dedicated local-admin proxy requires the explicit loopback diagnostic capability configured by the backend/frontend owners; a chat user ID does not grant admin access. Server-side diagnostic tokens stay out of the browser. An unconfigured/denied API shows an error rather than fixture data.

Review in this order:

1. **Storage map:** actual source counts, folder→table mapping, stored content/method, relations and index manifest.
2. **Sources:** filter by well/path; inspect a bounded 8 KiB source preview/hash and follow parsed-record or chunk links. Pages contain twenty records, server maximum one hundred.
3. **Parsed / effective:** select inspections and a well, then compare unchanged original JSON with effective field overlays and attributed corrections. Runtime authority comes from the separate memory backend.
4. **Chunks & index / Enrichment:** original UTF-8 spans, section text, protocol/entity tags and deterministic containment assertions. “span verified” means text support, not independent field verification. Narrative/table duplicates retain separate source spans.
5. **Query inspector:** two separate operations. **Search maintenance report text** uses the text field and lexical report search. **Run explicit manual plan** uses only collection/metric/filter/date/group controls and is labeled accordingly. Neither invokes a natural-language Gemma planner. A report query must never silently become a generic status answer.
6. **Execution traces:** inspect actual plan, involved stores, compiler SQL, redacted bound parameters, full matched population, selected/omitted evidence, coverage and estimated content accounting. UTF-8 units are a conservative packing estimate, **not measured Gemma tokens**.
7. **Saved memory / changes / compaction:** bounded backend-owned admin APIs show private/shared facts, owner, author, validity, timestamps/revisions and capsule/summary state. Empty real state is shown as empty, not seeded fake memory.

The user-requested executed Markdown walkthrough is [WELL-0001-WALKTHROUGH.md](WELL-0001-WALKTHROUGH.md), authored by the UI worker after ownership transfer. Do not overwrite it. The existing actual-data walkthrough route also remains available at `/admin.html#walkthrough?asset_id=WELL-0001`; it is not a claim that the architecture was approved.

## Repeat verification

From the project root, with the supplied same-format dataset acquired separately:

```sh
python3 -m unittest backend.retrieval.test_provider -v
backend/.venv/bin/python experiments/05-retrieval-viewer/http_smoke.py
frontend/node_modules/.bin/tsc --noEmit -p frontend/tsconfig.json
```

The dataset is an ignored independent MIT-licensed clone. Acquire the repository/revision in `docs/dataset-source.json`; the adapter accepts a list of roots with `fleet/` and `assets/`, never a fixed well range or report filename. Index output goes outside those source roots. No code in this experiment reads root `.env` or calls a model.

The actual index lives in ignored `backend/retrieval/.cache/dataset.sqlite` for these checks, with separately persisted derived lineage manifests. Runtime backend may use its own index path. `create_provider([...], db_path, rebuild=True)` rebuilds into a staging file and replaces the index atomically; re-create the provider to read the new index. Serialize rebuilds per target path. Canonical memory/corrections are not rebuilt or overwritten.

Evidence: `provider-tests.txt`, `http-smoke-results.json`, and captured real-browser screenshots in this folder. These verify the candidate's tested data/read behavior, **not an all-Q1–Q18 live Gemma pass or production security guarantee**. The live model workflow and final submission assessment remain backend/coordinator-owned.

Latest receipts: **19/19 provider tests, 10/10 in-process real-provider HTTP checks, frontend typecheck passed**. `browser-checks.json` records the actual report-search/manual-disable regression. `storage-map-desktop.png`, `report-search-desktop.png`, `query-trace-desktop.png` and `source-evidence-desktop.png` are actual 1440×1000 desktop captures. The report search is a ranked sample of document assertions; it is never presented as an exhaustive true-spill asset list.
