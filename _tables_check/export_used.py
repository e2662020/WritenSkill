# -*- coding: utf-8 -*-
"""导出其他书籍的正文引用图片到独立子目录。"""
import re
import zipfile
import shutil
from pathlib import Path

SRC = Path(r"C:\Users\RATE\编剧入门教程")
OUT = Path(r"C:\Users\RATE\WritenSkill\_tables_check")
IMG_EXT = (".jpeg", ".jpg", ".png", ".gif", ".webp", ".bmp")


def export_used(path: Path, folder: str):
    target = OUT / folder
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    used = set()
    with zipfile.ZipFile(path) as z:
        for n in sorted(z.namelist()):
            if not n.lower().endswith((".html", ".xhtml", ".htm")):
                continue
            data = z.read(n).decode("utf-8", "ignore")
            for m in re.finditer(r'<img[^>]+src="([^"]+)"[^>]*>', data):
                src = m.group(1).split("/")[-1].split("?")[0]
                used.add(src)
        for n in z.namelist():
            base = n.split("/")[-1]
            if base in used:
                with open(target / base, "wb") as f:
                    f.write(z.read(n))
            else:
                # 兼容 epub 内部引用路径与实际文件名不完全一致的情况
                for u in used:
                    if n.lower().endswith(u.lower()):
                        with open(target / u, "wb") as f:
                            f.write(z.read(n))
                        break
    print(f"{folder}: 导出 {len(list(target.iterdir()))} 张 -> {target}")


def main():
    for epub in sorted(SRC.glob("*.epub")):
        if "写作兵器库" in epub.name:
            continue
        folder = epub.stem[:10].strip().rstrip("：:") or "book"
        export_used(epub, folder)


if __name__ == "__main__":
    main()
