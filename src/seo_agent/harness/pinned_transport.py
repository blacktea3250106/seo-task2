"""連線點驗證的 httpx transport：在**實際建立 TCP 連線時**解析 DNS、驗證每個位址都是公開位址，
並直接連到這個已驗證的 IP。驗證與連線用同一次解析結果，沒有「檢查時公開、連線時改成私有」的 TOCTOU 空窗。

- TLS 的 SNI／憑證驗證仍使用原始 hostname（httpcore 以 request origin 的 host 做 start_tls）。
- 解析器可注入（測試用來模擬 DNS 變化）。每次嘗試都記錄在 `connections`。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import httpcore
import httpx

from .netguard import NetworkPolicyError, Resolver, is_public_ip, system_resolver


@dataclass
class PinnedBackend(httpcore.NetworkBackend):
    resolver: Resolver = system_resolver
    connections: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self._inner = httpcore.SyncBackend()

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        addresses = self.resolver(host, port)
        bad = [a for a in addresses if not is_public_ip(a)]
        if not addresses or bad:
            self.connections.append({"host": host, "port": port, "addresses": addresses, "allowed": False})
            raise NetworkPolicyError("private_address_at_connect", f"{host} -> {','.join(addresses) or '(none)'}")
        ip = addresses[0]
        self.connections.append({"host": host, "port": port, "ip": ip, "allowed": True})
        from . import egress
        if egress._STATE["mode"] == "live":
            egress.approve(ip)  # 只登記本次驗證過的公開 IP（N7）
        return self._inner.connect_tcp(ip, port, timeout=timeout, local_address=local_address,
                                       socket_options=socket_options)

    def connect_unix_socket(self, *args, **kwargs):
        raise NetworkPolicyError("unix_socket_not_allowed", "工具網路不允許 unix socket")

    def sleep(self, seconds):
        self._inner.sleep(seconds)


class PinnedTransport(httpx.HTTPTransport):
    """httpx.HTTPTransport，但底層 connection pool 改用 PinnedBackend。"""

    def __init__(self, resolver: Resolver = system_resolver, **kwargs):
        super().__init__(**kwargs)
        self.backend = PinnedBackend(resolver=resolver)
        self._pool = httpcore.ConnectionPool(ssl_context=self._pool._ssl_context, network_backend=self.backend,
                                             max_connections=10, max_keepalive_connections=5, retries=0)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        try:
            return super().handle_request(request)
        except NetworkPolicyError:
            raise
        except httpx.ConnectError as error:  # httpcore 可能把 backend 例外包成 ConnectError
            cause = error.__cause__ or error.__context__
            while cause is not None and not isinstance(cause, NetworkPolicyError):
                cause = cause.__cause__ or cause.__context__
            if isinstance(cause, NetworkPolicyError):
                raise cause from error
            raise


@dataclass
class AsyncPinnedBackend(httpcore.AsyncNetworkBackend):
    """Async equivalent: validate the same DNS answer that supplies the TCP IP."""
    resolver: Resolver = system_resolver
    connections: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self._inner = httpcore.AnyIOBackend()

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        import asyncio

        addresses = await asyncio.to_thread(self.resolver, host, port)
        if not addresses or not all(is_public_ip(a) for a in addresses):
            self.connections.append({"host": host, "port": port, "addresses": addresses, "allowed": False})
            raise NetworkPolicyError("private_address_at_connect", f"{host} resolved to a non-public address")
        ip = addresses[0]
        self.connections.append({"host": host, "port": port, "ip": ip, "allowed": True})
        from . import egress
        if egress._STATE["mode"] == "live":
            egress.approve(ip)
        return await self._inner.connect_tcp(ip, port, timeout=timeout, local_address=local_address,
                                             socket_options=socket_options)

    async def connect_unix_socket(self, *args, **kwargs):
        raise NetworkPolicyError("unix_socket_not_allowed", "model transport does not allow unix sockets")

    async def sleep(self, seconds):
        import asyncio
        await asyncio.sleep(seconds)


class AsyncPinnedTransport(httpx.AsyncHTTPTransport):
    """Keep original origin/TLS hostname while the backend connects to a validated IP."""
    def __init__(self, resolver: Resolver = system_resolver, **kwargs):
        super().__init__(**kwargs)
        self.backend = AsyncPinnedBackend(resolver=resolver)
        self._pool = httpcore.AsyncConnectionPool(ssl_context=self._pool._ssl_context,
            network_backend=self.backend, max_connections=10, max_keepalive_connections=5, retries=0)
