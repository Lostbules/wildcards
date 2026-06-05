#!/usr/bin/env python3
"""
split_clothing.py — 将角色文件按「有无衣物标签」拆分为两个文件

用途：
  读取 characters_categories/*.txt，判断每条目是否包含衣物标签，
  分别输出到 clothed/ 和 bare/ 子目录。

用法：
  python split_clothing.py <input_dir>

  示例：
  python split_clothing.py characters_categories

输出：
  <input_dir>/clothed/<原文件名>.txt  — 含衣物标签的条目
  <input_dir>/bare/<原文件名>.txt      — 不含衣物标签的条目

依赖：
  复用 program/strip_clothing.py 中的 is_clothing_tag() 判断逻辑。
"""

import sys
import os
import re

# 将 program/ 加入路径以复用 strip_clothing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strip_clothing import is_clothing_tag


def split_file(filepath, clothed_dir, bare_dir):
    """读取文件，按有无衣物标签拆分为两个文件。"""
    basename = os.path.basename(filepath)
    clothed_path = os.path.join(clothed_dir, basename)
    bare_path = os.path.join(bare_dir, basename)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    clothed_lines = []
    bare_lines = []
    empty_count = 0

    for line in lines:
        if not line.strip():
            empty_count += 1
            continue

        tags = [t.strip() for t in line.split(',')]
        if len(tags) < 3:
            # 过短的条目（无标签）归入 bare
            bare_lines.append(line)
            continue

        name = tags[0]
        series = tags[1]
        rest = tags[2:]

        has_clothing = any(is_clothing_tag(t) for t in rest)

        if has_clothing:
            clothed_lines.append(line)
        else:
            bare_lines.append(line)

    # 写入
    os.makedirs(clothed_dir, exist_ok=True)
    os.makedirs(bare_dir, exist_ok=True)

    with open(clothed_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(clothed_lines) + '\n')

    with open(bare_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(bare_lines) + '\n')

    return len(clothed_lines), len(bare_lines), empty_count


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python split_clothing.py <input_dir>", file=sys.stderr)
        sys.exit(1)

    input_dir = sys.argv[1]
    clothed_dir = os.path.join(input_dir, 'clothed')
    bare_dir = os.path.join(input_dir, 'bare')

    txt_files = sorted([
        f for f in os.listdir(input_dir)
        if f.endswith('.txt') and os.path.isfile(os.path.join(input_dir, f))
    ])

    if not txt_files:
        print("No .txt files found in", input_dir, file=sys.stderr)
        sys.exit(1)

    total_clothed = 0
    total_bare = 0
    total_empty = 0

    for fname in txt_files:
        fpath = os.path.join(input_dir, fname)
        c, b, e = split_file(fpath, clothed_dir, bare_dir)
        total_clothed += c
        total_bare += b
        total_empty += e
        print(f"  {fname}: {c} clothed + {b} bare (+ {e} empty)")

    print(f"\nTotal: {total_clothed} clothed + {total_bare} bare (+ {total_empty} empty)")
    print(f"Output: {clothed_dir}/  and  {bare_dir}/")
