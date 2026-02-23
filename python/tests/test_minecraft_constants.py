from __future__ import annotations

from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve

from pyritone.baritone import TypedTaskHandle
from pyritone.client_async import AsyncPyritoneClient
from pyritone.minecraft import blocks, entities, items
from pyritone.minecraft._identifiers import BlockId, EntityId, ItemId
from pyritone.protocol import decode_message, encode_message


async def _start_server(handler):
    server = await serve(handler, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()[:2]
    return server, f"ws://{host}:{port}/ws"


def test_minecraft_identifier_constants_are_namespaced_and_typed():
    assert isinstance(blocks.STONE, BlockId)
    assert isinstance(items.DIAMOND, ItemId)
    assert isinstance(entities.ZOMBIE, EntityId)

    assert blocks.STONE == "minecraft:stone"
    assert items.DIAMOND == "minecraft:diamond"
    assert entities.ZOMBIE == "minecraft:zombie"

    assert blocks.from_id("diamond_ore") == "minecraft:diamond_ore"
    assert items.from_id("minecraft:iron_ingot") == "minecraft:iron_ingot"
    assert entities.from_id("skeleton").path == "skeleton"


def test_entity_group_constants_are_exported():
    assert entities.GROUP_PLAYERS == "group:players"
    assert entities.GROUP_MOBS == "group:mobs"
    assert "GROUP_PLAYERS" in entities.__all__
    assert "GROUP_MOBS" in entities.__all__


@pytest.mark.asyncio
async def test_block_constants_interop_with_typed_baritone_wrappers():
    observed_constructs: list[dict[str, Any]] = []
    observed_invokes: list[dict[str, Any]] = []

    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")

            if method == "auth.login":
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {"protocol_version": 2, "server_version": "test"},
                        }
                    )
                )
                continue

            if method == "api.construct":
                observed_constructs.append(request["params"])
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {
                                "value": {
                                    "$pyritone_ref": "block-meta-1",
                                    "java_type": "baritone.api.utils.BlockOptionalMeta",
                                },
                                "java_type": "baritone.api.utils.BlockOptionalMeta",
                            },
                        }
                    )
                )
                continue

            if method == "api.invoke":
                params = request["params"]
                observed_invokes.append(params)
                target = params["target"]
                invoke_method = params["method"]

                if target == {"kind": "root", "name": "baritone"} and invoke_method == "getGetToBlockProcess":
                    await websocket.send(
                        encode_message(
                            {
                                "type": "response",
                                "id": request["id"],
                                "ok": True,
                                "result": {
                                    "value": {
                                        "$pyritone_ref": "get-to-block-1",
                                        "java_type": "baritone.api.process.IGetToBlockProcess",
                                    },
                                    "return_type": "baritone.api.process.IGetToBlockProcess",
                                },
                            }
                        )
                    )
                    continue

                if target == {"kind": "root", "name": "baritone"} and invoke_method == "getMineProcess":
                    await websocket.send(
                        encode_message(
                            {
                                "type": "response",
                                "id": request["id"],
                                "ok": True,
                                "result": {
                                    "value": {
                                        "$pyritone_ref": "mine-1",
                                        "java_type": "baritone.api.process.IMineProcess",
                                    },
                                    "return_type": "baritone.api.process.IMineProcess",
                                },
                            }
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "get-to-block-1"} and invoke_method == "getToBlock":
                    await websocket.send(
                        encode_message(
                            {
                                "type": "response",
                                "id": request["id"],
                                "ok": True,
                                "result": {"value": None, "return_type": "void"},
                            }
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "mine-1"} and invoke_method == "mineByName":
                    await websocket.send(
                        encode_message(
                            {
                                "type": "response",
                                "id": request["id"],
                                "ok": True,
                                "result": {"value": None, "return_type": "void"},
                            }
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
        get_to_block_process = await client.baritone.get_to_block_process()
        get_to_block_handle = await get_to_block_process.get_to_block_dispatch(blocks.DIAMOND_ORE)
        assert isinstance(get_to_block_handle, TypedTaskHandle)

        mine_process = await client.baritone.mine_process()
        mine_handle = await mine_process.mine_by_name_dispatch(32, blocks.COAL_ORE, blocks.IRON_ORE)
        assert isinstance(mine_handle, TypedTaskHandle)

        assert observed_constructs == [
            {
                "type": "baritone.api.utils.BlockOptionalMeta",
                "args": ["minecraft:diamond_ore"],
                "parameter_types": ["java.lang.String"],
            }
        ]

        get_to_block_calls = [call for call in observed_invokes if call["method"] == "getToBlock"]
        assert get_to_block_calls == [
            {
                "target": {"kind": "ref", "id": "get-to-block-1"},
                "method": "getToBlock",
                "args": [{"$pyritone_ref": "block-meta-1", "java_type": "baritone.api.utils.BlockOptionalMeta"}],
                "parameter_types": ["baritone.api.utils.BlockOptionalMeta"],
            }
        ]

        mine_calls = [call for call in observed_invokes if call["method"] == "mineByName"]
        assert mine_calls == [
            {
                "target": {"kind": "ref", "id": "mine-1"},
                "method": "mineByName",
                "args": [32, ["minecraft:coal_ore", "minecraft:iron_ore"]],
                "parameter_types": ["int", "java.lang.String[]"],
            }
        ]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_item_and_entity_constants_coerce_through_typed_api_invoke():
    observed_invokes: list[dict[str, Any]] = []

    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")

            if method == "auth.login":
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {"protocol_version": 2, "server_version": "test"},
                        }
                    )
                )
                continue

            if method == "api.invoke":
                observed_invokes.append(request["params"])
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {"value": True, "return_type": "boolean"},
                        }
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
        result = await client.api_invoke(
            "baritone",
            "echoConstants",
            items.DIAMOND,
            entities.ZOMBIE,
            parameter_types=["java.lang.String", "java.lang.String"],
        )
        assert result is True

        assert observed_invokes == [
            {
                "target": {"kind": "root", "name": "baritone"},
                "method": "echoConstants",
                "args": ["minecraft:diamond", "minecraft:zombie"],
                "parameter_types": ["java.lang.String", "java.lang.String"],
            }
        ]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()
