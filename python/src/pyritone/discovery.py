from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from .models import BridgeInfo, DiscoveryError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 27841
DEFAULT_BRIDGE_INFO_RELATIVE = Path("config") / "pyritone_bridge" / "bridge-info.json"


def default_minecraft_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / ".minecraft"

    xdg = os.getenv("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "minecraft"

    home = Path.home()
    if os.name == "nt":
        return home / "AppData" / "Roaming" / ".minecraft"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "minecraft"
    return home / ".minecraft"


def default_bridge_info_path() -> Path:
    return default_minecraft_dir() / DEFAULT_BRIDGE_INFO_RELATIVE


def load_bridge_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise DiscoveryError(f"Bridge info file does not contain an object: {path}")
    return parsed


def resolve_bridge_info(
    *,
    host: str | None = None,
    port: int | None = None,
    token: str | None = None,
    bridge_info_path: str | Path | None = None,
) -> BridgeInfo:
    env_bridge_info_path = os.getenv("PYRITONE_BRIDGE_INFO")
    env_host = os.getenv("PYRITONE_HOST")
    env_port = os.getenv("PYRITONE_PORT")
    env_token = os.getenv("PYRITONE_TOKEN")

    selected_info_path = (
        Path(bridge_info_path)
        if bridge_info_path is not None
        else Path(env_bridge_info_path)
        if env_bridge_info_path
        else default_bridge_info_path()
    )

    file_values = load_bridge_info(selected_info_path)

    resolved_host = host or env_host or str(file_values.get("host") or DEFAULT_HOST)

    if port is not None:
        resolved_port = int(port)
    elif env_port:
        resolved_port = int(env_port)
    elif "port" in file_values:
        resolved_port = int(file_values["port"])
    else:
        resolved_port = DEFAULT_PORT

    resolved_token = token or env_token or file_values.get("token")
    if not resolved_token:
        raise DiscoveryError(
            "No bridge token found. Start Minecraft with the pyritone_bridge mod first or set PYRITONE_TOKEN."
        )

    protocol_version = file_values.get("protocol_version")
    server_version = file_values.get("server_version")

    return BridgeInfo(
        host=resolved_host,
        port=resolved_port,
        token=str(resolved_token),
        protocol_version=int(protocol_version) if protocol_version is not None else None,
        server_version=str(server_version) if server_version is not None else None,
    )
