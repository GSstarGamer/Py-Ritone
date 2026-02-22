from __future__ import annotations

import shlex

from _common import (
    parse_scalars,
    print_json,
    run_sync_demo,
    step,
    summarize_dispatch,
    summarize_event,
    terminal_summary,
)
from pyritone import BridgeError


HELP_TEXT = """
Commands:
  help
  ping
  status
  exec <baritone command>
  goto <x> <y> <z>
  wait [task_id]
  cancel [task_id]
  event [timeout]
  set <name> <value>
  get <name>
  toggle <name>
  reset <name>
  <wrapper_method> [args...]   # dynamic dispatch if method exists on client
  quit | exit
""".strip()


def _maybe_track_task_id(last_task_id: str | None, payload: dict) -> str | None:
    task_id = payload.get("task_id")
    if isinstance(task_id, str) and task_id:
        return task_id

    task = payload.get("task")
    if isinstance(task, dict):
        nested = task.get("task_id")
        if isinstance(nested, str) and nested:
            return nested

    return last_task_id


def demo(client):
    step("Interactive mini console connected. Type 'help' for commands, 'quit' to exit.")
    print(HELP_TEXT)

    last_task_id: str | None = None

    while True:
        try:
            line = input("pyritone> ").strip()
        except EOFError:
            print()
            break

        if not line:
            continue

        try:
            parts = shlex.split(line)
        except ValueError as error:
            print(f"[warn] Parse error: {error}")
            continue

        command = parts[0].lower()
        args = parts[1:]

        if command in {"quit", "exit"}:
            break

        if command == "help":
            print(HELP_TEXT)
            continue

        try:
            if command == "ping":
                result = client.ping()
                print_json("ping()", result)
                continue

            if command == "status":
                result = client.status_get()
                print_json("status_get()", result)
                continue

            if command == "exec":
                if not args:
                    print("usage: exec <baritone command>")
                    continue
                result = client.execute(" ".join(args))
                print_json("execute(...) result", result)
                last_task_id = _maybe_track_task_id(last_task_id, result)
                continue

            if command == "goto":
                if len(args) != 3:
                    print("usage: goto <x> <y> <z>")
                    continue
                x, y, z = (int(value) for value in args)
                dispatch = client.goto(x, y, z)
                print(f"goto() dispatch: {summarize_dispatch(dispatch)}")
                print_json("goto()", dispatch)
                last_task_id = _maybe_track_task_id(last_task_id, dispatch)
                continue

            if command == "wait":
                task_id = args[0] if args else last_task_id
                if not task_id:
                    print("No task_id provided and no remembered task_id.")
                    continue
                event = client.wait_for_task(task_id)
                print(f"terminal event: {summarize_event(event)}")
                print_json("terminal event", event)
                print(terminal_summary(event))
                continue

            if command == "cancel":
                task_id = args[0] if args else last_task_id
                result = client.cancel(task_id=task_id)
                print_json("cancel()", result)
                continue

            if command == "event":
                timeout = float(args[0]) if args else 5.0
                event = client.next_event(timeout=timeout)
                print(f"event: {summarize_event(event)}")
                print_json("event", event)
                continue

            if command == "set":
                if len(args) < 2:
                    print("usage: set <name> <value>")
                    continue
                setting_name = args[0]
                value = " ".join(args[1:])
                parsed_value = parse_scalars([value])[0]
                dispatch = client.settings.set(setting_name, parsed_value)
                print_json("settings.set(...)", dispatch)
                continue

            if command == "get":
                if len(args) != 1:
                    print("usage: get <name>")
                    continue
                dispatch = client.settings.get(args[0])
                print_json("settings.get(...)", dispatch)
                continue

            if command == "toggle":
                if len(args) != 1:
                    print("usage: toggle <name>")
                    continue
                dispatch = client.settings.toggle(args[0])
                print_json("settings.toggle(...)", dispatch)
                continue

            if command == "reset":
                if len(args) != 1:
                    print("usage: reset <name>")
                    continue
                dispatch = client.settings.reset(args[0])
                print_json("settings.reset(...)", dispatch)
                continue

            if hasattr(client, command):
                method = getattr(client, command)
                if not callable(method):
                    print(f"{command!r} exists but is not callable")
                    continue

                parsed_args = parse_scalars(args)
                result = method(*parsed_args)
                if isinstance(result, dict):
                    print_json(f"{command}(...) result", result)
                    last_task_id = _maybe_track_task_id(last_task_id, result)
                else:
                    print(result)
                continue

            print(f"Unknown command: {command}. Type 'help' for options.")
        except BridgeError as error:
            print(f"[bridge] {error.code}: {error.message}")
        except ValueError as error:
            print(f"[warn] {error}")

    step("Leaving mini console.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sync_demo("07 - Interactive Mini Console", demo))
