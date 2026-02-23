# Migration From Legacy Client Aliases

Move existing code to `pyritone.Client` as the canonical async entry point.

### When to use this

- Your code imports `PyritoneClient` or `AsyncPyritoneClient`.
- You want a low-risk rename pass without changing behavior.

### Recommended import and flow

```python
import asyncio
from pyritone import Client


async def main() -> None:
    async with Client() as client:
        print(await client.ping())
        print(await client.status_get())


asyncio.run(main())
```

### Alias status

```text
PyritoneClient and AsyncPyritoneClient are temporary compatibility aliases to Client.
All client methods are async and must be awaited.
```

### Common mistakes

- Keeping old import names in new docs/examples.
- Treating alias names as sync clients.
- Mixing `Client` and alias names in the same code style guide.

### Related methods

- `async-client.md`
- `quickstart.md`
- `release-parity-fallback-report.md`
