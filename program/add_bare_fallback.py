#!/usr/bin/env python3
"""
Add bare fallback entries to characters_categories/bare/ for characters that
only appear in clothed/. Strips clothing tags from the most detailed clothed entry.

Usage:
    python add_bare_fallback.py              # report missing
    python add_bare_fallback.py --apply      # append bare entries
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_clothing import is_clothing_tag

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLOTHED_DIR = os.path.join(BASE, 'characters_categories', 'clothed')
BARE_DIR = os.path.join(BASE, 'characters_categories', 'bare')

SKIP = {'trance terra branford'}  # deliberately bare-only, handle separately


def base_name(name):
    return __import__('re').split(r'\\?\(', name)[0].strip()


def strip_clothing_tags(line):
    """Remove clothing tags from a CSV line, preserving name, series, and non-clothing tags."""
    parts = [p.strip() for p in line.split(',')]
    if len(parts) < 3:
        return line  # can't strip
    name, series = parts[0], parts[1]
    rest = parts[2:]
    kept = [t for t in rest if not is_clothing_tag(t)]
    return ', '.join([name, series] + kept)


def find_clothed_only():
    """Return [(fname, base_name, best_clothed_line, stripped_line), ...]."""
    missing = []

    for fname in sorted(os.listdir(CLOTHED_DIR)):
        if not fname.endswith('.txt'):
            continue

        # Get best entry per character from clothed/
        c_best = {}
        with open(os.path.join(CLOTHED_DIR, fname), 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                bn = base_name(line.split(',')[0].strip())
                if bn not in c_best or len(line.split(',')) > len(c_best[bn].split(',')):
                    c_best[bn] = line

        # Get characters in bare/
        b_names = set()
        b_path = os.path.join(BARE_DIR, fname)
        if os.path.exists(b_path):
            with open(b_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    b_names.add(base_name(line.split(',')[0].strip()))

        # Find clothed-only
        for bn, best_line in sorted(c_best.items()):
            if bn in b_names or bn.lower() in SKIP:
                continue
            stripped = strip_clothing_tags(best_line)
            missing.append((fname, bn, best_line, stripped))

    return missing


def report():
    missing = find_clothed_only()
    if not missing:
        print('All characters have bare entries. ✅')
        return
    print(f'{len(missing)} characters need bare entries:\n')
    for fname, bn, orig, stripped in missing:
        tags_before = len(orig.split(','))
        tags_after = len(stripped.split(','))
        removed = tags_before - tags_after
        preview = stripped[:120] + ('...' if len(stripped) > 120 else '')
        print(f'  [{fname}] {bn}  (-{removed} tags)')
        print(f'    {preview}')
    print()


def apply():
    missing = find_clothed_only()
    if not missing:
        print('All characters have bare entries. ✅')
        return

    by_file = {}
    for fname, bn, orig, stripped in missing:
        by_file.setdefault(fname, []).append((bn, stripped))

    total = 0
    for fname, items in sorted(by_file.items()):
        fpath = os.path.join(BARE_DIR, fname)
        with open(fpath, 'a', encoding='utf-8') as f:
            for bn, stripped_line in items:
                f.write(stripped_line + '\n')
                total += 1
        print(f'{fname}: +{len(items)} entries')

    print(f'\nTotal: {total} bare fallback entries added.')


if __name__ == '__main__':
    if '--apply' in sys.argv:
        apply()
    else:
        report()
