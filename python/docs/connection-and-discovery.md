# Connection And Discovery

How `pyritone` finds and authenticates with the local bridge.

### When to use this

- You need to understand zero-setup behavior.
- You are debugging token/host/port issues.

### Example

```python
from pyritone import Client

client = Client()
await client.connect()
try:
    print(await client.ping())
finally:
    await client.close()
```

### Return shape

```text
connect() returns None after:
1) bridge discovery
2) websocket connection
3) auth.login handshake
```

### Discovery precedence

1. Explicit constructor args
2. Environment variables:
   - `PYRITONE_BRIDGE_INFO`
   - `PYRITONE_TOKEN`
   - `PYRITONE_WS_URL`
   - `PYRITONE_HOST`
   - `PYRITONE_PORT`
3. Auto-discovery file:
   - `<minecraft>/config/pyritone_bridge/bridge-info.json`

### Common mistakes

- Setting only `PYRITONE_HOST`/`PYRITONE_PORT` without a token.
- Pointing `PYRITONE_BRIDGE_INFO` to a file that exists but has no `token`.
- Editing token manually while Minecraft is running.

### Related methods

- `async-client.md`
- `errors-and-troubleshooting.md`
