from __future__ import annotations

import argparse
import asyncio
import contextlib
from typing import Any

from _common import (
    run_async_demo,
    step,
    summarize_dispatch,
    summarize_event,
    summarize_pause_update,
    task_reason,
)


parser = argparse.ArgumentParser(description="Async-only workflow demo with heartbeat + pause-aware waiting")
parser.add_argument("x", type=int, nargs="?", default=0)
parser.add_argument("y", type=int, nargs="?", default=1000)
parser.add_argument("z", type=int, nargs="?", default=0)
parser.add_argument(
    "--cancel-after",
    type=float,
    default=6.0,
    help="Auto-cancel after this many seconds if no terminal event arrives",
)
parser.add_argument(
    "--heartbeat-interval",
    type=float,
    default=1.5,
    help="Seconds between async heartbeat ping calls",
)
args = parser.parse_args()


async def _heartbeat_worker(client, stop_event: asyncio.Event) -> None:
    heartbeat_count = 0

    while not stop_event.is_set():
        await asyncio.sleep(args.heartbeat_interval)
        if stop_event.is_set():
            break

        heartbeat_count += 1
        pong = await client.ping()
        print(f"[heartbeat {heartbeat_count:02}] pong ts={pong.get('ts')}")


async def _stop_task(task: asyncio.Task[None]) -> None:
    if task.done():
        with contextlib.suppress(asyncio.CancelledError):
            await task
        return

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


def _print_task_update(event: dict[str, Any]) -> None:
    event_name = str(event.get("event"))
    if event_name == "baritone.path_event":
        return

    if event_name in {"task.paused", "task.resumed"}:
        print(f"[update] {summarize_pause_update(event)}")
        return

    reason = task_reason(event)
    if reason:
        print(f"[update] {event_name}: {reason}")
    else:
        print(f"[update] {event_name}")


async def demo(client):
    step("Async-only demo: heartbeat pings continue while wait_for_task tracks updates.")
    status = await client.status_get()
    print(
        "[status] "
        + f"in_world={status.get('in_world')}, "
        + f"baritone_available={status.get('baritone_available')}, "
        + f"authenticated={status.get('authenticated')}"
    )

    stop_event = asyncio.Event()
    heartbeat_task = asyncio.create_task(
        _heartbeat_worker(client, stop_event),
        name="pyritone-demo-heartbeat",
    )

    try:
        step(f"Dispatching goto({args.x}, {args.y}, {args.z})")
        dispatch = await client.goto(args.x, args.y, args.z)
        print(f"[dispatch] {summarize_dispatch(dispatch)}")

        task_id = dispatch.get("task_id")
        if not task_id:
            step("No task_id returned. Ending async workflow cleanly.")
            return 0

        timeout_seconds = max(args.cancel_after, 0.1)
        wait_task = asyncio.create_task(
            client.wait_for_task(task_id, on_update=_print_task_update),
            name="pyritone-demo-wait",
        )

        try:
            terminal_event = await asyncio.wait_for(asyncio.shield(wait_task), timeout=timeout_seconds)
            step("Task reached terminal state before auto-cancel timeout.")
        except asyncio.TimeoutError:
            step(f"No terminal event after {args.cancel_after:.1f}s. Sending async cancel(task_id).")
            cancel_result = await client.cancel(task_id=task_id)
            print(f"[cancel] canceled={cancel_result.get('canceled')} task_id={task_id}")

            try:
                terminal_event = await asyncio.wait_for(asyncio.shield(wait_task), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                wait_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await wait_task
                step("Still no terminal event after cancel timeout. Stopping demo.")
                return 0

        print(f"[terminal] {summarize_event(terminal_event)}")
        terminal_reason = task_reason(terminal_event)
        if terminal_reason:
            step(f"Terminal reason: {terminal_reason}")
        return 0
    finally:
        stop_event.set()
        await _stop_task(heartbeat_task)


if __name__ == "__main__":
    raise SystemExit(run_async_demo("08 - Async Workflow", demo))
