from __future__ import annotations

import asyncio
import copy
import contextlib
import inspect
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from .commands.async_build import AsyncBuildCommands
from .commands.async_control import AsyncControlCommands
from .commands.async_info import AsyncInfoCommands
from .commands.async_navigation import AsyncNavigationCommands
from .commands.async_waypoints import AsyncWaypointsCommands
from .commands.async_world import AsyncWorldCommands
from .commands._types import CommandDispatchResult
from .discovery import resolve_bridge_info
from .models import BridgeError, BridgeInfo, RemoteRef, TypedCallError
from .protocol import decode_message, encode_message, new_request
from .schematic_paths import normalize_build_coords, normalize_schematic_path
from .settings import AsyncSettingsNamespace

EventPayload = dict[str, Any]
EventCheck = Callable[[EventPayload], bool]
EventCallback = Callable[[EventPayload], Any]


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
        self.settings = AsyncSettingsNamespace(self)
        self.state = ClientStateCache()
        self.task = _TaskNamespace(self)

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

        self._bridge_info = resolve_bridge_info(
            host=self._explicit_host,
            port=self._explicit_port,
            token=self._explicit_token,
            ws_url=self._explicit_ws_url,
            bridge_info_path=self._bridge_info_path,
        )

        self._logger.info("Connecting to pyritone bridge websocket: %s", self._bridge_info.ws_url)
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

        self._logger.info(
            "Connected to pyritone bridge (protocol=%s, server=%s)",
            self._bridge_info.protocol_version,
            self._bridge_info.server_version,
        )

    async def close(self) -> None:
        if self._closed and self._websocket is None and self._receive_task is None:
            return

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

    async def execute(self, command: str) -> dict[str, Any]:
        return await self._request("baritone.execute", {"command": command})

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
    ) -> EventPayload:
        deadline: float | None = None
        if timeout is not None:
            deadline = asyncio.get_running_loop().time() + timeout

        while True:
            remaining: float | None = None
            if deadline is not None:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise TimeoutError()

            event = await self.next_event(timeout=remaining)
            data = event.get("data")
            if not isinstance(data, dict):
                continue
            if data.get("task_id") != task_id:
                continue

            event_name = event.get("event")
            if isinstance(event_name, str) and event_name in self.TERMINAL_TASK_EVENTS:
                return event

            if on_update is not None:
                callback_result = on_update(event)
                if inspect.isawaitable(callback_result):
                    await callback_result

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

        if not response.get("ok", False):
            error = response.get("error") or {}
            code = str(error.get("code", "UNKNOWN"))
            message = str(error.get("message", "Unknown error"))
            details = error.get("data")
            parsed_details = details if isinstance(details, dict) else {}
            if method.startswith("api."):
                raise TypedCallError(code, message, response, parsed_details)
            raise BridgeError(code, message, response, parsed_details)

        result = response.get("result", {})
        if not isinstance(result, dict):
            raise BridgeError("BAD_RESPONSE", "Expected object result", response)
        return result

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

        if event_name == "status.update":
            status = data.get("status")
            if isinstance(status, dict):
                self.state._replace(status, ts=ts)
            return

        if event_name in {"task.started", "task.progress", "task.paused", "task.resumed"}:
            self.state._merge_active_task(data, ts=ts)
            return

        if event_name in self.TERMINAL_TASK_EVENTS:
            task_id = data.get("task_id")
            if isinstance(task_id, str) and task_id:
                self.state._clear_active_task(task_id, ts=ts)

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


AsyncPyritoneClient = Client
PyritoneClient = Client
