from __future__ import annotations

import argparse

from _common import print_json, run_sync_demo, step, summarize_dispatch, summarize_event, terminal_summary


parser = argparse.ArgumentParser(description="Use build_file with local Python-relative paths")
parser.add_argument("path", help="Schematic path; can be relative to this script or absolute")
parser.add_argument("--coords", nargs=3, type=int, metavar=("X", "Y", "Z"))
parser.add_argument("--base-dir", default=None, help="Optional base dir override for relative paths")
parser.add_argument("--wait", action="store_true", help="Wait for terminal task event")
args = parser.parse_args()


def demo(client):
    coords = tuple(args.coords) if args.coords else tuple()

    step("Dispatching build_file(...) with local path resolution")
    dispatch = client.build_file(args.path, *coords, base_dir=args.base_dir)
    print(f"build_file dispatch summary: {summarize_dispatch(dispatch)}")
    print_json("build_file dispatch", dispatch)

    if not args.wait:
        return 0

    task_id = dispatch.get("task_id")
    if not task_id:
        step("No task_id returned, so wait was requested but cannot run.")
        return 0

    step(f"Waiting for terminal task event for task_id={task_id}")
    terminal_event = client.wait_for_task(task_id)
    print(f"terminal event summary: {summarize_event(terminal_event)}")
    print_json("terminal event", terminal_event)
    step(terminal_summary(terminal_event))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sync_demo("09 - build_file Local Path", demo))
