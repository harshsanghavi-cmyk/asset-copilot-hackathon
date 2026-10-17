---
name: data-integrity-audit
description: Audit this asset-copilot dataset for material answer-changing inconsistencies, missing evidence and key/cardinality errors. Use for dataset integrity review or new same-format data, not general retrieval-framework selection.
---

# Material asset-data integrity review

Read the current project scope in `../../AGENTS.md`, source joins in
`../../dataset/02-dataset-guide.md`, relevant manuals/SOPs and the prior audit in
`../../agent-memory/data-audit.md`. Treat measured inventory counts as a revision
snapshot, never runtime constants. Preserve raw files and record dataset namespace,
revision and source hashes. Keep this review within its authorized scope; running
an audit does not authorize raw-data fixes, model calls or application changes.

Audit the complete relevant population with deterministic reads, not top-k search
or example expected answers. Check primary IDs, duplicates, asset-folder identity,
user/team/area/equipment references, latest actual inspections, nullable inspection
links, numeric coherence and source units. Distinguish a repeated import from a
conflicting same-ID record before proposing deduplication. Preserve one-to-many
incident relationships; joining regulator events must not multiply spill totals.

Resolve every maintenance `report_file` relative to its owning asset directory;
verify containment within that directory, existence and report heading identity.
Compare supported header/readings/cost fields to structured rows and report
internal sums. Record extraction coverage by field and preserve exact source
spans. Unmatched wording is unknown, not automatically missing evidence.

Review material interpretation risks:

- Derive production from effective temperature delta and the applicable type
  manual. Stored status and ordinary notes can disagree; retain their provenance.
- Apply formal corrections only to their named observation/field. Ordinary
  feedback is an attributed claim, not an automatic correction. Inspect prose-only
  inspection references too. A date-based note/job association is an inference.
- Compare shutdown and delay explanations without silently choosing a source.
  Different causes may coexist; identify explicit opposed claims separately.
- Treat future completion as planned when the guide/report says so. Interim
  reports can contain past-tense summaries and estimated costs. Distinguish
  recorded amounts, estimates and evidence of actual payment/completion.
- Build compliance timelines by inspection/incident: discovery, containment,
  written notice, NOV/response and passing agency verification. Closed now can
  still mean completed late. Repair cleanup is not agency verification. Missing
  events establish absence from supplied records, not proof of real-world inaction.
- Recompute totals, deadlines and current RCA counts from complete effective
  records and applicable rules. Historical report counts/conclusions are as-of
  claims, not current fleet truth. Weekly observed downtime differs from job hours.

Report only material answer impact, with count, IDs, source path/line/field or
section/excerpt, severity, affected query classes and mitigation. Separate
intentional challenge conditions, conflicting claims, demonstrated rule breaches,
unproven gaps and ingestion defects. Include clean checks and coverage limits;
do not invent defects to fill a findings list. Documented absent photos, routine
missed inspections and planned future ends are not generic corruption findings.

Save review artifacts only in the assigned paths. Provide reproducible read-only
commands/pseudocode and measured keys/cardinalities. Label proposed storage layers
as proposals. Editable diagram sources belong under agent-memory/diagram-sources;
the coordinator alone places final PNGs in flat diagrams/.
