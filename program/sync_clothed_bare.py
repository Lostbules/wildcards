#!/usr/bin/env python3
"""
sync_clothed_bare.py — 确保角色文件的 clothed/bare 双向对称

用途：
  读取一个角色 wildcard 文件（name, series, tag1, ... 格式），
  输出 clothed 和 bare 两个版本，确保每个角色在两个文件中各有一条目。

   clothed → bare：自动 strip_clothing()
   bare → clothed：使用内置 ICONIC_CLOTHING 映射添加标志性服装

用法：
  python sync_clothed_bare.py <input.txt> <output_clothed.txt> <output_bare.txt>

已知局限：
  - 对于 ICONIC_CLOTHING 映射中没有的角色，使用通用默认值
  - 裸角色（如 ghost、slime）的衣服映射为近似值
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_clothing import is_clothing_tag, strip_clothing

# ============================================================
# 标志性服装映射 — (name_lower, series_lower) → "clothing tags to append"
# 仅覆盖 bare-only 的角色（原条目无衣物标签的）
# ============================================================

ICONIC_CLOTHING = {
    # --- aikatsu! ---
    ("hikami sumire", "aikatsu! (series)"): "school uniform, long sleeves, pleated skirt, necktie",

    # --- amagi brilliant park ---
    ("sento isuzu", "amagi brilliant park"): "military uniform, long sleeves, belt, black thighhighs",

    # --- bishoujo mangekyou ---
    ("kagarino kirie", "bishoujo mangekyou"): "serafuku, long sleeves, red ribbon",

    # --- blue archive ---
    ("hina (blue archive)", "blue archive"): "white shirt, long sleeves, black skirt, halo",

    # --- chuunibyou demo koi ga shitai! ---
    ("shichimiya satone", "chuunibyou demo koi ga shitai!"): "serafuku, long sleeves, scarf",
    ("takanashi touka", "chuunibyou demo koi ga shitai!"): "white shirt, long sleeves, black skirt",

    # --- date a live ---
    ("itsuka kotori", "date a live"): "serafuku, long sleeves, hair ribbon, red ribbon",
    ("tobiichi origami", "date a live"): "serafuku, long sleeves",

    # --- danmachi ---
    ("aiz wallenstein", "dungeon ni deai wo motomeru no wa machigatteiru darou ka"): "armor, breastplate, blue dress, long sleeves, thigh boots, sword",
    ("liliruca arde", "dungeon ni deai wo motomeru no wa machigatteiru darou ka"): "white shirt, brown shorts, cape, backpack, long sleeves, hat",

    # --- eiyuu densetsu ---
    ("cecile_neues", "eiyuu densetsu"): "white shirt, long sleeves, skirt",
    ("ilya_platiere", "eiyuu densetsu"): "dress, long sleeves, jewelry",
    ("renne (eiyuu densetsu)", "eiyuu densetsu"): "dress, long sleeves, white thighhighs, hair ribbon",

    # --- final fantasy ---
    ("astrologian (final fantasy)", "final fantasy"): "robe, long sleeves, hood, cape",
    ("trance terra branford", "final fantasy"): "cape, long sleeves",

    # --- genshin impact ---
    ("boo tao (genshin impact)", "genshin impact"): "white dress, long sleeves",
    ("fischl (genshin impact )", "genshin impact"): "black dress, bare shoulders, detached sleeves, long sleeves, black choker",
    ("focalors (genshin impact)", "genshin impact"): "white dress, bare shoulders, detached sleeves, long sleeves",
    ("kamisato ayaka", "genshin impact"): "white dress, armor, long sleeves, geta, blue bow",

    # --- gochuumon wa usagi desu ka? ---
    ("kafuu chino", "gochuumon wa usagi desu ka?"): "blue dress, white apron, maid headdress, puffy short sleeves, white thighhighs",
    ("tedeza rize", "gochuumon wa usagi desu ka?"): "black dress, white apron, maid headdress, puffy short sleeves",

    # --- granblue fantasy ---
    ("djeeta (granblue fantasy)", "granblue fantasy"): "armor, blue dress, gauntlets, thigh boots, cape",

    # --- honkai: star rail ---
    ("herta (honkai: star rail )", "honkai: star rail"): "white dress, black hat, purple choker, long sleeves, beret",
    ("huohuo (honkai: star rail)", "honkai: star rail"): "green dress, hat, bare shoulders, long sleeves",

    # --- kimetsu no yaiba ---
    ("daki (kimetsu no yaiba)", "kimetsu no yaiba"): "kimono, obi, wide sleeves, japanese clothes, long sleeves",
    ("kamado nezuko", "kimetsu no yaiba"): "kimono, haori, obi, japanese clothes, long sleeves",
    ("kanroji mitsuri", "kimetsu no yaiba"): "demon slayer uniform, long sleeves, green thighhighs",
    ("kochou kanae", "kimetsu no yaiba"): "demon slayer uniform, haori, long sleeves",
    ("kochou shinobu", "kimetsu no yaiba"): "demon slayer uniform, haori, long sleeves",
    ("tsuyuri kanao", "kimetsu no yaiba"): "demon slayer uniform, long sleeves",

    # --- kobayashi-san chi no maidragon ---
    ("kanna kamui", "kobayashi-san chi no maidragon"): "white capelet, pink dress, long sleeves",

    # --- konosuba ---
    ("iris (konosuba)", "kono subarashii sekai ni shukufuku wo!"): "white dress, long sleeves, crown, cape",

    # --- mushoku tensei ---
    ("elinalise dragonroad", "mushoku tensei"): "crop top, detached sleeves, breastplate, short shorts, red thighhighs, thigh boots, waist cape",

    # --- naruto ---
    ("haruno sakura", "naruto (series)"): "pink dress, red headband, long sleeves, ninja",
    ("hyuuga hanabi", "naruto (series)"): "white kimono, japanese clothes, long sleeves",
    ("hyuuga hinata", "naruto (series)"): "white jacket, black pants, long sleeves, ninja",

    # --- neptune ---
    ("adult neptune", "neptune (series)"): "purple dress, bare shoulders, long sleeves",
    ("compa", "neptune (series)"): "white dress, long sleeves, red ribbon, knee boots",
    ("if (neptunia)", "neptune (series)"): "brown jacket, black shirt, long sleeves, black shorts",
    ("pish", "neptune (series)"): "blue dress, long sleeves, hat",

    # --- one piece ---
    ("nami (one piece)", "one piece"): "bikini top, jeans, belt, high heels",

    # --- oreimo ---
    ("hanazawa kana", "ore no imouto ga konna ni kawaii wake ga nai"): "serafuku, long sleeves, pleated skirt",

    # --- pokemon ---
    ("misty (pokemon)", "pokemon"): "yellow tank top, red shorts, suspenders, sneakers",

    # --- re:zero ---
    ("theresia van astrea", "re:zero kara hajimeru isekai seikatsu"): "white dress, armor, long sleeves, cape",

    # --- rozen maiden ---
    ("barasuishou", "rozen maiden"): "gothic lolita, lolita fashion, purple dress, long sleeves, puffy sleeves, ruffled collar, purple boots",

    # --- rune factory ---
    ("toona", "rune factory"): "white dress, long sleeves, jewelry",

    # --- symphogear ---
    ("yukine chris", "senki zesshou symphogear"): "armor, bodysuit, long sleeves, white cloak",

    # --- shakugan no shana ---
    ("shana", "shakugan no shana"): "serafuku, black coat, long sleeves, black thighhighs",

    # --- sword art online ---
    ("alice zuberg", "sword art online"): "white dress, armor, bare shoulders, long sleeves, blue ribbon",
    ("argo the rat", "sword art online"): "fairy wings, brown dress, bare shoulders, fairy (sao)",
    ("asuna (sao)", "sword art online"): "white jacket, red skirt, long sleeves, armor, breastplate",
    ("asuna (stacia)", "sword art online"): "white dress, bare shoulders, long sleeves, tiara",
    ("leafa", "sword art online"): "white dress, green jacket, long sleeves, fairy wings, fairy (sao)",
    ("lisbeth (sao-alo)", "sword art online"): "white dress, fairy wings, fairy (sao), bare shoulders",
    ("sinon (sao-alo)", "sword art online"): "green dress, fairy wings, fairy (sao), bare shoulders",
    ("yui (sao)", "sword art online"): "white dress, fairy wings, bare shoulders, fairy (sao), barefoot",

    # --- tate no yuusha ---
    ("melty q melromarc", "tate no yuusha no nariagari"): "blue dress, white capelet, long sleeves, crown",

    # --- to love-ru ---
    ("kurosaki mea", "to love-ru"): "serafuku, long sleeves, pleated skirt",
    ("master nemesis", "to love-ru"): "black dress, long sleeves, bare shoulders",
    ("nana asta deviluke", "to love-ru"): "serafuku, long sleeves, pleated skirt",
    ("yuuki mikan", "to love-ru"): "serafuku, long sleeves, pleated skirt, red ribbon",

    # --- toaru ---
    ("tsukuyomi komoe", "toaru majutsu no index"): "serafuku, long sleeves",

    # --- touhou ---
    ("alice margatroid", "touhou"): "blue dress, long sleeves, capelet, hairband",
    ("chen", "touhou"): "red dress, long sleeves",
    ("inaba tewi", "touhou"): "pink dress, long sleeves, carrot necklace",
    ("koakuma", "touhou"): "black dress, long sleeves, red bow",
    ("komeiji satori", "touhou"): "blue dress, long sleeves, hairband",
    ("konpaku youmu", "touhou"): "green dress, white shirt, long sleeves, black hairband",
    ("medicine melancholy", "touhou"): "black dress, long sleeves, red bow",
    ("nazrin", "touhou"): "grey dress, long sleeves, cape, pendant",
    ("watatsuki no yorihime", "touhou"): "white kimono, red hakama, long sleeves, bow",

    # --- mushoku tensei ---
    ("eris greyrat", "mushoku tensei"): "black hairband, white shirt, long sleeves",

    # --- sword art online ---
    ("silica", "sword art online"): "breastplate, black thighhighs, fingerless gloves",

    # --- zero no tsukaima ---
    ("louise francoise le blanc de la valliere", "zero no tsukaima"): "white shirt, black skirt, long sleeves, cape",

    # --- genshin impact (extras) ---
    ("keqing (genshin impact)", "genshin impact"): "black pantyhose, bare shoulders, detached sleeves, long sleeves",
    ("yae miko", "genshin impact"): "japanese clothes, bare shoulders, detached sleeves, wide sleeves, earrings",

    # --- neptune series (extras) ---
    ("if (neptunia)", "neptune (series)"): "brown jacket, black shirt, long sleeves, black shorts",
    ("pish", "neptune (series)"): "blue dress, long sleeves, hat",

    # --- wuthering waves ---
    ("changli (wuthering waves )", "wuthering waves"): "white dress, black jacket, bare shoulders, black collar, halterneck, long sleeves, colored extremities",

    # --- yosuga no sora ---
    ("kasugano sora", "yosuga no sora"): "white dress, long sleeves",

    # --- madoka ---
    ("kaname madoka (magical girl )", "mahou shoujo madoka magica (anime )"): "pink dress, bubble skirt, magical girl, red choker, short sleeves, long sleeves",
}

# Series-level defaults for characters not in ICONIC_CLOTHING
SERIES_DEFAULTS = {
    "aikatsu! (series)": "school uniform, long sleeves, pleated skirt",
    "angel beats!": "serafuku, long sleeves, shinda sekai sensen uniform",
    "arknights": "black jacket, white shirt, long sleeves, black shorts",
    "atelier (series)": "white dress, long sleeves, capelet",
    "azur lane": "military uniform, long sleeves, black thighhighs",
    "blue archive": "white shirt, long sleeves, pleated skirt, halo",
    "bocchi the rock!": "serafuku, long sleeves, pleated skirt",
    "chainsaw man": "white shirt, black necktie, black pants, long sleeves",
    "chuunibyou demo koi ga shitai!": "serafuku, long sleeves",
    "clannad": "serafuku, long sleeves, hikarizaka private high school uniform",
    "date a live": "serafuku, long sleeves",
    "douluo dalu": "white dress, bare shoulders, detached sleeves, long sleeves",
    "doupo cangqiong": "chinese clothes, long sleeves",
    "dungeon ni deai wo motomeru no wa machigatteiru darou ka": "white shirt, black skirt, long sleeves",
    "eiyuu densetsu": "dress, long sleeves",
    "eromanga sensei": "pajamas, long sleeves",
    "fatal fury": "chinese clothes, long sleeves",
    "final fantasy": "white shirt, black skirt, long sleeves",
    "gabriel dropout": "serafuku, long sleeves",
    "gekkan shoujo nozaki-kun": "serafuku, long sleeves, rouman academy school uniform",
    "genshin impact": "white dress, bare shoulders, detached sleeves, long sleeves",
    "goblin slayer!": "white shirt, long sleeves, black skirt",
    "gochuumon wa usagi desu ka?": "blue dress, white apron, maid headdress",
    "granblue fantasy": "dress, long sleeves, armor",
    "honkai (series)": "white dress, bare shoulders, detached sleeves, long sleeves",
    "honkai: star rail": "white shirt, black jacket, long sleeves",
    "hyouka": "serafuku, long sleeves, kamiyama high school uniform (hyouka)",
    "kaguya-sama wa kokurasetai ~tensai-tachi no renai zunousen~": "serafuku, long sleeves, shuuchiin academy school uniform",
    "kantai collection": "serafuku, long sleeves, pleated skirt",
    "kobayashi-san chi no maidragon": "maid headdress, white apron, black dress, long sleeves",
    "kono subarashii sekai ni shukufuku wo!": "white shirt, black skirt, long sleeves",
    "little busters!": "serafuku, long sleeves, little busters! school uniform",
    "lycoris recoil": "lycoris uniform, long sleeves",
    "mahou shoujo madoka magica": "serafuku, long sleeves",
    "mahouka koukou no rettousei": "serafuku, long sleeves, first high school uniform",
    "majo no tabitabi": "black robe, witch hat, long sleeves",
    "marvel": "superhero costume, bodysuit, long sleeves",
    "monogatari (series)": "serafuku, long sleeves, naoetsu high school uniform",
    "mushoku tensei": "white shirt, long sleeves, black skirt",
    "naruto (series)": "ninja outfit, long sleeves",
    "neptune (series)": "dress, long sleeves, bare shoulders",
    "nier (series)": "black dress, long sleeves",
    "no game no life": "serafuku, long sleeves",
    "one piece": "bikini top, jeans",
    "ore no imouto ga konna ni kawaii wake ga nai": "serafuku, long sleeves",
    "overwatch": "bodysuit, long sleeves",
    "owari no seraph": "military uniform, long sleeves",
    "pokemon": "jacket, short shorts, sneakers",
    "princess connect!": "white dress, long sleeves, bare shoulders",
    "re:zero kara hajimeru isekai seikatsu": "maid headdress, white apron, black dress, roswaal mansion maid uniform",
    "rozen maiden": "gothic lolita, lolita fashion, dress, long sleeves",
    "rune factory": "dress, long sleeves",
    "seishun buta yarou": "serafuku, long sleeves",
    "senki zesshou symphogear": "armor, bodysuit, long sleeves",
    "shakugan no shana": "serafuku, long sleeves",
    "shingeki no kyojin": "paradis military uniform, jacket, long sleeves",
    "sono bisque doll wa koi wo suru": "serafuku, long sleeves, pleated skirt",
    "sousou no frieren": "white dress, long sleeves",
    "spy x family": "black dress, long sleeves, bare shoulders",
    "steins;gate": "white shirt, black shorts, black pantyhose, red necktie, long sleeves",
    "strike the blood": "serafuku, long sleeves, saikai academy school uniform",
    "sword art online": "white dress, long sleeves, bare shoulders",
    "tate no yuusha no nariagari": "white dress, long sleeves",
    "tensei shitara slime datta ken": "white kimono, japanese clothes, long sleeves, miko",
    "the king of fighters": "chinese clothes, long sleeves",
    "to love-ru": "serafuku, long sleeves, pleated skirt",
    "toaru majutsu no index": "serafuku, long sleeves",
    "toradora!": "serafuku, long sleeves, oohashi high school uniform",
    "touhou": "dress, long sleeves",
    "violet evergarden (series)": "white dress, blue jacket, long sleeves",
    "wuthering waves": "white dress, long sleeves, bare shoulders",
    "xenoblade chronicles (series)": "armor, bodysuit, long sleeves",
    "yahari ore no seishun lovecome wa machigatteiru.": "serafuku, long sleeves, sobu high school uniform",
    "youkoso jitsuryoku shijou shugi no kyoushitsu e": "serafuku, long sleeves, advanced nurturing high school uniform",
    "zenless zone zero": "black jacket, white shirt, long sleeves",
    "zero no tsukaima": "white shirt, black skirt, long sleeves, cape",
}


def _norm(s):
    """Normalize a name/series string for key lookup: unescape parens, strip, lowercase."""
    s = s.replace('\\(', '(').replace('\\)', ')')  # unescape LaTeX-style parens
    s = re.sub(r'\s+', ' ', s)  # collapse whitespace
    s = re.sub(r'\s+\)', ')', s)  # remove space before closing paren
    s = re.sub(r'\(\s+', '(', s)  # remove space after opening paren
    return s.strip().lower()


def get_clothing_for_bare(name, series, existing_tags):
    """返回应追加到 bare 条目的标志性服装标签字符串。"""
    key = (_norm(name), _norm(series))
    if key in ICONIC_CLOTHING:
        return ICONIC_CLOTHING[key]

    # Try series default
    for prefix, clothing in SERIES_DEFAULTS.items():
        if series.lower().strip().startswith(prefix.lower()):
            return clothing

    # Fallback
    return "long sleeves, dress"


def sync_files(input_path, output_clothed, output_bare):
    """主逻辑：读取输入文件，输出对称的 clothed 和 bare 文件。"""
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\n').rstrip(', ').rstrip(',') for l in f.readlines() if l.strip()]

    clothed = []
    bare = []

    for line in lines:
        tags = [t.strip() for t in line.split(',') if t.strip()]
        if len(tags) < 2:
            continue

        name = tags[0]
        series = tags[1]
        rest = tags[2:]

        has_clothing = any(is_clothing_tag(t) for t in rest)

        if has_clothing:
            clothed.append(line)
            # Also generate bare version
            stripped = strip_clothing(line)
            if stripped != line and len(stripped.split(',')) >= 3:
                # Only add if not already in bare
                bare_tags = [t.strip() for t in stripped.split(',')]
                bare_name = bare_tags[0].lower().strip()
                bare_series = bare_tags[1].lower().strip() if len(bare_tags) > 1 else ""
                bare.append(stripped)
        else:
            bare.append(line)

    # Deduplicate bare (same name+series)
    seen_bare = set()
    dedup_bare = []
    for l in bare:
        tags = [t.strip() for t in l.split(',')]
        key = (_norm(tags[0]), _norm(tags[1])) if len(tags) >= 2 else l.lower()
        if key not in seen_bare:
            seen_bare.add(key)
            dedup_bare.append(l)
    bare = dedup_bare

    # Find bare entries without clothed counterpart
    clothed_keys = set()
    for l in clothed:
        tags = [t.strip() for t in l.split(',')]
        if len(tags) >= 2:
            clothed_keys.add((_norm(tags[0]), _norm(tags[1])))

    # Generate clothed versions for bare-only entries
    added_clothed = 0
    for l in bare:
        tags = [t.strip() for t in l.split(',')]
        if len(tags) < 2:
            continue
        key = (_norm(tags[0]), _norm(tags[1]))
        if key not in clothed_keys:
            name = tags[0]
            series = tags[1]
            rest = tags[2:]
            clothing_str = get_clothing_for_bare(name, series, rest)
            # Add clothing tags (dedup with existing)
            clothing_tags = [t.strip() for t in clothing_str.split(',')]
            existing = set(t.lower().strip() for t in rest)
            new_clothing = [t for t in clothing_tags if t.lower().strip() not in existing]
            new_line = ', '.join(tags + new_clothing)
            clothed.append(new_line)
            clothed_keys.add(key)
            added_clothed += 1

    # Post-process: enhance existing clothed entries with ICONIC_CLOTHING tags
    enhanced = 0
    for i, l in enumerate(clothed):
        # Clean trailing commas and whitespace first
        l = l.rstrip(', ')
        tags = [t.strip() for t in l.split(',') if t.strip()]
        if len(tags) < 3:
            continue
        key = (_norm(tags[0]), _norm(tags[1]))
        if key in ICONIC_CLOTHING:
            existing_tags = set(t.lower().strip() for t in tags)
            icon_tags = [t.strip() for t in ICONIC_CLOTHING[key].split(',')]
            missing = [t for t in icon_tags if t.lower().strip() not in existing_tags]
            if missing:
                clothed[i] = ', '.join(tags + missing)
                enhanced += 1

    if enhanced:
        print(f"Enhanced {enhanced} existing clothed entries with ICONIC_CLOTHING tags", file=sys.stderr)

    # Write output
    with open(output_clothed, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(clothed)) + '\n')
    with open(output_bare, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(bare)) + '\n')

    return len(clothed), len(bare), added_clothed


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python sync_clothed_bare.py <input.txt> <output_clothed.txt> <output_bare.txt>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_clothed = sys.argv[2]
    output_bare = sys.argv[3]

    nc, nb, added = sync_files(input_path, output_clothed, output_bare)
    print(f"Clothed: {nc} entries")
    print(f"Bare: {nb} entries")
    print(f"Bare→clothed added: {added}")
