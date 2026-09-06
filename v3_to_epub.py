#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v3_to_epub.py — 《服管足行志》凌霄篇 v3（自定义场标格式）→ EPUB 3 电子书

用法:
    python v3_to_epub.py 剧本.md [-o 输出.epub]

解析 v3 剧本格式（## 场标 / ▲ 动作 / **角色**（括号）：台词 / 【黑屏】/【本集完】），
按集拆分章节，生成符合 EPUB 3 规范的电子书。
结构与 CSS 复用 screenplay-engine/scripts/spl_to_epub.py 的设计（纯标准库，零依赖）。
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

# ---------------------------------------------------------------- 解析 v3 格式
EP_RE = re.compile(r"^# 第(\d+)集《(.+?)》$")
SLUG_RE = re.compile(r"^## (.+)，(.+)，(内|外|内/外|外/内)$")
DIALOGUE_RE = re.compile(r"^\*\*(.+?)\*\*\s*(?:（(.*?)）\s*)?[：:]\s*(.*)$")
QUOTE_RE = re.compile(r'^\*\*"(.+?)"\*\*$')
BLACK_RE = re.compile(r"^【(黑屏|本集完|全季终)】$")


def parse_script(text):
    lines = text.splitlines()
    book_title = "UNTITLED"
    metas = []          # 文件头 > 引用行（封面描述）
    episodes = []       # [{num,title,meta_lines[],scenes:[{slug,cast,blocks[]}]}]
    cur_ep = None
    cur_scene = None

    def flush_scene():
        nonlocal cur_scene
        if cur_scene is not None and cur_ep is not None:
            cur_ep["scenes"].append(cur_scene)
            cur_scene = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        # 集标题
        m = EP_RE.match(line)
        if m:
            flush_scene()
            cur_ep = {"num": int(m.group(1)), "title": m.group(2), "meta_lines": [], "scenes": []}
            episodes.append(cur_ep)
            continue
        # 文件头大标题
        if line.startswith("# ") and cur_ep is None and not episodes:
            book_title = line[2:].strip()
            continue
        # 文件头引用行
        if line.startswith(">") and cur_ep is None:
            metas.append(line[1:].strip())
            continue
        if cur_ep is None:
            continue
        # 集说明行
        if line.startswith("本集"):
            cur_ep["meta_lines"].append(line)
            continue
        # 场景标题
        m = SLUG_RE.match(line)
        if m:
            flush_scene()
            cur_scene = {"slug": line[3:].strip(), "cast": None, "blocks": []}
            continue
        # 场景人物行
        if line.startswith("人物："):
            if cur_scene is not None:
                cur_scene["cast"] = line[len("人物："):].strip()
            continue
        # 黑屏 / 集末 / 季终
        m = BLACK_RE.match(line)
        if m:
            if cur_scene is not None:
                cur_scene["blocks"].append(("transition", m.group(1)))
            elif cur_ep is not None:
                cur_ep["meta_lines"].append(("__end__", m.group(1)))
            continue
        # 物件文字（如信封上的"凌霄服管 收"）
        m = QUOTE_RE.match(line)
        if m:
            if cur_scene is not None:
                cur_scene["blocks"].append(("quote", m.group(1)))
            continue
        # 对白：**角色**（括号）：台词 或 **角色**：台词
        m = DIALOGUE_RE.match(line)
        if m:
            char, paren, text = m.group(1), m.group(2), m.group(3)
            if cur_scene is not None:
                cur_scene["blocks"].append(("character", char))
                if paren:
                    cur_scene["blocks"].append(("paren", f"（{paren}）"))
                cur_scene["blocks"].append(("dialogue", text))
            continue
        # 动作：▲ 开头
        if line.startswith("▲"):
            if cur_scene is not None:
                cur_scene["blocks"].append(("action", line[1:].strip()))
            continue
        # 分隔线
        if line == "---":
            continue
        # 兜底：其他行（如未闭合括号的角色行）按动作处理，剥掉 **
        if cur_scene is not None:
            t = re.sub(r"^\*\*|\*\*$", "", line)
            cur_scene["blocks"].append(("action", t))
    flush_scene()
    return book_title, metas, episodes


# ---------------------------------------------------------------- EPUB 生成
CSS = """\
@page { margin: 1.5em; }
body { font-family: serif; line-height: 1.55; margin: 0; padding: 0; }
.cover { text-align: center; margin-top: 25%; }
.cover h1 { font-family: sans-serif; font-size: 1.7em; margin-bottom: 0.6em; }
.cover .meta { color: #666; font-size: 0.95em; margin-top: 1.2em; }
.cover .desc { color: #555; font-style: italic; margin: 0.6em 10%; font-size: 0.9em; }
.episode-title { font-family: sans-serif; font-size: 1.45em; text-align: center; margin: 0.5em 0 0.2em; page-break-before: always; }
.episode-meta { text-align: center; color: #777; font-size: 0.85em; margin-bottom: 1.2em; }
.scene { font-family: sans-serif; font-weight: bold; font-size: 1.05em; margin-top: 1.4em; margin-bottom: 0.2em; }
.scene-cast { color: #999; font-size: 0.82em; margin: 0 0 0.7em 0; }
.action { margin: 0.7em 0; text-align: justify; }
.character { font-family: sans-serif; font-weight: bold; text-align: center; margin-top: 1em; margin-bottom: 0.1em; }
.paren { text-align: center; font-style: italic; color: #555; margin: 0.15em 0 0.15em 12%; }
.dialogue { margin: 0.25em 12% 0.7em 12%; text-align: center; }
.quote { text-align: center; font-style: italic; color: #444; margin: 0.8em 15%; }
.transition { font-family: sans-serif; font-weight: bold; text-align: right; margin: 1em 0; }
.end-mark { text-align: center; font-weight: bold; margin: 1.4em 0; color: #333; }
.synopsis-head { font-family: sans-serif; font-size: 1.2em; margin-top: 1.2em; margin-bottom: 0.3em; }
.synopsis-ep { font-family: sans-serif; font-size: 1em; margin-top: 1em; margin-bottom: 0.2em; }
"""

CONTAINER_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


def esc(t):
    return html.escape(t, quote=False)


def render_scene(scene):
    parts = [f'<h2 class="scene">{esc(scene["slug"])}</h2>']
    if scene.get("cast"):
        parts.append(f'<p class="scene-cast">人物：{esc(scene["cast"])}</p>')
    for kind, payload in scene["blocks"]:
        if kind == "action":
            parts.append(f'<p class="action">{esc(payload)}</p>')
        elif kind == "character":
            parts.append(f'<p class="character">{esc(payload)}</p>')
        elif kind == "paren":
            parts.append(f'<p class="paren">{esc(payload)}</p>')
        elif kind == "dialogue":
            parts.append(f'<p class="dialogue">{esc(payload)}</p>')
        elif kind == "quote":
            parts.append(f'<p class="quote">“{esc(payload)}”</p>')
        elif kind == "transition":
            parts.append(f'<p class="transition">{esc(payload)}</p>')
    return "\n".join(parts)


def render_episode(ep):
    parts = [f'<h1 class="episode-title">第{ep["num"]}集《{esc(ep["title"])}》</h1>']
    for mline in ep["meta_lines"]:
        if isinstance(mline, tuple):
            continue
        parts.append(f'<p class="episode-meta">{esc(mline)}</p>')
    for scene in ep["scenes"]:
        parts.append(render_scene(scene))
    parts.append('<p class="end-mark">—— 本集完 ——</p>')
    return "\n".join(parts)


def build_xhtml(title, body):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>{esc(title)}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{body}
</body>
</html>
"""


def build_cover(title):
    parts = ['<section class="cover">']
    parts.append(f"<h1>{esc(title)}</h1>")
    parts.append("</section>")
    return "\n".join(parts)


# ---------------------------------------------------------------- 剧情概览（基于剧本撰写的梗概）
SYNOPSIS_OVERALL = (
    "凌霄镇连日\u201c闹鬼\u201d——路灯灭、招牌掉、门窗自开，七封举报信落在掌事案头。"
    "记录官服管受命查案，按册查线，发现所有机关的红石线都汇向镇中钟楼；"
    "搭档陈曦凭直觉认定钟楼底下有东西，实诚的郭平一路拆门打架。线索层层收紧："
    "老手艺蜡线指向工匠老穆，销户旧号\u201c老山\u201d动过钟楼地基，封存仓库三天前放走同批老料，"
    "镇南废宅的地道直通钟楼底下的镇史库。掌事限期三天，服管决定不等——"
    "夜探、砸锁、三线并行擒下老穆。老穆守库五年，只为护住初代\u201c黑户\u201d旧账；"
    "可账本离桌触发护库机关，众人靠陈曦早先刮下的蜡块脱险。老穆被逐，掌事公告了结，"
    "却私抽封存清单；镇史库留下第四人的脚印与一封空白信。服管对质掌事，"
    "只换来一句\u201c你知道得太多了\u201d。钟楼底下的旧账，牵连的远不止老穆一人。"
)

SYNOPSIS_EPISODES = {
    1: "掌事限期三天，把七封举报信交给服管。服管拆信对图，发现路灯、招牌、门窗三处机关的线都汇向钟楼；"
       "陈曦带阿黄说钟楼底下有东西，服管坚持\u201c先查记录\u201d。夜查路灯证实线往钟楼，"
       "服管道出\u201c线可能是故意引我们\u201d的两难推理，仍决定先查记录。",
    2: "招牌被剪线撬钩，线又通钟楼。拆线发现老法子封蜡，镇上只有老穆会。蹲守老孙，见其半夜进老穆家；"
       "工坊试探，老穆以\u201c两个徒弟走了\u201d从容应对。服管记下老孙\u201c半夜取灯\u201d的破绽，疑点汇聚向红石工坊。",
    3: "钟楼地基被动过，操作账号是销户旧号\u201c老山\u201d。伏击抓到搬运工大头，"
       "供出\u201c镇公所后门递铁锭、镇北旧工地收货\u201d的链条；封存仓库三天前放走同批老料，经办人空白。"
       "服管在钟楼地基撒红石粉布下探针。",
    4: "探针显示有人再来。服管下洞，发现\u201c镇史库\u201d石门与新换的锁。镇南废宅藏着机关阵与看守小疤，"
       "地下还有新挖地道直通钟楼——做机关是为掩护挖地道。服管封住洞口，等他们自己开门。",
    5: "对账发现仓库调走的料对不上数。陈曦夜探钟楼背面，刮下新蜡。掌事给三天限期，服管应下并锁定调拨单；"
       "封存账末页夹着\u201c三日前镇公所曾问及镇史库封存事宜\u201d。服管决定不再等。",
    6: "服管独自夜探，在石门前守候；陈曦带阿黄钻地道跟来，两人撞见等老穆开门的人，阿黄被打伤。"
       "次日夜里，服管出洞看见陈曦抱着凉透的麦饼守了一夜，第一次说\u201c我该听你的\u201d。"
       "两人砸锁，走进镇史库。",
    7: "服管支开郭平去镇北追旧料（真找到辙印与蜡线），自己留守镇史库；陈曦从侧洞潜入。"
       "老穆现身摊牌，服管受伤，陈曦郭平赶到擒下老穆。账本后半本是空的，老穆只说\u201c拿去镇公所，自然知道\u201d。",
    8: "老穆交代初代\u201c黑户\u201d旧事——父亲是被涂名的劳工，他守库五年为护父名与镇平静。"
       "服管决定交账走程序，账本离桌触发初代护库机关，陈曦的蜡块封线救场。公告栏结案，掌事私抽封存清单；"
       "镇史库留下第四人脚印与空白信。服管对质掌事，只换来\u201c你知道得太多了\u201d。",
}


def build_synopsis(episodes):
    title_by_num = {ep["num"]: ep["title"] for ep in episodes}
    parts = ['<h1 class="episode-title">剧情概览</h1>']
    parts.append('<h2 class="synopsis-head">全季梗概</h2>')
    parts.append(f'<p class="action">{esc(SYNOPSIS_OVERALL)}</p>')
    parts.append('<h2 class="synopsis-head">分集剧情发展脉络</h2>')
    for num in sorted(SYNOPSIS_EPISODES):
        ep_title = title_by_num.get(num, "")
        parts.append(f'<h3 class="synopsis-ep">第{num}集《{esc(ep_title)}》</h3>')
        parts.append(f'<p class="action">{esc(SYNOPSIS_EPISODES[num])}</p>')
    return "\n".join(parts)


def build_nav(title, episodes):
    items = ['<li><a href="cover.xhtml">封面</a></li>',
             '<li><a href="synopsis.xhtml">剧情概览</a></li>']
    for ep in episodes:
        items.append(f'<li><a href="ep{ep["num"]:02d}.xhtml">第{ep["num"]}集《{esc(ep["title"])}》</a></li>')
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head><meta charset="utf-8"/><title>目录</title></head>
<body>
<nav epub:type="toc" id="toc">
  <h1>目录</h1>
  <ol>
    {chr(10).join(items)}
  </ol>
</nav>
</body>
</html>
"""


def build_opf(title, episodes):
    uid = "spl-" + re.sub(r"[^a-z0-9]", "-", title.lower())[:40]
    manifest = ['    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '    <item id="css" href="style.css" media-type="text/css"/>',
                '    <item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
                '    <item id="synopsis" href="synopsis.xhtml" media-type="application/xhtml+xml"/>']
    spine = ['    <itemref idref="cover"/>',
             '    <itemref idref="synopsis"/>']
    for ep in episodes:
        iid = f"ep{ep['num']:02d}"
        manifest.append(f'    <item id="{iid}" href="{iid}.xhtml" media-type="application/xhtml+xml"/>')
        spine.append(f'    <itemref idref="{iid}"/>')
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:{uid}</dc:identifier>
    <dc:title>{esc(title)}</dc:title>
    <dc:language>zh-CN</dc:language>
    <meta property="dcterms:modified">2026-09-05T00:00:00Z</meta>
  </metadata>
  <manifest>
{chr(10).join(manifest)}
  </manifest>
  <spine>
{chr(10).join(spine)}
  </spine>
</package>
"""


def write_epub(title, metas, episodes, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    cover_xhtml = build_xhtml(title, build_cover(title))
    synopsis_xhtml = build_xhtml("剧情概览", build_synopsis(episodes))
    nav = build_nav(title, episodes)
    opf = build_opf(title, episodes)
    ep_xhtmls = {f"ep{ep['num']:02d}": build_xhtml(
        f"第{ep['num']}集《{ep['title']}》", render_episode(ep)) for ep in episodes}

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", CONTAINER_XML)
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr("OEBPS/nav.xhtml", nav)
        zf.writestr("OEBPS/style.css", CSS)
        zf.writestr("OEBPS/cover.xhtml", cover_xhtml)
        zf.writestr("OEBPS/synopsis.xhtml", synopsis_xhtml)
        for name, body in ep_xhtmls.items():
            zf.writestr(f"OEBPS/{name}.xhtml", body)
    return True


def main():
    if len(sys.argv) < 2:
        print("用法：python v3_to_epub.py 剧本.md [-o 输出.epub]")
        sys.exit(1)
    src = sys.argv[1]
    out = None
    if "-o" in sys.argv:
        out = sys.argv[sys.argv.index("-o") + 1]
    if not out:
        base = os.path.splitext(os.path.basename(src))[0]
        out = os.path.join(os.path.dirname(os.path.abspath(src)), base + ".epub")

    with open(src, encoding="utf-8") as f:
        text = f.read()
    title, metas, episodes = parse_script(text)
    if not episodes:
        print(f"错误：未能解析出集标题（{src} 可能不是 v3 剧本格式）")
        sys.exit(1)
    write_epub(title, metas, episodes, out)
    n_scenes = sum(len(ep["scenes"]) for ep in episodes)
    print(f"✅ EPUB 导出完成：{out}")
    print(f"   集数：{len(episodes)}｜场数：{n_scenes}")
    sys.exit(0)


if __name__ == "__main__":
    main()
