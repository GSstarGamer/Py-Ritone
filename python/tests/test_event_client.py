from __future__ import annotations

import asyncio
import contextlib
from typing import Any

import pytest
from websockets.asyncio.server import ServerConnection, serve

from pyritone import Client
from pyritone.client_event import Client as EventClient
from pyritone.protocol import decode_message, encode_message


async def _start_server(handler):
    server = await serve(handler, "127.0.0.1", 0)
    host, port = server.sockets[0].getsockname()[:2]
    return server, f"ws://{host}:{port}/ws"


def _auth_ok(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "response",
        "id": request["id"],
        "ok": True,
        "result": {"protocol_version": 2, "server_version": "test"},
    }


def _status_ok(request: dict[str, Any], *, player: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "type": "response",
        "id": request["id"],
        "ok": True,
        "result": {
            "protocol_version": 2,
            "server_version": "test",
            "authenticated": True,
            "baritone_available": True,
            "in_world": True,
            "active_task": None,
            "watch_patterns": [],
            "player": player,
        },
    }


def _event(event_name: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "event",
        "event": event_name,
        "data": data,
        "ts": "2026-01-01T00:00:00Z",
    }


def test_event_decorator_requires_async_handler():
    client = EventClient(ws_url="ws://127.0.0.1:1/ws", token="token")

    def sync_handler():
        return None

    with pytest.raises(TypeError):
        client.event(sync_handler)  # type: ignore[arg-type]

    async def on_ready():
        return None

    assert client.event(on_ready) is on_ready


@pytest.mark.asyncio
async def test_on_ready_fires():
    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")
            if method == "auth.login":
                await websocket.send(encode_message(_auth_ok(request)))
                continue
            if method == "status.get":
                await websocket.send(encode_message(_status_ok(request)))
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
    client = Client(ws_url=ws_url, token="token")
    ready = asyncio.Event()

    @client.event
    async def on_ready():
        ready.set()
        await client.close()

    start_task = asyncio.create_task(client.start())
    try:
        await asyncio.wait_for(ready.wait(), timeout=1.0)
        await asyncio.wait_for(start_task, timeout=1.0)
    finally:
        if not start_task.done():
            start_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await start_task
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_on_message_aliases_on_chat_message():
    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")
            if method == "auth.login":
                await websocket.send(encode_message(_auth_ok(request)))
                continue
            if method == "status.get":
                await websocket.send(encode_message(_status_ok(request)))
                await websocket.send(
                    encode_message(
                        _event(
                            "minecraft.chat_message",
                            {
                                "message": "hello world",
                                "author": {"uuid": "u2", "name": "Other", "self": False},
                            },
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
    client = Client(ws_url=ws_url, token="token")
    seen_chat: list[str] = []
    seen_message: list[str] = []

    @client.event
    async def on_chat_message(ctx):
        seen_chat.append(ctx.message)

    @client.event
    async def on_message(ctx):
        seen_message.append(ctx.message)
        await client.close()

    start_task = asyncio.create_task(client.start())
    try:
        await asyncio.wait_for(start_task, timeout=1.0)
        assert seen_chat == ["hello world"]
        assert seen_message == ["hello world"]
    finally:
        if not start_task.done():
            start_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await start_task
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_author_self_comparison_uses_client_player_identity():
    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")
            if method == "auth.login":
                await websocket.send(encode_message(_auth_ok(request)))
                continue
            if method == "status.get":
                await websocket.send(
                    encode_message(_status_ok(request, player={"uuid": "u1", "name": "Self", "self": True}))
                )
                await websocket.send(
                    encode_message(
                        _event(
                            "minecraft.chat_message",
                            {
                                "message": "me",
                                "author": {"uuid": "u1", "name": "Self", "self": True},
                            },
                        )
                    )
                )
                await websocket.send(
                    encode_message(
                        _event(
                            "minecraft.chat_message",
                            {
                                "message": "other",
                                "author": {"uuid": "u2", "name": "Other", "self": False},
                            },
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
    client = Client(ws_url=ws_url, token="token")
    comparisons: list[bool] = []

    @client.event
    async def on_chat_message(ctx):
        comparisons.append(ctx.author == client.player)
        if len(comparisons) == 2:
            await client.close()

    start_task = asyncio.create_task(client.start())
    try:
        await asyncio.wait_for(start_task, timeout=1.0)
        assert comparisons == [True, False]
    finally:
        if not start_task.done():
            start_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await start_task
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_wait_for_message_and_timeout():
    sent_message = asyncio.Event()

    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")
            if method == "auth.login":
                await websocket.send(encode_message(_auth_ok(request)))
                continue
            if method == "status.get":
                await websocket.send(encode_message(_status_ok(request)))
                await websocket.send(
                    encode_message(
                        _event(
                            "minecraft.chat_message",
                            {
                                "message": "ping",
                                "author": {"uuid": "u2", "name": "Other", "self": False},
                            },
                        )
                    )
                )
                sent_message.set()
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
    client = Client(ws_url=ws_url, token="token")
    start_task = asyncio.create_task(client.start())
    try:
        await asyncio.wait_for(sent_message.wait(), timeout=1.0)
        context = await client.wait_for("message", timeout=1.0)
        assert context.message == "ping"

        with pytest.raises(TimeoutError):
            await client.wait_for("message", timeout=0.05)
    finally:
        await client.close()
        await asyncio.wait_for(start_task, timeout=1.0)
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_wait_for_raw_dotted_name_passthrough():
    sent_progress = asyncio.Event()

    async def handler(websocket: ServerConnection):
        async for message in websocket:
            request = decode_message(message)
            method = request.get("method")
            if method == "auth.login":
                await websocket.send(encode_message(_auth_ok(request)))
                continue
            if method == "status.get":
                await websocket.send(encode_message(_status_ok(request)))
                await websocket.send(
                    encode_message(
                        _event(
                            "task.progress",
                            {
                                "task_id": "task-1",
                                "detail": "working",
                            },
                        )
                    )
                )
                sent_progress.set()
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
    client = Client(ws_url=ws_url, token="token")
    start_task = asyncio.create_task(client.start())
    try:
        await asyncio.wait_for(sent_progress.wait(), timeout=1.0)
        payload = await client.wait_for(
            "task.progress",
            check=lambda event: event.get("data", {}).get("task_id") == "task-1",
            timeout=1.0,
        )
        assert payload["event"] == "task.progress"
        assert payload["data"]["task_id"] == "task-1"
    finally:
        await client.close()
        await asyncio.wait_for(start_task, timeout=1.0)
        server.close()
        await server.wait_closed()
