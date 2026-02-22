from __future__ import annotations

from typing import Any, Protocol

from ..models import BridgeError
from ._types import CommandArg, CommandDispatchResult


class AsyncCommandClient(Protocol):
    async def execute(self, command: str) -> dict[str, Any]:
        ...

    async def wait_for_task(self, task_id: str) -> dict[str, Any]:
        ...


class SyncCommandClient(Protocol):
    def execute(self, command: str) -> dict[str, Any]:
        ...

    def wait_for_task(self, task_id: str) -> dict[str, Any]:
        ...


def quote_if_needed(text: str) -> str:
    if text == "":
        return '""'
    if any(character.isspace() for character in text):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return text


def serialize_command_arg(value: CommandArg) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return quote_if_needed(str(value))


def build_command_text(command: str, *args: CommandArg) -> str:
    serialized_args = [serialize_command_arg(value) for value in args]
    return " ".join([command, *serialized_args]).strip()


def extract_task_id(raw_result: dict[str, Any]) -> str | None:
    task = raw_result.get("task")
    if not isinstance(task, dict):
        return None

    task_id = task.get("task_id")
    if isinstance(task_id, str) and task_id:
        return task_id
    return None


def build_dispatch_result(command_text: str, raw_result: dict[str, Any]) -> CommandDispatchResult:
    dispatch: CommandDispatchResult = {
        "raw": raw_result,
        "command_text": command_text,
    }

    accepted = raw_result.get("accepted")
    if isinstance(accepted, bool):
        dispatch["accepted"] = accepted

    task_id = extract_task_id(raw_result)
    if task_id is not None:
        dispatch["task_id"] = task_id

    return dispatch


async def dispatch_async(client: AsyncCommandClient, command: str, *args: CommandArg) -> CommandDispatchResult:
    command_text = build_command_text(command, *args)
    raw_result = await client.execute(command_text)
    return build_dispatch_result(command_text, raw_result)


async def dispatch_and_wait_async(client: AsyncCommandClient, command: str, *args: CommandArg) -> dict[str, Any]:
    dispatch = await dispatch_async(client, command, *args)
    task_id = dispatch.get("task_id")
    if not task_id:
        raise BridgeError("BAD_RESPONSE", f"No task_id returned for command: {command}", dispatch["raw"])
    return await client.wait_for_task(task_id)


def dispatch_sync(client: SyncCommandClient, command: str, *args: CommandArg) -> CommandDispatchResult:
    command_text = build_command_text(command, *args)
    raw_result = client.execute(command_text)
    return build_dispatch_result(command_text, raw_result)


def dispatch_and_wait_sync(client: SyncCommandClient, command: str, *args: CommandArg) -> dict[str, Any]:
    dispatch = dispatch_sync(client, command, *args)
    task_id = dispatch.get("task_id")
    if not task_id:
        raise BridgeError("BAD_RESPONSE", f"No task_id returned for command: {command}", dispatch["raw"])
    return client.wait_for_task(task_id)
