from __future__ import annotations

import argparse

from _common import (
    print_json,
    run_sync_demo,
    step,
    summarize_pause_update,
    summarize_dispatch,
    summarize_event,
    task_reason,
    terminal_summary,
)


parser = argparse.ArgumentParser(description="Dispatch goto and wait for terminal task event")
parser.add_argument("x", type=int, nargs="?", default=100)
parser.add_argument("y", type=int, nargs="?", default=70)
parser.add_argument("z", type=int, nargs="?", default=100)
args = parser.parse_args()


def demo(client):
    step(f"Dispatching goto({args.x}, {args.y}, {args.z})")
    dispatch = client.goto(args.x, args.y, args.z)
    print(f"goto dispatch summary: {summarize_dispatch(dispatch)}")
    print_json("goto dispatch", dispatch)

    task_id = dispatch.get("task_id")
    if not task_id:
        step("No task_id was returned, so there is nothing to wait for.")
        return 0

    step(f"Waiting for terminal event for task_id={task_id}")
    last_line: str | None = None

    def on_update(event):
        nonlocal last_line
        event_name = str(event.get("event"))
        if event_name == "baritone.path_event":
            return

        if event_name in {"task.paused", "task.resumed"}:
            pause_line = summarize_pause_update(event)
            if pause_line != last_line:
                print(f"task update: {pause_line}")
                last_line = pause_line
            return

        reason = task_reason(event)
        if reason:
            line = f"{event_name} ({reason})"
        else:
            line = event_name

        if line != last_line:
            print(f"task update: {line}")
            last_line = line

    terminal_event = client.wait_for_task(task_id, on_update=on_update)
    print(f"terminal event summary: {summarize_event(terminal_event)}")
    print_json("terminal event", terminal_event)
    step(terminal_summary(terminal_event))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sync_demo("03 - Goto + Completion", demo))
