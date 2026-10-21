# -*- coding: utf-8 -*-
"""
Murdoku 可解性校验器（原型）。

规则：9 个角色各占 1 格，任意一行 / 一列 / 一个 3×3 区里都不能有两个人。
给定若干线索后，穷举所有合法摆法，断言「有且仅有 1 个解」。

这是需求文档里说的「生命线」——能出题，必须先能验题。

用法： env/default/Scripts/python.exe tools/murdoku_check.py
"""
import itertools
import sys

NAMES = ["话务员", "组长", "取现手", "小林", "民警", "快递员", "邻居", "店主", "保安"]

# 设计解（样关「退款来电」）
SOL = {
    "话务员": (0, 0), "组长": (1, 3), "取现手": (2, 6),
    "小林": (3, 1), "民警": (4, 4), "快递员": (5, 7),
    "邻居": (6, 2), "店主": (7, 5), "保安": (8, 8),
}
# 开局直接摆好的人
GIVEN = {"民警": (4, 4), "保安": (8, 8)}


def row(p, n):
    return p[n][0]


def col(p, n):
    return p[n][1]


def zone(p, n):
    r, c = p[n]
    return (r // 3) * 3 + c // 3


# 线索：(给玩家看的文案, 判定函数)
CLUES = [
    ("三个骗子分别在 1、2、3 区，一人守一块",
     lambda p: sorted(zone(p, n) for n in ("话务员", "组长", "取现手")) == [0, 1, 2]),
    ("话务员贴着最西边那一列，从驿站前台打出去",
     lambda p: col(p, "话务员") == 0),
    ("取现手跑的区号最大，在门口快递柜那一片",
     lambda p: zone(p, "取现手") == 2),
    ("组长在第 2 行，管着一整排货架",
     lambda p: row(p, "组长") == 1),
    ("受害者所在的区号，正好比民警的行号小一",
     lambda p: zone(p, "小林") == row(p, "民警") - 1),
    ("小林的楼层比民警低一层",
     lambda p: row(p, "小林") == row(p, "民警") - 1),
    ("快递员站在倒数第二列，靠着东侧外墙",
     lambda p: col(p, "快递员") == 7),
    ("邻居在电动车棚（第 7 区），店主在分拣区（第 8 区）",
     lambda p: zone(p, "邻居") == 6 and zone(p, "店主") == 7),
    ("邻居就在店主正上方那层，两个人上下没说上话",
     lambda p: row(p, "邻居") == row(p, "店主") - 1),
    ("小林靠在门岗第二根柱子边上",
     lambda p: col(p, "小林") == 1),
    ("组长站在货架最靠里的那根立柱下",
     lambda p: col(p, "组长") == 3),
    ("话务员在最北边一排，紧贴着驿站门口",
     lambda p: row(p, "话务员") == 0),
]


def solve(limit=50):
    """按线索剪枝回溯，返回所有完整解"""
    sols = []
    pos = {}
    used_row = [False] * 9
    used_col = [False] * 9
    used_zone = [False] * 9
    # 已知的先放；待排的人里要排除它们，否则会重复分配
    order = [n for n in NAMES if n not in GIVEN]

    for n, (r, c) in GIVEN.items():
        pos[n] = (r, c)
        used_row[r] = used_col[c] = used_zone[(r // 3) * 3 + c // 3] = True

    def check_partial():
        """线索涉及的角色都已赋值时才判定，未赋值的跳过"""
        for _, fn in CLUES:
            try:
                ok = fn(pos)
            except KeyError:
                continue
            if ok is False:
                return False
        return True

    def bt(i):
        if len(sols) >= limit:
            return
        if i == len(order):
            if all(fn(pos) for _, fn in CLUES):
                sols.append(dict(pos))
            return
        n = order[i]
        for r in range(9):
            for c in range(9):
                z = (r // 3) * 3 + c // 3
                if used_row[r] or used_col[c] or used_zone[z]:
                    continue
                pos[n] = (r, c)
                used_row[r] = used_col[c] = used_zone[z] = True
                if check_partial():
                    bt(i + 1)
                used_row[r] = used_col[c] = used_zone[z] = False
        pos.pop(n, None)

    bt(0)
    return sols


def main():
    print("== 设计解自检 ==")
    p = dict(SOL)
    bad = False
    for i, (txt, fn) in enumerate(CLUES, 1):
        ok = fn(p)
        print("  线索 %d %s  %s" % (i, "通过" if ok else "不成立", txt[:22]))
        bad |= not ok
    # 行列区唯一
    for label, getter in (("行", row), ("列", col), ("区", zone)):
        vals = [getter(p, n) for n in NAMES]
        dup = len(vals) != len(set(vals))
        print("  %s唯一：%s" % (label, "否 ← 有问题" if dup else "是"))
        bad |= dup
    if bad:
        print("!! 设计解与线索不一致，先修数据")
        return 1

    print("\n== 穷举求解 ==")
    sols = solve(limit=5)
    print("  解的个数：", len(sols))
    if len(sols) == 1:
        print("  ✓ 唯一解，可以入库")
        for n in NAMES:
            r, c = sols[0][n]
            print("    %-5s 第 %d 行 第 %d 列（第 %d 区）"
                  % (n, r + 1, c + 1, (r // 3) * 3 + c // 3 + 1))
        return 0
    print("  ✗ 不唯一，需要加线索或改线索")
    for s in sols[:3]:
        print("    例：", {k: (v[0] + 1, v[1] + 1) for k, v in s.items()})
    return 1


if __name__ == "__main__":
    sys.exit(main())
