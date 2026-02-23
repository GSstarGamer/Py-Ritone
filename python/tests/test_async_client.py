from __future__ import annotations

from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve

from pyritone.client_async import AsyncPyritoneClient
from pyritone.models import BridgeError
from pyritone.protocol import decode_message, encode_message


async def _start_server(handler):
    server = await serve(handler, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()[:2]
    return server, f"ws://{host}:{port}/ws"


@pytest.mark.asyncio
async def test_async_client_ping_and_event():
    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")

            if method == "auth.login":
                response = {
                    "type": "response",
                    "id": request["id"],
                    "ok": True,
                    "result": {"protocol_version": 2, "server_version": "test"},
                }
                await websocket.send(encode_message(response))
                continue

            if method == "ping":
                response = {
                    "type": "response",
                    "id": request["id"],
                    "ok": True,
                    "result": {"pong": True},
                }
                event = {
                    "type": "event",
                    "event": "task.progress",
                    "data": {"task_id": "x"},
                    "ts": "2026-01-01T00:00:00Z",
                }
                await websocket.send(encode_message(response))
                await websocket.send(encode_message(event))
                continue

            response = {
                "type": "response",
                "id": request["id"],
                "ok": False,
                "error": {"code": "METHOD_NOT_FOUND", "message": "Unknown"},
            }
            await websocket.send(encode_message(response))

    server, ws_url = await _start_server(handler)

    client = AsyncPyritoneClient(ws_url=ws_url, token="token")
    try:
        await client.connect()
        ping = await client.ping()
        assert ping["pong"] is True

        event = await client.next_event(timeout=1.0)
        assert event["event"] == "task.progress"
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_wait_for_task_returns_terminal_event_for_matching_task_id():
    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")

            if method == "auth.login":
                response = {
                    "type": "response",
                    "id": request["id"],
                    "ok": True,
                    "result": {"protocol_version": 2, "server_version": "test"},
                }
                await websocket.send(encode_message(response))

                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.progress",
                            "data": {"task_id": "other"},
                            "ts": "2026-01-01T00:00:00Z",
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.progress",
                            "data": {"task_id": "target"},
                            "ts": "2026-01-01T00:00:01Z",
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.completed",
                            "data": {"task_id": "target"},
                            "ts": "2026-01-01T00:00:02Z",
                        }
                    )
                )
                continue

            response = {
                "type": "response",
                "id": request["id"],
                "ok": False,
                "error": {"code": "METHOD_NOT_FOUND", "message": "Unknown"},
            }
            await websocket.send(encode_message(response))

    server, ws_url = await _start_server(handler)

    client = AsyncPyritoneClient(ws_url=ws_url, token="token")
    try:
        await client.connect()
        event = await client.wait_for_task("target")
        assert event["event"] == "task.completed"
        assert event["data"]["task_id"] == "target"
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_wait_for_task_on_update_receives_non_terminal_matching_events():
    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")

            if method == "auth.login":
                response = {
                    "type": "response",
                    "id": request["id"],
                    "ok": True,
                    "result": {"protocol_version": 2, "server_version": "test"},
                }
                await websocket.send(encode_message(response))

                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.progress",
                            "data": {"task_id": "other", "detail": "skip me"},
                            "ts": "2026-01-01T00:00:00Z",
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.progress",
                            "data": {"task_id": "target", "detail": "Working"},
                            "ts": "2026-01-01T00:00:01Z",
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.paused",
                            "data": {
                                "task_id": "target",
                                "pause": {"reason_code": "BUILDER_PAUSED"},
                            },
                            "ts": "2026-01-01T00:00:02Z",
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.resumed",
                            "data": {"task_id": "target"},
                            "ts": "2026-01-01T00:00:03Z",
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.completed",
                            "data": {"task_id": "target"},
                            "ts": "2026-01-01T00:00:04Z",
                        }
                    )
                )
                continue

            response = {
                "type": "response",
                "id": request["id"],
                "ok": False,
                "error": {"code": "METHOD_NOT_FOUND", "message": "Unknown"},
            }
            await websocket.send(encode_message(response))

    server, ws_url = await _start_server(handler)

    updates: list[str] = []

    client = AsyncPyritoneClient(ws_url=ws_url, token="token")
    try:
        await client.connect()
        terminal = await client.wait_for_task(
            "target",
            on_update=lambda event: updates.append(str(event.get("event"))),
        )
        assert terminal["event"] == "task.completed"
        assert updates == ["task.progress", "task.paused", "task.resumed"]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_wait_for_event_with_check():
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
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.progress",
                            "data": {"task_id": "a", "stage": "start"},
                            "ts": "2026-01-01T00:00:00Z",
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.progress",
                            "data": {"task_id": "b", "stage": "target"},
                            "ts": "2026-01-01T00:00:01Z",
                        }
                    )
                )
                continue

            await websocket.send(
                encode_message(
                    {
                        "type": "response",
                        "id": request["id"],
                        "ok": True,
                        "result": {},
                    }
                )
            )

    server, ws_url = await _start_server(handler)
    client = AsyncPyritoneClient(ws_url=ws_url, token="token")
    try:
        await client.connect()
        event = await client.wait_for(
            "task.progress",
            check=lambda payload: payload.get("data", {}).get("stage") == "target",
            timeout=1.0,
        )
        assert event["data"]["task_id"] == "b"
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_goto_returns_dispatch_result_immediately():
    recorded_commands: list[str] = []

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

            if method == "baritone.execute":
                command = request["params"]["command"]
                recorded_commands.append(command)
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {
                                "accepted": True,
                                "task": {"task_id": "goto-task"},
                            },
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
        dispatch = await client.goto(10, 64, 10)
        assert dispatch["command_text"] == "goto 10 64 10"
        assert dispatch["task_id"] == "goto-task"
        assert dispatch["accepted"] is True
        assert recorded_commands == ["goto 10 64 10"]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_goto_wait_waits_for_terminal_event():
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

            if method == "baritone.execute":
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {
                                "accepted": True,
                                "task": {"task_id": "goto-task"},
                            },
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "task.completed",
                            "data": {"task_id": "goto-task", "detail": "Reached goal"},
                            "ts": "2026-01-01T00:00:02Z",
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
        terminal_event = await client.goto_wait(10, 64, 10)
        assert terminal_event["event"] == "task.completed"
        assert terminal_event["data"]["task_id"] == "goto-task"
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_goto_wait_raises_when_task_id_is_missing():
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

            if method == "baritone.execute":
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {
                                "accepted": True,
                            },
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
        with pytest.raises(BridgeError) as error:
            await client.goto_wait(10, 64, 10)

        assert error.value.code == "BAD_RESPONSE"
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_wait_for_timeout():
    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            if request.get("method") == "auth.login":
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

    server, ws_url = await _start_server(handler)
    client = AsyncPyritoneClient(ws_url=ws_url, token="token")
    try:
        await client.connect()
        with pytest.raises(TimeoutError):
            await client.wait_for("task.completed", timeout=0.05)
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

