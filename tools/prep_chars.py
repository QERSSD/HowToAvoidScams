# -*- coding: utf-8 -*-
"""
角色棋子图后处理：去白底 → 按标定裁圆 → 统一 512 画布。

AI 生图会带白底和右下角水印，圆底板大小也各不相同。这里按每张图实测的
圆心与直径裁出正圆，统一成「圆直径 480、画布 512、透明底」的棋子。

新增角色图时：若构图与现有不同，用 --probe 打印几何数据后补一行 CALIB。

用法：
    env/default/Scripts/python.exe tools/prep_chars.py
    env/default/Scripts/python.exe tools/prep_chars.py --probe
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "game-adaptations", "assets", "characters")
CANVAS = 512
DIAM = 480

# 输出名 → (源文件, 圆心x, 圆心y, 圆直径)
CALIB = {
    "pianzi.png": (
        "平面矢量游戏棋子头像_半身像_正面朝向_居中构图_人物_一名_2026-10-21T09-44-08.png",
        511, 523, 858),
    "shouhaizhe.png": (
        "平面矢量游戏棋子头像_半身像_正面朝向_居中构图_人物_一名_2026-10-21T09-43-59.png",
        556, 556, 902),
    "jingcha.png": (
        "平面矢量游戏棋子头像_半身像_正面朝向_居中构图_人物_一名_2026-10-21T09-44-05.png",
        512, 512, 1024),
    "luren.png": (
        "_luren2/平面矢量卡通图标_Q版半身像_五官极简_点状眼睛_简单嘴巴__2026-10-21T09-45-56.png",
        512, 512, 1024),
}


def flood_white(im, thresh=42):
    """从四角泛洪，把连通的白色变透明（人物身上的浅色不受影响）"""
    im = im.convert("RGBA")
    w, h = im.size
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        ImageDraw.floodfill(im, seed, (255, 255, 255, 0), thresh=thresh)
    a = np.array(im)
    near_white = a[..., :3].min(axis=2) > 246
    a[..., 3] = np.where(near_white, 0, a[..., 3])
    return Image.fromarray(a, "RGBA")


def circle_alpha(im, aa=4):
    w, h = im.size
    m = Image.new("L", (w * aa, h * aa), 0)
    d = ImageDraw.Draw(m)
    r = w * aa / 2
    d.ellipse([w * aa / 2 - r, h * aa / 2 - r,
               w * aa / 2 + r, h * aa / 2 + r], fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    a = np.array(im)
    a[..., 3] = (a[..., 3].astype(np.float32) * np.array(m) / 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def build(src_path, cx, cy, d):
    im = flood_white(Image.open(src_path))
    r = d / 2
    im = im.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))
    im = circle_alpha(im)
    im = im.resize((DIAM, DIAM), Image.LANCZOS)
    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    off = (CANVAS - DIAM) // 2
    out.paste(im, (off, off), im)
    return out


def probe():
    for name, (src, *_rest) in CALIB.items():
        p = os.path.join(SRC, src)
        if not os.path.exists(p):
            continue
        im = flood_white(Image.open(p))
        a = np.array(im)[..., 3] > 128
        ys, xs = np.where(a)
        rows = a.sum(axis=1)
        widest = int(np.argmax(rows))
        print("%-16s bbox x[%d,%d] y[%d,%d]  最宽行 y=%d w=%d"
              % (name, xs.min(), xs.max(), ys.min(), ys.max(),
                 widest, int(rows[widest])))


def main():
    for name, (src, cx, cy, d) in CALIB.items():
        p = os.path.join(SRC, src)
        if not os.path.exists(p):
            print("  跳过（缺失）:", name)
            continue
        build(p, cx, cy, d).save(os.path.join(SRC, name))
        print("  ✓", name, "圆 %d / 画布 %d" % (DIAM, CANVAS))


if __name__ == "__main__":
    probe() if "--probe" in sys.argv else main()
