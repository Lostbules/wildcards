#!/usr/bin/env python3
"""
Cross-reference tracker for NSFW_sex_categories duplicate entries.

Since one entry can appear in multiple subcategory files (模式 C), editing
an entry in one file leaves stale copies in others. This tool:

  - Builds a content-hash cross-reference index
  - Detects when previously-identical copies have diverged (one edited, others stale)
  - Syncs changes across all copies of the same entry

Usage:
    python nsfw_xref.py --build                  Build/rebuild cross-reference index
    python nsfw_xref.py --check                  Report stale duplicates (diverged copies)
    python nsfw_xref.py --check --verbose        Show all duplicates (including synced)
    python nsfw_xref.py --sync                   Sync diverged duplicates (propagate changes)
    python nsfw_xref.py --sync --auto            Sync without confirmation prompts
    python nsfw_xref.py --show <pattern>         Show cross-ref info for entries matching pattern
    python nsfw_xref.py --stats                  Quick stats: total entries, dupes, stale count

Index file: NSFW_sex_categories/_xref.json

How --sync works:
  When an entry was edited in file A (new hash) but still has the old version
  in files B and C, the script matches old→new by scene-context similarity.
  The new version is propagated to all files. If matching is ambiguous, the
  user is prompted (unless --auto).
"""

import os
import sys
import json
import hashlib
import re
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT_DIR = os.path.join(BASE, 'NSFW_sex_categories')
XREF_FILE = os.path.join(CAT_DIR, '_xref.json')

# Files to exclude from scanning
SKIP_FILES = {'_INDEX.md', '_xref.json'}


# ── helpers ──────────────────────────────────────────────────

def hash_line(line: str) -> str:
    """MD5 of a stripped line."""
    return hashlib.md5(line.strip().encode('utf-8')).hexdigest()


def iter_entries(directory: str):
    """Yield (filepath, filename, line_number, line_text, hash) for each entry."""
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith('.txt'):
            continue
        if fname in SKIP_FILES:
            continue
        fpath = os.path.join(directory, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                yield fpath, fname, i, line, hash_line(line)


def scene_keywords(line: str) -> set:
    """Extract scene-identifying keywords from a line (locations, positions, etc.)."""
    scene_tags = {
        'classroom', 'office', 'library', 'bedroom', 'bathroom', 'closet',
        'fitting room', 'dressing room', 'train interior', 'train',
        'restaurant', 'movie theater', 'park', 'tent', 'love hotel',
        'living room', 'couch', 'sofa', 'table', 'desk', 'bunk bed',
        'futon', 'tatami', 'sliding doors', 'window', 'doorway',
        'mirror', 'reflection', 'webcam', 'cellphone', 'recording',
        'game controller', 'television', 'shower curtain', 'backlighting',
        'silhouette', 'sleeping', 'confessional', 'gym', 'balcony',
        'missionary', 'doggystyle', 'cowgirl', 'girl on lap',
        'sex from behind', 'standing sex', 'handjob', 'fellatio',
        'anal', 'on bed', 'lying', 'bent over', 'against wall',
        'outdoors', 'night', 'moonlight', 'sunlight', 'sunbeam',
        'dim lighting', 'dark room', 'warm light', 'city lights',
        'after school', 'crowd',
    }
    found = set()
    ll = line.lower()
    for tag in scene_tags:
        if tag in ll:
            found.add(tag)
    return found


def find_best_match(old_content: str, candidates: list[tuple[str, str, str]]) -> tuple[str, str, str] | None:
    """
    Given old content and list of (fpath, fname, line) candidates from the
    likely source file (07_hidden_ntr), find the best replacement match.
    Uses scene keyword overlap.
    """
    if not candidates:
        return None
    old_kw = scene_keywords(old_content)
    best = None
    best_score = -1
    for fpath, fname, line in candidates:
        kw = scene_keywords(line)
        score = len(old_kw & kw)
        if score > best_score:
            best_score = score
            best = (fpath, fname, line)
    # Require at least 2 shared keywords for a confident match
    if best_score >= 2:
        return best
    return None


# ── build ────────────────────────────────────────────────────

def build_xref():
    """Scan all subcategory files and build the cross-reference index."""
    xref: dict[str, dict] = {}  # hash → {files: {fname: [line_numbers]}, preview}

    for fpath, fname, ln, line, h in iter_entries(CAT_DIR):
        if h not in xref:
            xref[h] = {'files': {}, 'preview': line[:120]}
        if fname not in xref[h]['files']:
            xref[h]['files'][fname] = []
        xref[h]['files'][fname].append(ln)

    # Keep only entries that appear in 2+ files
    multi = {h: v for h, v in xref.items() if len(v['files']) >= 2}
    single_count = len(xref) - len(multi)

    index = {
        'entries': multi,
        'built': datetime.utcnow().isoformat() + 'Z',
        'stats': {
            'total_hashes': len(xref),
            'multi_file_entries': len(multi),
            'single_file_entries': single_count,
        }
    }

    with open(XREF_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.join(BASE, 'backups'), exist_ok=True)

    print(f"Cross-reference built: {len(multi)} multi-file entries, {single_count} single-file")
    print(f"Saved to NSFW_sex_categories/_xref.json")
    return index


# ── load ─────────────────────────────────────────────────────

def load_xref() -> dict | None:
    """Load the stored cross-reference index, or None if not found."""
    if not os.path.exists(XREF_FILE):
        return None
    with open(XREF_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


# ── check ────────────────────────────────────────────────────

def check_stale(xref: dict, verbose: bool = False) -> list[dict]:
    """
    Compare current file contents against stored xref.
    Returns list of stale entries: {old_hash, old_content, old_files, new_entry_info}.
    """
    # Build current state: hash → files
    current: dict[str, dict] = {}
    for fpath, fname, ln, line, h in iter_entries(CAT_DIR):
        if h not in current:
            current[h] = {'files': {}, 'preview': line[:120]}
        if fname not in current[h]['files']:
            current[h]['files'][fname] = []
        current[h]['files'][fname].append(ln)

    stale = []
    synced_count = 0
    stale_count = 0

    for old_hash, old_info in xref.get('entries', {}).items():
        old_files = set(old_info['files'].keys())
        old_preview = old_info.get('preview', '')
        old_content = old_info.get('content', old_preview)

        # Check if this hash still exists in current state
        if old_hash in current:
            new_files = set(current[old_hash]['files'].keys())
            if old_files == new_files:
                synced_count += 1
                if verbose:
                    print(f"  ✓ synced: {old_preview[:80]}...  [{', '.join(sorted(old_files))}]")
            else:
                # Hash exists but some files removed — stale copies remain
                removed_files = old_files - new_files
                # Find which files still have old hash (stale) and which have new version
                stale_files = {}
                new_candidates = []
                for fname in sorted(old_files):
                    fpath = os.path.join(CAT_DIR, fname)
                    if not os.path.exists(fpath):
                        continue
                    with open(fpath, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f, 1):
                            line = line.strip()
                            if not line:
                                continue
                            if hash_line(line) == old_hash:
                                stale_files[fname] = i
                                break
                    if fname not in stale_files:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f, 1):
                                line = line.strip()
                                if not line:
                                    continue
                                new_candidates.append((fpath, fname, line))

                if stale_files and len(stale_files) < len(old_files):
                    stale_count += 1
                    entry = {
                        'old_hash': old_hash,
                        'old_preview': old_preview,
                        'old_files': old_files,
                        'stale_files': stale_files,
                        'candidates': new_candidates,
                    }
                    stale.append(entry)
                    print(f"  ⚠ stale: {old_preview[:80]}...")
                    print(f"      stale in: {', '.join(f'{f}:L{ln}' for f, ln in sorted(stale_files.items()))}")
                    if new_candidates:
                        best = find_best_match(old_preview, new_candidates)
                        if best:
                            _, bfname, bline = best
                            print(f"      likely new version in: {bfname} (scene match)")
                else:
                    synced_count += 1
                    if verbose and removed_files:
                        print(f"  ~ modified: {old_preview[:80]}...  [-{','.join(sorted(removed_files))}]")
        else:
            # Hash no longer exists — the entry was edited in at least one file
            # Find which files still have the old content and which have new
            stale_files = {}
            new_candidates = []

            for fname in sorted(old_files):
                fpath = os.path.join(CAT_DIR, fname)
                if os.path.exists(fpath):
                    with open(fpath, 'r', encoding='utf-8') as f:
                        found = False
                        for i, line in enumerate(f, 1):
                            line = line.strip()
                            if not line:
                                continue
                            if hash_line(line) == old_hash:
                                stale_files[fname] = i
                                found = True
                                break
                    if not found:
                        # Entry was edited/removed from this file — it's the "source" of change
                        # Collect candidates from this file for matching
                        with open(fpath, 'r', encoding='utf-8') as f:
                            for i, line in enumerate(f, 1):
                                line = line.strip()
                                if not line:
                                    continue
                                new_candidates.append((fpath, fname, line))

            if stale_files:
                stale_count += 1
                entry = {
                    'old_hash': old_hash,
                    'old_preview': old_preview,
                    'old_files': old_files,
                    'stale_files': stale_files,
                    'candidates': new_candidates,
                }
                stale.append(entry)
                print(f"  ⚠ stale: {old_preview[:80]}...")
                print(f"      stale in: {', '.join(f'{f}:L{ln}' for f, ln in sorted(stale_files.items()))}")
                if new_candidates:
                    # Find best match
                    best = find_best_match(old_preview, new_candidates)
                    if best:
                        _, bfname, bline = best
                        print(f"      likely new version in: {bfname} (match by scene keywords)")
                    else:
                        print(f"      ⚠ no confident match found among {len(new_candidates)} candidates")

    print(f"\n  Synced: {synced_count}  |  Stale: {stale_count}  |  Total multi: {synced_count + stale_count}")
    return stale


# ── sync ─────────────────────────────────────────────────────

def sync_stale(stale_entries: list[dict], auto: bool = False):
    """
    For each stale entry, propagate the new version to all stale copies.

    Matching logic:
      1. Find candidates from the file where the entry was edited (not in stale_files)
      2. Use scene keyword overlap to match old→new
      3. If confident, replace old entries in stale files with new version
      4. If ambiguous, prompt user
    """
    if not stale_entries:
        print("Nothing to sync.")
        return

    updated = 0
    skipped = 0

    for entry in stale_entries:
        old_preview = entry['old_preview']
        stale_files = entry['stale_files']
        candidates = entry['candidates']

        if not candidates:
            print(f"\n⚠  No candidates found for: {old_preview[:80]}...")
            print(f"   Stale in: {', '.join(stale_files.keys())}")
            skipped += 1
            continue

        # Find best match
        best = find_best_match(old_preview, candidates)
        if not best:
            print(f"\n⚠  Ambiguous match for: {old_preview[:80]}...")
            if not auto:
                print(f"   Candidates ({len(candidates)}):")
                for idx, (_, fname, cline) in enumerate(candidates[:5]):
                    cprev = cline[:100] + ('...' if len(cline) > 100 else '')
                    print(f"     [{idx}] {fname}: {cprev}")
                resp = input("   Skip? [s=skip] ").strip().lower()
                if resp:
                    skipped += 1
                    continue
            else:
                skipped += 1
                continue

        new_fpath, new_fname, new_line = best
        new_prev = new_line[:100] + ('...' if len(new_line) > 100 else '')

        print(f"\n  Syncing: {old_preview[:60]}...")
        print(f"    → new: {new_fname}: {new_prev}")

        if not auto:
            resp = input(f"    Update {len(stale_files)} stale copies? [Y/n/s] ").strip().lower()
            if resp == 's':
                skipped += 1
                continue
            if resp and resp != 'y':
                skipped += 1
                continue

        # Update all stale files: replace old line with new line
        for fname, ln in stale_files.items():
            fpath = os.path.join(CAT_DIR, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # Find the exact old line at the expected position
            if 1 <= ln <= len(lines):
                if hash_line(lines[ln - 1].strip()) == entry['old_hash']:
                    # Replace
                    if lines[ln - 1].endswith('\n'):
                        lines[ln - 1] = new_line + '\n'
                    else:
                        lines[ln - 1] = new_line + '\n'
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    print(f"      ✓ {fname}:L{ln}")
                    updated += 1
                else:
                    print(f"      ⚠ {fname}:L{ln} — content changed, skipping")

    print(f"\nUpdated: {updated}  |  Skipped: {skipped}")

    if updated > 0:
        # Rebuild xref
        print()
        build_xref()


# ── show ─────────────────────────────────────────────────────

def show_entry(pattern: str):
    """Show cross-ref info for entries matching pattern (case-insensitive)."""
    xref = load_xref()
    if not xref:
        print("No cross-reference index found. Run --build first.")
        return

    pat = pattern.lower()
    found = 0
    for h, info in xref.get('entries', {}).items():
        if pat in info['preview'].lower():
            found += 1
            print(f"\n  Hash: {h[:12]}...")
            print(f"  Preview: {info['preview'][:120]}")
            print(f"  Files:")
            for fname, lns in sorted(info['files'].items()):
                print(f"    {fname}: L{', L'.join(map(str, lns))}")

    if found == 0:
        print(f'No cross-ref entries matching "{pattern}".')
    else:
        print(f"\n{found} match(es).")


# ── stats ────────────────────────────────────────────────────

def show_stats():
    """Quick stats on the xref and current state."""
    xref = load_xref()
    if xref:
        s = xref.get('stats', {})
        built = xref.get('built', 'unknown')
        print(f"Cross-reference: {built}")
        print(f"  Multi-file entries: {s.get('multi_file_entries', '?')}")
        print(f"  Single-file entries: {s.get('single_file_entries', '?')}")
        print(f"  Total unique hashes: {s.get('total_hashes', '?')}")
    else:
        print("No cross-reference index found. Run --build first.")

    # Count current
    total = 0
    multi = 0
    seen = {}
    for _, fname, ln, line, h in iter_entries(CAT_DIR):
        total += 1
        if h not in seen:
            seen[h] = []
        seen[h].append(fname)
    for h, files in seen.items():
        if len(set(files)) >= 2:
            multi += 1
    print(f"\nCurrent state:")
    print(f"  Total entries: {total}")
    print(f"  Multi-file entries: {multi}")
    print(f"  Single-file entries: {len(seen) - multi}")


# ── propagate ────────────────────────────────────────────────

def propagate(source_file: str = '07_hidden_ntr.txt', auto: bool = False, min_score: int = 3):
    """
    Propagate changes from a source file to all other subcategory files.

    For each entry in the source file, find entries in other files that share
    ≥min_score scene keywords (likely the same scene). If content differs,
    update the other files to match the source.

    Use case: after editing 07_hidden_ntr.txt, propagate changes to copies
    in 14_standing_sex.txt, 16_vaginal_general.txt, etc.
    """
    source_path = os.path.join(CAT_DIR, source_file)
    if not os.path.exists(source_path):
        print(f"Source file not found: {source_path}")
        return

    # Load source entries
    source_entries = []
    with open(source_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line:
                source_entries.append((i, line))

    # Load all entries from other files
    other_entries: list[tuple[str, str, int, str, str]] = []  # (fpath, fname, ln, line, hash)
    for fpath, fname, ln, line, h in iter_entries(CAT_DIR):
        if fname == source_file:
            continue
        other_entries.append((fpath, fname, ln, line, h))

    updated = 0
    for src_ln, src_line in source_entries:
        src_kw = scene_keywords(src_line)
        src_hash = hash_line(src_line)

        for fpath, fname, ln, other_line, other_hash in other_entries:
            # Skip if already identical
            if src_hash == other_hash:
                continue

            other_kw = scene_keywords(other_line)
            overlap = len(src_kw & other_kw)

            if overlap >= min_score:
                src_prev = src_line[:60] + ('...' if len(src_line) > 60 else '')
                other_prev = other_line[:60] + ('...' if len(other_line) > 60 else '')

                print(f"\n  Match (score={overlap}): {fname}:L{ln}")
                print(f"    old: {other_prev}")
                print(f"    new: {src_prev}")

                if not auto:
                    resp = input(f"    Update? [Y/n/s] ").strip().lower()
                    if resp == 's':
                        continue
                    if resp and resp != 'y':
                        continue

                # Update
                with open(fpath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if 1 <= ln <= len(lines):
                    if hash_line(lines[ln - 1].strip()) == other_hash:
                        lines[ln - 1] = src_line + '\n'
                        with open(fpath, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                        print(f"      ✓ {fname}:L{ln}")
                        updated += 1

    print(f"\nUpdated: {updated}")
    if updated > 0:
        print()
        build_xref()


# ── fix-bootstrap ────────────────────────────────────────────

OLD_STYLE_MARKERS = ['stealth sex', 'netorare']

def fix_bootstrap(auto: bool = False):
    """
    Bootstrap: sync stale copies of old-style entries in non-07 files
    to their optimized counterparts in 07_hidden_ntr.txt.

    This handles the initial divergence where 07_hidden_ntr was optimized
    but other category files still have the old versions.
    """
    ntr_file = os.path.join(CAT_DIR, '07_hidden_ntr.txt')

    # Load new entries from 07_hidden_ntr
    ntr_entries = []
    with open(ntr_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                ntr_entries.append(line)

    # Find old entries in other files
    old_entries: dict[str, list[tuple[str, int, str]]] = {}  # old_hash → [(fname, ln, line)]
    for fpath, fname, ln, line, h in iter_entries(CAT_DIR):
        if fname == '07_hidden_ntr':
            continue
        # Detect old-style: has stealth sex, or has netorare with old formula tags
        ll = line.lower()
        if 'stealth sex' in ll:
            old_entries.setdefault(h, []).append((fname, ln, line))

    if not old_entries:
        print("No old-style entries found in other files. Already clean!")
        return

    print(f"Found {len(old_entries)} old-style entries across other subcategory files.\n")

    updated = 0
    skipped = 0
    unmatched = 0

    for old_hash, copies in sorted(old_entries.items()):
        old_line = copies[0][2]  # Use first copy as representative
        old_kw = scene_keywords(old_line)

        # Find best matching new entry in 07_hidden_ntr
        best_score = -1
        best_new = None
        for new_line in ntr_entries:
            new_kw = scene_keywords(new_line)
            score = len(old_kw & new_kw)
            # Boost score for shared unique location markers
            if score > best_score:
                best_score = score
                best_new = new_line

        # Require at least 1 shared keyword for a match
        if best_score < 1 or best_new is None:
            old_prev = old_line[:80] + ('...' if len(old_line) > 80 else '')
            print(f"  ⚠ unmatched: {old_prev}")
            print(f"      in: {', '.join(f'{f}:L{ln}' for f, ln, _ in copies)}")
            unmatched += 1
            continue

        old_prev = old_line[:60] + ('...' if len(old_line) > 60 else '')
        new_prev = best_new[:60] + ('...' if len(best_new) > 60 else '')
        file_list = ', '.join(f'{f}:L{ln}' for f, ln, _ in copies)

        print(f"  Match (score={best_score}): {old_prev}")
        print(f"    → {new_prev}")
        print(f"    in: {file_list}")

        if not auto:
            resp = input(f"    Replace? [Y/n/s] ").strip().lower()
            if resp == 's':
                skipped += len(copies)
                continue
            if resp and resp != 'y':
                skipped += len(copies)
                continue

        # Replace in all copies
        for fname, ln, _ in copies:
            fpath = os.path.join(CAT_DIR, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if 1 <= ln <= len(lines):
                if hash_line(lines[ln - 1].strip()) == old_hash:
                    lines[ln - 1] = best_new + '\n'
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    print(f"      ✓ {fname}:L{ln}")
                    updated += 1

    print(f"\nUpdated: {updated}  |  Skipped: {skipped}  |  Unmatched: {unmatched}")

    if updated > 0:
        print()
        build_xref()


# ── main ─────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args or '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)

    if '--fix-bootstrap' in args:
        auto = '--auto' in args
        fix_bootstrap(auto=auto)

    elif '--build' in args:
        build_xref()

    elif '--check' in args:
        xref = load_xref()
        if not xref:
            print("No cross-reference index found. Run --build first.")
            sys.exit(1)
        verbose = '--verbose' in args
        print(f"Checking against xref built {xref.get('built', '?')}...\n")
        check_stale(xref, verbose=verbose)

    elif '--sync' in args:
        xref = load_xref()
        if not xref:
            print("No cross-reference index found. Run --build first.")
            sys.exit(1)
        auto = '--auto' in args
        print(f"Checking stale duplicates against xref built {xref.get('built', '?')}...\n")
        stale = check_stale(xref, verbose=False)
        if stale:
            print(f"\n{'='*60}")
            print(f"Syncing {len(stale)} stale entries...")
            print(f"{'='*60}")
            sync_stale(stale, auto=auto)
        else:
            print("\nNo stale entries to sync.")

    elif '--show' in args:
        idx = args.index('--show')
        if idx + 1 < len(args):
            show_entry(args[idx + 1])
        else:
            print("Error: --show requires a pattern argument")
            sys.exit(1)

    elif '--stats' in args:
        show_stats()

    else:
        print(__doc__)
        sys.exit(0)


if __name__ == '__main__':
    main()
