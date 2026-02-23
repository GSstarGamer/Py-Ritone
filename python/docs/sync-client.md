# Sync Client

`PyritoneClient` is now a temporary async alias of `Client`.

### When to use this

- You are migrating older code that imported `PyritoneClient`.
- You need to update imports gradually while moving to async call sites.

### Migration example

```python
from pyritone import PyritoneClient

client = PyritoneClient()
await client.connect()
try:
    print(await client.ping())
finally:
    await client.close()
```

### Return shape

```text
`PyritoneClient` and `AsyncPyritoneClient` map to the same async client class.
All methods are awaitable.
```

### Common mistakes

- Treating `PyritoneClient` as synchronous (it is async-only now).
- Forgetting `await client.connect()` before requests.
- Not awaiting command helpers.

### Related methods

- `async-client.md`
- `tasks-events-and-waiting.md`
- `settings-api.md`
