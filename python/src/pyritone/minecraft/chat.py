from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .player import player


class author(player):
    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "author | None":
        value = player.from_payload(payload)
        if value is None:
            return None
        return cls(uuid=value.uuid, name=value.name, self=value.self)


@dataclass(slots=True, frozen=True)
class message:
    message: str
    author: author | None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "message":
        if not isinstance(payload, dict):
            raise TypeError("chat message payload must be a dict")

        text_value = payload.get("message")
        text = text_value if isinstance(text_value, str) else ""
        author_value = author.from_payload(payload.get("author"))
        return cls(message=text, author=author_value)


@dataclass(slots=True, frozen=True)
class system_message:
    message: str
    overlay: bool

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "system_message":
        if not isinstance(payload, dict):
            raise TypeError("system message payload must be a dict")
        message_value = payload.get("message")
        overlay_value = payload.get("overlay")
        return cls(
            message=message_value if isinstance(message_value, str) else "",
            overlay=bool(overlay_value) if isinstance(overlay_value, bool) else False,
        )


__all__ = ["author", "message", "system_message"]
