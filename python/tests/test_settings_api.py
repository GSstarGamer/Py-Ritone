import pytest

from pyritone.settings import AsyncSettingsNamespace


class DummyAsyncClient:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.settings = AsyncSettingsNamespace(self)

    async def set(self, *args):
        self.calls.append(args)
        command_text = "set " + " ".join(str(value).lower() if isinstance(value, bool) else str(value) for value in args)
        return {"raw": {}, "command_text": command_text}


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
    assert client.calls == [
        ("allowSprint", True),
        ("allowSprint",),
        ("toggle", "allowSprint"),
        ("reset", "allowSprint"),
    ]


@pytest.mark.asyncio
async def test_async_settings_private_attribute_access_raises():
    client = DummyAsyncClient()

    with pytest.raises(AttributeError):
        _ = client.settings._missing_private

