#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logs_to_epub.py — 《服管足行志》剧本格式 → EPUB 3

适配本项目正文格式（见 13-full-script-v4.md）：
    YAML frontmatter
    <!-- 第N集《标题》 -->  → 分章锚点（HTML 注释不渲染，用于切分章节）
    > **第N集《标题》**     → 章标题
    # INT. 地点 - 时间，内外 [场号]   → 场景行
    人物：…                  → 场次人物表
    ▲ 动作行                 → 动作
    **角色**（提示）：……台词   → 角色提示 + 括号提示 + 台词
    【黑屏】/【本集完】/【全季终】 → 分隔标记
    > FADE OUT.              → 转场

用法：
    python logs_to_epub.py 剧本.md [-o 输出.epub] [--title 书名] [--author 作者]

无第三方依赖（标准库 zipfile + 自写解析）。
退出码：0 成功 / 1 失败
"""
import sys
import os
import re
import html
import zipfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SCENE_RE = re.compile(r"^#\s+(INT\./EXT\.|INT\.|EXT\.|I/E\.)\s*(.+?)\s*-\s*(.+?)(?:\s*\[([^\]]+)\])?$")
EPISODE_COMMENT_RE = re.compile(r"^<!--\s*(第\d+集《[^》]+》)\s*-->$")
EPISODE_QUOTE_RE = re.compile(r"^>\s*\*\*(第\d+集《[^》]+》)\*\*$")
TRANS_RE = re.compile(r"^>\s*(.+)$")
CAST_RE = re.compile(r"^人物[：:]\s*(.+)$")
CHAR_RE = re.compile(r"^\*\*(.+?)\*\*\s*(（[^）]*）)?\s*[：:]?\s*(.*)$")
SEP_RE = re.compile(r"^【(.+?)】$")
ACTION_RE = re.compile(r"^▲\s*(.*)$")


def esc(t):
    return html.escape(t, quote=False)


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, 0
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, 0
    meta = {}
    for line in lines[1:end]:
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip().strip('"\'')
    return meta, end + 1


def split_episodes(text):
    """按 <!-- 第N集《X》 --> 切成 [(标题, 正文行列表)]"""
    lines = text.splitlines()
    eps, cur_title, cur = [], None, []
    for l in lines:
        m = EPISODE_COMMENT_RE.match(l.strip())
        if m:
            if cur_title is not None:
                eps.append((cur_title, cur))
            cur_title, cur = m.group(1), []
            continue
        if cur_title is None:
            continue
        cur.append(l)
    if cur_title is not None:
        eps.append((cur_title, cur))
    return eps


def render_body(lines):
    """把一集的正文行渲染为 XHTML"""
    out = []
    for raw in lines:
        line = raw.rstrip()
        s = line.strip()
        if not s or s == "---":
            continue
        if EPISODE_QUOTE_RE.match(s):            # 章标题已由 <h1> 渲染，跳过
            continue
        if s.startswith("<!--"):
            continue

        m = SCENE_RE.match(s)
        if m:
            prefix, loc, tm, num = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4)
            label = f"{prefix} {loc} — {tm}"
            if num:
                label += f"　[{num}]"
            out.append(f'<p class="scene">{esc(label)}</p>')
            continue

        m = SEP_RE.match(s)
        if m:
            out.append(f'<p class="sep">{esc(m.group(1))}</p>')
            continue

        m = CAST_RE.match(s)
        if m:
            out.append(f'<p class="cast"><span class="castlabel">人物</span>{esc(m.group(1))}</p>')
            continue

        m = ACTION_RE.match(s)
        if m:
            out.append(f'<p class="action">{esc(m.group(1))}</p>')
            continue

        m = TRANS_RE.match(s)
        if m:
            out.append(f'<p class="transition">{esc(m.group(1))}</p>')
            continue

        m = CHAR_RE.match(s)
        if m:
            who, paren, said = m.group(1), m.group(2), m.group(3)
            out.append(f'<p class="character">{esc(who)}</p>')
            if paren:
                out.append(f'<p class="paren">{esc(paren)}</p>')
            if said:
                out.append(f'<p class="dialogue">{esc(said)}</p>')
            continue

        out.append(f'<p class="action">{esc(s)}</p>')
    return "\n".join(out)


CSS = """\
@page { margin: 1.4em; }
html { font-size: 100%; }
body { font-family: serif; line-height: 1.6; margin: 0; padding: 0; }
h1.ep {
  font-family: sans-serif; font-size: 1.5em; font-weight: bold;
  text-align: center; margin: 1.6em 0 1.4em 0; padding-bottom: .4em;
  border-bottom: 2px solid #333;
}
h1.book { font-family: sans-serif; font-size: 1.9em; text-align: center; margin: 3.2em 0 .6em 0; }
p.author { text-align: center; font-size: 1.15em; color: #444; margin: 0 0 2em 0; }
p.metainfo { text-align: center; font-size: .92em; color: #777; margin: 0 0 1.2em 0; }
p.logline { font-style: italic; color: #333; text-align: center; margin: 0 8% 1.2em 8%; }
p.idea { text-align: center; font-size: .95em; color: #555; margin: 0 10% 2.5em 10%; }
p.scene {
  font-family: sans-serif; font-weight: bold; font-size: 1.02em;
  margin: 1.5em 0 .45em 0; padding: .18em .4em;
  border-left: 4px solid #666; background: #f2f2f2;
  page-break-after: avoid;
}
p.cast { font-size: .88em; color: #666; margin: 0 0 .8em .2em; }
.castlabel { font-family: sans-serif; color: #999; margin-right: .5em; }
p.action { margin: .55em 0; text-align: justify; text-indent: 2em; }
p.character {
  font-family: sans-serif; font-weight: bold; text-align: center;
  margin: .85em 0 0 0; page-break-after: avoid;
}
p.paren { text-align: center; font-style: italic; color: #555; margin: .1em 0; font-size: .94em; page-break-after: avoid; }
p.dialogue { margin: .15em 8% .75em 8%; text-align: justify; }
p.sep { text-align: center; font-family: sans-serif; font-size: .86em; color: #888; letter-spacing: .3em; margin: 1.1em 0; }
p.transition { font-family: sans-serif; font-weight: bold; text-align: right; margin: 1.4em 0; letter-spacing: .1em; }
hr.pb { page-break-after: always; border: none; height: 0; margin: 0; }
"""

CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

XHTML_TPL = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
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


def build(meta, eps, out_path):
    title = meta.get("title", "未命名剧本")
    author = meta.get("author", "")
    files = []          # [(id, href, title)]

    # 封面
    cover_bits = [f'<h1 class="book">{esc(title)}</h1>']
    if author:
        cover_bits.append(f'<p class="author">{esc(author)}</p>')
    mi = " / ".join(x for x in (meta.get("type"), meta.get("genre"), meta.get("runtime")) if x)
    if mi:
        cover_bits.append(f'<p class="metainfo">{esc(mi)}</p>')
    if meta.get("logline"):
        cover_bits.append(f'<p class="logline">{esc(meta["logline"])}</p>')
    if meta.get("controlling-idea"):
        cover_bits.append(f'<p class="idea">{esc(meta["controlling-idea"])}</p>')
    cover = XHTML_TPL.format(title=esc(title), body="\n".join(cover_bits))

    chapters = [("cover", "cover.xhtml", title, cover)]
    for i, (ep_title, body_lines) in enumerate(eps, 1):
        href = f"ep{i:02d}.xhtml"
        body = f'<h1 class="ep">{esc(ep_title)}</h1>\n' + render_body(body_lines)
        chapters.append((f"ep{i:02d}", href, ep_title, XHTML_TPL.format(title=esc(ep_title), body=body)))
    files = chapters

    # nav
    nav_items = "\n".join(
        f'    <li><a href="{href}">{esc(t)}</a></li>' for _id, href, t, _x in files
    )
    nav = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head><meta charset="utf-8"/><title>目录</title></head>
<body>
<nav epub:type="toc" id="toc">
  <h1>目录</h1>
  <ol>
{nav_items}
  </ol>
</nav>
</body>
</html>
"""

    manifest = "\n".join(
        f'    <item id="{i}" href="{h}" media-type="application/xhtml+xml"/>' for i, h, _t, _x in files
    )
    spine = "\n".join(f'    <itemref idref="{i}"/>' for i, _h, _t, _x in files)
    uid = "logs-" + re.sub(r"[^a-z0-9]+", "-", title.lower())[:36].strip("-")
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:{uid}</dc:identifier>
    <dc:title>{esc(title)}</dc:title>
    <dc:creator>{esc(author or '未署名')}</dc:creator>
    <dc:language>zh-CN</dc:language>
    <meta property="dcterms:modified">2026-09-12T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="style.css" media-type="text/css"/>
{manifest}
  </manifest>
  <spine>
{spine}
  </spine>
</package>
"""

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", CONTAINER_XML)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/nav.xhtml", nav)
        zf.writestr("OEBPS/style.css", CSS)
        for _i, href, _t, xhtml in files:
            zf.writestr(f"OEBPS/{href}", xhtml)
    return len(files)


def main():
    args = sys.argv[1:]
    if not args:
        print("用法：python logs_to_epub.py 剧本.md [-o 输出.epub]")
        sys.exit(1)
    src = args[0]
    out = args[args.index("-o") + 1] if "-o" in args else os.path.join(
        SCRIPT_DIR, "output", os.path.splitext(os.path.basename(src))[0] + ".epub")
    if not os.path.exists(src):
        print(f"错误：文件不存在 {src}")
        sys.exit(1)

    text = open(src, encoding="utf-8").read()
    meta, _ = parse_frontmatter(text)
    eps = split_episodes(text)
    if not eps:
        print("错误：未找到集标记 <!-- 第N集《…》 -->")
        sys.exit(1)
    n = build(meta, eps, out)
    print(f"✅ EPUB 导出完成：{out}")
    print(f"   章节数：{n}（封面 + {len(eps)} 集）")
    sys.exit(0)


if __name__ == "__main__":
    main()
