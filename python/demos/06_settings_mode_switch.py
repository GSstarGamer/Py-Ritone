from __future__ import annotations

import argparse

from _common import print_json, run_async_demo, step
from pyritone import BridgeError


MODES: dict[str, dict[str, bool]] = {
    "builder": {
        "allowPlace": True,
        "allowSprint": True,
    },
    "careful": {
        "allowPlace": False,
        "allowSprint": False,
    },
}


parser = argparse.ArgumentParser(description="Show settings API and mode presets")
parser.add_argument("--mode", choices=sorted(MODES.keys()), default="builder")
args = parser.parse_args()


async def _apply_mode(client, mode_name: str) -> None:
    mode = MODES[mode_name]
    step(f"Applying mode '{mode_name}' with {len(mode)} settings")

    for setting_name, value in mode.items():
        try:
            dispatch = await client.settings.set(setting_name, value)
            print_json(f"set {setting_name} {value}", dispatch)
        except BridgeError as error:
            print(
                f"[warn] Could not set {setting_name!r}: {error.code} - {error.message}. "
                "Continuing with remaining settings."
            )


async def demo(client):
    step("Handle methods: set/get/toggle/reset")
    print_json("allowPlace.set(True)", await client.settings.allowPlace.set(True))
    print_json("allowPlace.get()", await client.settings.allowPlace.get())
    print_json("allowPlace.toggle()", await client.settings.allowPlace.toggle())
    print_json("allowPlace.reset()", await client.settings.allowPlace.reset())

    await _apply_mode(client, args.mode)

    step("Final checks")
    print_json("allowPlace.get()", await client.settings.allowPlace.get())
    print_json("allowSprint.get()", await client.settings.allowSprint.get())
    return 0


if __name__ == "__main__":
    raise SystemExit(run_async_demo("06 - Settings Mode Switch", demo))
