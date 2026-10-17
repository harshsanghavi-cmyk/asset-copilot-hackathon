"""Real LangGraph functional workflow with durable, JSON-only stage receipts."""
from contextvars import ContextVar
from pathlib import Path
import hashlib
import json

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.func import entrypoint, task

runner = ContextVar("asset_workflow_stage_runner", default=None)


async def checkpointed(path: Path, run_id: str, inputs: dict, execute, dispatch):
    # The caller validates the application-owned run/session owner before opening
    # any checkpoint. No checkpoint is a substitute for authorization/idempotency.
    async with AsyncSqliteSaver.from_conn_string(str(path)) as saver:
        @task
        async def durable_stage(name: str, payload: dict):
            fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
            return {"stage_name": name, "input_hash": fingerprint, "result": await dispatch(name, payload)}

        @entrypoint(checkpointer=saver)
        async def bounded_workflow(payload: dict):
            token = runner.set(durable_stage)
            try:
                return await execute(payload)
            finally:
                runner.reset(token)

        # Legacy untyped positional task receipts remain preserved under their
        # original thread IDs. They cannot safely be replayed after code edits.
        config = {"configurable": {"thread_id": "typed-v2:" + run_id}, "recursion_limit": 30}
        prior = await saver.aget_tuple(config)
        # A non-None new input starts a new execution on the thread. None is the
        # documented resume input and reuses already successful task receipts.
        return await bounded_workflow.ainvoke(None if prior else inputs, config, durability="sync")
