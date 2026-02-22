from __future__ import annotations

import argparse

from _common import print_json, run_async_demo, step, summarize_dispatch, summarize_event, terminal_summary


parser = argparse.ArgumentParser(description="Async client workflow demo")
parser.add_argument("x", type=int, nargs="?", default=100)
parser.add_argument("y", type=int, nargs="?", default=70)
parser.add_argument("z", type=int, nargs="?", default=100)
args = parser.parse_args()


async def demo(client):
    step("Async ping/status")
    print_json("await ping()", await client.ping())
    print_json("await status_get()", await client.status_get())

    step("Async settings handle API")
    print_json("await settings.allowPlace.set(True)", await client.settings.allowPlace.set(True))
    print_json("await settings.allowPlace.get()", await client.settings.allowPlace.get())

    step(f"Dispatching await goto({args.x}, {args.y}, {args.z})")
    dispatch = await client.goto(args.x, args.y, args.z)
    print(f"goto() dispatch summary: {summarize_dispatch(dispatch)}")
    print_json("goto dispatch", dispatch)

    task_id = dispatch.get("task_id")
    if not task_id:
        step("No task_id returned, so completion wait is skipped.")
        return 0

    terminal_event = await client.wait_for_task(task_id)
    print(f"terminal event summary: {summarize_event(terminal_event)}")
    print_json("terminal event", terminal_event)
    step(terminal_summary(terminal_event))

    try:
        event = await client.next_event(timeout=1.0)
        print(f"extra event summary: {summarize_event(event)}")
    except TimeoutError:
        step("No extra event arrived within 1s. Async flow complete.")

    return 0


if __name__ == "__main__":
    raise SystemExit(run_async_demo("08 - Async Workflow", demo))
