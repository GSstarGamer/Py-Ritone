from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYRITONE_SRC = REPO_ROOT / "python" / "src" / "pyritone"
COMMANDS_DIR = PYRITONE_SRC / "commands"
MOD_NET_SRC = REPO_ROOT / "mod" / "src" / "main" / "java" / "com" / "pyritone" / "bridge" / "net"
MOD_NET_TESTS = REPO_ROOT / "mod" / "src" / "test" / "java" / "com" / "pyritone" / "bridge" / "net"
GATEWAY_PATH = REPO_ROOT / "mod" / "src" / "main" / "java" / "com" / "pyritone" / "bridge" / "runtime" / "BaritoneGateway.java"

MAX_COMPAT_ALIAS_ASSIGNMENTS = 3
MAX_SYNC_COMMAND_SHIMS = 6


def _compat_alias_assignments() -> int:
    pattern = re.compile(r"^\s*(?:AsyncPyritoneClient|PyritoneClient)\s*=\s*Client\s*$", re.MULTILINE)
    total = 0
    for path in (PYRITONE_SRC / "client_async.py", PYRITONE_SRC / "client_sync.py"):
        total += len(pattern.findall(path.read_text(encoding="utf-8")))
    return total


def test_compat_alias_debt_does_not_increase():
    count = _compat_alias_assignments()
    assert count <= MAX_COMPAT_ALIAS_ASSIGNMENTS, f"Compatibility alias debt increased: {count} > {MAX_COMPAT_ALIAS_ASSIGNMENTS}"


def test_sync_command_shim_count_does_not_increase():
    count = len(list(COMMANDS_DIR.glob("sync_*.py")))
    assert count <= MAX_SYNC_COMMAND_SHIMS, f"Sync command shim debt increased: {count} > {MAX_SYNC_COMMAND_SHIMS}"


def test_legacy_socket_bridge_server_is_removed():
    assert not (MOD_NET_SRC / "SocketBridgeServer.java").exists()
    assert not (MOD_NET_TESTS / "SocketBridgeServerAuthTest.java").exists()


def test_no_socket_bridge_server_symbol_remains_in_java_sources():
    symbol = re.compile(r"\bSocketBridgeServer\b")
    references: list[str] = []
    for path in (REPO_ROOT / "mod" / "src").rglob("*.java"):
        text = path.read_text(encoding="utf-8")
        if symbol.search(text):
            references.append(path.relative_to(REPO_ROOT).as_posix())
    assert not references, f"Legacy SocketBridgeServer symbol found in: {references}"


def test_cancel_path_uses_force_cancel_without_stop_command_fallback():
    source = GATEWAY_PATH.read_text(encoding="utf-8")
    assert 'invokeNoArgs(pathingBehavior, "forceCancel")' in source
    assert 'new Object[]{"stop"}' not in source
