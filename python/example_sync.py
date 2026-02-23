import asyncio
import sys
from pathlib import Path

_repo_src = Path(__file__).resolve().parent / "src"
if _repo_src.exists():
    sys.path.insert(0, str(_repo_src))

from pyritone import PyritoneClient


async def main() -> None:
    # PyritoneClient is now an async alias.
    client = PyritoneClient()
    await client.connect()
    try:
        print(await client.ping())
        print(await client.status_get())

        print(await client.settings.allowPlace.set(True))
        print(await client.settings.allowPlace.get())

        dispatch = await client.goto(100, 70, 100)
        print(dispatch)

        task_id = dispatch.get("task_id")
        if task_id:
            print(await client.wait_for_task(task_id))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
