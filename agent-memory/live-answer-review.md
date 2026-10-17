# Independent review of completed live answers

17 Oct 2026 · first available batch. Google AI Studio / ChatGoogleGenerativeAI / `gemma-4-26b-a4b-it` is the currently authorized model. **Neither completed answer is a full semantic pass**, despite evaluator PASS labels. This review made no model/API calls, code edits, fixture/runtime changes, service launches or new sessions; only this report was written.

Source: bounded read of `runtime/live-evaluation.json` (about182KB initially; size checked before parsing), completed envelopes Q1/Q2, and relevant raw source records/manuals. Latest batch metadata inspected: `updated_at=2026-10-17T10:25:01.063644+00:00`. Failed runs without a final envelope are not scored as factual hallucinations. Each completed envelope below was assessed once; follow-up checks extracted supporting metadata rather than rerunning the questions. Later retries must be distinguished by answer-content hash, since the evaluator can reuse answer IDs.

## Incremental matrix

| Scenario / actual answer | Facts and result data | Explanation / completeness | Citations | Visual contract | Independent verdict |
|---|---|---|---|---|---|
| Q1 / eval-Q1-answer | **PASS core:** correct latest inspection/time, Ryan Brooks/drone,25.6°C wellhead,22.4°C ambient,3.2°C delta in result; producing=false | **FAIL:** no planned7Oct rod-string replacement, Jake attribution, expected20Oct return or missing work-order context; no3.2-versus15°C rule explanation or stale active-status disclosure | **PARTIAL:** narrative cites a real result handle, inspection/manual sources exist in registry, but applicable rule and planned-shutdown note are not cited; no CTX note is present anywhere in evidence | **FAIL binding:** status block uses spill_detected as production status, recorded_status as asset label, producing boolean as value. Type exists, semantics wrong; no screenshot claim | **FAIL full answer** |
| Q2 / eval-Q2-answer | **FAIL narrative / PASS retrieved set:** says two down wells while its cited result contains all four correct wells/deltas | **FAIL:** wrongly says WELL-0170 cause unknown; open bearing repair is supplied. Omits WELL-0172/0175 from explanation and treats WELL-0164's stopped-pump observation as causal explanation rather than unknown underlying reason | **FAIL claim support:** cited four-row result contradicts “two”; no linked repair sources for0170/0172 are present. Having manuals in registry does not support the missing causes | **PASS declared type only:** table references the correct four-row result; actual rendered presentation not inspected | **FAIL full answer** |
| Q3–Q11 | Initial receipt batch contains generation/empty-response/JSON/grounding failures, not completed envelopes | Not assessed | Not assessed | Not assessed | **BLOCKED / no final answer to review** |
| Q12–Q18 | No completed envelopes available in this reviewed batch | Not assessed | Not assessed | Not assessed | **BLOCKED / no final answer to review** |

Do not convert this matrix to “0/18 factual accuracy.” Two completed answers have material semantic failures; sixteen lack reviewed completed envelopes. Likewise the automatic two PASS labels do not establish two successful official scenarios. The review covers payload semantics and raw evidence, not browser rendering or all private/shared sequences.

## L1 — Q1 missing decisive operational context

Answer `eval-Q1-answer`, primary result `result_053529c84bd84398b08c853dd6e4157c`, knowledge_revision0, reference_date2026-10-16. The narrative correctly states not producing and latest inspector/time, and lists the two temperatures. It never explains the applicable threshold, the recorded-status disagreement, or why the well was deliberately stopped.

Raw oracle: [WELL-0001 context.jsonl](../dataset/sample-data/assets/WELL-0001/context.jsonl), line3, **CTX-0001-003** by U-102/Jake Morales, recorded8Oct, valid7–20Oct. It states planned rod-string replacement from7Oct, expected return around20Oct, and work order not yet in maintenance. [Latest inspection](../dataset/sample-data/assets/WELL-0001/inspections.jsonl), line203, **INS-0001-0203**, records15Oct09:45UTC, U-104/Ryan Brooks, drone,22.4/25.6°C and “Pump jack not moving.” [Metadata](../dataset/sample-data/assets/WELL-0001/metadata.json) still says active; [T200 §9.3](../dataset/sample-data/fleet/well-types/T200.md) requires at least15°C above ambient.

The answer registry has54 evidence objects, largely inspection history/manuals, but **none contains CTX-0001-003 or any CTX note**. A second result contains50 of203 historical observations (complete calculation coverage, presentation truncated). That additional history does not replace the relevant shutdown note. Warning: “Evidence search unavailable: Supply searchable text or a registered evidence handle.” The answer therefore needs targeted operational-context retrieval, not simply more inspection rows.

Required repair: fetch applicable original context notes/shared assertions and relevant active jobs when explaining status; distinguish observation from cause. Include cited3.2°C delta versus15°C rule, stale stored active status and attributed planned-shutdown explanation. Do not claim the work was completed or that the expected return is guaranteed. This is a missing supported explanation, not a hallucinated temperature.

## L2 — Q1 production card is semantically misbound

Block `eval-Q1-answer:block:0` is titled “WELL-0001 Status Card” but has:

```json
{"label":"recorded_status","value":"producing","status":"spill_detected"}
```

All three are valid columns, so existence-only validation misses the problem. The row has recorded_status=active, producing=false and spill_detected=false. Current [PanelContent](../frontend/src/components/AnswerDashboard.tsx) interprets a boolean chosen as status as Producing/Not producing, so this binding derives a production label from spill absence and uses “active” as the asset label. It happens to agree with this well's down state; the same binding would mislabel a producing/no-spill well. Secondary value is a raw boolean rather than the thermal delta.

Required repair: production status blocks must bind semantic producing, asset_id label and appropriate units/value such as delta_c when shown. The backend and UI owners were sent the exact block/result IDs. Validate role meaning in addition to column membership; a spill flag must not become a production flag. This review did not open the UI or generate a screenshot.

## L3 — Q2 contradicts its own complete result and misses recorded repairs

Answer `eval-Q2-answer`, result **result_b7a5c7964dc045e8b466cb605589d0b2**. Its narrative begins “In Northeast Block 8, two wells are currently not producing oil” but the cited result has matching=evaluated=4, unknown0, no presentation truncation and these four rows:

| Well | Inspection | Delta°C | Stored status | Correct explanation evidence |
|---|---|---:|---|---|
| WELL-0164 | INS-0164-0205 |4.1|active| Underlying cause unrecorded; stopped-pump observation is not a diagnosed cause |
| WELL-0170 | INS-0170-0206 |2.9|down| MNT-0170-031: walking-beam bearing wear, started19Sep, planned end28Oct |
| WELL-0172 | INS-0172-0206 |5.7|active| MNT-0172-028: flowline corrosion pinhole leak, started3Oct, planned end21Oct |
| WELL-0175 | INS-0175-0204 |0.4|active| No recorded current cause |

Raw repair references: [WELL-0170 maintenance](../dataset/sample-data/assets/WELL-0170/maintenance.jsonl), line31, **MNT-0170-031** and its declared report; [WELL-0172 maintenance](../dataset/sample-data/assets/WELL-0172/maintenance.jsonl), line28, **MNT-0172-028** and its declared report. Both reports explicitly describe interim/in-progress work at the reference date. Empty notes on the latest inspection do not establish absence of a cause across maintenance/context sources.

The answer's13 evidence objects include inspections/manuals/SOP chunks but **neither repair ID**. Its warning says an RCA query was unavailable because counts require an equipment kind. An unrelated unsupported RCA attempt does not justify answering “unknown” without checking actual open repair records. No need to invent a cause for0164/0175; the missing0170/0172 explanations are directly supported.

Required repair: derive narrative cardinality from the displayed/full result, enumerate all four wells in the explanation, query linked/overlapping jobs and applicable notes, and preserve “No recorded reason” only when the relevant source scope was checked. Bind each explanation to its actual evidence and distinguish planned completion from completed work.

## Evaluator gaps and minimal follow-up checks

The current [live evaluator](../backend/evaluate_live.py) checks Q1's down flag/delta/inspection evidence/card existence and Q2's result-set membership/table type. It does not check Q1 planned-shutdown context, threshold reasoning or status-column meaning, nor compare Q2's narrative count/causes with the result. Consequently both stored PASS labels are false positives for complete official requirements.

Add semantic checks without injecting expected answers into runtime prompts: narrative count must agree with exact matching set; each listed well must be accounted for; required cause sources must be consulted; observational notes cannot silently become diagnoses; status rendering must consume a production-typed field. For Q1 require source/rule support, CTX note attribution and stale-status distinction. For Q2 require four wells plus known repairs and correct unknown cases. Preserve this failed receipt when retrying; changing code is not proof that this existing answer was corrected.

Future completed batches need independent checks of full chart values/bounds/markers, spill-correction exclusions and totals, zero heatmap cells, report-only containment, compliance deadlines/closure, and the stated cross-user/private-memory sequence. Q1–Q10 must remain independent originals; Q11–Q18 carry only declared dependencies. No later result is passed merely because a prior deterministic provider fixture was correct.

## Evidence identity and handoff

Reviewed answer hashes (SHA256 of sorted-key JSON serialization):

- Q1: `1e77411d8369c57ff5fb021807b5672516f21801dac7ebe39a9051fd66926ccb`
- Q2: `2562fd26cca6e9658e5c63d27a26b48f7fd016c99a39c4415ab1e48f258b66d1`

Shared dataset_revision for these envelopes: `73efe30ac34f41cac36c031a3656e4b928bee4f2539eaee27e0ffb3329f3005e`. Findings were sent immediately through Orca to backend ctx_5fd4f29f0867, UI ctx_84fbbad785d2 and coordinator. No raw private conversation history or secrets are copied here; only official synthetic scenario output fragments, source IDs and required evidence are recorded. Owners can fix/re-evaluate; this batch does not certify those fixes or later answers.
