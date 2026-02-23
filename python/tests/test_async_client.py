from __future__ import annotations

import asyncio
from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve

from pyritone.client_async import AsyncPyritoneClient
from pyritone.models import BridgeError, RemoteRef, TypedCallError
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
async def test_status_subscribe_and_unsubscribe_updates_state_cache():
    observed_methods: list[str] = []

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

            if method == "status.subscribe":
                observed_methods.append(method)
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {
                                "subscribed": True,
                                "heartbeat_interval_ms": 5000,
                                "status": {
                                    "authenticated": True,
                                    "baritone_available": True,
                                    "in_world": False,
                                    "active_task": None,
                                },
                            },
                        }
                    )
                )
                await websocket.send(
                    encode_message(
                        {
                            "type": "event",
                            "event": "status.update",
                            "data": {
                                "reason": "heartbeat",
                                "status": {
                                    "authenticated": True,
                                    "baritone_available": True,
                                    "in_world": True,
                                    "active_task": {
                                        "task_id": "task-1",
                                        "state": "RUNNING",
                                        "detail": "working",
                                    },
                                },
                            },
                            "ts": "2026-01-01T00:00:03Z",
                        }
                    )
                )
                continue

            if method == "status.unsubscribe":
                observed_methods.append(method)
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {"subscribed": False, "was_subscribed": True},
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

        subscribed = await client.status_subscribe()
        assert subscribed["subscribed"] is True
        assert subscribed["status"]["in_world"] is False

        heartbeat_event = await client.wait_for("status.update", timeout=1.0)
        assert heartbeat_event["data"]["reason"] == "heartbeat"
        assert client.state.snapshot["in_world"] is True
        assert client.task.id == "task-1"
        assert client.task.state == "RUNNING"

        unsubscribed = await client.status_unsubscribe()
        assert unsubscribed["subscribed"] is False
        assert observed_methods == ["status.subscribe", "status.unsubscribe"]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_task_wait_uses_cached_state_task_id_and_clears_on_terminal():
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
                            "data": {
                                "task_id": "task-9",
                                "state": "RUNNING",
                                "detail": "going",
                            },
                            "ts": "2026-01-01T00:00:00Z",
                        }
                    )
                )

                async def send_terminal() -> None:
                    await asyncio.sleep(0.05)
                    await websocket.send(
                        encode_message(
                            {
                                "type": "event",
                                "event": "task.completed",
                                "data": {
                                    "task_id": "task-9",
                                    "state": "COMPLETED",
                                    "detail": "done",
                                },
                                "ts": "2026-01-01T00:00:01Z",
                            }
                        )
                    )

                asyncio.create_task(send_terminal())
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
        progress = await client.wait_for("task.progress", timeout=1.0)
        assert progress["data"]["task_id"] == "task-9"
        assert client.task.id == "task-9"

        terminal = await client.task.wait(timeout=1.0)
        assert terminal["event"] == "task.completed"
        assert client.task.id is None
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_task_wait_raises_when_no_active_task_is_available():
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

            if method == "status.get":
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {
                                "authenticated": True,
                                "baritone_available": True,
                                "in_world": True,
                                "active_task": None,
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
            await client.task.wait(timeout=0.2)
        assert error.value.code == "NO_ACTIVE_TASK"
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_api_construct_and_invoke_handle_remote_refs():
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
                assert request["params"]["type"] == "tests.SampleBox"
                assert request["params"]["args"] == [5]
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {
                                "value": {"$pyritone_ref": "ref-1", "java_type": "tests.SampleBox"},
                                "java_type": "tests.SampleBox",
                            },
                        }
                    )
                )
                continue

            if method == "api.invoke":
                target = request["params"]["target"]
                if target == {"kind": "ref", "id": "ref-1"} and request["params"]["method"] == "add":
                    await websocket.send(
                        encode_message(
                            {
                                "type": "response",
                                "id": request["id"],
                                "ok": True,
                                "result": {"value": 8, "return_type": "int"},
                            }
                        )
                    )
                    continue

                if target == {"kind": "ref", "id": "ref-1"} and request["params"]["method"] == "child":
                    await websocket.send(
                        encode_message(
                            {
                                "type": "response",
                                "id": request["id"],
                                "ok": True,
                                "result": {
                                    "value": {"$pyritone_ref": "ref-2", "java_type": "tests.SampleBox"},
                                    "return_type": "tests.SampleBox",
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
        box = await client.api_construct("tests.SampleBox", 5)
        assert box == RemoteRef(ref_id="ref-1", java_type="tests.SampleBox")

        add_value = await client.api_invoke(box, "add", 3)
        assert add_value == 8

        child = await client.api_invoke(box, "child", 2)
        assert child == RemoteRef(ref_id="ref-2", java_type="tests.SampleBox")
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_api_invoke_uses_root_target_and_parameter_types():
    observed_payloads: list[dict[str, Any]] = []

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
                observed_payloads.append(request["params"])
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": True,
                            "result": {"value": "ok", "return_type": "java.lang.String"},
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
            "setFlag",
            "x",
            parameter_types=["java.lang.String"],
        )
        assert result == "ok"
        assert observed_payloads == [
            {
                "target": {"kind": "root", "name": "baritone"},
                "method": "setFlag",
                "args": ["x"],
                "parameter_types": ["java.lang.String"],
            }
        ]
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_api_error_raises_typed_call_error_with_details():
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
                await websocket.send(
                    encode_message(
                        {
                            "type": "response",
                            "id": request["id"],
                            "ok": False,
                            "error": {
                                "code": "API_ARGUMENT_COERCION_FAILED",
                                "message": "Bad arg",
                                "data": {"arg_index": 0, "expected_type": "int"},
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
        with pytest.raises(TypedCallError) as error:
            await client.api_invoke("baritone", "plus", "oops")

        assert error.value.code == "API_ARGUMENT_COERCION_FAILED"
        assert error.value.details["arg_index"] == 0
        assert error.value.details["expected_type"] == "int"
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
