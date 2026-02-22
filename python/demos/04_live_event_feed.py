from __future__ import annotations

import argparse

from _common import print_json, run_sync_demo, step, summarize_event


parser = argparse.ArgumentParser(description="Print live bridge events")
parser.add_argument("--max-events", type=int, default=20, help="0 means unlimited")
parser.add_argument("--timeout", type=float, default=5.0)
parser.add_argument("--full-json", action="store_true")
args = parser.parse_args()


def demo(client):
    step(
        "Listening for bridge events. Trigger Baritone commands in-game or from other scripts. Press Ctrl+C to stop."
    )

    seen = 0
    while args.max_events <= 0 or seen < args.max_events:
        try:
            event = client.next_event(timeout=args.timeout)
        except TimeoutError:
            step("No event arrived in the timeout window. Still listening...")
            continue

        seen += 1
        print(f"event #{seen}: {summarize_event(event)}")
        if args.full_json:
            print_json("event payload", event)

    step(f"Reached max-events={args.max_events}; exiting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_sync_demo("04 - Live Event Feed", demo))
