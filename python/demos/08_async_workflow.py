from __future__ import annotations

import argparse
import asyncio
import contextlib
from typing import Any

from _common import run_async_demo, step, summarize_dispatch, summarize_event, task_reason


parser = argparse.ArgumentParser(description="Async-only workflow demo with concurrent stream + heartbeat")
parser.add_argument("x", type=int, nargs="?", default=0)
parser.add_argument("y", type=int, nargs="?", default=1000)
parser.add_argument("z", type=int, nargs="?", default=0)
parser.add_argument(
    "--cancel-after",
    type=float,
    default=6.0,
    help="Auto-cancel the task after this many seconds if no terminal event",
)
parser.add_argument(
    "--heartbeat-interval",
    type=float,
    default=1.5,
    help="Seconds between async heartbeat ping calls",
)
parser.add_argument(
    "--max-stream-events",
    type=int,
    default=40,
    help="Cap displayed stream events so demo output stays readable",
)
parser.add_argument(
    "--include-idle-path-events",
    action="store_true",
    help="Include idle path events without task_id (can be noisy)",
)
args = parser.parse_args()


TERMINAL_TASK_EVENTS = {"task.completed", "task.failed", "task.canceled"}


def _is_idle_path_event(event: dict[str, Any]) -> bool:
    if event.get("event") != "baritone.path_event":
        return False

    data = event.get("data")
    if not isinstance(data, dict):
        return False

    task_id = data.get("task_id")
    return task_id in (None, "")


def _event_task_id(event: dict[str, Any]) -> str | None:
    data = event.get("data")
    if not isinstance(data, dict):
        return None

    task_id = data.get("task_id")
    if isinstance(task_id, str) and task_id:
        return task_id
    return None


async def _event_stream_worker(
    client,
    stop_event: asyncio.Event,
    target_task_ref: dict[str, str | None],
    terminal_future: asyncio.Future[dict[str, Any]],
) -> None:
    displayed = 0
    skipped_idle = 0
    capped_notice_printed = False

    async for event in client.events():
        if stop_event.is_set():
            break

        target_task_id = target_task_ref["value"]
        event_name = event.get("event")
        event_task_id = _event_task_id(event)

        if (
            target_task_id
            and isinstance(event_name, str)
            and event_name in TERMINAL_TASK_EVENTS
            and event_task_id == target_task_id
            and not terminal_future.done()
        ):
            terminal_future.set_result(event)

        if not args.include_idle_path_events and _is_idle_path_event(event):
            skipped_idle += 1
            continue

        if args.max_stream_events > 0 and displayed >= args.max_stream_events:
            if not capped_notice_printed:
                step(
                    "Stream display cap reached; continuing to monitor in background for terminal events."
                )
                capped_notice_printed = True
            continue

        displayed += 1
        print(f"[stream {displayed:02}] {summarize_event(event)}")

    if skipped_idle:
        step(f"Stream skipped {skipped_idle} idle path events.")


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


async def demo(client):
    step("Async-only demo: concurrent event stream + heartbeat + task control in one event loop.")
    status = await client.status_get()
    print(
        "[status] "
        + f"in_world={status.get('in_world')}, "
        + f"baritone_available={status.get('baritone_available')}, "
        + f"authenticated={status.get('authenticated')}"
    )

    stop_event = asyncio.Event()
    target_task_ref: dict[str, str | None] = {"value": None}
    terminal_future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()

    stream_task = asyncio.create_task(
        _event_stream_worker(client, stop_event, target_task_ref, terminal_future),
        name="pyritone-demo-stream",
    )
    heartbeat_task = asyncio.create_task(
        _heartbeat_worker(client, stop_event),
        name="pyritone-demo-heartbeat",
    )

    try:
        step(f"Dispatching goto({args.x}, {args.y}, {args.z}) while stream + heartbeat stay active.")
        dispatch = await client.goto(args.x, args.y, args.z)
        print(f"[dispatch] {summarize_dispatch(dispatch)}")

        task_id = dispatch.get("task_id")
        if not task_id:
            step("No task_id returned. Ending async workflow cleanly.")
            return 0

        target_task_ref["value"] = task_id

        timeout_seconds = max(args.cancel_after, 0.1)
        try:
            terminal_event = await asyncio.wait_for(asyncio.shield(terminal_future), timeout=timeout_seconds)
            step("Task reached terminal state before auto-cancel timeout.")
        except asyncio.TimeoutError:
            step(f"No terminal event after {args.cancel_after:.1f}s. Sending async cancel(task_id).")
            cancel_result = await client.cancel(task_id=task_id)
            print(f"[cancel] canceled={cancel_result.get('canceled')} task_id={task_id}")

            try:
                terminal_event = await asyncio.wait_for(asyncio.shield(terminal_future), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                step("Still no terminal event after cancel timeout. Stopping demo to avoid endless heartbeat.")
                return 0

        print(f"[terminal] {summarize_event(terminal_event)}")
        terminal_reason = task_reason(terminal_event)
        if terminal_reason:
            step(f"Terminal reason: {terminal_reason}")

        event_name = terminal_event.get("event")
        if isinstance(event_name, str) and event_name in TERMINAL_TASK_EVENTS:
            step(f"Observed async terminal event: {event_name}")

        return 0
    finally:
        stop_event.set()
        await _stop_task(heartbeat_task)
        await _stop_task(stream_task)


if __name__ == "__main__":
    raise SystemExit(run_async_demo("08 - Async Workflow", demo))
