"""Conservative disclosed estimate until exact compatible-token accounting is validated.

UTF-8 byte count is deliberately conservative and preserves a byte ceiling; it is
not advertised as measured Gemma tokenizer output. Provider usage is recorded too.
"""
from __future__ import annotations
import json
from typing import Any


def serialized(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def estimate(value: Any) -> int:
    return len((value if isinstance(value, str) else serialized(value)).encode("utf-8"))


def select(items: list[Any], cap: int) -> tuple[list[Any], int]:
    selected = []
    for item in items:
        if estimate(selected + [item]) <= cap:
            selected.append(item)
    return selected, len(items) - len(selected)


def make_pack(*, private_facts: list[dict], shared_facts: list[dict], summary: str,
              recent: list[dict], episodes: list[dict], private_revision: int,
              knowledge_revision: int, private_selected: list[dict] | None = None, byte_scale=1) -> dict:
    # Always-visible compact representation plus exact query-specific details.
    private_index = {"revision": private_revision, "count": len(private_facts), "manifest": "private-canonical"}
    private_core, omitted_core = select(private_facts, 490 * byte_scale)
    core_ids = {x["id"] for x in private_core}
    private_detail, omitted_private = select([x for x in (private_selected or private_facts) if x["id"] not in core_ids] + episodes, 390 * byte_scale)
    shared_header = {"revision": knowledge_revision, "count": len(shared_facts),
                     "manifest": "shared-canonical", "private_revision": private_revision}
    shared_detail, omitted_shared = select(shared_facts, 790 * byte_scale)
    long_term = {"private_index": private_index, "private_capsule": private_core, "private_detail": private_detail,
                 "shared_index": shared_header, "shared_detail": shared_detail}
    # Account container/schema metadata too; remove optional detail if necessary.
    while estimate(long_term) > 2000 * byte_scale and (private_detail or shared_detail):
        if shared_detail:
            shared_detail.pop(); omitted_shared += 1
        elif private_detail:
            private_detail.pop(); omitted_private += 1
    while estimate(long_term) > 2000 * byte_scale and private_core:
        private_core.pop(); omitted_core += 1
    summary_text = summary
    while estimate(summary_text) > 390 * byte_scale:
        summary_text = summary_text.rsplit(" ", 1)[0] if " " in summary_text else ""
    tail, omitted_tail = select(list(reversed(recent)), 480 * byte_scale)
    tail.reverse()
    refs, omitted_refs = select([{"id": e["id"]} for e in episodes], 80 * byte_scale)
    short_term = {"summary": summary_text, "dialogue": tail, "references": refs}
    while estimate(short_term) > 1000 * byte_scale and tail:
        tail.pop(0); omitted_tail += 1
    return {"long_term": long_term, "short_term": short_term,
            "accounting": {"method": "conservative_utf8_bytes_not_exact_tokens",
              "long_term": estimate(long_term), "long_term_cap": 2000, "long_term_byte_cap": 2000 * byte_scale,
              "short_term": estimate(short_term), "short_term_cap": 1000,
              "omitted_private": omitted_core + omitted_private,
              "omitted_shared": omitted_shared, "omitted_dialogue": omitted_tail,
              "omitted_reference_handles": omitted_refs}}


def pack_evidence(results: dict, evidence: dict, receipts=None, warnings=None, reference_date=None, byte_cap=2000) -> tuple[dict, dict]:
    """Balanced candidate pack; the caller subsequently enforces measured token caps.

    Keep result scope and canonical row indexes even when previews are shortened.
    Source excerpts are whole spans; omitted text never becomes an asserted cause.
    """
    def candidates(result):
        indexed = list(enumerate(result.get("rows", [])))
        metric = (result.get("operation") or {}).get("metric")
        if metric == "repair_candidates":
            fields = {"rank", "asset_id", "area_name", "latest_note_at", "latest_note_quote", "other_warning_signs", "last_repair_id", "last_repair_at", "producing", "priority_score", "warning_note_count"}
        elif metric in {"gas_response", "bypass_intervals", "recall_inventory", "letter_compliance", "freeze_checks", "wait_reasons", "temperature_profile"}:
            fields = None
        elif indexed and "note_id" in indexed[0][1]:
            indexed = [(i, r) for i, r in indexed if not reference_date or not r.get("valid_to") or reference_date < r["valid_to"]]
            indexed.sort(key=lambda pair: str(pair[1].get("created_at", "")), reverse=True)
            fields = {"note_id", "asset_id", "author_user_id", "author_name", "created_at", "text", "note_type", "valid_from", "valid_to"}
        elif indexed and "completion_state" in indexed[0][1]:
            # Completed work can explain historical downtime. Never silently discard it.
            fields = {"maintenance_id", "asset_id", "equipment_kind", "started_at", "completed_at", "completion_state", "report_source_id", "report_file", "triggered_by_inspection_id", "issue", "action_taken", "cost_usd"}
        elif indexed and "protocol_id" in indexed[0][1]:
            fields = {"asset_id", "inspection_id", "discovered_at", "spill_volume_bbl", "protocol_id", "duty", "assessment", "due_date", "due_at", "observed_hours", "limit_hours", "fine_usd", "detail"}
        elif indexed and "producing" in indexed[0][1] and metric != "temperature_series":
            fields = {"asset_id", "area_name", "well_type", "inspection_id", "inspected_at", "inspector_name", "method", "producing", "wellhead_temp_c", "ambient_temp_c", "delta_c", "threshold_c", "notes", "recorded_status", "lat", "lon"}
        elif metric == "temperature_series":
            fields = {"asset_id", "inspection_id", "inspected_at", "wellhead_temp_c", "ambient_temp_c", "delta_c", "threshold_c", "producing"}
        else:
            fields = None
        maximum = 16 if metric in {"temperature_series", "compliance"} else 10
        return [(i, {k: v for k, v in row.items() if fields is None or k in fields}) for i, row in indexed[:maximum]]

    catalog = [{"id": r["result_set_id"], "columns": [c["key"] for c in r.get("columns", [])],
                "evidence_ids": r.get("evidence_ids", [])[:3]} for r in results.values()]
    catalog, omitted_catalog = select(catalog, int(byte_cap * .35))
    pack = {"result_catalog": catalog, "results": [], "evidence": []}
    admitted = {c["id"] for c in catalog}
    previews = {}
    for result in results.values():
        rid = result["result_set_id"]
        if rid not in admitted:
            continue
        item = {"id": rid, "rows": [], "row_indices": [], "row_count": len(result.get("rows", [])),
                "coverage": result.get("coverage"), "bounds": result.get("bounds")}
        if estimate({**pack, "results": pack["results"] + [item]}) <= byte_cap * .70:
            pack["results"].append(item)
            previews[rid] = candidates(result)
            for key in ("summary", "assessment_counts"):
                if result.get(key) is not None:
                    item[key] = result[key]
    # Round-robin admission gives each result a chance before a large fleet preview
    # consumes the budget. Small compliance sets keep every available duty first.
    priority = sorted(pack["results"], key=lambda item: not any("protocol_id" in row for _, row in previews[item["id"]]))
    for turn in range(16):
        for item in priority:
            choices = previews[item["id"]]
            if turn >= len(choices):
                continue
            index, row = choices[turn]
            item["rows"].append(row); item["row_indices"].append(index)
            if estimate(pack) > byte_cap * .70:
                item["rows"].pop(); item["row_indices"].pop()
    omitted_rows = sum(len(r.get("rows", [])) for r in results.values()) - sum(len(r["rows"]) for r in pack["results"])
    receipt_refs, omitted_receipts = select([{"id": r["id"], "scope": r["scope"], "status": r["status"]} for r in receipts or []], int(byte_cap * .08))
    if receipt_refs and estimate({**pack, "save_receipts": receipt_refs}) <= byte_cap * .8:
        pack["save_receipts"] = receipt_refs
    else:
        omitted_receipts += len(receipt_refs)
    omitted_sources = 0
    sources = [s for s in evidence.values() if s.get("source_kind") not in {"shared_knowledge", "private_memory"}]
    def rank(source):
        kind = source.get("source_kind", "")
        return 0 if kind in {"manual", "sop", "report"} else 1
    for source in sorted(sources, key=rank):
        item = {"id": source["id"], "title": source.get("title", ""), "excerpt": source.get("excerpt", "")}
        if source.get("asset_id"):
            item["asset_id"] = source["asset_id"]
        referenced = any(source["id"] in r.get("evidence_ids", []) for r in results.values())
        if referenced and str(item["excerpt"]).lstrip().startswith("{"):
            item = {"id": source["id"], "title": source.get("title", ""), "note": "Original record citation; effective values are in results"}
        if estimate({**pack, "evidence": pack["evidence"] + [item]}) <= byte_cap:
            pack["evidence"].append(item)
        else:
            omitted_sources += 1
    warning_refs, omitted_warnings = select(warnings or [], int(byte_cap * .04))
    if warning_refs and estimate({**pack, "warnings": warning_refs}) <= byte_cap:
        pack["warnings"] = warning_refs
    else:
        omitted_warnings += len(warning_refs)
    omitted = omitted_catalog + omitted_receipts + omitted_rows + omitted_sources + omitted_warnings
    return pack, {"retrieved_context": estimate(pack), "retrieved_cap": 2000,
                  "candidate_byte_cap": byte_cap, "omitted_evidence_or_rows": omitted,
                  "partial_evidence": omitted > 0, "method": "conservative_utf8_bytes_not_exact_tokens"}


def attach_reference(pack, reference):
    """Exact private reference facts must not be hidden outside the memory cap."""
    long_term = pack["long_term"]
    reference_item = {k: v for k, v in reference.items() if k in {"status", "source_receipt", "entity_ids", "event_ids", "intent"}}
    while estimate(reference_item) > 400 and reference_item.get("intent"):
        words = reference_item["intent"].split()
        reference_item["intent"] = " ".join(words[:-1])
    if estimate(reference_item) > 400:
        reference_item = {"status": reference.get("status"), "source_receipt": reference.get("source_receipt"), "details": "server_side_only"}
    long_term["reference_resolution"] = reference_item
    byte_limit = pack["accounting"].get("long_term_byte_cap", 2000)
    for key in ("private_detail", "shared_detail", "private_capsule"):
        while estimate(long_term) > byte_limit and long_term.get(key):
            long_term[key].pop()
    pack["accounting"]["long_term"] = estimate(long_term)
    if pack["accounting"]["long_term"] > byte_limit:
        raise ValueError("Required reference metadata exceeds long-term budget")
    return pack
