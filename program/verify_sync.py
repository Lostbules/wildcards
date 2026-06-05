#!/usr/bin/env python3
"""
Verify and fix sync between NSFW_sex_categories/ (authoritative) and XL-pose_NSFW_sex.txt.

Approach:
  1. Load main file into hash set (O(1) lookup per entry)
  2. Iterate every line in subfolder files:
     - If missing from main → append to main immediately (当场补齐)
     - Report exact source (category + line number) of each missing entry
  3. After subfolders done, scan main file for orphan entries
     (lines not matched by any subfolder line) → save to _orphans.txt
  4. User reviews orphans manually — do NOT auto-delete

Usage:
    python verify_sync.py              # report only
    python verify_sync.py --fix        # append missing + save orphans + rebuild merged
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT_DIR = os.path.join(BASE, 'NSFW_sex_categories')
MAIN_FILE = os.path.join(BASE, 'XL-pose_NSFW_sex.txt')
SFW_FILE = os.path.join(BASE, 'XL-pose_SFW_clean.txt')
SOLO_FILE = os.path.join(BASE, 'XL-pose_NSFW_solo-nude.txt')
MERGED_FILE = os.path.join(BASE, 'XL-pose_merged.txt')
ORPHAN_FILE = os.path.join(BASE, '_orphans.txt')


# ── helpers ──────────────────────────────────────────────

def load_set(path):
    """Return set of stripped non-empty lines from a file."""
    lines = set()
    if not os.path.exists(path):
        return lines
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                lines.add(line)
    return lines


def load_list(path):
    """Return list of stripped non-empty lines (preserving order)."""
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip()]


def iter_subfolder(directory):
    """Yield (category_name, line_number, full_line, filepath) for every line."""
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(directory, fname)
        cat_name = fname.replace('.txt', '')
        with open(fpath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                yield cat_name, i, line, fpath


def rebuild_merged():
    """Rebuild XL-pose_merged.txt from three source files."""
    merged = []
    for src in [SFW_FILE, SOLO_FILE, MAIN_FILE]:
        merged.extend(load_list(src))
    with open(MERGED_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merged) + '\n')
    return len(merged)


# ── commands ─────────────────────────────────────────────

def verify():
    """Report-only: show missing + orphans without modifying anything."""
    main_set = load_set(MAIN_FILE)
    sub_set = set()

    missing = []
    for cat_name, ln, line, fpath in iter_subfolder(CAT_DIR):
        sub_set.add(line)
        if line not in main_set:
            missing.append((cat_name, ln, line))

    orphans = [line for line in load_list(MAIN_FILE) if line not in sub_set]

    print(f"Main file:     {len(main_set):>5} unique")
    print(f"Subfolder:     {len(sub_set):>5} unique (sum over categories)")
    print(f"Missing:       {len(missing):>5}  (in subfolder, not in main)")
    print(f"Orphans:       {len(orphans):>5}  (in main, not in any subfolder)")

    if missing:
        print(f"\n{'='*60}")
        print(f"  MISSING from main ({len(missing)} entries)")
        print(f"{'='*60}")
        for cat_name, ln, line in missing:
            preview = line[:110] + ('...' if len(line) > 110 else '')
            print(f"  [{cat_name}:L{ln}]  {preview}")

    if orphans:
        print(f"\n{'='*60}")
        print(f"  ORPHANS in main ({len(orphans)} entries)")
        print(f"{'='*60}")
        for line in orphans:
            preview = line[:110] + ('...' if len(line) > 110 else '')
            print(f"  {preview}")

    if not missing and not orphans:
        print("\n✅ Main ↔ subfolder perfectly in sync.")
    else:
        print("\n❌ Out of sync. Run with --fix to repair.")


def fix():
    """Append missing entries to main file, save orphans for review."""
    # 1. Load main into hash set
    main_set = load_set(MAIN_FILE)

    # 2. Walk subfolder files, append missing on the fly
    sub_set = set()
    appended = 0
    missing_detail = []

    for cat_name, ln, line, fpath in iter_subfolder(CAT_DIR):
        sub_set.add(line)
        if line not in main_set:
            missing_detail.append((cat_name, ln, line))
            with open(MAIN_FILE, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
            main_set.add(line)
            appended += 1

    if appended:
        print(f"✅ Appended {appended} missing entries to main file:")
        for cat_name, ln, line in missing_detail:
            preview = line[:110] + ('...' if len(line) > 110 else '')
            print(f"     [{cat_name}:L{ln}]  {preview}")
    else:
        print("✅ No missing entries (all subfolder lines already in main).")

    # 3. Find orphans: lines in main not matched by any subfolder line
    main_list = load_list(MAIN_FILE)
    orphans = [line for line in main_list if line not in sub_set]

    if orphans:
        with open(ORPHAN_FILE, 'w', encoding='utf-8') as f:
            for line in orphans:
                f.write(line + '\n')
        print(f"\n⚠  {len(orphans)} orphan entries saved to _orphans.txt")
        print(f"   These are in main but NOT in any subfolder category.")
        print(f"   Possible causes:")
        print(f"     a) Removed from subfolder but main wasn't rebuilt")
        print(f"     b) Legacy entries that should be deleted")
        print(f"     c) Entry should be added to a subfolder category")
        print(f"\n   --- Preview (first 10) ---")
        for line in orphans[:10]:
            preview = line[:110] + ('...' if len(line) > 110 else '')
            print(f"   {preview}")
    else:
        print("✅ No orphan entries.")
        if os.path.exists(ORPHAN_FILE):
            os.remove(ORPHAN_FILE)

    # 4. Rebuild merged
    merged_count = rebuild_merged()
    sfw = len(load_list(SFW_FILE))
    solo = len(load_list(SOLO_FILE))
    sex = len(load_list(MAIN_FILE))
    print(f"\n📊 Merged rebuilt: {sfw}+{solo}+{sex}={merged_count}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Final: sub={len(sub_set)} unique | main={sex} lines | merged={merged_count}")
    print(f"{'='*60}")


# ── main ─────────────────────────────────────────────────

if __name__ == '__main__':
    if '--fix' in sys.argv:
        fix()
    else:
        verify()
