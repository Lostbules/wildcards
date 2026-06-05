#!/usr/bin/env python3
"""
Add clothing fallback entries to characters_categories/clothed/ after split.

For characters that exist in bare/ but NOT in clothed/, take the most
detailed bare entry and append clothing tags to create a clothed fallback.
Entries are appended to the corresponding clothed/ series file.

The clothing tag map is curated per-character (no generic defaults).

Usage:
    python add_clothing_fallback.py              # report missing
    python add_clothing_fallback.py --apply      # append fallback entries

Run AFTER split_clothing.py to ensure clothed/ and bare/ are current.
"""

import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT_DIR = os.path.join(BASE, 'characters_categories')
CLOTHED_DIR = os.path.join(CAT_DIR, 'clothed')
BARE_DIR = os.path.join(CAT_DIR, 'bare')

# ── Per-character clothing tag map ───────────────────────
# Key: base character name (lowercase, no series/parens)
# Value: comma-separated clothing tags to append

CLOTHING_MAP = {
    # trails_series
    'cecile_neues': 'nurse uniform, white dress, nurse cap',
    'ilya_platiere': 'elegant dress, evening gown, long gloves',
    'renne': 'gothic lolita, purple dress, frilled dress, knee socks',

    # SAO
    'alice zuberg': 'armor, golden armor, blue cape, gauntlets',
    'argo the rat': 'cloak, hooded cloak, light armor, shorts',
    'leafa': 'green tunic, elf outfit, fairy wings, belt, boots',
    'lisbeth': 'blacksmith apron, leather apron',
    'sinon': 'archer outfit, light armor, cat ears, cat tail',

    # Touhou
    'alice margatroid': 'blue dress, frilled dress, apron, hairband',
    'inaba tewi': 'pink dress, rabbit ears, carrot necklace',
    'koakuma': 'black dress, gothic dress, demon wings, collar',
    'konpaku youmu': 'green dress, hakama, white shirt, ribbon',
    'medicine melancholy': 'gothic dress, black dress, red ribbon, doll joints',
    'nazrin': 'brown dress, mouse ears, mouse tail, pendant',
    'watatsuki no yorihime': 'elegant dress, purple dress, high collar, long skirt',

    # Genshin
    'kamisato ayaka': 'blue kimono, armor plates, geta, hair ornament',

    # Naruto
    'haruno sakura': 'red cheongsam, chinese dress, sandals',
    'hyuuga hanabi': 'kimono, hyuuga robe, traditional, sandals',
    'hyuuga hinata': 'ninja outfit, fishnet shirt, mesh armor, sandals, headband',

    # To Love-Ru
    'kurosaki mea': 'school uniform, serafuku, ribbon, knee socks',
    'nana asta deviluke': 'school uniform, serafuku, ribbon, demon tail',
    'yuuki mikan': 'school uniform, serafuku, hair bobbles, knee socks',

    # Neptune
    'adult neptune': 'purple hoodie, hoodie dress, d-pad hair ornament, thigh highs',
    'compa': 'nurse uniform, nurse cap, white dress',
    'if': 'green jacket, shorts, fingerless gloves, belt',

    # Date A Live
    'itsuka kotori': 'shrine maiden outfit, white ribbon, red hakama',
    'tobiichi origami': 'school uniform, serafuku, hairclip',

    # Danmachi
    'aiz wallenstein': 'armor, silver armor, cape, thigh highs',
    'liliruca arde': 'hoodie, cloak, backpack, belt, shorts',

    # Gochiusa
    'tedeza rize': 'maid uniform, frilled apron, cafe uniform, thigh highs',

    # Chuunibyou
    'shichimiya satone': 'school uniform, serafuku, hair rings',
    'takanashi touka': 'maid uniform, apron, ladle, frilled headband',

    # Solo characters
    'astrologian': 'astrologian robe, long robe, star pattern, hood, gold trim',
    'barasuishou': 'gothic lolita, white dress, frilled dress, eyepatch, rose',
    'elinalise dragonroad': 'adventurer outfit, cape, belt, boots, shorts',
    'hanazawa kana': 'school uniform, serafuku, ribbon',
    'hikami sumire': 'blue dress, check pattern, ruffled skirt, star charm, ribbon',
    'iris': 'princess dress, white dress, royal attire, tiara, long gloves',
    'kagarino kirie': 'black dress, gothic, detached sleeves, choker, frills',
    'kanna kamui': 'school uniform, randoseru, backpack',
    'kasugano sora': 'white dress, summer dress, hair ribbon',
    'melty q melromarc': 'princess dress, blue dress, royal attire, tiara',
    'misty': 'crop top, short shorts, suspenders',
    'nami': 'bikini top, jeans, log pose, bracelet',
    'sento isuzu': 'military uniform, royal guard uniform, gloves, boots',
    'shana': 'school uniform, black cloak, serafuku',
    'theresia van astrea': 'elegant dress, white dress, long skirt, hair ornament',
    'tsukuyomi komoe': 'school uniform, serafuku, lab coat',
    'toona': 'pink trench coat, orange scarf, black top, orange skirt, black leggings, pink boots, earrings',
    'yukine chris': 'symphogear armor, mecha armor, red and white, gauntlets, boots',
}

# Characters deliberately left bare-only (monster forms, special cases)
SKIP_BARE = {
    'trance terra branford',  # FF6 esper/monster form
}


# ── helpers ──────────────────────────────────────────────

def base_name(name):
    """Strip parenthetical suffixes from name. Handles both '(' and backslash-paren."""
    return __import__('re').split(r'\\?\(', name)[0].strip()


def load_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip()]


def get_clothed_chars():
    """Return set of base character names that exist in clothed/ files."""
    chars = set()
    for fname in sorted(os.listdir(CLOTHED_DIR)):
        if not fname.endswith('.txt'):
            continue
        for line in load_lines(os.path.join(CLOTHED_DIR, fname)):
            name = line.split(',')[0].strip()
            chars.add(base_name(name))
    return chars


def get_bare_entries():
    """Return {fname: [(base_name, full_line), ...]} for bare/ files."""
    entries = {}
    for fname in sorted(os.listdir(BARE_DIR)):
        if not fname.endswith('.txt'):
            continue
        fpath = os.path.join(BARE_DIR, fname)
        file_entries = []
        for line in load_lines(fpath):
            name = line.split(',')[0].strip()
            file_entries.append((base_name(name), line))
        entries[fname] = file_entries
    return entries


def find_missing():
    """Return [(fname, base_name, best_bare_line, clothing_tags), ...] for chars missing from clothed."""
    clothed_chars = get_clothed_chars()
    bare_entries = get_bare_entries()
    missing = []

    for fname, entries in bare_entries.items():
        # Group by base name, pick most detailed entry
        by_name = {}
        for bn, line in entries:
            if bn not in by_name:
                by_name[bn] = line
            elif len(line.split(',')) > len(by_name[bn].split(',')):
                by_name[bn] = line  # keep most detailed

        for bn, best_line in by_name.items():
            if bn not in clothed_chars:
                if bn.lower() in SKIP_BARE:
                    continue  # deliberately kept bare
                bn_lower = bn.lower()
                if bn_lower in CLOTHING_MAP:
                    missing.append((fname, bn, best_line, CLOTHING_MAP[bn_lower]))
                else:
                    missing.append((fname, bn, best_line, None))

    return missing


# ── commands ─────────────────────────────────────────────

def report():
    missing = find_missing()
    if not missing:
        print('All characters have clothing entries. ✅')
        return

    print(f'{len(missing)} characters missing from clothed/:\n')
    for fname, bn, bare_line, tags in missing:
        preview = bare_line[:100] + ('...' if len(bare_line) > 100 else '')
        if tags:
            print(f'  [{fname}] {bn}')
            print(f'    bare: {preview}')
            print(f'    +tag: {tags}')
        else:
            print(f'  [{fname}] {bn}  ⚠ NO CLOTHING MAP — needs manual assignment')
            print(f'    bare: {preview}')
        print()


def apply():
    missing = find_missing()
    unmapped = [(f, b, l) for f, b, l, t in missing if t is None]
    if unmapped:
        print(f'ERROR: {len(unmapped)} characters have no clothing mapping:')
        for fname, bn, _ in unmapped:
            print(f'  {fname}: {bn}')
        print('Add them to CLOTHING_MAP in this script and retry.')
        sys.exit(1)

    added = 0
    by_file = {}  # fname -> [(bn, new_line)]
    for fname, bn, bare_line, tags in missing:
        new_line = f'{bare_line}, {tags}'
        by_file.setdefault(fname, []).append((bn, new_line))

    for fname, items in sorted(by_file.items()):
        fpath = os.path.join(CLOTHED_DIR, fname)
        with open(fpath, 'a', encoding='utf-8') as f:
            for bn, new_line in items:
                f.write(new_line + '\n')
                added += 1
        print(f'{fname}: +{len(items)} entries')

    print(f'\nTotal: {added} fallback entries added to clothed/.')


if __name__ == '__main__':
    if '--apply' in sys.argv:
        apply()
    else:
        report()
