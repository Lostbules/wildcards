#!/usr/bin/env python3
"""
strip_clothing.py — 批量生成角色条目的去衣版本

用途：
  读取 ComfyUI Impact Pack wildcard 角色文件（name, series, tag1, tag2, ... 格式），
  为每个已有衣物标签的条目生成一条去除衣物标签的"裸肤"版本，追加到文件末尾。
  保留：发色、瞳色、发型、表情、身体特征、丝袜/腿饰、首饰、眼镜、种族特征等。
  移除：所有衣物、鞋类、手套、帽子、领饰、武器、职业装、盔甲等。

用法：
  python strip_clothing.py <input_file.txt> > output_file.txt

输出：
  原始条目 + 新增去衣条目到 stdout，摘要信息到 stderr。
  新增条目仅在去衣后仍有 ≥3 个字段（name, series, ≥1 个保留标签）时才追加。

注意事项：
  - SAFE_TAGS / CLOTHING_EXACT / CLOTHING_PATTERNS 硬编码在脚本中，修改匹配逻辑需编辑源码
  - 不会覆盖原文件，输出重定向到新文件；如需原地替换请用 mv
  - 生成后需用 awk '!seen[$0]++' 去重（不同衣物皮肤的去衣版可能收敛为同一条）

已知局限：
  - 不处理 name 中没有 series 的平铺标签文件
  - 衣物标签集偏向女性角色（裙装/女式服装覆盖较全）
  - 特殊服饰（如特定作品校服名）需手动添加到 CLOTHING_EXACT
"""

import sys
import re

# ============================================================
# 保留标签 — 不应被移除的"安全"标签
# ============================================================
SAFE_TAGS = {
    # 发饰（手工逐一确认，不受 clothing pattern 误伤）
    'hair_ribbon', 'hair_bow', 'hair_ornament', 'hair_flower', 'hair_clip',
    'hairpin', 'hairband', 'hair_bun', 'hair_scrunchie',
    'ahoge', 'side_hair', 'sidelocks', 'hair_between_eyes',
    # 丝袜/腿饰
    'thighhighs', 'pantyhose', 'stockings', 'socks', 'kneehighs',
    'fishnets', 'fishnet', 'leggings',
    'black_thighhighs', 'white_thighhighs', 'blue_thighhighs',
    'green_thighhighs', 'red_thighhighs', 'purple_thighhighs',
    'striped_thighhighs', 'frilled_thighhighs', 'lace-trimmed_thighhighs',
    'fishnet_thighhighs',
    'black_pantyhose', 'white_pantyhose', 'blue_pantyhose',
    'black_socks', 'white_socks', 'striped_socks',
    'black_stockings', 'white_stockings',
    'black_leggings', 'white_leggings',
    'garter_straps', 'bridal_garter',
    # 身体特征
    'breasts', 'large_breasts', 'small_breasts', 'medium_breasts',
    'huge_breasts', 'flat_chest', 'pendulous_breasts',
    'navel', 'cleavage', 'ass', 'pussy',
    'wide_hips', 'narrow_waist', 'hourglass_figure',
    # 首饰/装饰
    'earrings', 'necklace', 'bracelet', 'anklet', 'ring',
    'choker', 'collar', 'pet_collar',
    # 眼镜
    'glasses', 'sunglasses', 'eyepatch',
    # 种族特征
    'elf_ears', 'cat_ears', 'cat_tail', 'fox_ears', 'fox_tail',
    'horns', 'wings', 'halo', 'demon_tail', 'oni_horns',
    # 其他安全标签
    'barefoot', 'bandages', 'bandaged_arm', 'bandaged_leg',
    'headphones', 'earmuffs',
    'tattoo', 'scar', 'mole',
    'holding_mask',
    'mismatched_legwear', 'single_thighhigh', 'mismatched_thighhigh',
    'thighband_pantyhose',
    'arm_ribbon',
    'sweat', 'blush', 'tears',
}

# ============================================================
# 衣物标签 — 正则模式列表（模糊匹配）
# ============================================================
CLOTHING_PATTERNS = [
    r'dress\b', r'shirt\b', r'jacket\b', r'coat\b', r'skirt\b', r'pants\b', r'shorts\b',
    r'uniform\b', r'kimono', r'leotard', r'bodysuit', r'swimsuit', r'bikini', r'apron\b',
    r'cape\b', r'capelet', r'cloak', r'robe\b', r'hoodie', r'sweater', r'serafuku',
    r'blazer', r'corset', r'crop_top', r'tube_top', r'halterneck', r'bodystocking',
    r'overalls', r'romper', r'jumpsuit', r'vest\b', r'cardigan', r'tank_top',
    r'harem_outfit', r'turtleneck', r'china_dress', r'chinese_clothes', r'japanese_clothes',
    r'hanfu', r'cheongsam', r'qipao', r'miniskirt', r'microdress', r'pencil_dress',
    r'sailor_collar', r'sailor_shirt', r'collared_shirt', r'off-shoulder_shirt',
    r'sideless_dress', r'strapless_dress', r'sleeveless_dress', r'armored_dress',
    r'layered_dress', r'flamenco_dress', r'gradient_dress', r'argyle_kimono',
    r'frilled_dress', r'frilled_skirt', r'frilled_apron', r'frilled_panties',
    r'boots?\b', r'shoes\b', r'sneakers', r'heels', r'pumps', r'sandals', r'slippers',
    r'loafers', r'mary_janes',
    r'gloves\b', r'gauntlets', r'wrist_cuffs', r'bracer\b',
    r'ascot\b', r'necktie', r'bowtie', r'neckerchief', r'cravat', r'bolo_tie',
    r'hat\b', r'hats?\b', r'beret', r'bonnet', r'crown\b', r'tiara', r'headdress',
    r'cap\b', r'helmet', r'headwear', r'headpiece', r'kabuto', r'jingasa',
    r'sword\b', r'katana', r'scythe', r'staff\b', r'spear', r'lance', r'axe\b',
    r'hammer', r'shield', r'dagger', r'knife', r'gun\b', r'rifle', r'pistol',
    r'p90\b', r'crossbow', r'bow\b',
    r'_sleeves\b', r'sleeveless', r'bare_shoulders', r'off_shoulder', r'off-shoulder',
    r'strapless', r'backless', r'detached_sleeves', r'detached_collar',
    r'fur_trim', r'fur-trimmed', r'fur-trim', r'gold_trim',
    r'striped_clothes', r'argyle_clothes', r'plaid\b', r'polka_dot',
    r'frilled\b', r'frills\b',
    r'open_jacket', r'cropped_jacket', r'tied_jacket', r'open_coat',
    r'zettai_ryouiki', r'side_slit', r'center_opening',
    r'shoulder_cutout', r'navel_cutout', r'cleavage_cutout', r'cutout\b',
    r'buttons\b', r'zipper', r'drawstring', r'hood_down',
    r'juliet_sleeves', r'puffy_sleeves', r'puffy_short_sleeves', r'puffy_long_sleeves',
    r'see-through_sleeves', r'sleeves_past_fingers', r'ribbon-trimmed',
    r'sideless_outfit', r'side_cutout', r'revealing_clothes', r'pelvic_curtain',
    r'borrowed_clothes', r'burned_clothes', r'wet_shirt', r'tied_shirt',
    r'front-tie_top', r'side-tie', r'criss-cross_halter',
    r'chest_sarashi', r'sarashi',
    r'maid\b', r'waitress', r'nun\b', r'pilot\b', r'police\b', r'nurse\b',
    r'fast_food', r'employee',
    r'lolita_fashion', r'gothic_lolita', r'ouji_fashion', r'victorian\b',
    r'playboy_bunny', r'superhero_costume', r'santa_costume', r'magical_girl',
    r'witch\b', r'princess\b', r'jiangshi', r'ninja\b',
    r'belt\b', r'suspenders', r'garter_straps', r'bridal_garter', r'arm_garter',
    r'thigh_strap\b', r'arm_ribbon', r'rei_no_himo',
    r'bandaged_arm', r'bandaged_leg', r'bandages\b',
    r'epaulettes', r'aiguillette', r'id_card',
    r'vision_\(genshin', r'tassel\b', r'brooch\b',
    r'shimenawa', r'qingdai_guanmao', r'ofuda',
    r'neck_bell', r'jingle_bell',
    r'pocket_watch',
    r'chain_leash', r'leash\b',
    r'safety_pin',
    r'armor\b', r'breastplate', r'pauldron', r'chainmail',
    r'sports_bra', r'sportswear',
    r'mismatched_legwear',
    r'single_thighhigh', r'mismatched_thighhigh',
    r'thighband_pantyhose',
    r'collar\b', r'pet_collar',
    r'headphones', r'earmuffs',
    r'holster',
    r'bag\b', r'backpack', r'school_bag',
    r'holding_mask',
    r'snowflake_print',
    r'see-through_cleavage',
    r'covered_navel',
    r'flower_tattoo',
    r'black_ribbon\b', r'white_ribbon\b', r'red_ribbon\b', r'blue_ribbon\b',
    r'green_ribbon\b', r'pink_ribbon\b', r'purple_ribbon\b', r'yellow_ribbon\b',
    r'orange_ribbon\b', r'brown_ribbon\b',
    r'black_bow\b', r'white_bow\b', r'red_bow\b', r'blue_bow\b',
    r'green_bow\b', r'pink_bow\b', r'purple_bow\b', r'yellow_bow\b',
    r'orange_bow\b', r'brown_bow\b',
]

# ============================================================
# 衣物标签 — 精确匹配集合
# ============================================================
CLOTHING_EXACT = {
    'black_dress', 'red_dress', 'white_dress', 'blue_dress', 'green_dress',
    'pink_dress', 'purple_dress', 'yellow_dress', 'orange_dress', 'brown_dress',
    'grey_dress', 'gray_dress', 'multicolored_dress',
    'black_skirt', 'white_skirt', 'blue_skirt', 'red_skirt', 'green_skirt',
    'pink_skirt', 'purple_skirt', 'orange_skirt', 'grey_skirt',
    'plaid_skirt', 'pleated_skirt', 'bubble_skirt', 'pencil_skirt',
    'black_shorts', 'white_shorts', 'blue_shorts', 'red_shorts', 'green_shorts',
    'black_pants', 'white_pants', 'blue_pants',
    'black_leotard', 'blue_leotard', 'red_leotard', 'pink_leotard',
    'highleg_leotard', 'strapless_leotard',
    'black_jacket', 'red_jacket', 'blue_jacket', 'green_jacket', 'white_jacket',
    'pink_jacket', 'aqua_jacket', 'purple_jacket', 'yellow_jacket', 'orange_jacket',
    'brown_jacket', 'grey_jacket', 'fur-trimmed_jacket', 'cropped_jacket',
    'tied_jacket', 'open_jacket', 'track_jacket',
    'black_coat', 'red_coat', 'white_coat', 'blue_coat', 'green_coat', 'lab_coat',
    'black_kimono', 'red_kimono', 'white_kimono', 'pink_kimono', 'purple_kimono',
    'green_kimono', 'blue_kimono', 'orange_kimono', 'short_kimono',
    'black_cape', 'white_cape', 'blue_cape', 'green_cape', 'red_cape', 'purple_cape',
    'black_capelet', 'red_capelet', 'white_capelet', 'fur-trimmed_capelet',
    'green_capelet', 'pink_capelet',
    'black_cloak', 'white_cloak', 'multicolored_cloak',
    'black_scarf', 'blue_scarf', 'red_scarf', 'white_scarf', 'plaid_scarf',
    'green_scarf', 'purple_scarf', 'yellow_scarf',
    'white_sweater', 'yellow_sweater', 'purple_sweater', 'red_sweater',
    'green_sweater', 'blue_sweater', 'ribbed_sweater', 'turtleneck_sweater',
    'black_hoodie', 'white_hoodie', 'grey_hoodie',
    'white_shirt', 'black_shirt', 'red_shirt', 'blue_shirt', 'green_shirt',
    'pink_shirt', 'purple_shirt', 'yellow_shirt', 'orange_shirt', 'brown_shirt',
    'grey_shirt',
    'white_gloves', 'black_gloves', 'red_gloves', 'blue_gloves', 'brown_gloves',
    'yellow_gloves', 'purple_gloves', 'green_gloves', 'pink_gloves',
    'orange_gloves', 'grey_gloves', 'mismatched_gloves',
    'white_ascot', 'red_ascot', 'yellow_ascot', 'blue_ascot', 'purple_ascot',
    'green_ascot', 'black_ascot',
    'white_necktie', 'red_necktie', 'blue_necktie', 'black_necktie',
    'green_necktie', 'yellow_necktie',
    'white_bowtie', 'red_bowtie', 'black_bowtie', 'blue_bowtie',
    'black_hat', 'white_hat', 'red_hat', 'blue_hat', 'green_hat', 'pink_hat',
    'purple_hat', 'brown_hat', 'yellow_hat', 'orange_hat', 'grey_hat',
    'black_headwear', 'white_headwear', 'red_headwear', 'blue_headwear',
    'green_headwear', 'purple_headwear', 'brown_headwear', 'pink_headwear',
    'grey_headwear',
    'black_cap', 'white_cap', 'red_cap', 'blue_cap', 'green_cap',
    'shako_cap',
    'black_boots', 'white_boots', 'brown_boots', 'blue_boots', 'red_boots',
    'thigh_boots', 'thighboots', 'knee_boots',
    'black_pantyhose', 'white_pantyhose', 'blue_pantyhose',
    'black_thighhighs', 'white_thighhighs', 'blue_thighhighs',
    'green_thighhighs', 'red_thighhighs', 'purple_thighhighs',
    'striped_thighhighs', 'frilled_thighhighs', 'lace-trimmed_thighhighs',
    'fishnet_thighhighs',
    'black_socks', 'white_socks', 'striped_socks',
    'black_stockings', 'white_stockings',
    'black_leggings', 'white_leggings', 'fishnets', 'fishnet',
    'partially_fingerless_gloves', 'elbow_gloves', 'fingerless_gloves',
    'black_neck_ribbon', 'red_neck_ribbon', 'blue_neck_ribbon',
    'white_neck_ribbon', 'neck_ribbon',
    'white_bikini', 'red_bikini', 'black_bikini', 'purple_bikini', 'blue_bikini',
    'green_bikini', 'pink_bikini', 'strapless_bikini', 'highleg_bikini',
    'frilled_bikini', 'side-tie_bikini', 'side-tie_bikini_bottom',
    'bikini_skirt', 'bikini_top',
    'casual_one-piece_swimsuit', 'frilled_one-piece_swimsuit',
    'blue_one-piece_swimsuit', 'white_one-piece_swimsuit',
    'green_one-piece_swimsuit', 'competition_swimsuit',
    'two-tone_swimsuit', 'one-piece_swimsuit',
    'china_dress', 'chinese_clothes', 'japanese_clothes',
    'paradis_military_uniform', 'military_uniform', 'school_uniform',
    'roswaal_mansion_maid_uniform', 'lycoris_uniform',
    'shuuchiin_academy_school_uniform', 'sobu_high_school_uniform',
    'summer_uniform', 'winter_uniform',
    'swimsuit_cover-up', 'swimsuit_coverup',
    'white_apron', 'maid_apron',
    'baseball_cap', 'witch_hat', 'top_hat', 'sailor_hat', 'santa_hat',
    'maid_headdress', 'nurse_cap', 'garrison_cap',
    'fast_food_uniform', 'employee_uniform', 'pilot_suit', 'space_suit',
    'business_suit', 'gym_uniform', 'superhero_costume', 'santa_costume',
    'playboy_bunny',
    'black_sports_bra', 'sports_bra', 'sportswear', 'armor', 'breastplate',
    'shoulder_armor', 'single_pauldron',
}

# ============================================================
# 核心逻辑
# ============================================================

def is_clothing_tag(tag):
    """判断单个标签是否为衣物标签。先检查 SAFE_TAGS 白名单，再匹配衣物模式。"""
    tag_lower = tag.strip().lower().replace(' ', '_')
    if not tag_lower:
        return False

    # 白名单优先 — 发饰/丝袜/首饰等不视为衣物
    if tag_lower in SAFE_TAGS:
        return False

    if tag_lower in CLOTHING_EXACT:
        return True

    for pattern in CLOTHING_PATTERNS:
        if re.search(pattern, tag_lower):
            return True

    return False


def strip_clothing(line):
    """去除一行角色条目中的所有衣物标签。返回重构后的条目字符串。"""
    tags = [t.strip() for t in line.split(',')]
    if len(tags) < 2:
        return line

    name = tags[0]
    series = tags[1]
    rest = tags[2:]

    kept = [t for t in rest if not is_clothing_tag(t)]

    result_tags = [name, series] + kept
    result = ', '.join(result_tags)
    # 清理格式化产物
    result = re.sub(r'\s+,', ',', result)
    result = re.sub(r',,+', ',', result)
    result = re.sub(r',\s*$', '', result)
    result = result.strip()

    return result


def process_file(filepath):
    """读取文件，为每个条目生成去衣版本（跳过空行和无效条目）。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    lines_out = []
    added = 0

    for line in lines:
        lines_out.append(line)
        if not line.strip():
            continue

        stripped = strip_clothing(line)
        if stripped != line and stripped != '' and len(stripped.split(',')) >= 3:
            lines_out.append(stripped)
            added += 1

    return lines_out, added


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python strip_clothing.py <file.txt>", file=sys.stderr)
        print("  Reads a character wildcard file and appends clothing-free variants.", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    lines_out, added = process_file(filepath)

    for line in lines_out:
        print(line)

    print(f"\n--- Added {added} stripped entries ---", file=sys.stderr)
