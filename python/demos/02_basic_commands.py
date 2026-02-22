from __future__ import annotations

from _common import print_json, run_sync_demo, step, summarize_dispatch


def demo(client):
    step("High-level wrappers first: help(), version(), set(...).")

    help_dispatch = client.help()
    print(f"help() summary: {summarize_dispatch(help_dispatch)}")
    print_json("help()", help_dispatch)

    version_dispatch = client.version()
    print(f"version() summary: {summarize_dispatch(version_dispatch)}")
    print_json("version()", version_dispatch)

    set_dispatch = client.set("allowPlace", True)
    print(f"set('allowPlace', True) summary: {summarize_dispatch(set_dispatch)}")
    print_json("set('allowPlace', True)", set_dispatch)

    step("Raw fallback: execute('help').")
    print_json("execute('help')", client.execute("help"))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sync_demo("02 - Basic Commands", demo))
