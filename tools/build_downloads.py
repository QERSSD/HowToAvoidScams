# -*- coding: utf-8 -*-
"""生成 downloads/：PDF、EPUB、Anki 牌组。离线单文件应用不在这里复制（统一为根目录 人间防骗指南.html）。

- PDF   ：reportlab + 微软雅黑，16 类分章，书签大纲，emoji 已清理（PDF 字体不渲染 emoji）
- EPUB  ：手写 EPUB3（zipfile），16 章 + nav 目录，阅读器里可点开报道原文链接
- Anki  ：genanki，335 张文章卡（正面=类别+标题，背面=套路步骤+防身金句+报道）+ 黑话卡
"""
import io, os, re, json, shutil, zipfile, html, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glossary import GLOSSARY, CAT_ORDER

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "downloads")
os.makedirs(OUT, exist_ok=True)

arts = json.load(io.open(os.path.join(HERE, "articles.json"), encoding="utf-8"))
if not arts:
    raise SystemExit("articles.json 是空的，拒绝生成空下载物。")
news = json.load(io.open(os.path.join(HERE, "news.json"), encoding="utf-8"))["reports"]
BY_CAT = {}
for a in arts:
    BY_CAT.setdefault(a["cat"], []).append(a)

KIND_LABEL = {"step": "套路", "trap": "陷阱", "tip": "防范", "warn": "警示",
              "law": "法律", "end": "收尾", "money": "资金"}

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2B00-\u2BFF\u2049\u203C\u2122\u2139"
    "\u2194-\u21AA\u231A-\u231B\u2328\u23CF\u23E9-\u23FA\u24C2\u25AA-\u25FE"
    "\u2934\u2935\u3030\u303D\u3297\u3299]"
)
def no_emoji(s):
    s = EMOJI_RE.sub("", s)
    return re.sub(r"  +", " ", s).strip()


# ---------------------------------------------------------------- PDF
def build_pdf(path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                    Spacer, PageBreak)

    # 字体回退链：本地 Windows 用微软雅黑；GitHub Actions（Linux）用 Noto Sans CJK
    FONT_CANDIDATES = [
        r"C:\Windows\Fonts\msyh.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    HEI_CANDIDATES = [
        r"C:\Windows\Fonts\simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]
    yh = next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
    hei = next((f for f in HEI_CANDIDATES if os.path.exists(f)), yh)
    if not yh:
        raise RuntimeError("找不到中文字体（msyh.ttc / NotoSansCJK）")
    pdfmetrics.registerFont(TTFont("YH", yh, subfontIndex=0))
    pdfmetrics.registerFont(TTFont("HEI", hei, subfontIndex=0))

    BRAND = colors.HexColor("#B4272E")
    GREY = colors.HexColor("#666666")

    st_cover_t = ParagraphStyle("cover_t", fontName="HEI", fontSize=26, leading=38,
                                textColor=BRAND, alignment=1, spaceAfter=6)
    st_cover_s = ParagraphStyle("cover_s", fontName="YH", fontSize=12, leading=20,
                                textColor=GREY, alignment=1)
    st_cat = ParagraphStyle("CatTitle", fontName="HEI", fontSize=17, leading=24,
                            textColor=BRAND, spaceBefore=14, spaceAfter=8)
    st_art = ParagraphStyle("ArtTitle", fontName="HEI", fontSize=11.5, leading=17,
                            textColor=colors.HexColor("#1F1F1F"), spaceBefore=10, spaceAfter=3)
    st_lead = ParagraphStyle("lead", fontName="YH", fontSize=9.5, leading=15.5,
                             textColor=GREY, spaceAfter=4)
    st_sec = ParagraphStyle("sec", fontName="YH", fontSize=9.5, leading=15.5,
                            textColor=BRAND, spaceBefore=5)
    st_p = ParagraphStyle("p", fontName="YH", fontSize=9.5, leading=15.5, spaceAfter=3,
                          firstLineIndent=0)
    st_kind = ParagraphStyle("kind", fontName="YH", fontSize=9.5, leading=15.5, spaceAfter=2)
    st_ref = ParagraphStyle("ref", fontName="YH", fontSize=8.5, leading=13.5,
                            textColor=GREY, leftIndent=8, spaceAfter=1)

    class Doc(BaseDocTemplate):
        def afterFlowable(self, fl):
            if not isinstance(fl, Paragraph):
                return
            name = fl.style.name
            if name == "CatTitle":
                key = "cat-%d" % self.page
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(fl.getPlainText(), key, level=0, closed=False)
            elif name == "ArtTitle":
                key = "art-%d" % id(fl)
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(fl.getPlainText()[:60], key, level=1, closed=True)

    def esc(s):
        return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    story = []
    n_risk = sum(1 for a in arts if "刑责风险" in a.get("risks", []))
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("人间防骗指南", st_cover_t))
    story.append(Paragraph("%d 个真实骗局 · %d 篇可能背上刑责" % (len(arts), n_risk), st_cover_s))
    story.append(Paragraph("套路分几步 · 坑在哪 · 会损失什么 · 哪些话一听到就该挂电话", st_cover_s))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("每篇附法院 / 检察院 / 公安机关及央媒公开通报的同类案例链接", st_cover_s))
    story.append(Paragraph("同目录：PDF · EPUB · Anki 牌组 · 离线单文件（HTML）", st_cover_s))
    story.append(PageBreak())

    for ci, cat in enumerate(CAT_ORDER):
        rows = BY_CAT.get(cat, [])
        if not rows:
            continue
        story.append(Paragraph("%s · %d 篇" % (cat, len(rows)), st_cat))
        for a in rows:
            story.append(Paragraph(esc(no_emoji(a["title"])), st_art))
            if a.get("lead"):
                story.append(Paragraph(esc(no_emoji(a["lead"])), st_lead))
            for r in a["body"]:
                t = esc(no_emoji(r["t"]))
                k = r["k"]
                if k == "sec":
                    story.append(Paragraph(t, st_sec))
                elif k in KIND_LABEL:
                    story.append(Paragraph('<font color="#B4272E"><b>【%s】</b></font>%s' % (KIND_LABEL[k], t), st_kind))
                else:
                    story.append(Paragraph(t, st_p))
            if a.get("points"):
                pts = " · ".join(esc(no_emoji(x)) for x in a["points"][:4])
                story.append(Paragraph('<font color="#B4272E"><b>要点：</b></font>%s' % pts, st_kind))
            for g in a.get("guards", [])[:2]:
                story.append(Paragraph('<font color="#2E7D32"><b>防身：</b></font>%s' % esc(no_emoji(g)), st_kind))
            for ref in a.get("refs", [])[:4]:
                story.append(Paragraph('报道：%s（%s） %s' % (esc(ref["t"]), esc(ref["s"]), esc(ref["u"])), st_ref))
            story.append(Spacer(1, 4))

    doc = Doc(path, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
              topMargin=16 * mm, bottomMargin=16 * mm,
              title="人间防骗指南", author="fangpian")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame])])
    doc.build(story)


# ---------------------------------------------------------------- EPUB
def build_epub(path):
    E = html.escape

    css = ("body{font-family:'Microsoft YaHei',sans-serif;line-height:1.7;margin:5%%}"
           "h1{color:#B4272E;border-bottom:2px solid #B4272E;padding-bottom:6px}"
           "h2{color:#1F1F1F;font-size:1.05em;margin:1.6em 0 .4em;border-left:4px solid #B4272E;padding-left:8px}"
           ".lead{color:#666;font-size:.92em}"
           ".k{color:#B4272E;font-weight:700}"
           ".g{color:#2E7D32;font-weight:700}"
           ".ref{color:#666;font-size:.85em;margin-left:1em}"
           ".tag{color:#999;font-size:.85em}")

    def xhtml(title, body):
        return ('<?xml version="1.0" encoding="utf-8"?>\n'
                '<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" '
                'xmlns:epub="http://www.idpf.org/2007/ops" lang="zh-CN" xml:lang="zh-CN">'
                '<head><meta charset="utf-8"/><title>%s</title>'
                '<link rel="stylesheet" type="text/css" href="style.css"/></head>'
                '<body>%s</body></html>') % (E(title), body)

    chapters = []
    nav_items = []
    for ci, cat in enumerate(CAT_ORDER):
        rows = BY_CAT.get(cat, [])
        if not rows:
            continue
        fn = "ch%02d.xhtml" % ci
        buf = ["<h1>%s · %d 篇</h1>" % (E(cat), len(rows))]
        for a in rows:
            buf.append('<section epub:type="article" id="p%d">' % a["id"])
            buf.append("<h2>%d. %s</h2>" % (a["id"], E(a["title"])))
            if a.get("lead"):
                buf.append('<p class="lead">%s</p>' % E(a["lead"]))
            for r in a["body"]:
                t = E(r["t"])
                if r["k"] == "sec":
                    buf.append("<p><b>%s</b></p>" % t)
                elif r["k"] in KIND_LABEL:
                    buf.append('<p><span class="k">【%s】</span>%s</p>' % (KIND_LABEL[r["k"]], t))
                else:
                    buf.append("<p>%s</p>" % t)
            for g in a.get("guards", [])[:2]:
                buf.append('<p><span class="g">防身：</span>%s</p>' % E(g))
            for ref in a.get("refs", [])[:4]:
                buf.append('<p class="ref">报道：<a href="%s">%s</a>（%s）</p>'
                           % (E(ref["u"], quote=True), E(ref["t"]), E(ref["s"])))
            if a.get("tags"):
                buf.append('<p class="tag">%s</p>' % " ".join("#" + E(x) for x in a["tags"][:6]))
            buf.append("</section>")
        chapters.append((fn, cat, "\n".join(buf)))
        nav_items.append('<li><a href="%s">%s（%d 篇）</a></li>' % (fn, E(cat), len(rows)))

    nav = xhtml("目录", "<h1>目录</h1><nav epub:type=\"toc\" id=\"toc\"><ol>%s</ol></nav>"
                % "\n".join(nav_items))

    opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">'
           '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
           '<dc:identifier id="uid">urn:uuid:3f6a2c1e-8b4d-4e2a-9c7d-fangpian2026</dc:identifier>'
           '<dc:title>人间防骗指南</dc:title>'
           '<dc:language>zh-CN</dc:language>'
           '<dc:description>%d 个真实骗局：套路分几步、坑在哪、会损失什么。每篇附公开通报的同类案例链接。</dc:description>'
           '<meta property="dcterms:modified">2026-10-19T00:00:00Z</meta>'
           '</metadata><manifest>'
           '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
           '<item id="css" href="style.css" media-type="text/css"/>'
           '%s'
           '</manifest><spine>%s</spine></package>') % (
        len(arts),
        "".join('<item id="c%d" href="%s" media-type="application/xhtml+xml"/>' % (i, fn)
                for i, (fn, _, _) in enumerate(chapters)),
        "".join('<itemref idref="c%d"/>' % i for i in range(len(chapters))))

    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0"?><container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                   '<rootfiles><rootfile full-path="OEBPS/content.opf" '
                   'media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf", opf)
        z.writestr("OEBPS/nav.xhtml", nav)
        z.writestr("OEBPS/style.css", css)
        for fn, _, body in chapters:
            z.writestr("OEBPS/" + fn, xhtml("章节", body))


# ---------------------------------------------------------------- Anki
def build_apkg(path):
    import genanki

    model = genanki.Model(
        1607392319, "fangpian-article",
        fields=[{"name": "Q"}, {"name": "A"}],
        templates=[{
            "name": "card",
            "qfmt": '<div style="font-family:sans-serif;font-size:15px;line-height:1.7">'
                    '<div style="color:#999;font-size:13px">{{Category}}</div>{{Q}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer">'
                    '<div style="font-family:sans-serif;font-size:14px;line-height:1.8">{{A}}</div>',
        }])
    # 模板里用到 {{Category}}，把它并进 Q 前置行，避免多余字段
    deck = genanki.Deck(2059400110, "人间防骗指南")
    gloss_deck_id = 2059400111

    KIND = {"step": "套路", "trap": "陷阱", "tip": "防范", "warn": "警示", "law": "法律"}

    for a in arts:
        q = "<b>%s</b>%s<div style=\"color:#666;font-size:13px\">%s</div>" % (
            a["title"], ("<br/>" + a["lead"]) if a.get("lead") else "",
            "——这个骗局的套路和防法？")
        parts = []
        for r in a["body"]:
            if r["k"] in KIND:
                parts.append("<b>【%s】</b>%s" % (KIND[r["k"]], r["t"]))
            elif r["k"] == "sec":
                parts.append("<b>%s</b>" % r["t"])
        if len(parts) > 10:
            parts = parts[:10] + ["……（完整拆解见离线单文件应用）"]
        for g in a.get("guards", [])[:2]:
            parts.append('<font color="#2E7D32"><b>防身：</b>%s</font>' % g)
        if a.get("refs"):
            parts.append("相关案例：%s" % "；".join(x["t"] for x in a["refs"][:2]))
        deck.add_note(genanki.Note(model=model, fields=[q, "<br/>".join(parts)]))

    gdeck = genanki.Deck(gloss_deck_id, "人间防骗指南::黑话速查")
    for term, kind, desc, cats in GLOSSARY:
        q = "<b>%s</b><div style=\"color:#666;font-size:13px\">这个黑话是什么意思？</div>" % term
        a = "%s<div style=\"color:#999;font-size:12px;margin-top:6px\">常见于：%s</div>" % (
            desc, " / ".join(cats))
        gdeck.add_note(genanki.Note(model=model, fields=[q, a]))

    genanki.Package([deck, gdeck]).write_to_file(path)


# ---------------------------------------------------------------- main
def main():
    build_pdf(os.path.join(OUT, "人间防骗指南.pdf"))
    print("PDF ok")
    build_epub(os.path.join(OUT, "人间防骗指南.epub"))
    print("EPUB ok")
    build_apkg(os.path.join(OUT, "人间防骗指南.apkg"))
    print("Anki ok")
    # downloads/ 只放三件真下载物。离线单文件应用统一为根目录的「人间防骗指南.html」
    # （index.html 是它的 GitHub Pages 入口副本），这里不再复制第三份。
    stale = os.path.join(OUT, "人间防骗指南.html")
    if os.path.exists(stale):
        os.remove(stale)
    for f in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, f)
        print("%10.1f KB  %s" % (os.path.getsize(p) / 1024, f))


if __name__ == "__main__":
    main()
