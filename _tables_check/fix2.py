# -*- coding: utf-8 -*-
import pathlib

p = pathlib.Path(r"C:\Users\RATE\WritenSkill\_tables_check\generate_md.py")
t = p.read_text(encoding="utf-8")

# 1) HBO 分章正则（旧文本：无 # 前缀，字符集少了"十"）
old1 = 'chapters = split_chapters(body, r"^第[一二三四五六七八九]+章.*$")'
new1 = 'chapters = split_chapters(body, r"^#{0,4}\\s*第[一二三四五六七八九]+章.*$")'
print("1 HBO 命中:", old1 in t)
t = t.replace(old1, new1)

# 2) 故事正文起点正则
old2 = 'm0 = re.search(r"^CHAPTER\\s*\\d+\\s*/", text, re.M)'
new2 = 'm0 = re.search(r"^#{0,4}\\s*CHAPTER\\s*\\d+\\s*/", text, re.M)'
print("2 故事 m0 命中:", old2 in t)
t = t.replace(old2, new2)

# 3) 文件名去掉 # 标记
old3 = "def safe(name: str) -> str:\n    return re.sub(r'[\\\\/:*?\"<>|]', \"_\", name).strip()[:40]"
new3 = "def safe(name: str) -> str:\n    return re.sub(r'[\\\\/:*?#\"<>|]', \"_\", name).replace(\"#\", \"\").strip()[:40]"
print("3 safe 命中:", old3 in t)
t = t.replace(old3, new3)

p.write_text(t, encoding="utf-8")
print("已写入")
