from __future__ import annotations

import asyncio

from pyritone import BridgeError, Client
from pyritone.minecraft import entities

EMPTY_POLL_DELAY_SECONDS = 0.0
ERROR_RETRY_DELAY_SECONDS = 0


async def main() -> None:
    async with Client() as client:
        player = await client.get_player()
        print("Connected. Walking nearest mobs...")

        while True:
            try:
                entities_now = await player.get_entities(types=[entities.GROUP_MOBS])
            except BridgeError as error:
                if error.code == "UNAUTHORIZED":
                    print(f"Bridge disconnected: {error}")
                    break
                print(f"entities.list failed: {error}")
                await asyncio.sleep(ERROR_RETRY_DELAY_SECONDS)
                continue
            except (ConnectionError, RuntimeError) as error:
                print(f"Bridge disconnected: {error}")
                break

            if not entities_now:
                await asyncio.sleep(EMPTY_POLL_DELAY_SECONDS)
                continue

            print(f"Found {len(entities_now)} mobs (nearest-first):")
            for index, found in enumerate(entities_now, start=1):
                print(
                    f"  {index}. {found.type_id} ({found.id}) at "
                    f"{found.x:.1f}, {found.y:.1f}, {found.z:.1f}"
                )

            # Iterate IDs only. Before using an entity position, refresh the list and
            # resolve the same ID again so we always use current coordinates.
            candidate_ids = [entity.id for entity in entities_now]

            for entity_id in candidate_ids:
                try:
                    latest_entities = await player.get_entities(types=[entities.GROUP_MOBS])
                    latest_entity = next((entry for entry in latest_entities if entry.id == entity_id), None)
                    if latest_entity is None:
                        print(f"Entity {entity_id} is gone; skipping.")
                        continue

                    print(
                        f"Walking to {latest_entity.type_id} ({latest_entity.id}) at "
                        f"{latest_entity.x:.1f}, {latest_entity.y:.1f}, {latest_entity.z:.1f}"
                    )
                    terminal = await client.goto_entity(latest_entity, wait=True)
                    print(f"Finished {latest_entity.id}: {terminal.get('event', 'unknown')}")
                except BridgeError as error:
                    if error.code == "UNAUTHORIZED":
                        print(f"Bridge disconnected: {error}")
                        return
                    print(f"Skipping entity {entity_id}: {error}")
                    continue
                except (ConnectionError, RuntimeError) as error:
                    print(f"Bridge disconnected: {error}")
                    return
                except Exception as error:  # noqa: BLE001
                    print(f"Skipping entity {entity_id}: {error}")
                    continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")
