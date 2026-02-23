from __future__ import annotations

from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve

from pyritone.client_async import AsyncPyritoneClient
from pyritone.models import RemoteRef
from pyritone.protocol import decode_message, encode_message


async def _start_server(handler):
    server = await serve(handler, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()[:2]
    return server, f"ws://{host}:{port}/ws"


def _ok_response(request: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "response",
        "id": request["id"],
        "ok": True,
        "result": result,
    }


def _invoke_result(ref_id: str, java_type: str, *, return_type: str) -> dict[str, Any]:
    return {
        "value": {
            "$pyritone_ref": ref_id,
            "java_type": java_type,
        },
        "return_type": return_type,
    }


def _construct_result(ref_id: str, java_type: str) -> dict[str, Any]:
    return {
        "value": {
            "$pyritone_ref": ref_id,
            "java_type": java_type,
        },
        "java_type": java_type,
    }


@pytest.mark.asyncio
async def test_wave7_cache_and_selection_wrappers_use_explicit_signatures():
    observed_invokes: list[dict[str, Any]] = []
    observed_constructs: list[dict[str, Any]] = []

    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")

            if method == "auth.login":
                await websocket.send(
                    encode_message(
                        _ok_response(request, {"protocol_version": 2, "server_version": "test"}),
                    )
                )
                continue

            if method == "api.construct":
                params = request["params"]
                observed_constructs.append(params)
                if params["type"] == "baritone.api.utils.BetterBlockPos":
                    x, y, z = params["args"]
                    ref_id = f"pos-{x}-{y}-{z}"
                    await websocket.send(encode_message(_ok_response(request, _construct_result(ref_id, "baritone.api.utils.BetterBlockPos"))))
                    continue

            if method == "api.invoke":
                params = request["params"]
                observed_invokes.append(params)
                target = params["target"]

                if target == {"kind": "root", "name": "baritone"} and params["method"] == "getWorldProvider":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result("world-provider-1", "baritone.api.cache.IWorldProvider", return_type="baritone.api.cache.IWorldProvider"),
                            )
                        )
                    )
                    continue

                if target == {"kind": "type", "name": "baritone.api.cache.IWaypoint$Tag"} and params["method"] == "valueOf":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result("tag-home", "baritone.api.cache.IWaypoint$Tag", return_type="baritone.api.cache.IWaypoint$Tag"),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "world-provider-1"} and params["method"] == "getCurrentWorld":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result("world-data-1", "baritone.api.cache.IWorldData", return_type="baritone.api.cache.IWorldData"),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "world-data-1"} and params["method"] == "getWaypoints":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result(
                                    "waypoints-1",
                                    "baritone.api.cache.IWaypointCollection",
                                    return_type="baritone.api.cache.IWaypointCollection",
                                ),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "waypoints-1"} and params["method"] == "getByTag":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                {
                                    "value": [
                                        {"$pyritone_ref": "waypoint-1", "java_type": "baritone.api.cache.Waypoint"},
                                    ],
                                    "return_type": "java.util.Set",
                                },
                            )
                        )
                    )
                    continue

                if target == {"kind": "root", "name": "baritone"} and params["method"] == "getSelectionManager":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result(
                                    "selection-manager-1",
                                    "baritone.api.selection.ISelectionManager",
                                    return_type="baritone.api.selection.ISelectionManager",
                                ),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "selection-manager-1"} and params["method"] == "addSelection":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result("selection-1", "baritone.api.selection.ISelection", return_type="baritone.api.selection.ISelection"),
                            )
                        )
                    )
                    continue

            await websocket.send(
                encode_message(
                    {
                        "type": "response",
                        "id": request["id"],
                        "ok": False,
                        "error": {"code": "METHOD_NOT_FOUND", "message": "Unknown"},
                    }
                )
            )

    server, ws_url = await _start_server(handler)
    client = AsyncPyritoneClient(ws_url=ws_url, token="token")
    try:
        await client.connect()

        world_provider = await client.baritone.world_provider()
        world_data = await world_provider.current_world()
        assert world_data is not None
        waypoints = await world_data.waypoints()
        tagged = await waypoints.by_tag("home")
        assert [waypoint.ref.ref_id for waypoint in tagged] == ["waypoint-1"]

        selection_manager = await client.baritone.selection_manager()
        selection = await selection_manager.add_selection_points((1, 64, 1), (3, 70, 3))
        assert selection.ref.ref_id == "selection-1"

        enum_calls = [call for call in observed_invokes if call["target"] == {"kind": "type", "name": "baritone.api.cache.IWaypoint$Tag"}]
        assert enum_calls == [
            {
                "target": {"kind": "type", "name": "baritone.api.cache.IWaypoint$Tag"},
                "method": "valueOf",
                "args": ["HOME"],
                "parameter_types": ["java.lang.String"],
            }
        ]

        by_tag_calls = [call for call in observed_invokes if call["method"] == "getByTag"]
        assert by_tag_calls == [
            {
                "target": {"kind": "ref", "id": "waypoints-1"},
                "method": "getByTag",
                "args": [{"$pyritone_ref": "tag-home", "java_type": "baritone.api.cache.IWaypoint$Tag"}],
                "parameter_types": ["baritone.api.cache.IWaypoint$Tag"],
            }
        ]

        add_selection_calls = [call for call in observed_invokes if call["method"] == "addSelection"]
        assert add_selection_calls == [
            {
                "target": {"kind": "ref", "id": "selection-manager-1"},
                "method": "addSelection",
                "args": [
                    {"$pyritone_ref": "pos-1-64-1", "java_type": "baritone.api.utils.BetterBlockPos"},
                    {"$pyritone_ref": "pos-3-70-3", "java_type": "baritone.api.utils.BetterBlockPos"},
                ],
                "parameter_types": ["baritone.api.utils.BetterBlockPos", "baritone.api.utils.BetterBlockPos"],
            }
        ]

        assert observed_constructs == [
            {
                "type": "baritone.api.utils.BetterBlockPos",
                "args": [1, 64, 1],
                "parameter_types": ["int", "int", "int"],
            },
            {
                "type": "baritone.api.utils.BetterBlockPos",
                "args": [3, 70, 3],
                "parameter_types": ["int", "int", "int"],
            },
        ]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_wave7_command_and_event_wrappers_use_explicit_signatures():
    observed_invokes: list[dict[str, Any]] = []

    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")

            if method == "auth.login":
                await websocket.send(encode_message(_ok_response(request, {"protocol_version": 2, "server_version": "test"})))
                continue

            if method == "api.invoke":
                params = request["params"]
                observed_invokes.append(params)
                target = params["target"]

                if target == {"kind": "root", "name": "baritone"} and params["method"] == "getCommandManager":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result(
                                    "command-manager-1",
                                    "baritone.api.command.manager.ICommandManager",
                                    return_type="baritone.api.command.manager.ICommandManager",
                                ),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "command-manager-1"} and params["method"] == "tabComplete":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result("stream-1", "java.util.stream.ReferencePipeline$Head", return_type="java.util.stream.Stream"),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "stream-1"} and params["method"] == "toArray":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                {"value": ["goto", "goal"], "return_type": "java.lang.Object[]"},
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "command-manager-1"} and params["method"] == "getCommand":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result("command-help", "baritone.api.command.ICommand", return_type="baritone.api.command.ICommand"),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "command-help"} and params["method"] == "getLongDesc":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                {"value": ["line 1", "line 2"], "return_type": "java.util.List"},
                            )
                        )
                    )
                    continue

                if target == {"kind": "root", "name": "baritone"} and params["method"] == "getGameEventHandler":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result(
                                    "event-bus-1",
                                    "baritone.api.event.listener.IEventBus",
                                    return_type="baritone.api.event.listener.IEventBus",
                                ),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "event-bus-1"} and params["method"] == "registerEventListener":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                {"value": None, "return_type": "void"},
                            )
                        )
                    )
                    continue

            await websocket.send(
                encode_message(
                    {
                        "type": "response",
                        "id": request["id"],
                        "ok": False,
                        "error": {"code": "METHOD_NOT_FOUND", "message": "Unknown"},
                    }
                )
            )

    server, ws_url = await _start_server(handler)
    client = AsyncPyritoneClient(ws_url=ws_url, token="token")
    try:
        await client.connect()

        command_manager = await client.baritone.command_manager()
        completions = await command_manager.tab_complete("go")
        assert completions == ["goto", "goal"]

        command = await command_manager.command("help")
        assert command is not None
        assert await command.long_desc() == ["line 1", "line 2"]

        event_bus = await client.baritone.game_event_handler()
        await event_bus.register_event_listener(RemoteRef(ref_id="listener-1", java_type="baritone.api.event.listener.IGameEventListener"))

        tab_complete_calls = [call for call in observed_invokes if call["method"] == "tabComplete"]
        assert tab_complete_calls == [
            {
                "target": {"kind": "ref", "id": "command-manager-1"},
                "method": "tabComplete",
                "args": ["go"],
                "parameter_types": ["java.lang.String"],
            }
        ]

        to_array_calls = [call for call in observed_invokes if call["target"] == {"kind": "ref", "id": "stream-1"}]
        assert to_array_calls == [
            {
                "target": {"kind": "ref", "id": "stream-1"},
                "method": "toArray",
                "args": [],
                "parameter_types": [],
            }
        ]

        register_calls = [call for call in observed_invokes if call["method"] == "registerEventListener"]
        assert register_calls == [
            {
                "target": {"kind": "ref", "id": "event-bus-1"},
                "method": "registerEventListener",
                "args": [{"$pyritone_ref": "listener-1", "java_type": "baritone.api.event.listener.IGameEventListener"}],
                "parameter_types": ["baritone.api.event.listener.IGameEventListener"],
            }
        ]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_wave7_provider_schematic_and_utils_wrappers_use_explicit_signatures():
    observed_invokes: list[dict[str, Any]] = []
    observed_constructs: list[dict[str, Any]] = []

    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")

            if method == "auth.login":
                await websocket.send(encode_message(_ok_response(request, {"protocol_version": 2, "server_version": "test"})))
                continue

            if method == "api.construct":
                params = request["params"]
                observed_constructs.append(params)
                if params["type"] == "baritone.api.utils.BlockOptionalMeta":
                    await websocket.send(
                        encode_message(_ok_response(request, _construct_result("bom-1", "baritone.api.utils.BlockOptionalMeta")))
                    )
                    continue
                if params["type"] == "baritone.api.schematic.FillSchematic":
                    await websocket.send(
                        encode_message(_ok_response(request, _construct_result("fill-1", "baritone.api.schematic.FillSchematic")))
                    )
                    continue

            if method == "api.invoke":
                params = request["params"]
                observed_invokes.append(params)
                target = params["target"]

                if target == {"kind": "type", "name": "baritone.api.BaritoneAPI"} and params["method"] == "getProvider":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result("provider-1", "baritone.api.IBaritoneProvider", return_type="baritone.api.IBaritoneProvider"),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "provider-1"} and params["method"] == "getSchematicSystem":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result(
                                    "schematic-system-1",
                                    "baritone.api.schematic.ISchematicSystem",
                                    return_type="baritone.api.schematic.ISchematicSystem",
                                ),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "schematic-system-1"} and params["method"] == "getFileExtensions":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                {"value": ["schem", "litematic"], "return_type": "java.util.List"},
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "fill-1"} and params["method"] == "getBom":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result(
                                    "bom-2",
                                    "baritone.api.utils.BlockOptionalMeta",
                                    return_type="baritone.api.utils.BlockOptionalMeta",
                                ),
                            )
                        )
                    )
                    continue

                if target == {"kind": "root", "name": "baritone"} and params["method"] == "getInputOverrideHandler":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result(
                                    "input-override-1",
                                    "baritone.api.utils.IInputOverrideHandler",
                                    return_type="baritone.api.utils.IInputOverrideHandler",
                                ),
                            )
                        )
                    )
                    continue

                if target == {"kind": "type", "name": "baritone.api.utils.input.Input"} and params["method"] == "valueOf":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                _invoke_result(
                                    "input-sprint",
                                    "baritone.api.utils.input.Input",
                                    return_type="baritone.api.utils.input.Input",
                                ),
                            )
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "input-override-1"} and params["method"] == "setInputForceState":
                    await websocket.send(
                        encode_message(
                            _ok_response(
                                request,
                                {"value": None, "return_type": "void"},
                            )
                        )
                    )
                    continue

            await websocket.send(
                encode_message(
                    {
                        "type": "response",
                        "id": request["id"],
                        "ok": False,
                        "error": {"code": "METHOD_NOT_FOUND", "message": "Unknown"},
                    }
                )
            )

    server, ws_url = await _start_server(handler)
    client = AsyncPyritoneClient(ws_url=ws_url, token="token")
    try:
        await client.connect()

        schematic_system = await client.baritone.schematic_system()
        assert await schematic_system.file_extensions() == ["schem", "litematic"]

        fill = await client.baritone.fill_schematic(3, 4, 5, "minecraft:stone")
        bom = await fill.block_optional_meta()
        assert bom.ref_id == "bom-2"

        input_override = await client.baritone.input_override_handler()
        await input_override.set_input_force_state("sprint", True)

        provider_calls = [call for call in observed_invokes if call["target"] == {"kind": "type", "name": "baritone.api.BaritoneAPI"}]
        assert provider_calls == [
            {
                "target": {"kind": "type", "name": "baritone.api.BaritoneAPI"},
                "method": "getProvider",
                "args": [],
                "parameter_types": [],
            }
        ]

        input_enum_calls = [call for call in observed_invokes if call["target"] == {"kind": "type", "name": "baritone.api.utils.input.Input"}]
        assert input_enum_calls == [
            {
                "target": {"kind": "type", "name": "baritone.api.utils.input.Input"},
                "method": "valueOf",
                "args": ["SPRINT"],
                "parameter_types": ["java.lang.String"],
            }
        ]

        set_input_calls = [call for call in observed_invokes if call["method"] == "setInputForceState"]
        assert set_input_calls == [
            {
                "target": {"kind": "ref", "id": "input-override-1"},
                "method": "setInputForceState",
                "args": [
                    {"$pyritone_ref": "input-sprint", "java_type": "baritone.api.utils.input.Input"},
                    True,
                ],
                "parameter_types": ["baritone.api.utils.input.Input", "boolean"],
            }
        ]

        assert observed_constructs == [
            {
                "type": "baritone.api.utils.BlockOptionalMeta",
                "args": ["minecraft:stone"],
                "parameter_types": ["java.lang.String"],
            },
            {
                "type": "baritone.api.schematic.FillSchematic",
                "args": [3, 4, 5, {"$pyritone_ref": "bom-1", "java_type": "baritone.api.utils.BlockOptionalMeta"}],
                "parameter_types": ["int", "int", "int", "baritone.api.utils.BlockOptionalMeta"],
            },
        ]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()
