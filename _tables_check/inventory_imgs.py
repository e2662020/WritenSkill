# -*- coding: utf-8 -*-
"""盘点各 epub 的图片清单 + 在正文中的上下文；检查 pdf 页内图片。"""
import re
import zipfile
from pathlib import Path

SRC = Path(r"C:\Users\RATE\编剧入门教程")
OUT = Path(r"C:\Users\RATE\WritenSkill\_tables_check")

IMG_EXT = (".jpeg", ".jpg", ".png", ".gif", ".webp", ".bmp")


def epub_images(path: Path):
    print("=" * 70)
    print("EPUB:", path.name[:45])
    with zipfile.ZipFile(path) as z:
        imgs = [n for n in z.namelist() if n.lower().endswith(IMG_EXT)]
        print(f"图片文件数: {len(imgs)}")
        # 找 xhtml 中 img 引用
        refs = []
        for n in sorted(z.namelist()):
            if not n.lower().endswith((".html", ".xhtml", ".htm")):
                continue
            data = z.read(n).decode("utf-8", "ignore")
            for m in re.finditer(r'<img[^>]+src="([^"]+)"[^>]*>', data):
                src = m.group(1).split("/")[-1].split("?")[0]
                ctx = data[max(0, m.start() - 350):m.start()]
                ctx_txt = re.sub(r"<[^>]+>", " ", ctx)
                ctx_txt = re.sub(r"\s+", " ", ctx_txt).strip()
                refs.append((n, src, ctx_txt[-120:]))
        print(f"正文中引用图片: {len(refs)} 处")
        for n, src, ctx in refs:
            print(f"  [{src}]  {n}")
            print(f"       前文: {ctx}")
        unused = [i for i in imgs if i not in {r[1] for r in refs}]
        if unused:
            print("  未被正文引用（封面/资源）:", unused[:10])


def pdf_images(path: Path):
    print("=" * 70)
    print("PDF:", path.name[:45])
    import fitz
    doc = fitz.open(str(path))
    total = 0
    for pno in range(doc.page_count):
        page = doc[pno]
        imgs = page.get_images(full=True)
        if imgs:
            total += len(imgs)
            if total <= 15:
                txt = page.get_text("text").strip().replace("\n", " ")[:80]
                print(f"  第{pno+1}页: {len(imgs)} 张图 | 该页文本: {txt}")
    doc.close()
    print(f"  PDF 图片总张数: {total}")


def main():
    for epub in sorted(SRC.glob("*.epub")):
        if "写作兵器库" not in epub.name:
            epub_images(epub)
    pdf = [p for p in SRC.glob("*.pdf")][0]
    pdf_images(pdf)


if __name__ == "__main__":
    main()
