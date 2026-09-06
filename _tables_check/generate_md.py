# -*- coding: utf-8 -*-
"""生成 Markdown 版编剧理论书籍：每本一个文件夹、每章一个 md，图片转 Markdown 内容。"""
import posixpath
import re
import shutil
import zipfile
from html.parser import HTMLParser
from pathlib import Path

import sys

sys.path.insert(0, r"C:\Users\RATE\WritenSkill\_tables_check")
from img_map import WRITING_TABLES, PLAYBOOK_IMGS, STORY_IMGS

SRC = Path(r"C:\Users\RATE\编剧入门教程")
TXT_BOOKS = Path(r"C:\Users\RATE\WritenSkill\编剧理论书籍")
OUT = Path(r"C:\Users\RATE\WritenSkill\编剧理论书籍_md")

BLOCK = {
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "section", "article",
    "li", "ul", "ol", "blockquote", "table", "tr", "td", "th", "hr",
    "dt", "dd", "figcaption", "pre", "header", "footer",
}


class MdExtractor(HTMLParser):
    """提取为 (kind, text) 序列；kind: h1..h6 / para / img。"""

    def __init__(self, imgmap):
        super().__init__()
        self.items = []
        self.in_head = 0
        self.skip = 0
        self.imgmap = imgmap

    def _flush_buf(self):
        pass

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head += 1
            return
        if self.in_head:
            return
        if tag in ("script", "style", "noscript"):
            self.skip += 1
            return
        if tag == "img":
            d = dict(attrs)
            src = (d.get("src") or "").split("/")[-1].split("?")[0]
            key = src
            if key in self.imgmap:
                self.items.append(("img", key))
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.items.append((tag, ""))
        elif tag in BLOCK:
            self.items.append(("nl", ""))

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = max(0, self.in_head - 1)
            return
        if self.in_head:
            return
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
            return
        if tag in BLOCK:
            self.items.append(("nl", ""))

    def handle_data(self, data):
        if self.in_head or self.skip:
            return
        if self.items and self.items[-1][0] == "nl":
            self.items.pop()
        if self.items and self.items[-1][0] in ("h1", "h2", "h3", "h4", "h5", "h6", "para"):
            kind, old = self.items[-1]
            self.items[-1] = (kind, old + data)
        else:
            self.items.append(("para", data))


def extract_epub_items(path: Path, imgmap):
    with zipfile.ZipFile(path) as z:
        container = z.read("META-INF/container.xml").decode("utf-8", "ignore")
        m = re.search(r'full-path="([^"]+)"', container)
        opf_path = m.group(1)
        opf_dir = posixpath.dirname(opf_path)
        opf = z.read(opf_path).decode("utf-8", "ignore")
        manifest, spine = {}, []
        for m in re.finditer(r"<item\b[^>]*/?>", opf):
            seg = m.group(0)
            iid = re.search(r'\bid="([^"]+)"', seg)
            href = re.search(r'\bhref="([^"]+)"', seg)
            if iid and href:
                manifest[iid.group(1)] = href.group(1)
        for m in re.finditer(r"<itemref\b[^>]*/?>", opf):
            seg = m.group(0)
            idref = re.search(r'\bidref="([^"]+)"', seg)
            if idref:
                spine.append(idref.group(1))
        items = []
        for rid in spine:
            href = manifest.get(rid)
            if not href or not href.lower().endswith((".html", ".xhtml", ".htm")):
                continue
            full = posixpath.normpath(posixpath.join(opf_dir, href))
            try:
                data = z.read(full).decode("utf-8", "ignore")
            except KeyError:
                continue
            p = MdExtractor(imgmap)
            p.feed(data)
            for it in p.items:
                if it[0] != "nl":
                    items.append(it)
        return items


def items_to_text(items, imgmap):
    """将 (kind, text) 序列渲染为 markdown 文本。"""
    out = []
    for kind, val in items:
        if kind == "img":
            out.append(imgmap[val])
            out.append("")
        elif kind == "para":
            t = re.sub(r"[ \t\u00a0\u2003]+", " ", val).strip()
            if t:
                out.append(t)
        elif kind == "nl":
            continue
        else:  # h1..h6
            t = val.strip()
            if t:
                level = int(kind[1])
                out.append(f"{'#' * min(level, 4)} {t}")
    return "\n".join(out)


def clean_md(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for ln in text.split("\n"):
        s = ln.rstrip()
        if s.strip() in ("未知", "Cover", "cover"):
            s = ""
        lines.append(s)
    text = "\n".join(lines)
    text = re.sub(r"[ \t]+\n", "\n", text)     # 行尾空格
    text = re.sub(r"\n{3,}", "\n\n", text)     # 多余空行压缩到 1 个空行
    return text.strip()


def split_chapters(text, pattern, keep_prev=None):
    """按标题正则切分。返回 [(title, body)]。"""
    matches = list(re.finditer(pattern, text, re.M))
    if not matches:
        return [("", text)]
    segs = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segs.append((m.group(0).strip(), text[start:end]))
    return segs


def safe(name: str) -> str:
    n = re.sub(r'[\\/:*?"<>|]', "_", name).replace("#", "").strip()
    return re.sub(r"\s+", " ", n)[:40]


def write_chapters(book_title, chapters, out_dir, index_rows):
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, (title, body) in enumerate(chapters):
        body = clean_md(body)
        if not body:
            continue
        fname = f"{i:02d}_{safe(title)}.md" if title else f"{i:02d}_未命名.md"
        (out_dir / fname).write_text(body + "\n", encoding="utf-8")
        index_rows.append(f"- [{title or '（前言/杂项）'}]({out_dir.name}/{fname})")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    index_rows = []

    # ========== 1) 写作兵器库（epub） ==========
    epub = [p for p in SRC.glob("*.epub") if "写作兵器库" in p.name][0]
    items = extract_epub_items(epub, WRITING_TABLES)
    text = items_to_text(items, WRITING_TABLES)
    text = clean_md(text)
    chapters = split_chapters(text, r"^#{0,4}\s*第[一二三四五六七八九十]+章.*$")
    book_dir = OUT / "写作兵器库：故事创意指南"
    write_chapters("写作兵器库：故事创意指南", chapters, book_dir, index_rows)

    # ========== 2) 剧本（epub） ==========
    epub = [p for p in SRC.glob("*.epub") if "剧本" in p.name][0]
    items = extract_epub_items(epub, PLAYBOOK_IMGS)
    text = items_to_text(items, PLAYBOOK_IMGS)
    text = clean_md(text)
    chapters = split_chapters(text, r"^#{0,4}\s*Chapter \d+.*$")
    # 第一个 Chapter 之前的部分作为前言
    first = text.find("Chapter 1")
    pre = text[:first]
    chs = [("前言（版权与中文版序）", pre)] + chapters
    book_dir = OUT / "剧本：影视写作的艺术、技巧和商业运作"
    write_chapters("剧本：影视写作的艺术、技巧和商业运作", chs, book_dir, index_rows)

    # ========== 3) HBO（epub） ==========
    epub = [p for p in SRC.glob("*.epub") if "HBO" in p.name][0]
    items = extract_epub_items(epub, {})
    text = items_to_text(items, {})
    text = clean_md(text)
    # 目录区在正文前：正文起点 = "第一章"最后一次出现
    pos = [m.start() for m in re.finditer(r"^#{0,4}\s*第一章", text, re.M)]
    if len(pos) > 1:
        start = pos[-1]
    elif pos:
        start = pos[0]
    else:
        start = 0
    body = text[start:]
    pre = text[:start]
    chapters = split_chapters(body, r"^#{0,4}\s*第[一二三四五六七八九]+章.*$")
    if pre.strip():
        chapters = [("引言/目录说明", pre)] + chapters
    book_dir = OUT / "如何写出好故事 HBO大师写作课"
    write_chapters("如何写出好故事 HBO大师写作课", chapters, book_dir, index_rows)

    # ========== 4) 故事（epub） ==========
    epub = [p for p in SRC.glob("*.epub") if "故事材质" in p.name][0]
    items = extract_epub_items(epub, STORY_IMGS)
    text = items_to_text(items, STORY_IMGS)
    text = clean_md(text)
    # 正文标题格式 "CHAPTER 01 / 故事问题"
    m0 = re.search(r"^#{0,4}\s*CHAPTER\s*\d+\s*/", text, re.M)
    start = m0.start() if m0 else 0
    pre = text[:start]
    body = text[start:]
    chapters = split_chapters(body, r"^#{0,4}\s*CHAPTER\s*\d+\s*/.*$")
    # 提取 PART 卷标并入章节名
    new_chs = []
    for title, seg in chapters:
        pm = re.search(r"^PART\s*[ⅠIIVX\d]+\s*\S.*$", seg, re.M)
        part = pm.group(0).strip() if pm else ""
        new_title = f"{part} | {title}" if part else title
        new_chs.append((new_title, seg))
    if pre.strip():
        new_chs = [("导言：致中国读者与序言", pre)] + new_chs
    # 从最后一章尾部剥离"附录：文中涉及影片列表"与"译注"为独立章节
    last_title, last_body = new_chs[-1]
    i_app = last_body.find("\n# 附录：文中涉及影片列表")
    i_note = last_body.find("\n# 译注\n") if i_app > 0 else -1
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
    book_dir = OUT / "故事：材质、结构、风格和银幕剧作的原理"
    write_chapters("故事：材质、结构、风格和银幕剧作的原理", new_chs, book_dir, index_rows)

    # ========== 5) 救猫咪（txt） ==========
    src = TXT_BOOKS / "救猫咪_电影编剧指南.txt"
    text = clean_md(src.read_text(encoding="utf-8", errors="ignore"))
    # 目录区：Chapter 0N 单独成行的是正文（目录里是 "Chapter 01 标题" 同行）
    chapters = split_chapters(text, r"^#{0,4}\s*Chapter\s+0\d\s*$")
    # 章节名合并下一行标题（"Chapter 01" 行后跟 "它讲的是什么？"）
    chapters = [
        (t, b) if not re.search(r"\n\s*\n\s*([^\n]{2,30})\s*\n", b) or True else (t, b)
        for t, b in chapters
    ]
    merged = []
    for t, b in chapters:
        m2 = re.match(r"(^Chapter\s+0\d\s*\n\s*\n\s*)([^\n#]{2,30})\s*\n", b)
        if m2:
            t = f"{t.strip()} {m2.group(2).strip()}"
        merged.append((t, b))
    chapters = merged
    # 序言（Introduction/序言 之后、Chapter 01 之前）
    pre_end = text.find("Chapter 01\n")
    pre = text[:pre_end] if pre_end > 0 else ""
    chs = []
    if pre.strip():
        chs.append(("序言", pre))
    chs += chapters
    # 附录（最后一个 Chapter 之后的"附录"起）
    last_ch = chs[-1][1]
    tail_start = text.find(last_ch[:200])
    app_idx = text.find("\n附录", tail_start if tail_start >= 0 else 0)
    if app_idx == -1:
        app_idx = text.find("附录", tail_start if tail_start >= 0 else 0)
    if app_idx > 0:
        # 把附录从最后一个章节中剥离
        title, body = chs[-1]
        rel = app_idx - (tail_start if tail_start >= 0 else 0)
        if 0 < rel < len(body):
            chs[-1] = (title, body[:rel])
            chs.append(("附录", body[rel:]))
    book_dir = OUT / "救猫咪：电影编剧指南"
    write_chapters("救猫咪：电影编剧指南", chs, book_dir, index_rows)

    # ========== 6) 电影剧本写作基础（pdf 提取的 txt） ==========
    src = [p for p in TXT_BOOKS.glob("*.txt") if "电影剧本写作基础" in p.name][0]
    text = clean_md(src.read_text(encoding="utf-8", errors="ignore"))
    # 正文标题：第一章…第一七章（第十一~十七写作"第一一"等），目录在文末（标题文本重复出现）
    matches = list(re.finditer(r"^第[一二三四五六七八九十]+章.*$", text, re.M))
    kept = []
    seen_titles = set()
    for m in matches:
        title = m.group(0).strip()
        # 若同一章节标题已出现过，说明进入文末目录区
        if title in seen_titles:
            break
        seen_titles.add(title)
        kept.append(m.start())
    chapters = []
    for i, st in enumerate(kept):
        en = kept[i + 1] if i + 1 < len(kept) else len(text)
        title = text[st:st + 60].split("\n")[0].strip()
        chapters.append((title, text[st:en]))
    book_dir = OUT / "电影剧本写作基础"
    write_chapters("电影剧本写作基础", chapters, book_dir, index_rows)

    # 索引
    (OUT / "00_总目录索引.md").write_text(
        "# 编剧理论书籍 · Markdown 分章索引\n\n" + "\n".join(index_rows) + "\n",
        encoding="utf-8",
    )
    print("完成，输出到:", OUT)
    for d in sorted(OUT.iterdir()):
        if d.is_dir():
            print(f"  {d.name}/  ({len(list(d.glob('*.md')))} 个文件)")


if __name__ == "__main__":
    main()
