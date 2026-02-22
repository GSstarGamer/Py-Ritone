import pytest

from pyritone.client_async import AsyncPyritoneClient
from pyritone.client_sync import PyritoneClient
from pyritone.commands import ALIAS_METHOD_NAMES, ALIAS_TO_CANONICAL, COMMAND_METHOD_NAMES, COMMAND_SPECS
from pyritone.commands._core import build_command_text
from pyritone.commands.async_build import AsyncBuildCommands
from pyritone.commands.async_control import AsyncControlCommands
from pyritone.commands.async_info import AsyncInfoCommands
from pyritone.commands.async_navigation import AsyncNavigationCommands
from pyritone.commands.async_waypoints import AsyncWaypointsCommands
from pyritone.commands.async_world import AsyncWorldCommands
from pyritone.commands.sync_build import SyncBuildCommands
from pyritone.commands.sync_control import SyncControlCommands
from pyritone.commands.sync_info import SyncInfoCommands
from pyritone.commands.sync_navigation import SyncNavigationCommands
from pyritone.commands.sync_waypoints import SyncWaypointsCommands
from pyritone.commands.sync_world import SyncWorldCommands


class DummyAsyncClient(
    AsyncNavigationCommands,
    AsyncWorldCommands,
    AsyncBuildCommands,
    AsyncControlCommands,
    AsyncInfoCommands,
    AsyncWaypointsCommands,
):
    def __init__(self) -> None:
        self.commands: list[str] = []

    async def execute(self, command: str) -> dict[str, object]:
        self.commands.append(command)
        return {
            "accepted": True,
            "task": {"task_id": "task-1"},
        }

    async def wait_for_task(self, task_id: str) -> dict[str, object]:
        return {
            "event": "task.completed",
            "data": {"task_id": task_id},
        }

    async def cancel(self, task_id: str | None = None) -> dict[str, object]:
        return {"canceled": True, "task_id": task_id}


class DummySyncClient(
    SyncNavigationCommands,
    SyncWorldCommands,
    SyncBuildCommands,
    SyncControlCommands,
    SyncInfoCommands,
    SyncWaypointsCommands,
):
    def __init__(self) -> None:
        self.commands: list[str] = []

    def execute(self, command: str) -> dict[str, object]:
        self.commands.append(command)
        return {
            "accepted": True,
            "task": {"task_id": "task-1"},
        }

    def wait_for_task(self, task_id: str) -> dict[str, object]:
        return {
            "event": "task.completed",
            "data": {"task_id": task_id},
        }

    def cancel(self, task_id: str | None = None) -> dict[str, object]:
        return {"canceled": True, "task_id": task_id}


def test_catalog_counts_and_absence_of_schematica():
    names = {spec.name for spec in COMMAND_SPECS}
    assert len(COMMAND_SPECS) == 42
    assert len(ALIAS_TO_CANONICAL) == 21
    assert "schematica" not in names


def test_clients_expose_all_generated_methods():
    for canonical, method_name in COMMAND_METHOD_NAMES.items():
        assert hasattr(AsyncPyritoneClient, method_name), f"Missing async method for {canonical}: {method_name}"
        assert hasattr(PyritoneClient, method_name), f"Missing sync method for {canonical}: {method_name}"

        if canonical != "cancel":
            assert getattr(AsyncPyritoneClient, method_name).__doc__
            assert getattr(PyritoneClient, method_name).__doc__

    for alias, method_name in ALIAS_METHOD_NAMES.items():
        assert hasattr(AsyncPyritoneClient, method_name), f"Missing async alias method for {alias}: {method_name}"
        assert hasattr(PyritoneClient, method_name), f"Missing sync alias method for {alias}: {method_name}"

        assert getattr(AsyncPyritoneClient, method_name).__doc__
        assert getattr(PyritoneClient, method_name).__doc__


@pytest.mark.asyncio
async def test_async_wrappers_build_expected_commands_and_wait_helpers():
    client = DummyAsyncClient()

    goto_dispatch = await client.goto(100, 70, 100)
    mine_dispatch = await client.mine("diamond_ore", "iron_ore")
    bool_dispatch = await client.set("allowBreak", True)
    terminal = await client.goto_wait(100, 70, 100)

    assert goto_dispatch["command_text"] == "goto 100 70 100"
    assert mine_dispatch["command_text"] == "mine diamond_ore iron_ore"
    assert bool_dispatch["command_text"] == "set allowBreak true"
    assert terminal["event"] == "task.completed"



def test_sync_wrappers_match_async_command_text_shape():
    client = DummySyncClient()

    goto_dispatch = client.goto(100, 70, 100)
    mine_dispatch = client.mine("diamond_ore", "iron_ore")
    terminal = client.goto_wait(100, 70, 100)

    assert goto_dispatch["command_text"] == "goto 100 70 100"
    assert mine_dispatch["command_text"] == "mine diamond_ore iron_ore"
    assert goto_dispatch["task_id"] == mine_dispatch["task_id"]
    assert terminal["data"]["task_id"] == "task-1"


def test_command_text_builder_serializes_bool_and_quotes_spaces():
    assert build_command_text("set", "allowBreak", True) == "set allowBreak true"
    assert build_command_text("mine", "deepslate diamond_ore") == 'mine "deepslate diamond_ore"'

