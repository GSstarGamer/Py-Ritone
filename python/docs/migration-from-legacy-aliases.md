# Migration From Legacy Client Aliases

Move existing code after `pyritone.Client` switched to the Discord-style event client.

### When to use this

- Your code imports `PyritoneClient` or `AsyncPyritoneClient`.
- You previously used `from pyritone import Client` for async transport workflows.

### Event-style default (`Client`)

```python
import pyritone

client = pyritone.client()


@client.event
async def on_ready() -> None:
    print("connected")


client.connect()
```

### Raw async migration target

```text
If your old code used:
  from pyritone import Client
for async/await transport control, migrate to:
  from pyritone import AsyncPyritoneClient
or:
  from pyritone import AsyncClient
```

### Raw async example

```python
import asyncio
from pyritone import AsyncPyritoneClient


async def main() -> None:
    async with AsyncPyritoneClient() as client:
        print(await client.ping())


asyncio.run(main())
```

### Common mistakes

- Keeping async examples on top-level `Client`.
- Expecting `client.connect()` on top-level `Client` to be awaitable.
- Mixing decorator event style and raw async style in the same entrypoint.

### Related methods

- `async-client.md`
- `quickstart.md`
- `release-parity-fallback-report.md`
