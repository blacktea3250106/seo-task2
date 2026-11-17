"""Task2 設定：讀 config/run_policy.json（草稿上限與 --mode live 的模型額度）。

不讀金鑰；金鑰只在呼叫點從環境變數取得，且不寫入任何報告。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_policy() -> dict:
    """每次重讀，避免執行中被快取的舊值。"""
    return json.loads((ROOT / "config" / "run_policy.json").read_text(encoding="utf-8"))


def real_model_allowed(policy: dict) -> bool:
    """有產品模型、付費呼叫已啟用且額度為正，才可能走 --mode live。"""
    budget = policy["budget"]
    return bool(budget["external_calls_enabled"] and budget["external_budget_usd"] > 0
                and policy["models"]["product_model_id"])
