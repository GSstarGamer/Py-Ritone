from __future__ import annotations

import importlib.util
from pathlib import Path

from pyritone import BridgeError, DiscoveryError


def _load_common_module():
    common_path = Path(__file__).resolve().parents[1] / "demos" / "_common.py"
    spec = importlib.util.spec_from_file_location("pyritone_demo_common", common_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_scalar_and_parse_scalars():
    common = _load_common_module()

    assert common.parse_scalar("true") is True
    assert common.parse_scalar("FALSE") is False
    assert common.parse_scalar("none") is None
    assert common.parse_scalar("42") == 42
    assert common.parse_scalar("3.25") == 3.25
    assert common.parse_scalar("hello") == "hello"

    assert common.parse_scalars(["1", "true", "name"]) == [1, True, "name"]


def test_extract_task_id_prefers_top_level_then_nested_task():
    common = _load_common_module()

    assert common.extract_task_id({"task_id": "top"}) == "top"
    assert common.extract_task_id({"task": {"task_id": "nested"}}) == "nested"
    assert common.extract_task_id({"task": {"task_id": ""}}) is None
    assert common.extract_task_id({}) is None


def test_terminal_summary_messages():
    common = _load_common_module()

    completed = {"event": "task.completed", "data": {"task_id": "a"}}
    canceled = {"event": "task.canceled", "data": {"task_id": "a", "reason": "User request"}}
    failed = {"event": "task.failed", "data": {"task_id": "a", "message": "No path"}}

    assert common.terminal_summary(completed) == "Task completed."
    assert common.terminal_summary(canceled) == "Task ended (canceled): User request"
    assert common.terminal_summary(failed) == "Task failed: No path"


def test_summarize_pause_update_prefers_reason_and_source():
    common = _load_common_module()

    paused = {
        "event": "task.paused",
        "data": {
            "task_id": "a",
            "pause": {
                "reason_code": "BUILDER_PAUSED",
                "source_process": "builder",
            },
        },
    }
    resumed = {
        "event": "task.resumed",
        "data": {"task_id": "a", "pause": {"reason_code": "BUILDER_PAUSED"}},
    }

    assert common.summarize_pause_update(paused) == "task.paused: reason=BUILDER_PAUSED, source=builder"
    assert common.summarize_pause_update(resumed).startswith("task.resumed: reason=BUILDER_PAUSED")


def test_friendly_error_message_mapping():
    common = _load_common_module()

    code, message = common.friendly_error_message(DiscoveryError("missing token"))
    assert code == 2
    assert "Discovery failed" in message

    code, message = common.friendly_error_message(BridgeError("NOT_IN_WORLD", "Join a world"))
    assert code == 3
    assert "not in a world" in message.lower()

    code, message = common.friendly_error_message(BridgeError("BARITONE_UNAVAILABLE", "Missing"))
    assert code == 3
    assert "baritone" in message.lower()

    code, message = common.friendly_error_message(BridgeError("EXECUTION_FAILED", "Boom"))
    assert code == 3
    assert "EXECUTION_FAILED" in message

    code, message = common.friendly_error_message(ConnectionRefusedError("no listener"))
    assert code == 4
    assert "bridge socket" in message.lower() or "local bridge" in message.lower()

    code, message = common.friendly_error_message(OSError("socket down"))
    assert code == 4
    assert "socket" in message.lower()
