# -*- coding: utf-8 -*-
"""验证 md 输出质量。"""
import pathlib

root = pathlib.Path(r"C:\Users\RATE\WritenSkill\编剧理论书籍_md")
total = 0
for p in root.rglob("*.md"):
    t = p.read_text(encoding="utf-8")
    total += 1
    unk = t.count("未知")
    if unk:
        print(f"  含「未知」 {p.name}: {unk} 处")
print("md 文件总数:", total)

checks = [
    "写作兵器库：故事创意指南/01_第二章 故事的基本框架.md",
    "写作兵器库：故事创意指南/03_第四章 人物.md",
    "写作兵器库：故事创意指南/02_第三章 主题.md",
    "故事：材质、结构、风格和银幕剧作的原理/08_CHAPTER 08 _ 激励事件.md",
    "故事：材质、结构、风格和银幕剧作的原理/02_CHAPTER 02 _ 结构图谱.md",
    "剧本：影视写作的艺术、技巧和商业运作/11_Chapter 11格式.md",
    "救猫咪：电影编剧指南/09_附录.md",
]
for f in checks:
    p = root / f
    if p.exists():
        t = p.read_text(encoding="utf-8")
        has = "|---" in t or "[原书图示]" in t or "[原书插图]" in t
        print(f"{p.parent.name[:14]}/{p.name[:22]}  图片内容: {has}  字符: {len(t)}")
    else:
        print("缺失:", f)
