# -*- coding: utf-8 -*-
"""把《人间防骗指南》原始 markdown 拆成结构化文章 JSON。

原始素材是一份口播稿合集：一篇一个骗局，标题自带 emoji 和【栏目名】，
正文混排「套路拆解 / 致命风险 / 醒脑总结」等小标题，结尾一行 #标签。

第一步按标签行分篇；漏掉的（正文里没写标签行）再用标题行补一刀；
最后给每篇打上：骗局类型、会损失什么、专盯谁、风险等级，
并把正文拆成带类型（步骤 / 陷阱 / 防范 / 法律 / 收尾）的行，交给渲染层。
"""
import collections
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRCS = [
    # 唯一素材文件：原始口播稿 + 两轮增补（民生/反诈工具/2026最新骗局）已全部合并进来，
    # 之后更新只改这一个文件，不再新增补增文件。
    os.path.join(ROOT, "人间防骗指南.md"),
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles.json")

TAG_RE = re.compile(r"^#[^\s#][^\n]*$")

# 标题里几乎必然出现的强词（弱一点的"诈骗/犯罪"之类不加，会把正文里的警示句也捞进来）
TITLE_WORDS = re.compile(r"揭秘|起底|拆解|扒开|撕开|扒透|曝光|警惕|小心|当心|陷阱|骗局|套路|黑幕|避坑|注意")
# 文章标题常见的开头符号
TITLE_EMOJI = re.compile(
    "^[\U0001F6A8\U0001F4E2\U0001F4FA\U0001F4BC\U0001F393\U0001F4E6"
    "\U0001F4F1\U0001F4B8\U0001F4B0\U0001F3B2\U0001F37E\U0001F9FB"
    "\U0001FA78\U0001F576\U0001F4BE\U0001F41F\U0001F4B3\U0001F48A"
    "\U0001F494\U0001F3AC\U0001F465\U0001F9D8\U0001F4DA\U0001F381"
    "\U0001F3AE\u26FD\u20E3\U0001F575\U0001F30D\U0001F6AC\U0001F40D\U0001F631\U0001F4A5]"
)
SOC_EMOJI = re.compile(r"^[^\w\u4e00-\u9fff]")

STEP_RE = re.compile(r"^(\d\uFE0F?\u20E3|[①-⑳]|[•·])\s*(.*)$")

# ---------------- 骗局类型：权重词库，命中即累加，取最高的一类 ----------------
CATS = [
    ("网贷 · 套路贷", "🏦", [
        ("网贷", 3), ("套路贷", 4), ("砍头息", 4), ("高利贷", 4), ("借款", 2), ("贷款", 3),
        ("征信", 3), ("催收", 3), ("反催收", 4), ("停息挂账", 4), ("背债", 4), ("ab贷", 4),
        ("AB贷", 4), ("714", 3), ("放款", 2), ("解冻保证金", 4), ("额度", 1), ("花户", 3),
        ("债务优化", 3), ("车抵贷", 4), ("裸贷", 4), ("骗贷", 4), ("借条", 2), ("借贷", 3),
    ]),
    ("兼职 · 刷单", "🧾", [
        ("兼职", 4), ("刷单", 5), ("佣金", 2), ("返现", 2), ("返利", 3), ("日结", 3),
        ("日入", 2), ("打字员", 4), ("任务单", 4), ("外包", 1), ("零门槛", 2), ("手工活", 4),
        ("寄拍", 4), ("充场", 4), ("地推", 3), ("拉新", 3), ("打码", 3), ("扫码关注", 3),
        ("试玩", 3), ("悬赏", 2), ("副业", 2), ("接单", 2), ("拍照", 2), ("拍照赚钱", 4),
    ]),
    ("投资 · 虚拟币", "📈", [
        ("投资", 3), ("理财", 3), ("基金", 2), ("荐股", 4), ("内幕消息", 4), ("USDT", 4),
        ("虚拟货币", 4), ("加密货币", 4), ("泰达", 3), ("炒币", 4), ("区块链", 2), ("期货", 3),
        ("黄金", 2), ("保本保息", 4), ("稳赚", 4), ("量化", 2), ("资金盘", 4), ("代币", 3),
        ("投资平台", 4), ("提现", 1), ("app投资", 3), ("买U", 4), ("卖U", 4),
    ]),
    ("网赌 · 博彩", "🎰", [
        ("网赌", 5), ("赌博", 4), ("博彩", 4), ("百家乐", 5), ("彩票", 4), ("六合彩", 5),
        ("下注", 4), ("赌场", 3), ("PG电子", 5), ("PG", 2), ("菠菜", 5), ("庄家", 3),
        ("开奖", 3), ("投注", 4), ("赌石", 4), ("抢红包", 3), ("拼包", 4), ("游戏厅", 2),
        ("押注", 4), ("赌局", 3), ("电诈园区", 2),
    ]),
    ("情感 · 色情陷阱", "💔", [
        ("网恋", 4), ("杀猪盘", 4), ("裸聊", 5), ("招嫖", 5), ("约炮", 5), ("婚恋", 4),
        ("包养", 4), ("仙人跳", 5), ("饭托", 4), ("酒托", 4), ("女友", 2), ("色情", 4),
        ("异性好友", 3), ("原味", 4), ("征婚", 3), ("陪伴", 2),
        ("情感线索", 4), ("陪聊", 4), ("色流", 4), ("擦边", 3), ("交友粉", 3), ("偷拍", 3),
    ]),
    ("AI · 盗号技术", "🤖", [
        ("AI换脸", 5), ("AI", 3), ("人脸识别", 5), ("语音克隆", 5), ("木马", 4), ("钓鱼", 4),
        ("盗号", 4), ("盗刷", 4), ("伪基站", 4), ("猫池", 4), ("改号", 3), ("撞库", 3),
        ("无感盗", 5), ("恶意授权", 5), ("钓鱼网站", 5), ("短信嗅探", 4),
        ("深度伪造", 5), ("换脸", 5), ("设备指纹", 3), ("摄像头", 3),
    ]),
    ("洗钱 · 银行卡", "💳", [
        ("洗钱", 5), ("跑分", 5), ("两卡", 5), ("银行卡", 3), ("卡密", 4), ("冻结", 3),
        ("対公账户", 3), ("对公", 2), ("礼品卡", 4), ("油卡", 4), ("四方支付", 5),
        ("代收", 3), ("代付", 3), ("核销", 4), ("流水", 3), ("涉案账户", 5), ("口子", 1),
        ("现金换U", 4), ("黑吃黑", 3), ("通道", 2), ("手机口", 4), ("京东E卡", 4),
    ]),
    ("网购 · 二手快递", "🛒", [
        ("闲鱼", 4), ("二手", 3), ("快递", 4), ("退款", 3), ("电商", 3), ("网店", 3),
        ("下单", 2), ("运费险", 4), ("仅退款", 4), ("验货宝", 5), ("倒手刀", 5), ("卖家", 2),
        ("买家", 1), ("薅羊毛", 3), ("拼单", 2), ("代购", 3), ("七天无理由", 3), ("撸货", 3),
    ]),
    ("求职 · 加盟", "💼", [
        ("招聘", 4), ("求职", 4), ("找工作", 4), ("面试", 3), ("押金", 3), ("培训费", 4),
        ("加盟", 4), ("连锁", 2), ("模特", 3), ("实习", 3), ("违约金", 3), ("offer", 3),
        ("高管之路", 0), ("传媒公司", 3), ("女团", 3), ("夜场", 3), ("高薪招聘", 4),
    ]),
    ("冒充 · 公检法", "🕵️", [
        ("冒充", 5), ("公检法", 5), ("客服", 3), ("警察", 4), ("通缉", 4), ("协查", 4),
        ("领导", 3), ("熟人", 3), ("老师", 2), ("防疫", 3), ("医保局", 4), ("银行工作人员", 4),
        ("来电自称", 4), ("官方客服", 4),
    ]),
    ("隐私 · 信息黑市", "🔓", [
        ("隐私", 4), ("个人信息", 4), ("信息泄露", 5), ("数据黑市", 5), ("倒卖数据", 5),
        ("通讯录", 3), ("验证码", 3), ("身份证", 3), ("内鬼", 3), ("社工库", 5), ("快递单", 4),
        ("黑市", 3), ("手机号", 2), ("人脸信息", 4),
    ]),
    ("老人 · 学生 · 宝妈", "🧓", [
        ("老人", 5), ("老年", 5), ("中老年", 5), ("爸妈", 3), ("爸妈群", 3), ("学生", 4),
        ("大学", 3), ("未成年", 5), ("宝妈", 5), ("孩子", 2), ("学生党", 4), ("宿舍", 3),
        ("校园", 3), ("新生", 3), ("高中生", 4),
    ]),
    ("生活中的坑", "🧰", [
        ("维修", 4), ("健身", 4), ("私教", 4), ("收藏", 3), ("保健品", 4), ("相亲plitude", 0),
        ("亲子", 4), ("催乳", 4), ("二手车", 4), ("租房", 4), ("装修", 4), ("宠物", 4),
        ("免费领养", 4), ("直播间", 3), ("拍卖", 3), ("理发", 3), ("自助", 2),
        ("充电宝", 4), ("会员", 3), ("景区", 3), ("摆摊", 3), ("盲盒", 3),
    ]),
    # 「民生 · 缴费票务」「应急 · 反诈工具」两个新分类不参与打分：
    # 泛词（理赔/快递/报警…）会把旧文误吸进来，它们只由增补内容标题的【栏目名】指定。
    ("黑灰产大盘", "🌑", [
        ("黑产", 1), ("灰产", 1), ("黑灰产", 1), ("黑话", 4), ("暗语", 4), ("产业链", 1),
        ("资金链", 3), ("境外", 2), ("缅北", 4), ("东南亚", 4), ("园区", 3), ("犯罪团伙", 2),
        ("黑吃黑", 3), ("工具人", 3), ("替罪羊", 4), ("引流", 2), ("打粉", 3), ("接单软件", 3),
        ("偏门", 3),     ]),
]

# ---------------- 你会损失什么 ----------------
RISKS = [
    ("刑责风险", "⛓️", [("帮信罪", 3), ("掩隐罪", 3), ("诈骗罪", 2), ("洗钱罪", 3), ("开设赌场", 3),
                    ("非法经营", 2), ("涉嫌犯罪", 3), ("判刑", 3), ("有期徒刑", 3), ("刑事", 2),
                    ("坐牢", 3), ("案底", 3), ("传唤", 3), ("拘留", 3), ("逮捕", 3), ("违法", 1),
                    ("犯罪", 1), ("帮凶", 3), ("替罪羊", 3), ("处罚", 1)]),
    ("钱财损失", "💸", [("被骗", 2), ("骗走", 2), ("盗刷", 2), ("损失", 1), ("掏空", 2), ("转走", 2),
                    ("转账", 1), ("付款", 1), ("充值", 1), ("本金", 2), ("押金", 2), ("保证金", 2),
                    ("收割", 2), ("割韭菜", 2), ("套走", 2), ("交学费", 2), ("财货两空", 3)]),
    ("账号封禁", "🚫", [("封号", 3), ("被封", 2), ("拉黑", 1), ("平台处罚", 3), ("限流", 2),
                    ("封禁", 3), ("风控", 1), ("违规", 1)]),
    ("隐私泄露", "🔓", [("隐私", 2), ("个人信息", 2), ("通讯录", 2), ("身份证", 2), ("人脸", 2),
                    ("验证码", 2), ("泄露", 2), ("偷拍", 2), ("实名", 1)]),
    ("征信受损", "📉", [("征信", 3), ("逾期", 2), ("黑名单", 2), ("被执行", 3), ("限高", 3),
                    ("失信", 3), ("冻结", 1)]),
    ("人身安全", "🚨", [("绑架", 3), ("暴力", 2), ("迷药", 3), ("听话水", 3), ("取卵", 3),
                    ("代孕", 2), ("卖淫", 2), ("器官", 3), ("生命安全", 3), ("死亡", 2),
                    ("讨债公司", 2), (" cocoa", 0)]),
]

# ---------------- 专盯谁 ----------------
TARGETS = [
    ("中老年", [("老人", 3), ("老年", 3), ("中老年", 3), ("长辈", 2), ("大爷大妈", 3),
              ("退休", 2), ("爸妈", 1)]),
    ("女性", [("女生", 3), ("女性", 3), ("女孩", 3), ("女大学生", 3), ("宝妈", 3),
            ("姐妹", 2), ("女粉", 3), ("女卖家", 3)]),
    ("学生党", [("学生", 3), ("大学", 2), ("未成年", 3), ("校园", 3), ("高考", 3),
             ("新生", 2), ("宿舍", 2), ("学生证", 3), ("学业", 1)]),
    ("商家店主", [("商家", 3), ("店主", 3), ("老板", 2), ("商户", 3), ("店铺", 2), ("旅馆", 3),
              ("烟酒店", 3), ("珠宝店", 3), ("代运营", 3), ("博主", 2), ("卖家", 1)]),
    ("求职者", [("求职", 3), ("找工作", 3), ("简历", 3), ("面试", 3), ("打工人", 3),
             ("上班族", 2), ("应届", 3), ("入职", 2)]),
    ("负债人", [("负债", 3), ("逾期", 2), ("催收", 2), ("欠款", 2), ("黑名单", 2),
             ("上岸", 2), ("债务", 2)]),
]

STEP_HINT = re.compile(r"^(\d)\uFE0F?\u20E3\s*(.{0,40})")


def is_tag_line(line):
    """结尾的话题标签行，形如 `#黑产揭秘 #防骗指南 #反催收骗局`。
    markdown 的 `# 标题` 井号后有空格，这里明确区分。"""
    if not TAG_RE.match(line):
        return False
    parts = [p for p in re.split(r"\s+", line.strip()) if p]
    return all(p.startswith("#") and len(p) > 1 for p in parts)


def looks_like_title(s):
    """判断一行是不是「新文章的标题」，而不是正文里的小标题。

    真标题（"🚨 【黑产揭秘】……骗局！"）和正文小标题（"🚨 陷阱本质：……"、
    "🛡️ 防范指南与安全建议"）长得像，靠五条排除掉后者。
    """
    s = s.strip()
    if not (16 <= len(s) <= 90):
        return False
    if "：" in s or ":" in s:                      # 正文小标题几乎都带冒号，后面跟解释
        return False
    if not TITLE_EMOJI.match(s):                   # 文章标题几乎都用固定的那几个 emoji 开头
        return False
    if not TITLE_WORDS.search(s):                  # 标题里必然出现「揭秘/骗局/陷阱…」
        return False
    if not (re.search(r"[！？?]$", s) or len(s) >= 24):
        return False
    return True


def split_blocks(blocks):
    """标签行漏掉的文章，再用「标题行」补一刀：前面已经收尾了、后面还有成段正文。"""
    out = []
    for b in blocks:
        rows = [l.rstrip() for l in b]
        cut = None
        for i, l in enumerate(rows):
            if i == 0 or not looks_like_title(l.strip()):
                continue
            before = [x for x in rows[:i] if x.strip()]
            after = [x for x in rows[i + 1:] if x.strip()]
            body_before = before[1:] if before else []     # 去掉本篇自己的标题行
            if len(body_before) < 6 or len(after) < 4:
                continue
            cut = i
            break
        if cut is None:
            out.append(b)
            continue
        out.append(rows[:cut])
        out.append(rows[cut:])
    return out


def strip_tags_line(line):
    return [p[1:] for p in re.split(r"\s+", line.strip()) if p.startswith("#") and len(p) > 1]


ROW_KINDS = [
    ("trap", re.compile(r"^(❌|🚫|⛔)")),
    ("warn", re.compile(r"^(⚠|\U0001F6A8 极度|\U0001F6A8 警告)")),
    ("law", re.compile(r"^(⚖|\U0001F9FE|\U0001F4DC)")),
    ("tip", re.compile(r"^(\U0001F6E1|\U0001F4A1|\U0001F4AC 防骗|✅|🟢)")),
    ("end", re.compile(r"^(\U0001F6D1|\U0001F51A)")),
    ("money", re.compile(r"^(💸|💰|\U0001F4B8)")),
]


STEP_NUM_RE = re.compile(r"^(\d\uFE0F?\u20E3|[\u2460-\u2473]|[\u2022\u00B7])\s*")
LEAD_EMOJI_RE = re.compile(r"^[^\u4e00-\u9fffA-Za-z0-9\s]{1,6}\s*")
TRAIL_EMOJI_RE = re.compile(r"\s*[^\u4e00-\u9fffA-Za-z0-9,.!?;:%\s]{1,4}\s*$")
GUARD_RE = re.compile(r"(切勿|千万不要|千万别|别再|凡是|谨记|立即停止|第一时间报警|第一时间拨打|请立即|请勿|一律视为|请牢记|不要轻信|不要点击|不要下载|不要转)")


def short_of(s, n=22):
    """把一行压成一句要点：去序号、去装饰，截到第一个停顿。

    原文里步骤行有两种写法：「1️⃣ 分级筛选，隐私裸奔」整行就是要点；
    「1️⃣ 第一阶段：黑产跑马圈地」冒号前只是"第几步"，真正的信息在后面。
    冒号前的短语够长就用前面的，太短就取冒号后面的。
    """
    t = STEP_NUM_RE.sub("", s).strip()
    head, tail = t, ""
    for sep in ("：", ":"):
        if sep in t:
            head, tail = t.split(sep, 1)
            head = head.strip()
            tail = tail.strip()
            break
    if len(head) < 6 and tail:
        t = tail
    else:
        t = head
    t = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\s]+", "", t)
    t = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]+$", "", t).strip()
    if len(t) > n:
        cut = t[:n]
        for stop in "，、。；：":
            k = cut.rfind(stop)
            if k > 8:
                cut = cut[:k]
                break
        t = cut
    return t


def clean_title(t):
    """把标题拆成 图标 / 栏目 / 正文标题 三段，列表页显示时不用再带一串 emoji。"""
    col = ""
    m = re.search(r"【([^】]{2,12})】", t)
    if m:
        col = m.group(1)
        t = t.replace(m.group(0), " ").strip()
    icon = ""
    m = re.match(r"^([^\u4e00-\u9fffA-Za-z0-9\s]{1,4})\s*", t)
    if m:
        icon = m.group(1)
        t = t[m.end():]
    t = TRAIL_EMOJI_RE.sub("", t).strip()
    t = re.sub(r"\s{2,}", " ", t)
    return icon, col, t


def classify_row(s, in_summary=False):
    """给正文的每一行定个类型，渲染时按类型上色。"""
    if not s:
        return "blank"
    m = STEP_RE.match(s)
    if m:
        return "step"
    for kind, rx in ROW_KINDS:
        if rx.match(s):
            return kind
    # 小标题：带【】栏目名，或短行且以 emoji 起头
    if "【" in s and "】" in s and len(s) <= 60:
        return "sec"
    if SOC_EMOJI.match(s) and len(s) <= 34 and not s.endswith("。"):
        return "sec"
    if len(s) <= 20 and s.endswith("：") is False and re.match(r"^[^，。！？]*$", s) and SOC_EMOJI.match(s):
        return "sec"
    return "p"


FALLBACK_CATS = {"黑灰产大盘": 0.45}     # 兜底类大多是泛词，压低权重，别抢走具体分类

# 增补内容的栏目名直接决定分类，不再依赖关键词打分
CAT_OVERRIDE = {
    "民生骗局": "民生 · 缴费票务",
    "反诈工具箱": "应急 · 反诈工具",
    "冒充来电": "冒充 · 公检法",
    "征信陷阱": "网贷 · 套路贷",
    # 五期增补（2026 最新骗局）：每个栏目对应一个既有分类
    "大盘新变": "黑灰产大盘",
    "学生新骗局": "老人 · 学生 · 宝妈",
    "AI新骗局": "AI · 盗号技术",
    "资金新骗局": "洗钱 · 银行卡",
    "副业新骗局": "求职 · 加盟",
    "帮信新骗局": "洗钱 · 银行卡",
    "投资新骗局": "投资 · 虚拟币",
}


def score(text, words):
    """命中词数 + 权重：既看命中几个词，也看词本身有多特指。"""
    hits = [w for word, w in words if word in text]
    return sum(hits) + (len(hits) - 1) * 0.6 if hits else 0


def score_cats(text):
    best, best_score = None, -1
    for name, _icon, words in CATS:
        sc = score(text, words) * FALLBACK_CATS.get(name, 1)
        if sc > best_score:
            best_score, best = sc, name
    return best or "黑灰产大盘", best_score


def main():
    missing = [p for p in SRCS if not os.path.exists(p)]
    if missing:
        # 素材文件不在仓库里（本地维护、不公开）。这里必须直接失败：
        # 否则会解析出 0 篇，把已发布的 articles.json 和全部产物覆盖成空站。
        raise SystemExit(
            "缺少素材文件（本地维护、不入库）：\n  " +
            "\n  ".join(missing) +
            "\n请确认素材文件存在后再构建；CI 环境无素材时不会覆盖已有产物。")
    raw = "\n".join(io.open(p, encoding="utf-8").read().replace("\r\n", "\n") for p in SRCS)
    lines = raw.split("\n")

    blocks, cur = [], []
    for line in lines:
        cur.append(line)
        if is_tag_line(line):
            blocks.append(cur)
            cur = []
    if any(l.strip() for l in cur):
        blocks.append(cur)
    for _ in range(4):
        blocks = split_blocks(blocks)

    arts = []
    seen = set()
    for idx, blk in enumerate(blocks):
        rows = [l.rstrip() for l in blk]
        tags = []
        while rows and not rows[-1].strip():
            rows.pop()
        if rows and is_tag_line(rows[-1]):
            tags = strip_tags_line(rows.pop())
        while rows and not rows[-1].strip():
            rows.pop()
        title_i = next((i for i, l in enumerate(rows) if l.strip()), None)
        if title_i is None:
            continue
        title = rows[title_i].strip()
        body = [l.strip() for l in rows[title_i + 1:]]
        # 去重：标题完全一样的重复投稿只留第一篇
        key = re.sub(r"[\s\W_]+", "", title)[:40]
        if key in seen:
            continue
        seen.add(key)

        art_tags = tags + [t for t in re.findall(r"【([^】]{2,10})】", title)]
        blob = title + "\n" + "\n".join(body)
        cat, _ = score_cats(blob)
        for col_kw, cat_name in CAT_OVERRIDE.items():   # 增补内容：栏目名直接定分类
            if col_kw in art_tags:
                cat = cat_name
                break

        lines_out = []
        for b in body:
            if not b:
                continue
            lines_out.append({"k": classify_row(b), "t": b})

        risks = [name for name, _icon, words in RISKS if score(blob, words) >= 4]
        targets = [name for name, words in TARGETS if score(blob, words) >= 3]

        n_step = sum(1 for l in lines_out if l["k"] == "step")
        n_trap = sum(1 for l in lines_out if l["k"] in ("trap", "warn"))
        n_tip = sum(1 for l in lines_out if l["k"] in ("tip", "end"))

        # 摘要：取第一段正文；太长就截到句末
        lead = next((l["t"] for l in lines_out if l["k"] == "p" and len(l["t"]) > 20), "")
        if not lead:
            lead = next((l["t"] for l in lines_out if l["k"] in ("p", "sec")), "")
        lead = re.sub(r"^[^\u4e00-\u9fff\s]{1,4}\s*", "", lead).strip()
        if len(lead) > 110:
            cut = lead[:110]
            for stop in "。！？；":
                p = cut.rfind(stop)
                if p > 60:
                    cut = cut[:p + 1]
                    break
            lead = cut

        points, guards = [], []
        for l in lines_out:
            if l["k"] == "step" and len(points) < 4:
                v = short_of(l["t"])
                if v:
                    points.append(v)
            if (len(guards) < 3 and l["k"] in ("tip", "end", "law", "p")
                    and not STEP_NUM_RE.match(l["t"])
                    and GUARD_RE.search(l["t"]) and len(l["t"]) > 10):
                g = l["t"]
                g = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\s❌⚠️🛡️]+", "", g).strip()
                if len(g) > 60:
                    g = g[:60]
                guards.append(g)
        icon, col, clean = clean_title(title)

        arts.append({
            "id": len(arts) + 1,
            "title": clean,
            "icon": icon or "\U0001F6A8",
            "col": col,
            "points": points,
            "guards": guards,
            "cat": cat,
            "tags": art_tags,
            "lead": lead,
            "risks": risks,
            "targets": targets,
            "n": {"step": n_step, "trap": n_trap, "tip": n_tip},
            "body": lines_out,
        })

    io.open(OUT, "w", encoding="utf-8").write(json.dumps(arts, ensure_ascii=False, indent=1))

    # ---------- 体检输出 ----------
    print("articles:", len(arts))
    print("\n== 分类分布 ==")
    for k, v in collections.Counter(a["cat"] for a in arts).most_common():
        print("  %-16s %d" % (k, v))
    print("\n== 风险分布 ==")
    for k, v in collections.Counter(r for a in arts for r in a["risks"]).most_common():
        print("  %-10s %d" % (k, v))
    print("\n== 目标人群 ==")
    for k, v in collections.Counter(t for a in arts for t in a["targets"]).most_common():
        print("  %-10s %d" % (k, v))
    print("\n== 空导语文摘 ==", sum(1 for a in arts if len(a["lead"]) < 12))
    print("== 正文行数 ==", sum(len(a["body"]) for a in arts))
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
