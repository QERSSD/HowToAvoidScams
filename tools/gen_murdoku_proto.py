# -*- coding: utf-8 -*-
"""
《识骗迷局》9×9 样关示意图。

规则（对齐官方 Murdoku）：
  81 格 = 案发现场平面图，分 9 个区域（3×3 宫）
  9 个角色每人占 1 格，任意一行 / 一列 / 一区内不重复（数独式）
  按线索把 9 个人摆完，骗子和受害者的坐标就是答案

用法： env/default/Scripts/python.exe tools/gen_murdoku_proto.py
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from murdoku_check import CLUES as CLUE_SRC, GIVEN as GIVEN_SRC, NAMES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, "game-adaptations", "assets", "characters")
OUT = os.path.join(ROOT, "game-adaptations", "assets", "11-样关-9x9网格.png")

W, H = 1720, 1272
BG_TOP, BG_BOT = (10, 26, 42), (19, 44, 68)
PANEL, PANEL2 = (24, 51, 77), (18, 40, 61)
LINE = (58, 96, 131)
TXT, TXT2 = (233, 241, 248), (160, 187, 210)
ACC, ACC2 = (79, 209, 197), (232, 184, 75)
RED = (229, 72, 77)
GRID_LINE = (44, 74, 100)
BOX_LINE = (96, 136, 168)


def f(name, size):
    return ImageFont.truetype(os.path.join(r"C:/Windows/Fonts", name), size)


def bold(s):
    return f("msyhbd.ttc", s)


def reg(s):
    return f("msyh.ttc", s)


def num(s):
    return f("Dengl.ttf", s)


def canvas(w, h):
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(
            int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3)))
    return im, d


def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def tw(d, t, fnt):
    return d.textbbox((0, 0), t, font=fnt)[2]


def wrap(t, fnt, maxw, d):
    out, cur = [], ""
    for ch in t:
        if ch == "\n":
            out.append(cur)
            cur = ""
            continue
        if tw(d, cur + ch, fnt) > maxw and cur:
            out.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


# ---------- 关卡数据（样关：冒充客服退款） ----------
# 9 个角色：顺序必须与 murdoku_check.NAMES 一致（id = 下标 + 1）
# 图标只有 4 种，同阵营换的是名字与边框色
ROLES = {
    1: ("pianzi.png", "话务员", "骗"),
    2: ("pianzi.png", "话务组长", "骗"),
    3: ("pianzi.png", "取现手", "骗"),
    4: ("shouhaizhe.png", "小林", "受害"),
    5: ("jingcha.png", "反诈民警", "警"),
    6: ("luren.png", "快递员", "路"),
    7: ("luren.png", "邻居阿姨", "路"),
    8: ("luren.png", "便利店老板", "路"),
    9: ("luren.png", "保安", "路"),
}
ICON = {k: Image.open(os.path.join(CH, v[0])).convert("RGBA") for k, v in ROLES.items()}
TONE = {"骗": RED, "受害": (232, 184, 75), "警": (79, 209, 197), "路": (150, 178, 202)}

# 9 个角色各占 1 格：每行、每列、每 3×3 区各一人（数独式排布）
from murdoku_check import SOL  # noqa: E402

POS = {SOL[n]: i + 1 for i, n in enumerate(NAMES)}
GIVEN = {SOL[n] for n in GIVEN_SRC}
# 角色简称（画在头像下方，解决「图标只有 4 种、人却有 9 个」的辨识问题）
ABBR = {i + 1: n for i, n in enumerate(NAMES)}
ZONES = ["驿站前台", "快递货架", "门口快递柜", "小区门岗", "便利店",
         "3 号楼电梯", "电动车棚", "分拣区", "物业办公室"]

CLUES = [txt for txt, _ in CLUE_SRC]

GRID_X, GRID_Y, CELL = 96, 318, 88
GRID = CELL * 9


def draw_grid(d, img):
    # 外框
    rr(d, [GRID_X - 12, GRID_Y - 12, GRID_X + GRID + 12, GRID_Y + GRID + 12],
       14, fill=(15, 35, 54), outline=LINE, width=2)

    # 空格底 + 区号水印
    for z in range(9):
        zr, zc = z // 3, z % 3
        bx = GRID_X + zc * CELL * 3
        by = GRID_Y + zr * CELL * 3
        d.rectangle([bx, by, bx + CELL * 3, by + CELL * 3], fill=(21, 45, 68))
        d.text((bx + CELL * 1.5, by + CELL * 1.5), str(z + 1),
               font=num(132), fill=(28, 56, 82), anchor="mm")

    # 网格线
    for i in range(10):
        wd = 3 if i % 3 == 0 else 1
        col = BOX_LINE if i % 3 == 0 else GRID_LINE
        d.line([(GRID_X + i * CELL, GRID_Y), (GRID_X + i * CELL, GRID_Y + GRID)],
               fill=col, width=wd)
        d.line([(GRID_X, GRID_Y + i * CELL), (GRID_X + GRID, GRID_Y + i * CELL)],
               fill=col, width=wd)

    # 坐标
    fc = reg(17)
    for c in range(9):
        d.text((GRID_X + c * CELL + CELL / 2, GRID_Y - 20), str(c + 1),
               font=fc, fill=TXT2, anchor="mm")
    for r in range(9):
        d.text((GRID_X - 26, GRID_Y + r * CELL + CELL / 2), str(r + 1),
               font=fc, fill=TXT2, anchor="mm")

    # 角色（只在 9 个位置有人）
    ip = 56
    for (r, c), rid in POS.items():
        x = GRID_X + c * CELL
        y = GRID_Y + r * CELL
        _, name, camp = ROLES[rid]
        tone = TONE[camp]

        # 格底
        d.rounded_rectangle([x + 3, y + 3, x + CELL - 3, y + CELL - 3],
                            radius=9, fill=(27, 55, 82), outline=tone, width=3)
        # 头像
        ic = ICON[rid].resize((ip, ip), Image.LANCZOS)
        img.paste(ic, (x + (CELL - ip) // 2, y + 5), ic)
        # 名字
        d.text((x + CELL / 2, y + CELL - 20), ABBR[rid],
               font=bold(13), fill=tone, anchor="mm")

        # 主骗 / 受害者加重标记
        if rid == 1:
            d.rounded_rectangle([x + 1, y + 1, x + CELL - 1, y + CELL - 1],
                                radius=11, outline=RED, width=4)
            d.text((x + CELL - 15, y + 15), "骗", font=bold(15), fill=RED, anchor="mm")
        if rid == 4:
            d.rounded_rectangle([x + 1, y + 1, x + CELL - 1, y + CELL - 1],
                                radius=11, outline=ACC2, width=4)
            d.text((x + CELL - 15, y + 15), "受", font=bold(15), fill=ACC2, anchor="mm")

    # 给定标记
    for (r, c) in GIVEN:
        bx = GRID_X + c * CELL + 4
        by = GRID_Y + r * CELL + 4
        d.ellipse([bx, by, bx + 20, by + 20], fill=(14, 33, 51), outline=ACC, width=2)
        d.text((bx + 10, by + 10), "起", font=reg(12), fill=ACC, anchor="mm")


def main():
    im, d = canvas(W, H)

    # 标题
    d.text((96, 54), "样关 · 第 2 章 第 3 关「退款来电」", font=bold(38), fill=TXT)
    d.text((96, 100), "9×9 现场图 · 9 个人 · 每行每列每区各一人",
           font=reg(22), fill=TXT2)

    # 案情
    rr(d, [96, 146, W - 96, 286], 14, fill=PANEL, outline=LINE)
    d.text((126, 172), "案情", font=bold(23), fill=ACC)
    body = ("大学生小林接到「快递客服」电话，对方报得出她的姓名、订单号和收货地址，说包裹丢失要理赔。"
            "她按指引下载了远程协助软件，共享屏幕后账户被转走存款。当天这片街区里，"
            "一共九个人出现在错误的时间、错误的位置——把他们一个个放回原处，就知道谁在骗她。")
    yy = 206
    for ln in wrap(body, reg(21), W - 250, d):
        d.text((126, yy), ln, font=reg(21), fill=TXT if yy == 206 else TXT2)
        yy += 30

    # 网格
    draw_grid(d, im)

    # 右栏
    rx = GRID_X + GRID + 54
    rw = W - 96 - rx
    d.text((rx, 306), "现场线索", font=bold(23), fill=ACC)
    d.text((rx + 118, 311), "（全部成立才能结案）", font=reg(16), fill=TXT2)
    for i, t in enumerate(CLUES):
        cy = 344 + i * 52
        rr(d, [rx, cy, W - 96, cy + 46], 9, fill=PANEL2, outline=LINE)
        d.text((rx + 12, cy + 13), "%02d" % (i + 1), font=num(18), fill=ACC)
        d.text((rx + 46, cy + 12), t, font=reg(17), fill=TXT)

    # 结案判定
    ay = 344 + len(CLUES) * 52 + 16
    rr(d, [rx, ay, W - 96, ay + 150], 12, fill=(27, 50, 44), outline=ACC, width=2)
    d.text((rx + 20, ay + 16), "结案判定", font=bold(21), fill=ACC)

    def where(name):
        r, c = SOL[name]
        z = (r // 3) * 3 + c // 3
        return "第 %d 行 · 第 %d 列 · %s" % (r + 1, c + 1, ZONES[z])

    d.text((rx + 20, ay + 54), "受害者 小林", font=reg(19), fill=TXT2)
    d.text((rx + 170, ay + 52), where("小林"), font=bold(21), fill=ACC2)
    d.text((rx + 20, ay + 96), "主骗 话务员", font=reg(19), fill=TXT2)
    d.text((rx + 170, ay + 94), where("话务员"), font=bold(21), fill=RED)

    # 图例（一行 9 个角色）
    ly = GRID_Y + GRID + 34
    d.text((96, ly - 2), "九个角色 ｜ 图标只有四种，靠名字和边框颜色区分个体",
           font=reg(17), fill=TXT2)
    lx, ly2, cw, gap = 96, ly + 30, 165, 5
    for k in range(1, 10):
        icon, name, camp = ROLES[k]
        rr(d, [lx, ly2, lx + cw, ly2 + 56], 10, fill=PANEL2,
           outline=TONE[camp], width=2)
        ic = ICON[k].resize((38, 38), Image.LANCZOS)
        im.paste(ic, (lx + 7, ly2 + 9), ic)
        d.text((lx + 52, ly2 + 8), name, font=bold(15), fill=TXT)
        d.text((lx + 52, ly2 + 30), camp + "方", font=reg(12), fill=TONE[camp])
        lx += cw + gap

    im.save(OUT, quality=95)
    print("saved", OUT)


if __name__ == "__main__":
    main()
