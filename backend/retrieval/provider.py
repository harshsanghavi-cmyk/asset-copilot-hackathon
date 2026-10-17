"""Provisional SQLite/FTS candidate behind a replaceable public provider interface.

No arbitrary SQL, model/provider requests or canonical-memory writes are exposed.
"""
from __future__ import annotations

import collections
import calendar
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import threading
import time
import uuid

from ..ingestion import build_index
from ..ingestion.loader import scaled, uid
from ..ingestion.schema import MAPPINGS, RELATIONS, PARSER_VERSION, SCHEMA_VERSION
from .contracts import AuthoritySnapshot, RetrievalError
from .temporal import AssetTimeline
from .final_operations import DESCRIPTIONS as OPERATION_DESCRIPTIONS

TABLES = ("assets", "areas", "teams", "users", "equipment", "inspections", "maintenance", "regulatory_events", "context_notes", "baseline_corrections", "sources", "chunks", "facts", "rules", "issues")
COLLECTIONS = ("assets", "inspections", "maintenance", "regulatory_events", "context_notes", "areas", "teams", "users")
METRICS = ("records", "status", "temperature_series", "spills", "downtime_days", "spill_count", "spill_volume_bbl", "maintenance_cost_usd", "corrective_count", "rca", "containment", "compliance", "count")
METRIC_DESCRIPTIONS = {
    "records": "Rows from the requested public collection, with effective inspection fields and source handles; pagination limits presentation only.",
    "count": "Count records in the requested collection (assets means wells, not inspections); optional compatible group dimensions.",
    "status": "Latest observed effective thermal status per asset at reference date; includes readings, delta, threshold, inspector, timestamp, recorded_status and coordinates. Claims do not change readings.",
    "temperature_series": "Observed inspection temperatures, delta and producing mask over explicit date window; no invented/interpolated missed observations.",
    "spills": "Effective real spill inspection rows after formal detection corrections, with volume, timestamp and coordinates; not a document search.",
    "downtime_days": "Seven days per observed effective non-producing inspection in period; never maintenance hours. Default asset grouping.",
    "spill_count": "Count effective spill events over full matching population; area+month grouping includes complete-domain zero cells when import has no issues.",
    "spill_volume_bbl": "Exact scaled volume sum of effective spills; missing required volumes make coverage partial.",
    "maintenance_cost_usd": "Recorded job cost by started_at; includes source estimates for work in progress, not asserted paid expenditure.",
    "corrective_count": "Count corrective jobs by equipment and start date; default preceding12months when no explicit start.",
    "rca": "Corrective counts, applicable manual/user threshold and rca_required per asset/equipment. Pass equipment_kind filter or include equipment_kind grouping; type overrides remain attributed.",
    "containment": "All effective spill incidents with report-only elapsed containment hours; no repair-duration substitution. only_breaches=true returns delays>supplied4h while coverage counts all candidates.",
    "compliance": "Deterministic incident duties/deadlines from supplied SOP rows and effective volumes: SR01writtennotice,SR02containment,SR03passingagencyverification,RC04NOVresponse. Returns due_date/due_at, assessment, observed/limit hours, fine and sources; missing-record breaches remain possible, not proven real-world inaction. Not an exhaustive WS/safety audit. RCA/planned-shutdown context is queried separately.",
}

METRICS += tuple(OPERATION_DESCRIPTIONS)
METRIC_DESCRIPTIONS.update(OPERATION_DESCRIPTIONS)

IDS = {"assets": "asset_id", "inspections": "inspection_id", "maintenance": "maintenance_id", "regulatory_events": "event_id", "context_notes": "note_id", "areas": "area_id", "teams": "team_id", "users": "user_id"}
SYNONYMS = {"procedure": ["sop", "protocol"], "confine": ["contain", "contained"], "containment": ["contained"], "specimens": ["samples"], "discharge": ["spill"], "petroleum": ["crude"], "investigation": ["analysis"]}
STOP = set("a an the what which how when was were is are to of and or on in at from for by about with it this that asset well did we followed".split())


def _page(limit=25, offset=0):
    try:
        limit, offset = int(limit), int(offset)
    except (TypeError, ValueError):
        raise RetrievalError("invalid_arguments", "Pagination must be integers")
    if not 1 <= limit <= 100 or not 0 <= offset <= 1000000:
        raise RetrievalError("query_limit", "limit must be 1–100 and offset 0–1000000")
    return limit, offset


def _json(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def _end_day(value):
    try:
        return (dt.date.fromisoformat(str(value)[:10]) + dt.timedelta(days=1)).isoformat()
    except ValueError:
        raise RetrievalError("invalid_date", "Expected ISO calendar date")


class SQLiteRetrievalProvider:
    provider_id = "sqlite-fts-provisional-v1"

    def __init__(self, db_path: Path, *, namespace="asset-field", gemma_enricher=None):
        self.db_path = Path(db_path).resolve()
        self.namespace = namespace
        self._db = sqlite3.connect(self.db_path.as_uri() + "?mode=ro", uri=True, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA query_only=ON")
        self._db.enable_load_extension(False)
        self._lock = threading.RLock()
        self._manifest = {r[0]: json.loads(r[1]) for r in self._db.execute("SELECT key,value_json FROM manifest")}
        self.namespace = self._manifest["namespace"]
        self._sources = {r["id"]: dict(r) for r in self._db.execute("SELECT id,path,kind,asset_id,content_hash,byte_count FROM sources")}
        self._baseline = { (r["record_id"], r["field"]): dict(r, value=json.loads(r["value_json"])) for r in self._db.execute("SELECT * FROM baseline_corrections") }
        self._rules = {r["well_type"]: dict(r) for r in self._db.execute("SELECT * FROM rules WHERE predicate='production_delta_c'")}
        metadata = {r["id"]: json.loads(r["raw_json"]) for r in self._db.execute("SELECT id,raw_json FROM records WHERE collection='assets'")}
        operations_source, operations_effective = None, None
        for source in self._db.execute("SELECT id,preview FROM sources WHERE kind='sop'"):
            if re.search(r"^## OPS-3\b", source["preview"], re.M):
                operations_source = source["id"]
                effective = re.search(r"Effective (\d{1,2} [A-Za-z]+ \d{4})", source["preview"])
                if effective:
                    operations_effective = dt.datetime.strptime(effective[1], "%d %b %Y").date().isoformat()
        operator_notes = [dict(r) for r in self._db.execute("SELECT * FROM context_notes WHERE note_type='operator_note'")]
        self._timeline = AssetTimeline(metadata, operator_notes, operations_source, operations_effective)
        self._team_names = {r["team_id"]: r["name"] for r in self._db.execute("SELECT team_id,name FROM teams")}
        self._trace = collections.OrderedDict()
        self._results = collections.OrderedDict()
        self._authority = AuthoritySnapshot()
        self._gemma_enricher = gemma_enricher
        self._db.create_function("effective_value", 3, self._effective)
        self._db.create_function("production_threshold", 1, self._threshold)
        self._db.create_function("asset_type_at", 2, lambda asset, at: self._timeline.at(asset, "well_type", at))
        self._db.create_function("asset_team_at", 2, lambda asset, at: self._timeline.at(asset, "team_id", at))
        self._db.create_function("current_producing", 4, lambda asset, inspected, value, reference:
                                 self._timeline.status(asset, inspected, value, reference)["producing"])
        self._db.create_function("status_disagrees", 4, lambda asset, inspected, value, reference:
                                 self._timeline.status(asset, inspected, value, reference)["status_note_disagrees"])
        self._db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 65536)
        self._db.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 1024)
        self._db.execute("SELECT rowid FROM chunk_fts LIMIT 0").fetchall()
        schema_tables = tuple(dict.fromkeys(TABLES + ("records", "record_origins", "evidence_map", "chunk_fts")))
        self._schemas = {table: [dict(row) for row in self._db.execute("PRAGMA table_info(" + table + ")")] for table in schema_tables}
        self._db.set_authorizer(self._authorize)

    def _authorize(self, action, first, second, dbname, trigger):
        denied = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_PRAGMA}
        if action == sqlite3.SQLITE_PRAGMA and first == "data_version" and second is None:
            return sqlite3.SQLITE_OK
        if action in denied:
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_READ and first not in TABLES + ("records", "record_origins", "evidence_map", "equipment", "manifest", "sqlite_master") and not str(first).startswith("chunk_fts"):
            return sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_FUNCTION and str(second or first).lower() not in {"count", "sum", "min", "max", "coalesce", "substr", "lower", "row_number", "effective_value", "production_threshold", "asset_type_at", "asset_team_at", "current_producing", "status_disagrees", "match", "bm25", "snippet", "like", "length", "json_extract"}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def _scope(self, context):
        if not isinstance(context, dict):
            raise RetrievalError("invalid_scope", "Trusted context is required")
        namespace = context.get("dataset_namespace", self.namespace)
        if namespace != self.namespace:
            raise RetrievalError("invalid_scope", "Dataset namespace does not match this provider")
        _end_day(context.get("reference_date", "2026-10-16"))

    def _snapshot(self, authority):
        if authority is None:
            return AuthoritySnapshot()
        if isinstance(authority, AuthoritySnapshot):
            return authority
        if isinstance(authority, dict):
            return AuthoritySnapshot(knowledge_revision=int(authority.get("knowledge_revision", 0)), corrections=list(authority.get("corrections", [])), rule_overrides=list(authority.get("rule_overrides", [])), shared_claims=list(authority.get("shared_claims", [])))
        raise RetrievalError("invalid_authority", "Expected canonical structured authority snapshot")

    def _corrections(self):
        result = dict(self._baseline)
        for c in self._authority.corrections:
            if c.get("status", "accepted") not in ("accepted", "active", "committed"):
                continue
            record = c.get("record_id") or c.get("inspection_id") or c.get("target_id")
            field = c.get("field") or c.get("field_name")
            value = next((c[k] for k in ("value", "new_value", "effective_value") if c.get(k) is not None), None)
            if record and field in ("wellhead_temp_c", "ambient_temp_c", "spill_detected", "spill_est_volume_bbl"):
                result[(record, field)] = dict(c, value=value)
        return result

    def _effective(self, record, field, raw):
        correction = self._active_corrections.get((record, field))
        if correction is None:
            return raw
        value = correction["value"]
        if field == "spill_detected":
            if not isinstance(value, bool):
                raise ValueError("spill correction must be boolean")
            return int(value)
        return scaled(value)

    def _threshold(self, well_type):
        value = self._rules.get(well_type, {}).get("value_milli")
        for r in self._authority.rule_overrides:
            scope = r.get("scope", {})
            if (r.get("well_type") or scope.get("well_type") or r.get("subject_id")) == well_type and r.get("predicate") in ("production_delta_c", "production_threshold_c") and r.get("status", "active") in ("active", "accepted", "committed"):
                value = scaled(r.get("value", r.get("threshold")))
        return value

    def _run(self, sql, params=(), *, deadline=2.0):
        began = time.monotonic()
        ticks = 0
        def progress():
            nonlocal ticks
            ticks += 1
            return int(ticks > 20000 or time.monotonic() - began > deadline)
        self._db.set_progress_handler(progress, 1000)
        try:
            return [dict(r) for r in self._db.execute(sql, params)]
        except sqlite3.Error as error:
            code = "resource_limit" if "interrupted" in str(error).lower() else "query_error"
            raise RetrievalError(code, "Read query failed or exceeded its bounded execution budget") from error
        finally:
            self._db.set_progress_handler(None, 0)

    def catalog(self):
        with self._lock:
            return {"provider_id": self.provider_id, "replaceable": True, "selection_status": "provisional; awaiting user review", "dataset_namespace": self.namespace, "dataset_revision": self._manifest["dataset_revision"], "collections": list(COLLECTIONS), "users": self._run("SELECT user_id,name,role,team_id FROM users ORDER BY name"), "metrics": list(METRICS), "metric_descriptions": METRIC_DESCRIPTIONS, "group_by": ["asset_id", "area_id", "team_id", "month", "well_type", "equipment_kind"], "filters": ["asset_id", "asset_ids", "area_id", "team_id", "well_type", "equipment_kind", "maintenance_type", "spill_detected", "producing", "status_note_disagrees", "inspection_id"], "query_schema": {"collection": "enum collections", "metric": "enum metrics", "filters": "object using catalog filters; literal values only", "group_by": "up to 2 catalog dimensions", "start": "optional ISO date inclusive", "end": "optional ISO date inclusive", "limit": "1..100 presentation rows only"}, "query_examples": [{"collection": "assets", "metric": "status", "filters": {"producing": False}, "limit": 25}, {"collection": "inspections", "metric": "spill_count", "group_by": ["area_id", "month"], "start": "2026-01-01", "end": "2026-10-16"}, {"collection": "maintenance", "metric": "maintenance_cost_usd", "group_by": ["asset_id"], "start": "2026-01-01"}, {"collection": "inspections", "metric": "compliance", "start": "2025-10-16", "only_breaches": True, "limit": 50}], "limits": {"page_size": 100, "search_terms": 12, "search_candidates": 16, "evidence_content_budget": 2000, "statement_deadline_seconds": 2}, "model_enrichment": {"configured": self._gemma_enricher is not None, "status": "not_run", "allowed_model": "Gemini 3.5 Flash Lite via Google AI Studio; verified model ID owned by backend"}}

    def overview(self):
        with self._lock:
            counts = {table: self._run(f"SELECT count(*) n FROM {table}")[0]["n"] for table in TABLES}
            schemas = {"assets": ["asset_id", "well_type", "area_id", "recorded_status", "lat", "lon"], "inspections": ["inspection_id", "asset_id", "inspected_at", "ambient_milli", "wellhead_milli", "spill_detected", "volume_milli"], "maintenance": ["maintenance_id", "asset_id", "started_at", "completed_at", "cost_cents", "inspection_id", "report_source_id"], "records": ["id", "collection", "source_id", "line", "raw_json", "content_hash"], "chunks": ["id", "source_id", "section", "byte_start", "byte_end", "text", "method", "version", "status"], "facts": ["subject_id", "predicate", "value_json", "source_id", "byte_start", "byte_end", "method", "status"]}
            return {**self.catalog(), "manifest": self._manifest, "counts": counts, "mappings": MAPPINGS, "relations": RELATIONS, "schemas": self._schemas, "storage": [{"store": "Original dataset", "purpose": "Immutable filesystem files, never rewritten", "contains": "JSON / JSONL / Markdown originals"}, {"store": "SQLite candidate index", "purpose": "Replaceable derived projection; rebuild from all supplied roots", "contains": "Normalized records, source registry, chunks, facts, rules, FTS"}, {"store": "Canonical memory authority (backend owner)", "purpose": "External boundary, not this adapter's database", "contains": "Private/shared facts, accepted runtime corrections and type rules"}, {"store": "Bounded trace/result registry", "purpose": "Diagnostic runtime state; maximum 100 traces / 32 result handles", "contains": "Redacted execution, scope, coverage and evidence selection"}]}

    def sources(self, *, kind=None, asset_id=None, q=None, limit=25, offset=0):
        limit, offset = _page(limit, offset)
        clauses, params = [], []
        for field, value in (("kind", kind), ("asset_id", asset_id)):
            if value:
                clauses.append(field + "=?"); params.append(value)
        if q:
            if len(q) > 100:
                raise RetrievalError("query_limit", "Source search exceeds 100 characters")
            clauses.append("path LIKE ?"); params.append("%" + q + "%")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._lock:
            total = self._run("SELECT count(*) n FROM sources" + where, params)[0]["n"]
            rows = self._run("SELECT id,path,kind,asset_id,byte_count,record_count,status,content_hash,enrichment_method,enrichment_version,enrichment_status FROM sources" + where + " ORDER BY path LIMIT ? OFFSET ?", [*params, limit, offset])
            return {"items": rows, "total": total, "limit": limit, "offset": offset}

    def source(self, source_id):
        with self._lock:
            found = self._run("SELECT * FROM sources WHERE id=?", (source_id,))
            if not found:
                raise RetrievalError("not_found", "Unknown registered source")
            source = found[0]
            source["preview_truncated"] = source["byte_count"] > len(source["preview"].encode())
            source["preview_byte_limit"] = 8192
            source["parsed_collections"] = self._run("SELECT collection,count(*) count FROM records WHERE source_id=? GROUP BY collection", (source_id,))
            source["chunk_count"] = self._run("SELECT count(*) n FROM chunks WHERE source_id=?", (source_id,))[0]["n"]
            source["fact_count"] = self._run("SELECT count(*) n FROM facts WHERE source_id=?", (source_id,))[0]["n"]
            return source

    def records(self, collection, *, asset_id=None, source_id=None, limit=25, offset=0, authority=None):
        if collection not in COLLECTIONS:
            raise RetrievalError("invalid_collection", "Unknown public record collection")
        limit, offset = _page(limit, offset)
        clauses, params = ["collection=?"], [collection]
        if source_id:
            clauses.append("source_id=?"); params.append(source_id)
        if asset_id:
            if collection in ("assets", "inspections", "maintenance", "regulatory_events", "context_notes"):
                clauses.append("id IN (SELECT " + IDS[collection] + " FROM " + collection + " WHERE asset_id=?)"); params.append(asset_id)
        with self._lock:
            self._authority = self._snapshot(authority)
            self._active_corrections = self._corrections()
            total = self._run("SELECT count(*) n FROM records WHERE " + " AND ".join(clauses), params)[0]["n"]
            rows = self._run("SELECT id,collection,source_id,line,content_hash,raw_json FROM records WHERE " + " AND ".join(clauses) + " ORDER BY id LIMIT ? OFFSET ?", [*params, limit, offset])
            for row in rows:
                raw = json.loads(row.pop("raw_json")); effective = dict(raw); changes = []
                for (rid, field), correction in self._active_corrections.items():
                    if rid == row["id"]:
                        effective[field] = correction["value"]
                        changes.append({"field": field, "original": raw.get(field), "effective": correction["value"], "provenance": correction})
                row.update(original=raw, effective=effective, corrections=changes, evidence_ref=uid("ev_", row["id"]))
            return {"items": rows, "total": total, "limit": limit, "offset": offset, "knowledge_revision": self._authority.knowledge_revision}

    def chunks(self, *, source_id=None, limit=25, offset=0):
        limit, offset = _page(limit, offset)
        clause, params = (" WHERE c.source_id=?", [source_id]) if source_id else ("", [])
        with self._lock:
            total = self._run("SELECT count(*) n FROM chunks c" + clause, params)[0]["n"]
            rows = self._run("SELECT c.id,c.source_id,s.path,c.section,c.byte_start,c.byte_end,substr(c.text,1,320) preview,c.protocols_json,c.entities_json,c.method,c.version,c.status FROM chunks c JOIN sources s ON s.id=c.source_id" + clause + " ORDER BY s.path,c.ordinal LIMIT ? OFFSET ?", [*params, limit, offset])
            return {"items": rows, "total": total, "limit": limit, "offset": offset}

    def enrichments(self, *, source_id=None, limit=25, offset=0):
        limit, offset = _page(limit, offset)
        clause, params = (" WHERE f.source_id=?", [source_id]) if source_id else ("", [])
        with self._lock:
            total = self._run("SELECT count(*) n FROM facts f" + clause, params)[0]["n"]
            rows = self._run("SELECT f.*,s.path FROM facts f JOIN sources s ON s.id=f.source_id" + clause + " ORDER BY s.path,f.byte_start LIMIT ? OFFSET ?", [*params, limit, offset])
            for row in rows:
                row["value"] = json.loads(row.pop("value_json"))
            return {"items": rows, "total": total, "limit": limit, "offset": offset, "model_enrichment": self.catalog()["model_enrichment"], "note": "Deterministic source assertions, not independent field verification. Repeated narrative/table facts retain both spans."}

    def issues(self, limit=25, offset=0):
        limit, offset = _page(limit, offset)
        with self._lock:
            return {"items": self._run("SELECT * FROM issues ORDER BY id LIMIT ? OFFSET ?", (limit, offset)), "total": self._run("SELECT count(*) n FROM issues")[0]["n"], "limit": limit, "offset": offset}

    def evidence(self, handle, context):
        self._scope(context)
        with self._lock:
            if handle.startswith("result_"):
                saved = self._load_manifest(handle, context)
                members = self.members(handle, context, 20, 0)
                return {"evidence_id": handle, "source_kind": "aggregate_lineage", "dataset_revision": saved["dataset_revision"], "knowledge_revision": saved["authority"]["knowledge_revision"], "plan": saved["plan"], "coverage": saved["coverage"], "members": members, "note": "Complete calculation population is available through paginated member records; this preview is bounded"}
            if handle.startswith("ev_"):
                # IDs are opaque to callers; resolve using registered source records.
                found = self._run("SELECT r.id,r.source_id,r.line,r.raw_json FROM evidence_map e JOIN records r ON r.id=e.record_id WHERE e.handle=?", (handle,))
                record = found[0] if found else None
                if record is None:
                    raise RetrievalError("not_found", "Unknown evidence handle")
                src = self._sources[record["source_id"]]
                return {"evidence_id": handle, "source_id": record["source_id"], "record_id": record["id"], "line": record["line"], "path": src["path"], "content_hash": src["content_hash"], "source_kind": src["kind"], "dataset_revision": self._manifest["dataset_revision"], "original": json.loads(record["raw_json"]), "interpretation": "Original source record; effective corrections are supplied separately"}
            rows = self._run("SELECT c.*,s.path,s.kind,s.content_hash FROM chunks c JOIN sources s ON s.id=c.source_id WHERE c.id=?", (handle,))
            if rows:
                r = rows[0]
                return {**r, "evidence_id": r["id"], "dataset_revision": self._manifest["dataset_revision"], "span_verified": True, "interpretation": "Original document assertion, not proof of compliance"}
            rows = self._run("SELECT f.*,s.path,s.content_hash FROM facts f JOIN sources s ON s.id=f.source_id WHERE f.id=?", (handle,))
            if rows:
                r = rows[0]; r["value"] = json.loads(r.pop("value_json"))
                return {**r, "evidence_id": handle, "dataset_revision": self._manifest["dataset_revision"], "interpretation": "Deterministically extracted source assertion"}
            if handle in self._sources:
                return self.source(handle)
            raise RetrievalError("not_found", "Unknown registered evidence handle")

    def _persist_manifest(self, handle, plan, context, authority, result):
        directory = self.db_path.parent / "manifests"
        directory.mkdir(exist_ok=True)
        clean_plan = {k: v for k, v in plan.items() if k != "input_text"}
        payload = {"dataset_revision": self._manifest["dataset_revision"], "plan": clean_plan, "context": {k: context[k] for k in ("dataset_namespace", "user_id", "reference_date", "minimum_knowledge_revision") if k in context}, "authority": authority.to_dict(), "coverage": result["coverage"]}
        path = directory / (handle + ".json")
        path.write_text(_json(payload))

    def _load_manifest(self, handle, context):
        if not re.fullmatch(r"result_[a-f0-9]{32}", handle):
            raise RetrievalError("not_found", "Unknown result handle")
        path = self.db_path.parent / "manifests" / (handle + ".json")
        if not path.is_file() or path.stat().st_size > 1048576:
            raise RetrievalError("not_found", "Result manifest is unavailable")
        saved = json.loads(path.read_text())
        if saved["dataset_revision"] != self._manifest["dataset_revision"]:
            raise RetrievalError("stale_revision", "Index changed; source revision for this manifest is unavailable")
        owner = saved["context"].get("user_id")
        if owner and owner != context.get("user_id") and not context.get("is_admin"):
            raise RetrievalError("invalid_scope", "Result handle belongs to another requesting user")
        return saved

    def members(self, handle, context, limit=25, offset=0):
        self._scope(context)
        limit, offset = _page(limit, offset)
        with self._lock:
            saved = self._load_manifest(handle, context)
            plan = dict(saved["plan"])
            old_metric = plan.get("metric", "records")
            if old_metric in OPERATION_DESCRIPTIONS:
                plan.update(limit=limit, offset=offset)
                return self.query(plan, saved["context"], saved["authority"])
            plan.update(metric="status" if old_metric == "status" else "records", group_by=[], limit=limit, offset=offset)
            plan.pop("only_breaches", None)
            plan["collection"] = "maintenance" if old_metric in ("maintenance_cost_usd", "corrective_count", "rca") else "assets" if old_metric == "status" else plan.get("collection", "inspections") if old_metric in ("records", "count") else "inspections"
            if old_metric in ("spills", "spill_count", "spill_volume_bbl", "containment", "compliance"):
                filters = dict(plan.get("filters", {})); filters["spill_detected"] = True; plan["filters"] = filters
            if old_metric in ("corrective_count", "rca"):
                filters = dict(plan.get("filters", {})); filters["maintenance_type"] = "corrective"; plan["filters"] = filters
            return self.query(plan, saved["context"], saved["authority"])

    def search(self, terms, context, *, asset_id=None, kind=None, limit=8, offset=0, budget=2000):
        self._scope(context)
        limit, offset = _page(limit, offset)
        if limit > 16 or not 1 <= int(budget) <= 2000:
            raise RetrievalError("query_limit", "At most 16 candidates and 2000 retrieved-content units")
        original = terms if isinstance(terms, str) else " ".join(terms)
        if len(original) > 512:
            raise RetrievalError("query_limit", "Search text exceeds bounded length")
        words = [x for x in re.findall(r"[a-zA-Z0-9_-]{2,64}", original.lower()) if x not in STOP][:12]
        expanded = set(words)
        for word in words:
            expanded.update(SYNONYMS.get(word, []))
        if not expanded:
            raise RetrievalError("invalid_arguments", "Supply searchable text or a registered evidence handle")
        expr = " OR ".join('"' + word.replace('"', '""') + '"' for word in sorted(expanded))
        clauses, params = ["chunk_fts MATCH ?"], [expr]
        if asset_id:
            clauses.append("s.asset_id=?"); params.append(asset_id)
        if kind:
            if kind not in ("manual", "sop", "report"):
                raise RetrievalError("invalid_arguments", "Invalid document kind")
            clauses.append("s.kind=?"); params.append(kind)
        sql = "SELECT c.id,c.source_id,s.path,s.kind,s.asset_id,c.section,c.byte_start,c.byte_end,c.text,bm25(chunk_fts,0,2,1) score FROM chunk_fts JOIN chunks c ON c.id=chunk_fts.chunk_id JOIN sources s ON s.id=c.source_id WHERE " + " AND ".join(clauses)
        began = time.perf_counter()
        with self._lock:
            matches = self._run("SELECT count(*) n FROM chunk_fts JOIN chunks c ON c.id=chunk_fts.chunk_id JOIN sources s ON s.id=c.source_id WHERE " + " AND ".join(clauses), params)[0]["n"]
            ranked = self._run(sql + " ORDER BY score,c.id LIMIT ? OFFSET ?", [*params, limit, offset])
            selected, omitted, used = [], [], 0
            for rank, row in enumerate(ranked, 1):
                item = dict(row, rank=rank, evidence_id=row["id"], dataset_revision=self._manifest["dataset_revision"], excerpt=row["text"][:800], claim_status="source_asserted", effective_correction_check="not_assessed_by_lexical_match")
                estimate = len((row["section"] + row["text"]).encode())
                if used + estimate <= int(budget):
                    selected.append(item); used += estimate
                else:
                    omitted.append({"evidence_id": row["id"], "reason": "content_budget", "estimated_units": estimate})
            coverage = {"unit": "lexical_matching_chunk", "matching": matches, "evaluated": len(ranked), "selected": len(selected), "omitted_from_candidates": len(omitted), "status": "ranked_subset", "exhaustive_factual_scope": False}
            trace = self._save_trace({"operation": "lexical_search", "input_text": original, "expanded_terms": sorted(expanded), "enrichment": "deterministic synonyms; Gemma expansion not run", "tables": ["chunk_fts", "chunks", "sources"], "safe_sql": sql + " ORDER BY score,c.id LIMIT ? OFFSET ?", "parameters": ["<redacted>" for _ in params] + [limit, offset], "ranked_passages": [{k: r[k] for k in ("id", "path", "section", "score")} for r in ranked], "selected_evidence": [r["id"] for r in selected], "omitted_evidence": omitted, "coverage": coverage, "tokens": {"method": "UTF-8 byte estimate; Gemma tokenizer not verified here", "estimated_loaded_units": used, "content_budget": int(budget), "provider_tokens": None}, "elapsed_ms": round((time.perf_counter() - began) * 1000, 3)})
            return {"items": selected, "total": matches, "limit": limit, "offset": offset, "coverage": coverage, "warnings": ["Ranked lexical retrieval cannot prove a fleet total or source absence", "Report prose may predate corrections; a lexical hit does not confirm effective spill detection or current classification"], "omitted_evidence": omitted, "trace_id": trace, "token_accounting": self._trace[trace]["tokens"], "dataset_revision": self._manifest["dataset_revision"], "knowledge_revision": int(context.get("knowledge_revision", 0))}

    def _save_trace(self, trace):
        tid = "trace_" + uuid.uuid4().hex
        trace.update(trace_id=tid, provider_id=self.provider_id, dataset_namespace=self.namespace, dataset_revision=self._manifest["dataset_revision"], created_at=dt.datetime.now(dt.timezone.utc).isoformat())
        self._trace[tid] = trace
        while len(self._trace) > 100:
            self._trace.popitem(last=False)
        return tid

    def traces(self, limit=25, offset=0):
        limit, offset = _page(limit, offset)
        with self._lock:
            rows = list(reversed(self._trace.values()))
            return {"items": [{k: r.get(k) for k in ("trace_id", "operation", "input_text", "created_at", "elapsed_ms", "coverage", "dataset_revision", "knowledge_revision")} for r in rows[offset:offset + limit]], "total": len(rows), "limit": limit, "offset": offset}

    def trace(self, handle):
        with self._lock:
            if handle not in self._trace:
                raise RetrievalError("not_found", "Trace expired or unknown")
            return self._trace[handle]

    def walkthrough(self, asset_id, context, authority=None):
        """Bounded actual source-to-query walkthrough for any registered asset."""
        self._scope(context)
        if not isinstance(asset_id, str) or not 1 <= len(asset_id) <= 128:
            raise RetrievalError("invalid_arguments", "Supply a registered asset ID")
        with self._lock:
            self._authority = self._snapshot(authority)
            self._active_corrections = self._corrections()
            metadata = self._run("SELECT r.id,r.source_id,r.line,r.raw_json,s.path,s.content_hash FROM records r JOIN sources s ON s.id=r.source_id WHERE r.collection='assets' AND r.id=?", (asset_id,))
            if not metadata:
                raise RetrievalError("not_found", "Asset is not in this dataset")
            meta = metadata[0]; original_meta = json.loads(meta.pop("raw_json"))
            status = self.query({"collection": "assets", "metric": "status", "filters": {"asset_id": asset_id}, "limit": 1}, context, authority)
            latest = status["rows"][0] if status["rows"] else {}
            record_id = latest.get("inspection_id")
            original = self.evidence(uid("ev_", record_id), context) if record_id else None
            stored = self._run("SELECT * FROM inspections WHERE inspection_id=?", (record_id,)) if record_id else []
            normalized = []
            for field, column, unit, explanation in [("ambient_temp_c", "ambient_milli", "milli-C", "Decimal ×1000; comparison stays integer-scaled"), ("wellhead_temp_c", "wellhead_milli", "milli-C", "Original reading preserved; accepted correction is an overlay"), ("spill_est_volume_bbl", "volume_milli", "milli-bbl", "Null remains unknown/not supplied, never invented zero"), ("spill_detected", "spill_detected", "boolean as integer", "Formal detection corrections apply in effective query")]:
                normalized.append({"source_field": field, "original_value": original["original"].get(field) if original else None, "stored_field": "inspections." + column, "stored_value": stored[0].get(column) if stored else None, "effective_value": latest.get(field), "unit": unit, "method": explanation})
            correction = None
            existing = self._run("SELECT c.*,i.asset_id FROM baseline_corrections c JOIN inspections i ON i.inspection_id=c.record_id WHERE i.asset_id=? ORDER BY c.created_at DESC LIMIT 1", (asset_id,))
            if existing:
                c = existing[0]; raw = self.evidence(uid("ev_", c["record_id"]), context)
                correction = {"record_id": c["record_id"], "field": c["field"], "original": raw["original"].get(c["field"]), "effective": json.loads(c["value_json"]), "author_user_id": c["author_user_id"], "created_at": c["created_at"], "reason": c["reason"], "correction_id": c["id"], "storage": "baseline_corrections → effective overlay; runtime correction authority is separate"}
            jobs = self._run("SELECT m.maintenance_id,m.inspection_id,m.report_source_id,m.report_path,m.started_at,max(CAST(substr(f.value_json,2,length(f.value_json)-2) AS REAL)) delay FROM maintenance m JOIN facts f ON f.subject_id=m.maintenance_id AND f.predicate='containment_hours' WHERE m.asset_id=? GROUP BY m.maintenance_id ORDER BY delay DESC,m.started_at DESC LIMIT 1", (asset_id,))
            if not jobs:
                jobs = self._run("SELECT maintenance_id,inspection_id,report_source_id,report_path,started_at FROM maintenance WHERE asset_id=? AND report_source_id IS NOT NULL ORDER BY started_at DESC LIMIT 1", (asset_id,))
            report = None; assertion = None; chunk = None; index_row = None
            if jobs:
                job = jobs[0]
                job_record = self.evidence(uid("ev_", job["maintenance_id"]), context)
                src = self.source(job["report_source_id"])
                report = {**job, "original_job": job_record["original"], "declared_report_file": job_record["original"].get("report_file"), "resolved_path": src["path"], "source_id": src["id"], "content_hash": src["content_hash"], "selection": "Highest recorded containment delay for this asset; otherwise latest linked report", "preview": src["preview"][:2400], "preview_truncated": len(src["preview"]) > 2400}
                facts = self._run("SELECT * FROM facts WHERE source_id=? AND predicate='containment_hours' ORDER BY byte_start LIMIT 1", (src["id"],))
                if facts:
                    fact = facts[0]; fact["value"] = json.loads(fact.pop("value_json"))
                    raw = src["preview"].encode()
                    fact["excerpt"] = raw[fact["byte_start"]:fact["byte_end"]].decode() if fact["byte_end"] <= len(raw) else None
                    fact["excerpt_verified_in_preview"] = fact["excerpt"] is not None
                    assertion = fact
                    rows = self._run("SELECT * FROM chunks WHERE source_id=? AND byte_start<=? AND byte_end>=? ORDER BY ordinal LIMIT 1", (src["id"], fact["byte_start"], fact["byte_end"]))
                    if rows:
                        chunk = rows[0]
                if chunk is None:
                    rows = self._run("SELECT * FROM chunks WHERE source_id=? ORDER BY ordinal LIMIT 1", (src["id"],))
                    chunk = rows[0] if rows else None
                if chunk:
                    rows = self._run("SELECT rowid,chunk_id,title,substr(body,1,240) indexed_preview FROM chunk_fts WHERE chunk_id=? LIMIT 1", (chunk["id"],))
                    index_row = dict(rows[0], tokenizer="porter unicode61", ranking="FTS5 BM25; deterministic lexical search") if rows else None
            query_plan = {"collection": "inspections", "metric": "containment" if assertion else "status", "filters": {"asset_id": asset_id}, "limit": 10, "input_text": "Show source-backed containment evidence for " + asset_id if assertion else "Show latest observed status for " + asset_id}
            result = self.query(query_plan, context, authority)
            return {"provider_id": self.provider_id, "selection_status": "Replaceable candidate; not final retrieval selection", "asset_id": asset_id, "dataset_revision": self._manifest["dataset_revision"], "knowledge_revision": self._authority.knowledge_revision, "metadata_source": {**meta, "original_preview": {k: original_meta.get(k) for k in ("asset_id", "name", "well_type", "area_id", "team_id", "location", "recorded_status")}}, "source_files": self.sources(asset_id=asset_id, limit=10)["items"], "latest_inspection_source": original, "field_mapping": normalized, "correction_example": correction, "linked_report": report, "extracted_assertion": assertion, "chunk": chunk, "fts_index_row": index_row, "example_query": query_plan, "result": result, "execution_trace": self.trace(result["trace_id"]), "methods": {"parse": PARSER_VERSION, "enrichment": "deterministic typed fields, source sections and containment regex", "Gemma_enrichment": "not_run; only injected interface exists", "Gemma_query_expansion": "not_run", "runtime_model_policy": "Google AI Studio Gemini 3.5 Flash Lite; backend owns verified model ID; retrieval operations call no model"}, "limits": {"source_files": 10, "report_preview_characters": 2400, "query_rows": 10}, "warnings": (["No linked containment assertion found; this walkthrough cannot invent it"] if assertion is None else [])}

    def query(self, plan, context, authority=None):
        self._scope(context)
        if not isinstance(plan, dict) or len(_json(plan)) > 16384:
            raise RetrievalError("invalid_plan", "Expected bounded typed query plan")
        allowed = {"collection", "metric", "group_by", "filters", "start", "end", "date_from", "date_to", "window", "limit", "offset", "input_text", "equipment_kind", "asset_ids", "area_id", "well_type", "only_breaches"}
        if set(plan) - allowed:
            raise RetrievalError("invalid_plan", "Unknown fields; raw SQL/expressions/scopes are not allowed")
        metric = plan.get("metric", "records")
        collection = plan.get("collection", "maintenance" if metric in ("maintenance_cost_usd", "corrective_count", "rca") else "assets" if metric == "status" else "inspections")
        if metric not in METRICS or collection not in COLLECTIONS:
            raise RetrievalError("unsupported_operation", "Choose a catalog collection and metric")
        if metric in ("maintenance_cost_usd", "corrective_count", "rca") and collection != "maintenance":
            raise RetrievalError("unsupported_operation", "Maintenance metrics require the maintenance collection")
        if metric in ("status", "temperature_series", "spills", "downtime_days", "spill_count", "spill_volume_bbl", "containment", "compliance") and collection not in ("assets", "inspections"):
            raise RetrievalError("unsupported_operation", "Observation metrics require assets or inspections")
        limit, offset = _page(plan.get("limit", 50), plan.get("offset", 0))
        reference = context.get("reference_date", "2026-10-16")
        asof_end = _end_day(reference)
        window = plan.get("window") or {}
        start = plan.get("start") or plan.get("date_from") or window.get("start")
        end = plan.get("end") or plan.get("date_to") or window.get("end")
        if metric in ("rca", "corrective_count") and start is None:
            anchor = dt.date.fromisoformat(reference)
            year = anchor.year - 1
            start = dt.date(year, anchor.month, min(anchor.day, calendar.monthrange(year, anchor.month)[1])).isoformat()
        if start:
            _end_day(start)
        if end:
            _end_day(end)
        if start and end and start[:10] > end[:10]:
            raise RetrievalError("invalid_date", "Start cannot follow end")
        requested_end = end
        # Observed facts cannot certify future values or zero-count calendar bins.
        # Planned maintenance is a different collection and keeps its explicit bounds.
        observation_query = collection == "inspections" or metric in {
            "status", "temperature_series", "spills", "downtime_days", "spill_count",
            "spill_volume_bbl", "containment", "compliance"}
        clipped_future_end = bool(observation_query and end and end[:10] > reference[:10])
        if clipped_future_end:
            end = reference[:10]
        if observation_query and start and start[:10] > reference[:10]:
            raise RetrievalError("unsupported_operation", "Observed data cannot be queried after the reference date; future values require a separate forecast")
        bounds_warning = "Observed-data end was limited to the reference date; future periods are not verified zero observations"
        if metric == "status" or collection == "assets" and metric == "records":
            if start:
                raise RetrievalError("unsupported_operation", "Latest status uses an as-of end date; use temperature_series for a period")
            if end:
                asof_end = min(asof_end, _end_day(end))
        filters = plan.get("filters", {})
        if isinstance(filters, list):
            converted = {}
            for f in filters:
                if not isinstance(f, dict) or f.get("op", "eq") not in ("eq", "in"):
                    raise RetrievalError("invalid_plan", "Only typed eq/in filters are supported")
                converted[f.get("field")] = f.get("value")
            filters = converted
        if not isinstance(filters, dict) or set(filters) - {"asset_id", "asset_ids", "area_id", "team_id", "well_type", "equipment_kind", "maintenance_type", "producing", "status_note_disagrees", "spill_detected", "inspection_id"}:
            raise RetrievalError("invalid_plan", "Unsupported filter")
        filters = dict(filters)
        for key in ("asset_ids", "area_id", "well_type", "equipment_kind"):
            if plan.get(key) is not None:
                filters[key] = plan[key]
        group = plan.get("group_by", [])
        group = [group] if isinstance(group, str) else group
        if not isinstance(group, list) or len(group) > 2 or any(k not in ("asset_id", "area_id", "team_id", "month", "well_type", "equipment_kind") for k in group):
            raise RetrievalError("query_limit", "At most two allowed grouping dimensions")
        if metric == "rca" and group and "equipment_kind" not in group and not filters.get("equipment_kind"):
            raise RetrievalError("unsupported_operation", "RCA counts must use one equipment kind filter or equipment_kind grouping")
        if plan.get("only_breaches") is not None and not isinstance(plan["only_breaches"], bool):
            raise RetrievalError("invalid_plan", "only_breaches must be boolean")
        snapshot = self._snapshot(authority)
        if snapshot.knowledge_revision < int(context.get("minimum_knowledge_revision", 0)):
            raise RetrievalError("stale_revision", "Canonical authority snapshot is older than required revision")
        with self._lock:
            self._authority = snapshot
            self._active_corrections = self._corrections()
            if metric in OPERATION_DESCRIPTIONS:
                from .final_operations import assess
                return assess(self, plan, context, filters, start, end, reference, asof_end)
            if metric == "compliance":
                from .compliance import assess
                result = assess(self, plan, context, filters, start, end, reference, asof_end)
                if clipped_future_end:
                    result["requested_bounds"] = {"start": start, "end": requested_end, "closure": "both"}
                    result["warnings"].append(bounds_warning)
                return result
            sql, params, population, columns, rule_refs = self._compile(collection, metric, filters, group, start, end, asof_end, reference)
            population_params = list(params)
            if metric == "spill_count" and set(group) == {"area_id", "month"} and self._run("SELECT count(*) n FROM issues")[0]["n"] == 0:
                sql, params = self._dense_area_month(sql, params, filters, start, end or reference)
            coverage_sql = sql
            if plan.get("only_breaches") is not None:
                if metric != "containment" or not isinstance(plan["only_breaches"], bool):
                    raise RetrievalError("unsupported_operation", "only_breaches is a boolean available for containment only")
                if plan["only_breaches"]:
                    sql = "SELECT * FROM (" + sql + ") WHERE containment_hours>4 AND unknown_count=0"
            began = time.perf_counter()
            try:
                total = self._run("SELECT count(*) n FROM (" + sql + ")", params)[0]["n"]
                matching = self._run(population, population_params)[0]["n"]
                rows = self._run(sql + " LIMIT ? OFFSET ?", [*params, limit, offset])
            except RetrievalError as error:
                self._save_trace({"operation": metric, "input_text": str(plan.get("input_text", ""))[:1000], "plan": plan, "safe_sql": sql, "parameters": ["<redacted>" for _ in params], "coverage": {"status": "unknown", "matching": None}, "error": {"code": error.code, "message": str(error)}})
                raise
            unknown_columns = {"downtime_days", "containment", "status", "temperature_series", "spills"}
            if "unknown_count" in coverage_sql:
                unknown = self._run("SELECT coalesce(sum(unknown_count),0) n FROM (" + coverage_sql + ")", params)[0]["n"]
            else:
                unknown = 0
            result_id = "result_" + uuid.uuid4().hex
            for index, row in enumerate(rows):
                for boolean_key in ("producing", "spill_detected", "inspection_producing"):
                    if boolean_key in row and row[boolean_key] is not None:
                        row[boolean_key] = bool(row[boolean_key])
                if row.get("team_id") in self._team_names:
                    row["team_name"] = self._team_names[row["team_id"]]
                if (metric == "status" or collection == "assets" and metric == "records") and row.get("asset_id"):
                    if self._timeline.operations_source or self._timeline.metadata.get(row["asset_id"], {}).get("decommissioned_on"):
                        row.update(self._timeline.status(row["asset_id"], row.get("inspected_at"), row.get("inspection_producing"), reference))
                        row["decommissioned_on"] = self._timeline.metadata.get(row["asset_id"], {}).get("decommissioned_on")
                row["row_id"] = uid("row_", result_id + str(offset + index))
                rid = row.get("inspection_id") or row.get("maintenance_id") or row.get("event_id") or row.get("asset_id")
                row["evidence_refs"] = ([uid("ev_", rid)] if rid else []) + [result_id]
                if (metric == "status" or collection == "assets" and metric == "records") and row.get("asset_id"):
                    row["evidence_refs"].append(uid("ev_", row["asset_id"]))
                if row.get("latest_status_note_id"):
                    row["evidence_refs"].append(uid("ev_", row["latest_status_note_id"]))
                if row.get("status_rule_source"):
                    row["evidence_refs"].append(row["status_rule_source"])
                inspection_id = row.get("inspection_id")
                for (target, _), correction in self._active_corrections.items():
                    if target == inspection_id and correction.get("id"):
                        change_id = correction["id"]
                        row["evidence_refs"].append(uid("ev_", change_id) if change_id.startswith("CTX-") else change_id)
                if row.get("report_source_id"):
                    row["evidence_refs"].append(row["report_source_id"])
                if metric == "rca":
                    equipment_kind = row.get("equipment_kind") or filters.get("equipment_kind")
                    threshold, reference_id = self._rca_threshold(row.get("well_type"), equipment_kind, reference)
                    row["equipment_kind"] = equipment_kind
                    row.update(rca_threshold=threshold, rca_required=row["corrective_count"] >= threshold if threshold is not None else None)
                    if reference_id:
                        row["evidence_refs"].append(reference_id)
            issues = self._run("SELECT count(*) n FROM issues")[0]["n"]
            coverage = {"unit": "matching_source_record", "matching": matching, "evaluated": matching if not issues else None, "unknown": unknown, "import_issues": issues, "status": "partial" if unknown or issues else "complete", "output_rows": total, "displayed_rows": len(rows), "display_truncated": offset + len(rows) < total, "aggregation_input_truncated": False}
            trace_id = self._save_trace({"operation": metric, "input_text": str(plan.get("input_text", ""))[:1000], "plan": plan, "safe_sql": sql, "parameters": ["<redacted>" for _ in params], "tables": self._tables_for(metric, collection), "knowledge_revision": snapshot.knowledge_revision, "authority": {"baseline_corrections": len(self._baseline), "supplied_runtime_corrections": len(snapshot.corrections), "supplied_rule_overrides": len(snapshot.rule_overrides)}, "coverage": coverage, "selected_evidence": [e for r in rows[:5] for e in r["evidence_refs"]], "omitted_evidence": [{"reason": "presentation_pagination", "rows": max(0, total - len(rows))}] if total > len(rows) else [], "tokens": {"method": "Not sent to a model by this adapter", "provider_tokens": None, "retrieved_context_cap": 2000}, "elapsed_ms": round((time.perf_counter() - began) * 1000, 3)})
            result = {"schema_version": "1.0", "result_set_id": result_id, "provider_id": self.provider_id, "dataset_namespace": self.namespace, "dataset_revision": self._manifest["dataset_revision"], "knowledge_revision": snapshot.knowledge_revision, "reference_date": reference, "bounds": {"start": start, "end": end, "closure": "both"}, "time_basis": "maintenance.started_at" if metric in ("maintenance_cost_usd", "corrective_count", "rca") or collection == "maintenance" else "inspection.inspected_at" if metric != "records" or collection == "inspections" else "source record", "columns": self._result_columns(rows, columns), "rows": rows, "total_rows": total, "limit": limit, "offset": offset, "coverage": coverage, "rule_refs": rule_refs, "lineage_manifest_ref": result_id, "trace_id": trace_id, "warnings": (["Incomplete or unknown evidence; do not present partial values as a complete total"] if coverage["status"] != "complete" else []) + (["Recorded costs can include estimates for in-progress work"] if metric == "maintenance_cost_usd" else [])}
            if clipped_future_end:
                result["requested_bounds"] = {"start": start, "end": requested_end, "closure": "both"}
                result["warnings"].append(bounds_warning)
            self._results[result_id] = {"plan": dict(plan), "context": dict(context), "authority": snapshot, "result": result}
            self._persist_manifest(result_id, dict(plan, start=start, end=end), context, snapshot, result)
            while len(self._results) > 32:
                self._results.popitem(last=False)
            return result

    def _tables_for(self, metric, collection):
        if metric in ("maintenance_cost_usd", "corrective_count", "rca"):
            return ["maintenance", "assets", "areas", "canonical authority snapshot"]
        if metric == "containment":
            return ["inspections", "maintenance", "facts", "sources", "assets"]
        return [collection, "assets", "areas", "baseline_corrections", "rules", "canonical authority snapshot"]

    def _dense_area_month(self, sql, params, filters, start, end):
        earliest = self._run("SELECT min(inspected_at) at FROM inspections")[0]["at"]
        first = dt.date.fromisoformat((start or earliest or end)[:10]).replace(day=1)
        last = dt.date.fromisoformat(end[:10]).replace(day=1)
        months = []
        current = first
        while current <= last:
            months.append(current.strftime("%Y-%m"))
            if len(months) > 120:
                raise RetrievalError("query_limit", "Use a shorter period or coarser grouping; maximum 120 month bins")
            current = dt.date(current.year + (current.month == 12), 1 if current.month == 12 else current.month + 1, 1)
        if not months:
            raise RetrievalError("invalid_date", "Start must not follow end")
        # Calendar literals are generated from validated dates, never user SQL.
        calendar = " UNION ALL ".join("SELECT '" + month + "' month" for month in months)
        predicates, domain_params = [], []
        for key in ("area_id", "well_type"):
            if key in filters:
                predicates.append("a." + key + "=?"); domain_params.append(filters[key])
        assets = filters.get("asset_ids", filters.get("asset_id"))
        if assets:
            assets = assets if isinstance(assets, list) else [assets]
            predicates.append("a.asset_id IN (" + ",".join("?" for _ in assets) + ")"); domain_params.extend(assets)
        where = " WHERE " + " AND ".join(predicates) if predicates else ""
        area_domain = "SELECT DISTINCT a.area_id,ar.name area_name FROM assets a LEFT JOIN areas ar ON ar.area_id=a.area_id" + where
        dense = "SELECT d.area_id,d.area_name,calendar.month,coalesce(g.spill_count,0) spill_count FROM (" + area_domain + ") d CROSS JOIN (" + calendar + ") calendar LEFT JOIN (" + sql + ") g ON g.area_id=d.area_id AND g.month=calendar.month ORDER BY d.area_id,calendar.month"
        return dense, domain_params + list(params)

    def _result_columns(self, rows, fallback):
        units = dict(fallback)
        units.update({"ambient_temp_c": "C", "wellhead_temp_c": "C", "delta_c": "C", "threshold_c": "C", "spill_est_volume_bbl": "bbl", "cost_usd": "USD", "fine_usd": "USD", "hours_to_report": "hour", "containment_hours": "hour"})
        keys = list(dict.fromkeys(k for row in rows for k in row if k not in ("row_id", "evidence_refs"))) or [k for k, _ in fallback]
        output = []
        for key in keys:
            sample = next((r[key] for r in rows if r.get(key) is not None), None)
            kind = "boolean" if isinstance(sample, bool) else "number" if isinstance(sample, (int, float)) else "string"
            output.append({"key": key, "label": key.replace("_", " ").title(), "type": kind, "unit": units.get(key)})
        return output

    def _rca_threshold(self, well_type, equipment, reference, _seen=()):
        if well_type in _seen:
            return None, None
        for rule in self._authority.rule_overrides:
            scope = rule.get("scope", {})
            kind = rule.get("equipment_kind") or scope.get("equipment_kind")
            typ = rule.get("well_type") or scope.get("well_type") or rule.get("subject_id")
            if typ == well_type and kind in (None, equipment) and rule.get("predicate", "rca") in ("rca", "rca_threshold", "rca_repairs_threshold") and rule.get("status", "active") in ("active", "accepted", "committed"):
                if rule.get("valid_from") and rule["valid_from"][:10] > reference:
                    continue
                if rule.get("valid_to") and rule["valid_to"][:10] < reference:
                    continue
                return int(rule.get("value") if rule.get("value") is not None else rule.get("threshold", 0)), rule.get("id") or rule.get("rule_id")
        rows = self._run("SELECT c.id,c.text FROM chunks c JOIN sources s ON s.id=c.source_id WHERE s.kind='manual' AND s.path LIKE ? AND lower(c.section) LIKE '%maintenance escalation%' ORDER BY c.ordinal", ("%/" + str(well_type) + ".md",))
        inherited = None
        for row in rows:
            plain = row["text"].lower().replace("*", "")
            for match in re.finditer(r"(\d+|three|two)\s+(?:or more\s+)?corrective", plain):
                following = plain[match.end():match.end() + 180]
                target = re.search(r"\bon the\s+([a-z]+)", following)
                if target and target[1] not in {"same", "well"} and target[1] not in str(equipment).replace("_", " ").split():
                    continue
                return {"three": 3, "two": 2}.get(match[1], int(match[1]) if match[1].isdigit() else None), row["id"]
            parent = re.search(r"\bfollow\s+(t\d+)\s+section", plain)
            if parent:
                inherited = parent[1].upper()
        if inherited:
            return self._rca_threshold(inherited, equipment, reference, (*_seen, well_type))
        return None, None

    def _compile(self, collection, metric, filters, group, start, end, asof_end, reference):
        params = []
        clauses = []
        maintenance_metric = metric in ("maintenance_cost_usd", "corrective_count", "rca") or collection == "maintenance" and metric in ("records", "count")
        prefix = "" if maintenance_metric or collection in ("regulatory_events", "context_notes", "areas", "teams", "users") and metric in ("records", "count") else """WITH effective AS (SELECT i.*,effective_value(i.inspection_id,'ambient_temp_c',i.ambient_milli) ambient_value,effective_value(i.inspection_id,'wellhead_temp_c',i.wellhead_milli) wellhead_value,effective_value(i.inspection_id,'spill_detected',i.spill_detected) spill_value,effective_value(i.inspection_id,'spill_est_volume_bbl',i.volume_milli) volume_value,asset_type_at(i.asset_id,i.inspected_at) observation_well_type,production_threshold(asset_type_at(i.asset_id,i.inspected_at)) threshold FROM inspections i JOIN assets a ON a.asset_id=i.asset_id), latest AS (SELECT *,row_number() OVER(PARTITION BY asset_id ORDER BY inspected_at DESC,inspection_id DESC) rn FROM effective WHERE inspected_at<?) """
        if prefix:
            params.append(asof_end)
        current_query = metric == "status" or collection == "assets" and metric in ("records", "count")
        dimensions = {"asset_id": "a.asset_id", "area_id": "a.area_id",
                      "well_type": "asset_type_at(a.asset_id,'" + reference[:10] + "')",
                      "team_id": "asset_team_at(a.asset_id,'" + reference[:10] + "')"}
        inspection_producing = "CASE WHEN i.threshold IS NULL OR i.inspection_id IS NULL THEN NULL ELSE i.wellhead_value-i.ambient_value>=i.threshold END"
        producing_expression = "current_producing(a.asset_id,i.inspected_at,(" + inspection_producing + "),'" + reference[:10] + "')" if current_query else inspection_producing
        rule_refs = [r["source_id"] for r in self._rules.values()]
        if maintenance_metric:
            base = " FROM maintenance m JOIN assets a ON a.asset_id=m.asset_id LEFT JOIN areas ar ON ar.area_id=a.area_id"
            date_field = "m.started_at"
            dimensions.update(month="substr(m.started_at,1,7)", equipment_kind="m.equipment_kind")
            dimensions["team_id"] = "asset_team_at(a.asset_id,m.started_at)"
            if metric != "rca":
                dimensions["well_type"] = "asset_type_at(a.asset_id,m.started_at)"
            if metric in ("corrective_count", "rca"):
                clauses.append("m.maintenance_type='corrective'")
                if start is None:
                    start = (dt.date.fromisoformat(reference).replace(year=dt.date.fromisoformat(reference).year - 1)).isoformat()
            if metric == "rca" and not group:
                group = ["asset_id", "equipment_kind"]
            aggregate = {"maintenance_cost_usd": ("sum(m.cost_cents)/100.0", "USD"), "corrective_count": ("count(*)", "event"), "rca": ("count(*)", "event"), "count": ("count(*)", "record")}
            records = "m.maintenance_id,a.asset_id,a.well_type,a.area_id,ar.name area_name,m.started_at,m.completed_at,m.maintenance_type,m.equipment_kind,m.cost_cents/100.0 cost_usd,m.report_source_id,CASE WHEN m.completed_at>=? THEN 'planned/in_progress' ELSE 'recorded_completed' END completion_state"
            if metric == "records":
                # These are recorded repair claims, not inferred causes from an
                # empty inspection note. Raw record PK keeps the join one-to-one.
                base += " JOIN records job ON job.id=m.maintenance_id"
                records += ",json_extract(job.raw_json,'$.issue') issue,json_extract(job.raw_json,'$.action_taken') action_taken,m.report_path report_file,m.inspection_id triggered_by_inspection_id,json_extract(job.raw_json,'$.recorded_at') recorded_at,json_extract(job.raw_json,'$.cost_revision.original_total') original_cost_total_usd,json_extract(job.raw_json,'$.cost_revision.revised_on') cost_revised_on,json_extract(job.raw_json,'$.cost_revision.reason') cost_revision_reason"
            # Completion comparison is fixed to a safely validated date literal generated by application.
            records = records.replace("?", "'" + asof_end + "'")
        elif collection in ("areas", "teams", "users", "context_notes", "regulatory_events") and metric in ("records", "count"):
            alias = "r"
            base = " FROM " + collection + " r"
            if collection in ("context_notes", "regulatory_events"):
                base += " JOIN assets a ON a.asset_id=r.asset_id"
            elif set(filters) - {"team_id"}:
                raise RetrievalError("unsupported_operation", "Directory collection filters use the record/source explorer")
            date_field = "r.date" if collection == "regulatory_events" else "r.created_at" if collection == "context_notes" else None
            dimensions["team_id"] = "asset_team_at(a.asset_id," + date_field + ")" if date_field else "r.team_id"
            if date_field:
                dimensions["well_type"] = "asset_type_at(a.asset_id," + date_field + ")"
            records = "r.event_id,r.asset_id,r.date,r.event_type,r.protocol_id,r.inspection_id related_inspection_id,r.hours_milli/1000.0 hours_to_report,r.fine_cents/100.0 fine_usd,r.status" if collection == "regulatory_events" else "r.*"
            aggregate = {"count": ("count(*)", "record")}
        else:
            base = " FROM assets a LEFT JOIN latest i ON i.asset_id=a.asset_id AND i.rn=1" if metric == "status" or collection == "assets" and metric in ("records", "count") else " FROM effective i JOIN assets a ON a.asset_id=i.asset_id"
            base += " LEFT JOIN areas ar ON ar.area_id=a.area_id LEFT JOIN users u ON u.user_id=i.inspector_user_id"
            date_field = "i.inspected_at"
            dimensions["month"] = "substr(i.inspected_at,1,7)"
            if not current_query:
                dimensions["well_type"] = "i.observation_well_type"
                dimensions["team_id"] = "asset_team_at(a.asset_id,i.inspected_at)"
            if metric in ("spills", "spill_count", "spill_volume_bbl", "containment"):
                clauses.append("i.spill_value=1")
            records = "a.asset_id,a.well_type,a.area_id,ar.name area_name,a.recorded_status,a.lat,a.lon,i.inspection_id,i.inspected_at,u.name inspector_name,i.method,i.ambient_value/1000.0 ambient_temp_c,i.wellhead_value/1000.0 wellhead_temp_c,(i.wellhead_value-i.ambient_value)/1000.0 delta_c,i.threshold/1000.0 threshold_c,CASE WHEN i.threshold IS NULL OR i.inspection_id IS NULL THEN NULL ELSE i.wellhead_value-i.ambient_value>=i.threshold END producing,i.spill_value spill_detected,i.volume_value/1000.0 spill_est_volume_bbl,i.notes,CASE WHEN i.threshold IS NULL OR i.inspection_id IS NULL THEN 1 ELSE 0 END unknown_count"
            if current_query:
                records = records.replace(inspection_producing + " producing", inspection_producing + " inspection_producing," + producing_expression + " producing")
            records += ",i.observation_well_type inspection_well_type"
            records += ",(SELECT json_extract(ir.raw_json,'$.recorded_at') FROM records ir WHERE ir.id=i.inspection_id) recorded_at"
            aggregate = {"downtime_days": ("7*sum(CASE WHEN i.threshold IS NOT NULL AND i.wellhead_value-i.ambient_value<i.threshold THEN 1 ELSE 0 END)", "day"), "spill_count": ("count(*)", "spill"), "spill_volume_bbl": ("sum(i.volume_value)/1000.0", "bbl"), "count": ("count(*)", "record")}
            if metric == "containment":
                base += " LEFT JOIN maintenance m ON m.inspection_id=i.inspection_id LEFT JOIN facts f ON f.subject_id=m.maintenance_id AND f.predicate='containment_hours'"
                # Numeric cast is compiler-owned, no arbitrary expressions accepted.
                records = "a.asset_id,i.inspection_id,i.inspected_at,max(m.maintenance_id) maintenance_id,max(m.report_source_id) report_source_id,min(CAST(f.value_json AS REAL)) unused_value"
                records = records.replace("min(CAST(f.value_json AS REAL)) unused_value", "min(CAST(substr(f.value_json,2,length(f.value_json)-2) AS REAL)) containment_hours,CASE WHEN count(DISTINCT f.value_json)!=1 THEN 1 ELSE 0 END unknown_count")
        if maintenance_metric or prefix:
            records = records.replace("a.well_type,", dimensions["well_type"] + " well_type,")
            records += "," + dimensions["team_id"] + " team_id"
        for key, value in filters.items():
            if key in ("asset_id", "asset_ids"):
                values = value if isinstance(value, list) else [value]
                if not values or len(values) > 200 or any(not isinstance(v, str) or len(v) > 128 for v in values):
                    raise RetrievalError("query_limit", "Asset filter must contain 1–200 IDs")
                clauses.append("a.asset_id IN (" + ",".join("?" for _ in values) + ")"); params.extend(values)
            elif key == "inspection_id":
                if not prefix or not isinstance(value, str) or len(value) > 128:
                    raise RetrievalError("invalid_plan", "Inspection ID requires an inspection/status query")
                clauses.append("i.inspection_id=?"); params.append(value)
            elif key in ("area_id", "well_type"):
                if not isinstance(value, str) or len(value) > 128:
                    raise RetrievalError("invalid_plan", "Expected bounded filter value")
                clauses.append((dimensions["well_type"] if key == "well_type" else "a.area_id") + "=?"); params.append(value)
            elif key == "team_id":
                if not isinstance(value, str) or len(value) > 128:
                    raise RetrievalError("invalid_plan", "Expected bounded team ID")
                clauses.append(dimensions["team_id"] + "=?"); params.append(value)
            elif key in ("equipment_kind", "maintenance_type"):
                if not maintenance_metric:
                    raise RetrievalError("unsupported_operation", "Equipment/job filters require maintenance collection")
                clauses.append("m." + key + "=?"); params.append(str(value))
            elif key == "producing":
                if not prefix or not isinstance(value, bool):
                    raise RetrievalError("invalid_plan", "Producing filter must be boolean on inspection/status queries")
                clauses.append("(" + producing_expression + ")=?"); params.append(int(value))
            elif key == "status_note_disagrees":
                if not current_query or not isinstance(value, bool):
                    raise RetrievalError("invalid_plan", "Status-note disagreement is a boolean filter for current asset/status queries")
                clauses.append("status_disagrees(a.asset_id,i.inspected_at,(" + inspection_producing + "),'" + reference[:10] + "')=?")
                params.append(int(value))
            elif key == "spill_detected":
                if not prefix or not isinstance(value, bool):
                    raise RetrievalError("invalid_plan", "Spill filter must be boolean on inspection queries")
                clauses.append("i.spill_value=?"); params.append(int(value))
        if date_field and not (metric == "status" or collection == "assets" and metric in ("records", "count")):
            if start:
                clauses.append(date_field + ">=?"); params.append(start[:10])
            clauses.append(date_field + "<?"); params.append(_end_day(end) if end else asof_end)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        population = prefix + "SELECT count(" + ("DISTINCT i.inspection_id" if metric == "containment" else "*") + ") n" + base + where
        if metric in aggregate:
            if not group:
                group = ["asset_id"] if metric != "count" else []
            if any(k not in dimensions for k in group):
                raise RetrievalError("unsupported_operation", "Grouping is incompatible with selected metric")
            selections = [dimensions[k] + " " + k for k in group]
            if "area_id" in group:
                selections.append("max(ar.name) area_name")
            if metric == "rca":
                selections.append(dimensions["well_type"] + " well_type")
            name = "corrective_count" if metric == "rca" else metric
            expr, unit = aggregate[metric]
            selections.append(expr + " " + name)
            if metric == "spill_volume_bbl":
                selections.append("sum(CASE WHEN i.volume_value IS NULL THEN 1 ELSE 0 END) unknown_count")
            if metric == "downtime_days":
                selections.append("sum(CASE WHEN i.threshold IS NULL THEN 1 ELSE 0 END) unknown_count")
            sql = prefix + "SELECT " + ",".join(selections) + base + where
            if group:
                sql += " GROUP BY " + ",".join(dimensions[k] for k in group)
            sql += " ORDER BY " + name + " DESC" + ("," + ",".join(group) if group else "")
            return sql, params, population, [(k, None) for k in group] + [(name, unit)], rule_refs
        sql = prefix + "SELECT " + records + base + where
        if metric == "containment":
            sql += " GROUP BY i.inspection_id,a.asset_id ORDER BY i.inspected_at DESC,i.inspection_id"
            columns = [("asset_id", None), ("inspection_id", None), ("containment_hours", "hour"), ("unknown_count", "record")]
        else:
            sql += " ORDER BY " + ("m.started_at DESC,m.maintenance_id" if maintenance_metric else "a.asset_id,i.inspected_at DESC" if prefix else "r." + IDS[collection])
            columns = [("asset_id", None), ("inspection_id", None), ("inspected_at", None), ("delta_c", "C"), ("producing", None)] if prefix else [(IDS[collection], None)]
        return sql, params, population, columns, rule_refs

    def result_page(self, handle, context, limit=50, offset=0):
        self._scope(context)
        _page(limit, offset)
        with self._lock:
            saved = self._load_manifest(handle, context)
            plan = dict(saved["plan"], limit=limit, offset=offset)
            return self.query(plan, saved["context"], saved["authority"])

    def close(self):
        with self._lock:
            self._db.close()


def create_provider(dataset_roots, db_path=None, *, namespace="asset-field", rebuild=False, gemma_enricher=None):
    path = Path(db_path).resolve() if db_path else Path(__file__).parent / ".cache" / "dataset.sqlite"
    needs_rebuild = rebuild or not path.is_file()
    if not needs_rebuild:
        check = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        try:
            row = check.execute("SELECT value_json FROM manifest WHERE key='schema_version'").fetchone()
            needs_rebuild = not row or json.loads(row[0]) != SCHEMA_VERSION
        except sqlite3.Error:
            needs_rebuild = True
        finally:
            check.close()
    if needs_rebuild:
        build_index(dataset_roots, path, namespace=namespace)
    return SQLiteRetrievalProvider(path, namespace=namespace, gemma_enricher=gemma_enricher)
