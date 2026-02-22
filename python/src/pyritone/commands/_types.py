from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

CommandArg = str | int | float | bool


class _CommandDispatchRequired(TypedDict):
    raw: dict[str, Any]
    command_text: str


class CommandDispatchResult(_CommandDispatchRequired, total=False):
    task_id: str | None
    accepted: bool | None


@dataclass(frozen=True, slots=True)
class CommandSpec:
    name: str
    aliases: tuple[str, ...]
    short_desc: str
    long_desc_lines: tuple[str, ...]
    usage_lines: tuple[str, ...]
    source_file: str
    domain: str
    target: str | None = None
