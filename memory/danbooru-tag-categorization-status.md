---
name: danbooru-tag-categorization-status
description: Status and findings from the Danbooru general tags categorization project (2026-06-04)
metadata:
  type: project
---

# Danbooru Tag Categorization — 当前状态

**日期**: 2026-06-04
**任务书**: `wildcards/danbooru_tags/TASKBOOK.md`
**分类脚本**: `wildcards/danbooru_tags/scripts/categorize.sh`
**产出**: `~/.claude/skills/tag-crafter/tag-library/categorized/`

## 完成状态

- ✅ 阶段 A: 自动分类脚本 (categorize.sh v4) — 完成
- ✅ 阶段 B: P0/P1 分类审查 — 完成
- ✅ 阶段 C: 批量修正 — 完成（迭代改进）
- ✅ 阶段 D: README + _stats.json + tag-categories.json — 完成
- ⏳ 覆盖率提升 — 待后续迭代

## 核心指标

| 指标 | 当前 | 目标 | 状态 |
|------|------|------|------|
| 自动命中率 | 57.4% (13,946/24,317) | >92% | ❌ 待改进 |
| other.csv | 10,371 | <2,000 | ❌ 待改进 |
| P0 准确率 | ~90-95% | >95% | ⚠️ 接近 |
| CSV 格式 | ✅ 无误 | 无空行/坏行 | ✅ |
| 标签总数 | 28,688 (含重叠) | ≥24,317 | ✅ |

## 分类方法

- 组件词匹配 (underscore-split) — 将标签拆为单词后查词典
- 后缀规则 — `_hair` → body_traits, `_dress` → clothing 等
- 末词归类 (第二遍扫描) — 对未匹配标签用最后组件词推断类别
- 精确全词匹配 — 常见组合标签直接匹配

## 已知问题

1. **修饰词误匹配**: `dark`, `bright`, `shiny`, `wet` 在 D_LIGHT 导致 body_traits 标签误归入 lighting
2. **复合词漏报**: 如 `crop_top` (两个通用词组合成服装术语) 
3. **`facial` 关键词语义歧义**: `facial_hair`/`facial_mark` (面部) 被误归入 sex_acts (颜射)
4. **body_parts 过度重叠**: `blue_eyes`, `large_breasts`, `open_mouth` 等应优归类为 body_traits/expressions

## 下一步改进方向

1. 扩展 D_CLOTH, D_BODYP, D_BT_EXACT 词典
2. 从 D_LIGHT 移除通用修饰词（dark, bright, shiny 等）
3. 从 D_SEX 移除歧义词（facial → 改用更精确模式）
4. 对 other.csv top 500 标签进行人工归类并加入词典

**Why**: 任务书要求将 Danbooru General 24,317 条标签从扁平 CSV 拆分为 16 个子类。已完成基础自动化，覆盖率 57.4%，P0 分类质量可用但覆盖率需后续迭代提升。

**How to apply**: 运行 `bash wildcards/danbooru_tags/scripts/categorize.sh` 可重新生成全部分类文件。修改脚本中的关键词列表后可增量改进覆盖率。
