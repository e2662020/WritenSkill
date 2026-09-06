# -*- coding: utf-8 -*-
import pathlib

p = pathlib.Path(r"C:\Users\RATE\WritenSkill\_tables_check\generate_md.py")
t = p.read_text(encoding="utf-8")

old = '    text = "\\n".join(lines)\n    text = re.sub(r"\\n{3,}", "\\n\\n", text)\n    return text.strip()'
new = (
    '    text = "\\n".join(lines)\n'
    '    text = re.sub(r"[ \\t]+\\n", "\\n", text)     # 行尾空格\n'
    '    text = re.sub(r"\\n{3,}", "\\n\\n", text)     # 多余空行压缩到 1 个空行\n'
    '    return text.strip()'
)
if old in t:
    t = t.replace(old, new)
    print("clean_md 已优化")
else:
    print("未命中，打印当前内容：")
    i = t.find("def clean_md")
    print(t[i:i + 400])
p.write_text(t, encoding="utf-8")
