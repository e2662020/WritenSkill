# -*- coding: utf-8 -*-
import pathlib

p = pathlib.Path(r"C:\Users\RATE\WritenSkill\_tables_check\generate_md.py")
t = p.read_text(encoding="utf-8")

old = "def safe(name: str) -> str:\n    return re.sub(r'[\\\\/:*?#\"<>|]', \"_\", name).replace(\"#\", \"\").strip()[:40]"
new = (
    "def safe(name: str) -> str:\n"
    "    n = re.sub(r'[\\\\/:*?\"<>|]', \"_\", name).replace(\"#\", \"\").strip()\n"
    "    return re.sub(r\"\\s+\", \" \", n)[:40]"
)
print("safe 命中:", old in t)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("已写入")
