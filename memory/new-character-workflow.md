---
name: new-character-workflow
description: 新建角色条目的标准流程：先 clothed 后 bare
metadata:
  type: feedback
---

制作新角色条目时，除非用户有特殊要求，否则先做 clothed 版本（含完整衣物/装备标签），bare 版本由 clothed 删除衣物标签得到，只保留发色、瞳色、身材、丝袜等身体描述标签。

**Why:** 避免凭空构造 bare 条目导致与 clothed 版本不一致。clothed 是完整版，bare 是去衣派生版，确保两条目共享同一套外貌标签。

**How to apply:** 每次新增角色皮肤时，先在 `characters_categories/clothed/` 对应系列文件末尾追加完整条目，然后手动删除衣物/装备/手持物标签，追加到 `characters_categories/bare/` 对应文件。最后运行 `python program/rebuild_characters.py --apply` 同步。
