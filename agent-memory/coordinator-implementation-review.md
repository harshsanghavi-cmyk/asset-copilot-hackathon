# Coordinator implementation review

Code inspected 17 Oct 2026; findings sent to owners. These are open review items until owner evidence confirms fixes.

| ID | Owner | Finding | Required verification |
|---|---|---|---|
| B1 | Q&A | Evidence-only SOP search bypasses maker when no structured result exists | Supported cited prose answer without mandatory chart |
| B2 | Q&A | Fixed follow-up phrase regex and latest-only receipt selection ignore ambiguity/date | Unique, ambiguous, absent, same-user cross-session and yesterday cases |
| B3 | Q&A | Narrative grounding lacks structured claim/value checks | Invalid citation/value rejected or explicit limitation |
| B4 | Q&A | Rule conflict target can collapse to None; type/equipment predicates omitted | Independent type/equipment overrides do not conflict |
| B5 | Q&A/retrieval | UTF8 byte ceilings are not Gemma token ceilings; decisive excerpts may be omitted | Honest units, cached exact accounting where supported, missing-evidence behavior |
| R1 | Retrieval | Evidence handle lookup scans entire records table per reference | Indexed bounded lookup and repeated-citation check |
| R2 | Retrieval | Unknown counts taken only from paginated output | Unknown outside first page still marks full result coverage |
| R3 | Retrieval | Aggregates need resolvable member lineage beyond rule citations | Fleet/area/month numeric provenance and handle expiry/restart behavior |
| U1 | UI | In-memory runner map unbounded | Idle bounded eviction, active stream preservation, reconnect and owner isolation |
| U2 | UI | Coordinate scatter not geographic-map acceptance | Leaflet/OSM map, attribution, real coordinates and load/error behavior; owner reports implemented |

Current active ownership: Q&A ctx_5fd4f29f0867; retrieval ctx_4ae920d80c36; UI ctx_84fbbad785d2. Do not edit another worker files. Confirm fixes against tests and final code; do not mark fixed from acknowledgement alone.
