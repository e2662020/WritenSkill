# -*- coding: utf-8 -*-
"""改进版 epub 提取器：跳过 head（清除“未知”title 残留）、块级元素换行（保留小标题）、去图片。"""
import posixpath
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

SRC = Path(r"C:\Users\RATE\编剧入门教程")
OUT = Path(r"C:\Users\RATE\WritenSkill\编剧理论书籍")

BLOCK = {
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "section", "article",
    "li", "ul", "ol", "blockquote", "table", "tr", "td", "th", "hr",
    "dt", "dd", "figcaption", "pre", "header", "footer",
}


class BlockTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.in_head = 0      # <head> 深度
        self.skip = 0         # script/style 深度

    def _nl(self):
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head += 1
            return
        if self.in_head:
            return
        if tag in ("script", "style", "noscript"):
            self.skip += 1
            return
        if tag == "br":
            self._nl()
        elif tag in BLOCK:
            self._nl()

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
            self._nl()

    def handle_data(self, data):
        if self.in_head or self.skip:
            return
        self.parts.append(data)


def extract_epub(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        container = z.read("META-INF/container.xml").decode("utf-8", "ignore")
        m = re.search(r'full-path="([^"]+)"', container)
        if not m:
            raise ValueError(f"无 opf: {path.name}")
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

        chunks = []
        for rid in spine:
            href = manifest.get(rid)
            if not href or not href.lower().endswith((".html", ".xhtml", ".htm")):
                continue
            full = posixpath.normpath(posixpath.join(opf_dir, href))
            try:
                data = z.read(full).decode("utf-8", "ignore")
            except KeyError:
                continue
            parser = BlockTextExtractor()
            parser.feed(data)
            chunks.append("".join(parser.parts))
        return "\n".join(chunks)


def clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for ln in text.split("\n"):
        s = ln.strip()
        if s == "未知":          # 孤立“未知”占位行
            s = ""
        lines.append(s)
    text = "\n".join(lines)
    text = re.sub(r"[ \t\u00a0\u2003]+", " ", text)   # 全角/半角空格归一
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    for epub in sorted(SRC.glob("*.epub")):
        stem = epub.stem
        text = clean(extract_epub(epub))
        dst = OUT / f"{stem}.txt"
        dst.write_text(text, encoding="utf-8")
        n_unk = text.count("未知")
        print(f"[完成] {stem[:40]}  -> {len(text):,} 字符 | “未知”剩余: {n_unk}")


if __name__ == "__main__":
    main()
