"""Quick local test for the running Py-Ritone bridge.

Usage:
  1) Start Minecraft dev client from mod/:
       .\\gradlew.bat devClient
  2) Join a world in Minecraft.
  3) From python/ run:
       python example.py --x 100 --y 70 --z 100
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repository checkout without installing the package first.
_repo_src = Path(__file__).resolve().parent / "src"
if _repo_src.exists():
    sys.path.insert(0, str(_repo_src))

from pyritone import BridgeError, PyritoneClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Py-Ritone goto example")
    parser.add_argument("--x", type=int, default=100, help="Target X coordinate")
    parser.add_argument("--y", type=int, default=70, help="Target Y coordinate")
    parser.add_argument("--z", type=int, default=100, help="Target Z coordinate")
    parser.add_argument(
        "--bridge-info",
        default=None,
        help="Optional explicit path to bridge-info.json",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Only dispatch goto and exit without waiting for completion",
    )
    return parser.parse_args()


def detect_dev_bridge_info_path(explicit_path: str | None) -> str | None:
    if explicit_path:
        return explicit_path

    repo_root = Path(__file__).resolve().parents[1]
    dev_path = repo_root / "mod" / "run" / "config" / "pyritone_bridge" / "bridge-info.json"
    if dev_path.exists():
        return str(dev_path)

    return None


def _task_end_reason(event: dict[str, object]) -> str | None:
    data = event.get("data")
    if not isinstance(data, dict):
        return None

    for key in ("detail", "reason", "message", "path_event", "stage"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def main() -> int:
    args = parse_args()
    bridge_info_path = detect_dev_bridge_info_path(args.bridge_info)

    if bridge_info_path:
        print(f"Using bridge info: {bridge_info_path}")

    try:
        with PyritoneClient(bridge_info_path=bridge_info_path) as client:
            print(f"Dispatching goto({args.x}, {args.y}, {args.z})...")
            dispatch = client.goto(args.x, args.y, args.z)

            print(f"Command text: {dispatch['command_text']}")
            print(f"Accepted: {dispatch.get('accepted', True)}")

            task_id = dispatch.get("task_id")
            if not task_id:
                print("No task_id returned; nothing to wait on.")
                return 0

            print(f"Task ID: {task_id}")
            if args.no_wait:
                return 0

            print("Waiting for task completion...")
            terminal_event = client.wait_for_task(task_id)
            event_name = terminal_event.get("event", "task.completed")
            reason = _task_end_reason(terminal_event)

            if reason:
                print(f"Task ended: {event_name} ({reason})")
            else:
                print(f"Task ended: {event_name}")
    except BridgeError as error:
        print(f"Bridge error: {error.code} - {error.message}")
        print("Hint: if using the Gradle dev client, pass --bridge-info ..\\mod\\run\\config\\pyritone_bridge\\bridge-info.json")
        return 1
    except Exception as error:
        print(f"Unexpected error: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
