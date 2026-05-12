#!/usr/bin/env python3
"""Bump plugin version across the three pinned files, commit, tag, push.

The canonical version lives in `.claude-plugin/plugin.json`. Claude Code
resolves a plugin's version from `plugin.json` first, so that's the cache
key users update against. We keep `marketplace.json` and `pyproject.toml`
in lockstep so nothing looks stale to a reader.

Usage:
    release.py <patch|minor|major> --issue N
    release.py <patch|minor|major> --issue N --dry-run

The commit message is `release: vX.Y.Z` with a `closes #N` trailer so the
repo's commit-msg hook accepts it. Pushes both the branch and the new tag.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import tomllib

REPO = Path(__file__).resolve().parent.parent
PLUGIN_JSON = REPO / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO / ".claude-plugin" / "marketplace.json"
PYPROJECT = REPO / "pyproject.toml"

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def read_plugin_version() -> str:
    data = json.loads(PLUGIN_JSON.read_text())
    return str(data["version"])


def bump(current: str, kind: str) -> str:
    m = SEMVER_RE.match(current)
    if not m:
        sys.exit(f"plugin.json version {current!r} is not MAJOR.MINOR.PATCH")
    major, minor, patch = (int(x) for x in m.groups())
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    if kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    sys.exit(f"unknown bump kind: {kind!r}")


def write_json_version(path: Path, new: str, key_path: tuple[str, ...]) -> None:
    data = json.loads(path.read_text())
    cursor: object = data
    for key in key_path[:-1]:
        cursor = cursor[key]  # type: ignore[index]
    cursor[key_path[-1]] = new  # type: ignore[index]
    path.write_text(json.dumps(data, indent=2) + "\n")


def write_marketplace_version(new: str) -> None:
    data = json.loads(MARKETPLACE_JSON.read_text())
    for entry in data["plugins"]:
        if entry.get("name") == "gauntlet":
            entry["version"] = new
            break
    else:
        sys.exit("marketplace.json has no gauntlet plugin entry")
    MARKETPLACE_JSON.write_text(json.dumps(data, indent=2) + "\n")


def write_pyproject_version(new: str) -> None:
    text = PYPROJECT.read_text()
    new_text, count = re.subn(
        r'^version = "[^"]+"',
        f'version = "{new}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        sys.exit('could not find a single `version = "..."` line in pyproject.toml')
    PYPROJECT.write_text(new_text)


def read_pyproject_version() -> str:
    return str(tomllib.loads(PYPROJECT.read_text())["project"]["version"])


def read_marketplace_version() -> str:
    data = json.loads(MARKETPLACE_JSON.read_text())
    for entry in data["plugins"]:
        if entry.get("name") == "gauntlet":
            return str(entry["version"])
    sys.exit("marketplace.json has no gauntlet plugin entry")


def assert_versions_aligned(expected: str) -> None:
    mismatches = []
    for label, actual in (
        ("plugin.json", read_plugin_version()),
        ("marketplace.json", read_marketplace_version()),
        ("pyproject.toml", read_pyproject_version()),
    ):
        if actual != expected:
            mismatches.append(f"  {label}: {actual} (expected {expected})")
    if mismatches:
        sys.exit("version drift after bump:\n" + "\n".join(mismatches))


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=REPO)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("patch", "minor", "major"))
    parser.add_argument("--issue", type=int, required=True, help="release-tracking issue N")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-push", action="store_true")
    args = parser.parse_args()

    current = read_plugin_version()
    new = bump(current, args.kind)
    print(f"bumping {current} -> {new}")

    if args.dry_run:
        return 0

    write_json_version(PLUGIN_JSON, new, ("version",))
    write_marketplace_version(new)
    write_pyproject_version(new)
    assert_versions_aligned(new)

    tag = f"v{new}"
    msg = f"release: {tag}\n\ncloses #{args.issue}\n"

    run(["git", "add", str(PLUGIN_JSON), str(MARKETPLACE_JSON), str(PYPROJECT)])
    run(["git", "commit", "-m", msg])
    run(["git", "tag", tag])
    if not args.no_push:
        run(["git", "push"])
        run(["git", "push", "origin", tag])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
