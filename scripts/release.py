#!/usr/bin/env python3
"""Release helper for WorkflowBench.

Usage examples:
  python scripts/release.py patch --dry-run
  python scripts/release.py 0.1.1 --execute --github-release
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
INIT_FILE = ROOT / "workflowbench" / "__init__.py"

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=check)


def current_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"\s*$', text, flags=re.M)
    if not m:
        raise RuntimeError("Could not locate [project].version in pyproject.toml")
    return m.group(1)


def bump(version: str, level: str) -> str:
    m = SEMVER_RE.match(version)
    if not m:
        raise ValueError(f"Invalid semver: {version}")
    major, minor, patch = map(int, m.groups())
    if level == "patch":
        patch += 1
    elif level == "minor":
        minor += 1
        patch = 0
    elif level == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Unknown bump level: {level}")
    return f"{major}.{minor}.{patch}"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected snippet not found in {path}")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def ensure_clean_worktree() -> None:
    result = run(["git", "status", "--porcelain"], check=True)
    if result.stdout.strip():
        raise RuntimeError(
            "Git worktree is not clean. Commit or stash changes before running a release."
        )


def ensure_tag_not_exists(tag: str) -> None:
    result = run(["git", "tag", "-l", tag], check=True)
    if result.stdout.strip() == tag:
        raise RuntimeError(f"Tag already exists: {tag}")


def verify_gh_cli() -> None:
    try:
        run(["gh", "--version"], check=True)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("gh CLI is required for --github-release") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Bump version and create release artifacts")
    parser.add_argument(
        "target",
        help="Target version (e.g. 0.1.1) or bump level: patch/minor/major",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply changes and run git commands. Without this flag, only prints the plan.",
    )
    parser.add_argument(
        "--github-release",
        action="store_true",
        help="Create GitHub release with gh CLI after pushing tag.",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="Git remote to push to (default: origin)",
    )
    args = parser.parse_args()

    cur = current_version()
    if args.target in {"patch", "minor", "major"}:
        nxt = bump(cur, args.target)
    else:
        if not SEMVER_RE.match(args.target):
            parser.error("target must be semver (X.Y.Z) or one of: patch/minor/major")
        nxt = args.target

    if nxt == cur:
        parser.error(f"New version must differ from current version ({cur})")

    tag = f"v{nxt}"
    commit_msg = f"chore(release): v{nxt}"

    print(f"Current version: {cur}")
    print(f"Next version:    {nxt}")
    print(f"Tag:             {tag}")

    if not args.execute:
        print("\nDry run only. Use --execute to apply these steps:")
        print("1) Update pyproject.toml and workflowbench/__init__.py")
        print(f"2) git add {PYPROJECT.relative_to(ROOT)} {INIT_FILE.relative_to(ROOT)}")
        print(f"3) git commit -m \"{commit_msg}\"")
        print(f"4) git tag {tag}")
        print(f"5) git push {args.remote} main")
        print(f"6) git push {args.remote} {tag}")
        if args.github_release:
            print(f"7) gh release create {tag} --generate-notes --title {tag}")
        return 0

    ensure_clean_worktree()
    ensure_tag_not_exists(tag)
    if args.github_release:
        verify_gh_cli()

    replace_once(PYPROJECT, f'version = "{cur}"', f'version = "{nxt}"')
    replace_once(INIT_FILE, f'__version__ = "{cur}"', f'__version__ = "{nxt}"')

    run(["git", "add", str(PYPROJECT), str(INIT_FILE)], check=True)
    run(["git", "commit", "-m", commit_msg], check=True)
    run(["git", "tag", tag], check=True)
    run(["git", "push", args.remote, "main"], check=True)
    run(["git", "push", args.remote, tag], check=True)

    if args.github_release:
        run(["gh", "release", "create", tag, "--generate-notes", "--title", tag], check=True)

    print("Release steps completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
