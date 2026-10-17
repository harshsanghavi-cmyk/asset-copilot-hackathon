# PNG brief: compress the projection, retrieve the facts

Coordinator produces and owns the final PNG in flat `diagrams/`. This file is a
source brief only. Title: **“Long-term memory: stored once, loaded selectively”**.
Use operational arrows and explicit token caps, not framework logos.

Main recommendation, prominently: **Always-loaded compact capsule/index +
query-specific exact-fact retrieval. Atomic facts remain canonical.** Label the
design **PROPOSED — memory quality not yet tested**.

Show two separate flows converging into a bounded model pack:

**WRITE / PROJECTION FLOW**
User assertion or remember → Gemma proposes → deterministic scope/source/authority
validation → append/version canonical atomic fact in application-owned SQLite.
Branch into private user facts and shared asset/type/equipment/team/org claims;
correction/rule authority is a separate amber ledger. Accepted fact writes refresh
the exact index and capsule manifest; exact duplicates are idempotent. If the
capsule fits, rebuild deterministically. If its projection overflows, enqueue
optional **Gemma-only** compact rewriting with source IDs and field validation.
New capsule publication requires matching source revision and coverage manifest.
On failure/stale job: keep prior accepted version, show a bounded pending-delta
pointer, retrieve latest atomic facts directly. **No source deletion, no truth
rewrite, no ten-exchange wait for long-term saves.**

**READ / LOADING FLOW**
Trusted user/dataset/time → authorize private user + shared organization → always
load bounded capsules/index → resolve exact entity/event references → exact
subject/validity/authority lookup → SQLite FTS for additional relevant claims →
select exact records with authors/conflicts/dates → replace optional facts inside
the same long-term cap. Full manifests and raw facts remain server-side. Index
absence or top-k rank cannot suppress a relevant correction/shared plan.

**USER TOKEN STRIP: 5K CONTENT TOTAL**
Long-term **2K TOTAL private + shared**, proposed split:
- private capsule/index600, always loaded for the active user;
- shared compact index/version/manifest200, always loaded;
- relevant private exact facts/receipt details400;
- relevant shared exact claims/corrections/conflicts800.
Thus **800 always + 1,200 selected = 2,000 long-term**. Do not show an extra 2K
retrieval allowance for memories. The existing **1K short-term dialogue/summary**
and **2K fresh source/results context** remain separate: **2K + 1K + 2K = 5K**.
Shared cards appear once. Persona/tool instructions, current request and output
are separately counted overhead. Fetches replace content within caps; if essential
facts cannot fit, clarify or return supported partial results without expansion.

**TIMING CALLOUT**
Long-term projection refresh: accepted fact writes / projection overflow.
Query-specific memory retrieval: each relevant question, independent of refresh.
Short-term summary: completed exchange10/20 plus earlier dialogue overflow.
These are three different triggers. Durable raw archives/receipts are preserved.

**gbrain EVIDENCE BOX**
Draw gbrain outside the selected solid path as a dashed optional sourced
projection: **“17/17 exact engine checks; not adopted; no semantic/compression
benchmark.”** A Gemma-only exact/lexical projection could be built, but it currently
duplicates the selected SQLite index and adds synchronization/authorization seams.
No vector/embedding model or proven quality improvement may appear. Research was
comparison evidence, not an adoption commitment.

Small cross-user example: A/Jake's WELL-0007 planned work is a shared atomic claim;
B/Michael retrieves it with author and approximate dates. A's private three-well
discussion set has a blocked arrow to B. A 10-day plan is not a measured outage.
Use high-contrast private violet/shared green/authority amber, large labels, and
generous whitespace. Never imply all unbounded facts fit in an always-loaded
summary, that compression deletes originals, or that this is a deployed copilot.
