import json
import uuid
import httpx
import pytest

from backend.app import create_app
from backend.chains.gemma import ModelReply
from backend.memory import MemoryStore


class IndependentProvider:
    """No SQLite/FTS/ingestion dependency: replacement seam regression fixture."""
    namespace = "test-field"
    provider_id = "independent-in-memory-provider"

    def catalog(self):
        return {"dataset_revision": "test-revision", "collections": ["assets", "users", "areas", "teams"], "metrics": ["status", "records"]}

    def query(self, plan, context, authority=None):
        assert context["dataset_namespace"] == self.namespace
        collection = plan.get("collection")
        if collection == "users":
            rows = [{"user_id": "A", "name": "User A", "role": "operator", "team_id": "T1"}, {"user_id": "B", "name": "User B", "role": "inspector", "team_id": "T2"}]
        elif collection in {"areas", "teams"}:
            rows = []
        else:
            value = 24.0
            for c in (authority or {}).get("corrections", []):
                if c["inspection_id"] == "I-X":
                    value = c["value"]
            rows = [{"asset_id": "WELL-X", "inspection_id": "I-X", "wellhead_temp_c": value, "producing": value >= 35}]
        columns = [{"key": k} for k in (rows[0] if rows else {})]
        for row in rows:
            row["evidence_refs"] = ["source:real-test-record"]
        return {"result_set_id": "result:" + str(uuid.uuid4()), "dataset_revision": "test-revision", "knowledge_revision": context["knowledge_revision"],
                "columns": columns, "rows": rows, "coverage": {"matching": len(rows), "evaluated": len(rows), "unknown": 0}}

    def evidence(self, handle, context):
        return {"id": handle, "source_id": handle, "source_kind": "synthetic_unit_fixture", "excerpt": "Explicit test record", "title": "Test record"}

    def search(self, terms, context, **filters):
        return {"items": []}


class FixedModel:
    configured = True

    async def generate(self, purpose, system, payload, **kwargs):
        if purpose == "planner":
            data = {"title": "Asset status", "queries": [{"collection": "assets", "metric": "status"}], "requested_visuals": ["status"]}
        elif purpose == "maker":
            result = payload["evidence_pack"]["result_catalog"][0]
            data = {"narrative": "The provider returned the current effective status [source:real-test-record].", "blocks": [{"type": "status", "title": "Effective status", "result_set_id": result["id"], "evidence_ids": result["evidence_ids"], "encoding": {"value": "producing"}}]}
        else:
            data = {"summary": "Prior asset discussion", "covered": payload.get("target", 0)}
        return ModelReply(data, {"test": True}, live=False)


@pytest.mark.asyncio
async def test_sessions_agui_and_provider_replacement(tmp_path):
    provider = IndependentProvider()
    app = create_app(provider=provider, memory=MemoryStore(tmp_path / "memory.sqlite", provider.namespace), model=FixedModel(), runtime_dir=tmp_path, admin_enabled=True, admin_token="local-admin-test")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/users")).json()["users"][0]["user_id"] == "A"
        assert (await client.get("/api/sessions")).status_code == 401
        headers = {"X-User-Id": "A"}
        session = (await client.post("/api/sessions", headers=headers, json={"id": "conversation"})).json()
        assert session["id"] == "conversation"
        assert (await client.get("/api/sessions/conversation/messages", headers={"X-User-Id": "B"})).status_code == 404
        response = await client.post("/api/agent", headers={**headers, "X-Session-Id": "conversation"}, json={"threadId": "conversation", "runId": "run", "messages": [{"role": "user", "content": "Show WELL-X status"}]})
        assert response.status_code == 200
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
        assert events[0]["type"] == "RUN_STARTED"
        assert events[-1]["type"] == "RUN_FINISHED", response.text
        stages = [e["value"] for e in events if e["type"] == "CUSTOM" and e.get("value", {}).get("stage_id")]
        assert {"planner", "query_records", "maker", "validation", "publish"}.issubset({e["stage"] for e in stages})
        assert all(e["timestamp"] and e["status"] in {"started", "completed", "failed"} for e in stages)
        assert all(not {"payload", "sql", "prompt", "source_quote"}.intersection(e) for e in stages)
        args = next(e for e in events if e["type"] == "TOOL_CALL_ARGS")
        envelope = json.loads(args["delta"])["envelope"]
        assert envelope["sample"] is False
        assert envelope["generation"]["live"] is False  # no unit fixture claims to be live Gemma
        assert envelope["blocks"][0]["result_set_id"] in envelope["results"]
        assert envelope["budget"]["long_term"] <= 2000
        assert envelope["budget"]["short_term"] <= 1000
        assert envelope["budget"]["retrieved_context"] <= 2000
        history = (await client.get("/api/sessions/conversation/messages", headers=headers)).json()
        assert [m["role"] for m in history["messages"]] == ["user", "assistant"]
        assert history["messages"][0]["stages"] == stages
        assert (await client.get("/api/answers/run", headers={"X-User-Id": "B"})).status_code == 404
        assert (await client.get("/api/admin/memory", headers=headers)).status_code == 403
        assert (await client.get("/api/admin/memory", headers={"X-Admin-Token": "local-admin-test"})).status_code == 200
        assert (await client.patch("/api/sessions/conversation", headers=headers, json={"title": "Custom"})).json()["title"] == "Custom"
        assert (await client.get("/api/sessions?q=Custom", headers=headers)).json()["total"] == 1
        assert (await client.delete("/api/sessions/conversation", headers=headers)).status_code == 204
        assert (await client.get("/api/sessions/conversation/messages", headers=headers)).status_code == 404


@pytest.mark.asyncio
async def test_evidence_only_sop_answer_and_citation_validation(tmp_path):
    class EvidenceProvider(IndependentProvider):
        def search(self, terms, context, **filters):
            return {"items": [{"id": "source:sop", "source_id": "sop", "kind": "sop", "section": "Notice", "text": "Written notice is required within 24 hours."}]}
    class EvidenceModel(FixedModel):
        async def generate(self, purpose, system, payload, **kwargs):
            if purpose == "planner":
                data = {"queries": [], "evidence_searches": ["written notice"]}
            else:
                data = {"narrative": "The supplied procedure requires written notice within 24 hours [source:sop].", "blocks": [],
                        "claims": [{"text": "Written notice within 24 hours", "kind": "fact", "evidence_ids": ["source:sop"], "value_refs": []}]}
            return ModelReply(data, {}, live=False)
    provider = EvidenceProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    from backend.chains.service import CopilotService
    service = CopilotService(provider, memory, EvidenceModel())
    memory.create_session("A", "sop")
    answer = await service.answer(user_id="A", session_id="sop", run_id="sop-run", message="What is the supplied written notice procedure?")
    assert "24 hours" in answer["narrative"] and answer["blocks"] == []
    assert answer["generation"]["status"] == "complete"
    assert answer["claims"][0]["evidence_ids"] == ["source:sop"]
    from backend.contracts import ViewPlan, ModelUnavailable
    with pytest.raises(ModelUnavailable, match="does not exist"):
        service._assemble(service.context("A", "sop", "bad"), "bad", ViewPlan(narrative="Claim [made-up]"), {}, answer["evidence"], [], [], {"evidence": []})
    with pytest.raises(ModelUnavailable, match="numeric"):
        service._assemble(service.context("A", "sop", "bad"), "bad", ViewPlan(narrative="The limit is 9999 hours [source:sop]."), {}, answer["evidence"], [], [], {"evidence": [{"id": "source:sop", "excerpt": "24 hours"}]})


@pytest.mark.asyncio
async def test_real_langgraph_resume_reuses_successful_model_stage(tmp_path):
    from backend.chains.service import CopilotService
    class CrashModel(FixedModel):
        def __init__(self, fail=False):
            self.fail, self.calls = fail, []
        async def generate(self, purpose, system, payload, **kwargs):
            self.calls.append(purpose)
            if purpose == "maker" and self.fail:
                raise RuntimeError("Injected model-stage failure")
            return await super().generate(purpose, system, payload, **kwargs)
    provider = IndependentProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    memory.create_session("A", "resume")
    first = CrashModel(True)
    with pytest.raises(RuntimeError, match="Injected"):
        await CopilotService(provider, memory, first).answer(user_id="A", session_id="resume", run_id="durable-run", message="Show WELL-X status")
    assert first.calls == ["planner", "maker"]
    second = CrashModel(False)
    answer = await CopilotService(provider, MemoryStore(memory.path, provider.namespace), second).answer(user_id="A", session_id="resume", run_id="durable-run", message="Show WELL-X status")
    assert second.calls == ["maker"]
    assert answer["blocks"] and memory.session("resume", "A")["completed"] == 1


@pytest.mark.asyncio
async def test_greeting_is_model_generated_without_query_results(tmp_path):
    from backend.chains.service import CopilotService
    class GreetingModel:
        configured = True
        async def generate(self, purpose, system, payload, **kwargs):
            assert purpose == "greeting"
            assert "provider_catalog" not in payload
            return ModelReply({"intent": "greeting", "direct_response": "Hello. I can help inspect well data with evidence. What would you like to check?"}, {}, live=False)
    provider = IndependentProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    memory.create_session("A", "greeting")
    answer = await CopilotService(provider, memory, GreetingModel()).answer(user_id="A", session_id="greeting", run_id="hello-run", message="hello")
    assert answer["narrative"].startswith("Hello") and answer["results"] == {} and answer["blocks"] == []
    assert answer["generation"]["calls"][0]["stage"] == "greeting"


@pytest.mark.asyncio
async def test_report_request_cannot_silently_become_status_query(tmp_path):
    from backend.chains.service import CopilotService
    from backend.contracts import ModelUnavailable
    provider = IndependentProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    memory.create_session("A", "report")
    with pytest.raises(ModelUnavailable, match="report/procedure evidence"):
        await CopilotService(provider, memory, FixedModel()).answer(user_id="A", session_id="report", run_id="bad-report", message="Find assets whose maintaince report found crude oil on the pad")
    history = memory.history("report", "A")["messages"]
    assert history[-1]["status"] == "error" and history[-1]["error_code"] == "unsupported_plan"


@pytest.mark.asyncio
async def test_paused_generation_preserves_question_without_model_call(tmp_path):
    class NeverModel:
        configured = True
        async def generate(self, *args, **kwargs):
            pytest.fail("Paused API must not start generation")
    provider = IndependentProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    app = create_app(provider=provider, memory=memory, model=NeverModel(), runtime_dir=tmp_path, live_enabled=False)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        health = (await client.get("/api/health")).json()
        assert health["data_ready"] is True and health["model_generation_enabled"] is False
        headers = {"X-User-Id": "A"}
        await client.post("/api/sessions", headers=headers, json={"id": "paused"})
        response = await client.post("/api/agent", headers=headers, json={"threadId": "paused", "runId": "paused-run", "message": "hello"})
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
        assert events[-1]["type"] == "RUN_ERROR" and events[-1]["code"] == "model_under_repair"
        history = memory.history("paused", "A")["messages"]
        assert history[0]["content"] == "hello" and history[1]["status"] == "error"
        assert memory.session("paused", "A")["completed"] == 0


@pytest.mark.asyncio
async def test_mid_dashboard_write_marks_entire_answer_historical(tmp_path):
    from backend.chains.service import CopilotService
    from backend.contracts import MemoryDraft
    provider = IndependentProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    class ConcurrentModel(FixedModel):
        async def generate(self, purpose, system, payload, **kwargs):
            if purpose == "maker":
                memory.commit_draft("B", "concurrent-write", 0,
                    MemoryDraft(kind="plan", scope="shared", subject_ids=["WELL-X"], statement="WELL-X planned maintenance.", source_quote="WELL-X planned maintenance."),
                    "WELL-X planned maintenance.")
            return await super().generate(purpose, system, payload, **kwargs)
    memory.create_session("A", "concurrent")
    answer = await CopilotService(provider, memory, ConcurrentModel()).answer(user_id="A", session_id="concurrent", run_id="concurrent-answer", message="Show WELL-X status")
    assert answer["snapshot_status"] == "historical"
    assert answer["knowledge_revision"] < memory.head()
    assert all(r["knowledge_revision"] == answer["knowledge_revision"] for r in answer["results"].values())
    assert any("historical snapshot" in warning for warning in answer["warnings"])


@pytest.mark.asyncio
async def test_checkpoint_start_failure_is_durable(tmp_path, monkeypatch):
    from backend.chains import service as module
    async def broken_checkpoint(*args, **kwargs):
        raise RuntimeError("Injected checkpoint open failure")
    monkeypatch.setattr(module, "checkpointed", broken_checkpoint)
    provider = IndependentProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    memory.create_session("A", "broken")
    with pytest.raises(RuntimeError, match="checkpoint"):
        await module.CopilotService(provider, memory, FixedModel()).answer(user_id="A", session_id="broken", run_id="broken-run", message="hello")
    history = memory.history("broken", "A")["messages"]
    assert history[-1]["status"] == "error" and "checkpoint open failure" in history[-1]["content"]


@pytest.mark.asyncio
async def test_deleted_conversation_run_id_cannot_reopen_private_checkpoint(tmp_path):
    from backend.chains.service import CopilotService
    from backend.memory.store import ScopeError
    provider = IndependentProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    service = CopilotService(provider, memory, FixedModel())
    memory.create_session("A", "reused-thread")
    await service.answer(user_id="A", session_id="reused-thread", run_id="old-private-run", message="Show WELL-X status")
    memory.delete_session("reused-thread", "A")
    memory.create_session("B", "reused-thread")
    with pytest.raises(ScopeError):
        await service.answer(user_id="B", session_id="reused-thread", run_id="old-private-run", message="Show WELL-X status")
    assert memory.history("reused-thread", "B")["messages"] == []


@pytest.mark.asyncio
async def test_background_summary_failure_keeps_projection_and_raw_archive(tmp_path):
    from backend.chains.service import CopilotService
    from backend.contracts import ModelUnavailable
    class FailedSummary:
        configured = True
        async def generate(self, purpose, system, payload, **kwargs):
            assert purpose == "summary"
            assert len(json.dumps({"previous": payload["previous"], "dialogue": payload["dialogue"]}, separators=(",", ":")).encode()) <= 1000
            raise ModelUnavailable("test_provider_failure", "Injected background failure")
    provider = IndependentProvider()
    memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    memory.create_session("A", "summary-thread")
    for i in range(10):
        memory.begin(f"summary-{i}", "summary-thread", "A", "Show this well")
        memory.finish(f"summary-{i}", "summary-thread", "A", {"narrative": "Historical answer", "results": {}, "reference_date": "2026-10-16"})
    with memory.connect() as db:
        db.execute("INSERT INTO summaries VALUES(?,?,?,?,?,?,?)", ("summary-thread", "A", 1, 1, "Existing navigation", "[]", "2026-10-16"))
    await CopilotService(provider, memory, FailedSummary())._summarize("A", "summary-thread")
    with memory.connect() as db:
        summary = db.execute("SELECT * FROM summaries WHERE session_id='summary-thread'").fetchone()
        assert summary["version"] == 1 and summary["text"] == "Existing navigation"
        assert db.execute("SELECT count(*) FROM jobs WHERE status='failed'").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 20
    assert memory.session("summary-thread", "A")["completed"] == 10


@pytest.mark.asyncio
async def test_partial_quota_answer_preserves_tools_and_resumes_failed_maker(tmp_path):
    from backend.chains.service import CopilotService
    from backend.contracts import ModelUnavailable
    class Limited(FixedModel):
        def __init__(self, fail): self.fail, self.calls = fail, []
        async def generate(self, purpose, system, payload, **kwargs):
            self.calls.append(purpose)
            if purpose == "maker" and self.fail:
                raise ModelUnavailable("provider_rate_limited", "Actual simulated quota failure", retry_after=20)
            return await super().generate(purpose, system, payload, **kwargs)
    provider = IndependentProvider();memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    memory.create_session("A", "partial")
    first = Limited(True)
    answer = await CopilotService(provider, memory, first).answer(user_id="A", session_id="partial", run_id="partial-run", message="Show WELL-X status")
    assert answer["generation"]["status"] == "partial" and answer["results"] and answer["blocks"]
    assert answer["sample"] is False and answer["generation"]["retry_after"] == 20
    second = Limited(False)
    completed = await CopilotService(provider, memory, second).answer(user_id="A", session_id="partial", run_id="partial-run", message="Show WELL-X status")
    assert second.calls == ["maker"]
    assert completed["generation"]["status"] == "complete"
    history = memory.history("partial", "A")["messages"]
    assert len(history) == 2 and history[1]["status"] == "complete"
    assert memory.session("partial", "A")["completed"] == 1


def test_iso_timestamp_hour_formatting_remains_grounded(tmp_path):
    from backend.chains.service import CopilotService
    from backend.contracts import ViewPlan
    provider = IndependentProvider();service = CopilotService(provider, MemoryStore(tmp_path / "memory.sqlite", provider.namespace), FixedModel())
    result = service._assemble(service.context("A", "test", "run"), "run", ViewPlan(narrative="Inspected on 2026-10-15 at 09:45:00Z [source:record]."), {},
        {"source:record": {"id": "source:record"}}, [], [], {"evidence": [{"id": "source:record", "excerpt": "Inspected 2026-10-15T09:45:00Z"}]})
    assert "09:45" in result["narrative"]


@pytest.mark.asyncio
async def test_concurrent_retry_attaches_to_same_inflight_run(tmp_path):
    import asyncio
    from backend.chains.service import CopilotService
    entered, release = asyncio.Event(), asyncio.Event()
    class Slow(FixedModel):
        def __init__(self): self.calls = []
        async def generate(self, purpose, system, payload, **kwargs):
            self.calls.append(purpose)
            if purpose == "planner":
                entered.set(); await release.wait()
            return await super().generate(purpose, system, payload, **kwargs)
    provider = IndependentProvider();memory = MemoryStore(tmp_path / "memory.sqlite", provider.namespace)
    memory.create_session("A", "coalesced");model = Slow();service = CopilotService(provider, memory, model)
    first = asyncio.create_task(service.answer(user_id="A", session_id="coalesced", run_id="first", client_message_id="one-user-message", message="Show WELL-X status"))
    await entered.wait()
    second = asyncio.create_task(service.answer(user_id="A", session_id="coalesced", run_id="second", client_message_id="one-user-message", message="Show WELL-X status"))
    await asyncio.sleep(0)
    release.set();answers = await asyncio.gather(first, second)
    assert model.calls == ["planner", "maker"]
    assert answers[0]["answer_id"] == answers[1]["answer_id"] == "first"
    assert len(memory.history("coalesced", "A")["messages"]) == 2

@pytest.mark.asyncio
async def test_grounding_repairs_once_without_fresh_queries(tmp_path):
    from backend.chains.service import CopilotService
    class RepairModel(FixedModel):
        def __init__(self):self.calls=[]
        async def generate(self,purpose,system,payload,**kwargs):
            self.calls.append(purpose)
            if purpose=='maker':
                result=payload['evidence_pack']['result_catalog'][0]
                return ModelReply({'narrative':'The reading is 9999 [source:real-test-record].','blocks':[{'type':'table','title':'Actual records','result_set_id':result['id'],'evidence_ids':result['evidence_ids'],'encoding':{}}]}, {},live=False)
            if purpose=='repair':
                assert payload['repair_fields']==['narrative','claims']
                assert len(json.dumps(payload['memory']['short_term']).encode())<=1000
                return ModelReply({'narrative':'Verified records are shown [source:real-test-record].','claims':[]},{},live=False)
            return await super().generate(purpose,system,payload,**kwargs)
    p=IndependentProvider();m=MemoryStore(tmp_path/'memory.sqlite',p.namespace);m.create_session('A','grounded');model=RepairModel()
    answer=await CopilotService(p,m,model).answer(user_id='A',session_id='grounded',run_id='repair-run',message='Show WELL-X status')
    assert model.calls==['planner','maker','repair']
    assert answer['generation']['status']=='complete' and '9999' not in answer['narrative']
    history=m.validation_history('repair-run')
    assert history[0]['code']=='unsupported_narrative_number' and '9999' in history[0]['details']['invalid_numbers']
