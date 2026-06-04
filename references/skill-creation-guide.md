# Claude Code Skill 创建指南

> 来源：Claude Code 官方文档、Agent Skills 标准规范、skills.sh
> 整理日期：2026-06-04

---

## Skill 目录结构

```
skill-name/
├── SKILL.md           # 必需：YAML frontmatter + Markdown 指令
├── references/        # 可选：详细参考文档（按需加载）
│   └── REFERENCE.md
├── scripts/           # 可选：可执行脚本（Python/Bash/JS）
│   └── validate.sh
└── assets/            # 可选：模板、图片、数据文件
    └── template.md
```

**关键规则：**
- 只有 `SKILL.md` 必需
- `SKILL.md` 控制在 500 行以内，详细内容放 `references/`
- 目录名 = Skill 名，也是 `/` 调用名
- 仅限小写字母、数字、连字符

---

## SKILL.md Frontmatter 完整字段

```yaml
---
name: skill-name                   # 必需，1-64字符，小写字母/数字/连字符
description: 描述（≤200字最佳）     # 必需，用于自动触发匹配
when_to_use: 额外触发短语          # 可选，追加到 description 用于匹配
argument-hint: [参数提示]          # 可选，自动补全提示
arguments: [arg1, arg2]            # 可选，命名位置参数
disable-model-invocation: false    # true = 仅用户可手动调用 /skill-name
user-invocable: true               # false = 从 / 菜单隐藏（仅 Claude 可自动触发）
allowed-tools: Bash(gh *) Bash(npm *)  # 预授权工具
disallowed-tools: WebSearch        # 禁用工具
model: opus                        # 模型覆盖
effort: high                       # 努力级别：low/medium/high/xhigh/max
context: fork                      # fork = 在隔离子代理中运行
agent: Plan                        # 子代理类型
shell: bash                        # bash 或 powershell
paths: ["*.txt", "wildcards/**"]  # 限制自动激活的文件范围
compatibility: environment         # 环境要求
license: MIT                       # 许可证
metadata:                          # 任意键值对
  category: comfyui
---
```

---

## Skill 存放位置

| 作用域 | 路径 | 可见范围 |
|--------|------|---------|
| 个人全局 | `~/.claude/skills/<name>/SKILL.md` | 所有项目 |
| 项目级 | `.claude/skills/<name>/SKILL.md` | 当前项目（可 Git 共享） |
| 企业级 | 托管配置 | 整个组织 |

---

## Skill 初始化流程（手动）

```bash
# 1. 创建目录
mkdir -p ~/.claude/skills/my-skill/references
mkdir -p ~/.claude/skills/my-skill/scripts

# 2. 创建 SKILL.md（写入 frontmatter + 内容）

# 3. 测试调用
# 在 Claude Code 中输入：/my-skill

# 4. 迭代调优
# - 如果自动触发过频繁：收紧 description
# - 如果未自动触发：在 description 中增加触发短语
# - 从错误中学习，将注意事项写入 SKILL.md
```

---

## Skill 能力边界

### 可以做的（通过 Agent 工具）
- 执行 Shell 命令
- 读写文件
- 调用 Web API（curl/gh/MCP）
- 引用 `scripts/` 中的脚本
- 使用 `!`command`` 动态注入上下文
- Fork 为子代理运行

### 不能做的
- 不能直接执行代码（依赖 Agent 的工具集）
- 不能有自己的运行时环境
- 不能动态安装包（需预装）
- 不能定义新工具（只能指示 Agent 使用已有工具）

---

## 最佳实践

1. **description ≤ 200 字**：确保自动触发可靠
2. **SKILL.md ≤ 500 行**：详细参考放 `references/`
3. **"先产出，后询问"**：首先生成输出，而非暂停等用户输入
4. **写入触发短语**：description 中使用用户可能说的自然语言
5. **写 Agent 不知道的内容**：Skill 的价值在于提供 Agent 不具备的领域知识
6. **破坏性操作用 `disable-model-invocation: true`**：防止误触发
7. **使用 `allowed-tools` 预授权**：减少运行时权限提示
