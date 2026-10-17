# Primary-paper evidence and transfer to this project

Read on 17 Oct 2026. Papers inform design and test cases; their benchmark scores
are not results for this dataset or the selected Gemma endpoint.

## GateMem — supplied context-engineering reference

[Full paper](https://arxiv.org/html/2606.18829v1), especially sections 3–4 and
Appendix E. It evaluates useful authorized answers, cross-principal access and
post-deletion recovery together. Its case studies show that retrieval can find a
fact yet disclose it to the wrong requester, and that a policy-heavy system can
also wrongly refuse a legitimate request. Agent-facing forgetting is not a proof
of physical deletion. The benchmark uses synthesized institutional scenarios and
judge-based scoring with a human validation subset, so its numbers do not establish
our application's performance.

Project implication: test both shared operational recall and private-history
non-disclosure. Do not solve privacy by refusing all cross-user facts. Enforce
visibility before model context; check summaries/caches as well as primary stores.
Clear shared well notes should be immediately useful to another user, with scope
and provenance. Private preference deletion and auditable domain correction
retraction need distinct semantics.

## GenUI-Harness — supplied generative-UI reference

[Full paper](https://arxiv.org/html/2610.11123v1), including Appendix G limitations.
It separates task/data tools from a UI-coding role and evaluates database-backed
interactive tasks. Its study supports investigating data-aware interfaces, but
its code-generation/training approach differs from our trusted component catalog.
The authors note that source-aware simulated users and a selected usable-interface
survey subset limit transfer to real users; successful code execution does not
prove visually clear or accessible layouts.

Project implication: test the rendered five-panel experience, readable values,
correct source links, updates and recovery. Model-generated JSX is not required
to get task-specific interfaces. A typed ViewPlan is our deliberate constrained
choice and needs its own usability and correctness evidence.

## LongMemEval — memory retrieval evaluation

[Full paper](https://arxiv.org/html/2410.10813v2), especially sections 4–5.
It separates indexing, retrieval and reading, and examines multi-session recall,
time, updates and abstention. It notes that summary/fact compression can lose
detail and explores granular session decomposition and time-aware retrieval.
It does not establish cross-user authorization behavior or an optimal 3K/5K budget
for this application.

Project implication: keep exact entity-set receipts and raw sources behind
summaries, and test paraphrased cross-session questions with temporal distractors.
A missing previous conversation should produce an explicit absence, not an invented
well set. Compare memory budgets using identical fixtures and settings.

## GraphRAG — global sensemaking versus exact aggregates

[Full paper](https://arxiv.org/html/2404.16130v2), sections 3 and 6. It builds an
entity/relationship index and community summaries to answer broad corpus-level
sensemaking questions. Its evaluation covers two roughly million-token text corpora;
the authors call out limited domain generalization and the need to assess fabrication.
This is not evidence that graph summaries compute exact oil-field counts correctly.

Project implication: semantic/graph retrieval is a credible adjunct for themes,
related causes and exploratory prose. Structured joins and full-population SQL
remain authoritative for downtime, spill volume, repair costs and threshold rules.
Compare adjunct recall without substituting a sampled summary for an exact total.
