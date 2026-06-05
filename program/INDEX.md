# program/ — 工具脚本索引

本目录存放与 wildcard 文件维护相关的可复用脚本。每次修改后可运行验证清单（见 CLAUDE.md §3）。

## 索引

| 文件 | 用途 | 用法 |
|------|------|------|
| `series_index.py` | 从 4 个系列文件重建角色题材索引 series_index.txt（按系列分组，含来源文件和行号） | `python series_index.py` |
| `rebuild_characters.py` | 从 clothed/ + bare/ 权威源重建所有派生角色文件（系列文件 + curated 三版） | `python rebuild_characters.py` 或 `--apply` |
| `verify_sync.py` | 验证/修复 NSFW 姿势子文件夹与主文件一致性（行级哈希+孤儿检测+健康检查） | `python verify_sync.py` 或 `--fix` |
| `pose_index.py` | 生成 merged 全集行号索引，含 Sex 条目→子文件夹映射 | `python pose_index.py` 或 `--check` |
| `strip_clothing.py` | 衣物标签判断库（`is_clothing_tag()`），被 `add_bare_fallback.py` import | `from strip_clothing import is_clothing_tag` |
| `add_clothing_fallback.py` | [一次性] 批量为 bare-only 角色追加标志性衣物标签到 clothed/ | `python add_clothing_fallback.py` 或 `--apply` |
| `add_bare_fallback.py` | [一次性] 批量为 clothed-only 角色剥离衣物生成 bare 条目 | `python add_bare_fallback.py` 或 `--apply` |
| `delete_character.py` | 按角色名从所有 wildcard 文件中删除角色（含子文件夹和主文件） | `python delete_character.py <pattern>` 或 `--yes <pattern>` |
| `edit_entry.py` | 在 NSFW 姿势子文件夹中查找/替换/删除条目，可选重建主文件 | `python edit_entry.py --find <pattern> [--replace <new>] [--delete] [--sync]` |
| `nsfw_xref.py` | NSFW 子文件夹交叉引用：构建/检查/修复重复条目（追踪跨文件相同条目同步） | `python nsfw_xref.py --build` / `--check` / `--sync` / `--fix-bootstrap` |
| `split_clothing.py` | [已弃用] 按衣物标签将平面角色文件拆分为 clothed/ 和 bare/ | — |
| `sync_clothed_bare.py` | [已弃用] 确保角色的 clothed/bare 双向对称 | — |

## 约定

- 每个脚本开头必须有注释说明用途、用法、已知局限
- 脚本应可直接运行，不依赖本项目外的文件（Danbooru CSV 除外）
- 修改脚本后需同步更新本索引
