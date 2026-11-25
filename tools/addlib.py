# -*- coding: utf-8 -*-
"""入库公用件：块构造、n 推算、源稿回填、幂等追加。

各批 add_articles_*.py 只负责写 ENTRIES 数据，剩下的交给这里。
"""
import io
import json
import os
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "tools", "articles.json")
SRC = os.path.join(ROOT, "人间防骗指南.md")


def p(t):
    return {"k": "p", "t": t}


def sec(t):
    return {"k": "sec", "t": t}


def step(t):
    return {"k": "step", "t": t}


def warn(t):
    return {"k": "warn", "t": t}


def trap(t):
    return {"k": "trap", "t": t}


def law(t):
    return {"k": "law", "t": t}


def tip(t):
    return {"k": "tip", "t": t}


def end(t):
    return {"k": "end", "t": t}


def make_n(body):
    return {
        "step": sum(1 for b in body if b["k"] == "step"),
        "trap": sum(1 for b in body if b["k"] in ("warn", "trap")),
        "tip": sum(1 for b in body if b["k"] in ("tip", "end")),
    }


def build_raw(a):
    """从结构化条目反推源稿原文（标题行按 looks_like_title 规则清洗）。"""
    prefix = a.get("prefix", "🚨 【黑产揭秘】")
    title_line = prefix + a["title"].replace("：", "，")
    body_text = "\n".join(b["t"] for b in a["body"])
    tag_line = " ".join("#" + t for t in a["tags"])
    return title_line + "\n\n" + body_text + "\n\n" + tag_line + "\n"


def append(entries, rebuild=True):
    arts = json.load(io.open(ART, encoding="utf-8"))
    existing = {a["title"] for a in arts}
    start = max((a["id"] for a in arts), default=0)
    added = []
    for i, a in enumerate(entries):
        a = dict(a)
        if a["title"] in existing:
            print("已存在，跳过：%s" % a["title"][:36])
            continue
        a["id"] = start + len(added) + 1
        a["n"] = make_n(a["body"])
        rec = {
            "id": a["id"],
            "title": a["title"],
            "icon": a["icon"],
            "col": a.get("col", "黑产揭秘"),
            "points": a["points"],
            "guards": a["guards"],
            "cat": a["cat"],
            "tags": a["tags"],
            "lead": a["lead"],
            "risks": a["risks"],
            "targets": a["targets"],
            "n": a["n"],
            "body": a["body"],
        }
        arts.append(rec)
        existing.add(a["title"])
        added.append(rec)
        print("追加 %d《%s》 n=%s" % (rec["id"], rec["title"][:34], rec["n"]))

    with io.open(ART, "w", encoding="utf-8") as f:
        json.dump(arts, f, ensure_ascii=False, indent=1)
    print("articles.json：%d 篇（新增 %d）" % (len(arts), len(added)))

    txt = io.open(SRC, encoding="utf-8").read()
    for rec in added:
        marker = rec["title"][:12]
        if marker in txt:
            print("源稿已存在，跳过：%s" % rec["title"][:34])
            continue
        txt = txt.rstrip("\n") + "\n\n" + build_raw(rec).rstrip("\n") + "\n"
        io.open(SRC, "w", encoding="utf-8").write(txt)
        print("源稿已追加：%s" % rec["title"][:34])

    if rebuild:
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "rebuild_site.py")], check=False)
    return added
