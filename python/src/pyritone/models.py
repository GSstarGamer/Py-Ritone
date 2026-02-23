from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BridgeInfo:
    host: str
    port: int
    token: str
    ws_url: str
    ws_path: str = "/ws"
    transport: str = "websocket"
    protocol_version: int | None = None
    server_version: str | None = None


class DiscoveryError(ValueError):
    pass


class BridgeError(RuntimeError):
    def __init__(self, code: str, message: str, payload: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.payload = payload or {}
        super().__init__(f"{code}: {message}")
