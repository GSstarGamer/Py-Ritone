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


def _repo_dev_bridge_info_candidates() -> tuple[Path, ...]:
    candidates: list[Path] = []

    # Repository-relative path when running from checkout.
    repo_root = Path(__file__).resolve().parents[3]
    candidates.append(repo_root / "mod" / "run" / DEFAULT_BRIDGE_INFO_RELATIVE)

    # Common working directories during local development.
    cwd = Path.cwd()
    candidates.append(cwd / "mod" / "run" / DEFAULT_BRIDGE_INFO_RELATIVE)
    candidates.append(cwd.parent / "mod" / "run" / DEFAULT_BRIDGE_INFO_RELATIVE)

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(candidate)

    return tuple(unique)


def auto_bridge_info_paths() -> tuple[Path, ...]:
    return (default_bridge_info_path(), *_repo_dev_bridge_info_candidates())


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

    if bridge_info_path is not None:
        selected_paths = [Path(bridge_info_path)]
    elif env_bridge_info_path:
        selected_paths = [Path(env_bridge_info_path)]
    else:
        selected_paths = list(auto_bridge_info_paths())

    checked_paths: list[Path] = []
    file_values: dict[str, Any] = {}

    for candidate_path in selected_paths:
        checked_paths.append(candidate_path)
        values = load_bridge_info(candidate_path)
        if not values:
            continue

        file_values = values
        if values.get("token"):
            break

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
        checked = ", ".join(str(path) for path in checked_paths)
        raise DiscoveryError(
            "No bridge token found. Start Minecraft with the pyritone_bridge mod first or set PYRITONE_TOKEN. "
            f"Checked paths: {checked}"
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
