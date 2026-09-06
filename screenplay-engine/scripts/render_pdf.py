#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_pdf.py — SPL 剧本渲染器（Screenplay Language -> 标准格式 PDF）

用法:
    python render_pdf.py 剧本.md [-o 输出.pdf]

解析 SPL（见 references/spl-spec.md），按好莱坞标准剧本格式排版输出 PDF：
    场景标题左对齐加粗 / 动作左对齐 / 角色名居中大写 / 对白居中缩进块 /
    括号提示 / 转场右对齐 / 页眉页码 / 封面页。

字体：
    优先 Noto Sans SC（静态或可变字体，可变字体用 fontTools 实例化出
    Medium(500)/Bold(700) 两个静态字形——VF 默认实例为 Thin(100)，直接用会
    偏细，故常规取 500、粗体取 700）；回退 SimHei / Noto CJK / 系统字体。
排版：
    正文字号 11pt（略小于行业 12pt 以适配中文渲染观感），行高 5.3mm ≈ 字号
    1.36 倍（满足 >=1.25 倍行距要求）。
    角色名 / 括号提示 / 对白三块之间各留一个空行（一倍行距），避免对白块
    过于紧凑。

依赖: fpdf2 + fonttools (pip install fpdf2 fonttools)。
退出码: 0 成功 / 1 解析或渲染失败
"""
import sys
import re
import os
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ---------------------------------------------------------------- SPL 解析
SLUG_RE = re.compile(r"^#\s+(INT\./EXT\.|I/E\.|INT/EXT|INT\.|EXT\.)\s+(.+?)\s*-\s*(.+?)\s*(?:\[(\d+)\])?$")
SHOT_RE = re.compile(r"^##\s+(.+)$")
TRANS_RE = re.compile(r"^>\s*(.+)$")
MONTAGE_RE = re.compile(r"^##\s+蒙太奇\s*(.*)$")
CHAR_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
PAREN_RE = re.compile(r"^（.+?）$")
OLIST_RE = re.compile(r"^\d+\.\s+(.+)$")

KNOWN_TRANSITIONS = {"FADE IN:", "CUT TO:", "SMASH CUT TO:", "DISSOLVE TO:",
                     "FADE OUT.", "FADE OUT", "MATCH CUT TO:", "JUMP CUT TO:"}


def parse_frontmatter(text):
    """提取 YAML frontmatter，返回 (meta dict, 正文起始行号)。"""
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
    """把 SPL 正文解析为元素列表 [(kind, payload, line_no), ...]。"""
    meta, start = parse_frontmatter(text)
    elements = []
    lines = text.splitlines()
    in_montage = False
    expect_dialogue = False      # 最近出现角色提示，期待对白
    last_was_dialogue = False

    for idx in range(start - 1, len(lines)):
        ln = idx + 1
        raw = lines[idx]
        line = raw.strip()

        if not line:
            if expect_dialogue and not last_was_dialogue:
                pass  # 允许角色提示后空行再对白
            last_was_dialogue = False
            continue

        if line.startswith("%% "):
            elements.append(("comment", line[3:].strip(), ln))
            continue
        if line == "---":
            elements.append(("pagebreak", "", ln))
            in_montage = False
            expect_dialogue = False
            last_was_dialogue = False
            continue
        if line.startswith("###"):
            elements.append(("error", f"不支持的三级标题（第{ln}行）：{line}", ln))
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
            elements.append(("error", f"场景标题缺少内/外景前缀（第{ln}行）：{line}，应为「# INT./EXT. 地点 - 时间」", ln))
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
            else:
                elements.append(("error", f"括号提示出现在无对白上下文（第{ln}行）：{line}", ln))
            continue

        if expect_dialogue or last_was_dialogue:
            elements.append(("dialogue", line, ln))
            last_was_dialogue = True
            expect_dialogue = False
            continue

        elements.append(("action", line, ln))
        last_was_dialogue = False

    return meta, elements


# ---------------------------------------------------------------- 字体探测
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BUNDLED_FONTS = os.path.join(_SCRIPT_DIR, "..", "assets", "fonts")

# 技能自带的静态 Noto Sans SC（已从 VF 实例化，修正所有 nameID 与 usWeightClass）
BUNDLED_REGULAR = os.path.join(_BUNDLED_FONTS, "NotoSansSC-SemiBold.ttf")
BUNDLED_BOLD = os.path.join(_BUNDLED_FONTS, "NotoSansSC-ExtraBold.ttf")

NOTO_STATIC_CANDIDATES = [
    r"C:\Windows\Fonts\NotoSansSC-Regular.otf",
    r"C:\Windows\Fonts\NotoSansSC-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansSC-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
    "/System/Library/Fonts/Supplemental/NotoSansSC-Regular.otf",
    "/Library/Fonts/NotoSansSC-Regular.otf",
]
NOTO_VF_CANDIDATES = [
    r"C:\Windows\Fonts\NotoSansSC-VariableFont_wght.ttf",
    r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
]
NOTO_BOLD_STATICS = [
    r"C:\Windows\Fonts\NotoSansSC-Bold.otf",
    r"C:\Windows\Fonts\NotoSansSC-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]
CJK_FALLBACK = [
    r"C:\Windows\Fonts\simhei.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]

_VF_TABLES = {"fvar", "gvar", "HVAR", "MVAR", "STAT", "avar", "cvar", "VVAR", "DSIG"}


def _instantiate_vf(vf_path, wght, cache_dir):
    """把可变字体实例化为静态 TTF，并删除所有可变字体表。返回路径。"""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    tag = os.path.splitext(os.path.basename(vf_path))[0]
    out = os.path.join(cache_dir, f"{tag}-wght{wght}-static.ttf")
    if os.path.exists(out):
        return out
    font = TTFont(vf_path)
    instantiateVariableFont(font, {"wght": wght})
    for t in list(font.keys()):
        if t in _VF_TABLES:
            del font[t]
    font.save(out)
    return out


def find_cjk_fonts(cache_dir):
    """返回 {regular, bold, italic} 字体文件路径 dict，找不到返回 None。

    优先级：技能自带静态 Noto -> 系统静态 Noto -> VF 实例化 -> 其他 CJK。
    """
    # 1) 技能自带静态字体（最优先，已确保 fvar 已删除）
    if os.path.exists(BUNDLED_REGULAR):
        bold = BUNDLED_BOLD if os.path.exists(BUNDLED_BOLD) else BUNDLED_REGULAR
        return {"regular": BUNDLED_REGULAR, "bold": bold, "italic": BUNDLED_REGULAR}
    # 2) 系统静态常规 + 粗体
    for p in NOTO_STATIC_CANDIDATES:
        if os.path.exists(p):
            bold = None
            for bp in NOTO_BOLD_STATICS:
                if os.path.exists(bp):
                    bold = bp
                    break
            if bold is None:
                alt = p.replace("-Regular", "-Bold")
                if os.path.exists(alt):
                    bold = alt
            return {"regular": p, "bold": bold or p, "italic": p}
    # 3) 可变字体 -> 实例化 Regular(400)/Bold(700) 并删 fvar
    for p in NOTO_VF_CANDIDATES:
        if os.path.exists(p):
            try:
                reg = _instantiate_vf(p, 400, cache_dir)
                bold = _instantiate_vf(p, 700, cache_dir)
                return {"regular": reg, "bold": bold, "italic": reg}
            except Exception:
                continue
    # 4) 其他 CJK 回退
    for p in CJK_FALLBACK:
        if os.path.exists(p):
            return {"regular": p, "bold": p, "italic": p}
    return None


def find_mono_font():
    """探测可用的等宽英文字体（TTF）。返回路径或 None。"""
    candidates = [
        r"C:\Windows\Fonts\cour.ttf",
        r"C:\Windows\Fonts\consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ---------------------------------------------------------------- PDF 渲染
FS = 11          # 正文字号 pt（行业 12pt，中文观感下调至 11pt）
LH = 5.3         # 正文行高 mm（11pt*1.36 ≈ 1.36 倍行距，满足 >=1.25）


def render_pdf(meta, elements, out_path):
    try:
        from fpdf import FPDF
    except ImportError:
        print("错误：缺少 fpdf2。请先安装：pip install fpdf2 fonttools")
        sys.exit(1)

    cache_dir = os.path.join(tempfile.gettempdir(), "spl_fontcache")
    os.makedirs(cache_dir, exist_ok=True)
    cjk = find_cjk_fonts(cache_dir)
    if cjk:
        print(f"字体：Noto Sans SC（{os.path.basename(cjk['regular'])}）"
              + (f" + Bold（{os.path.basename(cjk['bold'])}）" if cjk.get("bold") and cjk["bold"] != cjk["regular"] else ""))

    class ScreenplayPDF(FPDF):
        _cjk = cjk

        def header(self):
            if self.page_no() <= 1:
                return
            title = meta.get("title", "")
            author = meta.get("author", "")
            head = title + (f" · {author}" if author else "")
            self.set_font("CJK" if self._cjk else "SP", "", 9)
            self.set_text_color(90, 90, 90)
            self.set_y(10)
            self.cell(0, 4.5, head, align="C")
            self.set_draw_color(180, 180, 180)
            self.line(25.4, 16, 210 - 25.4, 16)
            self.set_y(25.4)

        def footer(self):
            if self.page_no() <= 1:
                return
            self.set_y(-15)
            self.set_font("CJK" if self._cjk else "SP", "", 9)
            self.set_text_color(90, 90, 90)
            self.cell(0, 4.5, str(self.page_no()), align="R")

    pdf = ScreenplayPDF(format="A4")
    pdf.set_auto_page_break(True, margin=25.4)
    mono_path = find_mono_font()
    if mono_path:
        try:
            pdf.add_font("SP", "", mono_path)
        except Exception:
            mono_path = None
    if cjk:
        try:
            pdf.add_font("CJK", "", cjk["regular"])
            pdf.add_font("CJK", "B", cjk.get("bold") or cjk["regular"])
            pdf.add_font("CJK", "I", cjk["italic"])
        except Exception:
            cjk = None
    # 无等宽字体时用 fpdf2 内置 courier 兜底；无中文字体时中文可能无法显示
    mono = "SP" if mono_path else "courier"

    LEFT = 38.1      # 1.5 inch
    RIGHT = 25.4     # 1 inch
    ACTION_W = 210 - LEFT - RIGHT   # 6 inch
    DIALOG_LEFT = 63.5              # 2.5 inch
    DIALOG_W = 210 - DIALOG_LEFT * 2
    CENTER_X = 210 / 2

    def font_for(kind):
        return "CJK" if cjk else mono

    def set_style(kind):
        bold = kind in ("scene", "character", "transition")
        if kind == "parenthetical":
            pdf.set_font(font_for(kind), "I", FS)
        elif bold:
            pdf.set_font(font_for(kind), "B", FS)
        else:
            pdf.set_font(font_for(kind), "", FS)
        pdf.set_text_color(0, 0, 0)

    # ---------- 封面页 ----------
    pdf.add_page()
    pdf.set_font(font_for("scene"), "B", 24)
    pdf.set_y(90)
    title = meta.get("title", "UNTITLED")
    pdf.multi_cell(0, 11, title, align="C")
    pdf.ln(4)
    if meta.get("author"):
        pdf.set_font(font_for("dialogue"), "", 13)
        pdf.cell(0, 8, meta["author"], align="C")
    pdf.ln(16)
    pdf.set_font(font_for("dialogue"), "", 11)
    info = []
    if meta.get("type"):
        info.append(meta["type"])
    if meta.get("genre"):
        info.append(meta["genre"])
    if meta.get("runtime"):
        info.append(meta["runtime"])
    if info:
        pdf.cell(0, 7, " / ".join(info), align="C")
        pdf.ln(8)
    if meta.get("logline"):
        pdf.set_font(font_for("dialogue"), "I", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 6.5, meta["logline"], align="C")
    pdf.add_page()

    # ---------- 正文 ----------
    for kind, payload, _ln in elements:
        if kind == "comment":
            continue
        if kind == "pagebreak":
            pdf.add_page()
            continue

        set_style(kind)

        if kind == "scene":
            pdf.ln(2)
            pdf.set_x(LEFT)
            pdf.multi_cell(ACTION_W, LH, payload.upper(), align="L")
            pdf.ln(2)
        elif kind == "shot":
            pdf.ln(1)
            pdf.set_x(LEFT)
            pdf.multi_cell(ACTION_W, LH, payload, align="L")
        elif kind == "montage":
            pdf.ln(2)
            pdf.set_font(font_for("shot"), "B", FS)
            pdf.set_x(LEFT)
            pdf.cell(0, LH, payload.upper(), align="L")
            pdf.ln(LH)
        elif kind == "montage_item":
            pdf.set_x(LEFT + 10)
            pdf.multi_cell(ACTION_W - 10, LH, payload, align="L")
            pdf.ln(1)
        elif kind == "action":
            pdf.set_x(LEFT)
            pdf.multi_cell(ACTION_W, LH, payload, align="L")
            pdf.ln(2)
        elif kind == "character":
            pdf.ln(2)
            pdf.set_x(0)
            w = pdf.get_string_width(payload.upper()) + 6
            pdf.set_x(max(CENTER_X - w / 2, 0))
            pdf.cell(w, LH, payload.upper(), align="C")
            pdf.ln(2 * LH)   # 角色名与下方括号/对白之间留一倍空行
        elif kind == "parenthetical":
            # 括号提示放在对白块内，比对白多缩进约 0.5"
            px = DIALOG_LEFT + 12.7
            pw = DIALOG_W - 25.4
            pdf.set_x(px)
            pdf.multi_cell(pw, LH, payload, align="L")
            pdf.ln(2 * LH)   # 括号提示与对白之间留一倍空行
        elif kind == "dialogue":
            pdf.set_x(DIALOG_LEFT)
            if pdf.get_string_width(payload) <= DIALOG_W - 2:
                # 单行对白居中
                pdf.cell(DIALOG_W, LH, payload, align="C",
                         new_x="LMARGIN", new_y="NEXT")
            else:
                # 多行对白左对齐
                pdf.multi_cell(DIALOG_W, LH, payload, align="L")
            pdf.ln(1)
        elif kind == "transition":
            pdf.ln(3)
            pdf.set_x(0)
            w = pdf.get_string_width(payload.upper()) + 4
            pdf.set_x(210 - RIGHT - w)
            pdf.cell(w, LH, payload.upper(), align="R")
            pdf.ln(LH)
        elif kind == "error":
            print(f"警告：{payload}")

    pdf.output(out_path)
    return True


def main():
    if len(sys.argv) < 2:
        print("用法：python render_pdf.py 剧本.md [-o 输出.pdf]")
        sys.exit(1)
    src = sys.argv[1]
    out = None
    if "-o" in sys.argv:
        out = sys.argv[sys.argv.index("-o") + 1]
    if not out:
        out = os.path.splitext(src)[0] + ".pdf"

    if not os.path.exists(src):
        print(f"错误：文件不存在 {src}")
        sys.exit(1)
    with open(src, encoding="utf-8") as f:
        text = f.read()

    meta, elements = parse_spl(text)
    errors = [p for k, p, _ in elements if k == "error"]
    if errors:
        print("解析警告（可继续渲染）：")
        for e in errors:
            print("  -", e)

    render_pdf(meta, elements, out)
    print(f"✅ 渲染完成：{out}")
    print(f"   场景数：{sum(1 for k, _, _ in elements if k == 'scene')}，"
          f"页数：{len(open(out, 'rb').read()) and '见文件'}")
    sys.exit(0)


if __name__ == "__main__":
    main()
