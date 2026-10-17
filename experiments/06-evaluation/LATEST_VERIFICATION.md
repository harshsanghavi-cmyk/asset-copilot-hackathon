# Latest verified fixes — 17 October 2026

This supplements the initial QA_REPORT.md. It does not replace failed historical runs or claim all18 official scenarios pass.

## Exact user fleet question: completed

Question: “how many assests we have and where show me there states”.

- Owner: Jake Morales/U-102; existing conversation `4a788ab7-8b5e-4828-83e3-c5f96f973765`.
- Answer/run: `6008d885-f48d-40dc-9e98-d75184b3a514`.
- Independently fetched from the owner-scoped backend answer endpoint after completion.
- Real Google AI Studio `gemma-4-26b-a4b-it` through `langchain-google-genai`; generation status `complete`, live=true.
- Planner call114 and maker117 succeeded. Maker116 timed out; its failure remains recorded. Successful stages reused cached, typed workflow results.
- Count result: **200**, with matching200/evaluated200/unknown0.
- Effective-status/location result: **200 rows**, matching200/evaluated200/unknown0.
- Output plan: count card bound to `count`, status/location table, map bound to `lat`, `lon`, `asset_id` and `producing`.
-207 evidence entries. First row WELL-0001 preserves raw recorded_status=active and effective producing=false, delta3.2°C, threshold15°C. These are distinct fields, not interchangeable.
- Receipt summary: [fleet-retest-summary.json](fleet-retest-summary.json).
- Browser render verification belongs to the UI worker; successful backend data/envelope alone is not a blanket visual acceptance claim.

## Fixes made after initial QA

- Official ChatGoogleGenerativeAI replaces hand-built HTTP transport; selected model26B, Google only.
- YAML required/optional input binding and valid JSON examples aligned to runtime schemas.
- Shared token admission now accounts for the16,000 input-token/minute quota, not just30RPM; cooldown and foreground scheduling implemented.
- Typed/versioned workflow stage receipts prevent legacy positional checkpoint collisions after code changes.
- Failed maker runs preserve verified data as explicitly partial; successful retries can reuse earlier validated stages.
- Production status and aggregate-count semantic binding checks prevent spill-as-production and one-row-as-one-asset errors.
- UI typography/progress improvements are being browser-verified; consult current screenshots/report under ../04-ui-implementation/.

## Still not proven

The initial18-scenario QA contains semantic and delivery failures. No all18 pass claim is justified. Q1/Q2 explanation completeness, live correction/dependency sequences and provider reliability require targeted post-fix checks. See [QA_REPORT.md](QA_REPORT.md), [QA_REVIEW_ADDENDUM.md](QA_REVIEW_ADDENDUM.md), and [SCORING.md](SCORING.md). Raw unit tests, correct deterministic calculations and a successful fleet answer are separate evidence categories.
