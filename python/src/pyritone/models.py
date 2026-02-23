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
    def __init__(
        self,
        code: str,
        message: str,
        payload: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.payload = payload or {}
        self.details = details or {}
        super().__init__(f"{code}: {message}")


class TypedCallError(BridgeError):
    pass


@dataclass(slots=True, frozen=True)
class RemoteRef:
    ref_id: str
    java_type: str | None = None


@dataclass(slots=True, frozen=True)
class VisibleEntity:
    id: str
    type_id: str
    category: str
    x: float
    y: float
    z: float
    distance_sq: float

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "VisibleEntity":
        if not isinstance(payload, dict):
            raise TypeError("VisibleEntity payload must be a dict")

        return cls(
            id=_require_string(payload, "id"),
            type_id=_require_string(payload, "type_id"),
            category=_require_string(payload, "category"),
            x=_require_number(payload, "x"),
            y=_require_number(payload, "y"),
            z=_require_number(payload, "z"),
            distance_sq=_require_number(payload, "distance_sq"),
        )


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"VisibleEntity payload field '{key}' must be a non-empty string")
    return value


def _require_number(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"VisibleEntity payload field '{key}' must be a number")
    return float(value)
