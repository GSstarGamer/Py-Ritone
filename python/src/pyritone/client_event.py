from __future__ import annotations

import asyncio
import contextlib
import inspect
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from .client_async import AsyncPyritoneClient
from .minecraft import chat as minecraft_chat
from .minecraft import player as minecraft_player

RawEventPayload = dict[str, Any]
RawEventCheck = Callable[[RawEventPayload], bool]
RawEventCallback = Callable[[RawEventPayload], Any]
EventCallback = Callable[..., Awaitable[Any]]
EventCheck = Callable[..., bool]


@dataclass(slots=True)
class _EventWaiter:
    event_name: str
    check: EventCheck | None
    future: asyncio.Future[Any]


class Client:
    _RAW_EVENT_TO_HANDLERS: dict[str, tuple[str, ...]] = {
        "minecraft.chat_message": ("on_chat_message", "on_message"),
        "minecraft.system_message": ("on_system_message",),
        "minecraft.player_join": ("on_player_join",),
        "minecraft.player_leave": ("on_player_leave",),
        "minecraft.player_death": ("on_player_death",),
        "minecraft.player_respawn": ("on_player_respawn",),
        "status.update": ("on_status_update",),
        "baritone.path_event": ("on_path_event",),
        "task.started": ("on_task_started",),
        "task.progress": ("on_task_progress",),
        "task.paused": ("on_task_paused",),
        "task.resumed": ("on_task_resumed",),
        "task.completed": ("on_task_completed",),
        "task.failed": ("on_task_failed",),
        "task.canceled": ("on_task_canceled",),
    }
    _WAIT_FOR_ALIASES: dict[str, str] = {
        "ready": "on_ready",
        "disconnect": "on_disconnect",
        "message": "on_message",
        "chat_message": "on_chat_message",
        "system_message": "on_system_message",
        "player_join": "on_player_join",
        "player_leave": "on_player_leave",
        "player_death": "on_player_death",
        "player_respawn": "on_player_respawn",
        "status_update": "on_status_update",
        "path_event": "on_path_event",
        "task_started": "on_task_started",
        "task_progress": "on_task_progress",
        "task_paused": "on_task_paused",
        "task_resumed": "on_task_resumed",
        "task_completed": "on_task_completed",
        "task_failed": "on_task_failed",
        "task_canceled": "on_task_canceled",
    }

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
        self._raw = AsyncPyritoneClient(
            host=host,
            port=port,
            token=token,
            ws_url=ws_url,
            bridge_info_path=bridge_info_path,
            timeout=timeout,
        )
        self._logger = logging.getLogger("pyritone")
        self._event_handlers: dict[str, EventCallback] = {}
        self._event_waiters: list[_EventWaiter] = []
        self._raw_unsubscribe: Callable[[], None] | None = None
        self._started = False

    @property
    def raw(self) -> AsyncPyritoneClient:
        return self._raw

    @property
    def player(self) -> minecraft_player.player | None:
        snapshot = self._raw.state.snapshot
        raw_player = snapshot.get("player")
        if not isinstance(raw_player, dict):
            return None
        return minecraft_player.player.from_payload(raw_player)

    def event(self, callback: EventCallback) -> EventCallback:
        if not inspect.iscoroutinefunction(callback):
            raise TypeError("@client.event requires an async function")
        self._event_handlers[callback.__name__] = callback
        return callback

    def on(self, event: str, callback: RawEventCallback) -> Callable[[], None]:
        return self._raw.on(event, callback)

    def off(self, event: str, callback: RawEventCallback) -> None:
        self._raw.off(event, callback)

    async def next_event(self, timeout: float | None = None) -> RawEventPayload:
        return await self._raw.next_event(timeout=timeout)

    async def events(self):
        async for payload in self._raw.events():
            yield payload

    async def wait_for(
        self,
        event: str,
        check: EventCheck | RawEventCheck | None = None,
        timeout: float | None = None,
    ) -> Any:
        normalized = (event or "").strip()
        if not normalized:
            raise ValueError("event name is required")

        if "." in normalized:
            raw_check = check if check is None or callable(check) else None
            return await self._raw.wait_for(normalized, check=raw_check, timeout=timeout)

        loop = asyncio.get_running_loop()
        waiter = _EventWaiter(
            event_name=self._normalize_high_level_event_name(normalized),
            check=check if check is None or callable(check) else None,
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

    async def start(self) -> None:
        if self._started:
            raise RuntimeError("Client is already running")

        self._started = True
        connected = False
        try:
            await self._raw.connect()
            connected = True
            self._raw_unsubscribe = self._raw.on(self._raw.ANY_EVENT, self._on_raw_event)
            try:
                await self._raw.status_get()
            except Exception:
                self._logger.debug("Initial status_get failed during start()", exc_info=True)
            await self._dispatch_high_level("on_ready")

            receive_task = getattr(self._raw, "_receive_task", None)
            if receive_task is not None:
                with contextlib.suppress(asyncio.CancelledError):
                    await receive_task
        finally:
            unsubscribe = self._raw_unsubscribe
            self._raw_unsubscribe = None
            if unsubscribe is not None:
                unsubscribe()

            self._fail_high_level_waiters(ConnectionError("Client disconnected"))
            if connected:
                await self._dispatch_high_level("on_disconnect")
            self._started = False

    async def close(self) -> None:
        await self._raw.close()

    def run(self) -> None:
        asyncio.run(self.start())

    def connect(self) -> None:
        self.run()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw, name)

    async def _on_raw_event(self, payload: RawEventPayload) -> None:
        event_name = payload.get("event")
        if not isinstance(event_name, str):
            return

        data = payload.get("data")
        parsed_data = data if isinstance(data, dict) else {}

        if event_name == "minecraft.chat_message":
            context = minecraft_chat.message.from_payload(parsed_data)
            await self._dispatch_high_level("on_chat_message", context)
            await self._dispatch_high_level("on_message", context)
            return

        if event_name == "minecraft.system_message":
            context = minecraft_chat.system_message.from_payload(parsed_data)
            await self._dispatch_high_level("on_system_message", context)
            return

        if event_name == "minecraft.player_join":
            context = minecraft_player.join.from_payload(parsed_data)
            await self._dispatch_high_level("on_player_join", context)
            return

        if event_name == "minecraft.player_leave":
            context = minecraft_player.leave.from_payload(parsed_data)
            await self._dispatch_high_level("on_player_leave", context)
            return

        if event_name == "minecraft.player_death":
            context = minecraft_player.death.from_payload(parsed_data)
            await self._dispatch_high_level("on_player_death", context)
            return

        if event_name == "minecraft.player_respawn":
            context = minecraft_player.respawn.from_payload(parsed_data)
            await self._dispatch_high_level("on_player_respawn", context)
            return

        handlers = self._RAW_EVENT_TO_HANDLERS.get(event_name)
        if handlers is None:
            return
        for handler_name in handlers:
            await self._dispatch_high_level(handler_name, payload)

    async def _dispatch_high_level(self, event_name: str, *args: Any) -> None:
        self._resolve_high_level_waiters(event_name, args)
        handler = self._event_handlers.get(event_name)
        if handler is None:
            return

        try:
            await handler(*args)
        except Exception as error:
            await self._dispatch_error(event_name, error, *args)

    async def _dispatch_error(self, event_name: str, error: Exception, *args: Any) -> None:
        handler = self._event_handlers.get("on_error")
        if handler is None:
            self._logger.error(
                "Unhandled exception in %s",
                event_name,
                exc_info=(type(error), error, error.__traceback__),
            )
            return

        try:
            await handler(event_name, error, *args)
        except Exception:
            self._logger.exception("Unhandled exception in on_error")

    def _resolve_high_level_waiters(self, event_name: str, args: tuple[Any, ...]) -> None:
        for waiter in list(self._event_waiters):
            if waiter.future.done():
                with contextlib.suppress(ValueError):
                    self._event_waiters.remove(waiter)
                continue

            if waiter.event_name != event_name:
                continue

            if waiter.check is not None:
                try:
                    matches = bool(waiter.check(*args))
                except Exception as error:
                    waiter.future.set_exception(error)
                    with contextlib.suppress(ValueError):
                        self._event_waiters.remove(waiter)
                    continue
                if not matches:
                    continue

            if len(args) == 0:
                result: Any = None
            elif len(args) == 1:
                result = args[0]
            else:
                result = args
            waiter.future.set_result(result)
            with contextlib.suppress(ValueError):
                self._event_waiters.remove(waiter)

    def _fail_high_level_waiters(self, error: BaseException) -> None:
        for waiter in self._event_waiters:
            if not waiter.future.done():
                waiter.future.set_exception(error)
        self._event_waiters.clear()

    def _normalize_high_level_event_name(self, event: str) -> str:
        normalized = event.strip().lower()
        if normalized.startswith("on_"):
            return normalized
        if normalized in self._WAIT_FOR_ALIASES:
            return self._WAIT_FOR_ALIASES[normalized]
        return f"on_{normalized}"


EventClient = Client
