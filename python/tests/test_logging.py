from __future__ import annotations

import asyncio
import logging
from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve

from pyritone.client_async import AsyncPyritoneClient
from pyritone.models import VisibleEntity
from pyritone.protocol import decode_message, encode_message


async def _start_server(handler):
    server = await serve(handler, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()[:2]
    return server, f"ws://{host}:{port}/ws"


def _pyritone_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [
        record.getMessage()
        for record in caplog.records
        if record.name == "pyritone" and "[Py-Ritone]" in record.getMessage()
    ]


@pytest.mark.asyncio
async def test_logs_goto_entity_format(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger="pyritone")
    client = AsyncPyritoneClient(ws_url="ws://127.0.0.1:1/ws", token="token")

    async def fake_goto_wait(x: int, y: int, z: int, *extra_args: Any) -> dict[str, Any]:
        assert (x, y, z) == (10, 64, -2)
        assert extra_args == ()
        return {"event": "task.completed", "data": {"task_id": "task-1"}}

    client.goto_wait = fake_goto_wait  # type: ignore[method-assign]

    await client.goto_entity(
        VisibleEntity(
            id="entity-1",
            type_id="minecraft:zombie",
            category="monster",
            x=10.4,
            y=63.6,
            z=-2.2,
            distance_sq=3.0,
        ),
        wait=True,
    )

    messages = _pyritone_messages(caplog)
    assert any("Sent goto_entity ( minecraft:zombie, entity-1 )" in message for message in messages)


@pytest.mark.asyncio
async def test_logs_connection_lifecycle(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger="pyritone")

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
        await client.close()
    finally:
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    assert any("State connecting" in message for message in messages)
    assert any("State connected" in message for message in messages)
    assert any("State disconnecting" in message for message in messages)
    assert any("State disconnected ( reason=client_closed )" in message for message in messages)


@pytest.mark.asyncio
async def test_logs_pause_state_at_info_by_default(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger="pyritone")

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
                            "event": "bridge.pause_state",
                            "data": {
                                "paused": True,
                                "operator_paused": True,
                                "game_paused": False,
                                "reason": "operator_pause",
                                "seq": 1,
                            },
                            "ts": "2026-01-01T00:00:00Z",
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
        await asyncio.sleep(0.05)
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    assert any("State paused" in message and "reason=operator_pause" in message for message in messages)


@pytest.mark.asyncio
async def test_logs_command_dispatch_for_goto(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger="pyritone")

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
                            "result": {"accepted": True, "task": {"task_id": "goto-task"}},
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
        await client.goto(10, 64, 10)
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    assert any("Sent goto ( 10, 64, 10 )" in message for message in messages)
    assert not any("Received goto" in message for message in messages)


@pytest.mark.asyncio
async def test_logs_goto_entity_without_duplicate_nested_goto_info(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger="pyritone")

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
                            "result": {"accepted": True, "task": {"task_id": "goto-task"}},
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
        await client.goto_entity(
            VisibleEntity(
                id="entity-1",
                type_id="minecraft:iron_golem",
                category="creature",
                x=7.0,
                y=-63.0,
                z=10.0,
                distance_sq=5.0,
            ),
            wait=False,
        )
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    assert any("Sent goto_entity ( minecraft:iron_golem, entity-1 )" in message for message in messages)
    assert not any("Sent goto ( 7, -63, 10 )" in message for message in messages)


@pytest.mark.asyncio
async def test_logs_typed_api_invoke(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.DEBUG, logger="pyritone")

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
                            "ok": True,
                            "result": {
                                "value": {
                                    "$pyritone_ref": "pathing-1",
                                    "java_type": "baritone.api.behavior.IPathingBehavior",
                                },
                                "return_type": "baritone.api.behavior.IPathingBehavior",
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
        await client.baritone.pathing_behavior()
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    assert any("Sent api_invoke ( getPathingBehavior, root:baritone, args=0 )" in message for message in messages)
    assert any("Received api_invoke ( return_type=baritone.api.behavior.IPathingBehavior, value_type=remote_ref )" in message for message in messages)


@pytest.mark.asyncio
async def test_logs_state_transitions_from_task_events(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.DEBUG, logger="pyritone")

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
                events = [
                    {
                        "type": "event",
                        "event": "task.started",
                        "data": {"task_id": "task-1", "detail": "dispatched"},
                        "ts": "2026-01-01T00:00:00Z",
                    },
                    {
                        "type": "event",
                        "event": "task.progress",
                        "data": {"task_id": "task-1", "detail": "Working"},
                        "ts": "2026-01-01T00:00:01Z",
                    },
                    {
                        "type": "event",
                        "event": "task.paused",
                        "data": {
                            "task_id": "task-1",
                            "pause": {
                                "reason_code": "BUILDER_PAUSED",
                                "source_process": "builder",
                            },
                        },
                        "ts": "2026-01-01T00:00:02Z",
                    },
                    {
                        "type": "event",
                        "event": "task.resumed",
                        "data": {"task_id": "task-1", "detail": "Resumed after pause"},
                        "ts": "2026-01-01T00:00:03Z",
                    },
                    {
                        "type": "event",
                        "event": "task.completed",
                        "data": {"task_id": "task-1", "detail": "Reached goal"},
                        "ts": "2026-01-01T00:00:04Z",
                    },
                ]
                for event in events:
                    await websocket.send(encode_message(event))
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
        await asyncio.sleep(0.05)
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    assert any("State working" in message and "task_id=task-1" in message for message in messages)
    assert any("State paused" in message and "reason=BUILDER_PAUSED" in message for message in messages)
    assert any("State completed" in message and "task_id=task-1" in message for message in messages)


@pytest.mark.asyncio
async def test_logs_path_calculation_inference(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.DEBUG, logger="pyritone")

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
                events = [
                    {
                        "type": "event",
                        "event": "baritone.path_event",
                        "data": {"task_id": "task-1", "path_event": "NEXT_CALC_STARTED"},
                        "ts": "2026-01-01T00:00:00Z",
                    },
                    {
                        "type": "event",
                        "event": "baritone.path_event",
                        "data": {"task_id": "task-1", "path_event": "NEXT_CALC_FINISHED_NOW_EXECUTING"},
                        "ts": "2026-01-01T00:00:01Z",
                    },
                ]
                for event in events:
                    await websocket.send(encode_message(event))
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
        await asyncio.sleep(0.05)
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    assert any("State calculating" in message and "path_event=NEXT_CALC_STARTED" in message for message in messages)
    assert any(
        "State best_path_ready" in message and "path_event=NEXT_CALC_FINISHED_NOW_EXECUTING" in message
        for message in messages
    )


@pytest.mark.asyncio
async def test_logs_dedupes_repeated_progress_and_path_events(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.DEBUG, logger="pyritone")

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
                events = [
                    {
                        "type": "event",
                        "event": "task.progress",
                        "data": {"task_id": "task-1", "detail": "Working"},
                        "ts": "2026-01-01T00:00:00Z",
                    },
                    {
                        "type": "event",
                        "event": "task.progress",
                        "data": {"task_id": "task-1", "detail": "Working"},
                        "ts": "2026-01-01T00:00:01Z",
                    },
                    {
                        "type": "event",
                        "event": "baritone.path_event",
                        "data": {"task_id": "task-1", "path_event": "NEXT_CALC_STARTED"},
                        "ts": "2026-01-01T00:00:02Z",
                    },
                    {
                        "type": "event",
                        "event": "baritone.path_event",
                        "data": {"task_id": "task-1", "path_event": "NEXT_CALC_STARTED"},
                        "ts": "2026-01-01T00:00:03Z",
                    },
                ]
                for event in events:
                    await websocket.send(encode_message(event))
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
        await asyncio.sleep(0.05)
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    working = [message for message in messages if "State working" in message and "detail=Working" in message]
    calculating = [message for message in messages if "State calculating" in message and "NEXT_CALC_STARTED" in message]
    assert len(working) == 1
    assert len(calculating) == 1


@pytest.mark.asyncio
async def test_logs_typed_wait_state_transitions(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.DEBUG, logger="pyritone")
    client = AsyncPyritoneClient(ws_url="ws://127.0.0.1:1/ws", token="token")

    class DummyBehavior:
        def __init__(self) -> None:
            self._index = 0
            self._states = [
                (False, True),
                (True, True),
                (False, False),
            ]

        async def is_pathing(self) -> bool:
            return self._states[self._index][0]

        async def in_progress(self):
            calculating = self._states[self._index][1]
            if self._index < len(self._states) - 1:
                self._index += 1
            return object() if calculating else None

        async def has_path(self) -> bool:
            return True

        async def goal(self):
            return None

    behavior = DummyBehavior()

    async def fake_pathing_behavior():
        return behavior

    client.baritone.pathing_behavior = fake_pathing_behavior  # type: ignore[method-assign]

    result = await client.baritone._wait_for_pathing_idle(
        handle_id="typed-1",
        action="IMineProcess.mineByName",
        timeout=1.0,
        poll_interval=0.0,
        startup_timeout=0.0,
    )
    assert result.started is True
    assert result.has_path is True

    messages = _pyritone_messages(caplog)
    assert any(
        "State moving" in message and "handle_id=typed-1" in message and "calculating=true" in message
        for message in messages
    )
    assert any("State best_path_ready" in message and "handle_id=typed-1" in message for message in messages)
    assert any(
        "State working" in message and "handle_id=typed-1" in message and "has_path=true" in message
        for message in messages
    )


@pytest.mark.asyncio
async def test_logs_redact_auth_token(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.DEBUG, logger="pyritone")
    secret = "super-secret-token"

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
    client = AsyncPyritoneClient(ws_url=ws_url, token=secret)
    try:
        await client.connect()
    finally:
        await client.close()
        server.close()
        await server.wait_closed()

    messages = _pyritone_messages(caplog)
    assert any("Sent auth_login ( *** )" in message for message in messages)
    assert all(secret not in message for message in messages)
