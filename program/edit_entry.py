#!/usr/bin/env python3
"""
Find and replace entries in NSFW pose wildcard files.

Usage:
    python edit_entry.py --find <search> --replace <new_text>  # replace in subfolders
    python edit_entry.py --find <search> --delete              # delete from subfolders
    python edit_entry.py --find <search>                       # just show matches
    python edit_entry.py --find <search> --sync                # also rebuild main files

The script works on NSFW_sex_categories/*.txt (subfolder files) and will
automatically find all occurrences across category files.

To also rebuild XL-pose_NSFW_sex.txt and XL-pose_merged.txt, add --sync.

Examples:
    python edit_entry.py --find "bent over counter.*domestic" --replace "bent over counter, ass, footjob, barefoot"
    python edit_entry.py --find "sound effects" --delete --sync
    python edit_entry.py --find "netorare"    # just show matching lines
"""

import os
import sys
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT_DIR = os.path.join(BASE, 'NSFW_sex_categories')

MAIN_FILES = [
    os.path.join(BASE, 'XL-pose_NSFW_sex.txt'),
    os.path.join(BASE, 'XL-pose_merged.txt'),
]
SFW_FILE = os.path.join(BASE, 'XL-pose_SFW_clean.txt')
SOLO_NUDE_FILE = os.path.join(BASE, 'XL-pose_NSFW_solo-nude.txt')


def find_matches(pattern: str, directory: str) -> dict[str, list[tuple[int, str]]]:
    """Return {filepath: [(line_number, full_line), ...]} for lines matching pattern."""
    hits: dict[str, list[tuple[int, str]]] = {}
    pat = re.compile(pattern, re.IGNORECASE)
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(directory, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if pat.search(line):
                    hits.setdefault(fpath, []).append((i, line.rstrip('\n').rstrip('\r')))
    return hits


def find_matches_main(pattern: str) -> dict[str, list[tuple[int, str]]]:
    """Search in main NSFW file only."""
    hits: dict[str, list[tuple[int, str]]] = {}
    pat = re.compile(pattern, re.IGNORECASE)
    main = os.path.join(BASE, 'XL-pose_NSFW_sex.txt')
    if os.path.exists(main):
        with open(main, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if pat.search(line):
                    hits.setdefault(main, []).append((i, line.rstrip('\n').rstrip('\r')))
    return hits


def show_hits(hits: dict[str, list[tuple[int, str]]]):
    total = sum(len(v) for v in hits.values())
    print(f'Found {total} match(es):\n')
    for fpath, entries in sorted(hits.items()):
        rel = os.path.relpath(fpath, BASE)
        for ln, text in sorted(entries):
            display = text[:120] + ('...' if len(text) > 120 else '')
            print(f'  {rel}:{ln}  {display}')


def replace_in_files(hits: dict[str, list[tuple[int, str]]],
                     old_pattern: str, new_text: str) -> int:
    """Replace all matches. If new_text is None, delete instead."""
    pat = re.compile(old_pattern, re.IGNORECASE)
    total = 0
    for fpath, entries in sorted(hits.items()):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = pat.sub(new_text if new_text is not None else '', content)
        # Clean up blank lines from deletion
        if new_text is None:
            new_content = re.sub(r'\n\s*\n', '\n', new_content)
            new_content = re.sub(r'^\n+', '', new_content)
        if new_content != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            changed = len(entries)
            total += changed
    return total


def rebuild_main_files():
    """Rebuild XL-pose_NSFW_sex.txt and XL-pose_merged.txt from subfolder files.
    Equivalent to: cat NSFW_sex_categories/*.txt | sort -u > XL-pose_NSFW_sex.txt (CLAUDE.md §6)."""
    main_file = os.path.join(BASE, 'XL-pose_NSFW_sex.txt')
    merged_file = os.path.join(BASE, 'XL-pose_merged.txt')
    # Collect all lines from subfolder files
    lines = []
    for fname in sorted(os.listdir(CAT_DIR)):
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(CAT_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(line)
    # sort -u: alphabetically sort and deduplicate
    unique = sorted(set(lines))
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(unique) + '\n')
    # Rebuild merged
    merged = []
    for src in [SFW_FILE, SOLO_NUDE_FILE, main_file]:
        if os.path.exists(src):
            with open(src, 'r', encoding='utf-8') as f:
                merged.extend(l.strip() for l in f if l.strip())
    with open(merged_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merged) + '\n')
    sfw = sum(1 for _ in open(SFW_FILE)) if os.path.exists(SFW_FILE) else 0
    solo = sum(1 for _ in open(SOLO_NUDE_FILE)) if os.path.exists(SOLO_NUDE_FILE) else 0
    sex = len(unique)
    merged_count = len(merged)
    print(f'Synced: {sfw}+{solo}+{sex}={merged_count}')


def main():
    args = sys.argv[1:]
    if not args or '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)

    find_pattern = None
    replace_text = None
    do_delete = False
    do_sync = False

    i = 0
    while i < len(args):
        if args[i] == '--find' and i + 1 < len(args):
            find_pattern = args[i + 1]
            i += 2
        elif args[i] == '--replace' and i + 1 < len(args):
            replace_text = args[i + 1]
            i += 2
        elif args[i] == '--delete':
            do_delete = True
            i += 1
        elif args[i] == '--sync':
            do_sync = True
            i += 1
        else:
            i += 1

    if not find_pattern:
        print('Error: --find <pattern> is required')
        sys.exit(1)

    # Phase 1: Find matches in subfolder files
    hits = find_matches(find_pattern, CAT_DIR)
    if not hits:
        print(f'No matches for "{find_pattern}" in subfolder files.')
        sys.exit(0)

    show_hits(hits)

    if do_delete:
        print(f'\nDeleting {sum(len(v) for v in hits.values())} entries...')
        n = replace_in_files(hits, find_pattern + r'\n?', None)
        print(f'Deleted {n} entries.')
    elif replace_text is not None:
        print(f'\nReplacing with: {replace_text[:100]}...')
        n = replace_in_files(hits, find_pattern, replace_text)
        print(f'Replaced in {n} files.')

    if do_sync:
        rebuild_main_files()
    elif do_delete or replace_text is not None:
        print('\nTip: add --sync to rebuild main files automatically.')


if __name__ == '__main__':
    main()
