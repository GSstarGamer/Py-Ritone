from __future__ import annotations

from typing import Any

from ._core import dispatch_async
from ._types import CommandArg, CommandDispatchResult


class AsyncWorldCommands:
    async def click(self, *args: CommandArg) -> CommandDispatchResult:
        """Open click

Canonical command: `click`
Aliases: none
Usage:
- `> click`
Source: `ClickCommand.java`"""
        return await dispatch_async(self, 'click', *args)

    async def farm(self, *args: CommandArg) -> CommandDispatchResult:
        """Farm nearby crops

Canonical command: `farm`
Aliases: none
Usage:
- `> farm - farms every crop it can find.`
- `> farm <range> - farm crops within range from the starting position.`
- `> farm <range> <waypoint> - farm crops within range from waypoint.`
Source: `FarmCommand.java`"""
        return await dispatch_async(self, 'farm', *args)

    async def find(self, *args: CommandArg) -> CommandDispatchResult:
        """Find positions of a certain block

Canonical command: `find`
Aliases: none
Usage:
- `> find <block> [...] - Try finding the listed blocks`
Source: `FindCommand.java`"""
        return await dispatch_async(self, 'find', *args)

    async def follow(self, *args: CommandArg) -> CommandDispatchResult:
        """Follow entity things

Canonical command: `follow`
Aliases: none
Usage:
- `> follow entities - Follows all entities.`
- `> follow entity <entity1> <entity2> <...> - Follow certain entities (for example 'skeleton', 'horse' etc.)`
- `> follow players - Follow players`
- `> follow player <username1> <username2> <...> - Follow certain players`
Source: `FollowCommand.java`"""
        return await dispatch_async(self, 'follow', *args)

    async def mine(self, *args: CommandArg) -> CommandDispatchResult:
        """Mine some blocks

Canonical command: `mine`
Aliases: none
Usage:
- `> mine diamond_ore - Mines all diamonds it can find.`
Source: `MineCommand.java`"""
        return await dispatch_async(self, 'mine', *args)

    async def pickup(self, *args: CommandArg) -> CommandDispatchResult:
        """Pickup items

Canonical command: `pickup`
Aliases: none
Usage:
- `> pickup - Pickup anything`
- `> pickup <item1> <item2> <...> - Pickup certain items`
Source: `PickupCommand.java`"""
        return await dispatch_async(self, 'pickup', *args)
