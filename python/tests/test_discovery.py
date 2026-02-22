from pyritone.discovery import resolve_bridge_info


def test_explicit_values_override_env_and_file(tmp_path, monkeypatch):
    info_file = tmp_path / "bridge-info.json"
    info_file.write_text('{"host":"1.2.3.4","port":1234,"token":"file-token"}', encoding="utf-8")

    monkeypatch.setenv("PYRITONE_HOST", "9.9.9.9")
    monkeypatch.setenv("PYRITONE_PORT", "9999")
    monkeypatch.setenv("PYRITONE_TOKEN", "env-token")

    resolved = resolve_bridge_info(
        host="127.0.0.1",
        port=27841,
        token="explicit-token",
        bridge_info_path=info_file,
    )

    assert resolved.host == "127.0.0.1"
    assert resolved.port == 27841
    assert resolved.token == "explicit-token"


def test_env_values_override_file(tmp_path, monkeypatch):
    info_file = tmp_path / "bridge-info.json"
    info_file.write_text('{"host":"1.2.3.4","port":1234,"token":"file-token"}', encoding="utf-8")

    monkeypatch.setenv("PYRITONE_HOST", "127.0.0.1")
    monkeypatch.setenv("PYRITONE_PORT", "27841")
    monkeypatch.setenv("PYRITONE_TOKEN", "env-token")

    resolved = resolve_bridge_info(bridge_info_path=info_file)

    assert resolved.host == "127.0.0.1"
    assert resolved.port == 27841
    assert resolved.token == "env-token"
