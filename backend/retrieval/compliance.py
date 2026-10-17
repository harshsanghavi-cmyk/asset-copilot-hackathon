"""Deterministic, source-backed spill duties; no LLM arithmetic or generic legal claims."""
import datetime as dt
import json
import re
import time
import uuid

from .contracts import RetrievalError
from ..ingestion.loader import uid


def assess(provider, plan, context, filters, start, end, reference, asof_end):
    if plan.get("group_by"):
        raise RetrievalError("unsupported_operation", "Compliance returns one row per incident/duty; grouping is not implemented")
    began = time.perf_counter()
    sql, params, population, _, _ = provider._compile("inspections", "spills", filters, [], start, end, asof_end, reference)
    incidents = provider._run(sql + " LIMIT 1001", params)
    if len(incidents) > 1000:
        raise RetrievalError("resource_limit", "Compliance exceeds 1000 incidents; narrow the period or asset scope")
    sources = provider._run("SELECT id,preview FROM sources WHERE kind='sop'")
    protocols = {}
    for source in sources:
        for line in source["preview"].splitlines():
            if not line.lstrip().startswith("|"):
                continue
            protocol = re.match(r"^\|\s*\*{0,2}((?:SR|RC)-\d{2})\*{0,2}\s*\|", line)
            if protocol:
                protocols[protocol[1]] = {"text": line.replace("*", ""), "source_id": source["id"]}
    def hours(pid, major=False):
        text = protocols.get(pid, {}).get("text", "")
        values = re.findall(r"within\s+(\d+)\s+hours", text, re.I)
        return int(values[1 if major else 0]) if len(values) > (1 if major else 0) else None
    def days(pid):
        match = re.search(r"within\s+(\d+)\s+days", protocols.get(pid, {}).get("text", ""), re.I)
        return int(match[1]) if match else None
    class_match = next((re.search(r"\|\s*Reportable\s*\|\s*(\d+(?:\.\d+)?)\s*bbl to below\s*(\d+(?:\.\d+)?)", s["preview"], re.I) for s in sources if "Spill classes" in s["preview"]), None)
    reportable = float(class_match[1]) if class_match else None
    major_threshold = float(class_match[2]) if class_match else None
    rows, all_event_ids = [], set()
    today = dt.date.fromisoformat(reference)
    for inspection in incidents:
        iid, asset = inspection["inspection_id"], inspection["asset_id"]
        discovered = dt.datetime.fromisoformat(inspection["inspected_at"].replace("Z", "+00:00"))
        volume = inspection["spill_est_volume_bbl"]
        spill_class = "unknown" if volume is None or reportable is None else "major" if volume >= major_threshold else "reportable" if volume >= reportable else "below_reporting_threshold"
        events = [json.loads(r["raw_json"]) for r in provider._run("SELECT r.raw_json FROM regulatory_events e JOIN records r ON r.id=e.event_id WHERE e.inspection_id=? AND e.date<? ORDER BY e.date,e.event_id", (iid, asof_end))]
        all_event_ids.update(e["event_id"] for e in events)
        facts = provider._run("SELECT f.value_json,f.source_id,f.id,m.maintenance_id FROM facts f JOIN maintenance m ON m.maintenance_id=f.subject_id WHERE m.inspection_id=? AND f.predicate='containment_hours'", (iid,))
        def add(pid, duty, state, due=None, observed=None, limit=None, detail="", extra_refs=(), fine=None):
            source = protocols.get(pid)
            refs = [uid("ev_", iid)] + ([source["source_id"]] if source else []) + list(extra_refs)
            rows.append({"asset_id": asset, "inspection_id": iid, "discovered_at": inspection["inspected_at"], "spill_volume_bbl": volume, "spill_class": spill_class, "protocol_id": pid, "duty": duty, "assessment": state, "due_date": due.date().isoformat() if isinstance(due, dt.datetime) else due.isoformat() if due else None, "due_at": due.isoformat() if isinstance(due, dt.datetime) else None, "observed_hours": observed, "limit_hours": limit, "fine_usd": fine, "detail": detail, "evidence_refs": list(dict.fromkeys(refs))})
        delay_values = {float(json.loads(f["value_json"])) for f in facts}
        delay = next(iter(delay_values)) if len(delay_values) == 1 else None
        containment_limit = hours("SR-02")
        state = "unknown" if delay is None or containment_limit is None else "breach_supported" if delay > containment_limit else "met"
        add("SR-02", "source_stop_and_containment", state, observed=delay, limit=containment_limit, detail="Approximate elapsed containment from linked report, not repair duration", extra_refs=[f["id"] for f in facts[:4]])
        if spill_class == "unknown":
            add("SR-01", "written_notice", "unknown", detail="Effective volume or supplied spill-class rule is missing")
            continue
        if spill_class in ("reportable", "major"):
            limit = hours("SR-01", spill_class == "major")
            due = discovered + dt.timedelta(hours=limit) if limit is not None else None
            written = [e for e in events if e["event_type"] == "spill_report_filed"]
            if written and written[0].get("hours_to_report") is not None and limit is not None:
                elapsed = written[0]["hours_to_report"]
                state = "breach_supported" if elapsed > limit else "met"
            else:
                elapsed = None
                state = "unknown" if due is None else "possible_breach_missing_record" if due.date() < today else "pending_not_due"
            add("SR-01", "written_notice", state, due=due, observed=elapsed, limit=limit, detail="Written notice only; immediate phone-call duty has no separate supplied evidence" if written else "No written notice recorded in the imported incident events; real-world non-filing is not independently proven", extra_refs=[uid("ev_", e["event_id"]) for e in written])
            verify_days = days("SR-03")
            verify_due = discovered + dt.timedelta(days=verify_days) if verify_days is not None else None
            site_events = [e for e in events if e["event_type"] == "site_inspection"]
            passing = [e for e in site_events if e.get("status") == "closed" and re.search(r"pass|verified|below|met", e.get("detail", ""), re.I) and not re.search(r"fail|pending|residual", e.get("detail", ""), re.I)]
            if passing and verify_due:
                state = "met_late" if dt.date.fromisoformat(passing[0]["date"]) > verify_due.date() else "met"
            elif verify_due is None:
                state = "unknown"
            elif verify_due.date() >= today:
                state = "pending_not_due"
            else:
                state = "breach_supported" if any(e.get("status") == "open" for e in site_events) else "possible_breach_missing_record"
            add("SR-03", "passing_agency_verification", state, due=verify_due, detail="Requires a passing environmental-agency site inspection; cleanup or verification request is not closure", extra_refs=[uid("ev_", e["event_id"]) for e in site_events])
        novs = [e for e in events if e["event_type"] == "notice_of_violation"]
        responses = [e for e in events if e["event_type"] == "nov_response_filed"]
        for nov in novs:
            limit_days = days("RC-04")
            due = dt.date.fromisoformat(nov["date"]) + dt.timedelta(days=limit_days) if limit_days else None
            paired = responses if len(novs) == 1 else [e for e in responses if nov["event_id"] in e.get("detail", "")]
            if paired and due:
                state = "met_late" if dt.date.fromisoformat(paired[0]["date"]) > due else "met"
            else:
                state = "unknown" if due is None else "possible_breach_missing_record" if due < today else "pending_not_due"
            add("RC-04", "notice_of_violation_response", state, due=due, detail=f"NOV {nov['event_id']} remains {nov.get('status')}; response evidence and agency closure are separate", extra_refs=[uid("ev_", nov["event_id"])] + [uid("ev_", e["event_id"]) for e in paired], fine=nov.get("fine_usd"))
    all_rows = rows
    if plan.get("only_breaches"):
        rows = [r for r in rows if r["assessment"] in ("breach_supported", "met_late", "possible_breach_missing_record")]
    unknown = sum(r["assessment"] == "unknown" for r in all_rows)
    issue_count = provider._run("SELECT count(*) n FROM issues")[0]["n"]
    limit, offset = int(plan.get("limit", 50)), int(plan.get("offset", 0))
    rows.sort(key=lambda r: (r["asset_id"], r["discovered_at"], r["protocol_id"], r["duty"]))
    page = [dict(r) for r in rows[offset:offset + limit]]
    result_id = "result_" + uuid.uuid4().hex
    for i, row in enumerate(page):
        row["row_id"] = uid("row_", result_id + str(offset + i))
        row["evidence_refs"].append(result_id)
    coverage = {"unit": "incident_protocol_requirement", "matching": len(all_rows), "evaluated": len(all_rows) - unknown, "unknown": unknown, "source_incidents": len(incidents), "import_issues": issue_count, "status": "partial" if unknown or issue_count else "complete", "displayed_rows": len(page), "output_rows": len(rows), "display_truncated": offset + len(page) < len(rows), "aggregation_input_truncated": False}
    warnings = ["Assessment supports supplied SR-01 written notice, SR-02 elapsed containment, SR-03 agency verification and RC-04 response only; it is not an exhaustive safety/legal compliance audit", "Missing records are not independent proof of real-world inaction; same-day deadline time is not assumed passed from a calendar reference date"]
    trace = provider._save_trace({"operation": "compliance", "input_text": plan.get("input_text", ""), "plan": plan, "safe_sql": sql + " LIMIT 1001", "parameters": ["<redacted>" for _ in params], "tables": ["inspections", "maintenance", "facts", "regulatory_events", "records", "sources"], "follow_up_reads": "Bounded parameterized incident-event/report-fact lookups; supplied SOP rows parsed deterministically", "knowledge_revision": provider._authority.knowledge_revision, "coverage": coverage, "selected_evidence": list(dict.fromkeys(e for r in page for e in r["evidence_refs"]))[:30], "omitted_evidence": [{"reason": "presentation_pagination", "rows": max(0, len(rows) - len(page))}], "tokens": {"provider_tokens": None, "method": "No model called; renderer receives exact result handles"}, "elapsed_ms": round((time.perf_counter() - began) * 1000, 3)})
    result = {"schema_version": "1.0", "provider_id": provider.provider_id, "result_set_id": result_id, "dataset_namespace": provider.namespace, "dataset_revision": provider._manifest["dataset_revision"], "knowledge_revision": provider._authority.knowledge_revision, "reference_date": reference, "bounds": {"start": start, "end": end, "closure": "both"}, "time_basis": "inspection discovery timestamp / NOV date; deadlines computed from supplied SOP rows", "rows": page, "columns": provider._result_columns(page, [("protocol_id", None), ("assessment", None)]), "coverage": coverage, "total_rows": len(rows), "limit": limit, "offset": offset, "rule_refs": sorted({r["source_id"] for r in protocols.values()}), "lineage_manifest_ref": result_id, "trace_id": trace, "warnings": warnings}
    provider._persist_manifest(result_id, plan, context, provider._authority, result)
    provider._results[result_id] = {"plan": dict(plan), "context": dict(context), "authority": provider._authority, "result": result}
    while len(provider._results) > 32:
        provider._results.popitem(last=False)
    return result
