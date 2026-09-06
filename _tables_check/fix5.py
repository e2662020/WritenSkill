# -*- coding: utf-8 -*-
import pathlib

p = pathlib.Path(r"C:\Users\RATE\WritenSkill\_tables_check\generate_md.py")
t = p.read_text(encoding="utf-8")

old = '    i_app = last_body.find("\\n附录：文中涉及影片列表")\n    i_note = last_body.find("\\n译注\\n") if i_app > 0 else -1'
new = '    i_app = last_body.find("\\n# 附录：文中涉及影片列表")\n    i_note = last_body.find("\\n# 译注\\n") if i_app > 0 else -1'
print("命中:", old in t)
t = t.replace(old, new)
p.write_text(t, encoding="utf-8")
print("已写入")
