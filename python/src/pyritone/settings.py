from __future__ import annotations

from typing import TYPE_CHECKING

from .commands import CommandArg, CommandDispatchResult

if TYPE_CHECKING:
    from .client_async import Client


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
    def __init__(self, client: "Client") -> None:
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


SettingsNamespace = AsyncSettingsNamespace
SettingHandle = AsyncSettingHandle

