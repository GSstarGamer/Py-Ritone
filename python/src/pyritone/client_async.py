from __future__ import annotations

import asyncio
import contextlib
import inspect
from pathlib import Path
from typing import Any, Callable

from .commands.async_build import AsyncBuildCommands
from .commands.async_control import AsyncControlCommands
from .commands.async_info import AsyncInfoCommands
from .commands.async_navigation import AsyncNavigationCommands
from .commands.async_waypoints import AsyncWaypointsCommands
from .commands.async_world import AsyncWorldCommands
from .commands._types import CommandDispatchResult
from .discovery import resolve_bridge_info
from .models import BridgeError, BridgeInfo
from .protocol import decode_line, encode_line, new_request
from .schematic_paths import normalize_build_coords, normalize_schematic_path
from .settings import AsyncSettingsNamespace


class AsyncPyritoneClient(
    AsyncNavigationCommands,
    AsyncWorldCommands,
    AsyncBuildCommands,
    AsyncControlCommands,
    AsyncInfoCommands,
    AsyncWaypointsCommands,
):
    TERMINAL_TASK_EVENTS = {"task.completed", "task.failed", "task.canceled"}

    def __init__(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        token: str | None = None,
        bridge_info_path: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._explicit_host = host
        self._explicit_port = port
        self._explicit_token = token
        self._bridge_info_path = bridge_info_path
        self._timeout = timeout

        self._bridge_info: BridgeInfo | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._listen_task: asyncio.Task[None] | None = None
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._events: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._closed = True

        self.settings = AsyncSettingsNamespace(self)

    @property
    def bridge_info(self) -> BridgeInfo | None:
        return self._bridge_info

    async def connect(self) -> None:
        if not self._closed:
            return

        self._bridge_info = resolve_bridge_info(
            host=self._explicit_host,
            port=self._explicit_port,
            token=self._explicit_token,
            bridge_info_path=self._bridge_info_path,
        )

        self._reader, self._writer = await asyncio.open_connection(self._bridge_info.host, self._bridge_info.port)
        self._closed = False
        self._listen_task = asyncio.create_task(self._listen_loop(), name="pyritone-listen")

        try:
            await self._request("auth.login", {"token": self._bridge_info.token})
        except Exception:
            await self.close()
            raise

    async def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        if self._listen_task is not None:
            self._listen_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task
            self._listen_task = None

        if self._writer is not None:
            self._writer.close()
            with contextlib.suppress(Exception):
                await self._writer.wait_closed()

        self._reader = None
        self._writer = None

        for future in self._pending.values():
            if not future.done():
                future.set_exception(ConnectionError("Client closed"))
        self._pending.clear()

    async def ping(self) -> dict[str, Any]:
        return await self._request("ping", {})

    async def status_get(self) -> dict[str, Any]:
        return await self._request("status.get", {})

    async def execute(self, command: str) -> dict[str, Any]:
        return await self._request("baritone.execute", {"command": command})

    async def cancel(self, task_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if task_id is not None:
            payload["task_id"] = task_id
        return await self._request("task.cancel", payload)

    async def next_event(self, timeout: float | None = None) -> dict[str, Any]:
        if timeout is None:
            return await self._events.get()
        return await asyncio.wait_for(self._events.get(), timeout=timeout)

    async def events(self):
        while not self._closed:
            yield await self.next_event()

    async def wait_for_task(
        self,
        task_id: str,
        *,
        on_update: Callable[[dict[str, Any]], Any] | None = None,
    ) -> dict[str, Any]:
        while True:
            event = await self.next_event()
            event_name = event.get("event")
            data = event.get("data")
            if not isinstance(data, dict):
                continue

            if data.get("task_id") != task_id:
                continue

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
    ) -> dict[str, Any]:
        """Dispatch `build_file` and wait for terminal task event.

        Raises `BridgeError(code=\"BAD_RESPONSE\", ...)` when dispatch response
        does not include a `task_id`.
        """
        dispatch = await self.build_file(path, *coords, base_dir=base_dir)
        task_id = dispatch.get("task_id")
        if not task_id:
            raise BridgeError("BAD_RESPONSE", "No task_id returned for command: build", dispatch["raw"])
        return await self.wait_for_task(task_id)

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._ensure_connected()
        assert self._writer is not None

        request = new_request(method, params)
        request_id = request["id"]

        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[request_id] = future

        self._writer.write(encode_line(request))
        await self._writer.drain()

        try:
            response = await asyncio.wait_for(future, timeout=self._timeout)
        finally:
            self._pending.pop(request_id, None)

        if not response.get("ok", False):
            error = response.get("error") or {}
            raise BridgeError(str(error.get("code", "UNKNOWN")), str(error.get("message", "Unknown error")), response)

        result = response.get("result", {})
        if not isinstance(result, dict):
            raise BridgeError("BAD_RESPONSE", "Expected object result", response)
        return result

    async def _listen_loop(self) -> None:
        assert self._reader is not None

        while not self._closed:
            line = await self._reader.readline()
            if not line:
                break

            payload = decode_line(line)
            payload_type = payload.get("type")

            if payload_type == "response":
                request_id = payload.get("id")
                if isinstance(request_id, str):
                    future = self._pending.get(request_id)
                    if future is not None and not future.done():
                        future.set_result(payload)
            elif payload_type == "event":
                await self._events.put(payload)

        if not self._closed:
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(ConnectionError("Connection closed by bridge"))
            self._pending.clear()
            self._closed = True

    def _ensure_connected(self) -> None:
        if self._closed or self._writer is None:
            raise RuntimeError("Client is not connected")
