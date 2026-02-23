from __future__ import annotations

import re
from typing import TypeAlias

_DEFAULT_NAMESPACE = "minecraft"
_NAMESPACE_RE = re.compile(r"^[a-z0-9_.-]+$")
_PATH_RE = re.compile(r"^[a-z0-9/._-]+$")


def _normalize_identifier(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Expected str identifier, got {type(value)!r}")
    if not value:
        raise ValueError("Identifier cannot be empty")

    namespace: str
    path: str
    if ":" in value:
        namespace, path = value.split(":", 1)
    else:
        namespace, path = _DEFAULT_NAMESPACE, value

    if not namespace or not _NAMESPACE_RE.fullmatch(namespace):
        raise ValueError(f"Invalid identifier namespace: {namespace!r}")
    if not path or not _PATH_RE.fullmatch(path):
        raise ValueError(f"Invalid identifier path: {path!r}")
    return f"{namespace}:{path}"


class MinecraftIdentifier(str):
    def __new__(cls, value: str) -> "MinecraftIdentifier":
        return super().__new__(cls, _normalize_identifier(value))

    @property
    def namespace(self) -> str:
        return self.split(":", 1)[0]

    @property
    def path(self) -> str:
        return self.split(":", 1)[1]


class BlockId(MinecraftIdentifier):
    pass


class ItemId(MinecraftIdentifier):
    pass


class EntityId(MinecraftIdentifier):
    pass


BlockLike: TypeAlias = str | BlockId
ItemLike: TypeAlias = str | ItemId
EntityLike: TypeAlias = str | EntityId


def coerce_block_id(value: BlockLike) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Expected block identifier string, got {type(value)!r}")
    return value


def coerce_item_id(value: ItemLike) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Expected item identifier string, got {type(value)!r}")
    return value


def coerce_entity_id(value: EntityLike) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Expected entity identifier string, got {type(value)!r}")
    return value


__all__ = [
    "BlockId",
    "BlockLike",
    "EntityId",
    "EntityLike",
    "ItemId",
    "ItemLike",
    "MinecraftIdentifier",
    "coerce_block_id",
    "coerce_entity_id",
    "coerce_item_id",
]
