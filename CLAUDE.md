# ComfyUI Impact Pack — Wildcard 项目文档

## 文档维护规则

**每次更新本文件时，必须：**
1. 通读全文，确认新增内容不与其他节重复
2. 若新增内容属于已有话题，合并到对应节而非追加新节
3. 检查是否有可合并的近义描述，有机优化结构
4. 删除已被新信息取代的过时内容

---

## 1. 项目概述

### 文件格式

- 位置：`wildcards/` 目录下的 `.txt` 文件
- 每行一个条目，格式：`标签1, 标签2, 标签3, ...`
- 系统按行随机抽取（不依赖行号，行号仅用于 `grep -n` 定位）
- 编码：UTF-8

### 标签语法

| 语法 | 含义 | 示例 |
|------|------|------|
| `(tag:权重)` | 精确权重（推荐） | `(nipples:1.2)` |
| `((tag))` | 加强权重（≈×1.21） | `((feet))` |
| `[tag]` | 减弱权重（×0.9） | `[hair grab]` |
| `<lora:模型名:权重>` | 引用 LoRA | `<lora:VRP:0.8>` |
| `BREAK` | 分隔条件化 | 需 `ImpactWildcardEncode` 节点 |

### 项目结构

```
wildcards/
├── XL-pose_SFW_clean.txt          # SFW 姿势（309行）
├── XL-pose_NSFW_solo-nude.txt     # 单人裸体姿势（212行）
├── XL-pose_NSFW_sex.txt           # 性行为姿势（242行，去重后）
├── XL-pose_merged.txt             # 合并版（763行 = SFW+solo-nude+sex）
├── characters_curated.txt         # 角色通配符（精选后，563行）
├── series_index.txt               # 角色题材索引（含决策标记）
├── CLAUDE.md                      # 本文档
├── .gitignore                     # Git 忽略规则
├── backups/                       # 备份归档
├── lora/                          # LoRA 清单
├── samples/                       # 示例文件
├── danbooru_tags/                 # Danbooru 标签库
├── NSFW_sex_categories/           # 性行为分类快照（17类）
├── characters_categories/         # 角色分类快照（4系列）
└── references/                    # tag-crafter skill 参考文档
```

### Git 仓库

- 仓库：https://github.com/Lostbules/wildcards
- 本目录为独立 Git 仓库（非 ComfyUI-Impact-Pack 子仓库）
- 远程：`origin` → `https://github.com/Lostbules/wildcards`
- 分支：`master`
- 推送流程：
  ```bash
  git add -A
  git commit -m "改动说明"
  git push
  ```

---

## 2. 工具偏好与通用原则

### 工具选择

| 场景 | 工具 | 原因 |
|------|------|------|
| 文本处理/过滤 | `awk` | 一次遍历，避免 bash `while read` 循环 |
| 固定字符串匹配 | `grep -F` | 避免正则转义陷阱 |
| 正则搜索 | `grep -E` | 优先于 `grep -P`（部分环境 locale 问题） |
| 轻量修改 | `sed -i` | 索引标记等 |
| 重量级过滤 | `awk` | 多条件、白名单场景 |
| 字符诊断 | `od -c` / `cat -A` | 查看实际字节和隐藏字符 |
| 行数变化 | `wc -l` | 操作前后对比 |

### 搜索技巧

- `grep -w` — 精确匹配单词，避免子串误伤（`changing` ≠ `hanging`）
- `grep -c` — 先统计总量，再决定是否 `grep -n` 看详情
- `grep -iE` — 多模式正则（`grep -iE 'foo|bar'`）
- 搜索结果出来后人工确认，不看计数就下结论（`saki` 会匹配到 `misaki`）

### 转义陷阱

- 文件中有 `\` 时（如 LoRA 路径 `DZ\LoRAName`），先用 `tr '\\' '/'` 转换再处理
- `sed` 中写 `\\` 在 Windows bash 下容易出错，改用 `tr` + `sed` 分步处理
- `grep -F` 匹配字面量反斜杠+括号：`grep -F 'atelier \(series\)'`

---

## 3. 安全编辑规范

### 删除行

- **从高行号到低行号删除**，避免行号位移
- 每轮前创建 `.bak`：`sed -i.bak '103d;97d;1d' file.txt`
- 事后 `grep` 验证目标清零

### 备份管理

- 命名格式：`[原文件名]_[描述]_[YYYYMMDD-HHMM].bak`
- 描述用中文标注阶段：`原始备份`、`第一轮清理`、`最终清理版`
- 时间戳使用文件修改时间（UTC，精确到分钟）
- `sed -i.bak` 多次执行会产生 `.bak`、`.bak2`、`.bak3`……需根据时间戳和文件大小还原阶段
- 备份统一存放 `backups/`，可随时恢复：`cp backups/xxx.bak ../xxx.txt`

### 文件修改后检查

每次修改完成后，运行验证清单：

```bash
# 格式完整性
grep -c '^[^,]\+$' file.txt    # 无逗号孤立行（应为 0）
grep -c '^$' file.txt           # 空行（应为 0）

# 已删内容确认（逐项应为 0，非零则检查是否子串误匹配）
for tag in "deleted_1" "deleted_2"; do
  count=$(grep -ci "$tag" file.txt)
  [ "$count" -gt 0 ] && grep -in "$tag" file.txt
done
```

---

## 4. 批量编辑模式

### 模式 A：索引驱动的四阶段审查

适用于有 `name, series, tags...` 结构的角色文件。**核心思路：先建索引全盘审查，统一标记，最后一次执行。**

**阶段 1 — 建索引**

```bash
awk -F',' '{
  name=$1; gsub(/^ */,"",name)
  series=$2; gsub(/^ */,"",series)
  if(series=="") series="(no tag)"
  print series"|"NR"|"name
}' file.txt | sort -t'|' -k1,1 -k2,2n | awk -F'|' '
BEGIN{prev="__FIRST__";cnt=0}
{s=$1;ln=$2;nm=$3; if(s!=prev){if(prev!="__FIRST__")printf "## [ ] %-55s [%d]\n\n",prev,cnt;prev=s;cnt=0} cnt++;printf "  L%-5d %s\n",ln,nm}
END{printf "## [ ] %-55s [%d]\n\n",prev,cnt}
' > series_index.txt
```

**阶段 2 — 审查标记**

按条目数从多到少分批呈现。`[KEEP]` / `[DEL]` 标记：

- 大题材（10+条目）：逐题材呈现角色表
- 中型（3-9）：多题材合并一表加速决策
- 小题材（1-2）：用户一次性点名保留，其余默认删除

关键原则：属性标签（hair/eyes/clothing）不是题材；孤立无逗号行是遗留标题；小众题材向删除倾斜。

**阶段 3 — awk 白名单一次性过滤**

```bash
grep '^## \[KEEP\]' series_index.txt | sed 's/^## \[KEEP\] //;s/ *\[[0-9]*\]$//' > _keep_tags.txt
cp file.txt file.txt.bak
awk -F',' '
BEGIN { while ((getline < "_keep_tags.txt") > 0) { gsub(/^ +| +$/, "", $0); if ($0 != "") keep[$0] = 1 } }
{ series = $2; gsub(/^ +/, "", series); if (series in keep) print }
' file.txt.bak > file_new.txt
mv file_new.txt file.txt && rm _keep_tags.txt
```

优于逐次 `grep -v`：一次遍历完成所有过滤，白名单模式天然排除遗漏。

**阶段 4 — 验证与重建索引**

```bash
grep -c '^[^,]\+$' file.txt  # 孤立行应为 0
wc -l file.txt                # 应与索引条目数一致
# 抽样确认保留系列数量，检查 grep 实际输出排除子串误匹配
```

### 模式 B：grep -v 批量删除 + 选择性恢复

适用于待删除条目散布、需保留少数特定条目的场景：

```bash
cp file.txt file.txt.bak
grep -vi 'series_tag' file.txt > file_tmp.txt        # 全删
grep -i 'keeper.*series_tag' file.txt.bak >> file_tmp.txt  # 选择性恢复
mv file_tmp.txt file.txt
```

注意：**必须先删后恢复**，否则造成重复；多个系列分步执行，每步前新建备份。

### 模式 C：平铺标签的多标签分类

适用于无 `name, series` 结构的平铺标签文件，支持一条目归入多个类别：

```bash
awk -F',' '
{
  line = $0
  if (line ~ /keyword_a/)     print line >> "cat_a.txt"
  if (line ~ /keyword_b/)     print line >> "cat_b.txt"
  # 每个 if 独立判断，不互斥
  if (!(line ~ /keyword_a|keyword_b/)) print line >> "other.txt"
}' file.txt
```

### 模式 D：平铺文件的二分拆分

```bash
grep -iE 'keyword1|keyword2' file.txt > file_type_a.txt
grep -viE 'keyword1|keyword2' file.txt > file_type_b.txt
echo "$(wc -l < file_type_a.txt) + $(wc -l < file_type_b.txt) = $(wc -l < file.txt)"
```

### 按系列标签快速摸底

```bash
cat file.txt | cut -f2 | cut -d',' -f2 | sed 's/^ *//' | sort | uniq -c | sort -rn
```

---

## 5. 数据增强

### 通用原则

- 新增条目追加到文件末尾，系统按行随机抽取不依赖顺序
- 每次变体变化 **1~3 个标签**，保持骨架不变
- 标签必须从已有文件中验证存在（`grep -c 'tag' file.txt`），不凭空创造
- 不同条目间的变体比例保持均衡

### 场景 × 属性矩阵法

用于系统化扩充某类内容：

1. **摸底盘**：列出目标类别所有现有条目的 {场景} 和 {属性} 维度
2. **画矩阵**：以场景为行、属性为列，标记 ✅ 已有和 ❌ 空白
3. **分析缺口**：完全缺失的行/列 → 优先创建；稀疏格 → 按需补充
4. **分层创建**：
   - 第一层：Danbooru 经典场景（填补完全缺失的行/列）
   - 第二层：场景 × 属性混搭（填补空白格）
   - 第三层：角度/表情等细节变体

### 质量控制

**逻辑一致性**（加入前检查标签间是否存在矛盾）：

| 冲突类型 | 示例 | 修复 |
|----------|------|------|
| 物理矛盾 | `submerged` + `soles focus` | 改 `wet soles` |
| 空间矛盾 | `bathtub` + `two-footed footjob` | 换场景 |
| 情境矛盾 | `crowd` + `spread legs` + SFW | 删一个 |
| 姿势矛盾 | `m_legs` + footjob | 改 `legs together` |

**标签冗余**：同条目避免 `sleeping, asleep`；`train interior, train`；`changing room, clothing store, fitting room`。

**拼写检查**：`speed tines`→`speed lines`，`shinny`→`shiny`。

**表现力**：纯公式化变体（仅追加 1 个标签如 `phone`）视为弱表现力，建议重写。

### 近重复处理

- 定义：两条目共享 ≥80% 标签，仅 1~3 个属性有差异
- 策略：若变体标签更丰富 → 保留丰富版删精简版；仅场景不同 → 各自保留；同一属性已有 5+ 变体 → 精简

### Danbooru 标签参考

文件内标签不足时参考 Danbooru 体系。`danbooru_tags/danbooru_general.csv` 含 24,317 条 general 标签。校验命令：

```bash
# 批量校验标签是否在标准库中
for tag in $(cat _planned_tags.txt); do
  grep -ci "^$tag," danbooru_tags/danbooru_general.csv
done
```

常见的非标准→标准对照见 `references/standardization-fixups.md`（tag-crafter skill 内置）。

### 构图优先原则

每个新条目必须以视觉构图为骨架，叙事标签仅作辅助。每条至少包含：
- ≥1 个构图标签（camera angle / framing）
- ≥1 个光线标签（backlighting / sunbeam / moonlight / chiaroscuro）
- ≥1 个具体表情标签（非抽象情绪词，用 `biting` 不用 `embarrassed`）

详细构图配方见 `references/composition-recipes.md`（tag-crafter skill 内置）。

---

## 6. 文件维护

### 合并文件

```bash
cat fileB.txt >> fileA.txt   # 合并
wc -l fileA.txt               # 验证
cp fileB.txt backups/ && rm fileB.txt  # 归档后删除
```

### 多版本输出

```
项目输出/
├── file_type_a.txt      # 分离版 A
├── file_type_b.txt      # 分离版 B
└── file_merged.txt      # 合并版（A+B，随分离版更新重建）
```

### 合并版重建

```bash
cat XL-pose_SFW_clean.txt XL-pose_NSFW_solo-nude.txt XL-pose_NSFW_sex.txt > XL-pose_merged.txt
```

### 目录整理

每次大规模编辑后：

```bash
# 1. 清理散落的临时文件
find . -maxdepth 1 \( -name "*.bak*" -o -name "*_tmp*" \) -delete

# 2. 归档原始 .bak 到 backups/
mv *.bak backups/ 2>/dev/null

# 3. 验证一致性
echo "$(wc -l < XL-pose_SFW_clean.txt) + $(wc -l < XL-pose_NSFW_solo-nude.txt) + $(wc -l < XL-pose_NSFW_sex.txt) = $(wc -l < XL-pose_merged.txt)"
```

### 分类子文件同步（强制规则）

**核心原则：主文件和分类子文件必须始终保持双向同步。无论修改哪一方，都必须同步更新另一方。禁止只改一边。**

`NSFW_sex_categories/` 和 `characters_categories/` 等子目录是主文件的分类视图。

#### 主文件 → 子文件

主文件（`XL-pose_NSFW_sex.txt`、`characters_curated.txt`）修改后：

1. **删条目**：用 `grep -vE 'old_pattern'` 从对应分类文件移除过期条目
2. **增条目**：按分类规则将新条目追加到匹配的分类文件
3. **改条目**：先删旧版、再追加新版
4. `sort -u` 去重（仅删除完全字节相同的重复行）

#### 子文件 → 主文件

分类文件修改后（如调整归类），同样需要反查主文件是否需要同步。

#### 同步验证

每次修改后必须运行：

```bash
# 验证主文件所有条目都在分类中存在
awk 'BEGIN {
  cmd = "cat NSFW_sex_categories/*.txt"
  while ((cmd | getline) > 0) { if ($0 != "") cat[$0] = 1 }
  close(cmd)
  while ((getline < "XL-pose_NSFW_sex.txt") > 0) {
    if ($0 != "" && !($0 in cat)) { print "MISSING: " substr($0,1,80); missing++ }
  }
  print "Missing: " missing+0
}'

# 验证分类文件无孤儿条目（不在主文件中）
awk 'BEGIN {
  while ((getline < "XL-pose_NSFW_sex.txt") > 0) { src[$0] = 1 }
}
FNR==1 { fn=FILENAME }
{
  if ($0 != "" && !($0 in src)) { print "ORPHAN in " fn ": " substr($0,1,80); orphan++ }
}
END { print "Orphans: " orphan+0 }
' NSFW_sex_categories/*.txt

# 验证 merged 文件和分类总数一致
echo "$(wc -l < XL-pose_SFW_clean.txt) + $(wc -l < XL-pose_NSFW_solo-nude.txt) + $(wc -l < XL-pose_NSFW_sex.txt) = $(wc -l < XL-pose_merged.txt)"
```

#### 分类索引维护

`_INDEX.md` 记录了分类编号、名称和条数。分类文件变更后需同步更新索引中的条数和编号映射。

---

## 7. LoRA 管理

### 提取 LoRA 清单

```bash
grep -roh '<lora:[^>]*>' . --include="*.txt" | tr '\\' '/' | \
  sed 's/<lora://; s/>//; s/^DZ\///; s/:[0-9.]*$//' | sort -u
```

### 批量更新 LoRA 版本

```bash
# 先更新源文件，再重建 merged（merged 是 cat 拼接产物，直接改会被覆盖）
sed -i 's/lora-old-name/lora-new-name/g' XL-pose_SFW_clean.txt XL-pose_NSFW_solo-nude.txt XL-pose_NSFW_sex.txt
sed -i 's/lora-old-name/lora-new-name/g' lora/lora_list.txt
cat XL-pose_SFW_clean.txt XL-pose_NSFW_solo-nude.txt XL-pose_NSFW_sex.txt > XL-pose_merged.txt
grep -rc 'lora-old-name' --include="*.txt" . | grep -v 'backups/'  # 验证清零
```

注意：不更新 `backups/` 下的文件（备份保留历史状态）。

---

## 8. 角色与姿势管理

### 角色皮肤变体追加

原则：原条目不动；新皮肤基于最详细的已有条目创建，追加到文件末尾。

```
character_name, series_name, tag1, tag2, ...                    # 原条目（不动）
character_name (variant_name), series_name, tag1, tag2, ..., new_tag  # 新皮肤
```

---

## 9. 标签降级规范化

当需要统一 body part 尺寸级别时：

- `gigantic/huge/massive/giant/enormous/monster` → 降为 `large` 或不带尺寸修饰
- `large` 为允许的最大级别；`tiny/small` 不降级
- 同一行同时出现 `large` + 更大同义词时，删大的保留 `large`
- `huge` 可能修饰非目标对象（`huge ass`、`huge ahoge`），逐条确认

---

## 10. 网络问题排查

| 症状 | 原因 | 解决 |
|------|------|------|
| WebFetch "Unable to verify" | 预检 `claude.ai` 不通 | `settings.json` 设 `"skipWebFetchPreflight": true` |
| curl "Connection timed out" | Bash 沙箱拦截 | `settings.json` sandbox.network.allowedDomains 加目标域名 |
| 浏览器能访问但 CLI 不行 | 企业防火墙 | 用 WebSearch 或镜像域名替代 |

回退策略：WebSearch → 论坛帖 → GitHub Release 下载本地 CSV。

---

## 11. 外部工具

### tag-crafter Skill

`/tag-crafter` — 交互式生成带权重的 Danbooru 标签串，支持批量 wildcard 条目生成。

```
~/.claude/skills/tag-crafter/
├── SKILL.md
├── references/
│   ├── danbooru-tag-reference.md    # Danbooru 标签完整手册
│   ├── composition-recipes.md       # 六大构图配方
│   └── standardization-fixups.md    # 非标准→标准修正表
├── scripts/
│   ├── validate_tags.sh             # 标签标准化校验
│   └── diff_entries.sh              # 新条目去重检查
├── templates/
│   ├── wildcard-entry.txt
│   └── full-prompt.txt
└── tag-library/                     # 本地标签库（待构建分类版）
```

### Danbooru 标签库

本地库：`danbooru_tags/danbooru_general.csv`（24,317 条），来源 BetaDoggo/danbooru-tag-list (2024-12-10)。
