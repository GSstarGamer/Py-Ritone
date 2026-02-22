from __future__ import annotations

import argparse

from _common import (
    print_json,
    run_sync_demo,
    step,
    summarize_dispatch,
    summarize_event,
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
    terminal_event = client.wait_for_task(task_id)
    print(f"terminal event summary: {summarize_event(terminal_event)}")
    print_json("terminal event", terminal_event)
    step(terminal_summary(terminal_event))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sync_demo("03 - Goto + Completion", demo))
