from __future__ import annotations

import json
import uuid
from typing import Any


def new_request(method: str, params: dict[str, Any] | None = None, request_id: str | None = None) -> dict[str, Any]:
    return {
        "type": "request",
        "id": request_id or str(uuid.uuid4()),
        "method": method,
        "params": params or {},
    }


def encode_message(payload: dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"))


def decode_message(message: bytes | str) -> dict[str, Any]:
    if isinstance(message, bytes):
        text = message.decode("utf-8")
    else:
        text = message
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Protocol payload must be a JSON object")
    return parsed


def encode_line(payload: dict[str, Any]) -> bytes:
    return (encode_message(payload) + "\n").encode("utf-8")


def decode_line(line: bytes | str) -> dict[str, Any]:
    return decode_message(line)
