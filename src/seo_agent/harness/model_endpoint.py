"""模型端點分類：mode 由實際 base_url 推導，不接受設定直接宣告。

- loopback（127.0.0.0/8、::1、localhost）→ 一律 `fixture`，不論其他設定。
- `live` 需要：product_model_id 非空、external_calls_enabled、額度 > 0、host 不是私有位址、
  且 host 在 MODEL_HOST_ALLOWLIST（與工具網路 allowlist 分開）。
- 其他情況 → raise，拒絕建立 Agent。
"""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlsplit

from ..config import real_model_allowed
from .netguard import Resolver, is_public_ip, system_resolver

# 已知的官方 OpenAI 相容端點；新增 provider 需記錄在 ADR，並由使用者在設定中核准服務名稱。
MODEL_HOST_ALLOWLIST = {
    "api.anthropic.com", "api.openai.com", "openrouter.ai", "inference-api.nousresearch.com",
}


class EndpointPolicyError(Exception):
    pass


@dataclass(frozen=True)
class EndpointInfo:
    base_url: str
    host: str
    kind: str  # "fixture" | "live"


def _is_loopback_host(host: str) -> bool:
    if host in {"localhost", "localhost.localdomain"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def classify(base_url: str, policy: dict, resolver: Resolver = system_resolver) -> EndpointInfo:
    parts = urlsplit(base_url)
    host = (parts.hostname or "").lower()
    if parts.scheme not in {"http", "https"} or not host or parts.username or parts.password:
        raise EndpointPolicyError(f"無效的模型端點：{base_url!r}")
    if _is_loopback_host(host):
        return EndpointInfo(base_url, host, "fixture")
    if not real_model_allowed(policy):
        raise EndpointPolicyError("非 loopback 模型端點需要 product_model_id、external_calls_enabled 與正額度")
    if parts.scheme != "https":
        raise EndpointPolicyError("live 模型端點必須是 https")
    if host not in MODEL_HOST_ALLOWLIST:
        raise EndpointPolicyError(f"模型 host 未核准：{host}")
    addresses = resolver(host, parts.port or 443)
    if not addresses or not all(is_public_ip(a) for a in addresses):
        raise EndpointPolicyError(f"模型 host 解析到非公開位址：{host}")
    return EndpointInfo(base_url, host, "live")
