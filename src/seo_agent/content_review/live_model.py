"""Explicitly approved OpenAI-compatible T2 models. No SDK retries or secret logging.

Both roles share a conservative request/cost reservation. Unknown outcomes stop further
requests. JSON parsing and finite, known-response retries belong to graph.call_json.
"""
from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, field

import httpx

from ..harness.live_endpoint import LiveEndpoint
from ..harness.netguard import NetworkPolicyError
from ..harness.pinned_transport import AsyncPinnedTransport
from .agents import ModelAPIError, ModelOutcomeUnknown


@dataclass
class ModelAllowance:
    max_calls: int
    max_usd: float
    worst_usd_per_call: float
    calls: int = 0
    reserved_usd: float = 0.0
    unknown: bool = False
    events: list[dict] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def __post_init__(self):
        if (type(self.max_calls) is not int or self.max_calls <= 0 or
                not all(math.isfinite(v) and v > 0 for v in (self.max_usd, self.worst_usd_per_call))):
            raise ValueError("finite positive model call/cost limits required")

    async def reserve(self, model: str):
        async with self._lock:
            if self.unknown:
                raise ModelOutcomeUnknown("previous request requires reconciliation")
            if (self.calls >= self.max_calls or
                    self.reserved_usd + self.worst_usd_per_call > self.max_usd + 1e-12):
                raise ModelAPIError(402, "model allowance exhausted")
            self.calls += 1
            self.reserved_usd = round(self.reserved_usd + self.worst_usd_per_call, 12)
            self.events.append({"call": self.calls, "model": model, "state": "reserved",
                                "usd_upper_bound": self.worst_usd_per_call})
            return self.events[-1]

    def snapshot(self):
        return {"backend": "openai-compatible-api", "calls": self.calls,
                "reserved_usd_upper_bound": self.reserved_usd, "max_usd": self.max_usd,
                "outcome_unknown": self.unknown, "events": self.events,
                "cost_note": "Conservative configured upper bound, not provider-billed cost."}


class APIChatModel:
    def __init__(self, model: str, base_url: str, api_key: str, allowance: ModelAllowance,
                 *, timeout_s: float = 45.0, transport=None):
        self.name = model
        self._url, self._key = base_url.rstrip("/") + "/chat/completions", api_key
        self.allowance, self.timeout_s, self.transport = allowance, timeout_s, transport

    async def acomplete(self, messages: list[dict]) -> str:
        event = await self.allowance.reserve(self.name)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s, follow_redirects=False,
                                         trust_env=False, transport=self.transport or AsyncPinnedTransport()) as client:
                response = await client.post(self._url, headers={"Authorization": f"Bearer {self._key}"},
                                             json={"model": self.name, "messages": messages,
                                                   "max_tokens": 4096, "stream": False})
        except NetworkPolicyError:
            event["state"] = "network_refused"
            raise ModelAPIError(403, "model network policy refused connection") from None
        except (httpx.ConnectError, httpx.ConnectTimeout):
            event["state"] = "not_sent"
            # Keep the conservative reservation; graph retries are separately bounded.
            raise ModelAPIError(503, "provider connection failed") from None
        except (httpx.HTTPError, asyncio.CancelledError):
            event["state"] = "unknown"
            self.allowance.unknown = True
            raise ModelOutcomeUnknown("request may have reached provider") from None
        event.update(state="response_received", status=response.status_code)
        if response.status_code != 200:
            # Never include provider response bodies (may echo credentials or private input).
            raise ModelAPIError(response.status_code, "provider rejected request")
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("chat completion must be an object")
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("empty model response")
            usage = data.get("usage", {})
            if usage is None:
                usage = {}
            if not isinstance(usage, dict):
                raise ValueError("usage must be an object")
            event["tokens"] = {k: usage[k] for k in ("prompt_tokens", "completion_tokens")
                               if type(usage.get(k)) is int}
            return content
        except (ValueError, KeyError, TypeError, IndexError):
            event["parse_error"] = True
            raise ValueError("provider returned an invalid chat completion") from None


def api_models(policy: dict, *, max_calls: int = 12, env=None, resolver=None):
    """Validate all settings before any request; secrets are only read at this boundary."""
    endpoint = LiveEndpoint(policy, env=env, resolver=resolver)
    allowance = ModelAllowance(max_calls, policy["budget"]["external_budget_usd"], endpoint.worst_usd_per_call)
    # Same model may implement two distinct roles; role separation is in the graph prompts.
    def role():
        return APIChatModel(endpoint.model_name, endpoint.base_url, endpoint.api_key, allowance)
    return role(), role(), allowance
