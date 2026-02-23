from __future__ import annotations

import re
from pathlib import Path

from pyritone.commands import ALIAS_TO_CANONICAL, COMMAND_SPECS


DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"
COMMAND_DOCS_DIR = DOCS_DIR / "commands"
DOMAIN_FILES = [
    COMMAND_DOCS_DIR / "navigation.md",
    COMMAND_DOCS_DIR / "world.md",
    COMMAND_DOCS_DIR / "build.md",
    COMMAND_DOCS_DIR / "control.md",
    COMMAND_DOCS_DIR / "info.md",
    COMMAND_DOCS_DIR / "waypoints.md",
]
ALIAS_DOC = COMMAND_DOCS_DIR / "aliases.md"

COMMAND_HEADING_PATTERN = re.compile(r"^## `([a-z0-9]+)`$", re.MULTILINE)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_command_sections(text: str) -> dict[str, str]:
    matches = list(COMMAND_HEADING_PATTERN.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[name] = text[start:end]
    return sections


def _extract_python_example(section_text: str, heading: str) -> str:
    pattern = re.compile(rf"{re.escape(heading)}\s+```python\n(.*?)\n```", re.DOTALL)
    match = pattern.search(section_text)
    assert match is not None, f"Missing python code block after {heading}"
    return match.group(1)


def test_every_canonical_command_appears_in_one_domain_doc():
    expected = {spec.name for spec in COMMAND_SPECS}
    found: dict[str, int] = {}

    for path in DOMAIN_FILES:
        text = _read(path)
        for command_name in COMMAND_HEADING_PATTERN.findall(text):
            found[command_name] = found.get(command_name, 0) + 1

    assert set(found) == expected
    assert all(count == 1 for count in found.values())


def test_every_command_section_has_async_example():
    for path in DOMAIN_FILES:
        sections = _extract_command_sections(_read(path))
        assert sections, f"No command sections found in {path}"
        for command_name, section_text in sections.items():
            async_example = _extract_python_example(section_text, "### Example")
            method_name = command_name.replace("-", "_")

            assert f"await client.{method_name}(" in async_example, f"Async example does not await client.{method_name}"
            assert "### Sync example" not in section_text
            assert "### Async example" not in section_text


def test_alias_doc_contains_full_alias_mapping():
    text = _read(ALIAS_DOC)
    canonical_to_domain = {spec.name: spec.domain for spec in COMMAND_SPECS}
    alias_rows = [line for line in text.splitlines() if line.startswith("| `")]
    assert len(alias_rows) == len(ALIAS_TO_CANONICAL)

    for alias, canonical in sorted(ALIAS_TO_CANONICAL.items()):
        alias_method = "qmark" if alias == "?" else alias.replace("-", "_")
        canonical_method = canonical.replace("-", "_")
        domain = canonical_to_domain[canonical]
        line = f"| `{alias}` | `{canonical}` | `{alias_method}` | `{canonical_method}` | `{domain}` |"
        assert line in text
