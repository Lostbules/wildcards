#!/usr/bin/env python3
"""
Generate series_index.txt from the 4 derived series files under characters_categories/.

Groups character entries by series (field 2), sorted alphabetically within each
group. Each entry is annotated with its source file and line number.

Usage:
    python series_index.py              # generate series_index.txt
"""

import os
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT_DIR = os.path.join(BASE, 'characters_categories')
INDEX_FILE = os.path.join(BASE, 'series_index.txt')

SERIES_FILES = ['demon_slayer.txt', 'honkai_verse.txt', 'remaining_characters.txt', 'trails_series.txt']


def load_entries():
    """Return list of (name, series, source_file, line_number)."""
    entries = []
    for fname in SERIES_FILES:
        fpath = os.path.join(CAT_DIR, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',', 2)
                name = parts[0].strip() if len(parts) >= 1 else line
                series = parts[1].strip() if len(parts) >= 2 else '(no tag)'
                if not series:
                    series = '(no tag)'
                entries.append((name, series, fname, i))
    return entries


def main():
    entries = load_entries()

    # Group by series, preserving insertion order within each group
    groups = defaultdict(list)
    for name, series, fname, lineno in entries:
        groups[series].append((name, fname, lineno))

    with open(INDEX_FILE, 'w', encoding='utf-8') as out:
        for series in sorted(groups.keys(), key=str.lower):
            items = groups[series]
            for name, fname, lineno in items:
                out.write(f'  {fname}:L{lineno}  {name}\n')
            out.write(f'## {series}  [{len(items)}]\n\n')

    print(f'{INDEX_FILE}: {len(entries)} entries across {len(groups)} series', file=sys.stderr)


if __name__ == '__main__':
    main()
