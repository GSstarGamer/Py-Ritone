from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Any

from .client_async import AsyncPyritoneClient
from .commands.sync_build import SyncBuildCommands
from .commands.sync_control import SyncControlCommands
from .commands.sync_info import SyncInfoCommands
from .commands.sync_navigation import SyncNavigationCommands
from .commands.sync_waypoints import SyncWaypointsCommands
from .commands.sync_world import SyncWorldCommands
from .commands._types import CommandDispatchResult
from .models import BridgeError
from .schematic_paths import normalize_build_coords, normalize_schematic_path
from .settings import SyncSettingsNamespace


class _LoopThread:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="pyritone-sync-loop", daemon=True)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._thread.start()
        self._started = True

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coroutine):
        self.start()
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        return future.result()

    def stop(self) -> None:
        if not self._started:
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=2)
        self._started = False


class PyritoneClient(
    SyncNavigationCommands,
    SyncWorldCommands,
    SyncBuildCommands,
    SyncControlCommands,
    SyncInfoCommands,
    SyncWaypointsCommands,
):
    def __init__(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        token: str | None = None,
        bridge_info_path: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._runner = _LoopThread()
        self._client = AsyncPyritoneClient(
            host=host,
            port=port,
            token=token,
            bridge_info_path=bridge_info_path,
            timeout=timeout,
        )
        self._connected = False

        self.settings = SyncSettingsNamespace(self)

    def __enter__(self) -> "PyritoneClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def connect(self) -> None:
        if self._connected:
            return
        self._runner.run(self._client.connect())
        self._connected = True

    def close(self) -> None:
        if self._connected:
            self._runner.run(self._client.close())
            self._connected = False
        self._runner.stop()

    def ping(self) -> dict[str, Any]:
        return self._runner.run(self._client.ping())

    def status_get(self) -> dict[str, Any]:
        return self._runner.run(self._client.status_get())

    def execute(self, command: str) -> dict[str, Any]:
        return self._runner.run(self._client.execute(command))

    def cancel(self, task_id: str | None = None) -> dict[str, Any]:
        return self._runner.run(self._client.cancel(task_id))

    def next_event(self, timeout: float | None = None) -> dict[str, Any]:
        return self._runner.run(self._client.next_event(timeout=timeout))

    def wait_for_task(self, task_id: str) -> dict[str, Any]:
        return self._runner.run(self._client.wait_for_task(task_id))

    def build_file(
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
        return self.build(normalized_path, *normalized_coords)

    def build_file_wait(
        self,
        path: str | Path,
        *coords: int,
        base_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        """Dispatch `build_file` and wait for terminal task event.

        Raises `BridgeError(code=\"BAD_RESPONSE\", ...)` when dispatch response
        does not include a `task_id`.
        """
        dispatch = self.build_file(path, *coords, base_dir=base_dir)
        task_id = dispatch.get("task_id")
        if not task_id:
            raise BridgeError("BAD_RESPONSE", "No task_id returned for command: build", dispatch["raw"])
        return self.wait_for_task(task_id)
