from pathlib import Path

import pyritone.discovery as discovery


def test_explicit_values_override_env_and_file(tmp_path, monkeypatch):
    info_file = tmp_path / "bridge-info.json"
    info_file.write_text('{"host":"1.2.3.4","port":1234,"token":"file-token"}', encoding="utf-8")

    monkeypatch.setenv("PYRITONE_HOST", "9.9.9.9")
    monkeypatch.setenv("PYRITONE_PORT", "9999")
    monkeypatch.setenv("PYRITONE_TOKEN", "env-token")

    resolved = discovery.resolve_bridge_info(
        host="127.0.0.1",
        port=27841,
        token="explicit-token",
        bridge_info_path=info_file,
    )

    assert resolved.host == "127.0.0.1"
    assert resolved.port == 27841
    assert resolved.token == "explicit-token"
    assert resolved.ws_url == "ws://127.0.0.1:27841/ws"
    assert resolved.ws_path == "/ws"
    assert resolved.transport == "websocket"


def test_env_values_override_file(tmp_path, monkeypatch):
    info_file = tmp_path / "bridge-info.json"
    info_file.write_text('{"host":"1.2.3.4","port":1234,"token":"file-token"}', encoding="utf-8")

    monkeypatch.setenv("PYRITONE_HOST", "127.0.0.1")
    monkeypatch.setenv("PYRITONE_PORT", "27841")
    monkeypatch.setenv("PYRITONE_TOKEN", "env-token")

    resolved = discovery.resolve_bridge_info(bridge_info_path=info_file)

    assert resolved.host == "127.0.0.1"
    assert resolved.port == 27841
    assert resolved.token == "env-token"
    assert resolved.ws_url == "ws://127.0.0.1:27841/ws"


def test_auto_discovery_falls_back_to_dev_bridge_info(tmp_path, monkeypatch):
    default_info = tmp_path / "default" / "bridge-info.json"
    dev_info = tmp_path / "repo" / "mod" / "run" / "config" / "pyritone_bridge" / "bridge-info.json"
    dev_info.parent.mkdir(parents=True)
    dev_info.write_text('{"host":"127.0.0.1","port":27841,"token":"dev-token"}', encoding="utf-8")

    monkeypatch.setattr(discovery, "default_bridge_info_path", lambda: default_info)
    monkeypatch.setattr(discovery, "_repo_dev_bridge_info_candidates", lambda: (dev_info,))

    resolved = discovery.resolve_bridge_info()

    assert resolved.host == "127.0.0.1"
    assert resolved.port == 27841
    assert resolved.token == "dev-token"
    assert resolved.ws_url == "ws://127.0.0.1:27841/ws"


def test_ws_url_env_override(monkeypatch):
    monkeypatch.setenv("PYRITONE_TOKEN", "env-token")
    monkeypatch.setenv("PYRITONE_WS_URL", "ws://10.0.0.5:40000/custom")

    resolved = discovery.resolve_bridge_info()

    assert resolved.host == "10.0.0.5"
    assert resolved.port == 40000
    assert resolved.ws_url == "ws://10.0.0.5:40000/custom"
    assert resolved.ws_path == "/custom"
