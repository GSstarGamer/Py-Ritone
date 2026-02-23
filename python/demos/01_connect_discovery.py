from __future__ import annotations

from _common import print_json, run_async_demo, step


async def demo(client):
    step("Using default discovery: bridge-info file or PYRITONE_* overrides.")
    print_json("ping()", await client.ping())
    print_json("status_get()", await client.status_get())
    return 0


if __name__ == "__main__":
    raise SystemExit(run_async_demo("01 - Connect + Discovery", demo))
