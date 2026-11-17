"""Task2 Anthropic adapter 的離線契約：用假 client，不連網、不是 live 證據。"""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

anthropic = pytest.importorskip("anthropic")

from seo_agent.content_review.agents import ModelAPIError, ModelOutcomeUnknown, StubAuditor, StubPlanner  # noqa: E402
from seo_agent.content_review.anthropic_model import (  # noqa: E402
    AnthropicChatModel,
    SubscriptionAllowance,
    anthropic_models,
)
from seo_agent.content_review.graph import run_review  # noqa: E402
from seo_agent.harness.model_endpoint import EndpointPolicyError  # noqa: E402

FAKE_OAUTH = "sk-ant-oat01-test-only"


class FakeClient:
    """把請求轉給 fixture 替身，回 Anthropic Messages 形狀。"""

    def __init__(self, error=None):
        self.calls, self.error = [], error
        self.messages = SimpleNamespace(create=self.create)

    def with_options(self, **kw):
        return self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        system = kwargs.get("system", [])  # 訂閱 token 是區塊列表；一般 API key 是字串
        system = system if isinstance(system, str) else " ".join(b["text"] for b in system)
        inner = StubPlanner() if "SEO Content Planner" in system else StubAuditor()
        user = kwargs["messages"][-1]["content"]
        user = user if isinstance(user, str) else "".join(b.get("text", "") for b in user)
        text = asyncio.run(inner.acomplete([{"role": "user", "content": user}]))
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=20))


def _model(client, calls=12):
    return AnthropicChatModel("claude-opus-5-5", FAKE_OAUTH, SubscriptionAllowance(calls, float(calls), 1.0),
                              client=client)


def test_full_review_through_adapter_with_oauth_identity():
    client = FakeClient()
    planner, auditor = _model(client), _model(client)
    r = asyncio.run(run_review("娛樂城推薦", ["穩賺不賠", "保證出金"], planner, auditor, 4))
    assert r["status"] == "approved" and r["iteration"] == 2 and len(client.calls) == 4
    first = client.calls[0]
    assert first["model"] == "claude-opus-5-5" and first["max_tokens"] == 16000
    assert first["system"][0]["text"].startswith("You are Claude Code")  # Hermes 的訂閱 token 處理
    assert FAKE_OAUTH not in json.dumps(planner.allowance.snapshot())


def test_full_review_through_adapter_with_console_api_key():
    """一般 Console API key（sk-ant-api…）不套訂閱 token 的身分轉換，流程一樣能跑完。"""
    key = "sk-ant-api03-test-only"
    client = FakeClient()
    planner = AnthropicChatModel("claude-sonnet-5-5", key, SubscriptionAllowance(12, 12.0, 1.0), client=client)
    auditor = AnthropicChatModel("claude-sonnet-5-5", key, planner.allowance, client=client)
    assert planner._oauth is False
    r = asyncio.run(run_review("娛樂城推薦", ["穩賺不賠", "保證出金"], planner, auditor, 4))
    assert r["status"] == "approved" and len(client.calls) == 4
    assert isinstance(client.calls[0]["system"], str)  # 沒有套訂閱 token 的區塊格式與身分前綴
    assert not client.calls[0]["system"].startswith("You are Claude Code")
    assert key not in json.dumps(planner.allowance.snapshot())


def test_status_errors_and_timeouts_are_classified():
    import httpx
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    err = anthropic.APIStatusError("rate", response=httpx.Response(429, request=req), body=None)
    with pytest.raises(ModelAPIError) as exc:
        asyncio.run(_model(FakeClient(err)).acomplete([{"role": "user", "content": "{}"}]))
    assert exc.value.status == 429
    m = _model(FakeClient(anthropic.APITimeoutError(request=req)))
    with pytest.raises(ModelOutcomeUnknown):
        asyncio.run(m.acomplete([{"role": "user", "content": "{}"}]))
    assert m.allowance.unknown is True
    connect = anthropic.APITimeoutError(request=req)
    connect.__cause__ = httpx.ConnectTimeout("connect")
    m = _model(FakeClient(connect))
    with pytest.raises(ModelAPIError) as exc:
        asyncio.run(m.acomplete([{"role": "user", "content": "{}"}]))
    assert exc.value.status == 503 and m.allowance.unknown is False


def test_truncated_output_is_parse_error_not_silent():
    class Truncating(FakeClient):
        def create(self, **kwargs):
            self.calls.append(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(type="text", text='{"title": "半')],
                                   stop_reason="max_tokens", usage=None)
    with pytest.raises(ValueError, match="truncated"):
        asyncio.run(_model(Truncating()).acomplete([{"role": "user", "content": "{}"}]))


def test_call_cap_enforced_before_request():
    client = FakeClient()
    m = _model(client, calls=1)
    asyncio.run(m.allowance.reserve("x"))
    with pytest.raises(ModelAPIError) as exc:
        asyncio.run(m.acomplete([{"role": "user", "content": "{}"}]))
    assert exc.value.status == 402 and client.calls == []


def test_settings_validated_before_any_request():
    with pytest.raises(EndpointPolicyError, match="SEO_MODEL_API_KEY"):
        anthropic_models(env={})
    with pytest.raises(EndpointPolicyError, match="host"):
        anthropic_models(env={"SEO_MODEL_API_KEY": FAKE_OAUTH, "SEO_MODEL_BASE_URL": "https://evil.example/v1"})
    with pytest.raises(EndpointPolicyError, match="host"):
        anthropic_models(env={"SEO_MODEL_API_KEY": FAKE_OAUTH, "SEO_MODEL_BASE_URL": "http://api.anthropic.com/v1"})
