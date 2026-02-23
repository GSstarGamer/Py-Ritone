import logging

from .baritone import BaritoneNamespace, GoalRef, TypedTaskHandle, TypedTaskResult
from .client_async import AsyncPyritoneClient, Client
from .client_sync import PyritoneClient
from .commands import ALIAS_TO_CANONICAL, BARITONE_VERSION, COMMAND_SPECS, CommandArg, CommandDispatchResult
from . import minecraft
from .models import BridgeError, BridgeInfo, DiscoveryError, RemoteRef, TypedCallError, VisibleEntity

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
    "VisibleEntity",
    "minecraft",
]


def _configure_default_logger() -> None:
    logger = logging.getLogger("pyritone")
    has_non_null_handler = any(not isinstance(handler, logging.NullHandler) for handler in logger.handlers)
    has_root_handler = bool(logging.getLogger().handlers)

    if not has_non_null_handler and not has_root_handler:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)


_configure_default_logger()
