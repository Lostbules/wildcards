#!/usr/bin/env python3
"""
Delete a character from all wildcard files (subfolder + main).

Usage:
    python delete_character.py <pattern>          # find & confirm
    python delete_character.py --yes <pattern>    # skip confirmation

The pattern matches case-insensitively against the character name (first
comma-separated field).  It can be a substring — e.g. "houjuu" matches
"houjuu nue".  Only exact full-name matches are deleted though (the
pattern is validated by showing what will be deleted).

Files covered:
  - characters_curated.txt
  - characters_curated_clothed.txt / characters_curated_bare.txt
  - characters_categories/*.txt (all subdirectories)
  - series_index.txt
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = [
    'characters_curated.txt',
    'characters_curated_clothed.txt',
    'characters_curated_bare.txt',
    'series_index.txt',
]

CAT_DIRS = [
    'characters_categories',
    'characters_categories/bare',
    'characters_categories/clothed',
]


def find_hits(pattern: str) -> dict[str, list[tuple[int, str]]]:
    """Return {filepath: [(line_number, line_text), ...]} for matching lines."""
    hits: dict[str, list[tuple[int, str]]] = {}
    pat = pattern.lower()

    # Main files
    for fname in FILES:
        fpath = os.path.join(BASE, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                name = line.split(',')[0].strip().lower() if ',' in line else ''
                if pat in name:
                    hits.setdefault(fpath, []).append((i, line.rstrip('\n').rstrip('\r')))

    # Category directories
    for d in CAT_DIRS:
        dpath = os.path.join(BASE, d)
        if not os.path.isdir(dpath):
            continue
        for fname in sorted(os.listdir(dpath)):
            if not fname.endswith('.txt'):
                continue
            fpath = os.path.join(dpath, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    name = line.split(',')[0].strip().lower() if ',' in line else ''
                    if pat in name:
                        hits.setdefault(fpath, []).append((i, line.rstrip('\n').rstrip('\r')))

    return hits


def delete_hits(hits: dict[str, list[tuple[int, str]]]) -> int:
    """Delete matching lines (high-to-low per file). Returns total deleted."""
    total = 0
    for fpath, entries in sorted(hits.items()):
        line_nums = sorted([ln for ln, _ in entries], reverse=True)
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for ln in line_nums:
            if 1 <= ln <= len(lines):
                del lines[ln - 1]
                total += 1
        with open(fpath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    return total


def main():
    args = sys.argv[1:]
    auto_yes = False
    if args and args[0] == '--yes':
        auto_yes = True
        args = args[1:]

    if not args:
        print(__doc__)
        sys.exit(1)

    pattern = ' '.join(args)

    hits = find_hits(pattern)
    if not hits:
        print(f'No matches for "{pattern}"')
        sys.exit(0)

    total = sum(len(v) for v in hits.values())
    print(f'Found {total} entries matching "{pattern}":\n')
    for fpath, entries in sorted(hits.items()):
        rel = os.path.relpath(fpath, BASE)
        for ln, text in sorted(entries):
            display = text[:100] + ('...' if len(text) > 100 else '')
            print(f'  {rel}:{ln}  {display}')

    if not auto_yes:
        print(f'\nDelete {total} entries? [y/N] ', end='')
        resp = input().strip().lower()
        if resp not in ('y', 'yes'):
            print('Aborted.')
            sys.exit(0)

    deleted = delete_hits(hits)
    print(f'Deleted {deleted} entries.')

    # Verify
    remaining = sum(len(v) for v in find_hits(pattern).values())
    if remaining > 0:
        print(f'WARNING: {remaining} entries still remain!')
    else:
        print('Verified: 0 remaining.')


if __name__ == '__main__':
    main()
