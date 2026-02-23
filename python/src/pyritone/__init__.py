import logging

from .baritone import BaritoneNamespace, GoalRef, TypedTaskHandle, TypedTaskResult
from .client_async import AsyncPyritoneClient, Client
from .client_sync import PyritoneClient
from .commands import ALIAS_TO_CANONICAL, BARITONE_VERSION, COMMAND_SPECS, CommandArg, CommandDispatchResult
from . import minecraft
from .models import BridgeError, BridgeInfo, DiscoveryError, RemoteRef, TypedCallError

__all__ = [
    "ALIAS_TO_CANONICAL",
    "AsyncPyritoneClient",
    "BARITONE_VERSION",
    "BaritoneNamespace",
    "BridgeError",
    "BridgeInfo",
    "Client",
    "COMMAND_SPECS",
    "CommandArg",
    "CommandDispatchResult",
    "DiscoveryError",
    "GoalRef",
    "PyritoneClient",
    "RemoteRef",
    "TypedTaskHandle",
    "TypedTaskResult",
    "TypedCallError",
    "minecraft",
]

logging.getLogger("pyritone").addHandler(logging.NullHandler())
