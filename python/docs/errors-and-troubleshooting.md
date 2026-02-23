# Errors And Troubleshooting

Common failure codes and what to do next.

### When to use this

- You got a `BridgeError` or `DiscoveryError`.
- A command dispatch fails unexpectedly.

### Example

```python
from pyritone import BridgeError, Client, DiscoveryError

client = Client()
try:
    await client.connect()
    print(await client.status_get())
except DiscoveryError as error:
    print("Discovery failed:", error)
except BridgeError as error:
    print("Bridge error:", error.code, error.message)
finally:
    await client.close()
```

### Return shape

```text
BridgeError:
- code: protocol error code
- message: server message
- payload: full response envelope
- details: optional structured error data (`error.data`)

TypedCallError (for `api.*` methods):
- same fields as BridgeError with typed-call specific codes/details

DiscoveryError:
- message with checked paths/inputs
```

### Common error codes

- `UNAUTHORIZED`
- `BAD_REQUEST`
- `METHOD_NOT_FOUND`
- `NOT_IN_WORLD`
- `BARITONE_UNAVAILABLE`
- `EXECUTION_FAILED`
- `INTERNAL_ERROR`
- `API_*` typed-call error family (`API_METHOD_NOT_FOUND`, `API_ARGUMENT_COERCION_FAILED`, etc.)

### Common mistakes

- Running Python before the mod has produced bridge metadata.
- Using stale token after reinstalling/modifying client environment.
- Sending world-dependent commands before joining a world.

### Related methods

- `connection-and-discovery.md`
- `tasks-events-and-waiting.md`
- `../runbook.md`
