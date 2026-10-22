# -*- coding: utf-8 -*-
"""把 12 张案发现场插画压成网格背景雪碧图（288x288 JPEG data URI）。

每关一张微俯视场景图，3x3 切开后正好对应九宫格区块：
  - 去掉右下角平台水印（用正上方同尺寸像素延拓覆盖）
  - 1024 -> 288（LANCZOS），棋盘格区块即 96px，与格子尺寸匹配
  - JPEG q62，单张约 15~25KB
输出 game/murdoku-bgs.json（入仓库，保证别人拉下来也能构建）。
"""
import base64
import glob
import io
import json
import os
import sys

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "game-adaptations", "assets", "bg")
OUT = os.path.join(ROOT, "game", "murdoku-bgs.json")
OUT_LOCAL = os.path.join(ROOT, "game-adaptations", "识骗迷局", "art", "bgs.json")

# 生成顺序 = LEVELS 顺序（murdoku_content.py）
FILES = [
    ("ch01-01", "Bird_s_eye_view_top_down_illus_2026-10-21T23-48-29.png"),
    ("ch01-02", "Bird_s_eye_view_top_down_illus_2026-10-21T23-49-19.png"),
    ("ch01-03", "Bird_s_eye_view_top_down_illus_2026-10-21T23-49-13.png"),
    ("ch01-04", "Bird_s_eye_view_top_down_illus_2026-10-21T23-49-17.png"),
    ("ch01-05", "Bird_s_eye_view_top_down_illus_2026-10-21T23-49-16.png"),
    ("ch01-06", "Bird_s_eye_view_top_down_illus_2026-10-21T23-49-49.png"),
    ("ch02-01", "Bird_s_eye_view_top_down_illus_2026-10-21T23-49-54.png"),
    ("ch02-02", "Bird_s_eye_view_top_down_illus_2026-10-21T23-49-50.png"),
    ("ch02-03", "Bird_s_eye_view_top_down_illus_2026-10-21T23-50-57.png"),
    ("ch02-04", "Bird_s_eye_view_top_down_illus_2026-10-21T23-50-32.png"),
    ("ch02-05", "Bird_s_eye_view_top_down_illus_2026-10-21T23-50-29.png"),
    ("ch02-06", "Bird_s_eye_view_top_down_illus_2026-10-21T23-50-30.png"),
]

SIZE = 288          # 3x3 区块雪碧图总边长
Q = 62              # JPEG 质量
# 水印框（按 1024 边长的比例，缩放时同比例换算）
WM = (0.893, 0.962, 1.0, 1.0)


def strip_watermark(im):
    w, h = im.size
    box = tuple(int(v * (w if i % 2 == 0 else h)) for i, v in enumerate(WM))
    x0, y0, x1, y1 = box
    dy = y1 - y0
    if y0 - dy < 0:
        return im
    patch = im.crop((x0, y0 - dy, x1, y0))
    im.paste(patch, (x0, y0))
    return im


def main():
    out = {}
    for lid, fn in FILES:
        path = os.path.join(SRC, fn)
        if not os.path.exists(path):
            raise SystemExit("缺图：%s（关卡 %s）" % (fn, lid))
        im = Image.open(path).convert("RGB")
        if im.size != (1024, 1024):
            im = im.resize((1024, 1024), Image.LANCZOS)
        im = strip_watermark(im)
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=Q, optimize=True, progressive=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        out[lid] = uri
        print("%s  %-58s %6.1f KB" % (lid, fn[:58], len(uri) / 1024))
    total = sum(len(v) for v in out.values()) / 1024
    print("共 %d 张，合计 %.0f KB" % (len(out), total))
    for path in (OUT, OUT_LOCAL):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print("输出：%s（入仓库，构建用）" % OUT)
    print("副本：%s（本地工作区）" % OUT_LOCAL)


if __name__ == "__main__":
    main()
