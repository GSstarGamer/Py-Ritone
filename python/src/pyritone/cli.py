from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from .client_async import Client


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pyritone", description="Python client for the Py-Ritone bridge")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--token")
    parser.add_argument("--bridge-info")
    parser.add_argument("--timeout", type=float, default=5.0)

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ping")
    subparsers.add_parser("status")

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("baritone_command")

    cancel_parser = subparsers.add_parser("cancel")
    cancel_parser.add_argument("--task-id")

    subparsers.add_parser("events")

    return parser


async def run_async(args: argparse.Namespace) -> int:
    client = Client(
        host=args.host,
        port=args.port,
        token=args.token,
        bridge_info_path=args.bridge_info,
        timeout=args.timeout,
    )

    await client.connect()
    try:
        output: dict[str, Any]
        if args.command == "ping":
            output = await client.ping()
            print(json.dumps(output, indent=2, sort_keys=True))
            return 0

        if args.command == "status":
            output = await client.status_get()
            print(json.dumps(output, indent=2, sort_keys=True))
            return 0

        if args.command == "exec":
            output = await client.execute(args.baritone_command)
            print(json.dumps(output, indent=2, sort_keys=True))
            return 0

        if args.command == "cancel":
            output = await client.cancel(task_id=args.task_id)
            print(json.dumps(output, indent=2, sort_keys=True))
            return 0

        if args.command == "events":
            while True:
                event = await client.next_event()
                print(json.dumps(event, sort_keys=True))

        return 1
    finally:
        await client.close()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return asyncio.run(run_async(args))
    except KeyboardInterrupt:
        return 130

