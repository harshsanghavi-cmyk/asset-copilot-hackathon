# Long-term memory: compress the projection, retrieve the facts

17 Oct 2026 · focused design clarification, not application implementation. The reader copy at `experiments/02-qna-memory/long-term-memory-loading-decision.md` is identical. **No API calls, new experiments, dependencies or sessions. Memory extraction, compression and answer quality remain untested.**

## Decision

**Keep atomic facts durable. Always load a small scoped capsule/index, then retrieve relevant exact facts inside the same 2K long-term cap.** Refresh that projection on accepted fact changes. Use deterministic rebuilding first; invoke Gemma for compact rewriting only when the projection needs it, particularly on slot overflow. Query-time retrieval happens on each relevant question and does not wait for a rebuild or ten exchanges.

**Do not require gbrain now.** Its 17/17 experiment tested exact sourced-projection mechanics, not compression, lexical recall or semantic retrieval quality. Under Gemma-only/no-embedding-model constraints, a gbrain exact/lexical projection overlaps the SQLite IDs/FTS/canonical records already required. Adoption needs a distinct benefit to justify another synchronization/authorization boundary. This is a **design judgment, not a proven quality winner**.

## Three triggers that must not be confused

| Trigger | Operation | Result |
|---|---|---|
| Accepted remember, correction/rule or useful validated per-message proposal | Commit/version atomic knowledge immediately; refresh exact index and affected capsule manifest | Durable save receipt; no wait until exchange 10 |
| Accepted facts change the capsule, or its projection exceeds its slot | Deterministically rebuild eligible cards/pointers; optionally request Gemma compact rewriting if needed | New bounded projection/version, not changed source truth |
| Each question/reference | Exact IDs/subject/time lookup, then scoped SQLite FTS for additional relevant facts | A different selected fact pack within the same 2K |
| Completed exchange 10/20, or earlier dialogue overflow | Short-term conversation compaction | Summary/navigation plus recent dialogue inside the separate1K |

Useful memory proposals are checked on every message in the existing planner call. Application code validates source, scope and authority before commit. A capsule refresh usually needs no model call. Short-term summarization can recover missed candidates, but it is not the schedule for saving or retrieving long-term facts.

## Stored facts versus loaded projection

Canonical private/shared records retain stable IDs, author, audience/owner, subject/applicability, minimal assertion or exact value/unit, source refs, uncertainty/conflicts, validity/occurrence time, recorded time and supersession/version. Formal corrections/rules remain separate structured authority, preserving original/previous/effective values and reason. Neither a summary nor a newer ordinary claim can overwrite them.

A capsule is only a prompt-facing projection. It contains compact facts/topic groups and a manifest pointer to the originals. The server manifest maps cards to every covered source ID and marks facts as inlined, referenced or omitted from this projection. **Omitted from the prompt does not mean deleted, superseded or nonexistent.** A finite capsule cannot promise all unbounded original facts verbatim.

Capsules are labeled data, not privileged instructions. Read-only persona/routing stays separate; a remembered sentence cannot change tool policy, identity, permissions or authority.

### Exactly what is always loaded

These are proposed internal splits within the user's fixed content caps:

| Long-term slot | Tokens | Loading |
|---|---:|---|
| Active user's private capsule/index | 600 | Always: compact stable preferences/work context, topic groups and manifest/version |
| Shared capsule/index and revision/manifest header | 200 | Always: small authorized organization/routing header; relevant subject pointers can replace generic ones |
| Relevant private atomic facts / entity-event receipt details | 400 | Query-specific exact expansion |
| Relevant shared claims / corrections / conflicts | 800 | Query-specific subject/time expansion, with author/status/validity/source refs |
| **Long-term TOTAL private + shared** | **2,000** | **800 always +1,200 selected**; initial private 1K/shared 1K |

The shared 200-token header cannot name every well; direct subject lookup must still retrieve an applicable plan/correction it omits. Metadata counts within its card slot. Unused long-term subslots may be pooled inside 2K, not borrowed silently from another content category.

```text
Long-term =600 private capsule +200 shared header +400 private facts +800 shared facts =2,000
Short-term =400 rolling summary +500 recent user/assistant dialogue +100 handles =1,000
Fresh context =600 results +650 manual/SOP excerpts +550 report spans +200 coverage =2,000
USER content cap =2,000 +1,000 +2,000 =5,000
```

Shared cards appear once; fresh context can cite their IDs without repeating full text. Raw historical dialogue belongs inside short-term1K even if fetched through read_context; full receipts/archive stay server-side. Fresh SOP/report prose cannot be relabeled shared memory to evade its2K cap. Persona/tool instructions, current request, output and framing are separately measured overhead, not extra memory allowance.

## Rebuild and failed-compaction mechanism

1. **Commit first.** Validate the user-source statement/subject/scope, preserve uncertainty and time precision, then append/version the atomic record. Exact duplicate delivery reuses its receipt. Explicit saves are acknowledged after commit; accepted corrections/rules use their own authority validator. Private/shared revisions and durable projection work are recorded transactionally.
2. **Refresh deterministically.** Mark the affected scope dirty and update its manifest. Insert/replace an eligible compact tuple, remove explicitly superseded/withdrawn active cards and refresh topic/count pointers. If private 600/shared 200 still fit, publish without Gemma. Unrelated users do not need a rebuild.
3. **Compress only when needed.** If cards overflow, first group exact records behind stable topic/manifest pointers. Optional Gemma-only rewriting can shorten selected card wording within the slot. Debounce multiple dirty writes into a job for the latest scope revision; do not launch a model job after every write. Large archives use bounded chunks, never an unbounded prompt.
4. **Validate before publication.** Every card must cite authorized source IDs at the target revision. Preserve numbers, units, negation, uncertainty, author, conflict state and validity exactly where used. “Planned” cannot become “completed”; 5.4 cannot become 4.5. Keep contrary claims distinct. For prose whose safe paraphrase cannot be established, retain an exact attributed excerpt/tuple or reference-only card. JSON validity does not prove semantic fidelity.
5. **Version and recover.** Capsule metadata includes scope/owner, version, source revision, manifest/hash, token count/method and pending revision range. Publish by compare-and-swap; discard/rebase stale jobs. A rewrite failure keeps the prior accepted projection plus a bounded pending-delta pointer, not an ever-growing list of new sentences. Canonical reads immediately fetch current relevant facts and replace optional cards inside 2K. Withdrawal/correction eligibility is rechecked before use, so stale cards cannot resurrect truth.

A failed rebuild never deletes accepted facts or blocks their direct retrieval. If indispensable current/pending facts and conflicts cannot fit, clarify or return a supported partial answer. Never enlarge the cap silently, assert complete recall or switch to another model/encoder. All optional Gemma work shares 30 RPM and bounded retries.

## Retrieval on each question

Use the existing `read_context` capability; the other three remain `query_records`, `read_evidence`, `write_knowledge`.

- Authorize **this user's private records plus allowed shared organization facts before lookup**. Shared asset applicability is not an author's team-only ACL.
- Resolve known IDs/aliases and the user's exact entity/event receipts first. “The three wells yesterday” never searches another user's conversation; ambiguous/absent references stay explicit.
- Fetch applicable subject/type/equipment/team/org claims by time, current lifecycle and conflicts. Query tools separately apply all accepted corrections/rules over effective data, independent of prompt rank.
- Use scoped, escaped SQLite FTS terms/aliases for additional admitted-fact discovery; return actual source IDs and revalidate current eligibility. This is lexical retrieval, not vector semantics. [SQLite FTS5](https://www.sqlite.org/fts5.html)
- Assemble the always 800 + selected1,200 long-term pack with omitted-category/expansion handles. Follow-up memory fetches **replace** optional loaded facts inside 2K, not append another2K. Fresh record/report/SOP evidence remains inside its separate2K.

Example: A/Jake saves WELL-0007's workover planned from 17 Oct for about ten days. The atomic shared claim commits immediately even if its capsule rewrite is pending. B/Michael's exact well lookup selects it with Jake's attribution/approximate occurrence dates inside shared 800, regardless of the shared index omitting that well. A's private preferences/three-well set never enter B's pack. The plan is not measured downtime or proof of completion.

Targeted questions can often fit concise facts and citations; this is not a tested universal sufficiency result. Fleet-wide “all plans” requires complete canonical enumeration/coverage, not top-k search. If indispensable support still exceeds the cap, narrow the question or report a supported partial result.

## Why research gbrain if we are not adopting it?

We investigated whether a real sourced shared-knowledge interface could improve this project. Research is comparison evidence, not an adoption commitment. Useful patterns included source-qualified identity, attribution/validity, separation of shared knowledge from private continuity, and a projection distinct from authority. Policies/interfaces still require application-specific adaptation.

| Design | Benefit | Limitation / current decision |
|---|---|---|
| All facts in one fixed summary | Always-present text for a tiny archive | Unbounded exact facts cannot fit2K; repeated rewriting risks lost IDs/negation/time/conflicts. Do not use as sole memory; retain originals/manifests |
| Scoped capsule/index + exact facts from SQLite IDs/FTS | Bounded familiarity plus precise current facts, authority and scope | Lexical/reference/projection quality remains untested. **Recommended design judgment**, using required canonical records |
| Same authority + gbrain exact/lexical projection | Potential reusable sourced pages/facts interface | Another projection/index, revision mapping, lag repair and access boundary; useful recall/compression gain is unmeasured. Keep optional |

The installed gbrain 0.42.72.1 probe used a fresh explicit PGLite database. Its 17 checks exercised sourced exact fact/page reads/writes, controlled canonical-delta/withdrawal filtering, wrapper scope refusal, rollback and reopening. The separate 53-check canonical workflow suite is not additional semantic-accuracy evidence. See `agent-memory/memory-experiments.md`.

**Not tested:** lexical recall on held-out questions, vector/semantic search, compression, remember/context_pack operations, autonomous extraction, live Gemma memory quality or remote grant enforcement. No embedding/other runtime model was called. The documented source model is useful evidence, but source organization does not itself provide our per-user authorization. [gbrain brains/sources](https://github.com/garrytan/gbrain/blob/master/docs/architecture/brains-and-sources.md), [fact/context operations](https://github.com/garrytan/gbrain/blob/master/src/core/ops/facts.ts)

Under the current constraints, the tested gbrain projection adds another interface/storage representation, not a demonstrated new answer/compression capability beyond SQLite's required canonical records and exact/lexical index. A future shared knowledge publication service used by several applications, or matched evidence of better eligible recall/maintenance behavior, could justify it. Neither requirement/result is established. This is **not “gbrain failed” or “custom won”**; adoption has not yet earned its extra consistency/access boundary.

Memory tiers and retrieval are supported research patterns, not proof of this implementation's quality: [MemGPT](https://arxiv.org/html/2310.08560v2), [LongMemEval](https://arxiv.org/html/2410.10813v2), [GateMem](https://arxiv.org/html/2606.18829v1). They do not establish our 2K split, compression fidelity or cross-user security.

**Still to test:** full capsules during new writes; duplicate/superseding/conflicting facts; numeric/negation/validity preservation; failed/stale rebuilds; bounded deltas/manifests; A→B recall before rebuild; private negative cases; exact cap boundaries and supported abstention. Compare fixed-summary versus selective exact retrieval on the same sources/budget. No broad research or model evaluation was performed for this note; memory quality remains untested.
