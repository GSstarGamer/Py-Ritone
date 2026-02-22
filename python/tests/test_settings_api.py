import pytest

from pyritone.settings import AsyncSettingsNamespace, SyncSettingsNamespace


class DummySyncClient:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.settings = SyncSettingsNamespace(self)

    def set(self, *args):
        self.calls.append(args)
        command_text = "set " + " ".join(str(value).lower() if isinstance(value, bool) else str(value) for value in args)
        return {"raw": {}, "command_text": command_text}


class DummyAsyncClient:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.settings = AsyncSettingsNamespace(self)

    async def set(self, *args):
        self.calls.append(args)
        command_text = "set " + " ".join(str(value).lower() if isinstance(value, bool) else str(value) for value in args)
        return {"raw": {}, "command_text": command_text}


def test_sync_settings_attribute_assignment_and_helpers():
    client = DummySyncClient()

    client.settings.allowSprint = True
    assert client.calls[-1] == ("allowSprint", True)
    assert client.settings.last_dispatch is not None

    get_dispatch = client.settings.allowSprint.get()
    toggle_dispatch = client.settings.allowSprint.toggle()
    reset_dispatch = client.settings.allowSprint.reset()

    assert get_dispatch["command_text"] == "set allowSprint"
    assert toggle_dispatch["command_text"] == "set toggle allowSprint"
    assert reset_dispatch["command_text"] == "set reset allowSprint"


@pytest.mark.asyncio
async def test_async_settings_handle_methods():
    client = DummyAsyncClient()

    set_dispatch = await client.settings.allowSprint.set(True)
    get_dispatch = await client.settings.allowSprint.get()
    toggle_dispatch = await client.settings.allowSprint.toggle()
    reset_dispatch = await client.settings.allowSprint.reset()

    assert set_dispatch["command_text"] == "set allowSprint true"
    assert get_dispatch["command_text"] == "set allowSprint"
    assert toggle_dispatch["command_text"] == "set toggle allowSprint"
    assert reset_dispatch["command_text"] == "set reset allowSprint"
