#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate-spl.py — SPL 剧本格式校验器（剧本医生的格式检查引擎）

用法:
    python validate-spl.py 剧本.md

按 references/spl-spec.md 逐项校验 SPL 剧本：
    frontmatter 必填项 / 场景标题三段式 / 镜头归属 / 角色提示-对白配对 /
    括号提示上下文 / 转场合法性 / 蒙太奇列表 / 动作段规范 / FADE OUT 收尾。

退出码: 0 全部通过 / 1 存在错误。错误按「行号 | 级别 | 问题 | 修法」输出。
"""
import sys
import re

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SLUG_RE = re.compile(r"^#\s+(INT\./EXT\.|I/E\.|INT/EXT|INT\.|EXT\.)\s+(.+?)\s*-\s*(.+?)\s*(?:\[(\d+)\])?$")
SHOT_RE = re.compile(r"^##\s+(.+)$")
TRANS_RE = re.compile(r"^>\s*(.+)$")
MONTAGE_RE = re.compile(r"^##\s+蒙太奇\s*(.*)$")
CHAR_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
PAREN_RE = re.compile(r"^（.+?）$")
OLIST_RE = re.compile(r"^\d+\.\s+(.+)$")

KNOWN_TRANSITIONS = {"FADE IN:", "CUT TO:", "SMASH CUT TO:", "DISSOLVE TO:",
                     "FADE OUT.", "FADE OUT", "MATCH CUT TO:", "JUMP CUT TO:"}
ALLOWED_META = {"title", "author", "type", "genre", "runtime",
                "logline", "controlling-idea", "structure"}
ALLOWED_TYPES = {"feature", "short", "series", "short-drama"}

ERRORS = []
WARNINGS = []
fade_out_seen = False


def err(ln, problem, fix):
    ERRORS.append((ln, "错误", problem, fix))


def warn(ln, problem, fix):
    WARNINGS.append((ln, "警告", problem, fix))


def validate_frontmatter(text):
    if not text.startswith("---"):
        err(1, "缺少 YAML frontmatter", "在文件开头添加 --- 元数据块，至少含 title")
        return {}, 1
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        err(1, "frontmatter 未闭合", "在元数据后补一行 ---")
        return {}, 1

    meta = {}
    for i, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            err(i, f"frontmatter 行格式错误：{line}", "应为「字段: 值」")
            continue
        k, _, v = line.partition(":")
        k = k.strip().lower()
        if k not in ALLOWED_META:
            warn(i, f"未知元数据字段：{k}", f"仅允许：{', '.join(sorted(ALLOWED_META))}")
            continue
        meta[k] = v.strip().strip('"\'')
    if "title" not in meta or not meta["title"]:
        err(1, "缺少必填字段 title", "添加 title: 剧本标题")
    if "type" in meta and meta["type"] not in ALLOWED_TYPES:
        warn(1, f"type 取值非法：{meta['type']}", f"允许：{', '.join(sorted(ALLOWED_TYPES))}")
    return meta, end + 2


def main():
    if len(sys.argv) != 2:
        print("用法：python validate-spl.py 剧本.md")
        sys.exit(1)
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"无法读取文件：{e}")
        sys.exit(1)

    global fade_out_seen
    meta, start = validate_frontmatter(text)
    lines = text.splitlines()

    in_montage = False
    expect_dialogue = False        # 期待对白（角色提示之后）
    last_was_dialogue = False
    seen_scene = False
    last_scene_no = 0

    for idx in range(start - 1, len(lines)):
        ln = idx + 1
        line = lines[idx].strip()

        if not line:
            last_was_dialogue = False
            continue
        if line.startswith("%% "):
            continue
        if fade_out_seen:
            err(ln, "FADE OUT. 之后仍有内容", "删除 FADE OUT. 之后的内容，或把收尾移到其前")
            break

        if line == "---":
            in_montage = False
            expect_dialogue = False
            last_was_dialogue = False
            continue
        if line.startswith("###"):
            err(ln, f"不支持的三级标题：{line}", "场景用「# 」，镜头/字幕用「## 」")
            continue

        m = SLUG_RE.match(line)
        if m:
            seen_scene = True
            in_montage = False
            expect_dialogue = False
            last_was_dialogue = False
            if m.group(4):
                no = int(m.group(4))
                if last_scene_no and no != last_scene_no + 1:
                    warn(ln, f"场号跳变：[{no}] 前一场为 [{last_scene_no}]", "按连续整数编号，或去掉场号")
                last_scene_no = no
            continue

        if line.startswith("# ") and not SLUG_RE.match(line):
            err(ln, f"场景标题缺少内/外景前缀：{line}", "写为「# INT. 地点 - 时间」或「# EXT. 地点 - 时间」")
            continue

        m = MONTAGE_RE.match(line)
        if m:
            in_montage = True
            expect_dialogue = False
            last_was_dialogue = False
            continue

        if line.startswith("## "):
            if not seen_scene:
                err(ln, f"镜头/字幕出现在首个场景之前：{line}", "先写场景标题（# INT./EXT. ...）再写镜头")
            m = SHOT_RE.match(line)
            if not m or not m.group(1).strip():
                err(ln, "镜头标题为空", "写为「## 特写 内容」")
            in_montage = False
            expect_dialogue = False
            last_was_dialogue = False
            continue

        m = TRANS_RE.match(line)
        if m:
            t = m.group(1).strip()
            if t.upper() not in KNOWN_TRANSITIONS:
                if not (t == t.upper() and t.endswith(":") or t == t.upper()):
                    warn(ln, f"非常规转场：{t}", "使用 FADE IN: / CUT TO: / SMASH CUT TO: / DISSOLVE TO: / FADE OUT.")
            if t.upper().startswith("FADE OUT"):
                fade_out_seen = True
            continue

        m = CHAR_RE.match(line)
        if m:
            name = m.group(1).strip()
            if not name:
                err(ln, "角色提示为空", "写为「**姓名**」")
            expect_dialogue = True
            last_was_dialogue = False
            continue

        if in_montage:
            if OLIST_RE.match(line):
                continue

        m = PAREN_RE.match(line)
        if m:
            if not (expect_dialogue or last_was_dialogue):
                err(ln, f"括号提示出现在无对白上下文：{line}", "括号提示只能放在角色提示之后、对白之前/之中")
            last_was_dialogue = True
            continue

        if expect_dialogue or last_was_dialogue:
            if line.startswith("（"):
                err(ln, f"行内括号应以台词包裹：{line}", "把语气提示写成独立行括号，或嵌入台词中间")
            expect_dialogue = False
            last_was_dialogue = True
            continue

        if line.startswith("（"):
            err(ln, f"动作段以括号开头：{line}", "括号是语气提示，动作段应写可见行为")
            continue

        # 普通动作段
        last_was_dialogue = False

    if not seen_scene:
        err(1, "正文中没有场景标题", "用「# INT. 地点 - 时间」开始写戏")

    print(f"校验文件：{path}")
    print(f"frontmatter：title={meta.get('title', '(缺失)')}"
          + (f" | type={meta['type']}" if meta.get("type") else "")
          + (f" | genre={meta.get('genre')}" if meta.get("genre") else ""))
    print("-" * 60)
    if WARNINGS:
        for ln, lv, problem, fix in WARNINGS:
            print(f"{ln:>4} | {lv} | {problem} | 修法：{fix}")
    else:
        print("（无警告）")
    print("-" * 60)
    if ERRORS:
        for ln, lv, problem, fix in ERRORS:
            print(f"{ln:>4} | {lv} | {problem} | 修法：{fix}")
        print(f"\n❌ 发现 {len(ERRORS)} 个错误、{len(WARNINGS)} 个警告。"
              "请先修复格式，再进入剧本医生的内容诊断。")
        sys.exit(1)
    print(f"✅ 格式校验通过（{len(WARNINGS)} 个警告）。可进入内容诊断（references/doctor.md）并渲染 PDF。")
    sys.exit(0)


if __name__ == "__main__":
    main()
