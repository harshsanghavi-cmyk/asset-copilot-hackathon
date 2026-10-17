# Isolated gbrain shared-projection probe

This branch includes the identical canonical SQLite policy/fixture suite as the
explicit and LangGraph branches, plus an actual installed gbrain PGLite engine
probe. `export-fixture.py` admits asset/type/team/organization claims through that
canonical policy and exports B's shared context for projection; private preference
and episode records remain outside the index. Later projection-lag/withdrawal
cases use a controlled canonical-view map, not a second production database.

Run the canonical suite (standard Python, no dependencies):

```sh
python3 experiments/memory/canonical-benchmark.py --candidate explicit --output experiments/memory/canonical-results.json
```

Run the actual engine probe using Bun and an explicitly selected installed source
package, matching gbrain 0.42.72.1 and the source hash recorded in results:

```sh
GBRAIN_REFERENCE_ROOT=/path/to/isolated/pinned/gbrain bun experiments/memory/gbrain-probe.ts
```

The reference package must already have its dependencies. This probe imports only
the engine module, constructs PGLite with an explicit temporary database path,
and never resolves the default host brain, mounts, user config or `.env`. HTTP
fetch is prohibited. Temporary databases are removed. No services remain.

Measured: sourced exact entity facts, cross-user shared projections, provenance,
reopen persistence, transaction rollback, stale-projection canonical overlay,
withdrawn-fact filtering, contradictory claim retention, explicit source identity
and the distinction between trusted storage APIs and application authorization.

Not measured: memory `remember` operation, `context_pack`, remote source grants,
semantic/graph retrieval quality, embeddings, model extraction, synthesis, live
model responses or complete H2 end-to-end behavior. The canonical suite's pass
count must not be added to the engine probe and called superior memory quality.
An exact installed package version plus one engine-source hash documents this
local run; a full distribution/commit pin is still required for independent
reproduction. The installed reference package is not vendored or modified here.
