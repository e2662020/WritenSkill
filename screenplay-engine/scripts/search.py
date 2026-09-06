#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search.py — 剧本引擎知识库检索器

用法:
    python search.py "<关键词>" --domain beats|genres|archetypes|dialogue-moves|pitfalls [-n 结果数] [--all]

按关键词在 data/*.csv 中检索（中文子串匹配 + 英文分词匹配，标题字段加权），
返回相关行及其全部字段，供写作/诊断时快速取用。

退出码: 0 成功 / 1 参数错误或文件缺失
"""
import sys
import os
import csv
import re

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data")

DOMAINS = {
    "beats": "beats.csv",
    "genres": "genres.csv",
    "archetypes": "archetypes.csv",
    "dialogue-moves": "dialogue-moves.csv",
    "pitfalls": "pitfalls.csv",
}

FIELD_WEIGHT = {"id": 0, "name": 2, "beat": 2, "genre": 2, "archetype": 2,
                "move": 2, "pitfall": 2, "definition": 1.5, "function": 1.5,
                "value_axis": 1.5, "need": 1.5, "flaw": 1.5, "symptom": 1.5,
                "fix": 1.5, "example": 1, "example_films": 1.5,
                "example_line": 1.5, "effect": 1.5, "reverse_moves": 1.5,
                "antipattern": 1.5, "severity": 0.5, "arc": 1, "position": 1,
                "structure": 1}


def load_rows(domain):
    path = os.path.join(DATA_DIR, DOMAINS[domain])
    if not os.path.exists(path):
        print(f"错误：数据文件不存在 {path}")
        sys.exit(1)
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def tokenize(text):
    """中文按连续子串处理，英文/数字分词。"""
    tokens = set(re.findall(r"[a-zA-Z0-9]+", text.lower()))
    return tokens


def score_row(row, query_terms, query_lower):
    score = 0.0
    for k, v in row.items():
        if not v:
            continue
        w = FIELD_WEIGHT.get(k, 1.0)
        vl = v.lower()
        # 中文子串匹配
        for q in query_terms:
            if q and q in vl:
                score += w * 2 * len(q)
        # 英文分词匹配
        for t in tokenize(vl):
            if t in query_terms:
                score += w * 2
        # 全字段重合度（对短查询敏感）
        if len(query_lower) >= 2 and query_lower in vl:
            score += w
    return score


def main():
    if len(sys.argv) < 3:
        print("用法：python search.py \"<关键词>\" --domain beats|genres|archetypes|dialogue-moves|pitfalls [-n N] [--all]")
        print("示例：python search.py \"越狱 希望\" --domain genres")
        print("      python search.py \"请求\" --domain dialogue-moves")
        sys.exit(1)

    query = sys.argv[1]
    domain = None
    limit = 5
    show_all = False
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--domain" and i + 1 < len(sys.argv):
            domain = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "-n" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--all":
            show_all = True
            i += 1
        else:
            i += 1

    if domain not in DOMAINS:
        print(f"错误：--domain 必须是 {', '.join(DOMAINS)} 之一")
        sys.exit(1)

    rows = load_rows(domain)
    query_lower = query.lower()
    query_terms = {t for t in re.split(r"[\s,，、/]+", query_lower) if t}

    scored = [(score_row(r, query_terms, query_lower), r) for r in rows]
    scored.sort(key=lambda x: -x[0])

    if show_all:
        picked = rows
    else:
        picked = [r for s, r in scored if s > 0][:limit]
        if not picked:
            print(f"未找到与「{query}」相关的结果。换关键词，或 --all 查看全表。")
            sys.exit(0)

    keys = list(picked[0].keys()) if picked else []
    print(f"知识库：{domain}（{len(rows)} 条） | 查询：「{query}」 | 返回 {len(picked)} 条")
    print("=" * 70)
    for r in picked:
        print(f"[{r.get('id','')}] {r.get(next((k for k in keys if k in ('beat','genre','archetype','move','pitfall')), ''), '')}")
        for k in keys:
            if k in ("id", "beat", "genre", "archetype", "move", "pitfall"):
                continue
            if r.get(k):
                print(f"   {k}: {r[k]}")
        print("-" * 70)


if __name__ == "__main__":
    main()
