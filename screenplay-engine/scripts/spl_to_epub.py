#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spl_to_epub.py — SPL 剧本导出为 EPUB 3 电子书

用法:
    python spl_to_epub.py 剧本.md [-o 输出.epub]

解析 SPL（见 references/spl-spec.md），生成符合 EPUB 3 规范的电子书。
EPUB 不嵌入字体，由阅读器自行选择字体（满足"不限定字体"的需求）。
CSS 保留剧本格式的缩进、对齐、间距，用通用字体族（serif/sans-serif）。

依赖: 无第三方依赖（纯标准库 zipfile + 自写 SPL 解析）。
退出码: 0 成功 / 1 失败
"""
import sys
import os
import re
import zipfile
import html

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, "..", "output")


# ---------------------------------------------------------------- SPL 解析
SLUG_RE = re.compile(r"^#\s+(INT\./EXT\.|I/E\.|INT/EXT|INT\.|EXT\.)\s+(.+?)\s*-\s*(.+?)\s*(?:\[(\d+)\])?$")
SHOT_RE = re.compile(r"^##\s+(.+)$")
TRANS_RE = re.compile(r"^>\s*(.+)$")
MONTAGE_RE = re.compile(r"^##\s+蒙太奇\s*(.*)$")
CHAR_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
PAREN_RE = re.compile(r"^（.+?）$")
OLIST_RE = re.compile(r"^\d+\.\s+(.+)$")


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, 1
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, 1
    meta = {}
    for line in lines[1:end]:
        if ":" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition(":")
            meta[k.strip().lower()] = v.strip().strip('"\'')
    return meta, end + 2


def parse_spl(text):
    meta, start = parse_frontmatter(text)
    elements = []
    lines = text.splitlines()
    in_montage = False
    expect_dialogue = False
    last_was_dialogue = False

    for idx in range(start - 1, len(lines)):
        ln = idx + 1
        line = lines[idx].strip()
        if not line:
            last_was_dialogue = False
            continue
        if line.startswith("%% "):
            continue
        if line == "---":
            elements.append(("pagebreak", "", ln))
            in_montage = False
            expect_dialogue = False
            last_was_dialogue = False
            continue
        if line.startswith("###"):
            continue
        m = SLUG_RE.match(line)
        if m:
            slug = f"{m.group(1)} {m.group(2)} - {m.group(3)}"
            if m.group(4):
                slug += f" [{m.group(4)}]"
            elements.append(("scene", slug, ln))
            in_montage = False
            expect_dialogue = False
            last_was_dialogue = False
            continue
        if line.startswith("# "):
            elements.append(("error", f"场景标题缺少前缀（第{ln}行）", ln))
            continue
        m = MONTAGE_RE.match(line)
        if m:
            elements.append(("montage", m.group(1) or "蒙太奇", ln))
            in_montage = True
            expect_dialogue = False
            last_was_dialogue = False
            continue
        if line.startswith("## "):
            m = SHOT_RE.match(line)
            elements.append(("shot", m.group(1) if m else line[3:], ln))
            in_montage = False
            expect_dialogue = False
            last_was_dialogue = False
            continue
        m = TRANS_RE.match(line)
        if m:
            elements.append(("transition", m.group(1), ln))
            continue
        m = CHAR_RE.match(line)
        if m:
            elements.append(("character", m.group(1), ln))
            expect_dialogue = True
            last_was_dialogue = False
            continue
        if in_montage:
            m = OLIST_RE.match(line)
            if m:
                elements.append(("montage_item", m.group(1), ln))
                continue
        m = PAREN_RE.match(line)
        if m:
            if expect_dialogue or last_was_dialogue:
                elements.append(("parenthetical", line, ln))
                last_was_dialogue = True
            continue
        if expect_dialogue or last_was_dialogue:
            elements.append(("dialogue", line, ln))
            last_was_dialogue = True
            expect_dialogue = False
            continue
        elements.append(("action", line, ln))
        last_was_dialogue = False
    return meta, elements


# ---------------------------------------------------------------- EPUB 生成
CSS = """\
/* SPL 剧本 EPUB 样式 —— 不指定具体字体，由阅读器选择 */
@page { margin: 1.5em; }
body {
  font-family: serif;
  line-height: 1.5;
  margin: 0;
  padding: 0;
}
.cover {
  text-align: center;
  margin-top: 30%;
}
.cover h1 {
  font-size: 2em;
  font-family: sans-serif;
  margin-bottom: 0.5em;
}
.cover .author {
  font-size: 1.2em;
  color: #555;
}
.cover .meta {
  margin-top: 2em;
  font-size: 0.9em;
  color: #777;
}
.cover .logline {
  margin-top: 2em;
  font-style: italic;
  color: #444;
  padding: 0 10%;
}
.scene {
  font-family: sans-serif;
  font-weight: bold;
  font-size: 1.05em;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  text-transform: uppercase;
}
.action {
  margin: 0.8em 0;
  text-align: justify;
}
.character {
  font-family: sans-serif;
  font-weight: bold;
  text-align: center;
  margin-top: 1.2em;
  margin-bottom: 0;
  text-transform: uppercase;
}
.parenthetical {
  text-align: center;
  margin: 0.3em 0 0.3em 15%;
  font-style: italic;
  color: #444;
}
.dialogue {
  margin: 0.3em 15% 0.8em 15%;
  text-align: center;
}
.dialogue.multi {
  text-align: left;
}
.transition {
  font-family: sans-serif;
  font-weight: bold;
  text-align: right;
  margin: 1.2em 0;
  text-transform: uppercase;
}
.shot {
  font-family: sans-serif;
  font-style: italic;
  margin: 0.8em 0 0.3em 0;
  color: #333;
}
.montage {
  font-family: sans-serif;
  font-weight: bold;
  margin-top: 1.2em;
  margin-bottom: 0.3em;
}
.montage-item {
  margin: 0.2em 0 0.2em 10%;
}
.pagebreak {
  page-break-after: always;
  border: none;
  margin: 0;
}
"""

CONTAINER_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


def esc(text):
    return html.escape(text, quote=False)


def build_xhtml(meta, elements):
    """把 SPL 元素转为 XHTML 正文。"""
    parts = []
    # 封面
    title = esc(meta.get("title", "UNTITLED"))
    author = esc(meta.get("author", ""))
    parts.append('<section class="cover">')
    parts.append(f"<h1>{title}</h1>")
    if author:
        parts.append(f'<p class="author">{author}</p>')
    meta_bits = []
    for k in ("type", "genre", "runtime"):
        if meta.get(k):
            meta_bits.append(esc(meta[k]))
    if meta_bits:
        parts.append(f'<p class="meta">{" / ".join(meta_bits)}</p>')
    if meta.get("logline"):
        parts.append(f'<p class="logline">{esc(meta["logline"])}</p>')
    parts.append("</section>")
    parts.append('<hr class="pagebreak"/>')

    # 正文
    for kind, payload, _ln in elements:
        if kind == "scene":
            parts.append(f'<h2 class="scene">{esc(payload.upper())}</h2>')
        elif kind == "action":
            parts.append(f'<p class="action">{esc(payload)}</p>')
        elif kind == "character":
            parts.append(f'<p class="character">{esc(payload.upper())}</p>')
        elif kind == "parenthetical":
            parts.append(f'<p class="parenthetical">{esc(payload)}</p>')
        elif kind == "dialogue":
            # 长对白左对齐，短对白居中（CSS 控制，这里统一用 dialogue 类）
            parts.append(f'<p class="dialogue">{esc(payload)}</p>')
        elif kind == "transition":
            parts.append(f'<p class="transition">{esc(payload.upper())}</p>')
        elif kind == "shot":
            parts.append(f'<p class="shot">{esc(payload)}</p>')
        elif kind == "montage":
            parts.append(f'<h3 class="montage">{esc(payload.upper())}</h3>')
        elif kind == "montage_item":
            parts.append(f'<p class="montage-item">{esc(payload)}</p>')
        elif kind == "pagebreak":
            parts.append('<hr class="pagebreak"/>')
    body = "\n".join(parts)

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{body}
</body>
</html>
"""


def build_nav(meta):
    title = esc(meta.get("title", "UNTITLED"))
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head><meta charset="utf-8"/><title>目录</title></head>
<body>
<nav epub:type="toc" id="toc">
  <h1>目录</h1>
  <ol>
    <li><a href="screenplay.xhtml">{title}</a></li>
  </ol>
</nav>
</body>
</html>
"""


def build_opf(meta):
    title = esc(meta.get("title", "UNTITLED"))
    author = esc(meta.get("author", "Unknown"))
    lang = esc(meta.get("language", "zh-CN"))
    uid = "spl-" + re.sub(r"[^a-z0-9]", "-", title.lower())[:40]
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:{uid}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>{lang}</dc:language>
    <meta property="dcterms:modified">2026-01-01T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="style.css" media-type="text/css"/>
    <item id="screenplay" href="screenplay.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="screenplay"/>
  </spine>
</package>
"""


def write_epub(meta, elements, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    xhtml = build_xhtml(meta, elements)
    nav = build_nav(meta)
    opf = build_opf(meta)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype 必须第一个且不压缩
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", CONTAINER_XML)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/nav.xhtml", nav)
        zf.writestr("OEBPS/style.css", CSS)
        zf.writestr("OEBPS/screenplay.xhtml", xhtml)
    return True


def main():
    if len(sys.argv) < 2:
        print("用法：python spl_to_epub.py 剧本.md [-o 输出.epub]")
        sys.exit(1)
    src = sys.argv[1]
    out = None
    if "-o" in sys.argv:
        out = sys.argv[sys.argv.index("-o") + 1]
    if not out:
        os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
        base = os.path.splitext(os.path.basename(src))[0]
        out = os.path.join(DEFAULT_OUTPUT_DIR, base + ".epub")

    if not os.path.exists(src):
        print(f"错误：文件不存在 {src}")
        sys.exit(1)
    with open(src, encoding="utf-8") as f:
        text = f.read()

    meta, elements = parse_spl(text)
    write_epub(meta, elements, out)
    print(f"✅ EPUB 导出完成：{out}")
    print(f"   场景数：{sum(1 for k, _, _ in elements if k == 'scene')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
