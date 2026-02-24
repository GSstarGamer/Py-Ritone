from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _identity(uuid: str | None, name: str) -> tuple[str, str]:
    if isinstance(uuid, str) and uuid.strip():
        return ("uuid", uuid.strip().lower())
    return ("name", name.strip().casefold())


@dataclass(slots=True, frozen=True, eq=False)
class player:
    uuid: str | None
    name: str
    self: bool = False

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "player | None":
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise TypeError("player payload must be a dict or None")

        uuid_value = payload.get("uuid")
        uuid = uuid_value if isinstance(uuid_value, str) and uuid_value.strip() else None
        name_value = payload.get("name")
        name = name_value.strip() if isinstance(name_value, str) and name_value.strip() else "unknown"
        self_value = payload.get("self")
        is_self = bool(self_value) if isinstance(self_value, bool) else False
        return cls(uuid=uuid, name=name, self=is_self)

    def __eq__(self, other: object) -> bool:
        if other is self:
            return True

        other_uuid: str | None = None
        other_name: str | None = None

        if isinstance(other, dict):
            other_uuid_raw = other.get("uuid")
            if isinstance(other_uuid_raw, str):
                other_uuid = other_uuid_raw
            other_name_raw = other.get("name")
            if isinstance(other_name_raw, str):
                other_name = other_name_raw
        else:
            other_uuid_raw = getattr(other, "uuid", None)
            if isinstance(other_uuid_raw, str):
                other_uuid = other_uuid_raw
            other_name_raw = getattr(other, "name", None)
            if isinstance(other_name_raw, str):
                other_name = other_name_raw

        if other_name is None:
            return False

        return _identity(self.uuid, self.name) == _identity(other_uuid, other_name)

    def __hash__(self) -> int:
        return hash(_identity(self.uuid, self.name))


@dataclass(slots=True, frozen=True)
class join:
    player: player

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "join":
        value = player.from_payload(payload.get("player"))
        if value is None:
            raise ValueError("join payload requires player")
        return cls(player=value)


@dataclass(slots=True, frozen=True)
class leave:
    player: player

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "leave":
        value = player.from_payload(payload.get("player"))
        if value is None:
            raise ValueError("leave payload requires player")
        return cls(player=value)


@dataclass(slots=True, frozen=True)
class death:
    player: player

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "death":
        value = player.from_payload(payload.get("player"))
        if value is None:
            raise ValueError("death payload requires player")
        return cls(player=value)


@dataclass(slots=True, frozen=True)
class respawn:
    player: player

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "respawn":
        value = player.from_payload(payload.get("player"))
        if value is None:
            raise ValueError("respawn payload requires player")
        return cls(player=value)


__all__ = ["player", "join", "leave", "death", "respawn"]
