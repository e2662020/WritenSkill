# -*- coding: utf-8 -*-
import pathlib

p = pathlib.Path(r"C:\Users\RATE\WritenSkill\_tables_check\generate_md.py")
t = p.read_text(encoding="utf-8")
pairs = [
    ('split_chapters(text, r"^第[一二三四五六七八九十]+章.*$")',
     'split_chapters(text, r"^#{0,4}\\s*第[一二三四五六七八九十]+章.*$")'),
    ('split_chapters(text, r"^Chapter \\d+.*$")',
     'split_chapters(text, r"^#{0,4}\\s*Chapter \\d+.*$")'),
    ('split_chapters(body, r"^第[一二三四五六七八九十]+章.*$")',
     'split_chapters(body, r"^#{0,4}\\s*第[一二三四五六七八九十]+章.*$")'),
    ('split_chapters(body, r"^CHAPTER\\s*\\d+\\s*/.*$")',
     'split_chapters(body, r"^#{0,4}\\s*CHAPTER\\s*\\d+\\s*/.*$")'),
    ('split_chapters(text, r"^Chapter\\s+0\\d\\s*$")',
     'split_chapters(text, r"^#{0,4}\\s*Chapter\\s+0\\d\\s*$")'),
    ('re.finditer(r"^第一章", text, re.M)',
     're.finditer(r"^#{0,4}\\s*第一章", text, re.M)'),
]
for old, new in pairs:
    n = t.count(old)
    if n:
        t = t.replace(old, new)
        print(f"替换 x{n}: {old[:46]}")
    else:
        print(f"未命中: {old[:46]}")
p.write_text(t, encoding="utf-8")
print("OK")
