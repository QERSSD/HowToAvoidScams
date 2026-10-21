# -*- coding: utf-8 -*-
"""《识骗迷局》Murdoku 引擎 —— 出题与验题共用一套规则

规则（与数独同构）：
    9 个人各占 9×9 盘面中的一格；
    任意一排 / 一列 / 一个 3×3 区里，有且只有一个人。
于是「9 人占 9 排」意味着排号是一个 0~8 的排列（列、区同理），
任何一条“某人不在这排”都能顺着三重约束往下推——这是烧脑的来源。

本文件只做三件事：
    1. random_solution   —— 随机摆出一个合法现场
    2. candidate_clues   —— 由「真相」反推出一大池中文线索
    3. propagate / count —— 验题：能否纯逻辑推完（不用猜）+ 是否唯一解

线索是结构化的 dict（不是 lambda），好处：
    · 能在 Python 里验证；
    · 能序列化进 JSON 给网页用；
    · 文本和语义不会写歪（同一份 k/a/p 同时驱动 sat 与 apply_rule）。

用法： python tools/murdoku_engine.py   # 自检：随机出一关并验题
"""
import itertools
import random

N = 9
CELLS = [(r, c) for r in range(N) for c in range(N)]
ZONE = {(r, c): (r // 3) * 3 + c // 3 for (r, c) in CELLS}
DIMS = ("row", "col", "zone")


def dimval(cell, dim):
    r, c = cell
    if dim == "row":
        return r
    if dim == "col":
        return c
    return ZONE[cell]


def idx1(x):
    """内部 0 起 → 给玩家看的 1 起"""
    return x + 1


# ---------------------------------------------------------------- 线索语义
def sat(cl, pos):
    """clue 在完整赋值 pos 下是否成立（pos: {name: (r, c)}）"""
    k, a, p = cl["k"], cl["a"], cl["p"]

    def row(n):
        return pos[n][0]

    def col(n):
        return pos[n][1]

    def zone(n):
        return ZONE[pos[n]]

    if k == "row":
        return row(a[0]) == p[0]
    if k == "nrow":
        return row(a[0]) != p[0]
    if k == "col":
        return col(a[0]) == p[0]
    if k == "ncol":
        return col(a[0]) != p[0]
    if k == "zone":
        return zone(a[0]) == p[0]
    if k == "nzone":
        return zone(a[0]) != p[0]
    if k == "samerow":
        return row(a[0]) == row(a[1])
    if k == "samecol":
        return col(a[0]) == col(a[1])
    if k == "samezone":
        return zone(a[0]) == zone(a[1])
    if k == "diffrow":
        return row(a[0]) != row(a[1])
    if k == "diffcol":
        return col(a[0]) != col(a[1])
    if k == "diffzone":
        return zone(a[0]) != zone(a[1])
    if k == "above1":
        return row(a[0]) + 1 == row(a[1])
    if k == "above2":
        return row(a[0]) + 2 == row(a[1])
    if k == "left1":
        return col(a[0]) + 1 == col(a[1])
    if k == "zonediff":
        return zone(a[0]) + p[0] == zone(a[1])
    if k == "zonerow":
        return zone(a[0]) == row(a[1])
    if k == "rowzone":
        return row(a[0]) == zone(a[1])
    if k == "rowsum":
        return row(a[0]) + row(a[1]) == p[0]
    if k == "colsum":
        return col(a[0]) + col(a[1]) == p[0]
    if k == "rowor2":
        return row(a[0]) in p
    if k == "zoneor2":
        return zone(a[0]) in p
    if k == "zonetriple":
        return sorted(zone(n) for n in a) == sorted(p)
    if k == "colbetween":
        x, y, z = col(a[0]), col(a[1]), col(a[2])
        return (x - y) * (x - z) < 0
    raise ValueError("未知线索类型 " + k)


def _narrow(mapping, n, new):
    if new != mapping[n]:
        mapping[n] = new
        return True
    return False


def apply_rule(cl, R, C, Z):
    """把一条线索的约束传播到三个属性集合上（返回是否发生收缩）"""
    k, a, p = cl["k"], cl["a"], cl["p"]
    changed = False

    if k in ("row", "nrow"):
        v = {p[0]}
        new = (R[a[0]] & v) if k == "row" else (R[a[0]] - v)
        changed |= _narrow(R, a[0], new)
    elif k in ("col", "ncol"):
        v = {p[0]}
        new = (C[a[0]] & v) if k == "col" else (C[a[0]] - v)
        changed |= _narrow(C, a[0], new)
    elif k in ("zone", "nzone"):
        v = {p[0]}
        new = (Z[a[0]] & v) if k == "zone" else (Z[a[0]] - v)
        changed |= _narrow(Z, a[0], new)
    elif k == "samerow":
        s = R[a[0]] & R[a[1]]
        changed |= _narrow(R, a[0], s) | _narrow(R, a[1], s)
    elif k == "samecol":
        s = C[a[0]] & C[a[1]]
        changed |= _narrow(C, a[0], s) | _narrow(C, a[1], s)
    elif k == "samezone":
        s = Z[a[0]] & Z[a[1]]
        changed |= _narrow(Z, a[0], s) | _narrow(Z, a[1], s)
    elif k == "diffrow":
        changed |= _diff_prune(R, a[0], a[1]) | _diff_prune(R, a[1], a[0])
    elif k == "diffcol":
        changed |= _diff_prune(C, a[0], a[1]) | _diff_prune(C, a[1], a[0])
    elif k == "diffzone":
        changed |= _diff_prune(Z, a[0], a[1]) | _diff_prune(Z, a[1], a[0])
    elif k == "above1":
        changed |= _shift_prune(R, a[0], a[1], 1)
    elif k == "above2":
        changed |= _shift_prune(R, a[0], a[1], 2)
    elif k == "left1":
        changed |= _shift_prune(C, a[0], a[1], 1)
    elif k == "zonediff":
        d = p[0]
        nb = {z for z in Z[a[0]] if z + d in Z[a[1]]}
        na = {z for z in Z[a[1]] if z - d in Z[a[0]]}
        changed |= _narrow(Z, a[0], nb) | _narrow(Z, a[1], na)
    elif k == "zonerow":
        s = Z[a[0]] & R[a[1]]
        changed |= _narrow(Z, a[0], s) | _narrow(R, a[1], s)
    elif k == "rowzone":
        s = R[a[0]] & Z[a[1]]
        changed |= _narrow(R, a[0], s) | _narrow(Z, a[1], s)
    elif k == "rowsum":
        s = p[0]
        na = {x for x in R[a[0]] if s - x in R[a[1]]}
        nb = {x for x in R[a[1]] if s - x in R[a[0]]}
        changed |= _narrow(R, a[0], na) | _narrow(R, a[1], nb)
    elif k == "colsum":
        s = p[0]
        na = {x for x in C[a[0]] if s - x in C[a[1]]}
        nb = {x for x in C[a[1]] if s - x in C[a[0]]}
        changed |= _narrow(C, a[0], na) | _narrow(C, a[1], nb)
    elif k == "rowor2":
        changed |= _narrow(R, a[0], R[a[0]] & set(p))
    elif k == "zoneor2":
        changed |= _narrow(Z, a[0], Z[a[0]] & set(p))
    elif k == "zonetriple":
        changed |= _triple_prune(Z, a, p)
    elif k == "colbetween":
        changed |= _between_prune(C, a)
    else:
        raise ValueError("未知线索类型 " + k)
    return changed


def _diff_prune(M, x, y):
    """x 的可选值里，凡是 y 只有这一种取法的，都要让出去"""
    if len(M[y]) == 1:
        v = next(iter(M[y]))
        if v in M[x] and len(M[x]) > 1:
            M[x] = M[x] - {v}
            return True
    return False


def _shift_prune(M, x, y, d):
    """My ∋ Mx + d"""
    nx = {v for v in M[x] if v + d in M[y]}
    ny = {v for v in M[y] if v - d in M[x]}
    return _narrow(M, x, nx) | _narrow(M, y, ny)


def _triple_prune(Z, trio, p):
    changed = False
    S = set(p)
    for n in trio:
        changed |= _narrow(Z, n, Z[n] & S)
    for v in S:
        can = [n for n in trio if v in Z[n]]
        if not can:
            for n in trio:
                Z[n] = set()
            return True
        if len(can) == 1:
            changed |= _narrow(Z, can[0], {v})
    for i in range(3):
        rest = [trio[j] for j in range(3) if j != i]
        u = Z[rest[0]] | Z[rest[1]]
        if len(u) < 2:
            Z[trio[i]] = set()
            changed = True
        elif len(u) == 2:
            changed |= _narrow(Z, trio[i], Z[trio[i]] - u)
    return changed


def _between_prune(C, trio):
    a, b, c = trio
    na = {x for x in C[a] if any((x - y) * (x - z) < 0 for y in C[b] for z in C[c])}
    nb = {y for y in C[b] if any((x - y) * (x - z) < 0 for x in C[a] for z in C[c])}
    nc = {z for z in C[c] if any((x - y) * (x - z) < 0 for x in C[a] for y in C[b])}
    return _narrow(C, a, na) | _narrow(C, b, nb) | _narrow(C, c, nc)


# ---------------------------------------------------------------- 约束传播
def propagate(names, clues, given, max_iter=400, max_hall=4):
    """只用逻辑不猜：反复收缩候选集，看能否把 9 个人全部定死。

    返回 (status, cells, level)
      status: 'solved' | 'stuck' | 'contra'
      level : 用上的最高推理档位（1=单值/唯一值，2~4=子集排除的规模）
      max_hall: 允许用到多大规模的子集排除——调它就能给题目定难度档
    """
    cells = {n: set(CELLS) for n in names}
    for n, p in given.items():
        cells[n] = {tuple(p)}
    used_level = 1

    def attrs():
        R = {n: {cell[0] for cell in cells[n]} for n in names}
        C = {n: {cell[1] for cell in cells[n]} for n in names}
        Z = {n: {ZONE[cell] for cell in cells[n]} for n in names}
        return R, C, Z

    for _ in range(max_iter):
        changed = False
        # ---------- 1) 已定死的人，把同行同列同区从别人身上划掉 ----------
        for n in names:
            if len(cells[n]) == 1:
                r, c = next(iter(cells[n]))
                z = ZONE[(r, c)]
                for m in names:
                    if m == n:
                        continue
                    before = len(cells[m])
                    cells[m] = {x for x in cells[m]
                                if x[0] != r and x[1] != c and ZONE[x] != z}
                    if len(cells[m]) != before:
                        changed = True
        if any(not cells[n] for n in names):
            return "contra", cells, used_level

        # ---------- 2) 排/列/区：每格恰好一个人 ⇒ 9 个值是个排列 ----------
        for dim in DIMS:
            A = {n: {dimval(x, dim) for x in cells[n]} for n in names}
            for v in range(N):
                can = [n for n in names if v in A[n]]
                if not can:
                    return "contra", cells, used_level
                if len(can) == 1 and len(A[can[0]]) > 1:
                    A[can[0]] = {v}
                    changed = True
            # 子集排除（Hall）：k 个人只占得住 k 个排 → 这些排不许给别人
            for k in range(2, max_hall + 1):
                for combo in itertools.combinations(names, k):
                    u = set()
                    for n in combo:
                        u |= A[n]
                    if len(u) < k:
                        return "contra", cells, used_level
                    if len(u) == k:
                        used_level = max(used_level, k)
                        rest = [n for n in names if n not in combo]
                        for n in rest:
                            new = A[n] - u
                            if new != A[n]:
                                A[n] = new
                                changed = True
            for n in names:
                before = len(cells[n])
                cells[n] = {x for x in cells[n] if dimval(x, dim) in A[n]}
                if len(cells[n]) != before:
                    changed = True
        if any(not cells[n] for n in names):
            return "contra", cells, used_level

        # ---------- 3) 线索本身的约束 ----------
        R, C, Z = attrs()
        for cl in clues:
            if apply_rule(cl, R, C, Z):
                changed = True
        for n in names:
            before = len(cells[n])
            cells[n] = {x for x in cells[n]
                        if x[0] in R[n] and x[1] in C[n] and ZONE[x] in Z[n]}
            if len(cells[n]) != before:
                changed = True
        if any(not cells[n] for n in names):
            return "contra", cells, used_level

        if all(len(cells[n]) == 1 for n in names):
            return "solved", cells, used_level
        if not changed:
            return "stuck", cells, used_level

    return "stuck", cells, used_level


# ---------------------------------------------------------------- 穷举验解
def count_solutions(names, clues, given, limit=2):
    """回溯数解；拿到 limit 个就收手（只需知道是不是唯一）"""
    sols = []
    order = [n for n in names if n not in given]
    pos = {}
    used = {"row": [False] * N, "col": [False] * N, "zone": [False] * N}
    for n, cell in given.items():
        pos[n] = tuple(cell)
        used["row"][cell[0]] = used["col"][cell[1]] = used["zone"][ZONE[tuple(cell)]] = True

    def ok_partial():
        for cl in clues:
            if set(cl["a"]) <= set(pos):
                if not sat(cl, pos):
                    return False
        return True

    def bt(i):
        if len(sols) >= limit:
            return
        if i == len(order):
            sols.append(dict(pos))
            return
        n = order[i]
        for cell in CELLS:
            if used["row"][cell[0]] or used["col"][cell[1]] or used["zone"][ZONE[cell]]:
                continue
            pos[n] = cell
            used["row"][cell[0]] = used["col"][cell[1]] = used["zone"][ZONE[cell]] = True
            if ok_partial():
                bt(i + 1)
            used["row"][cell[0]] = used["col"][cell[1]] = used["zone"][ZONE[cell]] = False
        pos.pop(n, None)

    bt(0)
    return sols


# ---------------------------------------------------------------- 随机现场
def random_solution(names, rng):
    order = list(names)
    rng.shuffle(order)
    pos = {}
    ur = [False] * N
    uc = [False] * N
    uz = [False] * N

    def bt(i):
        if i == len(order):
            return True
        n = order[i]
        cand = list(CELLS)
        rng.shuffle(cand)
        for cell in cand:
            if ur[cell[0]] or uc[cell[1]] or uz[ZONE[cell]]:
                continue
            pos[n] = cell
            ur[cell[0]] = uc[cell[1]] = uz[ZONE[cell]] = True
            if bt(i + 1):
                return True
            ur[cell[0]] = uc[cell[1]] = uz[ZONE[cell]] = False
        pos.pop(n, None)
        return False

    bt(0)
    return pos


# ---------------------------------------------------------------- 线索文本
def _zone_text(z, zones):
    return "第 %d 区 %s" % (idx1(z), zones[z])


def _row_text(r, rows):
    return "第 %d 排 %s" % (idx1(r), rows[r])


def _col_text(c):
    if c == 0:
        return "最左边一列"
    if c == N - 1:
        return "最右边一列"
    if c == 4:
        return "正中间那一列"
    return "第 %d 列" % idx1(c)


def clue_text(cl, zones, rows, rng=None):
    """线索文案。rng 给定时会随机挑措辞变体（同一道题的文本就此固定）"""
    k, a, p = cl["k"], cl["a"], cl["p"]
    rn = _row_text(p[0], rows) if k in ("row", "nrow", "rowor2") else None
    pick = (rng or _NULL_RNG).random() if rng else 0

    if k == "row":
        return rng.choice([
            "%s 站在%s。" % (a[0], rn),
            "监控拍到 %s 就站在%s。" % (a[0], rn),
            "%s 从头到尾没离开过%s。" % (a[0], rn),
        ]) if rng else "%s 站在%s。" % (a[0], rn)
    if k == "nrow":
        return rng.choice([
            "%s 不在%s。" % (a[0], rn),
            "可以肯定 %s 当时不在%s。" % (a[0], rn),
        ]) if rng else "%s 不在%s。" % (a[0], rn)
    if k == "col":
        return rng.choice([
            "%s 站在%s。" % (a[0], _col_text(p[0])),
            "%s 的位置在%s。" % (a[0], _col_text(p[0])),
        ]) if rng else "%s 站在%s。" % (a[0], _col_text(p[0]))
    if k == "ncol":
        return "%s 不在%s。" % (a[0], _col_text(p[0]))
    if k == "zone":
        return rng.choice([
            "%s 在%s。" % (a[0], _zone_text(p[0], zones)),
            "%s 那会儿人在%s。" % (a[0], _zone_text(p[0], zones)),
            "有人认出 %s 出现在%s。" % (a[0], _zone_text(p[0], zones)),
        ]) if rng else "%s 在%s。" % (a[0], _zone_text(p[0], zones))
    if k == "nzone":
        return rng.choice([
            "%s 不在%s。" % (a[0], _zone_text(p[0], zones)),
            "%s 全程没进过%s。" % (a[0], _zone_text(p[0], zones)),
        ]) if rng else "%s 不在%s。" % (a[0], _zone_text(p[0], zones))
    if k == "samerow":
        return "%s 和 %s 在同一排。" % (a[0], a[1])
    if k == "samecol":
        return "%s 和 %s 在同一列。" % (a[0], a[1])
    if k == "samezone":
        return "%s 和 %s 在同一个区。" % (a[0], a[1])
    if k == "diffrow":
        return "%s 和 %s 不在同一排。" % (a[0], a[1])
    if k == "diffcol":
        return "%s 和 %s 不在同一列。" % (a[0], a[1])
    if k == "diffzone":
        return "%s 和 %s 不在同一个区。" % (a[0], a[1])
    if k == "above1":
        return "%s 紧挨着 %s 的北边一排。" % (a[0], a[1])
    if k == "above2":
        return "%s 在 %s 北边，中间还隔着整整一排。" % (a[0], a[1])
    if k == "left1":
        return "%s 就站在 %s 左手边一格。" % (a[0], a[1])
    if k == "zonediff":
        d = p[0]
        return "%s 的区号比 %s 大 %d。" % (a[0], a[1], d) if d > 0 else \
            "%s 的区号比 %s 小 %d。" % (a[0], a[1], -d)
    if k == "zonerow":
        return "%s 的区号，正好等于 %s 的排号。" % (a[0], a[1])
    if k == "rowzone":
        return "%s 的排号，正好等于 %s 的区号。" % (a[0], a[1])
    if k == "rowsum":
        return "%s 和 %s 的排号加起来是 %d。" % (a[0], a[1], p[0])
    if k == "colsum":
        return "%s 和 %s 的列号加起来是 %d。" % (a[0], a[1], p[0])
    if k == "rowor2":
        return "%s 只在 %s 或 %s 这两排里。" % (a[0], _row_text(p[0], rows), _row_text(p[1], rows))
    if k == "zoneor2":
        return "%s 只在 %s 或 %s 这两个区里。" % (a[0], _zone_text(p[0], zones), _zone_text(p[1], zones))
    if k == "zonetriple":
        return "%s、%s、%s 三个人，分别占了 %s、%s、%s，一人守一块。" % (
            a[0], a[1], a[2], _zone_text(p[0], zones), _zone_text(p[1], zones), _zone_text(p[2], zones))
    if k == "colbetween":
        return "%s 站的列，正好在 %s 和 %s 之间。" % (a[0], a[1], a[2])
    raise ValueError("未知线索类型 " + k)


_NULL_RNG = random.Random(0)

ORDER = ["zone", "row", "col", "above1", "left1", "zonediff", "zonerow", "rowzone",
         "above2", "rowsum", "colsum", "rowor2", "zoneor2", "colbetween",
         "nzone", "nrow", "ncol"]


# ---------------------------------------------------------------- 线索池
def candidate_clues(names, sol, zones, rows, rng, max_per_pair=4):
    """由真相反推一堆「为真」的线索；假线索不进池（不说谎）"""
    pool = []

    def row(n):
        return sol[n][0]

    def col(n):
        return sol[n][1]

    def zone(n):
        return ZONE[sol[n]]

    def add(k, a, p):
        cl = {"k": k, "a": list(a), "p": list(p)}
        assert sat(cl, sol), (k, a, p)
        cl["t"] = clue_text(cl, zones, rows, rng)
        pool.append(cl)

    for n in names:
        add("zone", [n], [zone(n)])
        add("row", [n], [row(n)])
        add("col", [n], [col(n)])
        for dim, real in (("nzone", zone(n)), ("nrow", row(n)), ("ncol", col(n))):
            others = [v for v in range(N) if v != real]
            rng.shuffle(others)
            add(dim, [n], [others[0]])
    # 两两一组：只挑真正为真的那几种说法
    # 注意：「不同排 / 不同列 / 不同区」在九人各占一排的规则下恒真，没有信息量，不入池
    for x, y in itertools.combinations(names, 2):
        cand = []
        if row(x) + 1 == row(y):
            cand.append(("above1", [x, y], []))
        elif row(x) + 2 == row(y):
            cand.append(("above2", [x, y], []))
        elif row(y) + 1 == row(x):
            cand.append(("above1", [y, x], []))
        elif row(y) + 2 == row(x):
            cand.append(("above2", [y, x], []))
        if col(x) + 1 == col(y):
            cand.append(("left1", [x, y], []))
        elif col(y) + 1 == col(x):
            cand.append(("left1", [y, x], []))
        cand.append(("zonediff", [x, y], [zone(y) - zone(x)]))
        if zone(x) == row(y):
            cand.append(("zonerow", [x, y], []))
        if row(x) == zone(y):
            cand.append(("rowzone", [x, y], []))
        cand.append(("rowsum", [x, y], [row(x) + row(y)]))
        cand.append(("colsum", [x, y], [col(x) + col(y)]))
        # 二选一：把真值混进一个假值里
        fake = rng.choice([v for v in range(N) if v != row(x)])
        cand.append(("rowor2", [x], sorted([row(x), fake])))
        fake = rng.choice([v for v in range(N) if v != zone(x)])
        cand.append(("zoneor2", [x], sorted([zone(x), fake])))
        rng.shuffle(cand)
        for k, args, p in cand[:max_per_pair]:
            add(k, args, p)
    # 列号夹在两人之间（三人一组，随机采样，别把池撑爆）
    trips = list(itertools.permutations(names, 3))
    rng.shuffle(trips)
    added = 0
    for trio in trips:
        if added >= 24:
            break
        x, y, z = trio
        if (col(x) - col(y)) * (col(x) - col(z)) < 0:
            add("colbetween", list(trio), [])
            added += 1
    # 去重
    seen = set()
    out = []
    for cl in pool:
        sig = (cl["k"], tuple(cl["a"]), tuple(cl["p"]))
        if sig in seen:
            continue
        seen.add(sig)
        out.append(cl)
    return out


# ---------------------------------------------------------------- 出题
TIER = {
    "zone": 1, "row": 1, "col": 1,
    "above1": 2, "left1": 2, "zonediff": 2, "zonerow": 2, "rowzone": 2,
    "above2": 3, "rowsum": 3, "colsum": 3, "rowor2": 3, "zoneor2": 3,
    "colbetween": 4, "nzone": 4, "nrow": 4, "ncol": 4,
}


def make_puzzle(names, zones, rows, seed, n_given=2, max_clues=13,
                max_direct=4, min_clues=6, min_level=1, victim_zone=None,
                scammer_zone=None, victim=None, scammer=None, tries=200):
    """出题：随机现场 → 挑线索直到「纯逻辑能推完」→ 再删到极小 → 验唯一解

    max_direct 卡住「直接报坐标」的条数，逼出题面里的关系型线索——
    全是直给的题推得太顺，没有 Murdoku 的味道。
    """
    rng = random.Random(seed)
    direct = {"zone", "row", "col"}
    for _ in range(tries):
        sol = random_solution(names, rng)
        # 受害者、主骗要落在这一关说得通的区块里（比如角色的 argues 位置要像）
        if victim and victim_zone and ZONE[sol[victim]] not in victim_zone:
            continue
        if scammer and scammer_zone and ZONE[sol[scammer]] not in scammer_zone:
            continue
        given_names = rng.sample(names, n_given)
        given = {n: tuple(sol[n]) for n in given_names}
        pool = candidate_clues(names, sol, zones, rows, rng)
        pool.sort(key=lambda cl: TIER.get(cl["k"], 5) + rng.random() * 1.6)
        chosen = []
        status, level = "stuck", 1
        for cl in pool:
            if cl["k"] in direct and sum(1 for c in chosen if c["k"] in direct) >= max_direct:
                continue
            chosen.append(cl)
            status, cells, level = propagate(names, chosen, given)
            if status == "solved":
                break
            if status == "contra":
                chosen.pop()
            if len(chosen) >= 26:
                break
        if status != "solved":
            continue
        # 极小化：能删就删，删完还要能纯逻辑推完
        rng.shuffle(chosen)
        for cl in list(chosen):
            trial = [x for x in chosen if x is not cl]
            st, _, _ = propagate(names, trial, given)
            if st == "solved":
                chosen = trial
        if not (min_clues <= len(chosen) <= max_clues):
            continue
        sols = count_solutions(names, chosen, given, limit=2)
        if len(sols) != 1:
            continue
        st, cells, _ = propagate(names, chosen, given)
        # 难度档：允许用到多大规模的子集排除才能推完
        level = 4
        for h in (1, 2, 3):
            if propagate(names, chosen, given, max_hall=h)[0] == "solved":
                level = h
                break
        # 题面排序：先给坐标锚点，再上关系，最后才是否定型
        if level < min_level:
            continue
        chosen.sort(key=lambda cl: ORDER.index(cl["k"]) if cl["k"] in ORDER else 99)
        return {
            "sol": {n: list(sol[n]) for n in names},
            "given": {n: list(sol[n]) for n in given_names},
            "clues": chosen,
            "level": level,
            "clue_count": len(chosen),
            "_verify": {"solutions": len(sols), "propagate": st},
        }
    return None


def make_hints(names, sol, zones, rows, clues, victim, main_scammer):
    """每关两条提示：先受害者方位，再主骗坐标"""
    has_zone = any(c["k"] == "zone" and c["a"][0] == victim for c in clues)
    out = []
    if not has_zone:
        out.append("受害者躲在" + _zone_text(ZONE[sol[victim]], zones) + "，"
                   "顺着这一区的行列往下推。")
    else:
        out.append("受害者在" + _row_text(sol[victim][0], rows) + "，"
                   "拿它去撞别人的排号。")
    r, c = sol[main_scammer]
    out.append("主骗在第 %d 排、第 %d 列。他一定位，剩下的人会连锁归位。"
               % (idx1(r), idx1(c)))
    return out


if __name__ == "__main__":
    names = ["话务员", "组长", "取现手", "小林", "民警", "快递员", "邻居", "店主", "保安"]
    zones = ["驿站前台", "快递货架", "门口快递柜", "小区门岗", "便利店",
             "3 号楼电梯", "电动车棚", "分拣区", "物业办公室"]
    rows = ["最南一排", "收银台前", "货架长廊", "靠窗走廊", "中庭",
            "花坛边", "停车位", "门口台阶", "最北一排"]
    for s in range(1, 4):
        pz = make_puzzle(names, zones, rows, s)
        if not pz:
            print(s, "出题失败")
            continue
        print("seed", s, "线索", pz["clue_count"], "条  推理档位", pz["level"],
              "唯一解", pz["_verify"])
        for cl in pz["clues"]:
            print("   ·", cl["t"])
        print("   提示：", make_hints(names, {n: tuple(v) for n, v in pz["sol"].items()},
                                    zones, rows, pz["clues"], "小林", "话务员"))
