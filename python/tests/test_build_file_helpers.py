from __future__ import annotations

from pathlib import Path

import pytest

from pyritone.client_async import AsyncPyritoneClient, Client
from pyritone.client_sync import PyritoneClient
from pyritone.commands._core import build_command_text
from pyritone.models import BridgeError
from pyritone.schematic_paths import normalize_build_coords, normalize_schematic_path


def _resolve_from_here(relative_path: str) -> str:
    return normalize_schematic_path(relative_path)


class FakeAsyncBuildClient(AsyncPyritoneClient):
    def __init__(self, dispatch: dict[str, object]) -> None:
        self._dispatch = dispatch
        self.build_calls: list[tuple[object, ...]] = []
        self.wait_calls: list[str] = []

    async def build(self, *args):
        self.build_calls.append(args)
        return self._dispatch

    async def wait_for_task(self, task_id: str):
        self.wait_calls.append(task_id)
        return {"event": "task.completed", "data": {"task_id": task_id}}


def test_pyritone_client_alias_is_async():
    assert PyritoneClient is Client


def test_relative_path_defaults_to_caller_file_directory():
    expected = (Path(__file__).resolve().parent / "local_house.schem").resolve().as_posix()
    assert _resolve_from_here("local_house.schem") == expected


def test_base_dir_override_wins(tmp_path):
    base_dir = tmp_path / "schematics"
    base_dir.mkdir()

    resolved = normalize_schematic_path("castle.schem", base_dir=base_dir)
    assert resolved == (base_dir / "castle.schem").resolve().as_posix()


def test_absolute_path_stays_absolute(tmp_path):
    absolute = (tmp_path / "tower.schem").resolve()
    resolved = normalize_schematic_path(absolute)
    assert resolved == absolute.as_posix()


def test_no_extension_prefers_existing_schem_then_schematic_then_litematic(tmp_path):
    base_dir = tmp_path / "schematics"
    base_dir.mkdir()

    schematic = base_dir / "fort.schematic"
    schem = base_dir / "fort.schem"
    litematic = base_dir / "fort.litematic"
    schematic.write_text("", encoding="utf-8")
    schem.write_text("", encoding="utf-8")
    litematic.write_text("", encoding="utf-8")

    resolved = normalize_schematic_path("fort", base_dir=base_dir)
    assert resolved == schem.resolve().as_posix()


def test_no_extension_without_existing_files_falls_back_to_bare_path(tmp_path):
    base_dir = tmp_path / "schematics"
    base_dir.mkdir()

    resolved = normalize_schematic_path("missing_schematic", base_dir=base_dir)
    assert resolved == (base_dir / "missing_schematic").resolve().as_posix()


def test_paths_with_spaces_are_quoted_correctly(tmp_path):
    base_dir = tmp_path / "schematics"
    base_dir.mkdir()

    resolved = normalize_schematic_path("my build.schem", base_dir=base_dir)
    command_text = build_command_text("build", resolved)
    assert command_text == f'build "{resolved}"'


def test_invalid_coordinate_count_raises():
    with pytest.raises(ValueError, match="either 0 or 3 coordinates"):
        normalize_build_coords((1, 2))


def test_invalid_coordinate_type_raises():
    with pytest.raises(ValueError, match="coordinates must be integers"):
        normalize_build_coords((1, 2, True))


@pytest.mark.asyncio
async def test_async_build_file_wait_returns_terminal_event(tmp_path):
    client = FakeAsyncBuildClient({"raw": {}, "command_text": "build x", "task_id": "task-2", "accepted": True})
    event = await client.build_file_wait("house.schem", 100, 70, 100, base_dir=tmp_path)

    assert event["event"] == "task.completed"
    assert client.wait_calls == ["task-2"]
    assert len(client.build_calls) == 1
    assert client.build_calls[0][0] == (tmp_path / "house.schem").resolve().as_posix()
    assert client.build_calls[0][1:] == (100, 70, 100)


@pytest.mark.asyncio
async def test_async_build_file_wait_raises_when_task_id_missing(tmp_path):
    client = FakeAsyncBuildClient({"raw": {}, "command_text": "build x", "accepted": True})

    with pytest.raises(BridgeError) as error:
        await client.build_file_wait("house.schem", base_dir=tmp_path)

    assert error.value.code == "BAD_RESPONSE"
    assert error.value.message == "No task_id returned for command: build"
    assert error.value.payload == {}
