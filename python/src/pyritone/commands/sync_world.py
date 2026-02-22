from __future__ import annotations

from typing import Any

from ._core import dispatch_sync
from ._types import CommandArg, CommandDispatchResult


class SyncWorldCommands:
    def click(self, *args: CommandArg) -> CommandDispatchResult:
        """Open click

Canonical command: `click`
Aliases: none
Usage:
- `> click`
Source: `ClickCommand.java`"""
        return dispatch_sync(self, 'click', *args)

    def farm(self, *args: CommandArg) -> CommandDispatchResult:
        """Farm nearby crops

Canonical command: `farm`
Aliases: none
Usage:
- `> farm - farms every crop it can find.`
- `> farm <range> - farm crops within range from the starting position.`
- `> farm <range> <waypoint> - farm crops within range from waypoint.`
Source: `FarmCommand.java`"""
        return dispatch_sync(self, 'farm', *args)

    def find(self, *args: CommandArg) -> CommandDispatchResult:
        """Find positions of a certain block

Canonical command: `find`
Aliases: none
Usage:
- `> find <block> [...] - Try finding the listed blocks`
Source: `FindCommand.java`"""
        return dispatch_sync(self, 'find', *args)

    def follow(self, *args: CommandArg) -> CommandDispatchResult:
        """Follow entity things

Canonical command: `follow`
Aliases: none
Usage:
- `> follow entities - Follows all entities.`
- `> follow entity <entity1> <entity2> <...> - Follow certain entities (for example 'skeleton', 'horse' etc.)`
- `> follow players - Follow players`
- `> follow player <username1> <username2> <...> - Follow certain players`
Source: `FollowCommand.java`"""
        return dispatch_sync(self, 'follow', *args)

    def mine(self, *args: CommandArg) -> CommandDispatchResult:
        """Mine some blocks

Canonical command: `mine`
Aliases: none
Usage:
- `> mine diamond_ore - Mines all diamonds it can find.`
Source: `MineCommand.java`"""
        return dispatch_sync(self, 'mine', *args)

    def pickup(self, *args: CommandArg) -> CommandDispatchResult:
        """Pickup items

Canonical command: `pickup`
Aliases: none
Usage:
- `> pickup - Pickup anything`
- `> pickup <item1> <item2> <...> - Pickup certain items`
Source: `PickupCommand.java`"""
        return dispatch_sync(self, 'pickup', *args)
