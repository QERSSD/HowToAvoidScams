# -*- coding: utf-8 -*-
"""生成 docs/查阅材料：目录.md、术语表.md、核实记录.md。

- 目录：364 篇按 16 类，每篇带编号/风险/人群标注，链接到 book/ 分类文件
- 术语表：黑话速查（42 条，与 Anki 黑话卡同源），每个术语自动关联出现最多的 3 篇文章
- 核实记录：120 条报道逐条列来源、摘要与核实说明
"""
import io, os, json, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glossary import GLOSSARY, CAT_ORDER
from build_repo import SLUG, RISK_ICON, CAT_INTRO

TARGET_ICON = {"中老年": "🧓", "女性": "👩", "学生党": "🎓", "商家店主": "🏪", "求职者": "💼", "负债人": "📉"}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)

arts = json.load(io.open(os.path.join(HERE, "articles.json"), encoding="utf-8"))
news = json.load(io.open(os.path.join(HERE, "news.json"), encoding="utf-8"))["reports"]
BY_CAT = {}
for a in arts:
    BY_CAT.setdefault(a["cat"], []).append(a)

TODAY = "2026-10-19"


def build_toc():
    lines = ["# 目录", "",
             "共 %d 篇，按 16 个骗局类型分组。编号即全站统一的文章编号（离线应用 `#p编号` 可直接定位；Anki 卡片、PDF / EPUB 书签使用同一编号）。" % len(arts), ""]
    lines += ["| 分类 | 篇数 | 直达 |", "|---|---|---|"]
    for cat in CAT_ORDER:
        rows = BY_CAT.get(cat, [])
        if rows:
            lines.append("| %s | %d | [book/%s.md](../book/%s.md) |" % (cat, len(rows), SLUG[cat], SLUG[cat]))
    lines.append("")
    for cat in CAT_ORDER:
        rows = BY_CAT.get(cat, [])
        if not rows:
            continue
        lines.append("## %s（%d 篇）" % (cat, len(rows)))
        lines.append("")
        lines.append(CAT_INTRO.get(cat, ""))
        lines.append("")
        for a in rows:
            marks = []
            for r in a.get("risks", []):
                marks.append("%s%s" % (RISK_ICON.get(r, ""), r))
            for t in a.get("targets", []):
                marks.append("%s%s" % (TARGET_ICON.get(t, ""), t))
            m = ("　" + "　".join(marks)) if marks else ""
            lines.append("- **%d. %s**%s" % (a["id"], a["title"], m))
        lines.append("")
    io.open(os.path.join(DOCS, "目录.md"), "w", encoding="utf-8").write("\n".join(lines))


def build_glossary():
    lines = ["# 术语表 · 黑话速查", "",
             "骗子圈和反诈报道里的黑话，一句话讲清「是什么 + 在骗局链条里的位置 + 对普通人意味着什么」。共 %d 条，按性质分四类；每条关联的出现最多文章可直接在离线应用里搜编号查看。同名内容也做成了 Anki 黑话卡（`downloads/人间防骗指南.apkg` 的「黑话速查」牌组）。" % len(GLOSSARY), ""]
    groups = {}
    for term, kind, desc, cats in GLOSSARY:
        groups.setdefault(kind, []).append((term, desc, cats))
    for kind in ["骗局类型", "产业链角色", "法律名词", "工具"]:
        rows = groups.get(kind, [])
        if not rows:
            continue
        lines.append("## %s" % kind)
        lines.append("")
        for term, desc, cats in rows:
            # 找出现该词最多的 3 篇文章
            scored = []
            for a in arts:
                blob = a["title"] + " " + " ".join(r["t"] for r in a["body"])
                c = blob.count(term)
                if c:
                    scored.append((c, a))
            scored.sort(key=lambda x: -x[0])
            rel = "、".join("#%d《%s》" % (a["id"], a["title"][:24]) for _, a in scored[:3])
            lines.append("**%s**　<sub>常见于：%s</sub>" % (term, " / ".join(cats)))
            lines.append("")
            lines.append("%s" % desc)
            if rel:
                lines.append("")
                lines.append("<sub>关联拆解：%s</sub>" % rel)
            lines.append("")
    io.open(os.path.join(DOCS, "术语表.md"), "w", encoding="utf-8").write("\n".join(lines))


def mount_count():
    """与 build_offline 同一套匹配逻辑，统计全站实际挂载条次（每篇最多 4 条）。"""
    total = 0
    for a in arts:
        blob = a["title"] + "\n" + "\n".join(r["t"] for r in a["body"])
        hits = 0
        for r in news:
            sc = 0
            if a["cat"] in r["cats"]:
                sc += 1
            ks = [k for k in r["keys"] if k in blob]
            if ks:
                sc += 2 + len(ks)
            if sc:
                hits += 1
        total += min(hits, 4)
    return total


def build_verify():
    lines = ["# 核实记录", "",
             "全站挂载的「相关案例与公开报道」逐条记录在此（共 %d 条，全站挂载 %d 条次）。" % (len(news), mount_count()), "",
             "## 核实口径", "",
             "1. **来源只收发布页**：全部链接指向各级法院、检察院、公安机关官网及央视、人民日报、新华社、光明网、法治日报等央媒的原始发布页，不收转载聚合页。",
             "2. **核实方式**：逐条经网络检索定位到发布页原文，核对标题、发布主体与案情摘要后录入（核实日期 %s）。链接内容以发布方为准，若日后页面迁移导致失效，可按「标题 + 来源」重新检索。" % TODAY,
             "3. **匹配语义**：每篇拆解挂载的是**同类案例**——法院 / 警方公开通报的同类骗局的定罪量刑与办案情况，不是口播稿对应的同一案件。这一点在 README 与 [分篇与标注口径](分篇与标注口径.md) 中均有说明。",
             "4. **案情摘要**：均为来源页面内容的摘编，尽量保留判决结果、涉案金额等可核对数字。",
             "",
             "## 报道清单", "",
             "| # | 报道（点开原文） | 来源 | 挂载类别 | 案情摘要 |",
             "|---|---|---|---|---|"]
    for i, r in enumerate(news, 1):
        cats = "、".join(r.get("cats", [])) or "关键词触发"
        lines.append("| %d | [%s](%s) | %s | %s | %s |" % (
            i, r["t"].replace("|", "｜"), r["u"], r["s"], cats,
            r["n"].replace("|", "｜")))
    lines.append("")
    io.open(os.path.join(DOCS, "核实记录.md"), "w", encoding="utf-8").write("\n".join(lines))


if __name__ == "__main__":
    build_toc()
    print("目录.md ok")
    build_glossary()
    print("术语表.md ok")
    build_verify()
    print("核实记录.md ok")
