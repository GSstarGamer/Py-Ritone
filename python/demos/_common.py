from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable

from pyritone import AsyncPyritoneClient, BridgeError, DiscoveryError, PyritoneClient
from pyritone.models import BridgeInfo

SyncDemoFn = Callable[[PyritoneClient], int | None]
AsyncDemoFn = Callable[[AsyncPyritoneClient], Awaitable[int | None]]


def banner(title: str) -> None:
    line = "=" * max(12, len(title) + 4)
    print(f"\n{line}\n  {title}\n{line}")


def step(message: str) -> None:
    print(f"[step] {message}")


def print_json(label: str, payload: Any) -> None:
    print(f"{label}:\n{json.dumps(payload, indent=2, sort_keys=True)}")


def extract_task_id(payload: dict[str, Any]) -> str | None:
    task_id = payload.get("task_id")
    if isinstance(task_id, str) and task_id:
        return task_id

    task = payload.get("task")
    if isinstance(task, dict):
        nested_task_id = task.get("task_id")
        if isinstance(nested_task_id, str) and nested_task_id:
            return nested_task_id

    return None


def summarize_dispatch(dispatch: dict[str, Any]) -> str:
    command_text = dispatch.get("command_text")
    accepted = dispatch.get("accepted")
    task_id = extract_task_id(dispatch)

    return (
        f"command_text={command_text!r}, accepted={accepted!r}, task_id={task_id!r}"
    )


def summarize_event(event: dict[str, Any]) -> str:
    event_name = event.get("event")
    data = event.get("data")
    task_id = data.get("task_id") if isinstance(data, dict) else None
    reason = task_reason(event)

    base = f"event={event_name!r}, task_id={task_id!r}"
    if reason:
        return f"{base}, reason={reason!r}"
    return base


def task_reason(event: dict[str, Any]) -> str | None:
    data = event.get("data")
    if not isinstance(data, dict):
        return None

    for key in ("reason", "detail", "message", "error"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def parse_scalar(text: str) -> Any:
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"none", "null"}:
        return None

    try:
        return int(text)
    except ValueError:
        pass

    if any(character in text for character in (".", "e", "E")):
        try:
            return float(text)
        except ValueError:
            pass

    return text


def parse_scalars(parts: list[str]) -> list[Any]:
    return [parse_scalar(part) for part in parts]


def terminal_summary(event: dict[str, Any]) -> str:
    event_name = str(event.get("event"))
    reason = task_reason(event)

    if event_name == "task.completed":
        return "Task completed."
    if event_name == "task.canceled":
        if reason:
            return f"Task ended (canceled): {reason}"
        return "Task ended (canceled)."
    if event_name == "task.failed":
        if reason:
            return f"Task failed: {reason}"
        return "Task failed."

    if reason:
        return f"Terminal event {event_name}: {reason}"
    return f"Terminal event {event_name}"


def friendly_error_message(error: BaseException) -> tuple[int, str]:
    if isinstance(error, DiscoveryError):
        return (
            2,
            "Discovery failed. Start Minecraft with pyritone_bridge once, or set PYRITONE_TOKEN/PYRITONE_BRIDGE_INFO. "
            f"Details: {error}",
        )

    if isinstance(error, BridgeError):
        if error.code == "NOT_IN_WORLD":
            return (
                3,
                "Bridge is connected, but player is not in a world yet. Join a world, then run this demo again.",
            )
        if error.code == "BARITONE_UNAVAILABLE":
            return (
                3,
                "Bridge is connected, but Baritone is unavailable. Make sure the Baritone mod is installed and loaded.",
            )
        return 3, f"Bridge error {error.code}: {error.message}"

    if isinstance(error, ConnectionRefusedError):
        return (
            4,
            "Could not connect to the local bridge socket. Start Minecraft with pyritone_bridge + Baritone first.",
        )

    if isinstance(error, OSError):
        return (
            4,
            "Socket error while reaching the local bridge. Verify Minecraft is running and the bridge is auto-started. "
            f"Details: {error}",
        )

    return 1, f"Unexpected error: {error}"


def print_friendly_error(error: BaseException) -> int:
    exit_code, message = friendly_error_message(error)
    print(f"[error] {message}")
    return exit_code


def _bridge_info_from_client(client: PyritoneClient | AsyncPyritoneClient) -> BridgeInfo | None:
    if isinstance(client, AsyncPyritoneClient):
        return client.bridge_info

    inner_client = getattr(client, "_client", None)
    if inner_client is None:
        return None

    bridge_info = getattr(inner_client, "bridge_info", None)
    if isinstance(bridge_info, BridgeInfo):
        return bridge_info
    return None


def announce_connection(client: PyritoneClient | AsyncPyritoneClient) -> None:
    info = _bridge_info_from_client(client)
    if info is None:
        step("Connected to bridge.")
        return

    protocol_text = info.protocol_version if info.protocol_version is not None else "unknown"
    server_text = info.server_version if info.server_version is not None else "unknown"
    step(
        f"Connected to bridge at {info.host}:{info.port} (protocol={protocol_text}, server={server_text})."
    )


def run_sync_demo(title: str, demo_fn: SyncDemoFn) -> int:
    banner(title)

    try:
        with PyritoneClient() as client:
            announce_connection(client)
            result = demo_fn(client)
            step("Demo finished.")
            if isinstance(result, int):
                return result
            return 0
    except KeyboardInterrupt:
        print("[stop] Interrupted with Ctrl+C.")
        return 130
    except Exception as error:  # pragma: no cover - exercised by demo runtime
        return print_friendly_error(error)


async def _run_async_demo_inner(title: str, demo_fn: AsyncDemoFn) -> int:
    banner(title)

    client = AsyncPyritoneClient()
    await client.connect()
    announce_connection(client)

    try:
        result = await demo_fn(client)
        step("Demo finished.")
        if isinstance(result, int):
            return result
        return 0
    finally:
        await client.close()


def run_async_demo(title: str, demo_fn: AsyncDemoFn) -> int:
    try:
        return asyncio.run(_run_async_demo_inner(title, demo_fn))
    except KeyboardInterrupt:
        print("[stop] Interrupted with Ctrl+C.")
        return 130
    except Exception as error:  # pragma: no cover - exercised by demo runtime
        return print_friendly_error(error)
