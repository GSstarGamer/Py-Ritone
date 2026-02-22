from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.request import urlopen

BARITONE_VERSION = "v1.15.0"
BARITONE_BASE_RAW_URL = f"https://raw.githubusercontent.com/cabaletta/baritone/{BARITONE_VERSION}/src/main/java/baritone/command/defaults"

DEFAULT_COMMANDS_URL = f"{BARITONE_BASE_RAW_URL}/DefaultCommands.java"
EXECUTION_CONTROL_URL = f"{BARITONE_BASE_RAW_URL}/ExecutionControlCommands.java"

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "src" / "pyritone" / "commands"
DOCS_PATH = ROOT / "docs" / "baritone-commands.md"

DOMAIN_BY_COMMAND = {
    "axis": "navigation",
    "blacklist": "navigation",
    "build": "build",
    "cancel": "control",
    "click": "world",
    "come": "navigation",
    "elytra": "navigation",
    "eta": "info",
    "explore": "navigation",
    "explorefilter": "navigation",
    "farm": "world",
    "find": "world",
    "follow": "world",
    "forcecancel": "control",
    "gc": "info",
    "goal": "navigation",
    "goto": "navigation",
    "help": "info",
    "home": "waypoints",
    "invert": "navigation",
    "litematica": "build",
    "mine": "world",
    "modified": "control",
    "path": "navigation",
    "pause": "control",
    "paused": "control",
    "pickup": "world",
    "proc": "info",
    "reloadall": "info",
    "render": "info",
    "repack": "info",
    "reset": "control",
    "resume": "control",
    "saveall": "info",
    "sel": "build",
    "set": "control",
    "sethome": "waypoints",
    "surface": "navigation",
    "thisway": "navigation",
    "tunnel": "navigation",
    "version": "info",
    "waypoints": "waypoints",
}

PYTHON_NAME_OVERRIDES = {
    "?": "qmark",
}

SPECIAL_CANONICAL_CALLS = {
    "modified": ("set", ["modified"]),
    "reset": ("set", ["reset"]),
    "sethome": ("waypoints", ["save", "home"]),
    "home": ("waypoints", ["goto", "home"]),
}

DOMAIN_MODULES = [
    "navigation",
    "world",
    "build",
    "control",
    "info",
    "waypoints",
]


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    name: str
    aliases: tuple[str, ...]
    short_desc: str
    long_desc_lines: tuple[str, ...]
    usage_lines: tuple[str, ...]
    source_file: str
    domain: str
    target: str | None = None


def fetch_text(url: str) -> str:
    with urlopen(url) as response:
        return response.read().decode("utf-8")


def parse_java_string_literal(literal: str) -> str:
    return ast.literal_eval(literal)


def extract_string_literals(text: str) -> list[str]:
    literals = re.findall(r'"(?:\\.|[^"\\])*"', text)
    return [parse_java_string_literal(literal) for literal in literals]


def split_top_level_args(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_string = False
    escape = False

    for character in text:
        if in_string:
            current.append(character)
            if escape:
                escape = False
            elif character == "\\":
                escape = True
            elif character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
            current.append(character)
            continue

        if character == "(":
            depth += 1
            current.append(character)
            continue

        if character == ")":
            depth -= 1
            current.append(character)
            continue

        if character == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue

        current.append(character)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def parse_short_desc(source: str) -> str:
    match = re.search(r'getShortDesc\(\)\s*\{\s*return\s+"((?:\\.|[^"\\])*)";\s*\}', source, re.S)
    if not match:
        return ""
    return parse_java_string_literal(f'"{match.group(1)}"')


def parse_long_desc_lines(source: str) -> tuple[str, ...]:
    match = re.search(r'getLongDesc\(\)\s*\{\s*return\s+Arrays\.asList\((.*?)\);\s*\}', source, re.S)
    if not match:
        return tuple()
    return tuple(extract_string_literals(match.group(1)))


def parse_usage_lines(long_desc_lines: Iterable[str]) -> tuple[str, ...]:
    return tuple(line for line in long_desc_lines if line.lstrip().startswith(">"))


def parse_command_names_from_super(source: str) -> tuple[str, ...]:
    match = re.search(r"super\(\s*baritone\s*,\s*(.*?)\);", source, re.S)
    if not match:
        raise ValueError("Could not parse command names from super(...) call")
    names = tuple(extract_string_literals(match.group(1)))
    if not names:
        raise ValueError("No command names found in super(...) call")
    return names


def parse_default_command_classes(default_source: str) -> list[str]:
    classes: list[str] = []
    for line in default_source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        match = re.search(r"new\s+([A-Za-z0-9_]+Command)\(baritone\)", stripped)
        if match:
            classes.append(match.group(1))
    return classes


def parse_command_alias_entries(default_source: str) -> list[ParsedCommand]:
    parsed: list[ParsedCommand] = []

    for line in default_source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if "new CommandAlias(" not in stripped:
            continue

        match = re.search(r"new\s+CommandAlias\(baritone,\s*(.*)\)\s*,?$", stripped)
        if not match:
            continue

        parts = split_top_level_args(match.group(1))
        if len(parts) != 3:
            raise ValueError(f"Unexpected CommandAlias argument structure: {parts}")

        names_expression = parts[0]
        short_desc = parse_java_string_literal(parts[1])
        target = parse_java_string_literal(parts[2])

        if names_expression.startswith("Arrays.asList"):
            names = tuple(extract_string_literals(names_expression))
        else:
            names = tuple(extract_string_literals(names_expression))

        if not names:
            raise ValueError("CommandAlias did not define names")

        canonical = names[0]
        long_desc_lines = (f"This command is an alias for: {target}",)
        parsed.append(
            ParsedCommand(
                name=canonical,
                aliases=names[1:],
                short_desc=short_desc,
                long_desc_lines=long_desc_lines,
                usage_lines=tuple(),
                source_file="DefaultCommands.java (CommandAlias)",
                domain=DOMAIN_BY_COMMAND[canonical],
                target=target,
            )
        )

    return parsed


def parse_default_commands(default_source: str) -> list[ParsedCommand]:
    parsed: list[ParsedCommand] = []

    class_names = parse_default_command_classes(default_source)
    for class_name in class_names:
        source_url = f"{BARITONE_BASE_RAW_URL}/{class_name}.java"
        source = fetch_text(source_url)

        names = parse_command_names_from_super(source)
        canonical = names[0]
        if canonical == "schematica":
            continue

        if canonical not in DOMAIN_BY_COMMAND:
            raise ValueError(f"Missing domain mapping for command: {canonical}")

        long_desc_lines = parse_long_desc_lines(source)

        parsed.append(
            ParsedCommand(
                name=canonical,
                aliases=names[1:],
                short_desc=parse_short_desc(source),
                long_desc_lines=long_desc_lines,
                usage_lines=parse_usage_lines(long_desc_lines),
                source_file=f"{class_name}.java",
                domain=DOMAIN_BY_COMMAND[canonical],
                target=None,
            )
        )

    parsed.extend(parse_command_alias_entries(default_source))
    return parsed


def parse_execution_control_commands(execution_source: str) -> list[ParsedCommand]:
    parsed: list[ParsedCommand] = []
    pattern = re.compile(
        r"new\s+Command\(baritone,\s*(?P<names>.*?)\)\s*\{(?P<body>.*?)^\s*\};",
        re.S | re.M,
    )

    for match in pattern.finditer(execution_source):
        names = tuple(extract_string_literals(match.group("names")))
        if not names:
            continue

        canonical = names[0]
        if canonical not in DOMAIN_BY_COMMAND:
            raise ValueError(f"Missing domain mapping for command: {canonical}")

        body = match.group("body")
        long_desc_lines = parse_long_desc_lines(body)
        parsed.append(
            ParsedCommand(
                name=canonical,
                aliases=names[1:],
                short_desc=parse_short_desc(body),
                long_desc_lines=long_desc_lines,
                usage_lines=parse_usage_lines(long_desc_lines),
                source_file="ExecutionControlCommands.java",
                domain=DOMAIN_BY_COMMAND[canonical],
                target=None,
            )
        )

    return parsed


def python_name(name: str) -> str:
    if name in PYTHON_NAME_OVERRIDES:
        return PYTHON_NAME_OVERRIDES[name]
    safe = name.replace("-", "_")
    if safe.isidentifier():
        return safe
    raise ValueError(f"Cannot convert command name to valid Python identifier: {name}")


def build_alias_to_canonical(commands: Iterable[ParsedCommand]) -> dict[str, str]:
    alias_to_canonical: dict[str, str] = {}
    for command in commands:
        for alias in command.aliases:
            alias_to_canonical[alias] = command.name
    return dict(sorted(alias_to_canonical.items()))


def command_docstring(command: ParsedCommand) -> str:
    alias_text = ", ".join(command.aliases) if command.aliases else "none"
    lines = [
        command.short_desc or f"Baritone command: {command.name}",
        "",
        f"Canonical command: `{command.name}`",
        f"Aliases: {alias_text}",
    ]

    if command.usage_lines:
        lines.append("Usage:")
        for usage in command.usage_lines:
            lines.append(f"- `{usage}`")

    lines.append(f"Source: `{command.source_file}`")
    return "\n".join(lines)


def render_async_method(command: ParsedCommand) -> str:
    name = python_name(command.name)
    doc = command_docstring(command)

    if command.name == "cancel":
        return ""

    if command.name == "goto":
        return (
            f"    async def {name}(self, x: int, y: int, z: int, *extra_args: CommandArg) -> CommandDispatchResult:\n"
            f"        \"\"\"{doc}\"\"\"\n"
            f"        return await dispatch_async(self, {command.name!r}, x, y, z, *extra_args)\n\n"
            f"    async def goto_wait(self, x: int, y: int, z: int, *extra_args: CommandArg) -> dict[str, Any]:\n"
            "        \"\"\"Dispatch `goto` and wait for its terminal task event.\"\"\"\n"
            "        return await dispatch_and_wait_async(self, 'goto', x, y, z, *extra_args)\n"
        )

    if command.name in SPECIAL_CANONICAL_CALLS:
        target_method, target_args = SPECIAL_CANONICAL_CALLS[command.name]
        literal_args = ", ".join(repr(value) for value in target_args)
        call_prefix = f"{literal_args}, *args" if literal_args else "*args"
        return (
            f"    async def {name}(self, *args: CommandArg) -> CommandDispatchResult:\n"
            f"        \"\"\"{doc}\"\"\"\n"
            f"        return await self.{python_name(target_method)}({call_prefix})\n"
        )

    return (
        f"    async def {name}(self, *args: CommandArg) -> CommandDispatchResult:\n"
        f"        \"\"\"{doc}\"\"\"\n"
        f"        return await dispatch_async(self, {command.name!r}, *args)\n"
    )


def render_sync_method(command: ParsedCommand) -> str:
    name = python_name(command.name)
    doc = command_docstring(command)

    if command.name == "cancel":
        return ""

    if command.name == "goto":
        return (
            f"    def {name}(self, x: int, y: int, z: int, *extra_args: CommandArg) -> CommandDispatchResult:\n"
            f"        \"\"\"{doc}\"\"\"\n"
            f"        return dispatch_sync(self, {command.name!r}, x, y, z, *extra_args)\n\n"
            f"    def goto_wait(self, x: int, y: int, z: int, *extra_args: CommandArg) -> dict[str, Any]:\n"
            "        \"\"\"Dispatch `goto` and wait for its terminal task event.\"\"\"\n"
            "        return dispatch_and_wait_sync(self, 'goto', x, y, z, *extra_args)\n"
        )

    if command.name in SPECIAL_CANONICAL_CALLS:
        target_method, target_args = SPECIAL_CANONICAL_CALLS[command.name]
        literal_args = ", ".join(repr(value) for value in target_args)
        call_prefix = f"{literal_args}, *args" if literal_args else "*args"
        return (
            f"    def {name}(self, *args: CommandArg) -> CommandDispatchResult:\n"
            f"        \"\"\"{doc}\"\"\"\n"
            f"        return self.{python_name(target_method)}({call_prefix})\n"
        )

    return (
        f"    def {name}(self, *args: CommandArg) -> CommandDispatchResult:\n"
        f"        \"\"\"{doc}\"\"\"\n"
        f"        return dispatch_sync(self, {command.name!r}, *args)\n"
    )


def render_async_alias(alias: str, canonical: str) -> str:
    alias_method = python_name(alias)
    canonical_method = python_name(canonical)

    if canonical == "cancel":
        return (
            f"    async def {alias_method}(self, task_id: str | None = None) -> dict[str, Any]:\n"
            f"        \"\"\"Alias for `{canonical_method}`.\"\"\"\n"
            "        return await self.cancel(task_id=task_id)\n"
        )

    return (
        f"    async def {alias_method}(self, *args: CommandArg) -> CommandDispatchResult:\n"
        f"        \"\"\"Alias for `{canonical_method}`.\"\"\"\n"
        f"        return await self.{canonical_method}(*args)\n"
    )


def render_sync_alias(alias: str, canonical: str) -> str:
    alias_method = python_name(alias)
    canonical_method = python_name(canonical)

    if canonical == "cancel":
        return (
            f"    def {alias_method}(self, task_id: str | None = None) -> dict[str, Any]:\n"
            f"        \"\"\"Alias for `{canonical_method}`.\"\"\"\n"
            "        return self.cancel(task_id=task_id)\n"
        )

    return (
        f"    def {alias_method}(self, *args: CommandArg) -> CommandDispatchResult:\n"
        f"        \"\"\"Alias for `{canonical_method}`.\"\"\"\n"
        f"        return self.{canonical_method}(*args)\n"
    )


def generate_domain_module(commands: list[ParsedCommand], alias_map: dict[str, str], domain: str, *, async_mode: bool) -> str:
    selected_commands = sorted((command for command in commands if command.domain == domain), key=lambda item: item.name)
    selected_aliases = sorted((alias, canonical) for alias, canonical in alias_map.items() if DOMAIN_BY_COMMAND[canonical] == domain)

    class_prefix = "Async" if async_mode else "Sync"
    class_name = f"{class_prefix}{domain.capitalize()}Commands"

    needs_wait_helper = any(command.name == "goto" for command in selected_commands)

    if async_mode:
        core_import = "from ._core import dispatch_async\n"
        if needs_wait_helper:
            core_import = "from ._core import dispatch_and_wait_async, dispatch_async\n"

        header = (
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n"
            + core_import
            + "from ._types import CommandArg, CommandDispatchResult\n\n\n"
        )
        method_renderer = render_async_method
        alias_renderer = render_async_alias
    else:
        core_import = "from ._core import dispatch_sync\n"
        if needs_wait_helper:
            core_import = "from ._core import dispatch_and_wait_sync, dispatch_sync\n"

        header = (
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n"
            + core_import
            + "from ._types import CommandArg, CommandDispatchResult\n\n\n"
        )
        method_renderer = render_sync_method
        alias_renderer = render_sync_alias

    body = [f"class {class_name}:\n"]

    for command in selected_commands:
        rendered = method_renderer(command)
        if rendered:
            body.append(rendered + "\n")

    for alias, canonical in selected_aliases:
        body.append(alias_renderer(alias, canonical) + "\n")

    return header + "".join(body).rstrip() + "\n"


def generate_catalog_module(commands: list[ParsedCommand], alias_map: dict[str, str]) -> str:
    command_method_names = {command.name: python_name(command.name) for command in commands}
    alias_method_names = {alias: python_name(alias) for alias in alias_map}

    lines = [
        "from __future__ import annotations",
        "",
        "from ._types import CommandSpec",
        "",
        f"BARITONE_VERSION = {BARITONE_VERSION!r}",
        "",
        "COMMAND_SPECS: tuple[CommandSpec, ...] = (",
    ]

    for command in sorted(commands, key=lambda item: item.name):
        lines.extend(
            [
                "    CommandSpec(",
                f"        name={command.name!r},",
                f"        aliases={command.aliases!r},",
                f"        short_desc={command.short_desc!r},",
                f"        long_desc_lines={command.long_desc_lines!r},",
                f"        usage_lines={command.usage_lines!r},",
                f"        source_file={command.source_file!r},",
                f"        domain={command.domain!r},",
                f"        target={command.target!r},",
                "    ),",
            ]
        )

    lines.extend(
        [
            ")",
            "",
            "ALIAS_TO_CANONICAL: dict[str, str] = {",
        ]
    )
    for alias, canonical in sorted(alias_map.items()):
        lines.append(f"    {alias!r}: {canonical!r},")

    lines.extend(
        [
            "}",
            "",
            "COMMAND_NAME_SET: frozenset[str] = frozenset(spec.name for spec in COMMAND_SPECS)",
            "",
            "COMMAND_METHOD_NAMES: dict[str, str] = {",
        ]
    )
    for command_name, method_name in sorted(command_method_names.items()):
        lines.append(f"    {command_name!r}: {method_name!r},")

    lines.extend(
        [
            "}",
            "",
            "ALIAS_METHOD_NAMES: dict[str, str] = {",
        ]
    )
    for alias_name, method_name in sorted(alias_method_names.items()):
        lines.append(f"    {alias_name!r}: {method_name!r},")

    lines.extend(["}", ""])
    return "\n".join(lines)


def generate_markdown(commands: list[ParsedCommand], alias_map: dict[str, str]) -> str:
    command_by_name = {command.name: command for command in commands}

    lines = [
        "# Pyritone Baritone Command Reference",
        "",
        f"Generated from Baritone `{BARITONE_VERSION}` source files.",
        "",
        "## Canonical Commands",
        "",
    ]

    for command in sorted(commands, key=lambda item: item.name):
        method_name = python_name(command.name)
        aliases = ", ".join(command.aliases) if command.aliases else "none"
        target_note = f"Target: `{command.target}`" if command.target else None

        lines.extend(
            [
                f"### `{command.name}`",
                "",
                f"- Python method: `{method_name}`",
                f"- Aliases: {aliases}",
                f"- Domain: `{command.domain}`",
                f"- Source: `{command.source_file}`",
            ]
        )

        if target_note:
            lines.append(f"- {target_note}")

        lines.append(f"- Summary: {command.short_desc}")
        lines.append("")

        if command.usage_lines:
            lines.append("Usage:")
            for usage_line in command.usage_lines:
                lines.append(f"- `{usage_line}`")
            lines.append("")

        if command.long_desc_lines:
            lines.append("Notes:")
            for note_line in command.long_desc_lines:
                if note_line:
                    lines.append(f"- {note_line}")
            lines.append("")

    lines.extend(["## Alias Methods", ""])
    for alias, canonical in sorted(alias_map.items()):
        lines.append(f"- `{python_name(alias)}` -> `{python_name(canonical)}` (`{alias}` -> `{canonical}`)")

    lines.append("")
    return "\n".join(lines)


def generate_commands_package_init() -> str:
    return "\n".join(
        [
            "from ._catalog import ALIAS_METHOD_NAMES, ALIAS_TO_CANONICAL, BARITONE_VERSION, COMMAND_METHOD_NAMES, COMMAND_NAME_SET, COMMAND_SPECS",
            "from ._types import CommandArg, CommandDispatchResult, CommandSpec",
            "",
            "__all__ = [",
            "    \"ALIAS_METHOD_NAMES\",",
            "    \"ALIAS_TO_CANONICAL\",",
            "    \"BARITONE_VERSION\",",
            "    \"COMMAND_METHOD_NAMES\",",
            "    \"COMMAND_NAME_SET\",",
            "    \"COMMAND_SPECS\",",
            "    \"CommandArg\",",
            "    \"CommandDispatchResult\",",
            "    \"CommandSpec\",",
            "]",
            "",
        ]
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Pyritone command wrappers from Baritone source")
    parser.add_argument("--check", action="store_true", help="Validate generated outputs without writing")
    args = parser.parse_args()

    default_source = fetch_text(DEFAULT_COMMANDS_URL)
    execution_source = fetch_text(EXECUTION_CONTROL_URL)

    commands = parse_default_commands(default_source)
    commands.extend(parse_execution_control_commands(execution_source))

    by_name: dict[str, ParsedCommand] = {}
    for command in commands:
        if command.name in by_name:
            raise ValueError(f"Duplicate command name parsed: {command.name}")
        by_name[command.name] = command

    commands = sorted(by_name.values(), key=lambda item: item.name)
    alias_map = build_alias_to_canonical(commands)

    if len(commands) != 42:
        raise ValueError(f"Expected 42 canonical commands, found {len(commands)}")
    if len(alias_map) != 21:
        raise ValueError(f"Expected 21 aliases, found {len(alias_map)}")
    if "schematica" in by_name:
        raise ValueError("schematica should not be included in generated commands")

    outputs = {
        COMMANDS_DIR / "_catalog.py": generate_catalog_module(commands, alias_map),
        COMMANDS_DIR / "__init__.py": generate_commands_package_init(),
        COMMANDS_DIR / "async_navigation.py": generate_domain_module(commands, alias_map, "navigation", async_mode=True),
        COMMANDS_DIR / "async_world.py": generate_domain_module(commands, alias_map, "world", async_mode=True),
        COMMANDS_DIR / "async_build.py": generate_domain_module(commands, alias_map, "build", async_mode=True),
        COMMANDS_DIR / "async_control.py": generate_domain_module(commands, alias_map, "control", async_mode=True),
        COMMANDS_DIR / "async_info.py": generate_domain_module(commands, alias_map, "info", async_mode=True),
        COMMANDS_DIR / "async_waypoints.py": generate_domain_module(commands, alias_map, "waypoints", async_mode=True),
        COMMANDS_DIR / "sync_navigation.py": generate_domain_module(commands, alias_map, "navigation", async_mode=False),
        COMMANDS_DIR / "sync_world.py": generate_domain_module(commands, alias_map, "world", async_mode=False),
        COMMANDS_DIR / "sync_build.py": generate_domain_module(commands, alias_map, "build", async_mode=False),
        COMMANDS_DIR / "sync_control.py": generate_domain_module(commands, alias_map, "control", async_mode=False),
        COMMANDS_DIR / "sync_info.py": generate_domain_module(commands, alias_map, "info", async_mode=False),
        COMMANDS_DIR / "sync_waypoints.py": generate_domain_module(commands, alias_map, "waypoints", async_mode=False),
        DOCS_PATH: generate_markdown(commands, alias_map),
    }

    if args.check:
        for path, content in outputs.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Out of date: {path}")
        return

    for path, content in outputs.items():
        write_text(path, content)

    print(f"Generated {len(outputs)} files")


if __name__ == "__main__":
    main()

