# Memory/workflow experiments: measured results

17 Oct 2026. Authorized isolated experiment branches only; main application, raw
dataset and private/configured gbrain memories untouched. **Zero model calls,
zero embedding calls, no API keys or `.env` reads, no services started.** This is
state/integration evidence, not a copilot answer-quality evaluation.

Final steering permits report/diagram finalization while the coordinator alone
verifies newly supplied direct Google AI Studio access. Gemma 4 31B is the only
eligible model in every copilot layer (original OpenRouter identifier:
`google/gemma-4-31b-it:free`); other LLMs/embedding models/rerankers, including SDK
defaults, are excluded. The completed experiments used no inference/embedding
models and remain valid. This worker made no API requests or key reads.

## Result and recommendation impact

**State-behavior tie:** the application-owned explicit journal and an actual
LangGraph StateGraph with SqliteSaver each pass the same **53/53 synthetic
fixed-proposal checks**. Shared asset/type/team/organization facts reach B;
private preferences and discussion entity sets remain user-scoped; formal
corrections, conflicts, validity and replay behavior match. LangGraph did not
demonstrate superior factual accuracy or recovery outcomes in this small
three-stage sequential workload. It remains a credible choice for richer
resumable workflow composition, not a winner established by this suite.

**gbrain is a credible shared projection adjunct:** actual installed gbrain
PGLite APIs pass **17/17 bounded integration checks** with fresh explicit storage.
The gbrain branch also passes the same 53-check canonical policy suite separately.
The 17 checks are not an end-to-end H2 benchmark and cannot be added to 53 and
interpreted as better memory quality. No semantic retrieval, model extraction,
`remember` operation, `context_pack` or remote grant policy was evaluated.

The strongest supported recommendation is independent of framework choice:
**own effective-record authority and audience policy in the application, keep
private continuity separate, store minimal shared operational claims once, and
join them for every relevant authorized user.** Never rely on a user profile,
summary, semantic top-k or stale projection to propagate corrections. The full
hybrid recommendation and paper evidence are in [architecture-review.md](architecture-review.md).

## Artifacts, versions and reproduction

| Candidate | Branch / committed experiment | Raw result | Final local elapsed |
|---|---|---|---:|
| Explicit journal | `experiment/memory-explicit`, commit `1c72ac1` | [results.json](/home/harshsanghavi/orca/projects/asset-copilot-experiments/memory-explicit/experiments/memory/results.json) | 1.381116 s |
| Actual LangGraph | `experiment/memory-langgraph`, commit `d93f8f9` | [results.json](/home/harshsanghavi/orca/projects/asset-copilot-experiments/memory-langgraph/experiments/memory/results.json) | 9.955061 s |
| gbrain canonical control | `experiment/memory-gbrain`, commit `245b8a3` | [canonical-results.json](/home/harshsanghavi/orca/projects/asset-copilot-experiments/memory-gbrain/experiments/memory/canonical-results.json) | 1.411433 s |
| Actual gbrain projection | Same gbrain branch/commit | [results.json](/home/harshsanghavi/orca/projects/asset-copilot-experiments/memory-gbrain/experiments/memory/results.json) | 4.499207 s |

Elapsed figures are single final harness runs, including fresh subprocesses,
imports, temp-store setup and fault injection. gbrain's time includes fresh
schema migration/reopen work. They are **not production request latency, a p95,
or an equal-workload speed contest**; the projection probe and canonical suite
do different work. The two workflow candidates use the same Python 3.11.15 and
SQLite 3.53.1 interpreter environment. Final runs were scheduled alongside each
other, so wall time also includes local scheduling contention.

Actual framework pins: `langgraph==1.2.16`, `langgraph-checkpoint==4.3.0`,
`langgraph-checkpoint-sqlite==3.1.2`. An isolated `.venv` exists only in the
LangGraph worktree; [requirements.lock.txt](/home/harshsanghavi/orca/projects/asset-copilot-experiments/memory-langgraph/experiments/memory/requirements.lock.txt)
records all 41 installed distributions. Packages/databases/virtual environments
are not committed. LangSmith/LangChain tracing is explicitly disabled by the
benchmark before importing LangGraph. No model is constructed.

All three canonical benchmark copies have SHA-256:

```text
1b6ab7e8bee71bef201df581b55f0422029ff6f0567d6e9c3fd9cd3cfe7e8c03
```

The installed gbrain reference is version `0.42.72.1`; the probe records Bun's
actual version and engine-source SHA-256
`698089f30fc62fbaaf023c8216f4bdbef256d81477d7b71dad786759f79252a0`.
It imports the selected package's engine module directly, with an explicit
temporary `database_path`. No CLI/default brain/config/mount resolution occurs.
The installed package was not modified or vendored. A version plus one source
hash documents this local observation; independent complete-package reproduction
still requires a pinned distribution/commit and its dependencies.

From the LangGraph worktree, recreate the isolated interpreter and run:

```sh
uv venv --python 3.11 .venv
uv pip sync --python .venv/bin/python experiments/memory/requirements.lock.txt
.venv/bin/python experiments/memory/benchmark.py --candidate langgraph --output experiments/memory/results.json
```

Run the explicit branch with the same interpreter for a matched comparison:

```sh
/home/harshsanghavi/orca/projects/asset-copilot-experiments/memory-langgraph/.venv/bin/python experiments/memory/benchmark.py --candidate explicit --output experiments/memory/results.json
```

From the gbrain worktree, run the canonical suite and the actual engine probe:

```sh
python3 experiments/memory/canonical-benchmark.py --candidate explicit --output experiments/memory/canonical-results.json
GBRAIN_REFERENCE_ROOT=/path/to/pinned/gbrain bun experiments/memory/gbrain-probe.ts
```

Each branch contains a README explaining exact boundaries. This worker committed
only owned source/docs/pin/results files on experiment branches. Root research
artifacts remain uncommitted for coordinator synthesis. Branches share a base
and have the same filenames, so they are reviewable alternative implementations,
not three branches to blindly merge together.

## What the 53 identical checks actually exercise

Both candidates call the same canonical ledger and stage functions. The flag
changes only the workflow adapter: an explicit per-stage SQLite run journal or
actual LangGraph `StateGraph` compiled with `SqliteSaver`. The graph has commit,
answer and persist nodes, a recursion cap and `durability="sync"`. Runtime run
ownership is checked by application code before any checkpoint is read/resumed.

| Family | Directly checked behavior |
|---|---|
| Shared/private scope | A's asset/team/type/org claim appears in B's shared context; future planned work remains known before occurrence; A's private preference and ordered three-entity episode never enter B's context; private episode survives reopening |
| Formal authority | Correction changes B's effective temperature; raw original remains; ordinary contrary note cannot undo it; competing formal correction remains disputed; explicit supersession applies while all correction records remain |
| Type and time | T350-only rule changes its count threshold; T200 stays at the original threshold; a new synthetic T350 member inherits the rule; validity end is exclusive |
| Write policy | Duplicate request returns one receipt/revision; changed intent under the same idempotency key fails; supplied identity, unsupported source marker and shared private-episode admission fail |
| Continuity | Different dataset namespace starts empty; private-fact tombstone hides the fact from the context path while the raw row remains; periodic count triggers at 10/20 cover 1–7/1–17; an injected overflow job at exchange 4 does not reset periodic count; duplicate exchange 10 does not double-count |
| Ownership | Other principal cannot write the thread or resume a known checkpoint/run; authorization occurs before framework access |
| Recovery | Actual fresh subprocesses terminate with exit 73 before ledger commit, after commit and after exchange persistence; new processes resume; one domain change and one exchange remain |
| Dashboard revision | Process stops before persist after answer is checkpointed at R1; B commits correction R2; resume preserves all five old R1 result fixtures and labels the whole answer historical; a later effective read uses R2 |
| Concurrency | Two independent OS processes write distinct requests with no lost revision; two simultaneous formal corrections leave one accepted and one disputed, not last-write-wins |

The effective query uses a short SQLite read transaction to pin values and
revision together. Writes use `BEGIN IMMEDIATE`. Ledger writes and workflow
checkpoints are deliberately separate transactions, exercising the gap a package
does not magically close. Idempotent receipts and unique exchange IDs prevent
replaying that gap from duplicating side effects.

## Failures encountered and fixes

The committed [development-findings.json](/home/harshsanghavi/orca/projects/asset-copilot-experiments/memory-explicit/experiments/memory/development-findings.json)
retains observations from initial runs rather than pretending every run passed.

1. Two independently initializing SQLite processes hit `database is locked` at
   `PRAGMA journal_mode=WAL`. The shared initializer now retries that lock
   condition up to 20 times at 10 ms. This same change applies to both candidates.
   Production should initialize schema/journal configuration before serving
   competing API workers, with bounded transaction retry policies.
2. LangGraph's default durability did not meet the fixture's strict requirement
   to preserve the prior answer snapshot across forced process exit before the
   next node's checkpoint. Selecting synchronous durability preserved the
   predecessor state and the final R1/historical result. The original assertion
   was stricter than accepting a wholly recomputed consistent R2 answer, so this
   failure is **not evidence of mixed revisions or leaked private information**.
3. Both designs require a write receipt even with durable workflow state:
   termination after commit but before stage/checkpoint save can replay commit.
   All final duplicate/recovery fixtures pass through the same idempotency key.

These fixes followed actual failures. Final checks were rerun after snapshot
transaction/tracing changes; no repeated model/provider attempts occurred.

## What the 17 gbrain checks establish

`export-fixture.py` admits the common fixed shared and private records through
the actual canonical Ledger class. The gbrain probe receives B's shared claims,
projects only those to `world` facts in an explicit synthetic shared source, and
keeps user preference/episode data outside the index. Controlled projection-lag,
withdrawal and contradictory-claim cases then use an in-memory canonical view
to isolate adapter behavior; they do not constitute a persistent second-system
integration or outbox implementation.

Actual `PGLiteEngine.insertFact`, `listFactsByEntity`, `listFactsSince`,
`putPage/getPage`, `transaction` and disconnect/reconnect calls were exercised.
The probe checks the four subject kinds, absence of the private canary from
projected facts, source/revision attribution, duplicate-projection receipt reuse,
canonical delta recovery when the index is deliberately stale, withdrawn-claim
filtering, opposing claims retained, source-qualified page identity, rollback and
reopen persistence. HTTP fetch is prohibited; no extractor/embedder/synthesis
path is invoked. All generated databases were temporary and removed.

A deliberate boundary probe places a harmless synthetic canary in another
source. The trusted engine API can read it when explicitly given that source,
because it has no application requester identity. The application wrapper
rejects an out-of-grant request before invoking the engine. This is a storage/API
boundary demonstration, **not a claim of a gbrain remote ACL vulnerability**.
Remote operations and source grants are separate interfaces, not tested here.

The useful measured conclusion is that sourced shared facts can be stored/read
and reopened in the real installed engine, while current eligibility and
read-after-write consistency still come from the canonical gateway. Rich
semantic benefit remains an open question. A raw index without the canonical
delta overlay demonstrably lacked the newly saved plan in the lag fixture.

## Important limits and next decision

These fixtures use synthetic `W-A`/`W-B` entities and fixed typed proposals. They
do not run Q1–Q18 against the real dataset, ingest new same-format directories,
extract real report spans, verify LLM intent/antecedent resolution, measure
semantic retrieval, generate summaries or count real prompt tokens. Synthetic
source-prefix checks are not an evidence registry. Overflow is an injected
signal; summary checks establish scheduling/coverage receipts only. Five panels
are immutable data fixtures, not React/browser or AG-UI tests.

Private forgetting covers this context projection, not every raw transcript,
embedding, checkpoint, summary, cached answer and source-viewer path. Publication
is a controlled process interruption test, not a full distributed delivery audit.
Concurrency is a small two-process test; it cannot certify production safety.
No claim is made that 53 checks represent 53 independent scenarios or that one
successful run establishes statistical reliability.

Do not use the pre-experiment weighted matrix as a measured scoreboard. Select
relational authority + scoped shared knowledge with confidence from these
mechanics; retain **explicit journal versus LangGraph as a measured tie** for the
current small workflow. A follow-up fan-out/interrupt/restore benchmark can test
whether LangGraph's built-in workflow capabilities earn integration cost.
Similarly, gbrain has earned a semantic-retrieval trial, not automatic adoption.
Use the same held-out organizational paraphrase/relationship corpus and evidence
budget for H1/H2, preserving the zero-critical-leak/correction gates. That broader
trial requires a demonstrated Gemma-only or deterministic configuration and is
outside the no-model-call boundary of this dispatched track. Introducing a
separate embedding model or reranker is not permitted by the current steering.
