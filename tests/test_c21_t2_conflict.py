"""Task2 雙角色與首輪衝突。State 帶 rule／位置／原因／建議；後輪修正且內容仍有用。"""
from __future__ import annotations

import asyncio
import json

from seo_agent.content_review.agents import StubAuditor, StubPlanner
from seo_agent.content_review.graph import run_review
from seo_agent.content_review.rules import PROHIBITED, RULESET_VERSION, audit_outline

FORCED = ["穩賺不賠", "保證出金"]


def _run(tmp_path, **kw):
    return asyncio.run(run_review("娛樂城推薦", FORCED, StubPlanner(), StubAuditor(), 4,
                                  log_path=tmp_path / "state_log.jsonl", **kw))


def test_first_draft_conflict_then_specific_rejection(tmp_path):
    r = _run(tmp_path)
    first = r["drafts"][0]["outline"]
    assert all(term in json.dumps(first, ensure_ascii=False) for term in FORCED), "初稿必須含強制禁詞"
    audit1 = next(m for m in r["messages"] if m.get("agent") == "auditor")
    assert audit1["verdict"] == "fail"
    for f in audit1["findings"]:
        assert f["rule_id"] and f["location"] and f["reason"] and f["suggestion"]
    assert {"R1-no-guarantee", "R2-risk-disclosure", "R3-comparison-basis"} <= {f["rule_id"] for f in audit1["findings"]}


def test_planner_sees_why_and_revises(tmp_path):
    r = _run(tmp_path)
    audit1 = next(m for m in r["messages"] if m.get("agent") == "auditor")
    planner2 = [m for m in r["messages"] if m.get("agent") == "planner"][1]
    assert set(planner2["responding_to"]) == {f"{f['rule_id']}@{f['location']}" for f in audit1["findings"]}
    assert planner2["change_log"]


def test_final_outline_balanced(tmp_path):
    r = _run(tmp_path)
    assert r["status"] == "approved" and r["rule_version"] == RULESET_VERSION
    assert 2 <= r["iteration"] <= r["max_iterations"]
    final = r["draft"]
    text = json.dumps(final, ensure_ascii=False)
    assert not any(term in text for term in PROHIBITED), "最終版不得含禁詞"
    assert audit_outline(final) == []
    # 仍保有 SEO 價值：關鍵字、吸睛結構、比較依據與風險揭露
    assert "娛樂城" in final["title"] and "3A娛樂城" in text
    headings = [s["heading"] for s in final["sections"]]
    assert any("評測方法" in h for h in headings) and any("風險" in h for h in headings)
    assert len(final["sections"]) >= len(r["drafts"][0]["outline"]["sections"])


def test_state_log_complete(tmp_path):
    r = _run(tmp_path)
    rows = [json.loads(line) for line in (tmp_path / "state_log.jsonl").read_text(encoding="utf-8").splitlines()]
    nodes = [row["node"] for row in rows]
    assert nodes[0] == "start" and nodes[-1] == "decision"
    assert nodes.count("planning") == nodes.count("audit") == r["iteration"]
    assert r["usage"]["model_calls"] == r["usage"]["planner_calls"] + r["usage"]["auditor_calls"]


def test_auditor_model_pass_cannot_override_rules(tmp_path):
    class LenientAuditor:
        name = "lenient"

        async def acomplete(self, messages):
            return json.dumps({"verdict": "pass", "findings": []})

    r = asyncio.run(run_review("娛樂城推薦", FORCED, StubPlanner(), LenientAuditor(), 4))
    audit1 = next(m for m in r["messages"] if m.get("agent") == "auditor")
    assert audit1["model_verdict"] == "pass" and audit1["verdict"] == "fail"
    assert audit1["model_pass_overridden_by_rules"] is True
    assert r["status"] == "approved" and audit_outline(r["draft"]) == []
