# Isolated retrieval comparison — experiment record

Status: **completed bounded comparison**, 17 Oct 2026. User authorization and boundaries are in `experiment-policy.md`; worktrees/branches are in `experiment-branches.json`. No main-app implementation. Evidence retrieval and exact/report paths were measured; live synthesis was blocked by the first HTTP 429 and no answer-quality claim follows.

## Decision

Prefer **the compatible combination of SQLite complete facts/effective authority + direct report/rule links + FTS5/MiniLM hybrid fallback**, retaining the same shared/private knowledge contracts and the UI/workflow selected by their own experiments. Hybrid wins narrowly on these fixed prose-retrieval fixtures: recall@5 improves by **16.7 percentage points**, with four improving questions, zero regressions at that cutoff and twenty ties. Exact calculation and complete report enumeration tie because both deliberately use the same tested deterministic path. This does not establish a universal embedding winner or superior generated answers; the only live request was rate-limited.

FTS-only remains a viable degraded/low-dependency path with explicit evidence limits. The measured extra indexing time is acceptable for a one-time sample import proposal, while the incremental query overhead is small relative to an unmeasured hosted model call. That delivery judgment follows the observed quality/resource tradeoff, not a claim that the simpler candidate is inherently better. Postgres, pgvector ANN, DuckDB and a cross-encoder remain documented but untested alternatives.

## Frozen design

Same original source revision `b8de8c9bd68f40334e5d06922126169e4f3bf3ca`, all 1,509 linked reports, five fleet manuals/SOPs and all 141 context notes. Identical 100-word source-section chunks preserve exact original UTF-8 byte spans; notes preserve JSONL line/note IDs. Corpus: 15,451 chunks (15,259 report, 51 fleet, 141 note) from 1,631 source files. Complete structured facts are loaded independently for exact SQL calculations in both candidates.

- **FTS candidate:** SQLite FTS5, Porter stemming, OR BM25 query over non-stopwords, heading weight 2/body 1, fixed domain synonym expansion, explicit fleet/report/note and asset filters.
- **Hybrid candidate:** the identical exact SQL and FTS pipeline plus **real learned** `sentence-transformers/all-MiniLM-L6-v2` CPU embeddings through FastEmbed/ONNX Runtime, exact cosine/dot-product scan inside identical metadata filters, reciprocal-rank fusion (k=60) of 40 lexical + 40 dense candidates. No ANN, network vector DB or cross-encoder is being tested. This is not token overlap mislabeled as embeddings.

`fixtures.json` was committed **before first execution** in both branches, with the same fixture bytes/source code in commit `ede17cb`. It contains 24 paraphrased evidence questions and independent expected report/rule/note references, plus nine independently expected aggregate/correction checks from scenario requirements. Expected evidence is used only in the scoring phase, never passed to either retriever. Top-k 3/5/8, candidate pool, fusion constant, chunk size and repeats were frozen before results. Report queries filter by named asset, but not by the expected report file; fleet questions search all fleet documents. This compares document fallback, separately from direct-link retrieval.

First execution hit a shared SQL insert-placeholder typo before results; fixed identically. Initial FTS scoring revealed one unresolved qrel because a phrase spans a newline; scorer now normalizes whitespace **only for relevance annotation matching**, identically in both branches, without changing query/ranking parameters or expected wording. The initial uncorrected FTS result is retained alongside final raw results. This is an annotation/scoring repair, not a tuned retriever improvement.

## Metrics and interpretation

Evidence-group recall@k measures the fraction of required source groups with at least one matching expected source/span in top k; complete@k requires every group. Two questions require two sources (T350 inheritance plus T200 rule, and both conflicting WELL-0101 notes). MRR measures first relevant chunk within the returned candidate list. These are hand-authored relevance judgments on a small set, not a blind held-out retrieval benchmark. Nearby equally useful unannotated evidence may be penalized; review failures qualitatively.

Exact SQL correctness uses all matching raw/effective records, independent of top-k: WELL-0001 corrected spill count/volume and 2025 downtime, full-area top downtime and 2026 spill counts, area status before/after a typed thermal correction, volume-class change, pump-jack RCA before/after a T350-only override. One extra cost is recorded without an expected value and is not scored. Both candidates preserve source records; simulated changes affect only in-memory fixture overlay. This narrow overlay is not a production ledger/concurrency implementation.

The corrected-scoring FTS run passes **9/9** expected numerical/correction checks; recall@5 is **0.6667**, recall@8 **0.7708** and complete@8 **0.75**. All expected evidence annotations resolve to source chunks after whitespace correction. Paired final evidence/latency/resource results will follow when the semantic run completes. Full citation correctness, narrative support and unknown handling require separate inspection; a valid source ID does not prove the claim.

Supplemental direct-link/full-scope checks were frozen in `report-fixtures.json` before execution and run identically in both branches (`report_scan.py`). They enumerate all **10** effective real spill inspections in Southwest Block 24 within the explicit `[2026-07-18, 2026-10-17)` window, follow their actual maintenance report links and extract containment spans. Both match the independently expected two breach records (WELL-0082 / INS-0082-0198 / 7.1 h; WELL-0100 / INS-0100-0196 / 8.1 h). With one event's extracted facts omitted in memory, both report matching=10/evaluated=9/unknown=1 and `partial`; no source file is modified. All five direct report-link checks pass, including both custom WELL-0001 filenames. This full-scope path does not depend on top-k prose results.

Orca crashed before the first semantic index completed; no hybrid result or live-call attempt file had been written. The recovered run retains the frozen corpus/parameters and now caches embeddings by identical model/input hash with durable batches. There are **6,933 distinct embedding inputs** across the unchanged 15,451 source chunks; vectors are expanded back to every original source identity before ranking/scoring. The optimization changes repeated computation and recovery cost, not source population or relevance rules. Interrupted indexing time is excluded from the completed-run index measurement and explicitly remains additional wasted work.

## Optional live selected-model check

The coordinator authorized this worker alone to use only the existing `OPENROUTER_API_KEY`, privately, for at most 12 selected free Gemma requests total. The process environment had no key; the expressly authorized root configuration contains one. No key value or other configuration is logged. `live_synthesis.py` takes top-five passages from the frozen paired rankings for six matched questions, with the same system prompt/model/settings, and stops on provider/network failure without retries or paid fallback. It stores attempts before transmission to prevent accidental duplicate batches.

**Actual outcome:** exactly **one** request to `google/gemma-4-31b-it:free`, for r01/FTS, returned **HTTP 429 after 0.890 seconds**. The guard stopped the batch; eleven allowed attempts were unused. There is no successful completion, generated answer, token/usage receipt, measured billable charge or authenticated JSON/tool compatibility conclusion. The error is not scored as a factual-accuracy failure. Raw attempt accounting is `retrieval-hybrid/results/gemma.json`; no retry, formatting-repair call or provider/model substitution occurred. Root configuration was read only for the expressly authorized key and remained untouched.

## Final paired measurements

| Metric | Exact SQL + FTS5 | Same + MiniLM/RRF |
|---|---:|---:|
| Exact numerical/correction fixtures | 9/9 | 9/9 |
| Full-scope containment expected records | Both / complete coverage of 10 spills | Both / complete coverage of 10 spills |
| Direct report links | 5/5 | 5/5 |
| Missing-fact injection | 1 unknown, partial | 1 unknown, partial |
| Evidence-group macro recall@3 | 0.6667 | 0.7292 |
| Evidence-group macro recall@5 | 0.6667 | 0.8333 |
| Evidence-group macro recall@8 | 0.7708 | 0.9167 |
| Complete required groups @5 | 16/24 | 20/24 |
| Complete required groups @8 | 18/24 | 22/24 |
| MRR within candidate ranking | 0.5137 | 0.5955 |
| Query p50 / p95, cold-run process | 5.42 / 10.53 ms | 18.46 / 26.01 ms |
| Peak RSS, same process run | 560,156 KiB | 638,452 KiB |
| Structured load / exact suite | 3.72 s / 0.169 s | 3.20 s / 0.161 s |
| FTS build | 0.159 s | 0.112 s |
| Additional cold semantic index | — | 266.08 s |
| Full benchmark wall time | 6.37 s | 273.31 s |

Report-scan-only time was 9.49 ms / 11.10 ms, excluding structured load. Index timings exclude initial dependency/model download and the discarded pre-crash run. They include exact duplicate-input reuse within the successful semantic build. Local machine had other supervised work: timings are descriptive samples, not controlled hardware performance comparisons. Each of the 24 questions runs three timing repeats; those repeats are not independent quality examples.

The semantic cache reload run reproduced **identical top-eight rankings, quality metrics and 9/9 exact results**, with vector loading 5.4 ms, total benchmark 6.28 s, p50/p95 query 10.50/15.70 ms and peak RSS 583,736 KiB. It demonstrates completed index reuse after process restart, not a post-fix mid-batch crash recovery test. Learned vectors use **384 dimensions**, total **23,732,736 bytes** for all chunk identities; dependency versions were FastEmbed 0.7.4, ONNX Runtime 1.31.0 and NumPy 2.5.4. The downloaded tokenizer caps at 256 wordpieces; independent tokenization found a maximum of **187** for these inputs, so no corpus chunk was truncated. Model/config file hashes are saved in raw semantic results; downloads are not a permanently pinned remote artifact unless future reproduction verifies those hashes.

At top five, fleet-rule macro recall was 11/13 versus 13/13; report-only recall 4/10 versus 6/10; the single conflicting-note question was complete in both. Improvements were r04 (agency verification state), r08 (September containment), m03 (T350 inheritance plus T200 escalation) and m04 (written-report deadline). The corpus, fixture and protocol hashes match, and the comparison script checks exact results are identical before scoring differences.

## Failure analysis and limits

Both fallback candidates still miss the July prime-mover root-cause paragraph (r05) and the decisive September WELL-0100 containment span (r07) within eight results. Many similar repair narratives and headers/dates separated from fact chunks compete; exact numeric expectations can be absent even when a top hit names the right report. Neither candidate is permitted to fill a missed value from model memory. Direct joins plus the separately tested full-report extraction path resolve these known linked questions and remain mandatory for complete compliance answers.

Future improvements should be tested on new held-out queries: carry parent report/equipment/date context into each chunk, use timestamp/inspection filters when unambiguously resolved, expand adjacent sections after a hit and consider a genuine cross-encoder if these gaps persist. Those improvements were **not tuned into this frozen result**. The present test does not prove missing evidence can be detected from similarity alone; unknown handling was tested through the deterministic full-scope scan.

The 24 questions are small and hand-authored by this research track; thirteen search the same five fleet documents and one tests shared-note conflict evidence. They are paraphrased evaluation fixtures, not blind unseen production requests. Source-group qrels allow stated alternatives but are not exhaustive independent annotations of every useful chunk. No separate held-out dataset root was supplied, no ingestion conflict/generalization benchmark was run, and there is no end-to-end Q1–Q18, privacy, concurrency, UI, arbitrary-model extraction or live answer-quality pass claim. The in-memory correction table supports only the specific fixture overlay and is not an implementation of the full proposed audit/temporal ledger.

## Reproduction and durable evidence

Worktrees:

- `/home/harshsanghavi/orca/projects/asset-copilot-experiments/retrieval-fts` on `experiment/retrieval-fts`.
- `/home/harshsanghavi/orca/projects/asset-copilot-experiments/retrieval-hybrid` on `experiment/retrieval-hybrid`.

Each owns `benchmark.py`, frozen `fixtures.json`, supplemental `report_scan.py` / `report-fixtures.json`, `compare.py`, README and raw `results/`. Hybrid additionally owns pinned `requirements.lock`, guarded `live_synthesis.py`, full/warm semantic results, comparison and live error receipt. FTS retains its original whitespace-scoring result as an audit artifact. Dependency/model caches and DBs remain ignored, outside commits; raw source data is acquired separately at the pinned MIT-licensed revision. README contains exact commands; all report/spill results use the original dataset unchanged.

Initial freeze commit: `ede17cb` in both branches. Pre-report-scan commits: FTS `3922044`, hybrid `4273e10`. Final artifact commits: **FTS `5088e7b`**, **hybrid `4288e54`**. Only owned benchmark sources, pinned dependency/reproduction information and bounded result artifacts were committed; no branch was merged or published. Worktree `AGENTS.md` files remain untracked instructions, and generated caches/DBs/dependencies remain ignored.

Final checks: saved paired result comparator passed corpus/fixture/config equality and identical exact-check assertions; warm-run top-eight rankings match cold-run rankings exactly; every qrel resolves to a real source chunk; original UTF-8 span assertions ran during corpus construction and containment extraction; all new experiment Python sources compile. `skills/data-retrieval/SKILL.md` passed the skill-creator validator. No services were started. These checks do not broaden the measured test boundary described above.

## Sources informing design

[BEIR](https://arxiv.org/abs/2104.08663) supports retaining a strong lexical comparison; [MTEB](https://arxiv.org/abs/2210.07316) motivates measuring a specific embedding on the intended task. [RRF](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) defines reciprocal rank fusion; [RAG](https://arxiv.org/abs/2005.11401) motivates retrieved context without establishing numerical completeness. The [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) documents learned 384-dimensional semantic vectors and paragraph-length limits; [FastEmbed](https://github.com/qdrant/fastembed) supplies the actual CPU runtime used here. Vendor/paper benchmark numbers are not reported as local outcomes.
