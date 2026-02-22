from __future__ import annotations

import json
import shutil
import subprocess
import sys

from _common import banner, step


COMMANDS: list[list[str]] = [
    ["ping"],
    ["status"],
    ["exec", "help"],
    ["cancel"],
]


def _run_command(prefix: list[str], suffix: list[str]) -> int:
    full_command = [*prefix, *suffix]
    print("$ " + " ".join(full_command))

    result = subprocess.run(full_command, capture_output=True, text=True)
    print(f"exit={result.returncode}")

    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
            print(json.dumps(parsed, indent=2, sort_keys=True))
        except json.JSONDecodeError:
            print(result.stdout.strip())

    if result.stderr.strip():
        print("stderr:")
        print(result.stderr.strip())

    print()
    return result.returncode


def main() -> int:
    banner("10 - CLI Entrypoints")
    step("Running pyritone CLI commands using default discovery.")

    if shutil.which("pyritone"):
        prefix = ["pyritone"]
    else:
        step("'pyritone' executable not found on PATH, using 'python -m pyritone' fallback.")
        prefix = [sys.executable, "-m", "pyritone"]

    worst_code = 0
    for suffix in COMMANDS:
        exit_code = _run_command(prefix, suffix)
        worst_code = max(worst_code, exit_code)

    if worst_code == 0:
        step("CLI demo finished.")
    else:
        step("CLI demo finished with at least one non-zero command exit code.")

    return worst_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("[stop] Interrupted with Ctrl+C.")
        raise SystemExit(130)
