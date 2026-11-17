"""Task2 failure handling: bounded conflict, asynchronous latency, malformed outputs and errors."""
import asyncio

import pytest

from seo_agent.content_review.agents import FaultyModel, StubAuditor, StubPlanner
from seo_agent.content_review.graph import ReviewConfig, run_review


def run(auditor, planner=None, **kw):
    return asyncio.run(run_review("娛樂城推薦", ["穩賺不賠", "保證出金"], planner or StubPlanner(), auditor,
                                 kw.pop("max_iterations", 4), **kw))


def test_always_forced_terms_end_as_conflict_not_approval():
    result = run(StubAuditor(), force_policy="always")
    assert result["status"] == "conflict_unresolvable"
    assert result["iteration"] <= result["max_iterations"] == 4
    assert result["unresolvable"] and result["findings_history"][-1]


@pytest.mark.parametrize("fault,kind,expected_calls", [
    (("delay", 1), "timeout", 2), (("invalid_json",), "parse_error", 2),
    (("api_error", 429), "api_error", 2), (("api_error", 503), "api_error", 2),
    (("api_error", 401), "auth", 1)])
def test_auditor_failures_never_pass_or_increase_draft_count(fault, kind, expected_calls):
    auditor = FaultyModel(StubAuditor(), faults=[fault, fault])
    result = run(auditor, cfg=ReviewConfig(timeout_s=0.01, backoff_s=0))
    assert result["status"] == "auditor_failed"
    assert result["iteration"] == 1 and auditor.calls == expected_calls
    assert result["usage"]["auditor_calls"] == expected_calls
    assert result["usage"]["retries"] == expected_calls - 1
    assert all(e["kind"] == kind for e in result["usage"]["errors"])


def test_transient_parse_failure_recovers_without_counting_retry_as_draft():
    auditor = FaultyModel(StubAuditor(), faults=[("invalid_json",)])
    result = run(auditor, cfg=ReviewConfig(backoff_s=0))
    assert result["status"] == "approved" and result["iteration"] == 2
    assert result["usage"]["auditor_calls"] == 3 and result["usage"]["retries"] == 1


def test_model_budget_stops_before_auditor_invocation():
    auditor = FaultyModel(StubAuditor())
    result = run(auditor, cfg=ReviewConfig(max_model_calls=1))
    assert result["status"] == "budget_exhausted"
    assert auditor.calls == 0 and result["usage"]["model_calls"] == 1


@pytest.mark.parametrize("role,output", [("auditor", "[]"), ("auditor", '{"verdict":"fail","findings":[42]}'),
                                        ("planner", '{"outline":42}'),
                                        ("planner", '{"outline":{"title":"x","sections":[42]}}')])
def test_valid_json_with_invalid_shape_has_safe_terminal(role, output):
    class InvalidShape:
        name = "invalid-shape"

        async def acomplete(self, messages):
            return output

    result = run(InvalidShape() if role == "auditor" else StubAuditor(),
                 planner=InvalidShape() if role == "planner" else StubPlanner(), cfg=ReviewConfig(backoff_s=0))
    assert result["status"] == role + "_failed"
    assert result["usage"]["retries"] == 1
