from __future__ import annotations

import asyncio
import hmac
import importlib
import json
import os
from pathlib import Path
from typing import Any
import uuid

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ag_ui.core import (CustomEvent, RunStartedEvent, RunFinishedEvent, RunErrorEvent,
                       TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent,
                       ToolCallStartEvent, ToolCallArgsEvent, ToolCallEndEvent, ToolCallResultEvent)
from ag_ui.encoder import EventEncoder

from backend.chains.gemma import GemmaClient, GlobalLimiter, MODEL
from backend.chains.service import CopilotService
from backend.contracts import ModelUnavailable
from backend.memory import MemoryStore
from backend.memory.store import ScopeError

ROOT = Path(__file__).resolve().parents[1]


class SessionInput(BaseModel):
    id: str | None = None
    title: str = Field(default="New conversation", max_length=90)


class RenameInput(BaseModel):
    title: str = Field(min_length=1, max_length=90)


class BranchInput(BaseModel):
    message_id: str = Field(min_length=1, max_length=300)
    mode: str


def create_app(*, provider=None, memory=None, model=None, runtime_dir=None,
               admin_enabled=None, admin_token=None, live_enabled=None) -> FastAPI:
    load_dotenv(ROOT / ".env", override=False)
    reference_default = os.environ.get("ASSET_REFERENCE_DATE", "2027-01-15")
    # Only composition root knows the current provider factory. Core chain does not.
    runtime = Path(runtime_dir or os.environ.get("ASSET_RUNTIME_DIR", ROOT / "runtime"))
    runtime.mkdir(parents=True, exist_ok=True)
    if provider is None:
        module = importlib.import_module("backend.retrieval.provider")
        roots = os.environ.get("ASSET_DATASET_ROOTS", str(ROOT / "dataset" / "test-data" / "dataset")).split(os.pathsep)
        provider = module.create_provider([Path(p) for p in roots], Path(os.environ.get("ASSET_RETRIEVAL_DB", runtime / "retrieval-test.sqlite")), namespace=os.environ.get("ASSET_DATASET_NAMESPACE", "asset-field-test-2027-01-15"))
    memory = memory or MemoryStore(runtime / "memory.sqlite", namespace=provider.namespace)
    limiter = None
    if model is None:
        load_dotenv(ROOT / ".env", override=False)
        limiter = GlobalLimiter(runtime / "model-requests.sqlite", max_generations=int(os.environ.get("ASSET_GENERATION_LIMIT", "20")))
        model = GemmaClient(os.environ.get("GOOGLE_API_KEY"), limiter, streaming=os.environ.get("ASSET_GEMMA_STREAM") == "1")
    service = CopilotService(provider, memory, model, reference_date=reference_default)
    enabled = admin_enabled if admin_enabled is not None else os.environ.get("ASSET_ADMIN_ENABLED") == "1"
    token = admin_token if admin_token is not None else os.environ.get("ASSET_ADMIN_TOKEN")
    generation_enabled = live_enabled if live_enabled is not None else os.environ.get("ASSET_LIVE_ENABLED", "1") == "1"
    if not token and os.environ.get("ASSET_ADMIN_TOKEN_FILE"):
        token_file = Path(os.environ["ASSET_ADMIN_TOKEN_FILE"])
        if token_file.is_file():
            token = token_file.read_text().strip()
    app = FastAPI(title="Asset Intelligence Copilot", version="0.1.0")
    app.state.service, app.state.provider, app.state.memory, app.state.limiter = service, provider, memory, limiter
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5190", "http://127.0.0.1:5190", "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5191", "http://127.0.0.1:5191", "http://localhost:5192", "http://127.0.0.1:5192"],
                       allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                       allow_headers=["Content-Type", "X-User-Id", "X-Session-Id", "X-Admin-Token", "Accept"])

    def user(x_user_id: str | None = Header(default=None)):
        try:
            service.validate_user(x_user_id)
        except PermissionError as exc:
            raise HTTPException(401, str(exc)) from exc
        return x_user_id

    def admin(x_admin_token: str | None = Header(default=None)):
        if not enabled or not token:
            raise HTTPException(403, "Local admin diagnostics are disabled or unconfigured")
        if not x_admin_token or not hmac.compare_digest(x_admin_token, token):
            raise HTTPException(403, "An explicit local admin capability is required")
        return True

    @app.exception_handler(ScopeError)
    async def scope_error(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.get("/api/health")
    def health():
        readiness = service.readiness()
        if not generation_enabled:
            readiness["ready"] = False
            readiness["reason"] = "Live Gemma generation is temporarily paused for provider diagnosis; data/session/admin APIs remain available"
        return {"status": "ready" if readiness["ready"] else "degraded", "liveness": "ok", **readiness,
                "reference_date": reference_default, "dataset_namespace": provider.namespace,
                "schema_version": "1.0", "provider": provider.catalog(),
                "model": getattr(model, "model_id", MODEL), "model_provider": getattr(model, "provider", "injected-test"), "model_configured": bool(getattr(model, "configured", False)),
                "model_adapter": getattr(model, "adapter", "injected-test"),
                "model_availability": "paused_for_diagnosis" if not generation_enabled else "not_guaranteed_by_liveness",
                "model_generation_enabled": generation_enabled,
                "identity": "dataset user picker, not production authentication", "admin_enabled": bool(enabled and token)}

    @app.get("/api/users")
    def users():
        return {"users": service.users()}

    @app.get("/api/sessions")
    def sessions(q: str = Query(default="", max_length=100), limit: int = Query(default=50, ge=1, le=100),
                 offset: int = Query(default=0, ge=0), uid=Depends(user)):
        return memory.list_sessions(uid, q, limit, offset)

    @app.post("/api/sessions", status_code=201)
    def create_session(body: SessionInput = Body(default=SessionInput()), uid=Depends(user)):
        try:
            return memory.create_session(uid, body.id, body.title)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/sessions/{session_id}")
    def get_session(session_id: str, uid=Depends(user)):
        return memory.session(session_id, uid)

    @app.patch("/api/sessions/{session_id}")
    def rename_session(session_id: str, body: RenameInput, uid=Depends(user)):
        return memory.rename_session(session_id, uid, body.title)

    @app.delete("/api/sessions/{session_id}", status_code=204)
    def delete_session(session_id: str, uid=Depends(user)):
        memory.delete_session(session_id, uid)
        return Response(status_code=204)

    @app.get("/api/sessions/{session_id}/messages")
    def messages(session_id: str, uid=Depends(user)):
        return memory.history(session_id, uid)

    @app.post("/api/sessions/{session_id}/branches", status_code=201)
    def branch_session(session_id: str, body: BranchInput, uid=Depends(user)):
        try:
            return memory.create_branch(session_id, uid, body.message_id, body.mode)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/answers/{answer_id}")
    def answer(answer_id: str, uid=Depends(user)):
        return memory.answer(answer_id, uid)

    @app.get("/api/answers/{answer_id}/suggestions")
    def suggestions(answer_id: str, uid=Depends(user)):
        return service.answer_suggestions(uid, answer_id)

    @app.post("/api/answers/{answer_id}/suggestions", status_code=202)
    async def queue_suggestions(answer_id: str, body: dict = Body(default={}), uid=Depends(user)):
        if body:
            raise HTTPException(400, "This endpoint accepts an empty body; visible scoped text is assembled server-side")
        return service.answer_suggestions(uid, answer_id, enqueue=True)

    @app.get("/api/evidence/{evidence_id:path}")
    def evidence(evidence_id: str, answer_id: str, uid=Depends(user)):
        envelope = memory.answer(answer_id, uid)
        if evidence_id not in envelope.get("evidence", {}):
            raise HTTPException(404, "Source is not part of this user's answer")
        if evidence_id.startswith(("memory:", "app:pages:", "app:capability:")):
            return envelope["evidence"][evidence_id]
        return provider.evidence(evidence_id, service.context(uid, envelope["thread_id"], answer_id, envelope["reference_date"]))

    @app.post("/api/agent")
    async def agent(request: Request, uid=Depends(user), x_session_id: str | None = Header(default=None)):
        body = await request.json()
        sid = body.get("threadId") or body.get("session_id") or x_session_id
        if not isinstance(sid, str) or x_session_id and sid != x_session_id:
            raise HTTPException(400, "A matching conversation ID is required")
        memory.session(sid, uid)
        run_id = body.get("runId") or body.get("run_id") or str(uuid.uuid4())
        if not isinstance(run_id, str) or len(run_id) > 160:
            raise HTTPException(400, "Invalid run ID")
        text = body.get("message")
        client_message_id = body.get("message_id")
        if text is None:
            latest = next((m for m in reversed(body.get("messages", [])) if m.get("role") == "user"), None)
            text = latest.get("content") if latest else None
            client_message_id = latest.get("id") if latest else client_message_id
        if isinstance(text, list):
            text = "\n".join(part.get("text", "") for part in text if isinstance(part, dict) and part.get("type") == "text")
        if not isinstance(text, str) or not text.strip() or len(text) > 30000:
            raise HTTPException(400, "A bounded user message is required")
        forwarded = body.get("forwardedProps") or {}
        client_message_id = forwarded.get("retry_of_user_message_id") or client_message_id
        reference_date = forwarded.get("reference_date", body.get("reference_date", reference_default))
        import datetime
        try:
            reference_date = datetime.date.fromisoformat(reference_date).isoformat()
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, "reference_date must be an ISO date") from exc
        encoder = EventEncoder(accept="text/event-stream")
        queue: asyncio.Queue = asyncio.Queue()

        async def progress(message):
            value = dict(message) if isinstance(message, dict) else {"message": message}
            await queue.put(CustomEvent(name="asset_progress", value={"run_id": run_id, **value}))

        async def stream():
            yield encoder.encode(RunStartedEvent(thread_id=sid, run_id=run_id))
            if not generation_enabled:
                prior = memory.begin(run_id, sid, uid, text, client_message_id)
                canonical = prior.get("id", run_id)
                error = "Gemma live generation is temporarily paused for provider diagnosis. Your question is saved; data and retrieval diagnostics remain available."
                memory.fail(canonical, uid, error, "model_under_repair")
                yield encoder.encode(RunErrorEvent(message=error, code="model_under_repair"))
                return
            task = asyncio.create_task(service.answer(user_id=uid, session_id=sid, run_id=run_id, message=text, reference_date=reference_date, progress=progress, client_message_id=client_message_id, attempt_id=run_id))
            try:
                while not task.done() or not queue.empty():
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=0.5)
                        yield encoder.encode(event)
                    except asyncio.TimeoutError:
                        if not task.done():
                            yield ": keep-alive\n\n"
                envelope = await task
                message_id = run_id + ":text"
                yield encoder.encode(TextMessageStartEvent(message_id=message_id, role="assistant"))
                yield encoder.encode(TextMessageContentEvent(message_id=message_id, delta=envelope["narrative"]))
                yield encoder.encode(TextMessageEndEvent(message_id=message_id))
                tool_id = run_id + ":dashboard"
                yield encoder.encode(ToolCallStartEvent(tool_call_id=tool_id, tool_call_name="answer_dashboard", parent_message_id=message_id))
                yield encoder.encode(ToolCallArgsEvent(tool_call_id=tool_id, delta=json.dumps({"envelope": envelope}, ensure_ascii=False, default=str)))
                yield encoder.encode(ToolCallEndEvent(tool_call_id=tool_id))
                status = "partial" if envelope.get("generation", {}).get("status") == "partial" else "ready"
                yield encoder.encode(ToolCallResultEvent(message_id=run_id + ":tool-result", tool_call_id=tool_id, content=json.dumps({"status": status, "answer_id": envelope["answer_id"]}), role="tool"))
                yield encoder.encode(RunFinishedEvent(thread_id=sid, run_id=run_id, result={"answer_id": envelope["answer_id"], "status": status, "sample": False}))
            except asyncio.CancelledError:
                # The shared run continues and persists its genuine terminal
                # state; a reconnect attaches instead of launching another call.
                raise
            except Exception as exc:
                code = getattr(exc, "code", "run_failed")
                message = str(exc) if isinstance(exc, (ModelUnavailable, ValueError, PermissionError)) else "The backend run failed; inspect server diagnostics without exposing credentials"
                retry = getattr(exc, "retry_after", None)
                metadata = {"retry_after_seconds": retry} if retry is not None else None
                yield encoder.encode(RunErrorEvent(message=message[:1000], code=code, metadata=metadata))

        return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.get("/api/admin/memory", dependencies=[Depends(admin)])
    def admin_memory(scope: str | None = None, user_id: str | None = None, kind: str | None = None,
                     q: str = Query(default="", max_length=100), limit: int = Query(default=25, ge=1, le=100), offset: int = Query(default=0, ge=0)):
        if scope is not None and scope not in {"private", "shared"}:
            raise HTTPException(400, "scope must be private or shared")
        return memory.admin_list(scope, user_id, kind, q, limit, offset)

    @app.get("/api/admin/memory/changes", dependencies=[Depends(admin)])
    def admin_changes(limit: int = Query(default=25, ge=1, le=100), offset: int = Query(default=0, ge=0)):
        return memory.admin_changes(limit, offset)

    @app.get("/api/admin/memory/status", dependencies=[Depends(admin)])
    def admin_status(user_id: str | None = None):
        return memory.admin_status(user_id)

    @app.get("/api/admin/memory/{identifier}", dependencies=[Depends(admin)])
    def admin_detail(identifier: str):
        try:
            return memory.admin_detail(identifier)
        except KeyError as exc:
            raise HTTPException(404, "Memory not found") from exc

    @app.get("/api/admin/model", dependencies=[Depends(admin)])
    def admin_model():
        return limiter.stats() if limiter else {"model": "injected-test-client", "live": False}

    @app.get("/api/admin/runs/{run_id}/validation", dependencies=[Depends(admin)])
    def validation_receipts(run_id: str):
        return {"run_id":run_id,"items":memory.validation_history(run_id)}

    # Retrieval owner owns its router; only the composition root mounts it.
    try:
        router_module = importlib.import_module("backend.retrieval.router")
        resolver = {"user": user, "admin": admin, "authority": memory.authority}
        router = router_module.create_router(provider, context_resolver=resolver)
        app.include_router(router, prefix="/api")
    except ModuleNotFoundError as exc:
        if exc.name != "backend.retrieval.router":
            raise
    return app


_app = None


def get_app():
    global _app
    if _app is None:
        _app = create_app()
    return _app
