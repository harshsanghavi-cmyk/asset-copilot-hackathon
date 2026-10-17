# Material dataset integrity audit

17 Oct 2026 · read-only research · source revision `b8de8c9bd68f40334e5d06922126169e4f3bf3ca` · scenario reference date `2026-10-16`.

**The dataset is structurally coherent. The material risks are competing causal accounts, effective-value handling, temporal interpretation and incomplete compliance evidence—not broken ingestion files.** Full scans found no duplicate record IDs, broken asset/user/inspection references, missing linked reports, incorrect metadata latest-inspection pointers, or repair/report cost mismatches. Newly measured causal discrepancies extend beyond the reference-well examples: 27 shutdown notes deny equipment failure while a repair associated by asset and discovery date diagnoses one; another 30 notes and associated reports give different delay explanations. Preserve these accounts and their uncertainty instead of generating one definitive cause.

This is an audit of supplied evidence, not a copilot implementation or model benchmark. No raw data, secrets or application files were changed; no dependencies or model calls were used. The independent dataset Git working tree was clean at audit. The inventory records a content manifest fingerprint so the results can be tied to the measured bytes.

## Measured storage overview

The source is a filesystem dataset, **not an existing SQL database**. There are 2,516 files under `dataset/sample-data/`, totaling 23,490,962 bytes: 200 metadata JSON files, 800 JSONL files, 1,509 report Markdown files and seven fleet files (two JSON directories plus five manuals/SOPs). The ignored local clone must be acquired reproducibly when packaging; these counts describe this revision, not constants for future ingestion.

| Entity/source | Measured rows | Key and relationship |
|---|---:|---|
| Areas, `fleet/areas.json → areas[]` | 4 | PK `area_id`; FK `team_id`; redundant `asset_ids[]` membership |
| Teams, same file `teams[]` | 4 | PK `team_id`; FK `lead_user_id → users.user_id` |
| Users, `fleet/users.json → users[]` | 15 | PK `user_id`; FK `team_id` |
| Asset metadata, `assets/*/metadata.json` | 200 | PK `asset_id`; FKs `area_id`, `team_id`, `in_charge_user_id`, `well_type`; nested latest-inspection pointer |
| Equipment, nested metadata `equipment[]` | 1,094 | PK `equipment_id` is unique in this sample; five or six entries per well; `kind` is not an equipment ID |
| Inspections | 39,567 | PK `inspection_id`; FKs `asset_id`, `inspector_user_id`; 77–209 per well |
| Maintenance | 5,665 | PK `maintenance_id`; FKs `asset_id`, `technician_user_id`, nullable `triggered_by_inspection_id`; 9–38 per well |
| Corrective maintenance / linked reports | 1,509 / 1,509 | Every corrective job has one report, every report has one job; FK-like path `report_file` resolves relative to its asset folder |
| Scheduled maintenance | 4,156 | No report or inspection trigger in this sample; these are valid nulls |
| Regulatory events | 90 | PK `event_id`; FKs `asset_id`, `related_inspection_id`, protocol ID into SOP; 0–10 per well, present on 34 wells |
| Context notes | 141 | PK `note_id`; FKs `asset_id`, `author_user_id`; only 56 formal corrections carry `inspection_id`; 0–3 per well, present on 117 wells |
| Rule documents | 5 | Two type manuals, three SOPs; document/revision + section/protocol is a useful proposed evidence key |
| Image references | 79,805 unique paths | 38,896 inspections have two, 671 have three; **image files are expressly not supplied** |

There are 119 T200 and 81 T350 wells; each of four areas owns 50 wells. Equipment includes 200 each of wellhead, pump jack, rod string, downhole pump and flowline, plus 94 optional separators. Area/team/user names are display labels; IDs are the join keys. Maintenance/HSE teams need not own a geographic area.

All 1,509 non-null maintenance inspection triggers point to different inspections in this sample: observed cardinality is zero or one repair per inspection. **Do not enforce that accidental sample maximum as a universal business rule.** Regulatory events have genuine one-to-many cardinality: 90 events cover 36 inspections, with up to four events per inspection. A spill with four events must still count once. The 56 correction notes target 56 distinct inspections. `metadata.last_inspection` repeats ID/time/inspector accurately for all 200 wells, but future ingestion should still verify it against actual observations.

Reports have no JSON primary key of their own. Preserve the source path and file revision/hash; cross-check the report heading's maintenance ID. Two valid names differ from the ID: `MNT-0001-july-2025-prime-mover.md` belongs to MNT-0001-021, and `MNT-0001-june-2026-flowline-spill.md` belongs to MNT-0001-029. Building filenames from IDs would lose important evidence.

## Material findings

Severity here means impact on generated answers, not operational/legal advice. **High** changes status, totals, causal claims or compliance conclusions; **medium** changes explanation or certainty. Every affected instance has exact path, JSONL line/field or report line/excerpt in [data-audit-inventory.json](../../agent-memory/data-audit-inventory.json), under the named `findings` key. The listed query classes are coverage implications, not assertions that model tests passed.

### F1 — Competing shutdown causes on 27 wells · high · source conflict, intent unknown

All 27 notes saying “Shut in by the operator during a nearby pipeline tie-in; not an equipment failure” occur on the same asset and date as the inspection triggering a corrective equipment repair. Example: [CTX-0008-002](../../dataset/sample-data/assets/WELL-0008/context.jsonl), line 2, denies failure, while [MNT-0008-015](../../dataset/sample-data/assets/WELL-0008/maintenance.jsonl), line 15, records a flowline corrosion pinhole. Its [report](../../dataset/sample-data/assets/WELL-0008/maintenance-reports/MNT-0008-015.md), lines 12–17, says excavation found the pinhole and attributes it to internal corrosion. INS-0008-0089 on 4 Jul 2024 is the report's explicit trigger.

**Association caveat:** ordinary notes do not contain a structured inspection FK; the note-to-repair association is inferred from matching asset and `valid_from` to trigger-inspection date. All 27 matches are unique under that predicate. These are materially opposed accounts of the apparent shutdown episode, not proof that the repair is false or that the pipeline work did not also occur. Neither source authorizes deletion or a formal correction.

All affected wells: WELL-0008, 0021, 0028, 0031, 0032, 0035, 0047, 0083, 0086, 0092, 0095, 0098, 0100, 0102, 0106, 0111, 0122, 0124, 0126, 0128, 0132, 0171, 0173, 0181, 0188, 0191 and 0197. Prefix `WELL-` applies to every abbreviated item. Exact note/job/inspection triples are in `findings.conflicting_shutdown_cause.instances`.

**Impact/mitigation:** “Why was this well down?”, equipment-failure summaries and maintenance RCA narratives must present both accounts with attribution. Use the thermal observation for production classification and count actual corrective records for RCA; do not silently reclassify repair rows because an ordinary note says “not an equipment failure.” Ask for clarification when a single confirmed cause is required.

### F2 — Different delay explanations in 30 more note/report pairs · medium · unresolved, potentially compatible

Of 54 bounded notes about weather delays or waiting for parts, 30 associated reports explicitly give another delay category, 11 support the same category and 13 give no explicit extra-delay reason. Example [CTX-0002-001](../../dataset/sample-data/assets/WELL-0002/context.jsonl), line 1, blames weather, while the [MNT-0002-018 report](../../dataset/sample-data/assets/WELL-0002/maintenance-reports/MNT-0002-018.md), line 13, says the replacement part was back-ordered. Match predicate and uncertainty are the same as F1. These causes could coexist; the data does not establish a sole cause or source precedence. `findings.different_delay_explanations.instances` contains all 30 exact pairs and excerpts.

**Impact/mitigation:** preserve separate claims for downtime explanations and planned restart answers. Do not combine them into a fabricated chronology or select the latest document as universally authoritative. Do not include these pairs in a count of proven data errors.

### F3 — 21 stored statuses disagree with current thermal evidence · high · intentional challenge condition

Latest observations show 15 non-producing wells. Of 21 disagreements, 13 metadata values say `active` despite non-producing thermal deltas, and eight say `down` despite producing deltas. For example WELL-0002 is recorded down but INS-0002-0141 has delta 30.5 °C; WELL-0001 is recorded active but INS-0001-0203 has delta 3.2 °C. Both directions matter. All 21 IDs/readings are under `findings.stale_recorded_status`.

**Impact/mitigation:** current status, maps and downtime tools derive corrected wellhead minus ambient with T200 ≥15 °C / T350 ≥20 °C. Cite [T200 §9.3](../../dataset/sample-data/fleet/well-types/T200.md) or [T350 §3](../../dataset/sample-data/fleet/well-types/T350.md). Keep the stored status visibly attributable; do not call accurate latest-inspection metadata stale. Ordinary notes do not alter a numerical production threshold. Covers current-status/area-list classes and Q1/Q2/Q12/Q15/Q17.

### F4 — 56 formal false-positive corrections change fleet totals · high · intentional effective-value requirement

Raw inspections contain **672 spill detections totaling 1,466.0 bbl**. All 56 formal corrections name valid spill inspections on their own well and identify water, soil or shadow rather than crude. Excluding those targets removes **113.7 bbl**, leaving **616 real spills and 1,352.3 bbl** over the entire supplied observation history. This is a measured audit calculation, not a hardcoded runtime answer. Seventeen exclusions fall in 2026.

All 56 targets are unique, correction dates match discovery dates, and none has a linked repair or regulator event. Originals remain `spill_detected=true` with estimated volume; filtering raw flags alone is wrong. Example CTX-0001-001, [context line 1](../../dataset/sample-data/assets/WELL-0001/context.jsonl), corrects INS-0001-0070. All target IDs/authors/timestamps/original volumes are in `findings.formal_false_positive_corrections`.

**Impact/mitigation:** normalize these as scoped effective detection corrections while preserving original values, source wording and provenance. Apply before spill counts, sums, area/month heatmaps, maps and compliance classification. A correction belongs to its named inspection, not every observation from `valid_from` onward. Current source corrections are all detection corrections; future field corrections require typed targets rather than a general “any note suppresses spill” rule.

Conversely, [CTX-0101-002 and CTX-0101-003](../../dataset/sample-data/assets/WELL-0101/context.jsonl), lines 2–3, are **ordinary feedback**, disagree about INS-0101-0197 and have no structured inspection FK. Ryan Brooks suspects water; Chris Dalton says a sample confirmed crude. The detection and MNT-0101-029 repair stand with both claims visible. A retrieval path following only formal `inspection_id` fields would miss this conflict. Covers Q4/Q7/Q8/Q13/Q15/Q18 and any fleet spill aggregate.

### F5 — Nine interim repairs carry planned ends and estimated costs · high · semantic hazard, not corrupt dates

IDs: MNT-0013-037, MNT-0077-025, MNT-0079-036, MNT-0110-030, MNT-0115-037, MNT-0121-035, MNT-0123-015, MNT-0170-031 and MNT-0172-028. Their `completed_at` is after 16 Oct. All nine reports explicitly say interim/work in progress and label costs as estimates, totaling **USD 95,716** in recorded amounts. All also contain a past-tense “Summary of the fix,” which can mislead if extracted in isolation.

Example [MNT-0172-028 report](../../dataset/sample-data/assets/WELL-0172/maintenance-reports/MNT-0172-028.md): lines 5–8 give a planned finish and interim status; lines 31–37 say testing/return to service are still to do, while line 33 summarizes the fix in past tense; line 39 labels cost an estimate. `maintenance.action_taken` similarly does not prove completed work. See all spans in `findings.interim_repairs`.

**Impact/mitigation:** status/cause answers and cost dashboards need explicit as-of completion state and cost basis. For “recorded repair cost” include the source amount with an estimate flag when applicable; for actual invoiced/paid cost the supplied fields do not establish it. Do not silently exclude these rows from a start-date period total or label all amounts realized expenditure. Weekly downtime remains seven days per observed non-producing inspection; the 928 hours on MNT-0170-031 describe its planned job interval, not that query metric. Covers Q2/Q5/Q6/Q11 and future maintenance/cost questions.

### F6 — Closed events do not establish timely compliance · high · demonstrated historical breaches

There are 36 effective reportable spills, 36 written notices, 11 NOVs, nine recorded NOV responses and 34 site inspections. **Six passing site inspections occurred 75 days after discovery**, beyond [SR-03's 60-day requirement](../../dataset/sample-data/fleet/sops/spill-response-sop.md), despite now being `closed`:

| Agency event | Discovery inspection | Verification due | Verified |
|---|---|---|---|
| REG-0064-002 | INS-0064-0103 | 23 Dec 2024 | 7 Jan 2025 |
| REG-0138-002 | INS-0138-0079 | 24 Jun 2024 | 9 Jul 2024 |
| REG-0145-002 | INS-0145-0067 | 22 Apr 2024 | 7 May 2024 |
| REG-0160-003 | INS-0160-0025 | 5 Jun 2023 | 20 Jun 2023 |
| REG-0168-008 | INS-0168-0144 | 22 Sep 2025 | 7 Oct 2025 |
| REG-0168-010 | INS-0168-0190 | 10 Aug 2026 | 25 Aug 2026 |

Each event is in its owning well's `regulatory-events.jsonl`; exact line refs and the linked historical report are under `findings.late_closed_verification`. The WELL-0168 history also shows why “one regulator record per well” is invalid: it has three separate reportable incidents and ten agency events.

**Historical-report trap:** all 36 original reportable-spill repair reports say SR-03 “In progress.” Later agency evidence closes verification for 33; one agency inspection remains open after a failed/pending result, and two spills have no agency inspection yet. Those two are INS-0042-0203, due 16 Nov 2026, and INS-0123-0093, due 23 Nov 2026—**not yet overdue** at this reference date. Repair cleanup completion and a passing agency verification are separate milestones.

Two NOVs remain open with **no recorded response**: REG-0001-002 (USD 5,000; response due 30 Jul 2026) and REG-0160-002 (USD 2,500; due 4 Jun 2023). All nine supplied responses to the other NOVs are within 30 days. Cite [RC-04](../../dataset/sample-data/fleet/sops/regulatory-compliance-sop.md) and the complete incident's event set. Missing evidence justifies “no response on record / possible unrecorded response,” not invented real-world non-action. An event's `closed` status applies to that event, not every duty on the well. No explicit closure timestamp exists for historical as-of reconstruction.

**Impact/mitigation:** compliance/open-action dashboards need incident-level evidence timelines and separate `requirement_met`, `met_late`, `open_not_due`, `overdue_no_record` and `unknown` states. Do not use the most relevant repair report or one event's status as a current universal verdict. Covers Q9 and fleet compliance questions.

### F7 — Containment is report-only evidence across 616 spills · high · retrieval/interpretation risk

Every effective spill has a linked repair report and an explicit containment-hours phrase; **211 of 616 exceed four hours**, with matching SR-02 “Not met” table labels. All 211 maintenance/inspection IDs and exact report excerpts are under `findings.containment_breaches`. These are observed source facts, not missing data. MNT-0001-029's report explicitly says about seven hours; its job lasts 35 hours, and the written report was filed after 41 hours. Those are three different clocks.

**Impact/mitigation:** enumerate all relevant spill inspections first, follow each repair's actual `report_file`, extract and cite containment prose, then compare against SR-02. Repair duration, first maintenance start and `hours_to_report` cannot substitute for containment. A top-k document result cannot establish “every late spill.” Covers Q10 and fleet compliance analysis.

## Clean checks and audit coverage

The inventory's `clean_checks` records evaluated counts and zero violations for all checks actually executed. All JSON/JSONL records parsed; record ID uniqueness, asset-folder association, user/team/area joins, equipment-kind membership, inspection FKs, full latest-inspection pointers and report path containment were checked. All 1,509 reports exist, have unique referenced paths, and none is orphaned. Every corrective repair has one; no supplied report was lost by ignoring nonstandard names.

All 5,665 costs satisfy labor + parts = total; none has negative cost or hours. Every job's timestamp interval equals its recorded hours, no completion precedes its start, and no triggered job precedes discovery. No inspection/job precedes asset installation. No producing thermal observation falls inside a corrective job's stopped interval. Spill flag/null coherence passes all 39,567 observations.

For **all 1,509 reports**, parsed title ID, asset ID/type, equipment kind, technician ID, trigger ID/date, start/end times, duration, internal line-item sum, labor, parts and total agree with the structured record. Parsed report thermal readings agree for 892 reports; volume agrees for 616, and affected-area regex matches 615. Those figures describe extraction coverage; unmatched narrative formats were not falsely counted as missing data or certified correct. Explicit “weekly drone” wording matches inspection method in all 504 reports where that pattern occurs.

Observed numeric ranges: ambient 4.0–43.1 °C; wellhead 3.5–77.4 °C; detected affected area 0.6–12.0% of pad; estimated spill volume 0.1–6.8 bbl. No supplied spill reaches the major class; there are 137 minor, 443 moderate and 36 reportable effective spills. Units are guide-defined; volume is not a pad-area percentage, and a flowline MOP is not the wellhead's pressure rating. The ranges alone do not certify physical measurement accuracy.

Report structure varies in meaningful ways: nine interim “Work done so far” / “Parts and cost (estimate; work in progress)” sections, 616 spill-cleanup sections, 323 waste sections and differing protocol rows. Protocol compliance tables record 211 SR-02, 11 SR-01, 35 WS-07, 26 WS-03, 22 WS-01 and 19 WS-06 “Not met” entries. These are report claims, not an independently verified exhaustive fleet breach ledger. Three interim WS-06 rows and nine WS-07 rows are pending. Do not infer “met” when a protocol is absent or pending.

There are 307 historical report RCA count claims. Their date anchor can differ from the current query and is not explicit enough to reuse as a current aggregate. Recompute per equipment kind from complete maintenance rows using the requested window/manual and any valid scoped override. A boundary-dependent 4-versus-5 historical count was not promoted into a material error: it does not change RCA eligibility and the prose lacks a precise as-of anchor.

**Known absence, not corruption:** 79,805 image references have no supplied image bytes by design. Do not display generated evidence photos or infer visual verification. Routine missed inspections and later-installed wells are expected; they do not warrant fabricated readings, calendar-gap downtime or generic corruption flags. Runtime temperature/volume corrections, type-wide overrides and private conversation histories are not supplied records; Q12–Q17 describe future user inputs, not existing evidence to ingest from expected answers.

## Reproducible read-only methodology

Run from the repository root with standard-library Python 3. The following core scan reproduces the material conflict/status/spill/interim/containment counts; it reads raw files only. The audit inventory is a research output, not backend application code.

```python
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
import json, re

root = Path('dataset/sample-data/assets')
def rows(kind):
    return [json.loads(line) for p in sorted(root.glob('*/'+kind+'.jsonl'))
            for line in p.read_text().splitlines() if line.strip()]
assets = {x['asset_id']: x for x in
          (json.loads(p.read_text()) for p in root.glob('*/metadata.json'))}
inspections = rows('inspections'); jobs = rows('maintenance')
notes = rows('context'); events = rows('regulatory-events')
by_id = {i['inspection_id']: i for i in inspections}
corrections = {n['inspection_id'] for n in notes if n['note_type']=='correction'}
real = [i for i in inspections if i['spill_detected']
        and i['inspection_id'] not in corrections]
print('real spills / bbl', len(real),
      sum(Decimal(str(i['spill_est_volume_bbl'])) for i in real))
stale = 0
for asset_id, asset in assets.items():
    i = max((i for i in inspections if i['asset_id']==asset_id),
            key=lambda i:i['inspected_at'])
    delta = Decimal(str(i['wellhead_temp_c']))-Decimal(str(i['ambient_temp_c']))
    producing = delta >= (15 if asset['well_type']=='T200' else 20)
    stale += producing != (asset['recorded_status']=='active')
print('stale recorded status', stale)
counts = Counter(); containment = []
for job in jobs:
    if not job['report_file']: continue
    p = root/job['asset_id']/job['report_file']
    assert p.resolve().is_relative_to((root/job['asset_id']).resolve())
    text = p.read_text(); trigger = by_id[job['triggered_by_inspection_id']]
    counts['interim'] += job['completed_at'][:10] > '2026-10-16'
    match = re.search(r'contained about (\d+(?:\.\d+)?) hours after', text)
    if match: containment.append(Decimal(match[1]))
    for note in notes:
        if (note['note_type'] != 'operator_note' or not note['valid_to']
            or note['asset_id'] != job['asset_id']
            or note['valid_from'] != trigger['inspected_at'][:10]): continue
        if 'not an equipment failure' in note['text']:
            counts['opposed_cause'] += 1; continue
        delay = re.search(r'The well (?:stayed|is expected to stay) shut in '
                          r'for about (.+?) because (.+?)\.', text)
        if not delay: counts['no_explicit_delay'] += 1; continue
        agree = (('weather' in note['text'] and 'heavy rain' in delay[2]) or
                 ('replacement parts' in note['text'] and 'back-ordered' in delay[2]))
        counts['same_delay' if agree else 'different_delay'] += 1
print(counts, 'containment evaluated / late', len(containment),
      sum(h > 4 for h in containment))
```

For regulatory reproduction: group **all** events by `related_inspection_id`; join effective spills and linked reports; compute discovery-date +60 days for SR-03, NOV-date +30 days for RC-04, and discovery-timestamp + `hours_to_report` for written-report chronology. Compare event types separately; use passing agency detail/status for closure, not just any site event. All 36 written-report event dates match inspection timestamp plus recorded hours. Date-only agency events do not support hour-precise verification/response claims.

For report-copy reproduction: resolve every non-null `report_file`; parse the heading/header and the `Parts and cost` section (including its interim suffix); strip comma separators and Markdown emphasis from amounts; compare labor and the sum of all other line items with `cost_usd`; compare total with both their sum and the structured total. Match equipment display spaces to structured underscores. Preserve unmatched fields as unknown; report parser coverage per field is in `report_parse_coverage`, not a blanket assertion that all prose is verified.

Fingerprint reproduction: sort every file under `dataset/sample-data/`; concatenate `relative_path + '\t' + sha256(file_bytes) + '\n'`; SHA-256 that UTF-8 manifest. The resulting digest is `2c5b9529c5ebbef7557ae947d8fefada69eb6d66fd382a82afd2166bca54d492`. Git identity is independently recorded in [docs/dataset-source.json](../../docs/dataset-source.json).

## High-level storage mapping proposal and next checks

Keep immutable source records/docs with path, line/section and hash; normalize the measured entities/keys into the retrieval track's chosen store. Add shared, attributed corrections/rules/operational claims as distinct records; current effective views apply the ledger and feed deterministic result sets. Keep private conversation references keyed by trusted user separately. These are proposed storage mappings, not existing tables or new framework recommendations.

Read and aligned with [retrieval research](retrieval-research.md), [memory research](memory-research.md), [UI research](ui-research.md), coordinator notes and the recovery steering/experiment policy. Retain their `EvidenceRef`, `ResultSet`, `dataset_revision` and `knowledge_revision` seams. The integrity additions are causal-claim attribution, explicit extraction coverage, incident timelines and estimated/interim cost state. All panels and prose must share effective facts/revisions. This audit changes no UI/framework recommendation and uses no experiment branch.

Before implementation claims, test held-out same-format data through the same joins; preserve zero/multiple child relations; distinguish repeated source imports from conflicting same-ID records using dataset namespace/revision. Add acceptance fixtures from F1/F2, both stale-status directions, all false-positive corrections, interim cost semantics, late-but-closed verification and report filename variation. Run full-population aggregates before presentation pagination. Cross-user shared operational facts are broader than corrections; private conversation entity sets remain private. Existing Q1–Q10 baseline fixtures and the specified Q11–Q18 sequence remain separate from runtime evidence.

Artifacts: [measured inventory](../../agent-memory/data-audit-inventory.json); `diagram-sources/data-audit/01-data-overview.mmd`; `02-keys-and-relations.mmd`; `image-brief.txt`; [integrity-review skill](../../skills/data-integrity-audit/SKILL.md). Source diagrams describe the measured file relationships and clearly marked proposed effective/private storage layers. The coordinator alone renders/enhances final PNGs in flat `diagrams/`.

Artifact validation: the official skill-creator `quick_validate.py` reports “Skill is valid!”; all report links resolve; all 630 inventory source references/excerpts were checked against the actual file and record/field; every recorded clean check has zero violations. Executing the report's read-only reproduction snippet returns 616 spills / 1,352.3 bbl, 21 stale statuses, 27 opposed cause accounts, 30 different delays, nine interim repairs and 211 late containments among 616 evaluated reports. Mermaid received structural/manual review only; rendering and final image inspection remain the coordinator's responsibility. No application/model test result is implied.
