#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md_to_txt.py — 把 v4 剧本 md 转为干净可读的 txt（纯文本，无任何标记语法）"""
import re
import sys

src = sys.argv[1]
out = sys.argv[2]
s = open(src, encoding='utf-8').read()

# 1) 去掉 YAML frontmatter，改成文件头的项目信息
if s.startswith('---'):
    end = s.index('\n---', 3)
    fm = s[3:end].strip()
    s = s[end + 4:]
    meta = {}
    for line in fm.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    head = [meta.get('title', ''), '']
    if meta.get('logline'):
        head += ['一句话故事：' + meta['logline']]
    if meta.get('controlling-idea'):
        head += ['主控思想：' + meta['controlling-idea']]
    if meta.get('runtime'):
        head += ['篇幅：' + meta['runtime']]
    s = '\n'.join(head) + '\n\n' + s

# 2) 集标记：<!-- 第N集《X》 --> + > **第N集《X》**  → 只留一行
s = re.sub(r'<!-- (第\d+集《[^》]+》) -->\n> \*\*\1\*\*', r'================  \1  ================', s)
s = re.sub(r'^> \*\*(第\d+集《[^》]+》)\*\*$', r'================  \1  ================', s, flags=re.M)
s = re.sub(r'^<!--.*?-->$', '', s, flags=re.M)

# 3) 场景标题：# INT. 地点 - 时间，内外 [场号] → 【场号】地点（时间）
def scene(m):
    loc, tm, num = m.group(2).strip(), m.group(3).strip(), (m.group(4) or '').strip()
    return f'【{num}】{loc}　（{tm}）' if num else f'{loc}　（{tm}）'
s = re.sub(r'^# (INT\./EXT\.|INT\.|EXT\.|I/E\.)\s*(.+?)\s*-\s*(.+?)\s*(?:\[([^\]]+)\])?$', scene, s, flags=re.M)

# 4) 人物行：人物：xxx → 【人物】 xxx
s = re.sub(r'^人物[：:]\s*(.+)$', r'【人物】\1', s, flags=re.M)

# 5) 台词：**角色**（提示）：台词 → 角色（提示）：台词
s = re.sub(r'^\*\*(.+?)\*\*（(.+?)）[：:]\s*(.*)$', r'\1（\2）：\3', s, flags=re.M)
s = re.sub(r'^\*\*(.+?)\*\*\s*[：:]\s*(.*)$', r'\1：\2', s, flags=re.M)

# 6) 转场 / 黑屏 / 【本集完】等保留；多余空行压缩
s = re.sub(r'\n>\s*(\*\*)?(.+?)(\*\*)?\s*$', r'\n［\2］', s, flags=re.M)
s = s.replace('<!--', '').replace('-->', '')
s = re.sub(r'\n{3,}', '\n\n', s).strip() + '\n'

open(out, 'w', encoding='utf-8', newline='\r\n').write(s)
han = len(re.findall(r'[\u4e00-\u9fff]', s))
print(f'✅ 已生成：{out}')
print(f'   汉字 {han}｜总字符 {len(s)}｜行数 {s.count(chr(10))}')
