from __future__ import annotations

from .client_async import AsyncPyritoneClient, Client

# Temporary compatibility alias: PyritoneClient is now async-only.
PyritoneClient = Client

__all__ = ["Client", "AsyncPyritoneClient", "PyritoneClient"]
