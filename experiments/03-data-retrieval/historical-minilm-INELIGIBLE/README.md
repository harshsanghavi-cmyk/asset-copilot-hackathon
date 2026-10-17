# Isolated retrieval experiment

This branch tests exact SQL + SQLite FTS5 plus real semantic retrieval. It is not
the application. The sibling `experiment/retrieval-fts` branch uses the same
corpus/fixtures/exact tools without dense retrieval. Main analysis and limits are
in the planning workspace's `agent-memory/retrieval-experiments.md`.

Acquire the MIT-licensed dataset repository separately at revision
`b8de8c9bd68f40334e5d06922126169e4f3bf3ca`; its `sample-data` folder is DATASET below.
No raw data, model files, DBs, environment secrets or dependencies are committed.

Python 3.12 was used. The lexical candidate needs standard library only. For the
semantic candidate create an isolated `.venv` and install `requirements.lock`.
MiniLM is downloaded once into ignored `.cache/models` via FastEmbed; real
384-dimensional CPU vectors are cached in ignored files. Exact duplicate text
shares computation, while all distinct source identities/spans remain in ranking.

```sh
python3 benchmark.py --dataset DATASET --mode fts --output results/fts.json
.venv/bin/python benchmark.py --dataset DATASET --mode hybrid --output results/hybrid.json
python3 report_scan.py --dataset DATASET --output results/report-scan.json
python3 compare.py --fts FTS_RESULTS --hybrid HYBRID_RESULTS --output results/comparison.json
```

Fixtures were frozen before initial candidate execution (commit `ede17cb`). Scorer
whitespace normalization repairs source annotation matching without altering
retrieval. Supplemental report-link/unknown tests were frozen in `report-fixtures.json`
before their first run. Rankings use metadata scope, lexical stemming/BM25 and
fixed synonyms; hybrid adds cosine semantic candidates and RRF k=60. No expected
record ID/span/answer enters retrieval. Numeric test requests naturally name
scenario subjects, but expectations are read only by scoring.

`live_synthesis.py` is optional and has a separate authorization boundary. Do not
run it without permission to use the exact configured free Gemma endpoint. It
requires `--allow-live`, refuses an existing attempt ledger, never logs the key,
allows at most twelve attempts and stops on provider failure without retries.
The paired six questions and settings are fixed in source. Missing/failed calls
do not establish answer quality. No rate limit, production safety, full copilot,
cross-encoder, ANN, Postgres or DuckDB performance claim follows from these tests.

Measured outcome: both exact suites pass 9/9; full-scope containment and missing-fact checks pass. Across 24 fixed evidence queries, FTS macro recall@5=0.6667, MiniLM/RRF=0.8333 (four improvements, no regressions at this cutoff). This is a narrow fallback-retrieval result, not live answer-quality validation. The first selected free Gemma request returned HTTP 429; one attempt was recorded, no retry or alternate model. Full limits and raw artifacts are in the planning report.
