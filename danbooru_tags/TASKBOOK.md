# Danbooru 标签库分类任务书

> 目标：将 24,317 条 Danbooru General 标签从单一 CSV 拆分为按子类组织的分类标签库
> 产出目录：`~/.claude/skills/tag-crafter/tag-library/categorized/`（主）<br>
> 数据源：`danbooru_tags/danbooru_general.csv`（不修改）
> 创建日期：2026-06-04

---

## 〇、背景

### 现状

```
danbooru_tags/
├── README.md
├── danbooru_full.csv         (90,857 tags, 2.4MB)  ← 暂不处理
├── danbooru_general.csv      (24,317 tags, 607KB)  ← 本次目标
├── danbooru_artist.csv       (34,196 tags)          ← 暂不处理
├── danbooru_character.csv    (25,540 tags)          ← 暂不处理
├── danbooru_copyright.csv    (6,431 tags)           ← 暂不处理
└── danbooru_meta.csv         (373 tags)             ← 暂不处理
```

- `danbooru_general.csv` 格式：`tag,category,post_count,"aliases"`
- 标签分布：顶级(10K+) 2,264 | 高频(1K-10K) 5,365 | 中频(100-1K) 11,416 | 低频(<100) 5,272
- 当前是扁平结构，不存在子类划分

### 目标

将 `danbooru_general.csv` 按功能拆分，产出放入 skill 自带的标签库目录（随 skill 迁移）：

```
~/.claude/skills/tag-crafter/tag-library/categorized/
├── subjects.csv          # 主体/数量
├── body_parts.csv        # 身体部位
├── clothing.csv          # 服装/配饰
├── poses.csv             # 姿势/动作
├── expressions.csv       # 表情/眼神
├── composition.csv       # 构图/镜头/景别
├── lighting.csv          # 光线/氛围/天气
├── scenes.csv            # 场景/地点/环境
├── objects.csv           # 道具/物品/武器
├── style.csv             # 风格/介质/质量
├── actions.csv           # 动作/行为（非姿势类）
├── sex_acts.csv          # 性行为标签（NSFW专用）
├── body_traits.csv       # 体型/身体特征（发色瞳色肤色等）
├── text_features.csv     # 文字/气泡/UI元素
├── audio_features.csv    # 音效文字/拟声词
└── other.csv             # 无法分类的标签
```

---

## 一、分类体系定义

### 1.1 十六个子类

| # | 文件名 | 说明 | 示例标签 | 预估数量 |
|---|--------|------|---------|---------|
| 1 | `subjects.csv` | 主体数量/性别/人数 | `1girl`, `1boy`, `solo`, `multiple_girls`, `no_humans` | ~30 |
| 2 | `body_parts.csv` | 身体部位 | `breasts`, `feet`, `hands`, `thighs`, `navel`, `armpits`, `ass` | ~400 |
| 3 | `clothing.csv` | 服装/鞋袜/配饰 | `skirt`, `thighhighs`, `choker`, `glasses`, `kimono`, `swimsuit` | ~1,200 |
| 4 | `poses.csv` | 姿势/体态 | `standing`, `sitting`, `seiza`, `lying`, `kneeling`, `all_fours`, `stretching` | ~200 |
| 5 | `expressions.csv` | 表情/眼神/嘴部 | `smile`, `blush`, `crying`, `looking_at_viewer`, `closed_eyes`, `open_mouth` | ~150 |
| 6 | `composition.csv` | 构图/镜头/视角 | `from_below`, `cowboy_shot`, `depth_of_field`, `dutch_angle`, `upper_body` | ~120 |
| 7 | `lighting.csv` | 光线/氛围/天气 | `backlighting`, `sunbeam`, `moonlight`, `chiaroscuro`, `fog`, `rain`, `sunlight` | ~180 |
| 8 | `scenes.csv` | 场景/地点/环境 | `classroom`, `bedroom`, `outdoors`, `beach`, `city`, `rooftop`, `indoors` | ~500 |
| 9 | `objects.csv` | 道具/物品/武器/食物 | `sword`, `phone`, `book`, `food`, `flower`, `microphone`, `gun` | ~800 |
| 10 | `style.csv` | 风格/介质/质量 | `monochrome`, `sketch`, `watercolor_(medium)`, `greyscale`, `absurdres` | ~150 |
| 11 | `actions.csv` | 动作/行为（功能性动作，非姿势） | `holding`, `eating`, `reading`, `running`, `jumping`, `dancing` | ~350 |
| 12 | `sex_acts.csv` | 性行为（NSFW专用分类） | `paizuri`, `fellatio`, `footjob`, `missionary`, `cowgirl_position` | ~400 |
| 13 | `body_traits.csv` | 体型/颜色/身体特征 | `large_breasts`, `blonde_hair`, `blue_eyes`, `dark_skin`, `muscular` | ~400 |
| 14 | `text_features.csv` | 文字/气泡/UI | `speech_bubble`, `english_text`, `signature`, `twitter_username`, `watermark` | ~60 |
| 15 | `audio_features.csv` | 音效文字/拟声词 | `sfx`, `sound_effects`, `onomatopoeia` | ~30 |
| 16 | `other.csv` | 无法归入以上的漏网标签 | 兜底类 | ~500-2,000 |

**注意：一条标签可以属于多个分类（允许重合）。** 例如：
- `thighhighs` 属于 `clothing.csv`（服装），同时也可能是 `sex_acts.csv` 中足交条目的相关标签
- `blush` 属于 `expressions.csv`（表情）和 `body_traits.csv`（身体特征）均可
- 分类时按**首要功能**归类，不需要完美互斥

### 1.2 与 validate_tags.sh 的联动

分类完成后，`validate_tags.sh` 中的 `guess_category()` 函数将使用这些分类文件进行精确查询：

```bash
# 当前逻辑（flat mode）：全量搜 danbooru_general.csv
# 分类后逻辑（categorized mode）：根据 tag 关键词路由到对应子文件

# 优先级：
# 1. 如果 categorized/ 目录存在且不为空，使用分类索引
# 2. 否则回退到 danbooru_general.csv
# 3. 两个模式都能正常工作
```

---

## 二、分类方法：关键词自动分类 + 人工复核

### 2.1 总体流程

```
阶段 A: 关键词自动分类脚本 → 生成 16 个 _auto_*.csv
阶段 B: 人工逐类抽查（重点：高频标签 + 边界标签）
阶段 C: 修正误分类、决定重合标签的"主分类"
阶段 D: 统计验证、生成 README
```

### 2.2 阶段 A：关键词自动分类脚本

见附录 A 完整脚本。核心逻辑：

1. 对每一行 CSV，提取标签名
2. 按优先级匹配关键词正则
3. 写入对应分类文件（一行可以写入多个文件）
4. 未被任何规则捕获的写入 `other.csv`
5. 输出统计报告

**关键词设计原则：**
- 优先匹配最明确的特征（如 `_hair` → body_traits，`_eyes` → body_traits）
- 注意子串陷阱（`hair_ribbon` 是 clothing，不是 body_traits；`holding_hands` 是 actions，不是 body_parts）
- 先用最具体的模式（如 `school_uniform` 匹配 clothing），再用通用模式（如 `_(uniform)` 也是 clothing）
- 性行为标签用独立的正则集合，避免污染 poses.csv 和 actions.csv

### 2.3 阶段 B：人工逐类抽查

每类按 post_count 降序排列，抽查：

| 抽查策略 | 范围 |
|---------|------|
| **全查** | post_count > 100,000 的顶级标签 |
| **抽查 20%** | post_count 1,000-100,000 的高频标签 |
| **抽查 5%** | post_count 100-1,000 的中频标签 |
| **抽查 1%** | post_count < 100 的低频标签 |

**检查要点：**
- 标签是否归属到了最合理的分类？
- 是否有标签应该出现在某个分类但没有？
- `other.csv` 中是否有大量本应归入已知分类的标签？（说明关键词规则遗漏）

### 2.4 阶段 C：边界修正

常见边界问题及处理原则：

| 边界场景 | 处理原则 |
|---------|---------|
| `blush` — 表情还是身体特征？ | 归入 expressions（主要功能是传达情感） |
| `sweat` — 身体特征还是表情？ | 归入 expressions（汗滴是情感符号） |
| `open_mouth` — 表情还是身体部位？ | 归入 expressions（嘴部表情上下文） |
| `hand_on_hip` — 姿势还是动作？ | 归入 poses（它是体态描述） |
| `holding_weapon` — 动作还是道具？ | 归入 actions（以动作为主） |
| `wet` / `wet_clothes` — 光线/氛围还是服装？ | `wet` → lighting；`wet_clothes` → clothing |
| `nude` / `completely_nude` — 身体特征还是性行为？ | 归入 body_traits（基础身体状态，非行为） |

### 2.5 阶段 D：统计验证与 README

完成后生成：
```
tag-library/categorized/README.md    ← 每个子类的说明、标签数、top-20 示例
tag-library/categorized/_stats.json  ← 机器可读的统计数据
```

验证命令：
```bash
SKILL_TAGS="$HOME/.claude/skills/tag-crafter/tag-library/categorized"

# 16 个子文件标签总数 vs 原 general.csv
cat "$SKILL_TAGS"/*.csv | grep -v '^$' | wc -l
# 应等于或略大于 24,317（因为允许重合）

# 每类数量分布
for f in "$SKILL_TAGS"/*.csv; do echo "$(basename $f): $(wc -l < $f)"; done

# other.csv 不应超过 2,000（说明关键词覆盖面够）
wc -l "$SKILL_TAGS/other.csv"
```

---

## 三、实施步骤（按优先级）

### Step 1：创建分类目录 + 运行自动分类脚本（30 分钟）

```bash
# 脚本在 danbooru_tags/scripts/ 下运行，输出自动写入 skill 目录
bash danbooru_tags/scripts/categorize.sh
```

产出：16 个 CSV 写入 `~/.claude/skills/tag-crafter/tag-library/categorized/` + 统计报告

### Step 2：审查 high-priority 分类（2 小时）

优先审这些（wildcard 最常用的类别）：

| 优先级 | 分类 | 理由 |
|--------|------|------|
| 🔴 P0 | `poses.csv` | tag-crafter 核心依赖 |
| 🔴 P0 | `expressions.csv` | tag-crafter 核心依赖 |
| 🔴 P0 | `composition.csv` | tag-crafter 核心依赖 |
| 🔴 P0 | `lighting.csv` | tag-crafter 核心依赖 |
| 🟡 P1 | `body_parts.csv` | 高频使用 |
| 🟡 P1 | `clothing.csv` | 高频使用 |
| 🟡 P1 | `sex_acts.csv` | NSFW 姿势分类依赖 |
| 🟢 P2 | `scenes.csv` | 常用补充 |
| 🟢 P2 | `body_traits.csv` | 常用补充 |
| 🟢 P2 | `actions.csv` | 常用补充 |
| ⚪ P3 | 其余 6 类 | 一次性审完 |

### Step 3：批量修正误分类（1 小时）

根据 Step 2 的审查发现，修改分类脚本的正则规则，重新运行，直到每类准确率 >95%。

### Step 4：生成 README + 统计文件（30 分钟）

### Step 5：更新 validate_tags.sh 的猜类逻辑（15 分钟）

让 `guess_category()` 函数的正则与分类脚本保持一致。

---

## 四、分类关键词正则表

以下是各类别的关键词匹配逻辑（用于分类脚本和 guess_category 函数）。

### subjects.csv
```
^solo$|^solo_focus$|^no_humans$
^[0-9]+girl(s)?$|^[0-9]+boy(s)?$|^[0-9]+other(s)?$
^multiple_girls$|^multiple_boys$|^male_focus$|^female_focus$
```

### body_parts.csv
```
_breasts$|_nipples$|_pussy$|_penis$|_testicles$|_ass$
^feet$|^foot$|^hands$|^hand$|^legs$|^arms$|^fingers$|^toes$
_thighs$|^thighs$|^thigh|_navel$|^navel$|^stomach$|^midriff$
_armpits$|^armpits$|^collarbone$|_hips$|^hips$|^waist$
_tongue$|^tongue$|_teeth$|^teeth$|^lips$|_lips$
^tail$|_tail$|^wings$|^horns$|^ears$|_ears$
# 注意排除：hair_ribbon, holding_hands 等会误匹配的
```

### clothing.csv
```
^dress|_dress$|^skirt|_skirt$|^shirt|_shirt$|^pants$|^shorts$
^thighhighs$|^kneehighs$|^pantyhose$|^fishnets$|^socks$|^shoes$|^boots$|^heels$
^hat$|^glasses$|^gloves$|_gloves$|^jacket$|^coat$|^sweater$
^swimsuit$|^bikini$|^underwear$|^bra$|^panties$|^lingerie$
^ribbon$|^bow$|_bow$|^choker$|^necklace$|^earrings$|^bracelet$|^jewelry$
^kimono$|_uniform$|^school_uniform$|^serafuku$|^japanese_clothes$
^open_clothes$|^open_jacket$|^detached_sleeves$|^wide_sleeves$|^long_sleeves$
_costume$|^alternate_costume$|^official_alternate_costume$
# 排除：hair_ribbon 归 clothing（配饰），不是 body_traits
```

### poses.csv
```
^standing$|^sitting$|^seiza$|^wariza$|^yokozuwari$|^indian_style$
^kneeling$|^on_one_knee$|^squatting$|^crouching$
^lying$|^on_back$|^on_stomach$|^on_side$|^reclining$|^fetal_position$
^all_fours$|^bent_over$|^stretching$|^reaching$
^leaning_forward$|^leaning_back$|^leg_up$|^leg_split$
^crossed_legs$|^legs_folded$|^lotus_position$
^spread_legs$|^knees_together_feet_apart$
^handstand$|^dynamic_pose$|^fighting_stance$|^contrapposto$
_pose$     # bowlegged_pose, ojou-sama_pose, zombie_pose 等
```

### expressions.csv
```
^smile$|^grin$|^frown$|^smirk$|^angry$|^surprised$|^sad$|^crying$
^blush$|^tears$|^despair$|^gloom|^sweatdrop$|^anger_vein$|^nosebleed$
^open_mouth$|^closed_mouth$|^parted_lips$|^tongue_out$
^open_eyes$|^closed_eyes$|^half-closed_eyes$|^wide_eyed$|^one_eye_closed$
^looking_at_viewer$|^looking_back$|^looking_down$|^looking_up$|^looking_away$
^looking_to_the_side$|^looking_ahead$|^looking_afar$|^averting_eyes$
^eye_contact$|^facing_viewer$|^facing_away$
^biting$|^licking_lips$|^biting_lip$
^heart_eyes$|^star_eyes$|^dilated_pupils$
^:d$|^:p$|^:o$|^;)$|^;($|^>:(|^>;)|^>_<$|^@_@$|^o_o$|^t_t$|^>_>$
```

### composition.csv
```
^from_above$|^from_below$|^aerial_view$|^dutch_angle$|^fisheye$
^front_view$|^side_view$|^back_view$|^rear_view$|^turned_back$
^full_body$|^cowboy_shot$|^cropped_legs$|^close-up$|^upper_body$
^selfie$|^multiple_views$|^pov$|^foreshortening$|^wide_shot$
^depth_of_field$|^bokeh$|^foreground_blur$|^background_blur$
^phone_screen_framing$|^shaky_handheld$|^first-person_view$
```

### lighting.csv
```
^sunlight$|^backlighting$|^sunbeam$|^moonlight$|^chiaroscuro$
^silhouette$|^cinematic_lighting$|^soft_light$|^harsh_light$|^lens_flare$
^fog$|^rain$|^snow$|^sparkle$|^glowing$|^neon_lights$|^dark_environment$
^rim_lighting$|^light_particles$|^against_light$|^god_rays$
^night$|^day$|^sunset$|^sunrise$|^dusk$|^dawn$|^twilight$
^light_rays$|^crepuscular_rays$
```

### scenes.csv
```
^bedroom$|^classroom$|^bathroom$|^living_room$|^kitchen$
^outdoors$|^indoors$|^beach$|^city$|^rooftop$|^school$|^office$
^park$|^street$|^forest$|^garden$|^pool$|^train$|^bus$|^car$
^cafe$|^restaurant$|^library$|^hospital$|^hotel$|^temple$|^shrine$
^building$|^room$|^doorway$|^window$|^balcony$|^stairs$
^sky$|^cloud|^ocean$|^sea$|^river$|^lake$|^mountain$
^field$|^meadow$|^desert$|^snowscape$|^underwater$
_room$|_shop$|_store$|_station$|_school$|_building$
```

### objects.csv
```
^sword$|^gun$|^weapon$|^shield$|^knife$|^spear$|^bow$|^arrow$
^book$|^phone$|^phone$|^food$|^drink$|^cup$|^plate$|^fork$|^spoon$
^flower$|^microphone$|^camera$|^bag$|^backpack$|^umbrella$
^musical_instrument$|^guitar$|^piano$|^violin$
^chair$|^table$|^desk$|^bed$|^couch$|^sofa$
^pillow$|^blanket$|^mirror$|^lamp$|^candle$
^ball$|^doll$|^teddy_bear$|^toy$
^computer$|^laptop$|^keyboard$|^mouse$|^screen$|^monitor$
^(holding_|^with_)
```

### style.csv
```
^monochrome$|^greyscale$|^sketch$|^lineart$|^watercolor|^oil_painting
^absurdres$|^highres$|^lowres$|^bad_id$|^tagme$
^simple_background$|^white_background$|^grey_background$|^transparent_background$
^gradient_background$|^simple_shading$|^flat_color$
^artist_name$|^signature$|^watermark$|^dated$|^copyright_notice$
^photorealistic$|^realistic$|^3d$|^2d$|^anime$|^cartoon$|^manga$
^comic$|^chibi$|^pixel_art$|^vector$
^official_art$|^fanart$|^doujinshi$
```

### actions.csv
```
^holding$|^carrying$|^eating$|^drinking$|^reading$|^writing$|^drawing$
^running$|^walking$|^jumping$|^dancing$|^flying$|^swimming$|^climbing$
^fighting$|^punching$|^kicking$|^grabbing$|^pulling$|^pushing$
^hugging$|^kissing$|^touching$|^caressing$|^stroking$
^sleeping$|^resting$|^waiting$|^hiding$|^peeking$
^pointing$|^waving$|^saluting$|^bowing$
^lifting$|^throwing$|^catching$|^dropping$
^opening$|^closing$|^pouring$|^sweeping$
^taking_photo$|^using_phone$|^typing$|^playing$
^singing$|^speaking$|^shouting$|^whispering$
^cooking$|^cleaning$|^washing$
```

### sex_acts.csv
```
^sex$|^anal$|^vaginal$|^fellatio$|^cunnilingus$|^irrumatio$
^paizuri$|^footjob$|^handjob$|^masturbation$|^fingering$
^missionary$|^cowgirl|^doggystyle$|^spooning$|^standing_sex$
^threesome$|^gangbang$|^group_sex$|^foursome$|^orgy$
^ahegao$|^cum$|^ejaculation$|^creampie$|^bukkake$|^facial$
^tentacle_sex$|^monster_sex$|^machine_sex$
^bondage$|^bdsm$|^restrained$|^gagged$|^blindfold$
^rape$|^molestation$|^groping$|^forced$
_dildo$|^vibrator$|^sex_toy$|^condom$
^deepthroat$|^facesitting$|^69_position$
^from_behind_position$|^doggystyle$|^reverse_cowgirl$
^double_penetration$|^triple_penetration$
^exhibitionism$|^voyeurism$|^public_sex$
```

### body_traits.csv
```
_hair$|^hair_|_hair_     # hair color, hair style, hair ornament EXCLUDED
_eyes$|^eye_             # eye color
_skin$|^dark_skin$|^pale_skin$|^tan$|_tan$
^small_breasts$|^medium_breasts$|^large_breasts$|^huge_breasts$|^gigantic_breasts$
^muscular$|^athletic$|^slim$|^chubby$|^plump$|^fat$
^tall$|^short$|^petite$
^ahoge$|^freckles$|^mole$|^scar$|^tattoo$|_tattoo$
^fangs$|^sharp_teeth$|^pointy_ears$|^elf_ears$|^cat_ears$|^animal_ears$
^(blonde|brown|black|red|blue|green|pink|purple|white|grey|silver|orange)_hair$
^(blue|brown|green|red|yellow|purple|pink|black|grey|white|heterochromia)_eyes$
^multicolored_hair$|^two-tone_hair$|^streaked_hair$
^very_long_hair$|^short_hair$|^medium_hair$|^long_hair$
^(twintails|ponytail|braid|bun|sidelocks|bangs|ahoge|hair_between_eyes)$
```

### text_features.csv
```
^speech_bubble$|^thought_bubble$|^scream_bubble$
^english_text$|^japanese_text$|^chinese_text$
^signature$|^watermark$|^twitter_username$|^pixiv_id$
^translation_request$|^tagme$|^bad_id$|^commentary_request$
^dialogue$|^monologue$|^onomatopoeia$|^sfx$
^text_focus$|^screen$|^ui$
```

### audio_features.csv
```
^sfx$|^sound_effects$|^onomatopoeia$|^sound$
```

---

## 五、自动化分类脚本

见附录 A（独立文件 `danbooru_tags/scripts/categorize.sh`）。

脚本功能：
1. 读取 `danbooru_general.csv`
2. 对每行按第四章的正则表逐规则匹配
3. 写入对应的 `categorized/{category}.csv`（保持原 CSV 格式）
4. 每条标签可以写入多个分类（允许重合）
5. 未被任何规则匹配的写入 `other.csv`
6. 输出统计报告：每类数量、other 数量、other 占总数的比例

---

## 六、验收标准

| 指标 | 目标 | 验证方法 |
|------|------|---------|
| 分类覆盖率 | other.csv < 2,000 (8%) | `wc -l "$SKILL_TAGS/other.csv"` |
| 核心分类准确率 | >95% (poses/expressions/composition/lighting) | 每类抽查 top-100 + 随机 50 |
| 非核心分类准确率 | >90% | 每类抽查 top-50 + 随机 30 |
| 标签总数 | ≥ 24,317（允许重合导致增加） | 16 个文件行数之和 |
| CSV 格式完整性 | 每行保持 `tag,category,post_count,"aliases"` | 抽样 `head -5` 每文件 |
| 无空行/无重复 | 不含空行，UTF-8 编码，LF 换行 | `file "$SKILL_TAGS"/*.csv` |
| validate_tags.sh 兼容 | categorized mode 正常运行 | `echo "smile, sitting, sunlight" \| bash validate_tags.sh` |

---

## 七、注意事项

1. **允许标签重合**：一条标签可以归入多个子类。16 个子文件总行数会大于 24,317。
2. **按首要功能归类**：如 `holding_weapon` 首要功能是动作，归 actions 而非 objects。
3. **性行为标签独立**：`sex_acts.csv` 单独存放，避免与 `poses.csv` 和 `actions.csv` 混淆。
4. **hair/eye 颜色**：全部归入 `body_traits.csv`，不单独设文件。
5. **低频标签(<100)**：允许一定比例的误分类，人工复核只查 1%。
6. **分类脚本可重复运行**：修改正则后重新运行，产出覆盖到 skill `tag-library/categorized/`。
7. **原 `danbooru_general.csv` 不动**：分类后的文件写入 skill 目录，项目原文件保持原样。

---

## 附录 A：自动分类脚本骨架

保存为 `danbooru_tags/scripts/categorize.sh`：

```bash
#!/bin/bash
# categorize.sh — 将 danbooru_general.csv 按子类拆分为分类标签库
# 用法: bash categorize.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TAGS_DIR="$(dirname "$SCRIPT_DIR")"
INPUT="$TAGS_DIR/danbooru_general.csv"
# 输出到 skill 自带标签库，随 skill 迁移
OUTPUT_DIR="$HOME/.claude/skills/tag-crafter/tag-library/categorized"

# 清空旧产出
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# 分类规则数组（按优先级排序，先匹配的优先）
# 格式：文件名|正则模式
# 注意：每条标签可命中多条规则（允许重合）

# 为每个分类创建临时文件
declare -A FILES
CATEGORIES=(subjects body_parts clothing poses expressions composition
            lighting scenes objects style actions sex_acts body_traits
            text_features audio_features other)

for cat in "${CATEGORIES[@]}"; do
  touch "$OUTPUT_DIR/$cat.csv"
done

# 逐行处理
TOTAL=0
MATCHED=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  TOTAL=$((TOTAL + 1))
  tag=$(echo "$line" | cut -d',' -f1)

  HIT=0

  # === 分类规则（按优先级） ===
  # 每条规则：if tag matches regex → append to category file

  # subjects (主体/数量)
  if echo "$tag" | grep -qiE '^(solo|solo_focus|no_humans|[0-9]+girls?|[0-9]+boys?|[0-9]+others?|multiple_girls|multiple_boys|male_focus|female_focus)$'; then
    echo "$line" >> "$OUTPUT_DIR/subjects.csv"
    HIT=1
  fi

  # 继续定义所有规则...
  # (完整规则见第四章的正则表)

  # 如果未被任何规则命中，归入 other
  if [ "$HIT" -eq 0 ]; then
    echo "$line" >> "$OUTPUT_DIR/other.csv"
  else
    MATCHED=$((MATCHED + 1))
  fi

  # 进度显示
  if [ $((TOTAL % 1000)) -eq 0 ]; then
    echo "Processing... $TOTAL / 24317"
  fi
done < "$INPUT"

# 统计报告
echo ""
echo "=== Categorization Report ==="
echo "Total tags: $TOTAL"
echo "Matched: $MATCHED"
echo "Other: $(wc -l < "$OUTPUT_DIR/other.csv")"
echo ""
for cat in "${CATEGORIES[@]}"; do
  count=$(wc -l < "$OUTPUT_DIR/$cat.csv")
  if [ "$count" -gt 0 ]; then
    echo "  $cat: $count"
  fi
done
```

> **注意：** 完整脚本需补全所有分类的正则规则（见第四章）。上述骨架展示了结构，实际运行前需将 16 类正则全部填入。

---

## 附录 B：分类完成后 tag-crafter 联动更新

分类库就绪后，需要更新以下文件：

### B1. SKILL.md — 更新本地标签库接口描述

`~/.claude/skills/tag-crafter/SKILL.md` 第 7 节，将"未来接口"改为"当前状态"。

### B2. validate_tags.sh — guess_category() 函数

将正则与分类脚本保持一致（复制第四章的正则表）。

### B3. 新增：references/tag-categories.json

```json
{
  "version": "1.0",
  "source": "BetaDoggo/danbooru-tag-list (2024-12-10)",
  "categories": {
    "subjects": {"file": "subjects.csv", "description": "主体数量/性别"},
    "body_parts": {"file": "body_parts.csv", "description": "身体部位"},
    "clothing": {"file": "clothing.csv", "description": "服装/鞋袜/配饰"},
    "poses": {"file": "poses.csv", "description": "姿势/体态"},
    "expressions": {"file": "expressions.csv", "description": "表情/眼神/嘴部"},
    "composition": {"file": "composition.csv", "description": "构图/镜头/视角"},
    "lighting": {"file": "lighting.csv", "description": "光线/氛围/天气"},
    "scenes": {"file": "scenes.csv", "description": "场景/地点/环境"},
    "objects": {"file": "objects.csv", "description": "道具/物品/武器"},
    "style": {"file": "style.csv", "description": "风格/介质/质量"},
    "actions": {"file": "actions.csv", "description": "动作/行为"},
    "sex_acts": {"file": "sex_acts.csv", "description": "性行为标签"},
    "body_traits": {"file": "body_traits.csv", "description": "体型/颜色/身体特征"},
    "text_features": {"file": "text_features.csv", "description": "文字/气泡/UI"},
    "audio_features": {"file": "audio_features.csv", "description": "音效文字/拟声词"},
    "other": {"file": "other.csv", "description": "未分类标签"}
  }
}
```

---

## 附录 C：文件清单

分类完成后的完整目录结构：

```
~/.claude/skills/tag-crafter/tag-library/     ← 分类产出（随 skill 迁移）
├── README.md
├── _stats.json
└── categorized/
    ├── README.md
    ├── subjects.csv                  ~30 条
    ├── body_parts.csv                ~400 条
    ├── body_traits.csv               ~400 条
    ├── clothing.csv                  ~1,200 条
    ├── poses.csv                     ~200 条
    ├── expressions.csv               ~150 条
    ├── actions.csv                   ~350 条
    ├── composition.csv               ~120 条
    ├── lighting.csv                  ~180 条
    ├── scenes.csv                    ~500 条
    ├── objects.csv                   ~800 条
    ├── style.csv                     ~150 条
    ├── sex_acts.csv                  ~400 条
    ├── text_features.csv             ~60 条
    ├── audio_features.csv            ~30 条
    └── other.csv                     ~500-2,000 条

danbooru_tags/                                ← 数据源（不动）
├── TASKBOOK.md
├── README.md
├── danbooru_general.csv              ← 原始全量
├── danbooru_full.csv
├── danbooru_artist.csv
├── danbooru_character.csv
├── danbooru_copyright.csv
├── danbooru_meta.csv
└── scripts/
    └── categorize.sh                 ← 分类脚本
```
