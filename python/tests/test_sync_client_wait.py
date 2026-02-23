from __future__ import annotations

import threading
from typing import Any

from pyritone.client_sync import PyritoneClient


class FakeSyncWaitClient(PyritoneClient):
    def __init__(self, events: list[dict[str, Any]]) -> None:  # type: ignore[super-init-not-called]
        self._events = iter(events)

    def next_event(self, timeout: float | None = None) -> dict[str, Any]:
        return next(self._events)


def test_sync_wait_for_task_on_update_runs_in_caller_thread():
    events = [
        {"event": "task.progress", "data": {"task_id": "target", "detail": "Working"}},
        {"event": "task.paused", "data": {"task_id": "target", "pause": {"reason_code": "BUILDER_PAUSED"}}},
        {"event": "task.completed", "data": {"task_id": "target"}},
    ]

    callback_thread_ids: list[int] = []
    callback_events: list[str] = []
    caller_thread_id = threading.get_ident()

    def on_update(event: dict[str, Any]) -> None:
        callback_events.append(str(event.get("event")))
        callback_thread_ids.append(threading.get_ident())

    client = FakeSyncWaitClient(events)
    terminal = client.wait_for_task("target", on_update=on_update)

    assert terminal["event"] == "task.completed"
    assert callback_events == ["task.progress", "task.paused"]
    assert callback_thread_ids == [caller_thread_id, caller_thread_id]
