"""T2 最終產出：最終大綱（或未通過原因）＋協商過程重點摘要。"""
from __future__ import annotations

from .rules import DISCLAIMER


def render_review(result: dict) -> str:
    lines = [f"# 內容規劃與合規審查：{result['topic']}", "",
             f"- 終態：**{result['status']}**（{result.get('stop_reason')}）",
             f"- 草稿數：{result['iteration']}／上限 {result['max_iterations']}；規則版本：{result.get('rule_version')}",
             f"- 模型呼叫：{result['usage']['model_calls']}（重試 {result['usage']['retries']}）",
             f"- 注意：{DISCLAIMER}", ""]
    draft = result.get("draft")
    if result["status"] == "approved" and draft:
        lines += ["## 最終文章大綱", "", f"**標題**：{draft['title']}", "", f"**Meta**：{draft.get('meta_description', '')}", ""]
        for i, sec in enumerate(draft["sections"], 1):
            lines.append(f"{i}. {sec['heading']}")
            lines += [f"   - {b}" for b in sec.get("bullets", [])]
        lines.append("")
    else:
        lines += ["## 未通過", "", f"原因：{result.get('stop_reason')}", ""]
        if draft:
            lines += [f"最後一版標題：{draft['title']}", ""]
    lines += ["## 協商過程重點", ""]
    for m in result.get("messages", []):
        agent = m.get("agent")
        if agent == "planner" and "iteration" in m:
            lines.append(f"- **Planner 第 {m['iteration']} 稿**：{m['title']}")
            lines += [f"  - {c}" for c in m.get("change_log", [])]
            if m.get("unresolvable_constraints"):
                lines.append(f"  - 宣告無法移除：{m['unresolvable_constraints']}")
        elif agent == "auditor" and "verdict" in m:
            lines.append(f"- **Auditor 審第 {m['iteration']} 稿**：{m['verdict']}（{len(m['findings'])} 項）")
            lines += [f"  - `{f['rule_id']}` @ {f['location']}：{f['reason']} → 建議：{f['suggestion']}" for f in m["findings"]]
        elif agent == "decision":
            lines.append(f"- **Decision**：{m.get('route')}｜{m.get('reason')}")
        elif m.get("error"):
            lines.append(f"- **{agent} 錯誤**：{m['error']}｜{m.get('detail')}")
    return "\n".join(lines) + "\n"
