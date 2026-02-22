from __future__ import annotations

import argparse

from _common import print_json, run_sync_demo, step
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


def _apply_mode(client, mode_name: str) -> None:
    mode = MODES[mode_name]
    step(f"Applying mode '{mode_name}' with {len(mode)} settings")

    for setting_name, value in mode.items():
        try:
            dispatch = client.settings.set(setting_name, value)
            print_json(f"set {setting_name} {value}", dispatch)
        except BridgeError as error:
            print(
                f"[warn] Could not set {setting_name!r}: {error.code} - {error.message}. "
                "Continuing with remaining settings."
            )


def demo(client):
    step("Property assignment style (sync): client.settings.allowPlace = True")
    client.settings.allowPlace = True
    if client.settings.last_dispatch is not None:
        print_json("last_dispatch", client.settings.last_dispatch)

    step("Handle methods: get/toggle/reset")
    print_json("allowPlace.get()", client.settings.allowPlace.get())
    print_json("allowPlace.toggle()", client.settings.allowPlace.toggle())
    print_json("allowPlace.reset()", client.settings.allowPlace.reset())

    _apply_mode(client, args.mode)

    step("Final checks")
    print_json("allowPlace.get()", client.settings.allowPlace.get())
    print_json("allowSprint.get()", client.settings.allowSprint.get())
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sync_demo("06 - Settings Mode Switch", demo))
