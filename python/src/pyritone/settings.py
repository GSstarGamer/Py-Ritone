from __future__ import annotations

from typing import TYPE_CHECKING

from .commands import CommandArg, CommandDispatchResult

if TYPE_CHECKING:
    from .client_async import AsyncPyritoneClient
    from .client_sync import PyritoneClient


class AsyncSettingHandle:
    def __init__(self, namespace: "AsyncSettingsNamespace", name: str) -> None:
        self._namespace = namespace
        self._name = name

    async def set(self, value: CommandArg) -> CommandDispatchResult:
        return await self._namespace.set(self._name, value)

    async def get(self) -> CommandDispatchResult:
        return await self._namespace.get(self._name)

    async def toggle(self) -> CommandDispatchResult:
        return await self._namespace.toggle(self._name)

    async def reset(self) -> CommandDispatchResult:
        return await self._namespace.reset(self._name)


class AsyncSettingsNamespace:
    def __init__(self, client: "AsyncPyritoneClient") -> None:
        self._client = client

    def __getattr__(self, name: str) -> AsyncSettingHandle:
        if name.startswith("_"):
            raise AttributeError(name)
        return AsyncSettingHandle(self, name)

    async def set(self, name: str, value: CommandArg) -> CommandDispatchResult:
        return await self._client.set(name, value)

    async def get(self, name: str) -> CommandDispatchResult:
        return await self._client.set(name)

    async def toggle(self, name: str) -> CommandDispatchResult:
        return await self._client.set("toggle", name)

    async def reset(self, name: str) -> CommandDispatchResult:
        return await self._client.set("reset", name)


class SyncSettingHandle:
    def __init__(self, namespace: "SyncSettingsNamespace", name: str) -> None:
        self._namespace = namespace
        self._name = name

    def set(self, value: CommandArg) -> CommandDispatchResult:
        return self._namespace.set(self._name, value)

    def get(self) -> CommandDispatchResult:
        return self._namespace.get(self._name)

    def toggle(self) -> CommandDispatchResult:
        return self._namespace.toggle(self._name)

    def reset(self) -> CommandDispatchResult:
        return self._namespace.reset(self._name)


class SyncSettingsNamespace:
    def __init__(self, client: "PyritoneClient") -> None:
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_last_dispatch", None)

    def __getattr__(self, name: str) -> SyncSettingHandle:
        if name.startswith("_"):
            raise AttributeError(name)
        return SyncSettingHandle(self, name)

    def __setattr__(self, name: str, value: CommandArg) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        dispatch = self.set(name, value)
        object.__setattr__(self, "_last_dispatch", dispatch)

    @property
    def last_dispatch(self) -> CommandDispatchResult | None:
        return self._last_dispatch

    def set(self, name: str, value: CommandArg) -> CommandDispatchResult:
        dispatch = self._client.set(name, value)
        object.__setattr__(self, "_last_dispatch", dispatch)
        return dispatch

    def get(self, name: str) -> CommandDispatchResult:
        dispatch = self._client.set(name)
        object.__setattr__(self, "_last_dispatch", dispatch)
        return dispatch

    def toggle(self, name: str) -> CommandDispatchResult:
        dispatch = self._client.set("toggle", name)
        object.__setattr__(self, "_last_dispatch", dispatch)
        return dispatch

    def reset(self, name: str) -> CommandDispatchResult:
        dispatch = self._client.set("reset", name)
        object.__setattr__(self, "_last_dispatch", dispatch)
        return dispatch
