# -*- coding: utf-8 -*-
"""
《识骗迷局》配图生成器

产出三类可直接使用的配图：
  1. 小红书封面（3:4 竖版 1080x1440）
  2. 界面预览 Mockup（16:10 横版，深蓝卷宗风）
  3. 说明图（玩法流程 / 样关示例 / 关卡结构）

风格与需求文档 5.3 对齐：深蓝案情卷宗风，红色仅用于涉刑与错误提示。

用法： env/default/Scripts/python.exe tools/gen_murdle_images.py
"""
import io
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "game-adaptations", "assets")
FONT_DIR = r"C:/Windows/Fonts"


# ---------------- 字体 ----------------
def _tt(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def f_reg(s):
    return _tt("msyh.ttc", s)


def f_bold(s):
    return _tt("msyhbd.ttc", s)


def f_num(s):
    return _tt("Dengl.ttf", s)


# ---------------- 色板（深蓝卷宗风） ----------------
BG_TOP = (11, 27, 43)
BG_BOT = (20, 46, 71)
INK = (10, 20, 31)
PANEL = (28, 57, 85)
PANEL2 = (33, 66, 98)
LINE = (58, 96, 131)
TXT = (233, 241, 248)
TXT2 = (163, 189, 212)
ACC = (79, 209, 197)      # 青（主强调）
ACC2 = (232, 184, 75)     # 金（次强调 / 星级）
RED = (229, 72, 77)       # 涉刑 / 错误
OKC = (86, 199, 130)      # 正确
WHITE = (255, 255, 255)


# ---------------- 绘图工具 ----------------
def canvas(w, h, top=BG_TOP, bot=BG_BOT):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(h - 1, 1)
        d.line([(0, y), (w, y)], fill=tuple(
            int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    return im, d


def grid_texture(d, w, h, step=54, color=(30, 58, 84), alpha=8):
    """极淡的卷宗网格（RGB 无 alpha，用接近背景的暗色实现）"""
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=color, width=1)


def tw(d, t, f):
    return d.textbbox((0, 0), t, font=f)[2]


def wrap(t, f, maxw, d):
    lines, cur = [], ""
    for ch in t:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if tw(d, cur + ch, f) > maxw and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def para(d, x, y, t, f, maxw, lh, fill=TXT2):
    """自动换行段落，返回结束 y"""
    yy = y
    for ln in wrap(t, f, maxw, d):
        d.text((x, yy), ln, font=f, fill=fill)
        yy += lh
    return yy


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def center(d, cx, cy, t, f, fill):
    d.text((cx, cy), t, font=f, fill=fill, anchor="mm")


def left_mid(d, x, cy, t, f, fill):
    d.text((x, cy), t, font=f, fill=fill, anchor="lm")


def mark_char(m):
    return {"ok": "√", "no": "×", "q": "?"}.get(m, "")


def draw_matrix(d, ox, oy, rows, cols, marks, cell=92,
                head_col=(21, 45, 68), head_row=(21, 45, 68),
                frow=f_reg(19), fcol=f_reg(19), fmark=f_bold(30)):
    """逻辑格矩阵：右上留空，第一列为行标题，第一行为列标题"""
    n_r, n_c = len(rows), len(cols)
    x0 = ox + 232          # 列宽固定给行标题
    y0 = oy + 56
    # 行标题
    for i, r in enumerate(rows):
        y = y0 + i * cell
        rrect(d, [ox, y, ox + 226, y + cell - 6], 8, fill=head_row, outline=LINE)
        left_mid(d, ox + 14, y + (cell - 6) / 2, r, frow, TXT)
    # 列标题
    for j, c in enumerate(cols):
        x = x0 + j * cell
        rrect(d, [x, oy, x + cell - 6, oy + 46], 8, fill=head_col, outline=LINE)
        center(d, x + (cell - 6) / 2, oy + 23, c, fcol, TXT)
    # 单元格
    for i in range(n_r):
        for j in range(n_c):
            x = x0 + j * cell
            y = y0 + i * cell
            m = marks.get((i, j))
            ch = mark_char(m) if m else ""
            if m == "ok":
                bg, fg, ol = (34, 92, 74), OKC, OKC
            elif m == "no":
                bg, fg, ol = (32, 53, 71), (86, 112, 138), None
            elif m == "q":
                bg, fg, ol = (31, 66, 98), ACC2, None
            else:
                bg, fg, ol = (23, 48, 73), TXT2, LINE
            rrect(d, [x, y, x + cell - 6, y + cell - 6], 8, fill=bg,
                  outline=ol or (41, 73, 101), width=2 if m == "ok" else 1)
            if ch:
                center(d, x + (cell - 6) / 2, y + (cell - 6) / 2, ch, fmark, fg)
    return x0 + n_c * cell, y0 + n_r * cell


def legend_dot(d, x, y, color, label, f=f_reg(18), fill=TXT2):
    d.ellipse([x, y - 6, x + 12, y + 6], fill=color)
    left_mid(d, x + 20, y, label, f, fill)


def browser_frame(d, box, title, sub=""):
    """浏览器窗口外框，返回内容区 box"""
    x, y, x2, y2 = box
    rrect(d, box, 16, fill=(13, 31, 49), outline=(52, 88, 121), width=2)
    d.rectangle([x, y, x2, y + 44], fill=(24, 51, 77))
    for i, c in enumerate([(229, 96, 92), (232, 184, 75), (86, 199, 130)]):
        d.ellipse([x + 18 + i * 22, y + 15, x + 30 + i * 22, y + 27], fill=c)
    center(d, (x + x2) / 2, y + 22, title, f_reg(18), TXT)
    if sub:
        pass
    return [x + 18, y + 62, x2 - 18, y2 - 18]


# =========================================================
# 1. 封面（3:4 竖版 1080x1440）
# =========================================================
def cover_main(path):
    W, H = 1080, 1440
    im, d = canvas(W, H, (9, 24, 39), (23, 52, 79))
    grid_texture(d, W, H, 76, (28, 55, 82))

    # 顶部标签
    rrect(d, [96, 84, 500, 138], 27, fill=(31, 66, 98), outline=LINE)
    center(d, 298, 111, "《人间防骗指南》 推理游戏", f_bold(23), ACC)

    # 主视觉：4x4 逻辑格
    bx, by = 96, 186
    cs = 118
    rows = ["冒充客服", "杀猪盘", "裸聊", "刷单"]
    cols = ["小王", "老师", "小姐姐", "群主"]
    x0, y0 = bx + 172, by + 62
    for i, r in enumerate(rows):
        y = y0 + i * cs
        rrect(d, [bx, y, bx + 164, y + cs - 10], 10, fill=(26, 55, 83), outline=LINE)
        left_mid(d, bx + 18, y + (cs - 10) / 2, r, f_bold(25), TXT)
    for j, c in enumerate(cols):
        x = x0 + j * cs
        rrect(d, [x, by, x + cs - 10, by + 50], 10, fill=(26, 55, 83), outline=LINE)
        center(d, x + (cs - 10) / 2, by + 25, c, f_bold(23), TXT)
    demo = {(0, 0): "ok", (0, 1): "no", (0, 2): "no", (0, 3): "no",
            (1, 1): "ok", (1, 0): "no", (1, 2): "no", (1, 3): "no",
            (2, 2): "ok", (3, 3): "q"}
    fmk = f_bold(44)
    for i in range(4):
        for j in range(4):
            x, y = x0 + j * cs, y0 + i * cs
            m = demo.get((i, j))
            ch = mark_char(m) if m else ""
            if m == "ok":
                bg, fg, ol = (34, 92, 74), OKC, OKC
            elif m == "no":
                bg, fg, ol = (32, 53, 71), (86, 112, 138), None
            else:
                bg, fg, ol = (23, 48, 73), ACC2, ACC2
            rrect(d, [x, y, x + cs - 10, y + cs - 10], 10, fill=bg,
                  outline=ol or (41, 73, 101), width=3 if m == "ok" else 1)
            if ch:
                center(d, x + (cs - 10) / 2, y + (cs - 10) / 2, ch, fmk, fg)

    # 标题
    ty = 838
    center(d, W / 2, ty, "识 骗 迷 局", f_bold(112), WHITE)
    d.line([(170, ty + 74), (910, ty + 74)], fill=ACC, width=3)
    center(d, W / 2, ty + 118, "谁是骗子 × 哪套剧本 × 盯上的是谁", f_bold(35), ACC)
    center(d, W / 2, ty + 172, "不靠猜，靠线索一步步把格子填满",
           f_reg(29), TXT2)

    # 底部数据条
    cy = 1156
    rw = 296
    for i, (num, lab) in enumerate([("371", "篇真实骗局"),
                                    ("40", "关烧脑推理"),
                                    ("123", "篇涉刑警示")]):
        x = 96 + i * 312
        rrect(d, [x, cy, x + rw, cy + 116], 14, fill=(17, 39, 60), outline=LINE)
        center(d, x + rw / 2, cy + 41, num, f_num(54), ACC2)
        center(d, x + rw / 2, cy + 90, lab, f_reg(23), TXT2)

    center(d, W / 2, 1344, "单文件 · 零依赖 · 双击离线就能玩",
           f_reg(25), (126, 158, 186))
    center(d, W / 2, 1392, "《人间防骗指南》出品 · 371 篇真实骗局改编",
           f_reg(22), (96, 128, 156))
    im.save(path, quality=95)
    return path


def cover_brain(path):
    W, H = 1080, 1440
    im, d = canvas(W, H, (13, 22, 34), (26, 46, 62))
    grid_texture(d, W, H, 70, (32, 54, 70))

    center(d, W / 2, 112, "第 4 章 · 灰产暗流 · 第 7 关", f_bold(26), ACC)

    # 难度星号
    sx = 420
    for i in range(5):
        c = ACC2 if i < 4 else (60, 84, 106)
        center(d, sx + i * 62, 186, "★", f_reg(44), c)

    center(d, W / 2, 306, "这 8 条线索", f_bold(64), TXT)
    center(d, W / 2, 392, "只 有 一 个 答 案", f_bold(84), ACC)
    d.line([(190, 452), (890, 452)], fill=LINE, width=2)

    # 线索卡列表
    cx, cy = 110, 496
    clues = [
        ("01", "自称客服的人，剧本不是杀猪盘", False),
        ("02", "盯上商家店主的人，收场是「被套走验证码」", False),
        ("03", "用荐股剧本的人，盯上的是负债人", False),
        ("04", "「同城小姐姐」没有用刷单返利剧本", False),
        ("05", "收场被拉黑的，剧本不是裸聊敲诈", True),
        ("06", "受害人说：他声音特别诚恳", True),
        ("07", "收场是「诱导借贷」的人，盯上的不是中老年", False),
        ("08", "四个人里，只有一个人用了裸聊敲诈", False),
    ]
    for i, (no, t, warn) in enumerate(clues):
        y = cy + i * 88
        fill = (38, 34, 46) if warn else (22, 47, 72)
        ol = RED if warn else LINE
        rrect(d, [cx, y, cx + 860, y + 74], 12, fill=fill, outline=ol,
              width=2 if warn else 1)
        center(d, cx + 44, y + 37, no, f_num(28), ACC if not warn else RED)
        left_mid(d, cx + 82, y + 37, t, f_reg(26), TXT if not warn else (240, 176, 178))
        if warn:
            rrect(d, [cx + 700, y + 20, cx + 842, y + 54], 17, fill=(72, 33, 38))
            center(d, cx + 771, y + 37, "干扰线索", f_reg(21), RED)

    center(d, W / 2, 1252, "案情里的话，有一半是骗你的判断",
           f_bold(36), ACC2)
    center(d, W / 2, 1312, "只有格子不撒谎", f_reg(32), TXT2)

    rrect(d, [130, 1352, 950, 1432], 14, fill=(17, 39, 60), outline=LINE)
    center(d, W / 2, 1378, "5 大章 · 40 关 · 每日谜题", f_bold(30), ACC)
    center(d, W / 2, 1412, "错了只亮红框，所有解析留到复盘", f_reg(23), TXT2)
    im.save(path, quality=95)
    return path


def cover_parents(path):
    W, H = 1080, 1440
    im, d = canvas(W, H, (28, 20, 18), (52, 34, 26))
    grid_texture(d, W, H, 70, (66, 43, 32))

    rrect(d, [72, 96, 500, 152], 28, fill=(70, 44, 32), outline=(112, 78, 56))
    center(d, 286, 124, "给家里人建一道防线", f_bold(26), ACC2)

    center(d, W / 2, 268, "别跟爸妈讲道理", f_bold(72), TXT)
    center(d, W / 2, 372, "让他们自己推理一遍", f_bold(72), ACC2)
    d.line([(160, 440), (920, 440)], fill=(112, 78, 56), width=2)

    items = [
        ("01", "一局一个真实骗局", "冒充客服 / 荐股 / 裸聊 / 刷单，全是发生过的"),
        ("02", "像做数独一样排排除法", "不用打字，点格子就行，手机上也能玩"),
        ("03", "错了不批评，最后才讲透", "复盘里写清楚这套话术怎么识破"),
        ("04", "涉刑的红字让他们自己看到", "借卡、走账、代取现，碰了不只是丢钱"),
    ]
    y = 512
    for no, t, s in items:
        rrect(d, [96, y, 984, y + 168], 16, fill=(43, 29, 23), outline=(112, 78, 56))
        center(d, 152, y + 84, no, f_num(44), ACC2)
        left_mid(d, 210, y + 62, t, f_bold(36), TXT)
        para(d, 212, y + 106, s, f_reg(26), 700, 36, (198, 172, 152))
        y += 190

    rrect(d, [96, 1290, 984, 1396], 16, fill=(70, 44, 32), outline=ACC2, width=2)
    center(d, W / 2, 1328, "《识骗迷局》", f_bold(40), ACC2)
    center(d, W / 2, 1374, "单文件离线 · 双击即玩 · 不用注册", f_reg(26), (206, 180, 158))
    im.save(path, quality=95)
    return path


# =========================================================
# 2. 界面预览 Mockup
# =========================================================
def ui_puzzle_page(path):
    W, H = 1600, 1000
    im, d = canvas(W, H, (7, 18, 30), (16, 37, 56))
    left_mid(d, 60, 46, "界面预览 · 关卡页", f_bold(30), TXT)
    left_mid(d, 60, 84, "案情 / 线索卡 / 逻辑格 / 指认面板 同屏可达",
             f_reg(20), TXT2)

    box = [80, 120, 1520, 940]
    bx = browser_frame(d, box, "识骗迷局 · 第 3 章 第 5 关 · 情感陷阱")
    x, y, x2, y2 = bx

    # 案情条
    rrect(d, [x, y, x2, y + 104], 12, fill=(24, 51, 77), outline=LINE)
    left_mid(d, x + 22, y + 28, "案情 · 受害人陈述", f_bold(20), ACC)
    para(d, x + 22, y + 58,
         "小林接到「快递客服」电话，说包裹丢失要理赔。对方报出了她的姓名、电话和订单号，"
         "说话特别有耐心，还提醒她「别挂断哦」。当天她先后联系过四个人。",
         f_reg(19), x2 - x - 44, 28, TXT)
    rrect(d, [x2 - 196, y + 16, x2 - 20, y + 48], 16, fill=(72, 33, 38))
    center(d, x2 - 108, y + 32, "陈述含情绪误导", f_reg(17), RED)

    gy = y + 128
    rows = ["冒充客服退款", "杀猪盘荐股", "裸聊敲诈", "刷单返利"]
    cols = ["客服小王", "荐股老师", "同城小姐姐", "刷单群主"]
    marks = {(0, 0): "ok", (0, 1): "no", (0, 2): "no", (0, 3): "no",
             (1, 0): "no", (1, 1): "ok", (2, 1): "no", (2, 2): "q",
             (3, 1): "no", (3, 3): "ok"}
    draw_matrix(d, x, gy, rows, cols, marks, cell=100)

    # 线索卡（右侧）
    cx = x + 232 + 4 * 100 + 40
    cw = x2 - cx
    rrect(d, [cx, gy, x2, gy + 44], 10, fill=(24, 51, 77), outline=LINE)
    left_mid(d, cx + 18, gy + 22, "线索卡（点击高亮关联行列）", f_bold(19), ACC)
    clues = [
        "自称客服的人，剧本不是杀猪盘",
        "盯上商家店主的，收场是被套走验证码",
        "「同城小姐姐」没用刷单返利剧本",
        "用荐股剧本的人，盯上的是负债人",
        "收场被拉黑的，剧本不是裸聊敲诈",
    ]
    for i, t in enumerate(clues):
        cy2 = gy + 58 + i * 78
        rrect(d, [cx, cy2, x2, cy2 + 66], 10,
              fill=(21, 45, 68) if i != 1 else (26, 58, 84),
              outline=ACC if i == 1 else LINE, width=2 if i == 1 else 1)
        center(d, cx + 26, cy2 + 33, str(i + 1), f_num(26),
               ACC if i == 1 else TXT2)
        para(d, cx + 48, cy2 + 20, t, f_reg(19), cw - 60, 24,
             TXT if i == 1 else TXT2)

    # 底部工具 + 指认
    by = y2 - 92
    for i, lab in enumerate(["√ / × / ? 单击循环", "拖动批量排除", "提示 ×2", "撤销"]):
        bw = 190
        bx2 = x + i * (bw + 16)
        rrect(d, [bx2, by, bx2 + bw, by + 52], 10, fill=(24, 51, 77), outline=LINE)
        center(d, bx2 + bw / 2, by + 26, lab, f_reg(19), TXT2)
    rrect(d, [x2 - 300, by, x2, by + 52], 10, fill=ACC, outline=None)
    center(d, x2 - 150, by + 26, "提交指认 →", f_bold(22), (8, 26, 24))

    im.save(path, quality=95)
    return path


def ui_accuse_page(path):
    W, H = 1600, 1000
    im, d = canvas(W, H, (7, 18, 30), (16, 37, 56))
    left_mid(d, 60, 46, "界面预览 · 指认面板 / 结算", f_bold(30), TXT)
    left_mid(d, 60, 84, "四个选项外观完全一致，正解不提前高亮", f_reg(20), TXT2)

    box = [80, 120, 1520, 940]
    x, y, x2, y2 = browser_frame(d, box, "识骗迷局 · 第 3 章 第 5 关 · 提交指认")
    center(d, (x + x2) / 2, y + 34,
           "谁在用哪套剧本，盯上谁，最后怎么收场？", f_bold(28), TXT)

    opts = [
        ("A", "客服小王", "冒充客服退款", "学生党", "被套走验证码", "ok"),
        ("B", "荐股老师", "杀猪盘荐股", "负债人", "诱导借贷", "no"),
        ("C", "同城小姐姐", "裸聊敲诈", "中老年", "被拉黑", "no"),
        ("D", "刷单群主", "刷单返利", "商家店主", "走上帮信罪", "no"),
    ]
    oy = y + 92
    for i, (k, who, script, tgt, end, st) in enumerate(opts):
        oy2 = oy + i * 132
        sel = st == "ok"
        rrect(d, [x, oy2, x2, oy2 + 114], 14,
              fill=(28, 60, 46) if sel else (22, 47, 72),
              outline=OKC if sel else LINE, width=3 if sel else 1)
        center(d, x + 46, oy2 + 57, k, f_bold(40), OKC if sel else TXT2)
        info = [(who, "嫌疑人"), (script, "剧本"), (tgt, "目标"), (end, "收场")]
        for j, (val, lab) in enumerate(info):
            cxx = x + 168 + j * 310
            center(d, cxx, oy2 + 34, lab, f_reg(17), TXT2)
            center(d, cxx, oy2 + 74, val, f_bold(27), TXT)
        if sel:
            rrect(d, [x2 - 190, oy2 + 14, x2 - 22, oy2 + 52], 19, fill=(31, 96, 61))
            center(d, x2 - 106, oy2 + 33, "本次正确", f_reg(20), OKC)

    by = y2 - 76
    for i, lab in enumerate(["用时 03:12", "第 1 次指认", "提示 未使用", "损失 ¥0"]):
        bw = 240
        bx2 = x + i * (bw + 20)
        rrect(d, [bx2, by, bx2 + bw, by + 54], 10, fill=(24, 51, 77), outline=LINE)
        center(d, bx2 + bw / 2, by + 27, lab, f_reg(20), TXT2)
    for i in range(3):
        cx3 = x2 - 150 + i * 54
        center(d, cx3, by + 27, "★", f_reg(34), ACC2 if i < 3 else (60, 84, 106))

    im.save(path, quality=95)
    return path


def ui_review_page(path):
    W, H = 1600, 1000
    im, d = canvas(W, H, (7, 18, 30), (16, 37, 56))
    left_mid(d, 60, 46, "界面预览 · 复盘页", f_bold(30), TXT)
    left_mid(d, 60, 84, "局中不讲解，全部解析后置到这里", f_reg(20), TXT2)

    box = [80, 120, 1520, 940]
    x, y, x2, y2 = browser_frame(d, box, "识骗迷局 · 第 3 章 第 5 关 · 复盘")

    # 左：推导链
    lw = 640
    rrect(d, [x, y, x + lw, y2], 12, fill=(19, 42, 65), outline=LINE)
    left_mid(d, x + 24, y + 30, "逐条线索怎么推出来的", f_bold(24), ACC)
    steps = [
        ("线索 2 + 线索 5", "被拉黑 ≠ 裸聊敲诈、≠ 刷单返利\n→ 收场只剩「借贷」或「验证码」"),
        ("线索 3", "同城小姐姐 ≠ 刷单返利\n→ 刷单返利落在另外三人"),
        ("线索 1", "客服身份 ≠ 杀猪盘\n→ 客服小王的剧本被锁定"),
        ("交叉唯一解", "客服小王 = 冒充客服退款 = 学生党 = 被套走验证码"),
    ]
    sy = y + 74
    for i, (h, t) in enumerate(steps):
        bl = []
        for ln in t.split("\n"):
            bl += wrap(ln, f_reg(19), lw - 108, d)
        hh = 56 + len(bl) * 28 + 12
        rrect(d, [x + 20, sy, x + lw - 20, sy + hh], 10,
              fill=(24, 51, 77), outline=LINE)
        rrect(d, [x + 20, sy, x + 26, sy + hh], 3, fill=ACC)
        left_mid(d, x + 44, sy + 28, h, f_bold(20), ACC)
        yy = sy + 52
        for ln in bl:
            d.text((x + 44, yy), ln, font=f_reg(19), fill=TXT)
            yy += 28
        sy += hh + 18

    # 右：真实骗术解析
    rx = x + lw + 28
    rrect(d, [rx, y, x2, y2], 12, fill=(19, 42, 65), outline=LINE)
    left_mid(d, rx + 24, y + 30, "真实骗术解析（摘自知识库）", f_bold(24), ACC2)

    center(d, rx + 34, y + 74, "!", f_bold(28), None)
    d.ellipse([rx + 22, y + 60, rx + 48, y + 86], outline=RED, width=2)

    left_mid(d, rx + 62, y + 74, "冒充客服退款 · 第 004 篇", f_bold(23), TXT)
    para(d, rx + 24, y + 112,
         "识别要点：\n"
         "① 客服不会主动索要验证码或让你下载远程软件\n"
         "② 理赔一定走平台原路径，不会让你先转账「验证流水」\n"
         "③ 报得出订单号不等于身份真实，信息早已泄露\n"
         "④ 对方越强调「别挂断」，越说明经不起核实",
         f_reg(20), x2 - rx - 48, 32, TXT2)

    # 判例卡
    py = y + 300
    rrect(d, [rx + 20, py, x2 - 20, py + 132], 12, fill=(24, 51, 77), outline=LINE)
    left_mid(d, rx + 44, py + 30, "同类真实判例", f_bold(20), ACC)
    para(d, rx + 44, py + 62,
         "2023 年某地法院判决：被告人冒充电商平台客服，以「理赔需验证账户」为由诱导被害人提供验证码，"
         "骗取多人钱款，以诈骗罪追究刑事责任。",
         f_reg(19), x2 - rx - 90, 28, TXT2)

    # 涉刑警示条（红）
    wy = y + 462
    rrect(d, [rx + 20, wy, x2 - 20, wy + 128], 12, fill=(63, 29, 33), outline=RED, width=2)
    left_mid(d, rx + 44, wy + 32, "涉刑警示", f_bold(22), RED)
    para(d, rx + 44, wy + 64,
         "这一类里，「帮忙走账、代取现」看着像人情，实际可能构成帮助信息网络犯罪活动罪。",
         f_reg(19), x2 - rx - 96, 30, (238, 176, 178))

    # 底部按钮
    by = y2 - 84
    rrect(d, [rx + 20, by, rx + 250, by + 56], 12, fill=(24, 51, 77), outline=LINE)
    center(d, rx + 135, by + 28, "复制为文字", f_reg(21), TXT2)
    rrect(d, [rx + 274, by, rx + 504, by + 56], 12, fill=ACC, outline=None)
    center(d, rx + 389, by + 28, "这篇讲透了 →", f_bold(21), (8, 26, 24))

    im.save(path, quality=95)
    return path


# =========================================================
# 3. 说明图
# =========================================================
def flow_chart(path):
    W, H = 1600, 900
    im, d = canvas(W, H, (7, 18, 30), (16, 37, 56))
    center(d, W / 2, 62, "一局怎么走完", f_bold(44), WHITE)
    center(d, W / 2, 116, "平均 3~8 分钟 · 错了只亮红框，可以随时重推理",
           f_reg(24), TXT2)

    steps = [
        ("01", "看案情", "受害人陈述 3~5 句\n里面混着情绪化误判", False),
        ("02", "翻线索", "8~12 条线索卡\n可标记「已用」", False),
        ("03", "填格子", "√ × ? 三态循环\n像数独一样做排除", False),
        ("04", "提交指认", "4 个组合选项\n外观完全一样", False),
        ("05", "复盘", "推导链 + 真实骗术解析\n+ 同类判例", True),
    ]
    bw, gap = 268, 42
    total = len(steps) * bw + (len(steps) - 1) * gap
    sx = (W - total) / 2
    sy = 196
    ch = 352
    for i, (no, t, desc, hot) in enumerate(steps):
        x = sx + i * (bw + gap)
        rrect(d, [x, sy, x + bw, sy + ch], 18,
              fill=(43, 30, 36) if hot else (22, 47, 72),
              outline=ACC2 if hot else LINE, width=2 if hot else 1)
        center(d, x + bw / 2, sy + 48, no, f_num(50), ACC2 if hot else ACC)
        center(d, x + bw / 2, sy + 124, t, f_bold(38), TXT)
        yy = sy + 180
        for ln in desc.split("\n"):
            center(d, x + bw / 2, yy, ln, f_reg(21), TXT2)
            yy += 34
        if i < len(steps) - 1:
            ax = x + bw + 6
            d.line([(ax, sy + 176), (ax + gap - 12, sy + 176)],
                   fill=ACC, width=3)
            d.polygon([(ax + gap - 12, sy + 168), (ax + gap - 12, sy + 184),
                       (ax + gap, sy + 176)], fill=ACC)

    # 底部红线提示
    rrect(d, [110, 606, W - 110, 772], 16, fill=(19, 42, 65), outline=LINE)
    left_mid(d, 150, 648, "局中的三条原则", f_bold(28), ACC)
    cols = [
        "选项迷惑：四个都像真的，正解靠推理",
        "案情不可信：描述里混着误导情绪",
        "讲解后置：解析全部放复盘",
    ]
    for i, t in enumerate(cols):
        cx = 150 + i * 456
        d.ellipse([cx, 700, cx + 13, 713], fill=ACC2)
        left_mid(d, cx + 24, 706, t, f_reg(20), TXT2)

    im.save(path, quality=95)
    return path


def sample_case(path):
    W, H = 1500, 1200
    im, d = canvas(W, H, (7, 18, 30), (16, 37, 56))
    left_mid(d, 70, 56, "样关 · 第 1 章 第 1 关「退款来电」", f_bold(38), WHITE)
    left_mid(d, 70, 100, "3×3 入门局 · 只用直接线索 · 保证唯一解", f_reg(22), TXT2)

    # 案情卡
    rrect(d, [70, 138, W - 70, 300], 14, fill=(24, 51, 77), outline=LINE)
    left_mid(d, 100, 172, "案情", f_bold(24), ACC)
    para(d, 100, 208,
         "大学生小林接到自称「快递客服」的电话，说包裹丢失要理赔。对方准确报出了她的订单信息，"
         "并让她下载一个远程协助软件。当天她接触过的三个人，都被列入排查。",
         f_reg(23), W - 210, 36, TXT)

    # 矩阵
    rows = ["冒充客服退款", "裸聊敲诈", "刷单返利"]
    cols = ["客服小王", "同城小姐姐", "刷单群主"]
    marks = {(0, 0): "ok", (0, 1): "no", (0, 2): "no",
             (1, 0): "no", (1, 1): "ok",
             (2, 0): "no", (2, 2): "ok"}
    draw_matrix(d, 70, 330, rows, cols, marks, cell=126,
                frow=f_bold(23), fcol=f_bold(23), fmark=f_bold(50))

    # 线索卡
    cx = 770
    rrect(d, [cx, 330, W - 70, 800], 14, fill=(19, 42, 65), outline=LINE)
    left_mid(d, cx + 30, 366, "线索卡", f_bold(26), ACC)
    clues = [
        "自称客服的人，剧本不是裸聊敲诈",
        "用刷单返利剧本的，不是客户口中的「小王」",
        "裸聊敲诈这一列，只有一个人会对上",
        "刷单群主背后常有完整任务群",
    ]
    for i, t in enumerate(clues):
        cy = 406 + i * 96
        rrect(d, [cx + 26, cy, W - 96, cy + 78], 12, fill=(24, 51, 77), outline=LINE)
        center(d, cx + 62, cy + 39, str(i + 1), f_num(32), ACC)
        left_mid(d, cx + 94, cy + 39, t, f_reg(23), TXT)

    # 正解条
    ay = 838
    rrect(d, [70, ay, W - 70, ay + 112], 14, fill=(28, 60, 46), outline=OKC, width=2)
    left_mid(d, 108, ay + 36, "唯一正解", f_bold(25), OKC)
    left_mid(d, 108, ay + 80, "客服小王 = 冒充客服退款 = 学生党 = 被套走验证码",
             f_bold(31), WHITE)

    # 复盘要点
    ry = 982
    rrect(d, [70, ry, W - 70, H - 44], 14, fill=(19, 42, 65), outline=LINE)
    left_mid(d, 108, ry + 34, "复盘要点", f_bold(25), ACC2)
    para(d, 108, ry + 68,
         "客服不会主动索要验证码，也不会让你装远程软件；理赔只走平台原路径。"
         "报得出订单号不等于身份真实——你的信息早就泄露过。",
         f_reg(22), W - 220, 34, TXT2)
    im.save(path, quality=95)
    return path


def chapter_map(path):
    W, H = 1600, 960
    im, d = canvas(W, H, (7, 18, 30), (16, 37, 56))
    center(d, W / 2, 58, "关卡体系 · 5 章 40 关", f_bold(44), WHITE)
    center(d, W / 2, 108, "每章第 8 关固定为「涉刑警示关」，读完比通关重要",
           f_reg(23), TXT2)

    rows = [
        ("第 1 章", "入门拆解", "校园 / 兼职高发骗术", "3×3 · 2 轴", "仅直接线索", 1),
        ("第 2 章", "话术迷阵", "冒充客服 / 公检法 / 领导", "3×3 · 3 轴", "否定线索 · 条件线索", 2),
        ("第 3 章", "情感陷阱", "杀猪盘 / 裸聊 / 同城", "4×4 · 3 轴", "案情假线索登场", 3),
        ("第 4 章", "灰产暗流", "洗钱 / 帮信 / 跑分 / 黑产", "4×4 · 4 轴", "共用线索 · 线索反转", 4),
        ("第 5 章", "终局对弈", "跨章综合大案", "5×5 · 4 轴", "全机制 + 陷阱线索", 5),
    ]
    y = 164
    rh = 106
    rrect(d, [70, y, W - 70, y + 44], 10, fill=(24, 51, 77), outline=LINE)
    heads = [("章", 96), ("标题", 216), ("题材", 420), ("矩阵", 890),
             ("新机制", 1080), ("难度", 1336)]
    for t, hx in heads:
        left_mid(d, hx, y + 22, t, f_bold(21), TXT2)

    for i, (ch, title, topic, size, mech, star) in enumerate(rows):
        yy = y + 56 + i * (rh + 12)
        last = i == 4
        rrect(d, [70, yy, W - 70, yy + rh], 12,
              fill=(38, 33, 28) if last else (21, 45, 68),
              outline=ACC2 if last else LINE, width=2 if last else 1)
        left_mid(d, 96, yy + rh / 2, ch, f_bold(25), ACC)
        left_mid(d, 216, yy + rh / 2, title, f_bold(33), TXT)
        left_mid(d, 420, yy + rh / 2, topic, f_reg(22), TXT2)
        left_mid(d, 890, yy + rh / 2, size, f_num(29), ACC2)
        left_mid(d, 1080, yy + rh / 2, mech, f_reg(22), TXT2)
        for s in range(5):
            c = ACC2 if s < star else (58, 82, 104)
            center(d, 1348 + s * 32, yy + rh / 2, "★", f_reg(27), c)

    # 底部说明
    by = y + 56 + 5 * (rh + 12) + 12
    notes = [
        ("难度不靠格子堆", "靠线索抽象度：直接 → 条件 → 传递"),
        ("错题可以无限重来", "错了只亮红框，不锁关、不劝退"),
        ("每日谜题", "每天 1 题 · 按日期种子 · 离线同题"),
    ]
    for i, (h, t) in enumerate(notes):
        nx = 70 + i * 500
        rrect(d, [nx, by, nx + 470, by + 90], 12, fill=(19, 42, 65), outline=LINE)
        left_mid(d, nx + 24, by + 30, h, f_bold(23), ACC)
        left_mid(d, nx + 24, by + 64, t, f_reg(19), TXT2)

    im.save(path, quality=95)
    return path


def tech_spec(path):
    W, H = 1600, 900
    im, d = canvas(W, H, (7, 18, 30), (16, 37, 56))
    center(d, W / 2, 62, "形态 · 与现有产品的关系", f_bold(44), WHITE)
    center(d, W / 2, 116, "单文件、零依赖、双击离线可玩，和《人间防骗指南》同源",
           f_reg(24), TXT2)

    # 左：本作规格
    rrect(d, [80, 176, 760, 566], 16, fill=(21, 45, 68), outline=LINE)
    left_mid(d, 116, 216, "《识骗迷局》（本作）", f_bold(30), ACC)
    para(d, 116, 262,
         "练的是「信息推理」\n"
         "· 单文件 HTML，≤ 400KB\n"
         "· 原生 HTML + CSS + ES6，无框架\n"
         "· 题库内联，断网可用\n"
         "· localStorage 存关卡星级\n"
         "· 构建：tools/build_murdle.py",
         f_reg(23), 610, 44, TXT2)

    # 右：现有游戏
    rrect(d, [860, 176, 1520, 566], 16, fill=(21, 45, 68), outline=LINE)
    left_mid(d, 896, 216, "现有 game/（12 局对话）", f_bold(30), ACC2)
    para(d, 896, 262,
         "练的是「当场反应」\n"
         "· 聊天式对话界面\n"
         "· 每选项独立回应\n"
         "· 局中不讲解，复盘才解析\n"
         "· 已上线：HowToAvoidScams/game/\n"
         "· 两者互补，入口互相链接",
         f_reg(23), 600, 44, TXT2)

    d.line([(810, 206), (810, 540)], fill=LINE, width=2)
    d.ellipse([768, 352, 852, 396], fill=(19, 42, 65), outline=LINE, width=2)
    center(d, 810, 374, "互补", f_bold(21), ACC)

    # 底部数据源
    rrect(d, [80, 604, 1520, 806], 16, fill=(19, 42, 65), outline=LINE)
    left_mid(d, 116, 646, "唯一数据源", f_bold(28), ACC)
    para(d, 116, 690,
         "tools/articles.json（371 篇 · 16 类）+ tools/news.json（判例挂载）\n"
         "每关的 9 个角色、9 个场景分区和全部线索，都从这一篇骗局里抽取改写；"
         "入库前跑穷举校验，断言「解有且只有一个」。",
         f_reg(23), 1360, 44, TXT2)
    im.save(path, quality=95)
    return path


# ---------------- 浏览页 ----------------
def write_index(items, path):
    cards = []
    for name, file, desc in items:
        cards.append(
            '<figure class="card"><a href="%s"><img loading="lazy" src="%s" alt="%s"></a>'
            '<figcaption><b>%s</b><span>%s</span></figcaption></figure>'
            % (file, file, name, name, desc))
    tpl = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>识骗迷局 · 配图</title><style>
body{margin:0;font:14px/1.7 "Microsoft YaHei",sans-serif;background:#0f2030;color:#e9f1f8}
header{background:#132b44;padding:18px 26px;border-bottom:1px solid #25506f}
header h1{margin:0;font-size:20px;color:#4fd1c5}
header p{margin:4px 0 0;font-size:12px;color:#a3bdd4}
.wrap{max-width:1400px;margin:0 auto;padding:20px 26px 50px;
display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}
.card{margin:0;background:#1b3955;border:1px solid #25506f;border-radius:12px;overflow:hidden}
.card img{width:100%d;display:block;background:#0f2030}
.card figcaption{padding:12px 14px}
.card b{display:block;font-size:15px;color:#e9f1f8}
.card span{display:block;margin-top:4px;font-size:12px;color:#a3bdd4}
.card:hover{border-color:#4fd1c5}
</style></head><body>
<header><h1>《识骗迷局》配图</h1>
<p>3:4 竖版封面可直接发小红书；横版为 UI 预览与说明图。重新生成：tools/gen_murdle_images.py</p></header>
<div class="wrap">%s</div></body></html>"""
    tpl = tpl.replace("100%d", "100%").replace("%s", "__CARDS__")
    io.open(path, "w", encoding="utf-8").write(tpl.replace("__CARDS__", "".join(cards)))


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []

    def add(name, file, desc, fn):
        p = os.path.join(OUT, file)
        fn(p)
        made.append((name, file, desc))
        print("  ✓", file)

    print("生成《识骗迷局》配图 →", OUT)

    # v1 玩法（4 轴逻辑格）已被推翻，04-09 已归档到 _v1-旧玩法/，不再生成

    # 以下由 tools/prep_chars.py、tools/gen_murdoku_proto.py 生成，这里只登记
    extra = [
        ("角色棋子 · 四身份", "12-角色棋子.png",
         "骗子 / 受害者 / 警察 / 路人 ｜ 512 透明底 PNG"),
        ("样关 · 9×9 网格", "11-样关-9x9网格.png",
         "9 人摆进 81 格 ｜ 唯一解已校验"),
    ]
    for item in extra:
        if os.path.exists(os.path.join(OUT, item[1])):
            made.append(item)
            print("  · 登记", item[1])

    add("形态与数据源", "10-形态与数据源.png", "单文件形态 · 数据源 · 与现有 game/ 的关系", tech_spec)

    # 封面仍按 v1 主视觉（4×4 逻辑格），玩法定稿后需重出，先标注保留
    for name, file, desc in [
        ("封面 · 主视觉（v1）", "01-封面-主视觉.png", "3:4 竖版 · 旧版逻辑格主视觉，待重出"),
        ("封面 · 烧脑（v1）", "02-封面-烧脑.png", "3:4 竖版 · 旧版，待重出"),
        ("封面 · 给爸妈（v1）", "03-封面-给爸妈.png", "3:4 竖版 · 旧版，待重出"),
    ]:
        if os.path.exists(os.path.join(OUT, file)):
            made.append((name, file, desc))
            print("  · 登记", file)

    write_index(made, os.path.join(OUT, "index.html"))
    print("完成，共 %d 张 + index.html" % len(made))


if __name__ == "__main__":
    main()
