"""Approved remote model settings, with secrets kept out of run config and trace."""
from __future__ import annotations

import math
import os

from ..config import real_model_allowed
from .model_endpoint import EndpointPolicyError, classify


class LiveEndpoint:
    def __init__(self, policy: dict, *, env=None, resolver=None):
        if not real_model_allowed(policy):
            raise EndpointPolicyError("live 研究被阻擋（B-LLM）：需核准模型、外部呼叫與正額度")
        env = os.environ if env is None else env
        self.base_url = env.get("SEO_MODEL_BASE_URL", "https://api.openai.com/v1")
        self.endpoint = classify(self.base_url, policy, **({"resolver": resolver} if resolver else {}))
        if self.endpoint.kind != "live":
            raise EndpointPolicyError("live models cannot use a fixture/loopback endpoint")
        self.api_key = env.get("SEO_MODEL_API_KEY", "")
        if not self.api_key:
            raise EndpointPolicyError("SEO_MODEL_API_KEY is required; never store keys in policy files")
        try:
            self.worst_usd_per_call = float(env.get("SEO_MODEL_WORST_USD_PER_CALL", "0"))
        except (ValueError, TypeError):
            self.worst_usd_per_call = 0
        if not math.isfinite(self.worst_usd_per_call) or self.worst_usd_per_call <= 0:
            raise EndpointPolicyError("set a finite positive SEO_MODEL_WORST_USD_PER_CALL before live calls")
        self.model_name = policy["models"]["product_model_id"]
        self.requests = []  # Body logging is disabled for remote requests; ledger records actual attempts.

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass
