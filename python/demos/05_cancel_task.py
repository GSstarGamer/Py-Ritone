from __future__ import annotations

import argparse
import asyncio

from _common import (
    print_json,
    run_async_demo,
    step,
    summarize_dispatch,
    summarize_event,
    terminal_summary,
)


parser = argparse.ArgumentParser(description="Start a task, cancel it, and inspect terminal state")
parser.add_argument("--delay", type=float, default=1.5, help="Seconds to wait before cancel")
args = parser.parse_args()


async def demo(client):
    step("Starting a long-running task with high-level wrapper: explore()")
    dispatch = await client.explore()
    print(f"explore() dispatch summary: {summarize_dispatch(dispatch)}")
    print_json("explore() dispatch", dispatch)

    task_id = dispatch.get("task_id")
    if not task_id:
        step("No task_id returned, cannot target a specific cancel. Sending global cancel instead.")
        print_json("cancel()", await client.cancel())
        return 0

    step(f"Waiting {args.delay:.1f}s before canceling task_id={task_id}")
    await asyncio.sleep(max(args.delay, 0.0))

    cancel_result = await client.cancel(task_id=task_id)
    print_json("cancel(task_id)", cancel_result)

    step("Waiting for terminal task event after cancel")
    terminal_event = await client.wait_for_task(task_id)
    print(f"terminal event summary: {summarize_event(terminal_event)}")
    print_json("terminal event", terminal_event)
    step(terminal_summary(terminal_event))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_async_demo("05 - Cancel Task", demo))
