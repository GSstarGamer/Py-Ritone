import pytest

from pyritone.protocol import decode_line, encode_line, new_request


def test_new_request_shape():
    request = new_request("ping", {})

    assert request["type"] == "request"
    assert request["method"] == "ping"
    assert request["params"] == {}
    assert isinstance(request["id"], str)


def test_new_request_honors_explicit_request_id_and_default_params():
    request = new_request("ping", request_id="req-123")

    assert request["id"] == "req-123"
    assert request["params"] == {}


def test_encode_line_adds_newline_framing():
    payload = {"type": "response", "id": "abc", "ok": True, "result": {"pong": True}}
    encoded = encode_line(payload)

    assert isinstance(encoded, bytes)
    assert encoded.endswith(b"\n")


def test_encode_decode_roundtrip():
    payload = {"type": "response", "id": "abc", "ok": True, "result": {"pong": True}}
    encoded = encode_line(payload)
    decoded = decode_line(encoded)

    assert decoded == payload


def test_decode_line_accepts_text_input():
    payload = decode_line('{"type":"event","event":"task.completed","data":{"task_id":"abc"}}')
    assert payload["type"] == "event"
    assert payload["data"]["task_id"] == "abc"


def test_decode_line_rejects_non_object_payloads():
    with pytest.raises(ValueError, match="JSON object"):
        decode_line("[]")
