"""Offline official SDK adapter checks; no HTTP requests or credentials."""
import json
import pytest
from langchain_core.messages import AIMessage
from backend.chains import gemma
from backend.contracts import ModelUnavailable


def test_alternate_provider_fails_before_request(tmp_path):
    limiter = gemma.GlobalLimiter(tmp_path / "calls.sqlite")
    with pytest.raises(ValueError, match="Only Google AI Studio"):
        gemma.GemmaClient("offline-test-key", limiter, provider="openrouter")
    assert limiter.stats()["generation_attempts"] == 0


@pytest.mark.asyncio
async def test_official_sdk_ainvoke_shape_and_usage(monkeypatch, tmp_path):
    captured = {}
    class SDK:
        def __init__(self, **kwargs):
            captured.update(kwargs)
        async def ainvoke(self, messages, **kwargs):
            assert messages[0].type == "system"
            assert messages[0].content == "Return useful JSON."
            assert json.loads(messages[1].content.split("\n", 1)[1]) == {"request": "hello"}
            return AIMessage(content='{"direct_response":"How can I help?"}', usage_metadata={"input_tokens": 10, "output_tokens": 8, "total_tokens": 18}, response_metadata={"finish_reason": "STOP"})
    monkeypatch.setattr(gemma, "ChatGoogleGenerativeAI", SDK)
    limiter = gemma.GlobalLimiter(tmp_path / "calls.sqlite")
    reply = await gemma.GemmaClient("offline-test-key", limiter).generate("greeting", "Return useful JSON.", {"request": "hello"}, max_tokens=512)
    assert captured["model"] == "gemini-3.5-flash-lite" and captured["vertexai"] is False
    assert captured["max_retries"] == 1 and captured["max_output_tokens"] == 512
    assert captured["client_args"]["http_options"]["retry_options"]["attempts"] == 1
    assert "extra_body" not in captured and "response_schema" not in captured
    assert reply.data["direct_response"] == "How can I help?"
    assert reply.usage["total_tokens"] == 18 and reply.live is True
    assert next(r for r in limiter.stats()["calls"] if r["kind"] == "generation")["status"] == "complete"


@pytest.mark.asyncio
async def test_sdk_error_redacts_key_and_keeps_status(monkeypatch, tmp_path):
    class SDKError(Exception):
        code = 500
    class SDK:
        def __init__(self, **kwargs): pass
        async def ainvoke(self, *args, **kwargs):
            raise SDKError("Invalid offline-test-key request")
    monkeypatch.setattr(gemma, "ChatGoogleGenerativeAI", SDK)
    limiter = gemma.GlobalLimiter(tmp_path / "calls.sqlite")
    with pytest.raises(ModelUnavailable) as error:
        await gemma.GemmaClient("offline-test-key", limiter).generate("planner", "JSON", {})
    assert "offline-test-key" not in str(error.value) and "HTTP 500" in str(error.value)
    assert next(r for r in limiter.stats()["calls"] if r["kind"] == "generation")["http_status"] == 500


@pytest.mark.asyncio
async def test_sdk_content_blocks_do_not_publish_reasoning(monkeypatch, tmp_path):
    class SDK:
        def __init__(self, **kwargs): pass
        async def ainvoke(self, *args, **kwargs):
            return AIMessage(content=[{"type": "reasoning", "reasoning": "private thoughts"}, {"type": "text", "text": '{"narrative":"Ready."}'}])
    monkeypatch.setattr(gemma, "ChatGoogleGenerativeAI", SDK)
    limiter = gemma.GlobalLimiter(tmp_path / "calls.sqlite")
    reply = await gemma.GemmaClient("offline-test-key", limiter).generate("maker", "JSON", {})
    assert reply.data == {"narrative": "Ready."}


@pytest.mark.asyncio
async def test_sdk_token_count_cached_and_shared_limiter(monkeypatch, tmp_path):
    calls = []
    class SDK:
        def __init__(self, **kwargs): pass
        def get_num_tokens(self, text):
            calls.append(text); return 3
    monkeypatch.setattr(gemma, "ChatGoogleGenerativeAI", SDK)
    limiter = gemma.GlobalLimiter(tmp_path / "calls.sqlite")
    client = gemma.GemmaClient("offline-test-key", limiter)
    assert (await client.count_tokens("test"))["cached"] is False
    assert (await client.count_tokens("test"))["cached"] is True
    assert calls == ["test"] and limiter.stats()["counting_attempts"] == 1
