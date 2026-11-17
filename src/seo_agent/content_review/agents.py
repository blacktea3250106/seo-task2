"""Task2 角色模型介面與離線 stub。

- `ChatModel.acomplete(messages) -> str`：非同步；live 時接真實 provider，離線用 stub。
- Stub Planner：根據 State 裡**實際的 Auditor findings** 修訂（不是預錄對話）；`force_policy` 控制禁詞是否
  只在初稿強制（first_draft）或每輪強制（always，用來測不可收斂）。
- Stub Auditor：輸出 JSON；判定一律與確定性規則 `audit_outline` 合併，模型只能**增加** finding。
- FaultyModel：注入延遲、無效 JSON、API 錯誤，用來測容錯。
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Protocol

from .rules import DATA_CLOSE, DATA_OPEN, PROHIBITED, RULESET_VERSION, audit_outline


class ModelAPIError(Exception):
    def __init__(self, status: int, message: str = ""):
        super().__init__(f"api_error {status}: {message}")
        self.status = status


class ModelOutcomeUnknown(Exception):
    """A request may have reached its provider: retain cost and do not retry blindly."""


class ChatModel(Protocol):
    name: str

    async def acomplete(self, messages: list[dict]) -> str: ...


# 替換詞本身不得含禁詞、不得宣稱沒做過的量測，也不含「風險」以免假冒風險段落（舊版「沒有保證獲利的真相」會重複替換而不收斂）
HONEST = {"穩賺不賠": "勝率實話", "保證出金": "出金流程說明", "保證獲利": "獲利機率真相",
          "必勝": "策略說明", "零風險": "可能損失說明", "100%": "有來源的數據"}


def _task(messages: list[dict]) -> dict:
    content = messages[-1]["content"]
    if DATA_OPEN in content:  # Spotlighting：Auditor 的草稿包在標記內
        content = content.split(DATA_OPEN, 1)[1].rsplit(DATA_CLOSE, 1)[0]
    return json.loads(content)


@dataclass
class StubPlanner:
    """SEO Content Planner 替身：目標是點擊率；初稿依設定塞入高點擊禁詞。"""
    name: str = "stub-planner-v1"

    async def acomplete(self, messages: list[dict]) -> str:
        task = _task(messages)
        topic, forced = task["topic"], task["forced_terms"]
        previous, findings = task.get("previous_draft"), task.get("findings") or []
        always = task.get("force_policy") == "always"
        change_log, unresolvable = [], []
        if previous is None:
            outline = {
                "title": f"2026 {topic}｜{'、'.join(forced)}的 3A娛樂城排行",
                "meta_description": f"精選{topic}，{forced[0]}，新手也能輕鬆上手。",
                "sections": [
                    {"heading": "本月娛樂城推薦排行 TOP 5", "bullets": ["人氣平台一覽", f"{forced[0]}的玩法"]},
                    {"heading": f"{forced[-1]}平台怎麼挑", "bullets": ["出金速度比較", "優惠活動"]},
                    {"heading": "3A娛樂城是什麼", "bullets": ["定義與特色", "常見問題"]},
                ]}
            change_log.append("初稿：依 SEO 目標放入高點擊關鍵字與排行結構")
        else:
            outline = json.loads(json.dumps(previous))
            for f in findings:
                if f["rule_id"] == "R1-no-guarantee":
                    term = next((t for t in PROHIBITED if t in f["reason"]), None)
                    if term and always and term in forced:
                        unresolvable.append(f"must_include:{term}")
                        continue
                    if term:
                        outline = _replace_everywhere(outline, term, HONEST.get(term, "風險說明"))
                        change_log.append(f"依 {f['rule_id']}@{f['location']}：「{term}」→「{HONEST.get(term)}」")
                elif f["rule_id"] == "S1-title-length":
                    outline["title"] = f"{topic}怎麼挑？看懂勝率與出金流程"
                    change_log.append(f"依 {f['rule_id']}：標題縮短，保留主關鍵字與問句")
                elif f["rule_id"] == "R2-risk-disclosure" and not any("風險" in s["heading"] for s in outline["sections"]):
                    outline["sections"].append({"heading": "風險揭露與理性娛樂",
                                                "bullets": ["輸錢風險與預算設定", "未滿 18 歲禁止參與", "求助資源"]})
                    change_log.append(f"依 {f['rule_id']}：新增風險揭露段落")
                elif f["rule_id"] == "R2-risk-disclosure":
                    for s in outline["sections"]:
                        if "風險" in s["heading"] and not any("18" in b for b in s["bullets"]):
                            s["bullets"].append("未滿 18 歲禁止參與")
                    change_log.append(f"依 {f['rule_id']}：補上年齡限制")
                elif f["rule_id"] == "R3-comparison-basis" and not any("評測方法" in s["heading"] for s in outline["sections"]):
                    outline["sections"].insert(1, {"heading": "評測方法與評比依據",
                                                   "bullets": ["牌照與監管資訊", "資安審查項目", "出金流程與資料時間（待查證，不寫未做過的結果）"]})
                    change_log.append(f"依 {f['rule_id']}：新增評比依據段落")
            if always:  # SEO 要求每輪都必須含禁詞：把被移除的禁詞放回標題
                for term in forced:
                    if term not in outline["title"]:
                        outline["title"] += f"｜{term}"
        unresolvable = sorted(set(unresolvable))
        return json.dumps({"outline": outline, "change_log": change_log, "unresolvable_constraints": unresolvable},
                          ensure_ascii=False)


def _replace_everywhere(outline: dict, term: str, replacement: str) -> dict:
    return json.loads(json.dumps(outline, ensure_ascii=False).replace(term, replacement))


@dataclass
class StubAuditor:
    """YMYL Compliance Auditor 替身：以 demo 規則輸出 JSON 判定。"""
    name: str = "stub-auditor-v1"

    async def acomplete(self, messages: list[dict]) -> str:
        task = _task(messages)
        findings = [f.as_dict() for f in audit_outline(task["draft"])]
        return json.dumps({"verdict": "fail" if findings else "pass", "rule_version": RULESET_VERSION,
                           "findings": findings}, ensure_ascii=False)


@dataclass
class FaultyModel:
    """依呼叫次序注入故障：("delay", 秒)、("invalid_json",)、("api_error", status)、None＝正常。"""
    inner: ChatModel
    faults: list = field(default_factory=list)
    calls: int = 0

    @property
    def name(self) -> str:
        return f"faulty({self.inner.name})"

    async def acomplete(self, messages: list[dict]) -> str:
        fault = self.faults[self.calls] if self.calls < len(self.faults) else None
        self.calls += 1
        if fault is None:
            return await self.inner.acomplete(messages)
        kind = fault[0]
        if kind == "delay":
            await asyncio.sleep(fault[1])
            return await self.inner.acomplete(messages)
        if kind == "invalid_json":
            return "verdict: pass (not json"
        if kind == "api_error":
            raise ModelAPIError(fault[1], "injected")
        raise ValueError(f"unknown fault {fault}")
