from __future__ import annotations

from .client_async import AsyncPyritoneClient, Client

# Temporary compatibility alias retained for the v0.2.x migration window.
PyritoneClient = Client

__all__ = ["Client", "AsyncPyritoneClient", "PyritoneClient"]
