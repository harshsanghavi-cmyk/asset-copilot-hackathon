"""Bounded Q&A workflow. Depends on a provider Protocol, never its storage."""
from __future__ import annotations

import asyncio
import json
import hashlib
import re
import uuid
from contextvars import ContextVar
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from backend.contracts import ModelUnavailable, PlannerOutput, ViewPlan, SuggestionOutput, json_safe
from backend.memory import MemoryStore
from backend.memory.budget import estimate, pack_evidence, select, attach_reference
from backend.memory.token_packing import fit_section
from backend.retrieval.contracts import AuthoritySnapshot, RetrievalProvider, RetrievalError
from .gemma import ModelReply, MODEL
from .prompts import load_prompt, bind_prompt
from .workflow import checkpointed, runner
from .dates import normalize_relative_window

execution_events = ContextVar("asset_execution_events", default=None)


def normalize_evidence(raw: dict, identifier: str | None = None) -> dict:
    eid = identifier or raw.get("evidence_id") or raw.get("id") or raw.get("source_id")
    if not eid:
        raise ValueError("Provider source is missing a stable evidence ID")
    excerpt = raw.get("text") or raw.get("excerpt") or raw.get("preview")
    if not excerpt and raw.get("original") is not None:
        excerpt = json.dumps(raw["original"], ensure_ascii=False, default=str)
    result = {"id": str(eid), "title": str(raw.get("title") or raw.get("section") or raw.get("record_id") or raw.get("path") or eid),
              "source_kind": str(raw.get("source_kind") or raw.get("kind") or "record"),
              "source_id": str(raw.get("source_id") or raw.get("id") or eid)}
    if raw.get("asset_id"):
        result["asset_id"] = str(raw["asset_id"])
    for key, value in {"excerpt": excerpt, "path": raw.get("path"), "author": raw.get("author"),
                       "source_time": raw.get("source_time")}.items():
        if value is not None:
            result[key] = str(value)
    return result


def normalize_result(raw: dict, revision: int, dataset_revision: str) -> dict:
    if raw.get("knowledge_revision", revision) != revision:
        raise ValueError("Provider result has a different authority revision")
    if str(raw.get("dataset_revision", dataset_revision)) != dataset_revision:
        raise ValueError("Provider result has a different dataset revision")
    columns = []
    for c in raw.get("columns", []):
        if isinstance(c, str):
            c = {"key": c}
        entry = {"key": c["key"], "label": c.get("label") or c["key"].replace("_", " ").title()}
        if c.get("unit"):
            entry["unit"] = c["unit"]
        columns.append(entry)
    keys = {c["key"] for c in columns}
    rows, eids = [], list(raw.get("evidence_ids", []))
    for item in raw.get("rows", []):
        row = {}
        for key in keys:
            value = item.get(key)
            row[key] = json_safe(value) if value is None or isinstance(value, (str, int, float, bool)) else json.dumps(json_safe(value), ensure_ascii=False)
        rows.append(row)
        for ref in item.get("evidence_refs", []):
            if ref not in eids:
                eids.append(ref)
    for ref in raw.get("rule_refs", []):
        if ref not in eids:
            eids.append(ref)
    result = {"result_set_id": raw["result_set_id"], "dataset_revision": dataset_revision,
              "knowledge_revision": revision, "columns": columns, "rows": rows, "evidence_ids": eids,
              "provider_coverage": raw.get("coverage", {}), "trace_id": raw.get("trace_id"),
              "warnings": list(raw.get("warnings", [])), "bounds": raw.get("bounds")}
    result["operation"] = raw.get("operation")
    for key in ("summary", "assessment_counts"):
        if raw.get(key) is not None:
            result[key] = raw[key]
    result["summary"] = raw.get("summary")
    coverage = raw.get("coverage", {})
    if all(isinstance(coverage.get(k), (int, float)) for k in ("matching", "evaluated", "unknown")):
        result["coverage"] = {k: coverage[k] for k in ("matching", "evaluated", "unknown")}
    return result


class CopilotService:
    def __init__(self, provider: RetrievalProvider, memory: MemoryStore, model, reference_date="2026-10-16"):
        self.provider, self.memory, self.model = provider, memory, model
        self._locks: dict[str, asyncio.Lock] = {}
        self._background: set[asyncio.Task] = set()
        self._users = None
        self._inflight: dict[str, asyncio.Task] = {}
        self._listeners: dict[str, list] = {}
        self._asset_names = None
        self._asset_revision = None
        self._suggestion_jobs = set()
        self.reference_date = reference_date

    def suggestion_input(self, user_id, answer_id):
        answer = self.memory.answer(answer_id, user_id)
        history = self.memory.history(answer["thread_id"], user_id)["messages"]
        question = next((m["content"] for m in history if m["role"] == "user" and m["run_id"] == answer_id), "")
        visible = []
        for message in history:
            if message.get("status") == "error":
                continue
            if message["role"] in {"user", "assistant"}:
                content = message["content"]
                if message["role"] == "assistant":
                    content = re.sub(r"\[[^\]]+\]", "", content).strip()
                visible.append({"role": message["role"], "content": content})
            if message["role"] == "assistant" and message["run_id"] == answer_id:
                break
        tail, _ = select(list(reversed(visible)), 1000)
        payload = {"question": question, "displayed_answer": re.sub(r"\[[^\]]+\]", "", answer["narrative"]).strip(), "visible_conversation": list(reversed(tail))}
        version = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return payload, version

    def answer_suggestions(self, user_id, answer_id, enqueue=False):
        payload, version = self.suggestion_input(user_id, answer_id)
        state = self.memory.suggestions(user_id, answer_id, version)
        if not enqueue and not state["exists"]:
            return {"answer_id": answer_id, "version": version, "status": "error", "suggestions": [], "error_code": "not_requested"}
        key = (user_id, answer_id, version)
        if not enqueue and state["status"] == "pending" and key not in self._suggestion_jobs:
            return self.memory.suggestions(user_id, answer_id, version, "error", error="interrupted")
        if enqueue and state["status"] != "ready" and key not in self._suggestion_jobs:
            if estimate(payload["question"]) > 4000 or estimate(payload["displayed_answer"]) > 8000:
                return self.memory.suggestions(user_id, answer_id, version, "error", error="input_budget")
            self.memory.suggestions(user_id, answer_id, version, "pending")
            self._suggestion_jobs.add(key)
            async def generate():
                try:
                    async with asyncio.timeout(120):
                        reply = await self.model.generate("suggestions", bind_prompt("suggestions", payload), payload, max_tokens=256)
                    parsed = SuggestionOutput.model_validate(reply.data)
                    self.memory.suggestions(user_id, answer_id, version, "ready", parsed.suggestions)
                except asyncio.CancelledError:
                    self.memory.suggestions(user_id, answer_id, version, "error", error="interrupted")
                    raise
                except Exception as exc:
                    code = "suggestions_timeout" if isinstance(exc, TimeoutError) else str(getattr(exc, "code", "invalid_suggestions"))[:80]
                    self.memory.suggestions(user_id, answer_id, version, "error", error=code)
                finally:
                    self._suggestion_jobs.discard(key)
            task = asyncio.create_task(generate())
            self._background.add(task)
            task.add_done_callback(self._background.discard)
        state.pop("exists", None)
        return state

    @staticmethod
    def _asset_key(value):
        key = re.sub(r"[^a-z0-9]", "", str(value).casefold())
        match = re.fullmatch(r"([a-z]+)0*(\d+)", key)
        return match[1] + str(int(match[2])) if match else key

    def asset_references(self, text, context):
        revision = context["dataset_revision"]
        if self._asset_names is None or self._asset_revision != revision:
            aliases = {}; offset = 0
            while offset < 10000:
                page = self.provider.query({"collection": "assets", "metric": "records", "limit": 100, "offset": offset}, context, self.memory.authority(context["reference_date"]))
                rows = page.get("rows", [])
                for row in rows:
                    identity = row.get("asset_id")
                    if identity:
                        for value in (identity, row.get("name")):
                            if value:
                                aliases.setdefault(self._asset_key(value), set()).add(identity)
                offset += len(rows)
                total = page.get("total_rows", len(rows))
                if not rows or offset >= total:
                    break
            self._asset_names, self._asset_revision = aliases, revision
        candidates = re.findall(r"\bwell[\s-]*\d+\b", text, re.I)
        resolved, unknown, ambiguous = [], [], []
        for candidate in candidates:
            matches = self._asset_names.get(self._asset_key(candidate), set())
            if len(matches) == 1:
                resolved.extend(matches)
            elif not matches:
                unknown.append(candidate)
            else:
                ambiguous.append(candidate)
        return list(dict.fromkeys(resolved)), unknown, ambiguous

    def context(self, user_id, session_id="", run_id="", reference_date=None):
        reference_date = reference_date or self.reference_date
        catalog = self.provider.catalog()
        return {"schema_version": "1.0", "dataset_namespace": self.provider.namespace,
                "dataset_revision": str(catalog.get("dataset_revision", "unknown")), "user_id": user_id,
                "user_name": next((u["name"] for u in self._users or [] if u["user_id"] == user_id), user_id),
                "user_team_id": next((u.get("team_id") for u in self._users or [] if u["user_id"] == user_id), None),
                "thread_id": session_id, "run_id": run_id, "reference_date": reference_date,
                "timezone": "UTC", "knowledge_revision": self.memory.head(),
                "minimum_knowledge_revision": self.memory.head()}

    def users(self):
        if not self._users:
            ctx = self.context("__directory__")
            result = self.provider.query({"collection": "users", "metric": "records", "limit": 100}, ctx, self.memory.authority())
            self._users = [{k: row.get(k) for k in ("user_id", "name", "role", "team_id")} for row in result.get("rows", [])]
        return self._users

    def readiness(self):
        try:
            people = self.users()
            ctx = self.context("__directory__")
            result = self.provider.query({"collection": "assets", "metric": "records", "limit": 1}, ctx, self.memory.authority())
            rows = result.get("rows", [])
            assets = result.get("total_rows", result.get("coverage", {}).get("matching")) if rows else 0
            # Non-counting replacement providers can expose availability without
            # a specific storage schema; a missing count is explicitly unknown.
            data_ready = bool(people) and bool(rows) and (assets is None or isinstance(assets, (int, float)) and assets > 0)
            return {"data_ready": data_ready, "user_count": len(people), "asset_count": assets,
                    "ready": data_ready and bool(getattr(self.model, "configured", False)),
                    "reason": None if data_ready else "Mandatory user/asset catalog is empty or unavailable; rebuild/replace the dataset provider before live Q&A"}
        except (RetrievalError, ValueError) as exc:
            return {"data_ready": False, "ready": False, "reason": "Dataset provider not ready: " + str(exc)}

    def validate_user(self, user_id):
        if not user_id or user_id not in {u["user_id"] for u in self.users()}:
            raise PermissionError("Select a known dataset user")

    def directories(self, context):
        data = {}
        for collection, identifier in [("areas", "area_id"), ("teams", "team_id")]:
            try:
                result = self.provider.query({"collection": collection, "metric": "records", "limit": 100}, context, self.memory.authority(context["reference_date"]))
                data[collection] = [{identifier: row.get(identifier), "name": row.get("name"), **({"team_id":row.get("team_id"), "team_name":row.get("team_name")} if collection == "areas" else {})} for row in result.get("rows", [])]
            except (RetrievalError, ValueError):
                data[collection] = []
        return data if estimate(data) <= 2000 else {"status": "directory_requires_targeted_lookup"}

    async def _stage(self, name, payload):
        if name == "read_context":
            payload = {**payload, "shared_head": self.memory.head(), "private_head": self.memory.private_head(payload["user_id"])}
        elif name == "model":
            payload = {**payload, "prompt_revision": hashlib.sha256(load_prompt(payload["purpose"]).encode()).hexdigest(), "selected_model":getattr(self.model,"model_id",MODEL)}
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        current = execution_events.get()
        if current:
            cached = self.memory.stage_result(current["user_id"], current["run_id"], name, fingerprint)
            if cached is not None:
                return cached
        active = runner.get()
        if active:
            receipt = await active(name, payload)
            if isinstance(receipt, dict) and receipt.get("stage_name") == name and receipt.get("input_hash") == fingerprint:
                result = receipt["result"]
            else:
                # Changed control flow must never reinterpret another cached
                # tool/model result as this operation.
                result = await self._dispatch_stage(name, payload)
        else:
            result = await self._dispatch_stage(name, payload)
        if current:
            self.memory.stage_result(current["user_id"], current["run_id"], name, fingerprint, result)
        return result

    @asynccontextmanager
    async def _track_stage(self, name, operation=None, tool_name=None):
        current = execution_events.get()
        details = {}
        stage_id = str(uuid.uuid4())
        async def emit(status):
            if not current:
                return
            event = {"stage_id": stage_id, "stage": name, "status": status,
                     "run_id": current["run_id"], "attempt_id": current["attempt_id"],
                     "timestamp": datetime.now(timezone.utc).isoformat(),
                     "operation": operation or name, "tool_name": tool_name,
                     "message": name.replace("_", " ").title() + " " + status, **details}
            self.memory.append_stage(current["run_id"], current["user_id"], event)
            if current["progress"]:
                await current["progress"](event)
        await emit("started")
        try:
            yield details
        except BaseException as exc:
            details["error_code"] = str(getattr(exc, "code", type(exc).__name__))[:80]
            await emit("failed")
            raise
        else:
            await emit("completed")

    async def _dispatch_stage(self, name, payload):
        stage = payload.get("purpose", name) if name == "model" else "read_evidence" if name == "search_evidence" else name
        plan = payload.get("plan", {})
        operation = ".".join(str(plan[k]) for k in ("collection", "metric") if k in plan) or stage
        tool = None if name == "model" else name
        async with self._track_stage(stage, operation, tool) as details:
            filters = plan.get("filters", {})
            if isinstance(filters, dict):
                if isinstance(filters.get("asset_id"), str):
                    details["asset_id"] = filters["asset_id"]
                if isinstance(filters.get("asset_ids"), list):
                    details["asset_ids"] = filters["asset_ids"][:5]
            result = await self._execute_stage(name, payload)
            if isinstance(result, dict) and isinstance(result.get("rows"), list):
                details["result_count"] = len(result["rows"])
            return result

    async def _execute_stage(self, name, payload):
        if name == "model":
            schema = {"PlannerOutput": PlannerOutput, "ViewPlan": ViewPlan}[payload["schema"]]
            attempts = list(payload["attempts"])
            value, reply = await self._validated_model_direct(payload["purpose"], payload["payload"], schema, attempts)
            return {"value": value.model_dump(), "reply": {"data": reply.data, "usage": reply.usage, "call_id": reply.call_id, "live": reply.live}, "attempts": attempts}
        if name == "query_records":
            plan = payload["plan"]
            result = json_safe(self.provider.query(plan, payload["context"], payload["authority"]))
            result["operation"] = {"collection": plan.get("collection"), "metric": plan.get("metric")}
            coverage = result.get("coverage", {})
            total = result.get("total_rows", 0)
            # Complete map/status populations through the public paging seam;
            # no storage or SQL assumptions enter the orchestration layer.
            if (plan.get("metric") == "status" and int(plan.get("limit", 100)) >= 100
                    and coverage.get("display_truncated") and isinstance(total, int) and 0 < total <= 1000):
                rows = list(result.get("rows", []))
                pages = [result["result_set_id"]]
                while len(rows) < total:
                    page = json_safe(self.provider.query({**plan, "offset": len(rows), "limit": 100}, payload["context"], payload["authority"]))
                    if (page.get("dataset_revision") != result.get("dataset_revision")
                            or page.get("knowledge_revision") != result.get("knowledge_revision") or not page.get("rows")):
                        raise ValueError("Paged provider result changed revision or stopped before its declared population")
                    rows.extend(page["rows"])
                    pages.append(page["result_set_id"])
                identity = "app:pages:" + str(uuid.uuid4())
                result.update(result_set_id=identity, rows=rows, total_rows=len(rows))
                result["coverage"] = {**coverage, "displayed_rows": len(rows), "display_truncated": False}
                result["application_evidence"] = {"id": identity, "source_id": identity,
                    "source_kind": "verified_paged_query", "title": "Complete effective status population",
                    "excerpt": f"{len(rows)} matching assets returned at one source and knowledge revision.",
                    "page_result_ids": pages}
                result.setdefault("evidence_ids", []).append(identity)
            return result
        if name == "read_evidence":
            return json_safe(self.provider.evidence(payload["handle"], payload["context"]))
        if name == "search_evidence":
            return json_safe(self.provider.search(payload["terms"], payload["context"], **payload["filters"]))
        if name == "write_knowledge":
            from backend.contracts import MemoryDraft
            return self.memory.commit_draft(payload["user_id"], payload["run_id"], payload["index"], MemoryDraft.model_validate(payload["draft"]), payload["message"], original_value=payload["original"])
        if name == "read_context":
            for _ in range(2):
                revision = self.memory.head()
                private_revision = self.memory.private_head(payload["user_id"])
                authority = self.memory.authority(payload["reference_date"])
                ctx = self.context(payload["user_id"], payload["session_id"], payload["run_id"], payload["reference_date"])
                pack = self.memory.context(payload["user_id"], payload["session_id"], payload["message"], payload["reference_date"], subjects=payload.get("subjects") or None, byte_scale=4 if hasattr(self.model, "count_tokens") else 1)
                if (revision == authority["knowledge_revision"] == ctx["knowledge_revision"] == self.memory.head()
                        and private_revision == self.memory.private_head(payload["user_id"])):
                    break
            else:
                raise ModelUnavailable("knowledge_changed", "Knowledge changed repeatedly while loading context; retry for a consistent snapshot")
            names = {u["user_id"]: u["name"] for u in self.users()}
            for key in ("private_capsule", "private_detail", "shared_detail"):
                for fact in pack["long_term"].get(key, []):
                    if fact.get("author") in names:
                        fact["author"] = names[fact["author"]]
            return {"context": ctx, "memory": pack,
                    "authority": authority, "directories": self.directories(ctx)}
        raise ValueError("Unknown workflow stage")

    async def _validated_model(self, purpose, payload, schema, attempts):
        result = await self._stage("model", {"purpose": purpose, "payload": payload, "schema": schema.__name__, "attempts": list(attempts)})
        attempts[:] = result["attempts"]
        return schema.model_validate(result["value"]), ModelReply(**result["reply"])

    async def _validated_model_direct(self, purpose, payload, schema, attempts):
        if attempts[0] >= 4:
            raise ModelUnavailable("attempt_budget", "Foreground completion attempt limit reached")
        attempts[0] += 1
        reply = await self.model.generate(purpose, bind_prompt(purpose, payload), payload, on_wait=self._quota_wait)
        try:
            return schema.model_validate(reply.data), reply
        except ValidationError as error:
            current = execution_events.get()
            if current:
                self.memory.record_validation(current["user_id"],current["run_id"],purpose,"invalid_model_schema",[{"path":list(e["loc"]),"type":e["type"]} for e in error.errors(include_input=False)][:20],reply.data)
            if attempts[0] >= 4 or attempts[1]:
                raise ModelUnavailable("invalid_model_schema", "Model output failed local schema validation") from error
            attempts[1] = True; attempts[0] += 1
            compact_errors = [{"path": list(e["loc"]), "type": e["type"]} for e in error.errors(include_input=False)]
            repair_short = {"invalid_output": reply.data, "validation_errors": compact_errors}
            repair_fields = []
            expected_schema = schema.model_json_schema()
            if estimate(repair_short) > 1000:
                repair_fields = list(dict.fromkeys(str(e["path"][0]) for e in compact_errors if e["path"]))
                repair_short["invalid_output"] = {k: reply.data[k] for k in repair_fields if k in reply.data}
                expected_schema = {**expected_schema, "properties": {k: v for k, v in expected_schema.get("properties", {}).items() if k in repair_fields}, "required": repair_fields, "additionalProperties": False}
                if "$ref" not in json.dumps(expected_schema["properties"]):
                    expected_schema.pop("$defs", None)
            if estimate(repair_short) > 1000:
                paths = ", ".join(".".join(map(str, e["path"])) + ":" + e["type"] for e in compact_errors)
                raise ModelUnavailable("repair_budget", "Invalid output cannot fit the short-term repair slot; no hidden expanded prompt sent. Invalid fields: " + paths[:400]) from error
            repair_memory = {**payload.get("memory", {}), "short_term": repair_short}
            repair_payload = {**payload, "memory": repair_memory, "expected_schema": expected_schema}
            if repair_fields:
                repair_payload["repair_fields"] = repair_fields
            async with self._track_stage("repair"):
                repair = await self.model.generate("repair", bind_prompt("repair", repair_payload), repair_payload, on_wait=self._quota_wait)
            try:
                candidate = {**reply.data, **{k: repair.data[k] for k in repair_fields if k in repair.data}} if repair_fields else repair.data
                return schema.model_validate(candidate), repair
            except ValidationError as exc:
                raise ModelUnavailable("invalid_model_schema", "Model formatting repair failed; no further repair attempted") from exc

    async def _quota_wait(self, event):
        current = execution_events.get()
        if not current:
            return
        retrying = event.get("state") == "retrying"
        state = {"stage_id": ("retry:" if retrying else "quota:") + str(event.get("queue_id",event.get("call_id","shared"))), "stage": "model_retry" if retrying else "quota_wait",
                 "run_id": current["run_id"], "attempt_id": current["attempt_id"],
                 "status": "completed" if event.get("state") == "admitted" else "started",
                 "timestamp": datetime.now(timezone.utc).isoformat(), "queue_state": event.get("state","queued"),
                 "retry_at": event.get("retry_at"), "reason": event.get("reason","transient_retry" if retrying else "shared_admission"), "priority": event.get("priority",0),
                 "message": event.get("message") or ("Retrying a transient model failure" if retrying else "Model request admitted" if event.get("state") == "admitted" else "Waiting for shared model quota")}
        self.memory.append_stage(current["run_id"], current["user_id"], state)
        if current["progress"]:
            await current["progress"](state)

    async def _repair_grounding(self, error, view, payload, attempts):
        current = execution_events.get()
        data = view.model_dump()
        details = getattr(error,"validation_details",{"message":str(error)[:300]})
        if current:
            self.memory.record_validation(current["user_id"],current["run_id"],"maker_grounding",error.code,details,data)
        if attempts[0] >= 4:
            raise error
        fields = ["blocks"] if error.code in {"invalid_result_reference","invalid_column_reference","invalid_evidence_reference","invalid_visual_semantics"} else ["narrative","claims"]
        short = {"invalid_output":{k:data[k] for k in fields},"validation_errors":[{"code":error.code,"details":details}]}
        counter = getattr(self.model,"count_tokens",None)
        count = (await counter(json.dumps(short),on_wait=self._quota_wait))["count"] if counter else estimate(short)
        if count > 1000:
            raise ModelUnavailable("grounding_repair_budget","The invalid answer fields do not fit the bounded repair slot")
        schema = ViewPlan.model_json_schema()
        schema.update(properties={k:v for k,v in schema["properties"].items() if k in fields},required=fields,additionalProperties=False)
        repair_payload = {**payload,"memory":{**payload["memory"],"short_term":short},"expected_schema":schema,"repair_fields":fields}
        attempts[0] += 1
        async with self._track_stage("grounding_repair"):
            reply = await self.model.generate("repair",bind_prompt("repair",repair_payload),repair_payload,on_wait=self._quota_wait)
        try:
            fixed = ViewPlan.model_validate({**data,**{k:reply.data[k] for k in fields if k in reply.data}})
        except ValidationError as exc:
            if current:self.memory.record_validation(current["user_id"],current["run_id"],"grounding_repair","invalid_model_schema",[{"path":list(e["loc"]),"type":e["type"]} for e in exc.errors(include_input=False)][:20],reply.data)
            raise ModelUnavailable("grounding_repair_invalid","The bounded answer repair did not validate") from exc
        return fixed,reply

    async def _fit_memory(self, pack):
        counter = getattr(self.model, "count_tokens", None)
        methods = {}
        for key, cap in (("long_term", 2000), ("short_term", 1000)):
            fitted, info = await fit_section(pack[key], cap, counter, key, self._quota_wait)
            pack[key] = fitted
            pack["accounting"][key] = info["count"]
            methods[key] = info
        pack["accounting"]["slot_measurements"] = methods
        pack["accounting"]["method"] = "google_sdk_countTokens_slots" if all(x["method"] == "google_sdk_countTokens" for x in methods.values()) else "conservative_utf8_upper_bound_fallback"
        return pack

    def _private_presentation(self, results, pack):
        preferences = [f.get("statement","") for k in ("private_capsule","private_detail") for f in pack["long_term"].get(k,[]) if f.get("kind") in {"preference","work_context"}]
        text = " ".join(preferences)
        thousands = bool(re.search(r"thousand",text,re.I) and re.search(r"dollar|\bUSD\b|cost|money",text,re.I))
        sort_area = bool(re.search(r"sort|order",text,re.I) and re.search(r"area|region",text,re.I) and re.search(r"well|asset|\bID\b",text,re.I))
        from decimal import Decimal
        for result in results.values():
            keys={c["key"] for c in result.get("columns",[])}
            if sort_area and "asset_id" in keys and ({"area_id","area_name"}&keys):
                result["rows"].sort(key=lambda r:(str(r.get("area_name") or r.get("area_id") or ""),str(r.get("asset_id") or "")))
                result.setdefault("presentation",{})["sort_keys"]=["area_name","asset_id"]
            if thousands:
                for column in list(result.get("columns",[])):
                    if column.get("unit") == "USD" or column["key"].endswith("_usd"):
                        original=column["key"];derived=original+"_thousands"
                        if derived in keys:continue
                        for row in result["rows"]:
                            value=row.get(original)
                            row[derived]=float(Decimal(str(value))/Decimal(1000)) if isinstance(value,(int,float)) and not isinstance(value,bool) else None
                        result["columns"].append({"key":derived,"label":column.get("label",original)+" (thousand USD)","unit":"thousand USD","derived_from":original,"display_divisor":1000})
                        column["raw_source_value"]=True
                        result.setdefault("presentation",{})["currency_unit"]="thousand USD"
                        keys.add(derived)

    async def answer(self, *, user_id, session_id, run_id, message, reference_date=None, progress=None, client_message_id=None, attempt_id=None):
        reference_date = reference_date or self.reference_date
        self.validate_user(user_id)
        prior = self.memory.begin(run_id, session_id, user_id, message, client_message_id)
        run_id = prior.get("id", run_id)
        layout_request = bool(re.search(r"\b(?:row|column|horizontal|vertical|side by side|layout|grid)\b", message, re.I)
                              and re.search(r"\b(?:single|one|instead|arrange|layout|change|put|make|side by side)\b", message, re.I)
                              and not re.search(r"\b(?:filter|top|latest|producing|downtime|spill|cost|WELL-\d+)\b", message, re.I))
        if layout_request:
            old = json.loads(prior["response"]) if prior.get("response") else {}
            if old.get("presentation_only"):
                return old
            source = self.memory.previous_answer(session_id, user_id, run_id)
            ctx = self.context(user_id, session_id, run_id, reference_date)
            if source:
                answer = json.loads(json.dumps(source))
                direction = "column" if re.search(r"(?:single|one)\s+column|vertical|stack", message, re.I) and not re.search(r"(?:single|one)\s+row", message, re.I) else "row"
                answer.update(answer_id=run_id, thread_id=session_id, user_id=user_id,
                    narrative="Rearranged the same verified results into one " + direction + ".",
                    presentation_only=True, source_answer_id=source.get("source_answer_id", source["answer_id"]),
                    layout={"direction": direction, "mode": "single_" + direction})
                answer["blocks"] = [{**b, "id": f"{run_id}:layout:{i}", "span": 1 if direction == "row" else 3} for i, b in enumerate(source.get("blocks", []))]
                answer["generation"] = {"status": "complete", "mode": "presentation_only", "live": False, "calls": []}
            else:
                answer = self._empty(ctx, "There is no earlier result in this conversation to rearrange. Select the answer you want to change.", [])
                answer["presentation_only"] = True
            self.memory.finish(run_id, session_id, user_id, answer, "presentation", replace_existing=True)
            return answer
        alias_context = self.context(user_id, session_id, run_id, reference_date)
        current_assets = []
        if re.search(r"\bwell[\s-]*\d+\b", message, re.I):
            current_assets, _, _ = self.asset_references(message, alias_context)
            if current_assets:
                self.memory.focus(session_id, user_id, asset_ids=current_assets, run_id=run_id)
        elif not self.memory.focus(session_id, user_id)["asset_ids"] and re.search(r"dash|trend|\bit\b", message, re.I):
            earlier_texts = self.memory.recent_user_texts(session_id, user_id, run_id)
            pending_text = next((r["content"] for r in earlier_texts if re.search(r"dash|trend", r["content"], re.I)), None)
            for previous in earlier_texts:
                if not re.search(r"\bwell[\s-]*\d+\b", previous["content"], re.I):
                    continue
                found, unknown, ambiguous = self.asset_references(previous["content"], alias_context)
                if found and not unknown and not ambiguous:
                    self.memory.focus(session_id, user_id, asset_ids=found, pending_intent=pending_text, run_id=previous["run_id"])
                    break
        if prior.get("response") and prior.get("status") != "partial":
            return json.loads(prior["response"])
        listeners = self._listeners.setdefault(run_id, [])
        if progress:
            listeners.append(progress)
        owner = self._inflight.get(run_id)
        if owner and owner is not asyncio.current_task():
            try:
                return await asyncio.shield(owner)
            finally:
                if progress in listeners:
                    listeners.remove(progress)
        self._inflight[run_id] = asyncio.current_task()
        async def broadcast(value):
            for callback in list(self._listeners.get(run_id, [])):
                await callback(value)
        payload = {"user_id": user_id, "session_id": session_id, "run_id": run_id, "message": message, "reference_date": reference_date}
        async def execute(value):
            return await self._answer_workflow(**value, progress=broadcast)
        event_token = execution_events.set({"run_id": run_id, "user_id": user_id, "progress": broadcast, "attempt_id": attempt_id or str(uuid.uuid4())})
        try:
            return await checkpointed(self.memory.path.parent / "workflow-checkpoints.sqlite", run_id, payload, execute, self._dispatch_stage)
        except asyncio.CancelledError:
            self.memory.fail(run_id, user_id, "The request was interrupted; retry to resume committed stages", "run_interrupted")
            raise
        except Exception as exc:
            # Checkpoint/open/resume failures can occur before workflow's own
            # try block. They must become durable errors as well.
            self.memory.fail(run_id, user_id, str(exc), getattr(exc, "code", "run_failed"), getattr(exc, "retry_after", None))
            if getattr(exc, "partial_envelope", None):
                return exc.partial_envelope
            raise
        finally:
            execution_events.reset(event_token)
            self._inflight.pop(run_id, None)
            self._listeners.pop(run_id, None)

    async def _answer_workflow(self, *, user_id, session_id, run_id, message, reference_date="2026-10-16", progress=None):
        self.validate_user(user_id)
        if not message.strip() or len(message) > 30000:
            raise ValueError("Message must contain 1–30000 characters")
        lock = self._locks.setdefault(session_id, asyncio.Lock())
        async with lock:
            existing = self.memory.begin(run_id, session_id, user_id, message)
            if existing.get("response") and existing.get("status") != "partial":
                return json.loads(existing["response"])
            attempts, usage, warnings = [0, False], [], []
            try:
                if progress:
                    await progress("Loading your conversation references and current shared knowledge")
                reference = self.memory.resolve_reference(user_id, message, session_id=session_id)
                normalized_message = re.sub(r"\b(?:dashbaord|dasbhbaord|dasboard)\b", "dashboard", message, flags=re.I)
                asset_ids, unknown_aliases, ambiguous_aliases = self.asset_references(message, self.context(user_id, session_id, run_id, reference_date)) if re.search(r"\bwell[\s-]*\d+\b", message, re.I) else ([], [], [])
                if unknown_aliases or ambiguous_aliases:
                    ctx = self.context(user_id, session_id, run_id, reference_date)
                    envelope = self._empty(ctx, "I could not uniquely match that well identifier to this dataset. Please choose the well ID before I build the dashboard.", [])
                    self.memory.finish(run_id, session_id, user_id, envelope, "clarification")
                    return envelope
                pending = normalized_message if re.search(r"\bdashboard\b|\btrend\b", normalized_message, re.I) else None
                old_focus = self.memory.focus(session_id, user_id)
                if pending and len(pending.split()) <= 6 and old_focus.get("pending_intent"):
                    pending = old_focus["pending_intent"]
                focus = self.memory.focus(session_id, user_id, asset_ids=asset_ids if asset_ids else None, pending_intent=pending, run_id=run_id)
                data_local_reference = bool(re.search(r"\bevery\b|\beach\b|\bat a well\b|\ball (?:our )?(?:wells|assets|reports)\b|\bour (?:wells|assets|field|reservoir)\b|\boperator notes?\b", normalized_message, re.I))
                use_focus = not asset_ids and bool(re.search(r"\bdashboard\b|\btrend\b|\bit\b|\bthat well\b", normalized_message, re.I)) and not data_local_reference and not re.search(r"fleet|all assets|all wells|how many|yesterday|we discussed", normalized_message, re.I)
                if use_focus and focus["asset_ids"]:
                    asset_ids = focus["asset_ids"]
                    reference = {"status": "resolved", "entity_ids": asset_ids, "event_ids": [], "source_receipt": "private-session-focus", "intent": focus.get("pending_intent")}
                subjects = list(dict.fromkeys(asset_ids + re.findall(r"T\d{3}", message, re.I)))
                references_requested = not subjects and bool(re.search(r"we (?:discussed|talked|looked at)|(?:earlier|previous|last|first) (?:conversation|chat|question|discussion)|wells? from (?:our )?(?:earlier|previous)", message, re.I))
                rank_followup = bool(re.search(r"\b(?:which|choose|pick|select)\s+(?:three|\d+)\s+(?:would you|from (?:those|that)|of those)", message, re.I)) and reference.get("status") == "resolved" and not data_local_reference
                if rank_followup:
                    references_requested = True
                if use_focus and asset_ids:
                    references_requested = True
                if asset_ids and focus.get("pending_intent"):
                    reference = {"status": "resolved", "entity_ids": asset_ids, "event_ids": [], "source_receipt": "private-session-focus", "intent": focus["pending_intent"]}
                    references_requested = True
                initial = await self._stage("read_context", {"user_id": user_id, "session_id": session_id, "run_id": run_id, "message": message, "reference_date": reference_date, "subjects": subjects})
                ctx, pack, authority = initial["context"], initial["memory"], initial["authority"]
                pack = attach_reference(pack, reference if references_requested else {"status": "not_requested"})
                pack = await self._fit_memory(pack)
                if references_requested and reference["status"] in {"absent", "ambiguous"}:
                    envelope = self._empty(ctx, "I do not have that earlier well discussion for your user. Please provide the well IDs or select your own earlier conversation.", ["Private reference absent; another user's history was not searched."])
                    if reference["status"] == "ambiguous":
                        envelope["narrative"] = "Your history contains several possible wells or incidents. Which well and incident do you mean?"
                    self.memory.finish(run_id, session_id, user_id, envelope, "clarification")
                    return envelope
                subjects += reference.get("entity_ids", []) if references_requested else []
                catalog = self.provider.catalog()
                model_catalog = {k: v for k, v in catalog.items() if k in {"provider_id", "collections", "metrics", "metric_descriptions", "group_by", "filters", "query_schema", "query_examples", "examples", "limits"}}
                plan_payload = {"request": message, "trusted_context": ctx, "memory": {"long_term": pack["long_term"], "short_term": pack["short_term"]},
                                "provider_catalog": model_catalog, "retrieved_context": initial["directories"]}
                if progress:
                    await progress("Planning scoped data queries and checking useful remembered facts")
                greeting = bool(re.fullmatch(r"\s*(?:hello|hi|hey|good morning|good afternoon|who are you|what can you do)[\s.!?]*", message, re.I))
                purpose = "greeting" if greeting else "planner"
                if greeting:
                    plan_payload = {k: v for k, v in plan_payload.items() if k in {"request", "trusted_context", "memory"}}
                plan, reply = await self._validated_model(purpose, plan_payload, PlannerOutput, attempts)
                branch = self.memory.branch(session_id, user_id)
                reused_receipts = []
                if branch and branch["mode"] == "regenerate" and branch["source_text"] == message:
                    reused_receipts = self.memory.receipts_for_run(user_id, branch["source_run_id"])
                    plan.memory_proposals = []
                explicit_visuals = [kind for pattern, kind in [
                    (r"\bstatus card\b", "status"), (r"\bline chart\b", "line"),
                    (r"\bbar chart\b", "bar"), (r"\bheatmap\b", "heatmap"),
                    (r"\bmap\b", "map"), (r"\btable\b", "table"), (r"\bdiagram\b", "diagram")]
                    if re.search(pattern, message, re.I)]
                if explicit_visuals:
                    plan.requested_visuals = explicit_visuals
                if re.search(r"\bwhere\b|\blocations?\b", message, re.I) and "map" not in plan.requested_visuals:
                    plan.requested_visuals.append("map")
                usage.append({"stage": purpose, "usage": reply.usage, "call_id": reply.call_id, "live": reply.live})
                if plan.title and self.memory.session(session_id, user_id)["completed"] == 0:
                    self.memory.rename_session(session_id, user_id, plan.title, manual=False)
                if greeting and plan.direct_response:
                    envelope = self._empty(ctx, plan.direct_response, [])
                    envelope["generation"] = {"status": "complete", "model": getattr(self.model, "model_id", MODEL), "calls": usage, "live": reply.live}
                    envelope["budget"] = {**pack["accounting"], "retrieved_context": 0, "retrieved_cap": 2000, "content_cap": 5000}
                    self.memory.finish(run_id, session_id, user_id, envelope, "greeting")
                    return envelope
                plan.queries = [normalize_relative_window(q, message, reference_date) for q in plan.queries]
                global_scope = bool(re.search(r"across (?:the )?(?:whole|entire) (?:field|fleet)|across all areas|not (?:just|only) my (?:area|team)|beyond my area",message,re.I)) or bool(re.search(r"\ball (?:our )?(?:wells|assets)\b",message,re.I) and not re.search(r"\bin my (?:area|team)\b",message,re.I))
                explicit_area = any(str(a.get("name","")).casefold() in message.casefold() or str(a.get("area_id","")).casefold() in message.casefold() for a in initial["directories"].get("areas",[]) if a.get("name") and a.get("area_id"))
                for query in plan.queries:
                    filters = query.setdefault("filters", {})
                    if isinstance(filters,dict) and global_scope and not explicit_area:
                        filters.pop("area_id",None);filters.pop("team_id",None)
                        if not asset_ids and not references_requested:
                            filters.pop("asset_id",None);filters.pop("asset_ids",None)
                    if isinstance(filters, dict) and not global_scope and re.search(r"\bmy (?:area|team)\b", message, re.I) and ctx.get("user_team_id"):
                        assigned = [a["area_id"] for a in initial["directories"].get("areas", []) if a.get("team_id") == ctx["user_team_id"]]
                        if len(assigned) == 1:
                            filters["area_id"] = assigned[0]
                        else:
                            filters["team_id"] = ctx["user_team_id"]
                        if not asset_ids and not references_requested:
                            filters.pop("asset_id",None);filters.pop("asset_ids",None)
                    reference_ids = reference.get("entity_ids", []) if references_requested and reference.get("status") == "resolved" else []
                    if isinstance(filters, dict) and reference_ids and not asset_ids and query.get("collection") in {"assets","inspections","maintenance","context_notes","regulatory_events"}:
                        filters.pop("asset_id", None)
                        filters["asset_ids"] = reference_ids
                    if asset_ids and isinstance(filters, dict) and query.get("collection") in {"assets", "inspections", "maintenance", "context_notes", "regulatory_events"}:
                        if not re.search(r"compare|versus|\bfleet\b|all assets|all wells", message, re.I):
                            filters.pop("asset_id", None)
                            filters["asset_ids"] = asset_ids
                    if not query.get("metric") or not query.get("collection"):
                        raise ModelUnavailable("unsupported_plan", "The model query omitted an explicit collection/metric; no default status query was executed")
                    if query["metric"] not in catalog.get("metrics", []) or query["collection"] not in catalog.get("collections", []):
                        raise ModelUnavailable("unsupported_plan", "The model query selected an operation outside this provider catalog")
                rank_limit = re.search(r"\b(?:top|which|the)\s+(\d+|three)\s+(?:wells|assets)\b", message, re.I) or (re.search(r"\b(?:which|choose|pick|select)\s+(three|\d+)\b",message,re.I) if rank_followup else None)
                if rank_limit and (rank_followup or re.search(r"most|highest|longest|\btop\b", message, re.I)):
                    requested_limit = 3 if rank_limit[1].casefold() == "three" else int(rank_limit[1])
                    if 1 <= requested_limit <= 100:
                        for query in plan.queries:
                            if query["metric"] in {"downtime_days", "maintenance_cost_usd", "spill_count", "spill_volume_bbl", "corrective_count", "repair_candidates"}:
                                query["limit"] = min(int(query.get("limit", requested_limit)), requested_limit)
                prose_request = bool(re.search(r"\breports?\b|\bSOP\b|\bprocedures?\b", message, re.I))
                prose_planned = bool(plan.evidence_searches) or any(q.get("collection") == "maintenance" for q in plan.queries)
                if prose_request and not prose_planned and not plan.memory_proposals:
                    raise ModelUnavailable("unsupported_plan", "This request needs report/procedure evidence; a generic status query cannot answer it")
                if plan.reference_text and not subjects and not data_local_reference and (references_requested or reference.get("status") == "resolved"):
                    references_requested = True
                    reference = self.memory.resolve_reference(user_id, plan.reference_text, session_id=session_id)
                    if reference["status"] != "resolved":
                        text = "I do not have a unique earlier well/incident reference for your user. Please name the well or incident."
                        envelope = self._empty(ctx, text, ["Private reference " + reference["status"]])
                        self.memory.finish(run_id, session_id, user_id, envelope, "clarification")
                        return envelope
                    for query in plan.queries:
                        filters = query.setdefault("filters", {})
                        if isinstance(filters, dict) and not any(k in filters for k in ("asset_id", "asset_ids", "area_id")):
                            filters["asset_ids"] = reference["entity_ids"]
                if references_requested and reference["status"] == "resolved":
                    for query in plan.queries:
                        filters = query.setdefault("filters", {})
                        if isinstance(filters, dict) and not any(k in filters for k in ("asset_id", "asset_ids", "area_id")):
                            filters["asset_ids"] = reference["entity_ids"]
                if plan.clarification and not plan.queries and not plan.memory_proposals:
                    envelope = self._empty(ctx, plan.clarification, [])
                    envelope["generation"] = {"calls": usage, "status": "clarification"}
                    self.memory.finish(run_id, session_id, user_id, envelope, "clarification")
                    return envelope
                # Generic domain safety: a claimed operational state needs its
                # effective observation, and corrections need the original target.
                # These use only advertised public query primitives, never storage.
                for draft in plan.memory_proposals:
                    if not draft.subject_ids or draft.subject_kind != "asset":
                        continue
                    if draft.kind == "correction" and not plan.queries and "records" in catalog.get("metrics", []):
                        query = {"collection": "inspections", "metric": "records", "filters": {"asset_ids": draft.subject_ids}, "limit": 100}
                        hint = re.search(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*(?:\s+(20\d{2}))?", message, re.I)
                        if hint:
                            import datetime
                            month = datetime.datetime.strptime(hint[2][:3].title(), "%b").month
                            date = datetime.date(int(hint[3] or reference_date[:4]), month, int(hint[1])).isoformat()
                            query.update(start=date, end=date)
                        if draft.target_record_id:
                            query["filters"]["inspection_id"] = draft.target_record_id
                        plan.queries.append(query)
                    current_claim = draft.kind in {"observation", "hypothesis"} or draft.kind == "plan" and draft.planned_start and draft.planned_start <= reference_date
                    if current_claim and not plan.queries and "status" in catalog.get("metrics", []):
                        plan.queries.append({"collection": "assets", "metric": "status", "filters": {"asset_ids": draft.subject_ids}, "limit": 100})
                # Read original targets through public query plans before formal writes.
                raw_results = []
                for query in plan.queries:
                    safe_query = dict(query)
                    safe_query["input_text"] = message[:1000]
                    try:
                        raw_results.append(await self._stage("query_records", {"plan": safe_query, "context": ctx, "authority": authority}))
                    except (RetrievalError, ValueError) as exc:
                        warnings.append(f"Query unavailable: {getattr(exc, 'code', 'invalid_query')}: {str(exc)}")
                status_rows = [row for raw in raw_results if isinstance(raw.get("operation"),dict) and raw["operation"].get("metric") == "status" for row in raw.get("rows", []) if "producing" in row]
                focus = list(dict.fromkeys(row["asset_id"] for row in status_rows
                    if row.get("asset_id") and (row.get("producing") is False or len(status_rows) == 1)))
                # A small status investigation needs attributed operating notes
                # and current work as well as the inspection. Resolve entities
                # from actual tool rows, never from generated causes.
                if focus and len(focus) <= 12 and len(status_rows) <= 12:
                    for collection in ("context_notes", "maintenance"):
                        if collection not in catalog.get("collections", []) or any(q.get("collection") == collection for q in plan.queries):
                            continue
                        contextual = {"collection": collection, "metric": "records", "filters": {"asset_ids": focus}, "end": reference_date, "limit": 100}
                        plan.queries.append(contextual)
                        try:
                            raw_results.append(await self._stage("query_records", {"plan": contextual, "context": ctx, "authority": authority}))
                        except (RetrievalError, ValueError) as exc:
                            warnings.append("Operational context unavailable: " + str(exc))
                receipts = reused_receipts
                for index, draft in enumerate(plan.memory_proposals):
                    if draft.kind in {"observation","work_context","guidance","hypothesis"} and asset_ids:
                        cited_assets, _, _ = self.asset_references(draft.source_quote, ctx)
                        if cited_assets or len(asset_ids) == 1:
                            draft = draft.model_copy(update={"subject_kind":"asset","subject_ids":cited_assets or asset_ids})
                    original = None
                    if draft.kind == "correction":
                        candidates = []
                        for result in raw_results:
                            for row in result.get("rows", []):
                                if row.get("inspection_id") and draft.field in row and (not draft.subject_ids or row.get("asset_id") in draft.subject_ids):
                                    candidates.append(row)
                        if draft.target_record_id:
                            candidates = [row for row in candidates if row["inspection_id"] == draft.target_record_id]
                        # A user can name an observation by asset/date without knowing
                        # its internal ID; resolve it from actual provider records only.
                        date_hint = re.search(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\b", message, re.I)
                        if date_hint:
                            import datetime
                            month = datetime.datetime.strptime(date_hint[2][:3].title(), "%b").month
                            candidates = [row for row in candidates if str(row.get("inspected_at", ""))[5:10] == f"{month:02d}-{int(date_hint[1]):02d}"]
                        unique = {row["inspection_id"]: row for row in candidates}
                        if len(unique) == 1:
                            row = next(iter(unique.values()))
                            draft = draft.model_copy(update={"target_record_id": row["inspection_id"]})
                            original = row.get(draft.field)
                    try:
                        receipts.append(await self._stage("write_knowledge", {"user_id": user_id, "run_id": run_id, "index": index, "draft": draft.model_dump(), "message": message, "original": original}))
                    except ValueError as exc:
                        warnings.append("Memory not committed: " + str(exc))
                # Canonical writes precede effective results; recompute all queries at one new revision.
                if receipts:
                    after_write = await self._stage("read_context", {"user_id": user_id, "session_id": session_id, "run_id": run_id, "message": message, "reference_date": reference_date, "subjects": subjects})
                    ctx, pack, authority = after_write["context"], after_write["memory"], after_write["authority"]
                    pack = attach_reference(pack, reference if references_requested else {"status": "not_requested"})
                    pack = await self._fit_memory(pack)
                    raw_results = []
                    for query in plan.queries:
                        try:
                            raw_results.append(await self._stage("query_records", {"plan": {**query, "input_text": message[:1000]}, "context": ctx, "authority": authority}))
                        except (RetrievalError, ValueError) as exc:
                            warnings.append("Post-save query unavailable: " + str(exc))
                if progress:
                    await progress("Calculating complete effective results and resolving their sources")
                results, evidence = {}, {}
                for raw in raw_results:
                    result = normalize_result(raw, ctx["knowledge_revision"], ctx["dataset_revision"])
                    results[result["result_set_id"]] = result
                    if raw.get("application_evidence"):
                        source = raw["application_evidence"]
                        evidence[source["id"]] = source
                    warnings.extend(result.get("warnings", []))
                    for handle in result["evidence_ids"]:
                        if handle in evidence:
                            continue
                        try:
                            if str(handle).startswith("memory:"):
                                fact = next((f for f in self.memory.facts(user_id, reference_date=reference_date) if f["id"] == handle), None)
                                if fact:
                                    evidence[handle] = self._memory_evidence(fact)
                            else:
                                evidence[handle] = normalize_evidence(await self._stage("read_evidence", {"handle": handle, "context": ctx}), handle)
                        except (RetrievalError, ValueError):
                            warnings.append(f"Source unavailable: {handle}")
                    result["evidence_ids"] = [e for e in result["evidence_ids"] if e in evidence]
                for receipt in receipts:
                    fact = next((f for f in self.memory.facts(user_id, reference_date=reference_date) if f["id"] == receipt["id"]), None)
                    if fact:
                        evidence[fact["id"]] = self._memory_evidence(fact)
                loaded_memory_ids = {f["id"] for key in ("private_capsule", "private_detail", "shared_detail") for f in pack["long_term"].get(key, []) if "id" in f}
                for fact in self.memory.facts(user_id, subjects=subjects or None, reference_date=reference_date):
                    if fact["id"] in loaded_memory_ids:
                        evidence[fact["id"]] = self._memory_evidence(fact)
                for search in plan.evidence_searches:
                    search = search.model_dump(exclude_none=True) if hasattr(search, "model_dump") else search
                    try:
                        terms = search if isinstance(search, str) else search.get("terms") or search.get("query") or ""
                        filters = {k: search[k] for k in ("asset_id", "kind") if isinstance(search, dict) and k in search}
                        found = await self._stage("search_evidence", {"terms": terms, "context": ctx, "filters": {"limit": 6, "budget": 2000, **filters}})
                        warnings.extend(found.get("warnings", []))
                        for raw in found.get("items", found.get("results", [])):
                            source = normalize_evidence(raw)
                            evidence[source["id"]] = source
                    except (RetrievalError, ValueError) as exc:
                        warnings.append("Evidence search unavailable: " + str(exc))
                unavailable_draft = bool(plan.direct_response and not results and not evidence and not plan.queries and not plan.evidence_searches and re.search(r"not available|not provided|not supplied|unavailable|cannot (?:calculate|determine|measure)|does not (?:include|provide|contain)|no .{0,50}(?:data|measurements|records|series)", plan.direct_response, re.I))
                if unavailable_draft:
                    capability_id = "app:capability:" + str(ctx["dataset_revision"])
                    excerpt = "Active supplied-data query capabilities: " + ", ".join(catalog.get("metrics",[])) + ". Collections: " + ", ".join(catalog.get("collections",[])) + ". A field rating or pressure test is not a measured reservoir-pressure series; spill volume and thermal production status are not measured produced-oil volume. Missing operations must not be replaced by such proxies."
                    years = list(dict.fromkeys(re.findall(r"\b20\d{2}\b",message)))
                    if years:excerpt += " Requested year scope: " + ", ".join(years) + "."
                    if asset_ids:excerpt += " Requested catalog-resolved assets: " + ", ".join(asset_ids) + "."
                    evidence[capability_id] = {"id":capability_id,"source_id":capability_id,"source_kind":"dataset_capabilities","title":"Supplied data fields and supported measurements","excerpt":excerpt,"dataset_revision":ctx["dataset_revision"]}
                self._private_presentation(results, pack)
                evidence_pack, evidence_accounting = pack_evidence(results, evidence, receipts, warnings, reference_date=reference_date, byte_cap=8000 if hasattr(self.model, "count_tokens") else 2000)
                evidence_pack["summaries"] = [{"result_set_id": r["result_set_id"], "summary": r["summary"]} for r in results.values() if r.get("summary")]
                evidence_pack, measured_evidence = await fit_section(evidence_pack, 2000, getattr(self.model, "count_tokens", None), "evidence", self._quota_wait)
                evidence_accounting.update(retrieved_context=measured_evidence["count"], method=measured_evidence["method"], token_fit_omitted=measured_evidence["omitted_items"], partial_evidence=evidence_accounting["partial_evidence"] or measured_evidence["omitted_items"] > 0)
                # Current shared/private context may support a sourced prose answer
                # without a numeric result or a mandatory chart.
                save_only = bool(receipts) and not results and not plan.queries and not plan.evidence_searches
                validated_view = False
                if save_only or not results and not evidence:
                    if receipts:
                        names = {u["user_id"]: u["name"] for u in self.users()}
                        text = " ".join(f"Saved {r['scope']} {r['statement']} (author {names.get(r['author_user_id'],r['author_user_id'])}, {r['status']})." for r in receipts)
                    elif warnings:
                        text = "I could not produce a supported data answer. " + " ".join(warnings)
                    else:
                        text = "Please specify the well, incident, period or comparison you want me to inspect."
                    envelope = self._empty(ctx, text, warnings)
                    envelope["evidence"] = evidence
                else:
                    if progress:
                        await progress("Preparing the evidence-grounded answer and inline panels")
                    payload = {"request": message, "trusted_context": ctx,
                               "memory": {"long_term": pack["long_term"], "short_term": pack["short_term"]},
                               "evidence_pack": evidence_pack,
                               "requested_visuals": plan.requested_visuals}
                    try:
                        view, answer_reply = await self._validated_model("maker", payload, ViewPlan, attempts)
                        usage.append({"stage": "maker", "usage": answer_reply.usage, "call_id": answer_reply.call_id, "live": answer_reply.live})
                        try:
                            async with self._track_stage("validation"):
                                envelope = self._assemble(ctx, run_id, view, results, evidence, warnings, plan.requested_visuals, {**evidence_pack, "memory": pack["long_term"]})
                        except ModelUnavailable as grounding_error:
                            view, repair_reply = await self._repair_grounding(grounding_error, view, payload, attempts)
                            usage.append({"stage":"grounding_repair","usage":repair_reply.usage,"call_id":repair_reply.call_id,"live":repair_reply.live})
                            async with self._track_stage("validation"):
                                envelope = self._assemble(ctx, run_id, view, results, evidence, warnings, plan.requested_visuals, {**evidence_pack,"memory":pack["long_term"]})
                        validated_view = True
                    except ModelUnavailable as exc:
                        if not results:
                            raise
                        text = "Partial answer: verified data is shown below. The explanation could not be completed because " + ("the model quota is temporarily exhausted." if exc.code == "provider_rate_limited" else "the generated response did not complete or pass its evidence checks.")
                        counts = [r for r in results.values() if (r.get("operation") or {}).get("metric") == "count" and len(r.get("rows", [])) == 1 and isinstance(r["rows"][0].get("count"), (int, float))]
                        if counts:
                            count = counts[0]
                            collection = (count.get("operation") or {}).get("collection", "records").replace("_", " ")
                            text = f"Verified data: {count['rows'][0]['count']} matching {collection} [{count['evidence_ids'][0]}]. " + text
                        envelope = self._empty(ctx, text, warnings + ["Explanation unavailable: " + exc.code])
                        envelope.update(results=results, evidence=evidence)
                        envelope["blocks"] = self._verified_blocks(run_id, results, plan.requested_visuals)
                        if not envelope["blocks"]:
                            complete_zero = all((r.get("coverage") or {}).get("matching") == 0 and (r.get("coverage") or {}).get("unknown") == 0 for r in results.values()) and not warnings
                            envelope["data_state"] = "complete_zero" if complete_zero else "unknown"
                            envelope["narrative"] = "No records matched the selected query scope. Check the well and date filters." if complete_zero else "I could not establish data for this selection. Please confirm the well and date range."
                            # No verified display block was established. Keep canonical
                            # tool results in the run trace, not the unverified UI payload.
                            envelope["results"] = {}
                        envelope["generation"] = {"status": "partial", "model": getattr(self.model, "model_id", MODEL), "live": False,
                            "verified_tool_data": bool(envelope["blocks"]), "explanation_error_code": exc.code, "retry_after": exc.retry_after, "calls": usage}
                        envelope["budget"] = {**pack["accounting"], **evidence_accounting, "content_cap": 5000}
                        async with self._track_stage("publish"):
                            self.memory.finish(run_id, session_id, user_id, envelope, plan.intent, status="partial")
                        exc.partial_envelope = envelope
                        # Keep the failed workflow checkpoint resumable. The API
                        # receives verified partial data from the outer boundary.
                        raise
                if self.memory.head() != ctx["knowledge_revision"]:
                    envelope["warnings"].append("Knowledge changed during generation; this entire answer is a historical snapshot. Refresh to use current knowledge.")
                    envelope["snapshot_status"] = "historical"
                envelope["generation"] = {"status": "complete" if validated_view or results or receipts else "partial", "model": getattr(self.model, "model_id", MODEL), "calls": usage,
                                          "provider": getattr(self.model, "provider", "injected-test"),
                                          "foreground_attempts": attempts[0], "live": bool(usage) and all(u["live"] for u in usage)}
                envelope["budget"] = {**pack["accounting"], **evidence_accounting,
                                      "content_cap": 5000, "instructions_and_catalog_bytes": estimate(load_prompt("planner")) + estimate(catalog),
                                      "current_request_bytes_separate": estimate(message), "output_reserve": "Local bounded JSON/field limits; provider output limit unverified, observed usage recorded"}
                async with self._track_stage("publish"):
                    self.memory.finish(run_id, session_id, user_id, envelope, plan.intent)
                self._schedule_summary(user_id, session_id)
                return envelope
            except Exception as exc:
                self.memory.fail(run_id, user_id, str(exc), getattr(exc, "code", "run_failed"), getattr(exc, "retry_after", None))
                raise

    def _memory_evidence(self, fact):
        author = next((u["name"] for u in self.users() if u["user_id"] == fact["author_user_id"]), fact["author_user_id"])
        return {"id": fact["id"], "title": fact["kind"].title() + " reported by " + author,
                "source_kind": "shared_knowledge" if fact["scope"] == "shared" else "private_memory",
                "source_id": fact["id"], "excerpt": fact["statement"] + " [" + fact["status"] + "]",
                "author": author, "source_time": fact["created_at"]}

    def _verified_blocks(self, run_id, results, requested):
        blocks = []
        seen = set()
        for index, result in enumerate(results.values()):
            if not result.get("rows"):
                continue
            signature = json.dumps([result.get("operation"), result.get("columns"), result.get("rows")], sort_keys=True, default=str)
            if signature in seen:
                continue
            seen.add(signature)
            keys = {c["key"] for c in result["columns"]}
            kind, encoding = "table", {}
            if "map" in requested and {"lat", "lon"}.issubset(keys):
                kind, encoding = "map", {"latitude": "lat", "longitude": "lon", "label": "asset_id"}
                if "producing" in keys:
                    encoding["value"] = "producing"
            elif len(result["rows"]) == 1 and {"producing", "delta_c", "asset_id"}.issubset(keys):
                kind, encoding = "status", {"label": "asset_id", "value": "delta_c", "status": "producing"}
            if result.get("evidence_ids"):
                blocks.append({"id": f"{run_id}:verified:{index}", "type": kind, "title": "Verified data — explanation incomplete",
                               "result_set_id": result["result_set_id"], "evidence_ids": result["evidence_ids"][:8], "encoding": encoding, "span": 2})
        return blocks

    def _empty(self, context, text, warnings):
        safe_warnings = []
        for warning in warnings:
            if warning.startswith(("Query unavailable", "Post-save query unavailable")):
                warning = "Part of the requested data could not be retrieved."
            elif warning.startswith(("Evidence search unavailable", "Source unavailable")):
                warning = "Some supporting documents could not be opened."
            elif warning.startswith("Explanation unavailable"):
                warning = "The explanation is incomplete; the panels contain verified records."
            elif warning.startswith("Memory not committed"):
                warning = "A proposed memory could not be verified and was not saved."
            if warning not in safe_warnings:
                safe_warnings.append(warning)
        return {"schema_version": "1.0", "answer_id": context["run_id"], "thread_id": context["thread_id"],
                "user_id": context["user_id"], "dataset_namespace": context["dataset_namespace"],
                "dataset_revision": context["dataset_revision"], "knowledge_revision": context["knowledge_revision"],
                "reference_date": context["reference_date"], "narrative": text, "blocks": [],
                "results": {}, "evidence": {}, "warnings": safe_warnings, "sample": False}

    def _assemble(self, context, run_id, view, results, evidence, warnings, requested, evidence_pack=None):
        claims = [c.model_dump() if hasattr(c, "model_dump") else c for c in view.claims]
        visible = evidence_pack or {"results": list(results.values()), "evidence": list(evidence.values())}
        grounding_values = [r.get("rows", []) for r in visible.get("results", [])]
        grounding_values += [{"bounds": r.get("bounds")} for r in visible.get("results", [])]
        grounding_values += [{"coverage": r.get("coverage"), "summary": r.get("summary"), "assessment_counts": r.get("assessment_counts")} for r in visible.get("results", [])]
        grounding_values += [{"title": e.get("title"), "excerpt": e.get("excerpt")} for e in visible.get("evidence", [])]
        for key in ("private_capsule", "private_detail", "shared_detail"):
            grounding_values += [{k: f.get(k) for k in ("statement", "valid_from", "valid_to")} for f in visible.get("memory", {}).get(key, [])]
        grounding = json.dumps(grounding_values, ensure_ascii=False, default=str)
        narrative_refs = re.findall(r"\[([^\]\s]+)\]", view.narrative)
        if any(ref not in evidence for ref in narrative_refs):
            raise ModelUnavailable("invalid_narrative_citation", "Narrative cited a source that does not exist")
        from decimal import Decimal, InvalidOperation
        def numbers(text):
            result = set()
            # ISO's date/time separator is formatting, not part of the hour.
            # Preserve the same source value when prose writes "at09:45".
            text = re.sub(r"(?<=\d)T(?=\d{2}:)", " ", text)
            for token in re.findall(r"(?<!\w)[+-]?\d[\d,]*(?:\.\d+)?", text):
                try:
                    result.add(Decimal(token.replace(",", "")))
                except InvalidOperation:
                    pass
            return result
        allowed_numbers = numbers(grounding)
        prose_without_citations = re.sub(r"\[[^\]]+\]", "", view.narrative + " " + " ".join(str(c.get("text", "")) for c in claims))
        if not numbers(prose_without_citations).issubset(allowed_numbers):
            error = ModelUnavailable("unsupported_narrative_number", "Narrative includes a numeric value absent from its visible evidence")
            error.validation_details = {"invalid_numbers":[str(v) for v in numbers(prose_without_citations)-allowed_numbers][:20],"visible_numbers":[str(v) for v in sorted(allowed_numbers)][:40]}
            raise error
        populations = [r for r in results.values() if (r.get("operation") or {}).get("metric") == "status" and r.get("rows") and len(r["rows"]) == (r.get("coverage") or {}).get("matching")]
        if len(populations) == 1:
            expected = len({r.get("asset_id") for r in populations[0]["rows"] if r.get("asset_id")})
            names = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}
            for match in re.finditer(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:(?:total|matching|primary|affected)\s+)?(?:wells|assets)\b", view.narrative, re.I):
                count = names.get(match[1].lower(), int(match[1]) if match[1].isdigit() else -1)
                if expected and count != expected and not re.search(r"example|such as|including", view.narrative[max(0,match.start()-25):match.start()], re.I):
                    error = ModelUnavailable("unsupported_population_count","Narrative cardinality disagrees with the complete matching result")
                    error.validation_details = {"claimed":count,"matching":expected,"result_set_id":populations[0]["result_set_id"]}
                    raise error
        for claim in claims:
            refs = claim.get("evidence_ids", [])
            if claim.get("kind", "fact") == "fact" and not refs:
                raise ModelUnavailable("unsupported_claim", "A factual claim has no source reference")
            if any(ref not in evidence for ref in refs):
                raise ModelUnavailable("invalid_claim_citation", "Claim cited an unavailable source")
            for value in claim.get("value_refs", []):
                result = results.get(value.get("result_set_id"))
                index = value.get("row_index")
                if not result or not isinstance(index, int) or not 0 <= index < len(result["rows"]) or value.get("column") not in result["rows"][index]:
                    raise ModelUnavailable("invalid_claim_value", "Claim referenced an unavailable exact result value")
        answer = self._empty(context, view.narrative, list(dict.fromkeys(warnings)))
        answer.update(results=results, evidence=evidence)
        answer["claims"] = claims
        blocks = []
        seen_blocks = set()
        for index, block in enumerate(view.blocks):
            result = results.get(block.result_set_id)
            if not result:
                raise ModelUnavailable("invalid_result_reference", "View plan referenced a result that does not exist")
            if not result.get("rows"):
                continue
            keys = {c["key"] for c in result["columns"]}
            if block.type == "status" and "producing" in keys:
                block.encoding["status"] = "producing"
                if "asset_id" in keys:
                    block.encoding["label"] = "asset_id"
                if "delta_c" in keys:
                    block.encoding["value"] = "delta_c"
            if block.type == "map" and (result.get("operation") or {}).get("metric") == "status" and "producing" in keys:
                block.encoding["value"] = "producing"
                if "asset_id" in keys:
                    block.encoding["label"] = "asset_id"
            if any(key not in keys for key in block.encoding.values()):
                raise ModelUnavailable("invalid_column_reference", "View plan referenced an unavailable result column")
            if block.type == "heatmap" and any(block.encoding.get(role) in {"lat", "lon", "latitude", "longitude"} for role in ("x", "y")):
                raise ModelUnavailable("invalid_visual_semantics", "Coordinates require a geographic map; the categorical heatmap needs actual categories")
            if any(e not in evidence for e in block.evidence_ids):
                raise ModelUnavailable("invalid_evidence_reference", "View plan cited an unavailable source")
            refs = block.evidence_ids or result["evidence_ids"][:8]
            if not refs:
                answer["warnings"].append("A panel was omitted because its source could not be resolved")
                continue
            signature = (block.type, block.result_set_id, json.dumps(block.encoding, sort_keys=True))
            if signature in seen_blocks:
                continue
            seen_blocks.add(signature)
            blocks.append({"id": run_id + ":block:" + str(index), **block.model_dump(), "evidence_ids": refs})
        if not blocks:
            for index, result in enumerate(results.values()):
                if result["evidence_ids"] and result.get("rows"):
                    blocks.append({"id": run_id + ":block:" + str(index), "type": "table", "title": "Verified result",
                                   "result_set_id": result["result_set_id"], "evidence_ids": result["evidence_ids"][:8], "encoding": {}, "span": 2})
        answer["blocks"] = blocks
        if requested and not all(kind in {b["type"] for b in blocks} for kind in requested):
            answer["warnings"].append("One or more requested visual kinds could not be validated; verified data remains available")
        return answer

    def _schedule_summary(self, user_id, session_id):
        task = asyncio.create_task(self._summarize(user_id, session_id))
        self._background.add(task)
        task.add_done_callback(self._background.discard)

    async def _summarize(self, user_id, session_id):
        # Durable raw records/receipts remain authoritative even if the background call fails.
        with self.memory.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE session_id=? AND user_id=? AND status='pending' ORDER BY target DESC LIMIT 1", (session_id, user_id)).fetchone()
            if not row:
                return
            job = dict(row)
            db.execute("UPDATE jobs SET status='running',attempts=attempts+1,updated_at=? WHERE id=?", (__import__('datetime').datetime.now().isoformat(), job["id"]))
            previous = db.execute("SELECT * FROM summaries WHERE session_id=? AND user_id=?", (session_id, user_id)).fetchone()
        try:
            history = self.memory.history(session_id, user_id)["messages"]
            completed = [m for m in history if m["role"] == "assistant" and m.get("status") != "error"][:job["target"]]
            already = previous["covered"] if previous else 0
            raw_by_run = {m["run_id"]: m["content"] for m in history if m["role"] == "user"}
            entries = [{"sequence": i + 1, "source_id": m["id"], "user": raw_by_run.get(m["run_id"], ""), "answer": m["content"]} for i, m in enumerate(completed) if i >= already]
            prefix = []
            for entry in entries:
                candidate = prefix + [entry]
                if estimate({"previous": previous["text"] if previous else "", "dialogue": candidate}) > 1000:
                    break
                prefix = candidate
            if not prefix:
                raise ValueError("Raw summary source needs smaller validated chunks; prior summary retained")
            covered = prefix[-1]["sequence"]
            summary_payload = {"owner": user_id, "previous": previous["text"] if previous else "", "dialogue": prefix, "target": covered}
            reply = await self.model.generate("summary", bind_prompt("summary", summary_payload), summary_payload, max_tokens=400)
            text = reply.data.get("summary")
            if not isinstance(text, str) or estimate(text) > 400 or int(reply.data.get("covered", -1)) != covered:
                raise ValueError("Summary output failed budget or coverage validation")
            with self.memory.connect() as db:
                current = db.execute("SELECT version FROM summaries WHERE session_id=?", (session_id,)).fetchone()
                expected = previous["version"] if previous else 0
                if (current[0] if current else 0) != expected:
                    raise ValueError("Stale summary job; newer projection retained")
                db.execute("INSERT INTO summaries VALUES(?,?,?,?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET version=excluded.version,covered=excluded.covered,text=excluded.text,manifest=excluded.manifest,updated_at=excluded.updated_at",
                           (session_id, user_id, expected + 1, covered, text, json.dumps([x["source_id"] for x in prefix]), __import__('datetime').datetime.now().isoformat()))
                db.execute("UPDATE jobs SET status=?,updated_at=? WHERE id=?", ("complete" if covered == job["target"] else "pending", __import__('datetime').datetime.now().isoformat(), job["id"]))
        except Exception as exc:
            with self.memory.connect() as db:
                db.execute("UPDATE jobs SET status='failed',error=?,updated_at=? WHERE id=?", (str(exc)[:300], __import__('datetime').datetime.now().isoformat(), job["id"]))
