"""Task2 LangGraph 工作流：Start → Planning → Audit → Decision。

State：topic、draft、drafts、messages、findings、rule_version、iteration、max_iterations、usage、status。
- iteration＝已產生的草稿數；retry 另計（usage.retries），照樣記帳（usage.model_calls）。
- Decision 終態：approved／max_iterations_reached／conflict_unresolvable／planner_failed／auditor_failed／budget_exhausted；
  未分類例外一律落到 *_failed 或 internal_error，且照樣寫 state_log。
- Planner 收到完整退件歷史 rejection_history，不只最新一輪。
- Auditor 的草稿以 Spotlighting 標記包住，標記內只是資料（防 prompt injection）。
- Auditor 解析失敗或 timeout **永不當作通過**。
- 模型呼叫：asyncio.wait_for 逾時；429／5xx／timeout／無效 JSON 有限重試；401／403 不重試。
"""
from __future__ import annotations

import asyncio
import json
import operator
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents import ChatModel, ModelAPIError, ModelOutcomeUnknown, StubAuditor, StubPlanner
from .prompts import auditor_prompt, planner_prompt
from .rules import DISCLAIMER, RULESET_VERSION, audit_outline, extract_json_text, spotlight

TERMINAL = {"approved", "max_iterations_reached", "conflict_unresolvable", "planner_failed", "auditor_failed",
            "budget_exhausted", "internal_error"}


class ReviewState(TypedDict, total=False):
    topic: str
    forced_terms: list[str]
    force_policy: str
    draft: dict | None
    drafts: Annotated[list[dict], operator.add]
    messages: Annotated[list[dict], operator.add]
    findings: list[dict]
    findings_history: Annotated[list[list[dict]], operator.add]
    unresolvable: list[str]
    rule_version: str
    iteration: int
    max_iterations: int
    usage: dict
    status: str
    stop_reason: str


@dataclass
class ReviewConfig:
    timeout_s: float = 20.0
    max_attempts: int = 2
    max_model_calls: int = 12
    backoff_s: float = 0.05


class CallFailed(Exception):
    def __init__(self, kind: str, detail: str, attempts: int):
        super().__init__(f"{kind}: {detail}")
        self.kind, self.detail, self.attempts = kind, detail, attempts


def _usage(state: ReviewState) -> dict:
    return dict(state.get("usage") or {"model_calls": 0, "retries": 0, "planner_calls": 0, "auditor_calls": 0,
                                       "latency_s": 0.0, "errors": []})


async def call_json(model: ChatModel, messages: list[dict], usage: dict, role: str, cfg: ReviewConfig,
                    validate) -> dict:
    """呼叫模型並解析 JSON；所有嘗試（含失敗）都記入 usage。"""
    last = None
    for attempt in range(1, cfg.max_attempts + 1):
        if usage["model_calls"] >= cfg.max_model_calls:
            raise CallFailed("budget_exhausted", "model call budget reached", attempt - 1)
        usage["model_calls"] += 1
        usage[f"{role}_calls"] += 1
        if attempt > 1:
            usage["retries"] += 1
        started = time.monotonic()
        try:
            raw = await asyncio.wait_for(model.acomplete(messages), timeout=cfg.timeout_s)
            data = json.loads(extract_json_text(raw))
            validate(data)
            usage["latency_s"] = round(usage["latency_s"] + time.monotonic() - started, 4)
            return data
        except ModelOutcomeUnknown as error:
            usage["errors"].append({"role": role, "attempt": attempt, "kind": "outcome_unknown",
                                    "detail": "provider outcome unknown; no automatic retry"})
            raise CallFailed("outcome_unknown", "provider outcome unknown; reconcile before retry", attempt) from error
        except asyncio.TimeoutError:
            last = ("timeout", f"{role} > {cfg.timeout_s}s")
        except ModelAPIError as error:
            last = ("api_error", f"{role} status={error.status}")
            if error.status in {401, 403}:
                usage["errors"].append({"role": role, "attempt": attempt, "kind": "auth", "detail": str(error)})
                raise CallFailed("auth", str(error), attempt) from error
            if error.status == 402:
                raise CallFailed("budget_exhausted", "model allowance exhausted", attempt) from error
            if error.status != 429 and not 500 <= error.status <= 599:
                usage["errors"].append({"role": role, "attempt": attempt, "kind": "api_error",
                                        "detail": str(error)})
                raise CallFailed("api_error", str(error), attempt) from error
        except (ValueError, KeyError, TypeError) as error:
            last = ("parse_error", f"{role}: {type(error).__name__}: {str(error)[:120]}")
        except Exception as error:  # 未分類例外：不重試（可能是程式錯誤），由節點轉成 *_failed 終態
            detail = f"{role}: {type(error).__name__}: {str(error)[:120]}"
            usage["errors"].append({"role": role, "attempt": attempt, "kind": "unexpected", "detail": detail})
            raise CallFailed("unexpected", detail, attempt) from error
        usage["latency_s"] = round(usage["latency_s"] + time.monotonic() - started, 4)
        usage["errors"].append({"role": role, "attempt": attempt, "kind": last[0], "detail": last[1]})
        if attempt < cfg.max_attempts:
            await asyncio.sleep(cfg.backoff_s * attempt)
    raise CallFailed(last[0], last[1], cfg.max_attempts)


def _validate_planner(data):
    if not isinstance(data, dict) or not isinstance(data.get("outline"), dict):
        raise ValueError("planner response needs an outline object")
    outline = data["outline"]
    if not isinstance(outline.get("title"), str) or not isinstance(outline.get("sections"), list):
        raise ValueError("planner outline 缺 title／sections")
    if not isinstance(outline.get("meta_description", ""), str):
        raise ValueError("meta_description must be text")
    for section in outline["sections"]:
        if not isinstance(section, dict) or not isinstance(section.get("heading"), str):
            raise ValueError("section needs a heading string")
        if not isinstance(section.get("bullets", []), list) or any(not isinstance(b, str) for b in section.get("bullets", [])):
            raise ValueError("section bullets must be a list of strings")
    for field in ("change_log", "unresolvable_constraints"):
        if not isinstance(data.get(field, []), list) or any(not isinstance(v, str) for v in data.get(field, [])):
            raise ValueError(f"{field} must be a list of strings")


def _validate_auditor(data):
    if not isinstance(data, dict) or data.get("verdict") not in {"pass", "fail"} or not isinstance(data.get("findings"), list):
        raise ValueError("auditor 輸出缺 verdict／findings")
    for f in data["findings"]:
        if not isinstance(f, dict):
            raise ValueError("finding must be an object")
        for key in ("rule_id", "location", "reason", "suggestion"):
            if not isinstance(f.get(key), str) or not f[key]:
                raise ValueError(f"finding 缺 {key}")
    # 判定與 findings 必須一致，否則當作解析錯誤（重試後 auditor_failed，永不 approved）
    if data["verdict"] == "fail" and not any(f.get("severity", "blocking") == "blocking" for f in data["findings"]):
        raise ValueError("auditor 判 fail 但沒有 blocking finding（Planner 無法依此修訂）")
    if data["verdict"] == "pass" and any(f.get("severity", "blocking") == "blocking" for f in data["findings"]):
        raise ValueError("auditor 判 pass 卻列出 blocking finding（判定自相矛盾）")


def _blocking(findings: list[dict]) -> list[dict]:
    return [f for f in findings if f.get("severity", "blocking") == "blocking"]


def _rejection_history(history: list[list[dict]]) -> list[dict]:
    """每一輪的退件重點，讓 Planner 不會改好 A 又把上一輪的 B 改回去。"""
    return [{"draft": i, "findings": [{k: f[k] for k in ("rule_id", "location", "reason", "suggestion")}
                                      for f in round_findings]}
            for i, round_findings in enumerate(history, 1)]


def build_graph(planner: ChatModel, auditor: ChatModel, cfg: ReviewConfig | None = None):
    cfg = cfg or ReviewConfig()

    async def start(state: ReviewState) -> dict:
        return {"iteration": 0, "draft": None, "findings": [], "unresolvable": [], "rule_version": RULESET_VERSION,
                "usage": _usage(state), "status": "planning",
                "messages": [{"agent": "system", "content": f"任務：{state['topic']}；規則 {RULESET_VERSION}（{DISCLAIMER}）；"
                              f"強制詞 {state.get('forced_terms')}（{state.get('force_policy')}）；最多 {state['max_iterations']} 份草稿"}]}

    async def planning(state: ReviewState) -> dict:
        usage = _usage(state)
        task = {"topic": state["topic"], "forced_terms": state.get("forced_terms", []),
                "force_policy": state.get("force_policy", "first_draft"), "previous_draft": state.get("draft"),
                "findings": state.get("findings", []),
                "rejection_history": _rejection_history(state.get("findings_history", [])),
                "iteration": state["iteration"] + 1}
        prompt = [{"role": "system", "content": planner_prompt()},
                  {"role": "user", "content": json.dumps(task, ensure_ascii=False)}]

        def validate(data):
            _validate_planner(data)
            if state["iteration"] == 0 or task["force_policy"] == "always":
                missing = [term for term in task["forced_terms"] if term not in data["outline"]["title"]]
                if missing:
                    raise ValueError(f"required conflict terms missing from title: {missing}")
        try:
            data = await call_json(planner, prompt, usage, "planner", cfg, validate)
        except CallFailed as error:
            status = "budget_exhausted" if error.kind == "budget_exhausted" else "planner_failed"
            return {"usage": usage, "status": status, "stop_reason": f"planner {error.kind}: {error.detail}",
                    "messages": [{"agent": "planner", "error": error.kind, "detail": error.detail}]}
        iteration = state["iteration"] + 1
        return {"draft": data["outline"], "drafts": [{"iteration": iteration, "outline": data["outline"]}],
                "iteration": iteration, "usage": usage, "status": "auditing",
                "unresolvable": data.get("unresolvable_constraints", []),
                "messages": [{"agent": "planner", "iteration": iteration, "responding_to": [
                    f"{f['rule_id']}@{f['location']}" for f in state.get("findings", [])],
                    "change_log": data.get("change_log", []), "unresolvable_constraints": data.get("unresolvable_constraints", []),
                    "title": data["outline"]["title"]}]}

    async def audit(state: ReviewState) -> dict:
        usage = _usage(state)
        prompt = [{"role": "system", "content": auditor_prompt()},
                  {"role": "user", "content": spotlight({"draft": state["draft"], "rule_version": RULESET_VERSION})}]
        try:
            data = await call_json(auditor, prompt, usage, "auditor", cfg, _validate_auditor)
        except CallFailed as error:
            status = "budget_exhausted" if error.kind == "budget_exhausted" else "auditor_failed"
            return {"usage": usage, "status": status, "stop_reason": f"auditor {error.kind}: {error.detail}（不視為通過）",
                    "messages": [{"agent": "auditor", "error": error.kind, "detail": error.detail}]}
        # 確定性規則一律合併：模型只能增加 finding，不能讓違規草稿通過
        deterministic = [f.as_dict() for f in audit_outline(state["draft"])]
        # 程式已在同一位置抓到同一規則時，略過模型重複的那條（建議精簡）；模型多抓到的照樣保留
        covered = {(f["rule_id"], loc) for f in deterministic for loc in f["location"].split("、")}
        model_only = [f for f in data["findings"]
                      if not all((f["rule_id"], loc) in covered for loc in f["location"].split("、"))]
        merged, seen = [], set()
        for f in deterministic + model_only:
            key = (f["rule_id"], f["location"], f["reason"])
            if key not in seen:
                seen.add(key)
                merged.append(f)
        overridden = data["verdict"] == "pass" and bool(deterministic)
        return {"findings": merged, "findings_history": [merged], "usage": usage,
                "status": "decision", "messages": [{"agent": "auditor", "iteration": state["iteration"],
                                                    # 與 Decision 同一判準：只有 blocking 才算 fail
                                                    "verdict": "fail" if _blocking(merged) else "pass",
                                                    "blocking_count": len(_blocking(merged)),
                                                    "model_verdict": data["verdict"],
                                                    "model_pass_overridden_by_rules": overridden, "findings": merged}]}

    # 邊的名稱就是 Mermaid 上的條件文字，拓撲圖直接看得出邊的邏輯
    REVISE, FINISH = "fail 帶修訂建議退回", "pass 或其他終態"
    DRAFTED, PLAN_FAILED = "草稿完成送審", "Planner 失敗或超出預算"

    def decide(state: ReviewState) -> str:
        if state.get("status") in TERMINAL:
            return FINISH
        return REVISE if state.get("status") == "planning" else FINISH

    async def decision(state: ReviewState) -> dict:
        if state.get("status") in TERMINAL:
            return {}
        findings = state.get("findings", [])
        blocking = _blocking(findings)
        history = state.get("findings_history", [])
        if not blocking:
            status, reason = "approved", f"第 {state['iteration']} 份草稿通過 {RULESET_VERSION}"
        elif state.get("unresolvable") and len(history) >= 2 and \
                {f["rule_id"] for f in history[-1]} & {f["rule_id"] for f in history[-2]} >= {"R1-no-guarantee"}:
            status, reason = "conflict_unresolvable", f"Planner 宣告不可移除的限制 {state['unresolvable']}，且同一規則連續違反"
        elif state["iteration"] >= state["max_iterations"]:
            status, reason = "max_iterations_reached", f"已達 {state['max_iterations']} 份草稿仍有 {len(blocking)} 項違規"
        else:
            return {"status": "planning", "messages": [{"agent": "decision", "route": "planning",
                                                        "reason": f"{len(blocking)} 項違規，退回修訂"}]}
        return {"status": status, "stop_reason": reason,
                "messages": [{"agent": "decision", "route": "end", "status": status, "reason": reason}]}

    graph = StateGraph(ReviewState)
    graph.add_node("start", start)
    graph.add_node("planning", planning)
    graph.add_node("audit", audit)
    graph.add_node("decision", decision)
    graph.add_edge(START, "start")
    graph.add_edge("start", "planning")
    graph.add_conditional_edges("planning", lambda s: PLAN_FAILED if s.get("status") in TERMINAL else DRAFTED,
                                {DRAFTED: "audit", PLAN_FAILED: END})
    graph.add_edge("audit", "decision")
    graph.add_conditional_edges("decision", decide, {REVISE: "planning", FINISH: END})
    return graph.compile()


async def run_review(topic: str, forced_terms: list[str], planner: ChatModel, auditor: ChatModel, max_iterations: int,
                     force_policy: str = "first_draft", cfg: ReviewConfig | None = None,
                     log_path: Path | None = None) -> dict:
    if type(max_iterations) is not int or not 1 <= max_iterations <= 100:
        raise ValueError("max_iterations must be an integer from 1 to 100")
    if force_policy not in {"first_draft", "always"}:
        raise ValueError("unknown force_policy")
    if not topic.strip() or not forced_terms or any(not isinstance(t, str) or not t.strip() for t in forced_terms):
        raise ValueError("topic and forced_terms must be non-empty text")
    app = build_graph(planner, auditor, cfg)
    state: dict[str, Any] = {"topic": topic, "forced_terms": forced_terms, "force_policy": force_policy,
                             "max_iterations": max_iterations, "drafts": [], "messages": [], "findings_history": []}
    log = []
    final: dict[str, Any] = dict(state)
    try:
        # recursion_limit：每輪 3 個節點；上限保護避免任何設定錯誤造成死循環
        async for update in app.astream(state, config={"recursion_limit": 4 * max_iterations + 6},
                                        stream_mode="updates"):
            for node, delta in update.items():
                delta = delta or {}
                for key, value in delta.items():
                    if key in {"drafts", "messages", "findings_history"}:
                        final[key] = final.get(key, []) + value
                    else:
                        final[key] = value
                log.append({"node": node, "iteration": final.get("iteration"), "status": final.get("status"),
                            "delta": delta})
    except Exception as error:  # 節點外的未分類例外（含 recursion limit）：落到終態、不當作通過
        reason = f"internal_error: {type(error).__name__}: {str(error)[:200]}"
        final.update(status="internal_error", stop_reason=reason)
        final.setdefault("iteration", 0)
        final.setdefault("rule_version", RULESET_VERSION)
        final.setdefault("usage", _usage(final))
        final["messages"] = final.get("messages", []) + [{"agent": "system", "error": "internal_error", "detail": reason}]
        log.append({"node": "error", "iteration": final.get("iteration"), "status": "internal_error",
                    "delta": {"stop_reason": reason}})
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as fh:
            for row in log:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    final["state_log"] = log
    return final


def mermaid() -> str:
    return build_graph(StubPlanner(), StubAuditor()).get_graph().draw_mermaid()
