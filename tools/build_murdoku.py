# -*- coding: utf-8 -*-
"""生成《识骗迷局》题库，并把它打包成一个单文件 HTML。

流程：tools/murdoku_content.py（内容） → 引擎出题 → 唯一解校验 → 打包
用法： python tools/build_murdoku.py
"""
import base64
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from murdoku_content import LEVELS, CHAPTERS, FOCUS, MIN_CLUES, MIN_LEVEL    # noqa: E402
from murdoku_engine import (ZONE, make_puzzle, make_hints,        # noqa: E402
                            count_solutions, propagate)

OUT_DIR = os.path.join(ROOT, "game-adaptations", "识骗迷局")
CHARS = {"骗": "pianzi", "受害": "shouhaizhe", "警": "jingcha", "路": "luren"}
RISK_NOTE = "本案在原文里标注了法律责任风险。"


def build_level(spec):
    names = [r["name"] for r in spec["roles"]]
    victim = next(r["name"] for r in spec["roles"] if r["camp"] == "受害")
    scammer = next(r["name"] for r in spec["roles"] if r["camp"] == "骗")
    focus = FOCUS.get(spec["id"], {})
    pz = make_puzzle(
        names, spec["zones"], spec["rows"], spec["seed"],
        n_given=spec.get("given", 2),
        max_clues=spec.get("max_clues", 12),
        max_direct=spec.get("max_direct", 3),
        min_clues=MIN_CLUES.get(spec["chapter"], 6),
        min_level=MIN_LEVEL.get(spec["chapter"], 1),
        victim_zone=focus.get("victim"), scammer_zone=focus.get("scammer"),
        victim=victim, scammer=scammer,
    )
    if not pz:
        raise SystemExit("出题失败：%s" % spec["id"])
    sol = {n: tuple(v) for n, v in pz["sol"].items()}
    # 二次独立验题：不许有双解，不许需要猜
    sols = count_solutions(names, pz["clues"], {n: tuple(v) for n, v in pz["given"].items()}, limit=2)
    status, _, _ = propagate(names, pz["clues"], {n: tuple(v) for n, v in pz["given"].items()})
    assert len(sols) == 1, "%s 有 %d 个解" % (spec["id"], len(sols))
    assert status == "solved", "%s 不能纯逻辑推完" % spec["id"]
    assert sols[0] == sol, "%s 校验解与设计解不一致" % spec["id"]

    vr, vc = sol[victim]
    sr, sc = sol[scammer]
    lv = {
        "id": spec["id"],
        "chapter": spec["chapter"],
        "index": spec["index"],
        "seed": spec["seed"],
        "title": spec["title"],
        "article": spec["article"],
        "scene": spec["scene"],
        "case": spec["case"],
        "zones": spec["zones"],
        "rows": spec["rows"],
        "roles": [{"name": r["name"], "camp": r["camp"], "icon": CHARS[r["camp"]],
                   "desc": r["desc"]} for r in spec["roles"]],
        "given": [{"name": n, "r": v[0], "c": v[1]} for n, v in pz["given"].items()],
        "clues": [{"t": c["t"], "k": c["k"], "a": c["a"], "p": c["p"]} for c in pz["clues"]],
        "sol": {n: {"r": v[0], "c": v[1]} for n, v in pz["sol"].items()},
        "victim": victim,
        "scammer": scammer,
        "answer": {
            "victim": {"name": victim, "row": vr + 1, "col": vc + 1,
                       "zone": ZONE[(vr, vc)] + 1, "zoneName": spec["zones"][ZONE[(vr, vc)]]},
            "scammer": {"name": scammer, "row": sr + 1, "col": sc + 1,
                        "zone": ZONE[(sr, sc)] + 1, "zoneName": spec["zones"][ZONE[(sr, sc)]]},
        },
        "hints": make_hints(names, sol, spec["zones"], spec["rows"], pz["clues"], victim, scammer),
        "pick": spec["pick"],
        "review": spec["review"],
        "crime": spec["review"].get("crime", ""),
        "difficulty": pz["level"],
        "clueCount": len(pz["clues"]),
    }
    return lv, sol


def load_chars(size=224):
    """角色棋子转 base64 内联（单文件必须自带图）。

    有 Pillow 就先缩到 size×size 并做量化压缩——原始 512 的图会让单文件涨到 1MB+。
    """
    out = {}
    try:
        from PIL import Image
    except ImportError:
        Image = None
    src = os.path.join(ROOT, "game-adaptations", "assets", "characters")
    for camp, fn in CHARS.items():
        raw = open(os.path.join(src, fn + ".png"), "rb").read()
        if Image is not None:
            im = Image.open(io.BytesIO(raw)).convert("RGBA").resize((size, size), Image.LANCZOS)
            q = im.quantize(colors=200, method=Image.FASTOCTREE)
            buf = io.BytesIO()
            q.save(buf, "PNG", optimize=True)
            raw = buf.getvalue()
        out[camp] = "data:image/png;base64," + base64.b64encode(raw).decode()
    return out


def load_bgs():
    """每关一张现场插画（tools/prep_bg.py 压好的 288x288 雪碧图 data URI）。

    3x3 切开后正好对应九宫格区块：同一宫内的九格拼回这幅画的对应区块。
    """
    for p in (os.path.join(ROOT, "game", "murdoku-bgs.json"),
              os.path.join(ROOT, "game-adaptations", "识骗迷局", "art", "bgs.json")):
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as f:
                return json.load(f)
    print("  提示：没找到 murdoku-bgs.json，网格背景留空（先跑 tools/prep_bg.py）")
    return {}


def main():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    levels = []
    sols = {}
    for spec in LEVELS:
        lv, sol = build_level(spec)
        levels.append(lv)
        sols[lv["id"]] = {n: list(v) for n, v in sol.items()}
        print("  ✓ %s《%s》 线索 %d 条 · 推理档位 %d · 受害者 %s 在 %s · 主骗 %s 在 %s"
              % (lv["id"], lv["title"], lv["clueCount"], lv["difficulty"],
                 lv["answer"]["victim"]["name"], lv["answer"]["victim"]["zoneName"],
                 lv["answer"]["scammer"]["name"], lv["answer"]["scammer"]["zoneName"]))
    data = {"chapters": CHAPTERS, "levels": levels}
    pj = os.path.join(OUT_DIR, "puzzles.json")
    io.open(pj, "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=1))
    print("题库：%s（%d 关）" % (pj, len(levels)))

    # ---------- 打包单文件 ----------
    html = io.open(os.path.join(HERE, "murdoku_template.html"), encoding="utf-8").read()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*__DATA__*/null/*__DATA__*/", payload)
    html = html.replace("/*__CHARS__*/null/*__CHARS__*/",
                        json.dumps(load_chars(), ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*__BGS__*/null/*__BGS__*/",
                        json.dumps(load_bgs(), ensure_ascii=False, separators=(",", ":")))
    out_html = os.path.join(OUT_DIR, "识骗迷局.html")
    io.open(out_html, "w", encoding="utf-8").write(html)
    print("单文件：%s（%.0f KB）" % (out_html, os.path.getsize(out_html) / 1024))
    # 再放一份到 game/ 下，GitHub Pages 上直接能玩（纯 ASCII 路径，转发不易出错）
    pub = os.path.join(ROOT, "game", "murdoku.html")
    io.open(pub, "w", encoding="utf-8").write(html)
    print("发布副本：%s（%.0f KB）" % (pub, os.path.getsize(pub) / 1024))
    # 题库单独放一份进仓库，方便别人核查/复用（game-adaptations/ 是本地工作区，不入库）
    io.open(os.path.join(ROOT, "game", "murdoku-puzzles.json"), "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=1))
    print("题库副本：game/murdoku-puzzles.json")


if __name__ == "__main__":
    main()
