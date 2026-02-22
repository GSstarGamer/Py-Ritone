import sys 
from pathlib import Path

_repo_src = Path(__file__).resolve().parent / "src"
if _repo_src.exists():
    sys.path.insert(0, str(_repo_src))

from pyritone import PyritoneClient


with PyritoneClient() as client:
    print(client.ping())
    print(client.status_get())

    # Settings API (sync property-style)
    client.settings.allowPlace = True
    print(client.settings.allowPlace.get())
    # print(client.settings.allowPlace.toggle())
    # print(client.settings.allowPlace.reset())

    dispatch = client.goto(100, 70, 100)
    print(dispatch)

    task_id = dispatch.get("task_id")
    if task_id:
        print(client.wait_for_task(task_id))

