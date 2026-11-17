"""Anthropic Messages 連線：重用 vendor Hermes 的 anthropic_adapter。

- 憑證只從環境變數 SEO_MODEL_API_KEY 讀；API key 或訂閱 setup-token 由 Hermes 自動判別，不寫入任何紀錄。
- 只允許 MODEL_HOST_ALLOWLIST 內的 HTTPS 主機；SDK 自動重試關閉，重試只由 graph.call_json 控制。
- 呼叫次數用 ModelAllowance 預留；訂閱沒有逐次美元帳單，美元欄位只是名目上限。
- 逾時等「請求可能已送達」的情況標記 unknown 並停止後續呼叫，與 live_model.APIChatModel 一致。
"""
from __future__ import annotations

import asyncio
import os
from urllib.parse import urlsplit

import httpx

from ..harness.model_endpoint import MODEL_HOST_ALLOWLIST, EndpointPolicyError
from .agents import ModelAPIError, ModelOutcomeUnknown
from .live_model import ModelAllowance

DEFAULT_MODEL = "claude-opus-5-5"


class SubscriptionAllowance(ModelAllowance):
    def snapshot(self):
        snap = super().snapshot()
        snap.update(backend="anthropic-messages-via-hermes",
                    cost_note="Call-count cap only; subscription/API billing is not measured here.")
        return snap


def _sdk_base_url(url: str) -> str:
    url = url.strip().rstrip("/")
    return url[:-3] if url.endswith("/v1") else url  # SDK 自己會加 /v1/messages


class AnthropicChatModel:
    def __init__(self, model: str, api_key: str, allowance: ModelAllowance, *,
                 base_url: str = "https://api.anthropic.com", max_tokens: int = 16000, timeout_s: float = 170.0,
                 client=None):
        from agent.anthropic_adapter import build_anthropic_client  # Hermes：import 前 HERMES_HOME 已由 CLI 設定
        from agent.anthropic_credentials import _is_oauth_token
        self.name, self.allowance, self.max_tokens = model, allowance, max_tokens
        self._base_url = _sdk_base_url(base_url)
        self._oauth = _is_oauth_token(api_key)
        self._client = client or build_anthropic_client(api_key, self._base_url, timeout=timeout_s)
        try:
            self._client = self._client.with_options(max_retries=0)
        except AttributeError:
            pass

    def _kwargs(self, messages: list[dict]) -> dict:
        from agent.anthropic_adapter import build_anthropic_kwargs
        return build_anthropic_kwargs(self.name, messages, None, self.max_tokens, None,
                                      is_oauth=self._oauth, base_url=self._base_url)

    async def acomplete(self, messages: list[dict]) -> str:
        import anthropic
        event = await self.allowance.reserve(self.name)
        kwargs = self._kwargs(messages)
        try:
            response = await asyncio.to_thread(self._client.messages.create, **kwargs)
        except anthropic.APIStatusError as error:
            event.update(state="response_received", status=error.status_code)
            # 不帶回應內容（可能回顯輸入或憑證資訊）
            raise ModelAPIError(error.status_code, "provider rejected request") from None
        except anthropic.APITimeoutError as error:
            if isinstance(error.__cause__, (httpx.ConnectTimeout, httpx.PoolTimeout)):
                event["state"] = "not_sent"  # 連線還沒建立，請求沒送出，可安全重試
                raise ModelAPIError(503, "provider connect timeout") from None
            event["state"] = "unknown"
            self.allowance.unknown = True
            raise ModelOutcomeUnknown("request may have reached provider") from None
        except anthropic.APIConnectionError:
            event["state"] = "not_sent"
            raise ModelAPIError(503, "provider connection failed") from None
        event.update(state="response_received", status=200)
        text = "".join(getattr(block, "text", "") for block in response.content
                       if getattr(block, "type", "") == "text")
        usage = getattr(response, "usage", None)
        if usage is not None:
            event["tokens"] = {k: getattr(usage, k) for k in ("input_tokens", "output_tokens")
                               if type(getattr(usage, k, None)) is int}
        if getattr(response, "stop_reason", None) == "max_tokens":
            event["parse_error"] = True
            raise ValueError(f"model output truncated at max_tokens={self.max_tokens}")
        if not text.strip():
            event["parse_error"] = True
            raise ValueError("empty model response")
        return text


def anthropic_models(*, model: str | None = None, max_calls: int = 12, env=None):
    """在任何請求前驗證設定；兩個角色共用同一模型與同一個呼叫上限（角色分工在 prompt）。"""
    env = os.environ if env is None else env
    api_key = env.get("SEO_MODEL_API_KEY", "")
    if not api_key:
        raise EndpointPolicyError("缺少 SEO_MODEL_API_KEY（API key 或 claude setup-token）")
    base_url = env.get("SEO_MODEL_BASE_URL") or "https://api.anthropic.com"
    parts = urlsplit(base_url)
    if parts.scheme != "https" or parts.hostname not in MODEL_HOST_ALLOWLIST:
        raise EndpointPolicyError(f"模型 host 未核准或非 HTTPS：{parts.hostname}")
    model = model or env.get("SEO_MODEL_ID") or DEFAULT_MODEL
    allowance = SubscriptionAllowance(max_calls, float(max_calls), 1.0)
    return (AnthropicChatModel(model, api_key, allowance, base_url=base_url),
            AnthropicChatModel(model, api_key, allowance, base_url=base_url), allowance)
