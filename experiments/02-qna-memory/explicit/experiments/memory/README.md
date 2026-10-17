# Explicit journal versus LangGraph: fixed-proposal memory experiment

This is a synthetic experiment, not the copilot application. `benchmark.py` is
byte-identical on both candidate branches. The flag changes only the workflow
adapter: explicit per-stage SQLite journal or actual LangGraph StateGraph with
SqliteSaver and synchronous durability. Both use the same application-owned
ledger, user authorization, fixtures, fixed proposals and crash schedule.

Run with Python 3.11+ (no dependencies for explicit):

```sh
python3 experiments/memory/benchmark.py --candidate explicit --output experiments/memory/results.json
```

The LangGraph branch contains the pinned dependency list and corresponding run
command. For matched comparisons use that same Python interpreter for both.
SQLite files live in temporary directories and are removed after each run.

Coverage includes shared asset/type/team/organization claims across users;
private preferences/ordered entity sets across restart; correction authority,
conflicts and explicit supersession; scoped expiring type rules; revision and
idempotency behavior; source/identity validation; independent periodic/overflow
summary triggers; real subprocess termination and resume; simultaneous writers;
and a correction between answer checkpoint and dashboard publication.

Fault points use `os._exit(73)` before commit, after commit, before publication
and after exchange persistence. Recovery runs in a fresh process. `--worker`
and `--resume` are internal fixture commands; they never read the real dataset.

Limitations: all model proposals are fixed; no extraction or natural-language
quality is tested. Summary jobs store coverage receipts, not model-generated
summaries. The overflow trigger is injected, not tokenizer-driven. Five panels
are result fixtures, not browser UI. The tombstone test covers one context path,
not all transcripts/caches or certified physical deletion. This is a small
three-stage sequential workflow, not a production authorization or concurrency
audit. Schema uses synthetic source markers, not a real evidence registry.

Initial findings retained in `development-findings.json`: simultaneous WAL-mode
initialization could contend; the common initializer now retries boundedly.
Default LangGraph durability did not preserve the prior answer snapshot under
the injected process exit; synchronous durability passed. Both models of
workflow still need idempotency because ledger commit and workflow checkpoint
are different transactions.
