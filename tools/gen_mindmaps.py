# -*- coding: utf-8 -*-
"""生成《人间防骗指南》思维导图：
- mindmaps/00-整体结构.png + .xmind   全书总览（16 分类 + 关键数据）
- mindmaps/01..16-<分类>.png + .xmind 各章：分类 -> 每篇文章 -> 要点(4)
- mindmaps/index.html                  交互浏览入口（可折叠、可打印）
"""
import io, json, os, re, zipfile, time, hashlib
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mindmaps")
os.makedirs(OUT, exist_ok=True)

ARTS = json.load(io.open(os.path.join(ROOT, "tools", "articles.json"), encoding="utf-8"))

# ---------- 字体 ----------
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]
def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=0)
            except Exception:
                continue
    return ImageFont.load_default()

F_ROOT, F_CAT, F_ART, F_PT = load_font(26), load_font(17), load_font(13), load_font(11)

# ---------- 树节点 ----------
class N:
    __slots__ = ("t", "kids", "depth", "x", "y", "w", "h", "bg", "fg", "outline", "font", "maxchars", "label", "hot")
    def __init__(self, t, depth, kids=None, hot=False):
        self.t, self.depth, self.kids, self.hot = t, depth, kids or [], hot
        self.x = self.y = 0.0
        self.w = self.h = 0
        self.bg = self.fg = self.outline = self.font = self.maxchars = self.label = None

PALETTE = {
    0: ("#1f4e79", "#ffffff", F_ROOT, 30),
    1: ("#d6e4f0", "#1f4e79", F_CAT, 22),
    2: ("#ffffff", "#2d333b", F_ART, 26),
    3: ("#f2f4f7", "#57606a", F_PT, 34),
}

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF"
    "\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF]"
)

def strip_emoji(s):
    return EMOJI_RE.sub("", s).strip()

def trunc(s, n):
    s = re.sub(r"\s+", " ", s).strip()
    return s if len(s) <= n else s[: n - 1] + "…"

def measure(font, s):
    b = font.getbbox(s)
    return b[2] - b[0], b[3] - b[1]

def style(node):
    bg, fg, font, mc = PALETTE[min(node.depth, 3)]
    node.bg, node.fg, node.font, node.maxchars = bg, fg, font, mc
    node.outline = "#c5cdd6"
    if node.hot:
        node.bg, node.fg, node.outline = "#fde8e8", "#b42318", "#e08a82"
    node.label = strip_emoji(trunc(node.t, mc))
    if not node.label:
        node.label = trunc(node.t, mc)
    tw, th = measure(font, node.label)
    node.w, node.h = tw + 22, max(th + 12, 26)
    for k in node.kids:
        style(k)

# ---------- 布局 ----------
LEAF_GAP, COL_GAP, PAD_Y = 26, 58, 46

def layout(node):
    if not node.kids:
        node.y = layout.cur
        layout.cur += node.h + LEAF_GAP
        return node.y
    ys = [layout(k) for k in node.kids]
    node.y = (ys[0] + ys[-1]) / 2
    return node.y

def place_x(node):
    node.x = node.depth * (max(320, COL_GAP + 200)) if node.depth == 0 else 0
    # x 按“上一列最宽节点 + 间距”累计更紧凑，这里用逐层最大宽度
    return node

def assign_x(node, col_x):
    node.x = col_x
    if node.kids:
        next_x = node.x + node.w + COL_GAP
        for k in node.kids:
            assign_x(k, next_x)

def bounds(node):
    xs = [node.x + node.w, node.y + node.h]
    for k in node.kids:
        a, b = bounds(k)
        xs[0] = max(xs[0], a)
        xs[1] = max(xs[1], b)
    return xs

# ---------- 绘制 ----------
TITLE_H = 42  # 标题条高度；所有节点 y 均相对标题条下方计算

def draw_tree(root, path, title, legend=True):
    style(root)
    layout.cur = 0
    layout(root)
    assign_x(root, 20)
    maxw, maxh = bounds(root)
    W, H = int(maxw + 40), int(maxh + 80 + TITLE_H)
    img = Image.new("RGB", (W, H), "#fafbfc")
    d = ImageDraw.Draw(img)

    # 标题条
    d.rectangle([0, 0, W, TITLE_H], fill="#1f4e79")
    d.text((16, 10), title, font=F_CAT, fill="#ffffff")
    if legend:
        # 右侧图例
        ly = 14
        d.rounded_rectangle([W - 230, ly, W - 210, ly + 16], radius=4, fill="#fde8e8", outline="#e08a82", width=1)
        d.text((W - 204, 11), "红色 = 涉刑风险（碰了不只是丢钱）", font=F_PT, fill="#ffbdb7")

    def draw_node(n):
        ny = n.y + TITLE_H  # 节点框顶
        cy = ny + n.h / 2   # 节点中心（连线用，与框对齐）
        for k in n.kids:
            ky = k.y + TITLE_H + k.h / 2
            x1, y1 = n.x + n.w, cy
            x2, y2 = k.x, ky
            mid = (x1 + x2) / 2
            # 平滑折线
            d.line([(x1, y1), (mid, y1), (mid, ky), (x2, ky)], fill="#9aa4b2", width=2)
        x0, y0 = n.x, ny
        d.rounded_rectangle([x0, y0, x0 + n.w, y0 + n.h], radius=8, fill=n.bg, outline=n.outline, width=1)
        label = n.label
        b = n.font.getbbox(label)
        d.text((x0 + 11, y0 + (n.h - (b[3] - b[1])) / 2 - b[1]), label, font=n.font, fill=n.fg)
        for k in n.kids:
            draw_node(k)

    draw_node(root)
    img.save(path)
    return path, W, H

# ---------- XMind ----------
def xmind(node, sheet_title, path):
    def topic(n):
        t = {"id": "n" + hashlib.md5((n.t + str(n.depth) + str(id(n))).encode()).hexdigest()[:10],
             "class": "topic", "title": n.t}
        if n.hot:
            t["markers"] = [{"markerId": "markerId-redFlag"}]
        if n.kids:
            t["children"] = {"attached": [topic(k) for k in n.kids]}
        return t
    content = [{
        "id": "sheet0", "class": "sheet", "title": sheet_title,
        "rootTopic": topic(node), "topicPositioning": "fixed",
    }]
    meta = {"creator": {"name": "HowToAvoidScams", "version": "1.0"}}
    manifest = {"file-entries": {"content.json": {}, "metadata.json": {}}}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("content.json", json.dumps(content, ensure_ascii=False))
        z.writestr("metadata.json", json.dumps(meta, ensure_ascii=False))
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))
    return path

# ---------- 交互 HTML ----------
def html_map(nodes_data, path, title):
    def li(items):
        s = []
        for item in items:
            label, kids = item[0], item[1]
            hot = item[2] if len(item) > 2 else False
            if kids:
                s.append("<li><details open><summary%s>%s</summary><ul>%s</ul></details></li>"
                         % (' class="crime"' if hot else "", label, li(kids)))
            else:
                s.append("<li><span%s>%s</span></li>" % (' class="crime"' if hot else "", label))
        return "".join(s)

    body = li(nodes_data)
    tpl = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s · 思维导图</title>
<style>
body{margin:0;font:14px/1.7 "Microsoft YaHei",sans-serif;background:#fafbfc;color:#2d333b}
header{background:#1f4e79;color:#fff;padding:14px 22px}
header h1{margin:0;font-size:18px}
.wrap{max-width:1060px;margin:0 auto;padding:18px 22px 40px}
ul{list-style:none;padding-left:22px;border-left:1px solid #d0d7de}
li{margin:2px 0}
summary{cursor:pointer;font-weight:600;outline:none}
summary:hover{color:#1f4e79}
span{display:inline-block;padding:1px 8px;border-radius:6px;background:#fff;border:1px solid #d0d7de;margin:1px 0}
span:hover{border-color:#1f4e79;background:#eef4fb}
span.crime,summary.crime{background:#fde8e8;border-color:#e08a82;color:#b42318}
summary.crime{background:none;border:none;display:inline-block;padding:1px 8px;border-radius:6px}
summary.crime:hover{color:#b42318}
.root>ul>li>details>summary,.root>ul>li>span{font-size:16px;color:#1f4e79}
small{opacity:.65;font-weight:400}
.legend{display:inline-block;margin-left:12px;font-size:12px;padding:2px 10px;border-radius:999px;background:#fde8e8;color:#ffbdb7;border:1px solid #e08a82}
.tools{padding:10px 22px;background:#eef4fb;font-size:13px}
.tools a{color:#1f4e79;margin-right:14px}
@media print{.tools{display:none}details{open:true}}
</style></head><body>
<header><h1>%(title)s<span class="legend">红色 = 涉刑风险</span></h1><div style="opacity:.85;font-size:12px;margin-top:4px">《人间防骗指南》思维导图源文件 · 点标题可折叠/展开</div></header>
<div class="tools">快捷：<a href="#" onclick="document.querySelectorAll('details').forEach(d=>d.open=true);return false">全部展开</a>
<a href="#" onclick="document.querySelectorAll('details').forEach(d=>d.open=false);return false">全部折叠</a>
<a href="javascript:print()">打印 / 导出 PDF</a></div>
<div class="wrap root"><ul>%(body)s</ul></div>
</body></html>"""
    io.open(path, "w", encoding="utf-8").write(tpl % {"title": title, "body": body})
    return path

# ---------- 章节顺序（对齐 book/ 编号） ----------
CHAPTERS = [
    ("01-兼职刷单", "兼职 · 刷单"), ("02-洗钱银行卡", "洗钱 · 银行卡"),
    ("03-网购二手快递", "网购 · 二手快递"), ("04-网赌博彩", "网赌 · 博彩"),
    ("05-投资虚拟币", "投资 · 虚拟币"), ("06-网贷套路贷", "网贷 · 套路贷"),
    ("07-情感色情陷阱", "情感 · 色情陷阱"), ("08-AI盗号技术", "AI · 盗号技术"),
    ("09-冒充公检法", "冒充 · 公检法"), ("10-隐私信息黑市", "隐私 · 信息黑市"),
    ("11-求职加盟", "求职 · 加盟"), ("12-老人学生宝妈", "老人 · 学生 · 宝妈"),
    ("13-生活中的坑", "生活中的坑"), ("14-黑灰产大盘", "黑灰产大盘"),
    ("15-民生缴费票务", "民生 · 缴费票务"), ("16-应急反诈工具", "应急 · 反诈工具"),
]

made = []
# ---------- 16 章 ----------
for fname, cat in CHAPTERS:
    arts = [a for a in ARTS if a["cat"] == cat]
    arts.sort(key=lambda a: a["id"])
    n_crime_ch = sum(1 for a in arts if "刑责风险" in a.get("risks", []))
    root = N("%s（%d 篇 · 涉刑 %d）" % (cat, len(arts), n_crime_ch), 0)
    for a in arts:
        hot = "刑责风险" in a.get("risks", [])
        art_node = N("%s %s" % (a["icon"], a["title"]), 1, hot=hot)
        for p in a["points"]:
            art_node.kids.append(N(p, 2, hot=hot))
        root.kids.append(art_node)
    png = os.path.join(OUT, fname + ".png")
    xm = os.path.join(OUT, fname + ".xmind")
    draw_tree(root, png, "《人间防骗指南》· %s（%d 篇 · 涉刑 %d）" % (cat, len(arts), n_crime_ch),
              legend=n_crime_ch > 0)
    xmind(root, cat, xm)
    # HTML 源
    html_data = []
    for a in arts:
        hot = "刑责风险" in a.get("risks", [])
        html_data.append(("%s %s" % (a["icon"], a["title"]), [(p, []) for p in a["points"]], hot))
    html_map([(cat, html_data)], os.path.join(OUT, fname + ".html"),
             "%s · %d 篇 · 涉刑 %d" % (cat, len(arts), n_crime_ch))
    made.append((fname, cat, len(arts)))

# ---------- 00 总览 ----------
n_crime = sum(1 for a in ARTS if "刑责风险" in a.get("risks", []))
root = N("《人间防骗指南》%d 篇真实骗局拆解（涉刑 %d 篇标红）" % (len(ARTS), n_crime), 0)
cats_branch = N("🗂 16 类骗局分类（红色=涉刑风险）", 1)
for fname, cat in CHAPTERS:
    arts = [a for a in ARTS if a["cat"] == cat]
    n_crime_c = sum(1 for a in arts if "刑责风险" in a.get("risks", []))
    node = N("%s · %d 篇（涉刑 %d）" % (cat, len(arts), n_crime_c), 2)
    # 每类取前 3 个代表文章做三级节点（涉刑的标红）
    for a in sorted(arts, key=lambda x: x["id"])[:3]:
        hot = "刑责风险" in a.get("risks", [])
        node.kids.append(N("%s %s" % (a["icon"], trunc(a["title"], 20)), 3, hot=hot))
    if len(arts) > 3:
        node.kids.append(N("…等共 %d 篇（其中涉刑 %d 篇）" % (len(arts), n_crime_c), 3, hot=n_crime_c > 0))
    cats_branch.kids.append(node)
stats = N("📊 全书数据", 1)
stats.kids = [
    N("涉刑风险 %d 篇（碰了不只是丢钱）" % n_crime, 2, hot=True),
    N("权威判例挂载 1466 条次（法院/检察/公安/央媒）", 2),
    N("45 道自查清单（是/否题，按优先级排序）", 2),
    N("12 局防骗小游戏（选错就扣钱，局中不讲对错）", 2),
    N("下载：PDF / EPUB / Anki 牌组 / 离线单文件 HTML", 2),
]
use = N("🎯 怎么用", 1)
use.kids = [
    N("搜对方说的话：“垫付”“共享屏幕”“验证码”直接命中", 2),
    N("按人群筛：老人 / 学生 / 宝妈 / 商家 / 求职者", 2),
    N("每篇五件事：套路分几步 · 坑在哪 · 怎么防 · 哪条法律 · 一句总结", 2),
    N("在线：https://qerssd.github.io/HowToAvoidScams/", 2),
]
root.kids = [cats_branch, stats, use]
draw_tree(root, os.path.join(OUT, "00-整体结构.png"), "《人间防骗指南》· 全书整体结构（红色=涉刑风险 %d 篇）" % n_crime)
xmind(root, "全书整体结构", os.path.join(OUT, "00-整体结构.xmind"))
cat_html = []
for fname, cat in CHAPTERS:
    arts = [x for x in ARTS if x["cat"] == cat]
    n_crime_c = sum(1 for y in arts if "刑责风险" in y.get("risks", []))
    kids = []
    for a in sorted(arts, key=lambda x: x["id"]):
        hot = "刑责风险" in a.get("risks", [])
        kids.append(("%s %s" % (a["icon"], trunc(a["title"], 24)), [(p, []) for p in a["points"]], hot))
    cat_html.append(("%s · %d 篇（涉刑 %d）" % (cat, len(arts), n_crime_c), kids, n_crime_c > 0))
html_data = [
    ("🗂 16 类骗局分类", cat_html),
    ("📊 全书数据", [(t.t, [], t.hot) for t in stats.kids]),
    ("🎯 怎么用", [(t.t, []) for t in use.kids]),
]
html_map(html_data, os.path.join(OUT, "00-整体结构.html"),
         "全书整体结构 · 涉刑 %d 篇" % n_crime)

# ---------- index.html 总入口 ----------
rows = []
for fname, cat, n in [("00-整体结构", "全书整体结构（16 类总览）", len(ARTS))] + made:
    rows.append(
        '<a class="card" href="%s.html"><b>%s</b><small>%s 篇</small>'
        '<span class="links"><i>PNG</i><i>XMind</i></span></a>'
        % (fname, fname.split("-", 1)[1], n))
idx = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>《人间防骗指南》思维导图 · 索引</title>
<style>
body{margin:0;font:14px/1.7 "Microsoft YaHei",sans-serif;background:#fafbfc;color:#2d333b}
header{background:#1f4e79;color:#fff;padding:20px 22px}header h1{margin:0;font-size:20px}
header p{margin:6px 0 0;opacity:.85;font-size:13px}
.wrap{max-width:1060px;margin:0 auto;padding:20px 22px 40px;display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.card{display:block;padding:14px 16px;background:#fff;border:1px solid #d0d7de;border-radius:12px;text-decoration:none;color:inherit}
.card:hover{border-color:#1f4e79;box-shadow:0 2px 10px rgba(31,78,121,.12)}
.card b{display:block;font-size:15px;color:#1f4e79}
.card small{opacity:.65}
.links i{display:inline-block;font-style:normal;font-size:11px;margin-right:6px;margin-top:6px;padding:1px 8px;border-radius:999px;background:#eef4fb;color:#1f4e79;border:1px solid #c9daf0}
.note{max-width:1060px;margin:0 auto;padding:0 22px;color:#57606a;font-size:13px}
</style></head><body>
<header><h1>《人间防骗指南》思维导图</h1>
<p>整体 1 张 + 16 章各 1 张。点击进入交互版（可折叠/打印），同名 .png 为图片、.xmind 为可编辑源文件。</p></header>
<div class="wrap">%s</div>
<p class="note">源文件说明：.xmind 用 XMind / MindMaster 等导入后可直接编辑；.html 是零依赖源文件，双击即可打开。</p>
</body></html>""" % "".join(rows)
io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(idx)

print("生成完成：%d 张 PNG + %d 个 .xmind + %d 个 .html" % (len(made) + 1, len(made) + 1, len(made) + 2))
for fname, cat, n in made:
    print("  %s  %s  %d 篇" % (fname + ".png", cat, n))
print("  00-整体结构.png  全书总览")
print("  index.html  浏览入口")
