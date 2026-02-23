from __future__ import annotations

from _common import print_json, run_async_demo, step, summarize_dispatch


async def demo(client):
    step("High-level wrappers first: help(), version(), set(...).")

    help_dispatch = await client.help()
    print(f"help() summary: {summarize_dispatch(help_dispatch)}")
    print_json("help()", help_dispatch)

    version_dispatch = await client.version()
    print(f"version() summary: {summarize_dispatch(version_dispatch)}")
    print_json("version()", version_dispatch)

    set_dispatch = await client.set("allowPlace", True)
    print(f"set('allowPlace', True) summary: {summarize_dispatch(set_dispatch)}")
    print_json("set('allowPlace', True)", set_dispatch)

    step("Raw command transport: execute('help').")
    print_json("execute('help')", await client.execute("help"))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_async_demo("02 - Basic Commands", demo))
