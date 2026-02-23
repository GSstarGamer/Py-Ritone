from __future__ import annotations

import argparse

from _common import run_async_demo, step, task_reason, terminal_summary


parser = argparse.ArgumentParser(description="Build a local schematic file with Pyritone")
parser.add_argument("path", help="Local schematic path (relative or absolute)")
parser.add_argument("--coords", nargs=3, type=int, metavar=("X", "Y", "Z"))
parser.add_argument("--wait", action="store_true", help="Wait until task reaches terminal event")
args = parser.parse_args()


async def demo(client):
    coords = tuple(args.coords) if args.coords else tuple()

    step("Setting maxFallHeightNoWater=255 so Baritone allows fall-damage-risk drops in this demo.")
    await client.settings.maxFallHeightNoWater.set(255)

    dispatch = await client.build_file(args.path, *coords)
    task_id = dispatch.get("task_id")

    print(f"accepted: {dispatch.get('accepted')}")
    print(f"task_id: {task_id}")
    print(f"command: {dispatch.get('command_text')}")

    if not args.wait:
        return 0

    if not task_id:
        step("No task_id returned, so cannot wait.")
        return 0

    step("Waiting for build to finish. Use #pyritone cancel to force-stop.")
    last_line: str | None = None

    def on_update(event):
        nonlocal last_line
        event_name = str(event.get("event"))
        if event_name == "baritone.path_event":
            return

        if event_name == "task.paused":
            line = "update: paused"
        elif event_name == "task.resumed":
            line = "update: resumed"
        elif event_name == "task.progress":
            line = "update: in progress"
        else:
            reason = task_reason(event)
            line = f"update: {event_name} ({reason})" if reason else f"update: {event_name}"

        if line != last_line:
            print(line)
            last_line = line

    terminal_event = await client.wait_for_task(task_id, on_update=on_update)
    print(terminal_summary(terminal_event))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_async_demo("09 - build_file Local Path", demo))
