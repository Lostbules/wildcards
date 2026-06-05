#!/usr/bin/env python3
"""
Rebuild derived character files from the authoritative source directories.

Authoritative sources:
    characters_categories/clothed/*.txt
    characters_categories/bare/*.txt

Derived files (rebuilt by this script):
    characters_categories/*.txt           — per-series deduplicated union
    characters_curated.txt                — all-series deduplicated union
    characters_curated_clothed.txt        — all clothed entries deduplicated
    characters_curated_bare.txt           — all bare entries deduplicated

Usage:
    python rebuild_characters.py              # dry-run: report what would change
    python rebuild_characters.py --apply      # rebuild all derived files
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT_DIR = os.path.join(BASE, 'characters_categories')
CLOTHED_DIR = os.path.join(CAT_DIR, 'clothed')
BARE_DIR = os.path.join(CAT_DIR, 'bare')

SERIES = ['demon_slayer', 'honkai_verse', 'remaining_characters', 'trails_series']


def load_lines(path):
    """Return sorted list of non-empty, stripped lines from a file."""
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return sorted({l.strip() for l in f if l.strip()})


def write_lines(path, lines):
    """Write sorted lines to file with trailing newline."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def check_series_files():
    """Verify all 4 series files match clothed/ + bare/ unions. Return True if all OK."""
    all_ok = True
    for series in SERIES:
        union = set()
        for sub_dir in [CLOTHED_DIR, BARE_DIR]:
            fp = os.path.join(sub_dir, f'{series}.txt')
            if os.path.exists(fp):
                with open(fp, encoding='utf-8') as f:
                    for l in f:
                        l = l.strip()
                        if l:
                            union.add(l)
        src = set(load_lines(os.path.join(CAT_DIR, f'{series}.txt')))
        diff = union ^ src
        if diff:
            all_ok = False
            print(f'  ✗ {series}: {len(diff)} differences (clothed+bare vs source)')
        else:
            print(f'  ✓ {series}: {len(union)} entries')
    return all_ok


def rebuild_derived(apply=False):
    """Rebuild all derived files from authoritative sources."""
    changes = []

    # ── 1. Series files from clothed/ + bare/ ──
    for series in SERIES:
        union = set()
        for sub_dir in [CLOTHED_DIR, BARE_DIR]:
            fp = os.path.join(sub_dir, f'{series}.txt')
            if os.path.exists(fp):
                with open(fp, encoding='utf-8') as f:
                    for l in f:
                        l = l.strip()
                        if l:
                            union.add(l)

        src_path = os.path.join(CAT_DIR, f'{series}.txt')
        current = set(load_lines(src_path))
        if union != current:
            changes.append(('series', series, len(current), len(union)))
            if apply:
                write_lines(src_path, sorted(union))

    # ── 2. characters_curated.txt = all series combined ──
    all_series = set()
    for series in SERIES:
        for sub_dir in [CLOTHED_DIR, BARE_DIR]:
            fp = os.path.join(sub_dir, f'{series}.txt')
            if os.path.exists(fp):
                with open(fp, encoding='utf-8') as f:
                    for l in f:
                        l = l.strip()
                        if l:
                            all_series.add(l)

    curated_path = os.path.join(BASE, 'characters_curated.txt')
    current_curated = set(load_lines(curated_path))
    if all_series != current_curated:
        changes.append(('curated', 'characters_curated.txt', len(current_curated), len(all_series)))
        if apply:
            write_lines(curated_path, sorted(all_series))

    # ── 3. characters_curated_clothed.txt = all clothed/ combined ──
    all_clothed = set()
    for series in SERIES:
        fp = os.path.join(CLOTHED_DIR, f'{series}.txt')
        if os.path.exists(fp):
            with open(fp, encoding='utf-8') as f:
                for l in f:
                    l = l.strip()
                    if l:
                        all_clothed.add(l)

    cc_path = os.path.join(BASE, 'characters_curated_clothed.txt')
    current_cc = set(load_lines(cc_path))
    if all_clothed != current_cc:
        changes.append(('clothed', 'characters_curated_clothed.txt', len(current_cc), len(all_clothed)))
        if apply:
            write_lines(cc_path, sorted(all_clothed))

    # ── 4. characters_curated_bare.txt = all bare/ combined ──
    all_bare = set()
    for series in SERIES:
        fp = os.path.join(BARE_DIR, f'{series}.txt')
        if os.path.exists(fp):
            with open(fp, encoding='utf-8') as f:
                for l in f:
                    l = l.strip()
                    if l:
                        all_bare.add(l)

    cb_path = os.path.join(BASE, 'characters_curated_bare.txt')
    current_cb = set(load_lines(cb_path))
    if all_bare != current_cb:
        changes.append(('bare', 'characters_curated_bare.txt', len(current_cb), len(all_bare)))
        if apply:
            write_lines(cb_path, sorted(all_bare))

    return changes


def main():
    apply = '--apply' in sys.argv

    print('=== Series files vs clothed/ + bare/ ===')
    series_ok = check_series_files()
    print()

    print('=== Derived files ===')
    changes = rebuild_derived(apply=apply)

    if not changes:
        print('All derived files are up to date. ✓')
        return

    for kind, name, old, new in changes:
        delta = new - old
        arrow = '→' if apply else '→ (dry-run)'
        print(f'  {kind}: {name}  {old} {arrow} {new}  ({"+" if delta > 0 else ""}{delta})')

    if not apply:
        print(f'\n{len(changes)} file(s) would be updated. Run with --apply to rebuild.')
    else:
        print(f'\n{len(changes)} file(s) rebuilt. ✓')
        print()
        print('=== Post-rebuild verification ===')
        check_series_files()


if __name__ == '__main__':
    main()
