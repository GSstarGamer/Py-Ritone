from __future__ import annotations

from typing import Any

from ._core import dispatch_sync
from ._types import CommandArg, CommandDispatchResult


class SyncControlCommands:
    def forcecancel(self, *args: CommandArg) -> CommandDispatchResult:
        """Force cancel

Canonical command: `forcecancel`
Aliases: none
Usage:
- `> forcecancel`
Source: `ForceCancelCommand.java`"""
        return dispatch_sync(self, 'forcecancel', *args)

    def modified(self, *args: CommandArg) -> CommandDispatchResult:
        """List modified settings

Canonical command: `modified`
Aliases: mod, baritone, modifiedsettings
Source: `DefaultCommands.java (CommandAlias)`"""
        return self.set('modified', *args)

    def pause(self, *args: CommandArg) -> CommandDispatchResult:
        """Pauses Baritone until you use resume

Canonical command: `pause`
Aliases: p, paws
Usage:
- `> pause`
Source: `ExecutionControlCommands.java`"""
        return dispatch_sync(self, 'pause', *args)

    def paused(self, *args: CommandArg) -> CommandDispatchResult:
        """Tells you if Baritone is paused

Canonical command: `paused`
Aliases: none
Usage:
- `> paused`
Source: `ExecutionControlCommands.java`"""
        return dispatch_sync(self, 'paused', *args)

    def reset(self, *args: CommandArg) -> CommandDispatchResult:
        """Reset all settings or just one

Canonical command: `reset`
Aliases: none
Source: `DefaultCommands.java (CommandAlias)`"""
        return self.set('reset', *args)

    def resume(self, *args: CommandArg) -> CommandDispatchResult:
        """Resumes Baritone after a pause

Canonical command: `resume`
Aliases: r, unpause, unpaws
Usage:
- `> resume`
Source: `ExecutionControlCommands.java`"""
        return dispatch_sync(self, 'resume', *args)

    def set(self, *args: CommandArg) -> CommandDispatchResult:
        """View or change settings

Canonical command: `set`
Aliases: setting, settings
Usage:
- `> set - Same as `set list``
- `> set list [page] - View all settings`
- `> set modified [page] - View modified settings`
- `> set <setting> - View the current value of a setting`
- `> set <setting> <value> - Set the value of a setting`
- `> set reset all - Reset ALL SETTINGS to their defaults`
- `> set reset <setting> - Reset a setting to its default`
- `> set toggle <setting> - Toggle a boolean setting`
- `> set save - Save all settings (this is automatic tho)`
- `> set load - Load settings from settings.txt`
- `> set load [filename] - Load settings from another file in your minecraft/baritone`
Source: `SetCommand.java`"""
        return dispatch_sync(self, 'set', *args)

    def baritone(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `modified`."""
        return self.modified(*args)

    def c(self, task_id: str | None = None) -> dict[str, Any]:
        """Alias for `cancel`."""
        return self.cancel(task_id=task_id)

    def mod(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `modified`."""
        return self.modified(*args)

    def modifiedsettings(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `modified`."""
        return self.modified(*args)

    def p(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `pause`."""
        return self.pause(*args)

    def paws(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `pause`."""
        return self.pause(*args)

    def r(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `resume`."""
        return self.resume(*args)

    def setting(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `set`."""
        return self.set(*args)

    def settings(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `set`."""
        return self.set(*args)

    def stop(self, task_id: str | None = None) -> dict[str, Any]:
        """Alias for `cancel`."""
        return self.cancel(task_id=task_id)

    def unpause(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `resume`."""
        return self.resume(*args)

    def unpaws(self, *args: CommandArg) -> CommandDispatchResult:
        """Alias for `resume`."""
        return self.resume(*args)
