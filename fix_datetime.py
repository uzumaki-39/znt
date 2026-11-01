#!/usr/bin/env python3
"""
Kill the datetime.datetime('now') plague.
Byte-precise. Handles ASCII and typographic quotes.
"""
import re
import sys
from pathlib import Path

# Skip venv, __pycache__, .git — only touch YOUR code
SKIP_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules", "backups"}

# Patterns in order of specificity (longest first to avoid overlap)
PATTERNS = [
    # Broken literal 'now' argument
    (re.compile(r"datetime\.datetime\(\s*['\u2018\u2019\u02bc]\s*now\s*['\u2018\u2019\u02bc]\s*\)"), "datetime.now()"),
    # Explicit .now() with empty parens
    (re.compile(r"datetime\.datetime\.now\(\s*\)"), "datetime.now()"),
    # .now() with args — datetime.datetime.now(tz) → datetime.now(tz)
    (re.compile(r"datetime\.datetime\.now\("), "datetime.now("),
    # fromtimestamp
    (re.compile(r"datetime\.datetime\.fromtimestamp\("), "datetime.fromtimestamp("),
    # utcnow
    (re.compile(r"datetime\.datetime\.utcnow\(\s*\)"), "datetime.utcnow()"),
    # strptime
    (re.compile(r"datetime\.datetime\.strptime\("), "datetime.strptime("),
    # strftime on datetime.datetime.X — rare, but catch it
    (re.compile(r"datetime\.datetime\.strftime\("), "datetime.strftime("),
    # fromisoformat
    (re.compile(r"datetime\.datetime\.fromisoformat\("), "datetime.fromisoformat("),
]

def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & SKIP_DIRS)

def fix_file(path: Path, dry_run: bool = False) -> int:
    try:
        src = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"  SKIP {path}: {e}")
        return 0

    original = src
    changes = 0
    for pattern, replacement in PATTERNS:
        src, n = pattern.subn(replacement, src)
        changes += n

    if changes == 0:
        return 0

    if dry_run:
        print(f"  WOULD FIX {path}: {changes} change(s)")
        return changes

    path.write_text(src, encoding="utf-8")
    print(f"  FIXED {path}: {changes} change(s)")
    return changes

def main():
    root = Path.cwd()
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be modified\n")

    total = 0
    for path in sorted(root.rglob("*.py")):
        if should_skip(path):
            continue
        total += fix_file(path, dry_run=dry_run)

    print(f"\nTotal: {total} change(s)" + (" (dry run)" if dry_run else ""))

if __name__ == "__main__":
    main()