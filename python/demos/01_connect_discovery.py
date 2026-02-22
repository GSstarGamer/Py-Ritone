from __future__ import annotations

from _common import print_json, run_sync_demo, step


def demo(client):
    step("Using default discovery: bridge-info file or PYRITONE_* overrides.")
    print_json("ping()", client.ping())
    print_json("status_get()", client.status_get())
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sync_demo("01 - Connect + Discovery", demo))
