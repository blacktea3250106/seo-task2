"""Task2 demo 合規規則（出題方沒有提供公司手冊；只宣稱「符合本 demo 規則集」，不是法律保證）。

規則至少涵蓋：禁止無依據保證、要求風險揭露、比較性主張要有依據。
每個 finding 都有 rule_id、位置、理由、具體修改建議，讓 Planner 知道「為什麼被退件、怎麼改」。
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass

RULESET_VERSION = "demo-ymyl-2026.11-v3"
DISCLAIMER = "Demo 規則集，僅供展示工作流；不代表任何公司手冊或法律意見。"

# 禁詞 → 建議的誠實替代（建議只是方向，Planner 可改寫）
# v2：建議文字本身不得含任何禁詞（test_suggestions_never_contain_prohibited 檢查），
#     也不建議「實測」等系統沒做過的量測，避免誘導捏造。
PROHIBITED = {
    "穩賺不賠": "誠實揭露勝率與風險（例如「了解賠率與輸贏機率」）",
    "保證出金": "改為可查證的出金說明（例如「出金流程與審核時間說明」）",
    "保證獲利": "改為說明「沒有穩定獲利的方法」與主要風險",
    "必勝": "改為「策略與風險說明」",
    "零風險": "改為「主要風險與自我保護方式」",
    "100%": "移除絕對化數字，改為有來源的數據或範圍",
}
# 簡體寫法對應到正體禁詞（最小正規化，不引入 OpenCC）
VARIANTS = {"稳赚不赔": "穩賺不賠", "保证出金": "保證出金", "保证获利": "保證獲利", "必胜": "必勝",
            "零风险": "零風險"}
# 正規化時移除的空白與標點（保留 %，因為「100%」是禁詞）
_STRIP = re.compile(r"[\s·・.,，。、!！?？:：;；'\"“”‘’「」『』()（）\[\]【】〔〕<>《》〈〉\-－—_~～*＊/／\\|｜]+")
COMPARATIVE = ("推薦", "排行", "最佳", "第一", "TOP", "Top")
RISK_TERMS = ("風險", "理性", "負責任")
AGE_TERMS = ("18歲", "18 歲", "未成年")
BASIS_TERMS = ("評測方法", "評比依據", "評分標準", "資料來源")
# SEO 底線：搜尋結果約顯示 30 個中文字；超過就被截斷，吸睛點會看不到
TITLE_MAX = 32


@dataclass(frozen=True)
class Finding:
    rule_id: str
    location: str
    reason: str
    suggestion: str
    severity: str = "blocking"

    def as_dict(self) -> dict:
        return asdict(self)


def _locations(outline: dict):
    yield "title", outline.get("title") or ""
    yield "meta_description", outline.get("meta_description") or ""
    for i, sec in enumerate(outline.get("sections") or []):
        yield f"sections[{i}].heading", sec.get("heading") or ""
        for j, bullet in enumerate(sec.get("bullets") or []):
            yield f"sections[{i}].bullets[{j}]", bullet


def normalize(text: str) -> str:
    """NFKC（全形轉半形）＋移除空白與標點，讓「穩 賺不賠」「穩・賺・不・賠」也比得到。"""
    return _STRIP.sub("", unicodedata.normalize("NFKC", text or ""))


def prohibited_in(text: str) -> list[str]:
    """回傳文字中出現的禁詞（正體原名；簡體寫法對應回正體）。"""
    norm = normalize(text)
    hits = [term for term in PROHIBITED if normalize(term) in norm]
    hits += [canon for variant, canon in VARIANTS.items() if variant in norm and canon not in hits]
    return hits


def audit_outline(outline: dict) -> list[Finding]:
    findings: list[Finding] = []
    full_text = " ".join(text for _, text in _locations(outline))
    # 同一個禁詞出現在多處只列一條，位置合併（建議精簡，Planner 一次看懂）
    places: dict[str, list[str]] = {}
    for location, text in _locations(outline):
        for term in prohibited_in(text):
            places.setdefault(term, []).append(location)
    for term, locs in places.items():
        findings.append(Finding("R1-no-guarantee", "、".join(locs),
                                f"「{term}」屬於無依據保證或誇大字眼，YMYL 內容零容忍（含空白、標點或簡體寫法），共 {len(locs)} 處",
                                f"刪除「{term}」，{PROHIBITED[term]}"))
    headings = " ".join(s.get("heading", "") for s in outline.get("sections") or [])
    if not any(t in headings for t in RISK_TERMS):
        findings.append(Finding("R2-risk-disclosure", "sections", "缺少獨立的風險揭露段落",
                                "新增段落「風險揭露與理性娛樂」：說明輸錢風險、設定預算、求助資源"))
    if not any(t in full_text for t in AGE_TERMS):
        findings.append(Finding("R2-risk-disclosure", "sections", "未標示年齡限制",
                                "在風險段落加入「未滿 18 歲禁止參與」"))
    if any(t in full_text for t in COMPARATIVE) and not any(t in headings for t in BASIS_TERMS):
        findings.append(Finding("R3-comparison-basis", "sections", "有推薦／排行等比較性主張，但沒有說明比較依據",
                                "新增段落「評測方法與評比依據」：列出評比項目（牌照、資安審查、出金流程）、要取得的證據與資料時間；未查證的結果不要寫成事實"))
    title = outline.get("title") or ""
    if len(title) > TITLE_MAX:
        findings.append(Finding("S1-title-length", "title",
                                f"SEO 底線（不是合規規則）：標題 {len(title)} 字，超過 {TITLE_MAX} 字，搜尋結果會截斷，吸睛點看不到",
                                f"標題縮到 {TITLE_MAX} 字內：主關鍵字放最前面，保留一個誠實的吸睛點（例如問句、年份或讀者好處）；細節移到 meta 或內文"))
    return findings


def violated_terms(outline: dict) -> set[str]:
    return {term for _, text in _locations(outline) for term in prohibited_in(text)}


# Spotlighting（防 prompt injection）：交給模型的草稿包在標記內；JSON 內的「<」轉成 \u003c，草稿無法偽造結束標記
DATA_OPEN, DATA_CLOSE = "<<<DRAFT_DATA>>>", "<<<END_DRAFT_DATA>>>"


def spotlight(payload) -> str:
    body = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return f"{DATA_OPEN}\n{body}\n{DATA_CLOSE}"


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def extract_json_text(text: str) -> str:
    match = _JSON_FENCE.search(text)
    return match.group(1) if match else text
