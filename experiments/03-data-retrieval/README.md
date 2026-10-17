# Data and retrieval

- [Dataset integrity audit and keys](../reports/data-audit.md)
- [Measured retrieval experiments](../reports/retrieval-experiments.md)
- [Retrieval/storage design](../reports/retrieval-research.md)

Eligible foundation: complete exact SQL calculations, correction-aware values,
direct report/manual joins, source spans and FTS/BM25. Both original experiments
passed 9 numerical/correction checks and full-area linked-report coverage checks.

Historical MiniLM/RRF improved evidence recall in a matched 24-query test but is
INELIGIBLE because the user requires Gemma as the only model in every layer.
Do not copy the old MiniLM recommendation into the final system. Its documents
remain here as historical evidence, clearly labeled, rather than erased results.

Gemma-only query expansion/extraction can be evaluated later. No alternative
embedding/reranking model is permitted. The latest policy is
[model-policy.md](../reports/model-policy.md).
