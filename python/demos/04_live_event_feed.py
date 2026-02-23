from __future__ import annotations

import argparse

from _common import run_async_demo, step, task_reason


parser = argparse.ArgumentParser(description="Dispatch demo goto and print concise live bridge events")
parser.add_argument("--x", type=int, default=0, help="Demo goto X")
parser.add_argument("--y", type=int, default=1000, help="Demo goto Y (high value for likely failure)")
parser.add_argument("--z", type=int, default=0, help="Demo goto Z")
parser.add_argument("--max-events", type=int, default=30, help="0 means unlimited")
parser.add_argument("--timeout", type=float, default=5.0)
parser.add_argument(
    "--include-idle-path-events",
    action="store_true",
    help="Include baritone.path_event events that have no task_id (can be noisy)",
)
args = parser.parse_args()


TERMINAL_TASK_EVENTS = {"task.completed", "task.failed", "task.canceled"}


def _is_idle_path_event(event: dict) -> bool:
    if event.get("event") != "baritone.path_event":
        return False

    data = event.get("data")
    if not isinstance(data, dict):
        return False

    task_id = data.get("task_id")
    return task_id in (None, "")


def _event_task_id(event: dict) -> str | None:
    data = event.get("data")
    if not isinstance(data, dict):
        return None

    value = data.get("task_id")
    if isinstance(value, str) and value:
        return value
    return None


def _compact_ts(raw_ts: object) -> str:
    if not isinstance(raw_ts, str) or not raw_ts:
        return "--:--:--"

    tail = raw_ts.split("T", 1)[-1]
    tail = tail.rstrip("Z")
    return tail[:12]


def _event_line(index: int, event: dict) -> str:
    event_name = str(event.get("event", "?"))
    event_task = _event_task_id(event) or "-"
    data = event.get("data")
    data = data if isinstance(data, dict) else {}

    stage = data.get("stage", "-")
    path_event = data.get("path_event", "-")
    reason = task_reason(event) or "-"
    ts = _compact_ts(event.get("ts"))

    return (
        f"[event {index:02}] {ts} | {event_name:<19} | task={event_task} | "
        f"stage={stage} | path={path_event} | reason={reason}"
    )


async def demo(client):
    step(
        "Dispatching demo goto to an intentionally high Y so recording clearly shows live path/task behavior."
    )
    dispatch = await client.goto(args.x, args.y, args.z)
    task_id = dispatch.get("task_id")
    accepted = dispatch.get("accepted")
    print(
        f"[dispatch] goto {args.x} {args.y} {args.z} | accepted={accepted!r} | task_id={task_id or '-'}"
    )
    if not task_id:
        step("No task_id returned. Streaming general events only.")

    step("Listening for events. Press Ctrl+C to stop.")

    received = 0
    displayed = 0
    skipped_idle_path = 0
    skipped_other_task = 0
    terminal_seen = None

    while args.max_events <= 0 or displayed < args.max_events:
        try:
            event = await client.next_event(timeout=args.timeout)
        except TimeoutError:
            step(f"No event in {args.timeout:.1f}s window; still listening...")
            continue

        received += 1

        if not args.include_idle_path_events and _is_idle_path_event(event):
            skipped_idle_path += 1
            continue

        event_task = _event_task_id(event)
        if task_id and event_task is not None and event_task != task_id:
            skipped_other_task += 1
            continue

        displayed += 1
        print(_event_line(displayed, event))

        event_name = event.get("event")
        if (
            task_id
            and isinstance(event_name, str)
            and event_name in TERMINAL_TASK_EVENTS
            and event_task == task_id
        ):
            terminal_seen = event
            break

    if skipped_idle_path:
        step(
            "Skipped "
            + str(skipped_idle_path)
            + " idle baritone.path_event events. Use --include-idle-path-events to show them."
        )

    if skipped_other_task:
        step(f"Skipped {skipped_other_task} events from other task IDs.")

    if terminal_seen is not None:
        terminal_name = terminal_seen.get("event")
        reason = task_reason(terminal_seen) or "no reason provided"
        step(f"Terminal event reached: {terminal_name} ({reason})")
    else:
        step("No terminal event reached within current event window.")

    step(f"Summary: received={received}, displayed={displayed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_async_demo("04 - Live Event Feed", demo))
