from pyritone.protocol import decode_line, encode_line, new_request


def test_new_request_shape():
    request = new_request("ping", {})

    assert request["type"] == "request"
    assert request["method"] == "ping"
    assert request["params"] == {}
    assert isinstance(request["id"], str)


def test_encode_decode_roundtrip():
    payload = {"type": "response", "id": "abc", "ok": True, "result": {"pong": True}}
    encoded = encode_line(payload)
    decoded = decode_line(encoded)

    assert decoded == payload
