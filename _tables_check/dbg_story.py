# -*- coding: utf-8 -*-
import sys, pathlib, importlib.util

BASE = pathlib.Path(r"C:\Users\RATE\WritenSkill\_tables_check")
spec = importlib.util.spec_from_file_location("gm", BASE / "generate_md.py")
gm = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(BASE))
spec.loader.exec_module(gm)

from img_map import STORY_IMGS

epub = [p for p in gm.SRC.glob("*.epub") if "故事材质" in p.name][0]
items = gm.extract_epub_items(epub, STORY_IMGS)
text = gm.items_to_text(items, STORY_IMGS)
text = gm.clean_md(text)
m0 = gm.re.search(r"^#{0,4}\s*CHAPTER\s*\d+\s*/", text, gm.re.M)
start = m0.start() if m0 else 0
body = text[start:]
chapters = gm.split_chapters(body, r"^#{0,4}\s*CHAPTER\s*\d+\s*/.*$")
last_title, last_body = chapters[-1]
print("last_title:", last_title[:40])
print("len(last_body):", len(last_body))
for kw in ["附录：文中涉及影片列表", "译注"]:
    i = last_body.find(kw)
    print(f"find({kw}) =", i)
    if i > 0:
        print(repr(last_body[i - 20:i + 40]))
