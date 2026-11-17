"""Live adapter contracts using simulated HTTP only; these are NOT live evidence."""
import asyncio
import copy
import json

import httpx
import pytest

from seo_agent.config import load_policy
from seo_agent.content_review.agents import ModelAPIError, ModelOutcomeUnknown, StubAuditor, StubPlanner
from seo_agent.content_review.graph import ReviewConfig, run_review
from seo_agent.content_review.live_model import APIChatModel, ModelAllowance, api_models
from seo_agent.harness.model_endpoint import EndpointPolicyError


def test_unapproved_configuration_never_constructs_live_models():
    with pytest.raises(EndpointPolicyError, match="B-LLM"):
        api_models(load_policy(), env={})


def test_live_endpoint_rejects_loopback_and_missing_cost_before_calls():
    policy = copy.deepcopy(load_policy())
    policy["models"]["product_model_id"] = "test-model"
    policy["budget"].update(external_calls_enabled=True, external_budget_usd=1)
    with pytest.raises(EndpointPolicyError, match="loopback"):
        api_models(policy, env={"SEO_MODEL_BASE_URL": "http://localhost:123/v1"})
    with pytest.raises(EndpointPolicyError, match="WORST_USD"):
        api_models(policy, env={"SEO_MODEL_API_KEY": "secret-test-value"}, resolver=lambda *_: ["8.8.8.8"])


def test_real_adapter_serializes_both_roles_and_revises_from_actual_findings():
    seen = []
    planner, auditor = StubPlanner(), StubAuditor()

    async def respond(request):
        data = json.loads(request.content)
        seen.append(data)
        inner = planner if "SEO Content Planner" in data["messages"][0]["content"] else auditor
        content = await inner.acomplete(data["messages"])
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}],
                                         "usage": {"prompt_tokens": 10, "completion_tokens": 20}})

    async def exercise():
        budget = ModelAllowance(12, 1, 0.01)
        transport = httpx.MockTransport(respond)
        p = APIChatModel("test-planner", "https://api.openai.com/v1", "private-key", budget, transport=transport)
        a = APIChatModel("test-auditor", "https://api.openai.com/v1", "private-key", budget, transport=transport)
        result = await run_review("娛樂城推薦", ["穩賺不賠", "保證出金"], p, a, 4)
        assert result["status"] == "approved" and result["iteration"] == 2
        assert budget.calls == 4 and budget.reserved_usd == 0.04
        assert "private-key" not in json.dumps(budget.snapshot())
        assert all(e["tokens"]["completion_tokens"] == 20 for e in budget.events)
        revision = json.loads(seen[2]["messages"][-1]["content"])
        assert revision["findings"] and revision["previous_draft"]
        assert "prohibited_substrings" in seen[1]["messages"][0]["content"]
    asyncio.run(exercise())


def test_allowance_shared_across_roles_and_reserved_before_network():
    sent = []
    async def respond(request):
        sent.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    async def exercise():
        budget = ModelAllowance(10, 0.01, 0.01)
        model = APIChatModel("test", "https://api.openai.com/v1", "key", budget,
                             transport=httpx.MockTransport(respond))
        await model.acomplete([])
        with pytest.raises(ModelAPIError) as exc:
            await model.acomplete([])
        assert exc.value.status == 402 and len(sent) == 1
    asyncio.run(exercise())


def test_unknown_outcome_stops_graph_without_retry_or_second_network_request():
    sent = []
    async def fail(request):
        sent.append(request)
        raise httpx.ReadTimeout("possibly sent", request=request)

    async def exercise():
        budget = ModelAllowance(12, 1, 0.01)
        model = APIChatModel("test", "https://api.openai.com/v1", "key", budget,
                             transport=httpx.MockTransport(fail))
        result = await run_review("娛樂城推薦", ["穩賺不賠"], model, model, 4)
        assert result["status"] == "planner_failed"
        assert result["usage"]["model_calls"] == 1
        assert "outcome_unknown" in result["stop_reason"]
        with pytest.raises(ModelOutcomeUnknown):
            await model.acomplete([])
        assert len(sent) == 1 and budget.reserved_usd == 0.01
    asyncio.run(exercise())


@pytest.mark.parametrize("status,retries", [(400, 0), (401, 0), (403, 0), (404, 0), (429, 1), (503, 1)])
def test_http_error_classification_and_no_secret_in_logs(status, retries):
    async def respond(request):
        return httpx.Response(status, text="private-key should never be exposed")

    async def exercise():
        budget = ModelAllowance(12, 1, 0.01)
        model = APIChatModel("test", "https://api.openai.com/v1", "private-key", budget,
                             transport=httpx.MockTransport(respond))
        result = await run_review("娛樂城推薦", ["穩賺不賠"], model, model, 4,
                                  cfg=ReviewConfig(backoff_s=0))
        assert result["status"] == "planner_failed"
        assert result["usage"]["retries"] == retries
        assert "private-key" not in json.dumps(result)
    asyncio.run(exercise())


@pytest.mark.parametrize("payload", [[], None, 42,
    {"choices": [{"message": {"content": "{}"}}], "usage": [1]},
    {"choices": [{"message": {"content": "{}"}}], "usage": []},
    {"choices": []}, {"choices": [None]}])
def test_malformed_provider_json_ends_safely_and_preserves_log(tmp_path, payload):
    async def respond(request):
        return httpx.Response(200, json=payload)

    async def exercise():
        budget = ModelAllowance(12, 1, 0.01)
        model = APIChatModel("test", "https://api.openai.com/v1", "key", budget,
                             transport=httpx.MockTransport(respond))
        result = await run_review("娛樂城推薦", ["穩賺不賠"], model, model, 4,
                                  cfg=ReviewConfig(backoff_s=0), log_path=tmp_path / "state.jsonl")
        assert result["status"] == "planner_failed" and budget.calls == 2
        assert result["usage"]["errors"][-1]["kind"] == "parse_error"
        assert (tmp_path / "state.jsonl").is_file()
    asyncio.run(exercise())


def test_outer_timeout_cancels_api_and_does_not_retry_unknown_request():
    sent = []
    async def slow(request):
        sent.append(request)
        await asyncio.sleep(10)
        return httpx.Response(200)

    async def exercise():
        budget = ModelAllowance(12, 1, 0.01)
        model = APIChatModel("test", "https://api.openai.com/v1", "key", budget,
                             transport=httpx.MockTransport(slow))
        result = await run_review("娛樂城推薦", ["穩賺不賠"], model, model, 4,
                                  cfg=ReviewConfig(timeout_s=0.01, backoff_s=0))
        assert result["status"] == "planner_failed" and budget.unknown
        assert len(sent) == 1 and budget.calls == 1
    asyncio.run(exercise())
