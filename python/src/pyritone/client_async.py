from __future__ import annotations

import asyncio
import copy
import contextlib
import contextvars
import inspect
import json
import logging
import shlex
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from .baritone import BaritoneNamespace
from .commands.async_build import AsyncBuildCommands
from .commands.async_control import AsyncControlCommands
from .commands.async_info import AsyncInfoCommands
from .commands.async_navigation import AsyncNavigationCommands
from .commands.async_waypoints import AsyncWaypointsCommands
from .commands.async_world import AsyncWorldCommands
from .commands._types import CommandArg, CommandDispatchResult
from .discovery import resolve_bridge_info
from .models import BridgeError, BridgeInfo, RemoteRef, TypedCallError, VisibleEntity
from .protocol import decode_message, encode_message, new_request
from .schematic_paths import normalize_build_coords, normalize_schematic_path
from .settings import AsyncSettingsNamespace

EventPayload = dict[str, Any]
EventCheck = Callable[[EventPayload], bool]
EventCallback = Callable[[EventPayload], Any]
_execute_notice_label: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "pyritone_execute_notice_label",
    default=None,
)
_HUMAN_LOG_PREFIX = "[Py-Ritone]"


@dataclass(slots=True)
class _EventWaiter:
    event_name: str
    check: EventCheck | None
    future: asyncio.Future[EventPayload]


class ClientStateCache:
    def __init__(self) -> None:
        self._status: dict[str, Any] = {}
        self._updated_at: str | None = None

    @property
    def updated_at(self) -> str | None:
        return self._updated_at

    @property
    def snapshot(self) -> dict[str, Any]:
        return copy.deepcopy(self._status)

    @property
    def active_task(self) -> dict[str, Any] | None:
        value = self._status.get("active_task")
        if isinstance(value, dict):
            return copy.deepcopy(value)
        return None

    @property
    def task_id(self) -> str | None:
        task = self._status.get("active_task")
        if not isinstance(task, dict):
            return None

        task_id = task.get("task_id")
        if isinstance(task_id, str) and task_id:
            return task_id
        return None

    @property
    def task_state(self) -> str | None:
        task = self._status.get("active_task")
        if not isinstance(task, dict):
            return None

        state = task.get("state")
        if isinstance(state, str) and state:
            return state
        return None

    @property
    def task_detail(self) -> str | None:
        task = self._status.get("active_task")
        if not isinstance(task, dict):
            return None

        detail = task.get("detail")
        if isinstance(detail, str):
            return detail
        return None

    def _clear(self) -> None:
        self._status = {}
        self._updated_at = None

    def _replace(self, status: dict[str, Any], *, ts: str | None = None) -> None:
        self._status = copy.deepcopy(status)
        self._updated_at = ts

    def _merge_active_task(self, task_payload: dict[str, Any], *, ts: str | None = None) -> None:
        next_status = dict(self._status)
        next_status["active_task"] = copy.deepcopy(task_payload)
        self._status = next_status
        self._updated_at = ts

    def _clear_active_task(self, task_id: str | None, *, ts: str | None = None) -> None:
        current = self._status.get("active_task")
        if not isinstance(current, dict):
            return
        if task_id is not None and current.get("task_id") != task_id:
            return

        next_status = dict(self._status)
        next_status["active_task"] = None
        self._status = next_status
        self._updated_at = ts


class _TaskNamespace:
    def __init__(self, client: "Client") -> None:
        self._client = client

    @property
    def id(self) -> str | None:
        return self._client.state.task_id

    @property
    def state(self) -> str | None:
        return self._client.state.task_state

    @property
    def detail(self) -> str | None:
        return self._client.state.task_detail

    @property
    def data(self) -> dict[str, Any] | None:
        return self._client.state.active_task

    async def wait(
        self,
        task_id: str | None = None,
        *,
        on_update: Callable[[dict[str, Any]], Any] | None = None,
        timeout: float | None = None,
    ) -> EventPayload:
        resolved_task_id = task_id or self.id
        if resolved_task_id is None:
            latest_status = await self._client.status_get()
            active_task = latest_status.get("active_task")
            if isinstance(active_task, dict):
                candidate = active_task.get("task_id")
                if isinstance(candidate, str) and candidate:
                    resolved_task_id = candidate

        if resolved_task_id is None:
            raise BridgeError(
                "NO_ACTIVE_TASK",
                "No active task available in client state cache",
                {"state": self._client.state.snapshot},
            )

        return await self._client.wait_for_task(
            resolved_task_id,
            on_update=on_update,
            timeout=timeout,
        )


class WorldView:
    def __init__(self, client: "Client") -> None:
        self._client = client

    async def get_entities(
        self,
        types: str | list[str] | tuple[str, ...] | None = None,
    ) -> list[VisibleEntity]:
        return await self._client.entities_list(types=types)


class PlayerView:
    def __init__(self, client: "Client") -> None:
        self._client = client

    async def get_entities(
        self,
        types: str | list[str] | tuple[str, ...] | None = None,
    ) -> list[VisibleEntity]:
        return await self._client.entities_list(types=types)


class Client(
    AsyncNavigationCommands,
    AsyncWorldCommands,
    AsyncBuildCommands,
    AsyncControlCommands,
    AsyncInfoCommands,
    AsyncWaypointsCommands,
):
    TERMINAL_TASK_EVENTS = {"task.completed", "task.failed", "task.canceled"}
    ANY_EVENT = "*"
    WAIT_FOR_TASK_POLL_SECONDS = 0.25
    PAUSE_EVENT_NAME = "bridge.pause_state"

    def __init__(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        token: str | None = None,
        ws_url: str | None = None,
        bridge_info_path: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._explicit_host = host
        self._explicit_port = port
        self._explicit_token = token
        self._explicit_ws_url = ws_url
        self._bridge_info_path = bridge_info_path
        self._timeout = timeout

        self._bridge_info: BridgeInfo | None = None
        self._websocket: ClientConnection | None = None
        self._receive_task: asyncio.Task[None] | None = None
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._events: asyncio.Queue[EventPayload] = asyncio.Queue()
        self._event_waiters: list[_EventWaiter] = []
        self._event_listeners: dict[str, set[EventCallback]] = defaultdict(set)
        self._listener_tasks: set[asyncio.Task[None]] = set()
        self._closed = True

        self._logger = logging.getLogger("pyritone")
        self._state_log_signatures: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {}
        self._last_status_task_signature: tuple[str | None, str | None, str | None] | None = None
        self._unexpected_close_logged = False
        self._pause_state = _default_pause_state()
        self._pause_state_seq = -1
        self.settings = AsyncSettingsNamespace(self)
        self.state = ClientStateCache()
        self.task = _TaskNamespace(self)
        self.baritone = BaritoneNamespace(self)

    async def __aenter__(self) -> "Client":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    @property
    def bridge_info(self) -> BridgeInfo | None:
        return self._bridge_info

    async def connect(self) -> None:
        if not self._closed:
            return
        self.state._clear()
        self._state_log_signatures.clear()
        self._last_status_task_signature = None
        self._unexpected_close_logged = False
        self._reset_pause_state()

        self._bridge_info = resolve_bridge_info(
            host=self._explicit_host,
            port=self._explicit_port,
            token=self._explicit_token,
            ws_url=self._explicit_ws_url,
            bridge_info_path=self._bridge_info_path,
        )

        self._log_state("connecting", ws_url=self._bridge_info.ws_url)
        self._websocket = await connect(
            self._bridge_info.ws_url,
            open_timeout=self._timeout,
            close_timeout=self._timeout,
            ping_interval=20.0,
            ping_timeout=20.0,
            logger=self._logger,
        )
        self._closed = False
        self._receive_task = asyncio.create_task(self._receive_loop(), name="pyritone-receive")

        try:
            await self._request("auth.login", {"token": self._bridge_info.token})
        except Exception:
            await self.close()
            raise

        self._log_state(
            "connected",
            protocol=self._bridge_info.protocol_version,
            server=self._bridge_info.server_version,
        )

    async def close(self) -> None:
        if self._closed and self._websocket is None and self._receive_task is None:
            return

        self._log_state_once("connection_close", "disconnecting")
        self._closed = True

        receive_task = self._receive_task
        self._receive_task = None
        if receive_task is not None:
            receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await receive_task

        websocket = self._websocket
        self._websocket = None
        if websocket is not None:
            with contextlib.suppress(Exception):
                await websocket.close()

        self._fail_pending(ConnectionError("Client closed"))
        self._fail_waiters(ConnectionError("Client closed"))
        await self._cancel_listener_tasks()
        self.state._clear()
        self._last_status_task_signature = None
        self._state_log_signatures.clear()
        self._reset_pause_state()
        self._log_state_once("connection_close_complete", "disconnected", reason="client_closed")

    def on(self, event: str, callback: EventCallback) -> Callable[[], None]:
        normalized = event or self.ANY_EVENT
        self._event_listeners[normalized].add(callback)

        def _unsubscribe() -> None:
            self.off(normalized, callback)

        return _unsubscribe

    def off(self, event: str, callback: EventCallback) -> None:
        normalized = event or self.ANY_EVENT
        callbacks = self._event_listeners.get(normalized)
        if callbacks is None:
            return

        callbacks.discard(callback)
        if not callbacks:
            self._event_listeners.pop(normalized, None)

    async def ping(self) -> dict[str, Any]:
        return await self._request("ping", {})

    async def status_get(self) -> dict[str, Any]:
        status = await self._request("status.get", {})
        self.state._replace(status)
        return status

    async def status_subscribe(self) -> dict[str, Any]:
        state_before = self.state.updated_at
        result = await self._request("status.subscribe", {})
        status = result.get("status")
        if isinstance(status, dict) and self.state.updated_at == state_before:
            self.state._replace(status)
        return result

    async def status_unsubscribe(self) -> dict[str, Any]:
        return await self._request("status.unsubscribe", {})

    async def get_world(self) -> WorldView:
        self._log_sent_debug("get_world")
        return WorldView(self)

    async def get_player(self) -> PlayerView:
        self._log_sent_debug("get_player")
        return PlayerView(self)

    async def entities_list(
        self,
        types: str | list[str] | tuple[str, ...] | None = None,
    ) -> list[VisibleEntity]:
        normalized_types = _normalize_entity_types(types)
        payload: dict[str, Any]
        if normalized_types is None:
            payload = {}
        else:
            payload = {"types": normalized_types}

        result = await self._request("entities.list", payload)
        raw_entities = result.get("entities")
        if not isinstance(raw_entities, list):
            raise BridgeError("BAD_RESPONSE", "Expected list in entities.list result.entities", result)

        entities: list[VisibleEntity] = []
        for index, raw_entity in enumerate(raw_entities):
            if not isinstance(raw_entity, dict):
                raise BridgeError("BAD_RESPONSE", f"Expected object at entities[{index}]", result)
            try:
                entities.append(VisibleEntity.from_payload(raw_entity))
            except (TypeError, ValueError) as error:
                raise BridgeError(
                    "BAD_RESPONSE",
                    f"Invalid entity payload at entities[{index}]: {error}",
                    result,
                ) from error

        return entities

    async def goto_entity(
        self,
        entity: VisibleEntity | dict[str, Any],
        *,
        wait: bool = True,
    ) -> dict[str, Any]:
        if isinstance(entity, VisibleEntity):
            visible = entity
        elif isinstance(entity, dict):
            visible = VisibleEntity.from_payload(entity)
        else:
            raise TypeError("entity must be VisibleEntity or dict[str, Any]")

        type_id_for_label = _normalize_entity_type_id(visible.type_id)
        self._log_sent("goto_entity", type_id_for_label, visible.id)
        token = _execute_notice_label.set(f"goto_entity {type_id_for_label} id={visible.id}")
        try:
            if wait:
                return await self._goto_entity_wait_with_pause_retarget(visible, type_id_for_label)
            x = round(visible.x)
            y = round(visible.y)
            z = round(visible.z)
            return await self.goto(x, y, z)
        finally:
            _execute_notice_label.reset(token)

    async def _goto_entity_wait_with_pause_retarget(
        self,
        visible: VisibleEntity,
        normalized_type_id: str,
    ) -> dict[str, Any]:
        current_visible = visible
        current_coords = _rounded_entity_coords(current_visible)

        while True:
            pause_seq_before = self._pause_state_seq
            terminal = await self.goto_wait(*current_coords)
            pause_seq_after = self._pause_state_seq
            if pause_seq_after == pause_seq_before:
                return terminal

            refreshed = await self._refresh_visible_entity(
                entity_id=current_visible.id,
                normalized_type_id=normalized_type_id,
            )
            if refreshed is None:
                raise BridgeError(
                    "ENTITY_NOT_VISIBLE",
                    f"Entity {current_visible.id} ({normalized_type_id}) is no longer visible",
                    {
                        "entity_id": current_visible.id,
                        "type_id": normalized_type_id,
                    },
                )

            refreshed_coords = _rounded_entity_coords(refreshed)
            if refreshed_coords == current_coords:
                return terminal

            current_visible = refreshed
            current_coords = refreshed_coords

    async def _refresh_visible_entity(
        self,
        *,
        entity_id: str,
        normalized_type_id: str,
    ) -> VisibleEntity | None:
        entities_now = await self.entities_list(types=[normalized_type_id])
        for candidate in entities_now:
            if candidate.id != entity_id:
                continue
            if _normalize_entity_type_id(candidate.type_id) != normalized_type_id:
                continue
            return candidate
        return None

    async def api_metadata_get(self, target: str | RemoteRef | dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if target is not None:
            payload["target"] = _encode_typed_target(target)
        return await self._request("api.metadata.get", payload)

    async def api_construct(
        self,
        type_name: str,
        *args: Any,
        parameter_types: list[str] | tuple[str, ...] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "type": type_name,
            "args": [_encode_typed_value(value) for value in args],
        }
        if parameter_types is not None:
            payload["parameter_types"] = list(parameter_types)

        result = await self._request("api.construct", payload)
        if "value" not in result:
            raise BridgeError("BAD_RESPONSE", "Expected value in api.construct result", result)
        return _decode_typed_value(result["value"])

    async def api_invoke(
        self,
        target: str | RemoteRef | dict[str, Any],
        method: str,
        *args: Any,
        parameter_types: list[str] | tuple[str, ...] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "target": _encode_typed_target(target),
            "method": method,
            "args": [_encode_typed_value(value) for value in args],
        }
        if parameter_types is not None:
            payload["parameter_types"] = list(parameter_types)

        result = await self._request("api.invoke", payload)
        if "value" not in result:
            raise BridgeError("BAD_RESPONSE", "Expected value in api.invoke result", result)
        return _decode_typed_value(result["value"])

    async def execute(self, command: str, *, label: str | None = None) -> dict[str, Any]:
        """Execute raw Baritone command text.

        Advanced escape hatch for command interop/CLI-style flows.
        Prefer generated command wrappers or typed `client.baritone.*` APIs in new code.
        """
        resolved_label = label if label is not None else _execute_notice_label.get()
        payload: dict[str, Any] = {"command": command}
        if isinstance(resolved_label, str) and resolved_label.strip():
            payload["label"] = resolved_label
        return await self._request("baritone.execute", payload)

    async def cancel(self, task_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if task_id is not None:
            payload["task_id"] = task_id
        return await self._request("task.cancel", payload)

    async def next_event(self, timeout: float | None = None) -> EventPayload:
        if timeout is None:
            return await self._events.get()
        return await asyncio.wait_for(self._events.get(), timeout=timeout)

    async def events(self):
        while not self._closed:
            yield await self.next_event()

    async def wait_for(
        self,
        event: str,
        check: EventCheck | None = None,
        timeout: float | None = None,
    ) -> EventPayload:
        self._ensure_connected()

        buffered_match = self._pop_buffered_event(event or self.ANY_EVENT, check)
        if buffered_match is not None:
            return buffered_match

        loop = asyncio.get_running_loop()
        waiter = _EventWaiter(
            event_name=event or self.ANY_EVENT,
            check=check,
            future=loop.create_future(),
        )
        self._event_waiters.append(waiter)

        try:
            if timeout is None:
                return await waiter.future
            return await asyncio.wait_for(waiter.future, timeout=timeout)
        finally:
            with contextlib.suppress(ValueError):
                self._event_waiters.remove(waiter)

    async def wait_for_task(
        self,
        task_id: str,
        *,
        on_update: Callable[[dict[str, Any]], Any] | None = None,
        timeout: float | None = None,
        prefer_path_hints: bool = False,
    ) -> EventPayload:
        self._log_state_once_debug(
            f"wait_for_task:{task_id}",
            "waiting",
            task_id=task_id,
            prefer_path_hints=prefer_path_hints,
        )
        loop = asyncio.get_running_loop()
        deadline: float | None = None
        task_paused = self._is_wait_task_paused(task_id)
        bridge_paused = self._is_effectively_paused()
        if timeout is not None:
            deadline = loop.time() + timeout

        while True:
            if self._closed and self._events.empty():
                self._log_state_once_debug(f"wait_for_task:{task_id}:closed", "disconnected", task_id=task_id)
                raise ConnectionError("Connection closed by bridge")

            remaining: float | None = None
            if deadline is not None:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    self._log_state_once_debug(f"wait_for_task:{task_id}:timeout", "wait_timeout", task_id=task_id)
                    raise TimeoutError()

            poll_timeout = remaining
            if poll_timeout is None or poll_timeout > self.WAIT_FOR_TASK_POLL_SECONDS:
                poll_timeout = self.WAIT_FOR_TASK_POLL_SECONDS

            try:
                event = await self.next_event(timeout=poll_timeout)
            except asyncio.TimeoutError:
                continue

            data = event.get("data")
            if not isinstance(data, dict):
                continue
            event_name = event.get("event")
            if event_name == self.PAUSE_EVENT_NAME:
                paused_flag = data.get("paused")
                if isinstance(paused_flag, bool):
                    bridge_paused = paused_flag
            if data.get("task_id") != task_id:
                continue

            if event_name == "task.paused":
                task_paused = True
            elif event_name == "task.resumed":
                task_paused = False
            elif event_name in {"task.started", "task.progress"}:
                state = data.get("state")
                if isinstance(state, str) and state.upper() == "PAUSED":
                    task_paused = True
                elif isinstance(state, str):
                    task_paused = False
            if (
                prefer_path_hints
                and event_name == "baritone.path_event"
            ):
                path_event = data.get("path_event")
                if path_event == "AT_GOAL":
                    terminal_event = _synthetic_task_completed_event(task_id, event)
                    self._log_wait_terminal(task_id, terminal_event, source="path_hint")
                    return terminal_event
                if path_event == "CANCELED":
                    if task_paused or bridge_paused or self._is_wait_task_paused(task_id):
                        continue
                    terminal_event = _synthetic_task_canceled_event(task_id, event)
                    self._log_wait_terminal(task_id, terminal_event, source="path_hint")
                    return terminal_event

            if isinstance(event_name, str) and event_name in self.TERMINAL_TASK_EVENTS:
                self._log_wait_terminal(task_id, event, source="event")
                return event

            if on_update is not None:
                callback_result = on_update(event)
                if inspect.isawaitable(callback_result):
                    await callback_result

    def _is_wait_task_paused(self, task_id: str) -> bool:
        if self._is_effectively_paused():
            return True

        active_task = self.state.active_task
        if not isinstance(active_task, dict):
            return False
        if active_task.get("task_id") != task_id:
            return False

        task_state = active_task.get("state")
        if isinstance(task_state, str) and task_state.upper() == "PAUSED":
            return True

        task_detail = active_task.get("detail")
        if isinstance(task_detail, str):
            normalized_detail = task_detail.strip().lower()
            if normalized_detail == "paused" or normalized_detail.startswith("paused "):
                return True

        return False

    async def goto_wait(self, x: int, y: int, z: int, *extra_args: CommandArg) -> dict[str, Any]:
        """Dispatch `goto` and wait for completion with an AT_GOAL fast path."""
        dispatch = await self.goto(x, y, z, *extra_args)
        task_id = dispatch.get("task_id")
        if not task_id:
            raise BridgeError("BAD_RESPONSE", "No task_id returned for command: goto", dispatch["raw"])
        return await self.wait_for_task(task_id, prefer_path_hints=True)

    async def build_file(
        self,
        path: str | Path,
        *coords: int,
        base_dir: str | Path | None = None,
    ) -> CommandDispatchResult:
        """Dispatch Baritone `build` using a local schematic path.

        Relative paths resolve from the calling Python file directory by default.
        Use `base_dir` to override that base path.

        Coordinate args must be either:
        - none (build at player position), or
        - exactly three ints `(x, y, z)`.
        """
        normalized_path = normalize_schematic_path(path, base_dir=base_dir)
        normalized_coords = normalize_build_coords(coords)
        return await self.build(normalized_path, *normalized_coords)

    async def build_file_wait(
        self,
        path: str | Path,
        *coords: int,
        base_dir: str | Path | None = None,
    ) -> EventPayload:
        """Dispatch `build_file` and wait for terminal task event.

        Raises `BridgeError(code="BAD_RESPONSE", ...)` when dispatch response
        does not include a `task_id`.
        """
        dispatch = await self.build_file(path, *coords, base_dir=base_dir)
        task_id = dispatch.get("task_id")
        if not task_id:
            raise BridgeError("BAD_RESPONSE", "No task_id returned for command: build", dispatch["raw"])
        return await self.wait_for_task(task_id)

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        websocket = self._ensure_connected()
        action, action_args = self._describe_request_for_log(method, params)
        first_attempt = True

        while True:
            if first_attempt:
                if _is_command_send_request(method, params):
                    self._log_sent(action, *action_args)
                else:
                    self._log_sent_debug(action, *action_args)
            else:
                self._log_state_debug("retry_after_pause", method=method, action=action)

            request = new_request(method, params)
            request_id = request["id"]

            loop = asyncio.get_running_loop()
            future: asyncio.Future[dict[str, Any]] = loop.create_future()
            self._pending[request_id] = future

            await websocket.send(encode_message(request))
            self._log_payload("send", request, sensitive=(method == "auth.login"))

            try:
                response = await asyncio.wait_for(future, timeout=self._timeout)
            finally:
                self._pending.pop(request_id, None)

            if response.get("ok", False):
                result = response.get("result", {})
                if not isinstance(result, dict):
                    self._log_received(action, {"error_code": "BAD_RESPONSE", "message": "Expected object result"})
                    raise BridgeError("BAD_RESPONSE", "Expected object result", response)
                self._log_received(action, self._summarize_result_for_log(method, result))
                return result

            error = response.get("error") or {}
            code = str(error.get("code", "UNKNOWN"))
            message = str(error.get("message", "Unknown error"))
            details = error.get("data")
            parsed_details = details if isinstance(details, dict) else {}

            if code == "PAUSED":
                self._log_received(action, {"error_code": code, "message": message})
                if not parsed_details:
                    parsed_details = {
                        "paused": True,
                        "operator_paused": False,
                        "game_paused": False,
                        "reason": "paused",
                        "seq": self._pause_state_seq,
                    }
                self._update_pause_state(parsed_details)
                await self._wait_until_resumed(min_seq=_as_int(parsed_details.get("seq")))
                first_attempt = False
                continue

            self._log_received(action, {"error_code": code, "message": message})
            if method.startswith("api."):
                raise TypedCallError(code, message, response, parsed_details)
            raise BridgeError(code, message, response, parsed_details)

    async def _receive_loop(self) -> None:
        websocket = self._websocket
        assert websocket is not None

        try:
            async for message in websocket:
                payload = decode_message(message)
                self._log_payload("recv", payload, sensitive=False)

                payload_type = payload.get("type")
                if payload_type == "response":
                    request_id = payload.get("id")
                    if isinstance(request_id, str):
                        future = self._pending.get(request_id)
                        if future is not None and not future.done():
                            future.set_result(payload)
                elif payload_type == "event":
                    await self._dispatch_event(payload)
                else:
                    self._logger.debug("Ignoring unknown payload type: %r", payload_type)
        except asyncio.CancelledError:
            raise
        except ConnectionClosed as error:
            if not self._closed:
                if not self._unexpected_close_logged:
                    self._unexpected_close_logged = True
                    self._log_state(
                        "disconnected_unexpected",
                        code=error.code,
                        reason=error.reason,
                    )
                self._logger.warning(
                    "Bridge websocket closed unexpectedly (code=%s, reason=%s)",
                    error.code,
                    error.reason,
                )
        except Exception:
            if not self._closed:
                self._logger.exception("Bridge websocket receive loop failed")
        finally:
            if not self._closed:
                self._closed = True
                self._fail_pending(ConnectionError("Connection closed by bridge"))
                self._fail_waiters(ConnectionError("Connection closed by bridge"))

    async def _dispatch_event(self, payload: EventPayload) -> None:
        self._update_state_from_event(payload)
        await self._events.put(payload)

        event_name = payload.get("event")
        if isinstance(event_name, str):
            callbacks = list(self._event_listeners.get(event_name, set()))
        else:
            callbacks = []
        callbacks.extend(self._event_listeners.get(self.ANY_EVENT, set()))

        for callback in callbacks:
            self._invoke_event_callback(callback, payload)

        for waiter in list(self._event_waiters):
            if waiter.future.done():
                with contextlib.suppress(ValueError):
                    self._event_waiters.remove(waiter)
                continue

            if waiter.event_name != self.ANY_EVENT and waiter.event_name != event_name:
                continue

            if waiter.check is not None:
                try:
                    matches = bool(waiter.check(payload))
                except Exception as error:
                    waiter.future.set_exception(error)
                    with contextlib.suppress(ValueError):
                        self._event_waiters.remove(waiter)
                    continue

                if not matches:
                    continue

            waiter.future.set_result(payload)
            with contextlib.suppress(ValueError):
                self._event_waiters.remove(waiter)

    def _update_state_from_event(self, payload: EventPayload) -> None:
        event_name = payload.get("event")
        if not isinstance(event_name, str):
            return

        event_ts = payload.get("ts")
        ts = event_ts if isinstance(event_ts, str) else None

        data = payload.get("data")
        if not isinstance(data, dict):
            return

        if event_name == self.PAUSE_EVENT_NAME:
            self._update_pause_state(data)
            self._log_pause_state(data)
            return

        if event_name == "status.update":
            status = data.get("status")
            if isinstance(status, dict):
                self.state._replace(status, ts=ts)
                reason = data.get("reason")
                self._log_status_snapshot(
                    status,
                    reason=reason if isinstance(reason, str) else None,
                )
            return

        if event_name == "baritone.path_event":
            self._log_path_event_state(data)
            return

        if event_name in {"task.started", "task.progress", "task.paused", "task.resumed"}:
            self.state._merge_active_task(data, ts=ts)
            self._log_task_event_state(event_name, data)
            return

        if event_name in self.TERMINAL_TASK_EVENTS:
            task_id = data.get("task_id")
            if isinstance(task_id, str) and task_id:
                self.state._clear_active_task(task_id, ts=ts)
            self._log_task_event_state(event_name, data)

    def _reset_pause_state(self) -> None:
        self._pause_state = _default_pause_state()
        self._pause_state_seq = -1

    def _is_effectively_paused(self) -> bool:
        paused = self._pause_state.get("paused")
        return bool(paused is True)

    def _update_pause_state(self, payload: dict[str, Any]) -> None:
        paused_value = payload.get("paused")
        if not isinstance(paused_value, bool):
            return

        operator_value = payload.get("operator_paused")
        operator_paused = operator_value if isinstance(operator_value, bool) else False
        game_value = payload.get("game_paused")
        game_paused = game_value if isinstance(game_value, bool) else False
        reason_value = payload.get("reason")
        reason = reason_value if isinstance(reason_value, str) and reason_value else _pause_reason_from_flags(
            operator_paused,
            game_paused,
        )
        seq_value = _as_int(payload.get("seq"))
        if seq_value is None:
            seq_value = self._pause_state_seq
        if seq_value is not None and seq_value < self._pause_state_seq:
            return

        self._pause_state = {
            "paused": paused_value,
            "operator_paused": operator_paused,
            "game_paused": game_paused,
            "reason": reason,
            "seq": seq_value,
        }
        if seq_value is not None:
            self._pause_state_seq = seq_value

    async def _wait_until_resumed(self, *, min_seq: int | None) -> None:
        while True:
            if self._closed:
                raise ConnectionError("Connection closed by bridge")

            if not self._is_effectively_paused():
                if min_seq is None or self._pause_state_seq >= min_seq:
                    return

            def _resume_check(payload: EventPayload) -> bool:
                data = payload.get("data")
                if not isinstance(data, dict):
                    return False
                paused = data.get("paused")
                if paused is not False:
                    return False
                event_seq = _as_int(data.get("seq"))
                if min_seq is None or event_seq is None:
                    return True
                return event_seq >= min_seq

            try:
                await self.wait_for(self.PAUSE_EVENT_NAME, check=_resume_check)
            except ConnectionError:
                raise
            except RuntimeError as error:
                raise ConnectionError("Connection closed by bridge") from error

    def _log_pause_state(self, payload: dict[str, Any]) -> None:
        paused = payload.get("paused")
        if not isinstance(paused, bool):
            return
        reason = payload.get("reason")
        seq = payload.get("seq")
        operator_paused = payload.get("operator_paused")
        game_paused = payload.get("game_paused")
        label = "paused" if paused else "resumed"
        self._log_state_once(
            "bridge:pause_state",
            label,
            paused=paused,
            reason=reason,
            seq=seq,
            operator_paused=operator_paused,
            game_paused=game_paused,
        )

    def _invoke_event_callback(self, callback: EventCallback, payload: EventPayload) -> None:
        try:
            callback_result = callback(payload)
        except Exception:
            self._logger.exception("Event callback raised")
            return

        if inspect.isawaitable(callback_result):
            task = asyncio.create_task(
                self._await_event_callback(callback_result),
                name="pyritone-event-callback",
            )
            self._listener_tasks.add(task)
            task.add_done_callback(self._listener_tasks.discard)

    async def _await_event_callback(self, callback_result: Awaitable[Any]) -> None:
        try:
            await callback_result
        except Exception:
            self._logger.exception("Async event callback raised")

    async def _cancel_listener_tasks(self) -> None:
        if not self._listener_tasks:
            return

        tasks = list(self._listener_tasks)
        self._listener_tasks.clear()
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

    def _fail_pending(self, error: BaseException) -> None:
        for future in self._pending.values():
            if not future.done():
                future.set_exception(error)
        self._pending.clear()

    def _fail_waiters(self, error: BaseException) -> None:
        for waiter in self._event_waiters:
            if not waiter.future.done():
                waiter.future.set_exception(error)
        self._event_waiters.clear()

    def _ensure_connected(self) -> ClientConnection:
        if self._closed or self._websocket is None:
            raise RuntimeError("Client is not connected")
        return self._websocket

    def _log_sent(self, action: str, *args: Any) -> None:
        if not self._logger.isEnabledFor(logging.INFO):
            return

        if args:
            self._logger.info("%s Sent %s ( %s )", _HUMAN_LOG_PREFIX, action, _format_call_args(args))
            return

        self._logger.info("%s Sent %s", _HUMAN_LOG_PREFIX, action)

    def _log_sent_debug(self, action: str, *args: Any) -> None:
        if not self._logger.isEnabledFor(logging.DEBUG):
            return

        if args:
            self._logger.debug("%s Sent %s ( %s )", _HUMAN_LOG_PREFIX, action, _format_call_args(args))
            return

        self._logger.debug("%s Sent %s", _HUMAN_LOG_PREFIX, action)

    def _log_received(self, action: str, summary: Any | None = None) -> None:
        if not self._logger.isEnabledFor(logging.DEBUG):
            return

        if summary is None:
            self._logger.debug("%s Received %s", _HUMAN_LOG_PREFIX, action)
            return

        formatted_summary = _format_summary(summary)
        if not formatted_summary:
            self._logger.debug("%s Received %s", _HUMAN_LOG_PREFIX, action)
            return
        self._logger.debug("%s Received %s ( %s )", _HUMAN_LOG_PREFIX, action, formatted_summary)

    def _log_state(self, label: str, **fields: Any) -> None:
        if not self._logger.isEnabledFor(logging.INFO):
            return

        if fields:
            self._logger.info("%s State %s ( %s )", _HUMAN_LOG_PREFIX, label, _format_fields(fields))
            return

        self._logger.info("%s State %s", _HUMAN_LOG_PREFIX, label)

    def _log_state_debug(self, label: str, **fields: Any) -> None:
        if not self._logger.isEnabledFor(logging.DEBUG):
            return

        if fields:
            self._logger.debug("%s State %s ( %s )", _HUMAN_LOG_PREFIX, label, _format_fields(fields))
            return

        self._logger.debug("%s State %s", _HUMAN_LOG_PREFIX, label)

    def _log_state_once(self, key: str, label: str, **fields: Any) -> None:
        signature = (label, _signature_fields(fields))
        if self._state_log_signatures.get(key) == signature:
            return
        self._state_log_signatures[key] = signature
        self._log_state(label, **fields)

    def _log_state_once_debug(self, key: str, label: str, **fields: Any) -> None:
        if not self._logger.isEnabledFor(logging.DEBUG):
            return
        signature = (label, _signature_fields(fields))
        if self._state_log_signatures.get(key) == signature:
            return
        self._state_log_signatures[key] = signature
        self._log_state_debug(label, **fields)

    def _log_wait_terminal(self, task_id: str, event: EventPayload, *, source: str) -> None:
        event_name = event.get("event")
        data = event.get("data")
        payload = data if isinstance(data, dict) else {}

        label = "terminal"
        if event_name == "task.completed":
            label = "completed"
        elif event_name == "task.failed":
            label = "failed"
        elif event_name == "task.canceled":
            label = "canceled"

        fields: dict[str, Any] = {
            "task_id": task_id,
            "event": event_name,
            "source": source,
        }
        detail = payload.get("detail")
        if isinstance(detail, str) and detail:
            fields["detail"] = detail
        stage = payload.get("stage")
        if isinstance(stage, str) and stage:
            fields["stage"] = stage
        reason = payload.get("reason")
        if isinstance(reason, str) and reason:
            fields["reason"] = reason
        self._log_state_once_debug(f"wait_for_task:{task_id}:terminal", label, **fields)

    def _describe_request_for_log(self, method: str, params: dict[str, Any]) -> tuple[str, tuple[Any, ...]]:
        if method == "auth.login":
            return ("auth_login", ("***",))
        if method == "baritone.execute":
            return _describe_execute_request(params)

        if method == "task.cancel":
            task_id = params.get("task_id")
            if isinstance(task_id, str) and task_id:
                return ("cancel", (task_id,))
            return ("cancel", ())

        if method == "entities.list":
            types = params.get("types")
            if isinstance(types, list):
                return ("entities_list", tuple(types))
            return ("entities_list", ())

        if method == "api.metadata.get":
            target = params.get("target")
            if target is None:
                return ("api_metadata_get", ())
            return ("api_metadata_get", (_summarize_typed_target(target),))

        if method == "api.construct":
            type_name = params.get("type")
            args = params.get("args")
            arg_count = len(args) if isinstance(args, list) else 0
            return ("api_construct", (type_name, f"args={arg_count}"))

        if method == "api.invoke":
            target = _summarize_typed_target(params.get("target"))
            invoke_method = params.get("method")
            args = params.get("args")
            arg_count = len(args) if isinstance(args, list) else 0
            return ("api_invoke", (invoke_method, target, f"args={arg_count}"))

        action = _rpc_action_name(method)
        return (action, ())

    def _summarize_result_for_log(self, method: str, result: dict[str, Any]) -> Any | None:
        if method == "ping":
            pong = result.get("pong")
            if isinstance(pong, bool):
                return {"pong": pong}
            return None

        if method == "entities.list":
            entities = result.get("entities")
            if isinstance(entities, list):
                return {"count": len(entities)}
            return None

        if method == "baritone.execute":
            summary: dict[str, Any] = {}
            accepted = result.get("accepted")
            if isinstance(accepted, bool):
                summary["accepted"] = accepted
            task_id = _extract_task_id(result)
            if task_id is not None:
                summary["task_id"] = task_id
            return summary or None

        if method in {"status.get", "status.subscribe"}:
            status_payload = result
            if method == "status.subscribe":
                nested = result.get("status")
                if isinstance(nested, dict):
                    status_payload = nested
            return _summarize_status(status_payload)

        if method == "status.unsubscribe":
            summary: dict[str, Any] = {}
            subscribed = result.get("subscribed")
            if isinstance(subscribed, bool):
                summary["subscribed"] = subscribed
            was_subscribed = result.get("was_subscribed")
            if isinstance(was_subscribed, bool):
                summary["was_subscribed"] = was_subscribed
            return summary or None

        if method == "task.cancel":
            canceled = result.get("canceled")
            if isinstance(canceled, bool):
                return {"canceled": canceled}
            return None

        if method == "api.construct":
            summary: dict[str, Any] = {}
            java_type = result.get("java_type")
            if isinstance(java_type, str) and java_type:
                summary["java_type"] = java_type
            if "value" in result:
                summary["value_type"] = _summarize_value_type(result.get("value"))
            return summary or None

        if method == "api.invoke":
            summary = {}
            return_type = result.get("return_type")
            if isinstance(return_type, str) and return_type:
                summary["return_type"] = return_type
            if "value" in result:
                summary["value_type"] = _summarize_value_type(result.get("value"))
            return summary or None

        if method == "api.metadata.get":
            summary = {}
            roots = result.get("roots")
            if isinstance(roots, list):
                summary["roots"] = len(roots)
            type_meta = result.get("type")
            if isinstance(type_meta, dict):
                methods = type_meta.get("methods")
                constructors = type_meta.get("constructors")
                if isinstance(methods, list):
                    summary["methods"] = len(methods)
                if isinstance(constructors, list):
                    summary["constructors"] = len(constructors)
            return summary or None

        if "task" in result:
            task_id = _extract_task_id(result)
            if task_id:
                return {"task_id": task_id}
        return None

    def _log_status_snapshot(self, status: dict[str, Any], *, reason: str | None) -> None:
        active_task = status.get("active_task")
        if not isinstance(active_task, dict):
            if self._last_status_task_signature is not None:
                self._last_status_task_signature = None
                fields: dict[str, Any] = {"source": "status.update"}
                if reason:
                    fields["reason"] = reason
                self._log_state_once_debug("status:update:idle", "idle", **fields)
            return

        task_id = active_task.get("task_id") if isinstance(active_task.get("task_id"), str) else None
        task_state = active_task.get("state") if isinstance(active_task.get("state"), str) else None
        task_detail = active_task.get("detail") if isinstance(active_task.get("detail"), str) else None
        signature = (task_id, task_state, task_detail)
        if self._last_status_task_signature == signature:
            return
        self._last_status_task_signature = signature

        normalized_state = task_state.upper() if isinstance(task_state, str) else ""
        if normalized_state in {"PENDING", "RUNNING"}:
            label = "working"
        elif normalized_state:
            label = normalized_state.lower()
        else:
            label = "working"

        fields = {"task_id": task_id, "state": task_state, "detail": task_detail, "source": "status.update"}
        if reason:
            fields["reason"] = reason
        self._log_state_once_debug(f"status:update:{task_id or 'unknown'}", label, **fields)

    def _log_task_event_state(self, event_name: str, data: dict[str, Any]) -> None:
        task_id = data.get("task_id") if isinstance(data.get("task_id"), str) else None
        detail = data.get("detail") if isinstance(data.get("detail"), str) and data.get("detail") else None
        stage = data.get("stage") if isinstance(data.get("stage"), str) and data.get("stage") else None

        if event_name in {"task.started", "task.progress"}:
            fields: dict[str, Any] = {"task_id": task_id}
            if detail is not None:
                fields["detail"] = detail
            if stage is not None:
                fields["stage"] = stage
            self._log_state_once_debug(f"task:{task_id or 'unknown'}:working", "working", **fields)
            return

        if event_name == "task.paused":
            pause_payload = data.get("pause")
            fields = {"task_id": task_id}
            if isinstance(pause_payload, dict):
                reason_code = pause_payload.get("reason_code")
                if isinstance(reason_code, str) and reason_code:
                    fields["reason"] = reason_code
                source_process = pause_payload.get("source_process")
                if isinstance(source_process, str) and source_process:
                    fields["source_process"] = source_process
                command_type = pause_payload.get("command_type")
                if isinstance(command_type, str) and command_type:
                    fields["command_type"] = command_type
            self._log_state_once_debug(f"task:{task_id or 'unknown'}:paused", "paused", **fields)
            return

        if event_name == "task.resumed":
            fields = {"task_id": task_id}
            if detail is not None:
                fields["detail"] = detail
            self._log_state_once_debug(f"task:{task_id or 'unknown'}:resumed", "working", **fields)
            return

        if event_name in self.TERMINAL_TASK_EVENTS:
            label_map = {
                "task.completed": "completed",
                "task.failed": "failed",
                "task.canceled": "canceled",
            }
            fields = {"task_id": task_id}
            if detail is not None:
                fields["detail"] = detail
            if stage is not None:
                fields["stage"] = stage
            self._log_state_once_debug(
                f"task:{task_id or 'unknown'}:terminal",
                label_map.get(event_name, "terminal"),
                **fields,
            )

    def _log_path_event_state(self, data: dict[str, Any]) -> None:
        path_event = data.get("path_event")
        if not isinstance(path_event, str) or not path_event:
            return

        task_id = data.get("task_id") if isinstance(data.get("task_id"), str) else None
        normalized = path_event.strip().upper()

        label = "path_event"
        if "CALC" in normalized and "FAIL" in normalized:
            label = "calculation_failed"
        elif "CALC" in normalized and ("FINISH" in normalized or "SUCCESS" in normalized):
            label = "best_path_ready"
        elif "CALC" in normalized and "START" in normalized:
            label = "calculating"
        elif normalized == "AT_GOAL":
            label = "at_goal"
        elif normalized == "CANCELED":
            label = "canceled"
        elif "EXECUT" in normalized or "PATH" in normalized or "MOVE" in normalized:
            label = "moving"

        self._log_state_once_debug(
            f"path_event:{task_id or 'none'}",
            label,
            task_id=task_id,
            path_event=normalized,
        )

    def _log_typed_wait_transition(
        self,
        *,
        handle_id: str,
        action: str,
        moving: bool,
        calculating: bool,
    ) -> None:
        label = "moving" if moving else "working"
        self._log_state_once_debug(
            f"typed_wait:{handle_id}:transition",
            label,
            handle_id=handle_id,
            action=action,
            moving=moving,
            calculating=calculating,
        )

    def _log_typed_wait_best_path(
        self,
        *,
        handle_id: str,
        action: str,
        has_path: bool,
    ) -> None:
        if not has_path:
            return
        self._log_state_once_debug(
            f"typed_wait:{handle_id}:best_path",
            "best_path_ready",
            handle_id=handle_id,
            action=action,
        )

    def _log_typed_wait_complete(
        self,
        *,
        handle_id: str,
        action: str,
        started: bool,
        has_path: bool,
    ) -> None:
        self._log_state_once_debug(
            f"typed_wait:{handle_id}:complete",
            "working",
            handle_id=handle_id,
            action=action,
            started=started,
            moving=False,
            calculating=False,
            has_path=has_path,
        )

    def _log_payload(self, direction: str, payload: EventPayload, *, sensitive: bool) -> None:
        if not self._logger.isEnabledFor(logging.DEBUG):
            return

        if sensitive:
            safe_payload = _redact_sensitive_payload(payload)
        else:
            safe_payload = payload

        self._logger.debug("%s %s", direction, json.dumps(safe_payload, sort_keys=True))

    def _pop_buffered_event(self, event_name: str, check: EventCheck | None) -> EventPayload | None:
        buffered = getattr(self._events, "_queue", None)
        if buffered is None:
            return None

        for payload in list(buffered):
            payload_event_name = payload.get("event")
            if event_name != self.ANY_EVENT and event_name != payload_event_name:
                continue

            if check is not None:
                if not check(payload):
                    continue

            with contextlib.suppress(ValueError):
                buffered.remove(payload)
            return payload

        return None


_RPC_ACTION_NAMES: dict[str, str] = {
    "auth.login": "auth_login",
    "ping": "ping",
    "status.get": "status_get",
    "status.subscribe": "status_subscribe",
    "status.unsubscribe": "status_unsubscribe",
    "entities.list": "entities_list",
    "api.metadata.get": "api_metadata_get",
    "api.construct": "api_construct",
    "api.invoke": "api_invoke",
    "baritone.execute": "execute",
    "task.cancel": "cancel",
}


def _rpc_action_name(method: str) -> str:
    return _RPC_ACTION_NAMES.get(method, method.replace(".", "_"))


def _is_command_send_request(method: str, params: dict[str, Any]) -> bool:
    if method == "baritone.execute":
        return not _is_execute_log_suppressed(params)
    if method == "task.cancel":
        return True
    return False


def _is_execute_log_suppressed(params: dict[str, Any]) -> bool:
    label = params.get("label")
    if not isinstance(label, str):
        return False
    normalized = label.strip().lower()
    return normalized.startswith("goto_entity ")


def _describe_execute_request(params: dict[str, Any]) -> tuple[str, tuple[Any, ...]]:
    command = params.get("command")
    if not isinstance(command, str) or not command.strip():
        return ("execute", ())

    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.strip().split()

    if not tokens:
        return ("execute", ())

    return (tokens[0], tuple(tokens[1:]))


def _extract_task_id(payload: dict[str, Any]) -> str | None:
    task = payload.get("task")
    if isinstance(task, dict):
        task_id = task.get("task_id")
        if isinstance(task_id, str) and task_id:
            return task_id

    task_id = payload.get("task_id")
    if isinstance(task_id, str) and task_id:
        return task_id
    return None


def _summarize_status(payload: dict[str, Any]) -> dict[str, Any] | None:
    summary: dict[str, Any] = {}
    authenticated = payload.get("authenticated")
    if isinstance(authenticated, bool):
        summary["authenticated"] = authenticated
    baritone_available = payload.get("baritone_available")
    if isinstance(baritone_available, bool):
        summary["baritone_available"] = baritone_available
    in_world = payload.get("in_world")
    if isinstance(in_world, bool):
        summary["in_world"] = in_world

    active_task = payload.get("active_task")
    if isinstance(active_task, dict):
        task_id = active_task.get("task_id")
        if isinstance(task_id, str) and task_id:
            summary["task_id"] = task_id
        state = active_task.get("state")
        if isinstance(state, str) and state:
            summary["task_state"] = state
    elif active_task is None:
        summary["task_state"] = "none"
    return summary or None


def _summarize_value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, dict):
        if isinstance(value.get("$pyritone_ref"), str):
            return "remote_ref"
        return "object"
    if isinstance(value, list):
        return "list"
    return type(value).__name__


def _summarize_typed_target(target: Any) -> str:
    if isinstance(target, RemoteRef):
        return f"ref:{target.ref_id}"
    if isinstance(target, str):
        return target
    if isinstance(target, dict):
        kind = target.get("kind")
        if kind == "root":
            name = target.get("name")
            return f"root:{name}" if isinstance(name, str) and name else "root"
        if kind == "ref":
            ref_id = target.get("id")
            return f"ref:{ref_id}" if isinstance(ref_id, str) and ref_id else "ref"
        if kind == "type":
            name = target.get("name")
            return f"type:{name}" if isinstance(name, str) and name else "type"
        return _truncate_text(json.dumps(target, sort_keys=True, default=str))
    return _format_log_value(target)


def _format_summary(summary: Any) -> str:
    if isinstance(summary, dict):
        return _format_fields(summary)
    if isinstance(summary, (list, tuple)):
        return _format_call_args(summary)
    return _format_log_value(summary)


def _format_call_args(args: tuple[Any, ...] | list[Any]) -> str:
    return ", ".join(_format_log_value(arg) for arg in args)


def _format_fields(fields: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in fields.items():
        if value is None:
            continue
        parts.append(f"{key}={_format_log_value(value)}")
    return ", ".join(parts)


def _signature_fields(fields: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, _format_log_value(value)) for key, value in fields.items() if value is not None))


def _format_log_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return _truncate_text(" ".join(value.split()))
    if isinstance(value, RemoteRef):
        if value.java_type:
            return _truncate_text(f"ref:{value.ref_id}:{value.java_type}")
        return _truncate_text(f"ref:{value.ref_id}")
    if isinstance(value, dict):
        return _truncate_text(json.dumps(value, sort_keys=True, default=str))
    if isinstance(value, list):
        rendered = "[" + ", ".join(_format_log_value(item) for item in value[:5]) + "]"
        if len(value) > 5:
            rendered = rendered[:-1] + ", ...]"
        return _truncate_text(rendered)
    if isinstance(value, tuple):
        rendered = "(" + ", ".join(_format_log_value(item) for item in value[:5]) + ")"
        if len(value) > 5:
            rendered = rendered[:-1] + ", ...)"
        return _truncate_text(rendered)
    return _truncate_text(str(value))


def _truncate_text(text: str, *, max_len: int = 160) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _redact_sensitive_payload(payload: EventPayload) -> EventPayload:
    method = payload.get("method")
    if method != "auth.login":
        return payload

    params = payload.get("params")
    if not isinstance(params, dict):
        return payload

    redacted = dict(payload)
    redacted_params = dict(params)
    if "token" in redacted_params:
        redacted_params["token"] = "***"
    redacted["params"] = redacted_params
    return redacted


def _normalize_entity_types(
    types: str | list[str] | tuple[str, ...] | None,
) -> list[str] | None:
    if types is None:
        return None

    raw_types: list[str]
    if isinstance(types, str):
        raw_types = [types]
    elif isinstance(types, (list, tuple)):
        raw_types = list(types)
    else:
        raise TypeError("types must be None, a string, or a list/tuple of strings")

    normalized: list[str] = []
    for index, entry in enumerate(raw_types):
        if not isinstance(entry, str):
            raise TypeError(f"types[{index}] must be a string")
        token = entry.strip()
        if not token:
            raise ValueError(f"types[{index}] must be a non-empty string")
        normalized.append(token)
    return normalized


def _normalize_entity_type_id(type_id: str) -> str:
    token = type_id.strip()
    if not token:
        return token
    if ":" in token:
        return token
    return f"minecraft:{token}"


def _rounded_entity_coords(entity: VisibleEntity) -> tuple[int, int, int]:
    return (round(entity.x), round(entity.y), round(entity.z))


def _default_pause_state() -> dict[str, Any]:
    return {
        "paused": False,
        "operator_paused": False,
        "game_paused": False,
        "reason": "resumed",
        "seq": -1,
    }


def _pause_reason_from_flags(operator_paused: bool, game_paused: bool) -> str:
    if operator_paused and game_paused:
        return "operator_and_game_pause"
    if operator_paused:
        return "operator_pause"
    if game_paused:
        return "game_pause"
    return "resumed"


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _synthetic_task_completed_event(task_id: str, source_event: EventPayload) -> EventPayload:
    data: dict[str, Any] = {
        "task_id": task_id,
        "detail": "Reached goal",
        "stage": "at_goal_hint",
    }
    payload: EventPayload = {
        "type": "event",
        "event": "task.completed",
        "data": data,
    }
    ts = source_event.get("ts")
    if isinstance(ts, str):
        payload["ts"] = ts
    return payload


def _synthetic_task_canceled_event(task_id: str, source_event: EventPayload) -> EventPayload:
    data: dict[str, Any] = {
        "task_id": task_id,
        "detail": "Baritone canceled",
        "stage": "canceled_hint",
    }
    payload: EventPayload = {
        "type": "event",
        "event": "task.canceled",
        "data": data,
    }
    ts = source_event.get("ts")
    if isinstance(ts, str):
        payload["ts"] = ts
    return payload


def _encode_typed_target(target: str | RemoteRef | dict[str, Any]) -> dict[str, Any]:
    if isinstance(target, RemoteRef):
        return {"kind": "ref", "id": target.ref_id}
    if isinstance(target, str):
        return {"kind": "root", "name": target}
    if isinstance(target, dict):
        return target
    raise TypeError(f"Unsupported typed target: {type(target)!r}")


def _encode_typed_value(value: Any) -> Any:
    if isinstance(value, RemoteRef):
        payload: dict[str, Any] = {"$pyritone_ref": value.ref_id}
        if value.java_type:
            payload["java_type"] = value.java_type
        return payload
    if isinstance(value, tuple):
        return [_encode_typed_value(item) for item in value]
    if isinstance(value, list):
        return [_encode_typed_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode_typed_value(item) for key, item in value.items()}
    return value


def _decode_typed_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode_typed_value(item) for item in value]
    if isinstance(value, dict):
        reference_id = value.get("$pyritone_ref")
        if isinstance(reference_id, str) and reference_id:
            java_type = value.get("java_type")
            return RemoteRef(reference_id, java_type if isinstance(java_type, str) else None)
        return {key: _decode_typed_value(item) for key, item in value.items()}
    return value


# Compatibility aliases retained for the v0.2.x migration window.
AsyncPyritoneClient = Client
PyritoneClient = Client
