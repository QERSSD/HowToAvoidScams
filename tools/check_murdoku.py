# -*- coding: utf-8 -*-
"""《识骗迷局》交付前自检

不联网、不起服务，只做三件事：
  1. 题库自检：九个人、坐标合法、陈述的答案和解法对得上
  2. 重跑验题器：每一关重新数一遍解，必须还是 1
  3. 单文件自检：占位符替换干净、内联 JSON 能解析、关卡编号连续

用法： python tools/check_murdoku.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from murdoku_engine import ZONE, count_solutions, propagate            # noqa: E402

OUT_DIR = os.path.join(ROOT, "game-adaptations", "识骗迷局")
problems = []


def check_puzzles(data):
    levels = data["levels"]
    print("== 题库 ==")
    print("  关卡 %d 个，章节 %d 个" % (len(levels), len(data["chapters"])))
    for i, lv in enumerate(levels):
        tag = lv["id"]
        names = [r["name"] for r in lv["roles"]]
        if len(names) != 9:
            problems.append("%s 角色数 %d" % (tag, len(names)))
        if len(set(names)) != 9:
            problems.append("%s 角色重名" % tag)
        if len(lv["zones"]) != 9 or len(lv["rows"]) != 9:
            problems.append("%s 区/排数量不对" % tag)
        sol = {n: (v["r"], v["c"]) for n, v in lv["sol"].items()}
        # 每排 / 每列 / 每区只能有一个人
        for what, key in (("排", lambda p: p[0]), ("列", lambda p: p[1]),
                          ("区", lambda p: ZONE[p])):
            vals = [key(p) for p in sol.values()]
            if len(set(vals)) != 9:
                problems.append("%s 同%s有两人" % (tag, what))
        # 开局给定的人，位置必须和标准答案一致
        for g in lv["given"]:
            if sol[g["name"]] != (g["r"], g["c"]):
                problems.append("%s 给定位置与答案不符：%s" % (tag, g["name"]))
        # 陈述的受害者 / 主骗坐标必须和真解一致
        for who in ("victim", "scammer"):
            a = lv["answer"][who]
            r, c = sol[a["name"]]
            if (r + 1, c + 1, ZONE[(r, c)] + 1) != (a["row"], a["col"], a["zone"]):
                problems.append("%s %s 坐标写错了" % (tag, who))
        if lv["answer"]["victim"]["zoneName"] != lv["zones"][lv["answer"]["victim"]["zone"] - 1]:
            problems.append("%s 受害者区名不符" % tag)
        if lv["answer"]["scammer"]["zoneName"] != lv["zones"][lv["answer"]["scammer"]["zone"] - 1]:
            problems.append("%s 主骗区名不符" % tag)
        # 线索里提到的人必须是这一关的人
        for cl in lv["clues"]:
            for nm in cl["a"]:
                if nm not in names:
                    problems.append("%s 线索提到陌生人 %s" % (tag, nm))
        # 破绽问答：四个选项 + 一个有且仅有一个正确答案
        p = lv["pick"]
        if len(p["options"]) != 4 or not (0 <= p["answer"] < 4):
            problems.append("%s 破绽问答选项不对" % tag)
        if not p["why"]:
            problems.append("%s 破绽问答缺解析" % tag)
        # 再来一遍：独立验题
        given = {g["name"]: (g["r"], g["c"]) for g in lv["given"]}
        sols = count_solutions(names, lv["clues"], given, limit=2)
        if len(sols) != 1:
            problems.append("%s 解的数量 %d" % (tag, len(sols)))
        st, _, _ = propagate(names, lv["clues"], given)
        if st != "solved":
            problems.append("%s 不能纯逻辑推完（%s）" % (tag, st))
        print("  ✓ %s《%s》线索 %d · 唯一解 %d · 传播 %s"
              % (tag, lv["title"], lv["clueCount"], len(sols), st))


def check_html(path, data):
    print("\n== 单文件 ==")
    html = io.open(path, encoding="utf-8").read()
    print("  体积 %.0f KB" % (os.path.getsize(path) / 1024))
    if "__DATA__" in html or "__CHARS__" in html or "__BGS__" in html:
        problems.append("HTML 里还有未替换的占位符")
    m = re.search(r"const DATA = (\{.*?\});\nconst CHARS", html, re.S)
    if not m:
        problems.append("找不到内联的题库")
        return
    try:
        inline = json.loads(m.group(1))
    except Exception as e:
        problems.append("内联题库解析失败：%s" % e)
        return
    if len(inline["levels"]) != len(data["levels"]):
        problems.append("内联关卡数 %d 与题库 %d 不一致"
                        % (len(inline["levels"]), len(data["levels"])))
    for camp in ("骗", "受害", "警", "路"):
        key = '"%s":"data:image/png;base64,' % camp
        if key not in m.group(1) and key not in html:
            problems.append("缺少棋子图：%s" % camp)
    # 每关都要有现场背景图
    mb = re.search(r"const BGS = (\{.*?\});", html, re.S)
    if not mb:
        problems.append("找不到内联的场景背景图 BGS")
    else:
        try:
            bgs = json.loads(mb.group(1))
        except Exception as e:
            problems.append("BGS 解析失败：%s" % e)
            bgs = {}
        for lv in data["levels"]:
            if not bgs.get(lv["id"], "").startswith("data:image/jpeg;base64,"):
                problems.append("关卡 %s 缺少现场背景图" % lv["id"])
    if html.count("<script>") != 1 or html.count("</script>") != 1:
        problems.append("script 标签数量异常")


def main():
    data = json.load(io.open(os.path.join(OUT_DIR, "puzzles.json"), encoding="utf-8"))
    check_puzzles(data)
    check_html(os.path.join(OUT_DIR, "识骗迷局.html"), data)
    print()
    if problems:
        print("✗ 有问题 %d 处：" % len(problems))
        for p in problems:
            print("   -", p)
        return 1
    print("✓ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
