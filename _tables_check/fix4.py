# -*- coding: utf-8 -*-
import pathlib

p = pathlib.Path(r"C:\Users\RATE\WritenSkill\_tables_check\generate_md.py")
t = p.read_text(encoding="utf-8")

old = '''    if pre.strip():
        new_chs = [("导言：致中国读者与序言", pre)] + new_chs
    book_dir = OUT / "故事：材质、结构、风格和银幕剧作的原理"'''

new = '''    if pre.strip():
        new_chs = [("导言：致中国读者与序言", pre)] + new_chs
    # 从最后一章尾部剥离"附录：文中涉及影片列表"与"译注"为独立章节
    last_title, last_body = new_chs[-1]
    i_app = last_body.find("\\n附录：文中涉及影片列表")
    i_note = last_body.find("\\n译注\\n") if i_app > 0 else -1
    appendix = note = ""
    if i_app > 0:
        appendix = last_body[i_app:].strip()
        last_body = last_body[:i_app].strip()
    if i_note > 0 and i_note > i_app:
        note = appendix[i_note - i_app:].strip()
        appendix = appendix[:i_note - i_app].strip()
    new_chs[-1] = (last_title, last_body)
    if appendix:
        new_chs.append(("附录", appendix))
    if note:
        new_chs.append(("译注", note))
    book_dir = OUT / "故事：材质、结构、风格和银幕剧作的原理"'''

print("命中:", old in t)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("已写入")
