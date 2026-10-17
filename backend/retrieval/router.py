"""Read-only diagnostic router. Application must inject an explicit admin guard.

Mount with app.include_router(create_router(provider, context_resolver=guard,
authority_resolver=memory_snapshot), prefix='/api'). No model or write route.
"""
from __future__ import annotations

import inspect
from fastapi import APIRouter, HTTPException, Request
from .contracts import RetrievalError


def create_router(provider, context_resolver=None, authority_resolver=None):
    router = APIRouter(prefix="/retrieval", tags=["retrieval diagnostics"])

    async def context(request):
        if context_resolver is None:
            raise HTTPException(503, "Local diagnostic admin guard is not configured")
        if isinstance(context_resolver, dict):
            guard = context_resolver.get("admin")
            if guard is None:
                raise HTTPException(503, "Local diagnostic administrator guard is not configured")
            checked = guard(request.headers.get("X-Admin-Token"))
            if inspect.isawaitable(checked):
                checked = await checked
            if checked is not True:
                raise HTTPException(403, "Explicit local administrator capability required")
            return {"dataset_namespace": provider.namespace, "reference_date": "2026-10-16", "is_admin": True}
        value = context_resolver(request)
        if inspect.isawaitable(value):
            value = await value
        if not value:
            raise HTTPException(403, "Explicit local administrator capability required")
        return value if isinstance(value, dict) else {"dataset_namespace": provider.namespace, "reference_date": "2026-10-16"}

    async def authority(ctx):
        if isinstance(context_resolver, dict) and context_resolver.get("authority"):
            return context_resolver["authority"](ctx.get("reference_date", "2026-10-16"))
        if authority_resolver is None:
            return None
        value = authority_resolver(ctx)
        return await value if inspect.isawaitable(value) else value

    async def call(request, fn, *args, **kwargs):
        await context(request)
        try:
            return fn(*args, **kwargs)
        except RetrievalError as error:
            raise HTTPException(404 if error.code == "not_found" else 422, {"code": error.code, "message": str(error)})

    @router.get("/overview")
    async def overview(request: Request):
        return await call(request, provider.overview)

    @router.get("/catalog")
    async def catalog(request: Request):
        return await call(request, provider.catalog)

    @router.get("/walkthrough")
    async def walkthrough(request: Request, asset_id: str):
        ctx = await context(request)
        return await call(request, provider.walkthrough, asset_id, ctx, await authority(ctx))

    @router.get("/sources")
    async def sources(request: Request, kind: str | None = None, asset_id: str | None = None, q: str | None = None, limit: int = 25, offset: int = 0):
        return await call(request, provider.sources, kind=kind, asset_id=asset_id, q=q, limit=limit, offset=offset)

    @router.get("/sources/{source_id}")
    async def source(request: Request, source_id: str):
        return await call(request, provider.source, source_id)

    @router.get("/records/{collection}")
    async def records(request: Request, collection: str, asset_id: str | None = None, source_id: str | None = None, limit: int = 25, offset: int = 0):
        ctx = await context(request)
        return await call(request, provider.records, collection, asset_id=asset_id, source_id=source_id, limit=limit, offset=offset, authority=await authority(ctx))

    @router.get("/chunks")
    async def chunks(request: Request, source_id: str | None = None, limit: int = 25, offset: int = 0):
        return await call(request, provider.chunks, source_id=source_id, limit=limit, offset=offset)

    @router.get("/enrichments")
    async def enrichments(request: Request, source_id: str | None = None, limit: int = 25, offset: int = 0):
        return await call(request, provider.enrichments, source_id=source_id, limit=limit, offset=offset)

    @router.get("/issues")
    async def issues(request: Request, limit: int = 25, offset: int = 0):
        return await call(request, provider.issues, limit=limit, offset=offset)

    @router.get("/traces")
    async def traces(request: Request, limit: int = 25, offset: int = 0):
        return await call(request, provider.traces, limit=limit, offset=offset)

    @router.get("/traces/{trace_id}")
    async def trace(request: Request, trace_id: str):
        return await call(request, provider.trace, trace_id)

    @router.get("/evidence/{handle}")
    async def evidence(request: Request, handle: str):
        ctx = await context(request)
        return await call(request, provider.evidence, handle, ctx)

    async def body(request):
        raw = await request.body()
        if len(raw) > 16384:
            raise HTTPException(413, "Diagnostic plan exceeds 16 KiB")
        try:
            value = await request.json()
        except ValueError:
            raise HTTPException(422, "Expected JSON object")
        if not isinstance(value, dict):
            raise HTTPException(422, "Expected JSON object")
        return value

    @router.post("/query")
    async def query(request: Request):
        ctx = await context(request)
        plan = await body(request)
        return await call(request, provider.query, plan, ctx, await authority(ctx))

    @router.post("/search")
    async def search(request: Request):
        ctx = await context(request)
        args = await body(request)
        if set(args) - {"terms", "asset_id", "kind", "limit", "offset", "budget"}:
            raise HTTPException(422, "Only typed lexical search arguments are allowed")
        return await call(request, provider.search, args.pop("terms", ""), ctx, **args)

    @router.get("/results/{handle}")
    async def result(request: Request, handle: str, limit: int = 50, offset: int = 0):
        ctx = await context(request)
        return await call(request, provider.result_page, handle, ctx, limit, offset)

    @router.get("/results/{handle}/members")
    async def members(request: Request, handle: str, limit: int = 25, offset: int = 0):
        ctx = await context(request)
        return await call(request, provider.members, handle, ctx, limit, offset)

    return router
