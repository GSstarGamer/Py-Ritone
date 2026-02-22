from __future__ import annotations

from typing import Any

from ._core import dispatch_sync
from ._types import CommandArg, CommandDispatchResult


class SyncWaypointsCommands:
    def home(self, *args: CommandArg) -> CommandDispatchResult:
        """Path to your home waypoint

Canonical command: `home`
Aliases: none
Source: `DefaultCommands.java (CommandAlias)`"""
        return self.waypoints('goto', 'home', *args)

    def sethome(self, *args: CommandArg) -> CommandDispatchResult:
        """Sets your home waypoint

Canonical command: `sethome`
Aliases: none
Source: `DefaultCommands.java (CommandAlias)`"""
        return self.waypoints('save', 'home', *args)

    def waypoints(self, *args: CommandArg) -> CommandDispatchResult:
        """Manage waypoints

Canonical command: `waypoints`
Aliases: waypoint, wp
Usage:
- `> wp [l/list] - List all waypoints.`
- `> wp <l/list> <tag> - List all waypoints by tag.`
- `> wp <s/save> - Save an unnamed USER waypoint at your current position`
- `> wp <s/save> [tag] [name] [pos] - Save a waypoint with the specified tag, name and position.`
- `> wp <i/info/show> <tag/name> - Show info on a waypoint by tag or name.`
- `> wp <d/delete> <tag/name> - Delete a waypoint by tag or name.`
- `> wp <restore> <n> - Restore the last n deleted waypoints.`
- `> wp <c/clear> <tag> - Delete all waypoints with the specified tag.`
- `> wp <g/goal> <tag/name> - Set a goal to a waypoint by tag or name.`
- `> wp <goto> <tag/name> - Set a goal to a waypoint by tag or name and start pathing.`
Source: `WaypointsCommand.java`"""
        return dispatch_sync(self, 'waypoints', *args)

    def waypoint(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `waypoints`."""
        return self.waypoints(*args)

    def wp(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `waypoints`."""
        return self.waypoints(*args)
