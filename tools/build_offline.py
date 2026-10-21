# -*- coding: utf-8 -*-
"""把 articles.json 打包成一个双击即开的 html。

布局仿 Vue 官方文档（vuejs.org）：
- 顶部导航：logo / 搜索 / 随机 / 深浅色
- 左侧三级目录：板块（速览/骗局分类/查阅/长文/下载）→ 分类（16 类）→ 文章（全部篇目）
  点击分类 = 筛选；点击文章 = 跳转到该篇并展开
- 中间正文：卡片流（折叠摘要 + 展开全文 + 报道链接 + 复制）
- 右侧「本页目录」：当前展开文章的小节锚点
数据全部内联，离线可用，不联网、不上传任何输入。
"""
import datetime
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "articles.json")
OUT = os.path.join(ROOT, "人间防骗指南.html")

BRAND = "#42b883"

CSS = r"""
:root{
  --brand:#42b883; --brand-2:#33a06f; --brand-soft:rgba(66,184,131,.12); --brand-t:#2f9e6c;
  --bg:#ffffff; --bg-soft:#f6f6f7; --bg-elv:#ffffff;
  --t1:#282c34; --t2:#476582; --t3:#8b95a5;
  --divider:#e2e3e5; --divider-soft:#eceef0;
  --code-bg:#f6f6f7;
  --shadow:0 1px 2px rgba(0,0,0,.04),0 4px 16px rgba(0,0,0,.06);
  --nav-h:56px; --sb-w:284px; --toc-w:212px;
}
html.dark{
  --brand:#42d392; --brand-2:#89ddc7; --brand-soft:rgba(66,211,146,.14); --brand-t:#6ee7b0;
  --bg:#1b1b1f; --bg-soft:#212127; --bg-elv:#232329;
  --t1:#e6e6ea; --t2:#a8b3c1; --t3:#717a87;
  --divider:#34343c; --divider-soft:#2c2c33;
  --code-bg:#25252c;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 4px 16px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--t1);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,
    "PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  font-size:16px;line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:var(--brand-t);text-decoration:none}
a:hover{text-decoration:underline}
button{font-family:inherit;cursor:pointer}
svg{fill:currentColor}

/* ---------- 顶部导航 ---------- */
.nav{position:sticky;top:0;z-index:60;background:var(--bg);border-bottom:1px solid var(--divider)}
.nav-in{max-width:1440px;margin:0 auto;height:var(--nav-h);display:flex;align-items:center;gap:14px;padding:0 22px}
.title{display:flex;align-items:center;gap:9px;font-weight:700;font-size:17px;color:var(--t1);white-space:nowrap}
.title .logo{width:26px;height:26px;color:var(--brand);flex:none}
.title:hover{text-decoration:none}
.menu-btn{display:none}
.search{flex:1;max-width:520px;margin:0 auto;position:relative;display:flex;align-items:center}
.search svg{position:absolute;left:11px;width:15px;height:15px;color:var(--t3);pointer-events:none}
.search input{width:100%;height:36px;border:1px solid var(--divider);border-radius:8px;background:var(--bg-soft);
  color:var(--t1);font-size:13.5px;padding:0 36px 0 33px;outline:none;transition:border .2s,background .2s}
.search input:focus{border-color:var(--brand);background:var(--bg)}
.search kbd{position:absolute;right:9px;font-size:11px;color:var(--t3);border:1px solid var(--divider);
  border-radius:4px;padding:0 5px;line-height:16px;background:var(--bg)}
.nav-r{display:flex;align-items:center;gap:6px}
.nav-game{display:inline-flex;align-items:center;gap:5px;height:32px;padding:0 11px;border-radius:16px;
  background:var(--brand);color:#fff;font-size:13px;font-weight:600;text-decoration:none;white-space:nowrap}
.nav-game:hover{opacity:.88;color:#fff}
.nav-game .ico{font-size:14px;line-height:1}
.icon-btn{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border:none;
  background:transparent;border-radius:8px;color:var(--t2)}
.icon-btn:hover{background:var(--bg-soft);color:var(--brand-t)}
.icon-btn svg{width:19px;height:19px}
.switch{width:42px;height:24px;border-radius:999px;border:1px solid var(--divider);background:var(--bg-soft);
  position:relative;transition:background .25s}
.switch .knob{position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:var(--brand);
  display:flex;align-items:center;justify-content:center;color:#fff;transition:left .25s}
.switch .knob svg{width:11px;height:11px}
.switch .moon{display:none}
html.dark .switch .knob{left:20px}
html.dark .switch .sun{display:none}
html.dark .switch .moon{display:block}

/* ---------- 三栏布局 ---------- */
.layout{max-width:1440px;margin:0 auto;display:flex}
.sidebar{width:var(--sb-w);flex:none;height:calc(100vh - var(--nav-h));position:sticky;top:var(--nav-h);
  overflow-y:auto;border-right:1px solid var(--divider-soft);padding:20px 12px 60px;scrollbar-width:thin}
.content{flex:1;min-width:0;padding:34px 44px 120px}
.toc{width:var(--toc-w);flex:none;height:calc(100vh - var(--nav-h));position:sticky;top:var(--nav-h);
  overflow-y:auto;padding:34px 20px 60px;border-left:1px solid var(--divider-soft);font-size:13px;scrollbar-width:thin}
@media (max-width:1200px){.toc{display:none}}
@media (max-width:860px){
  .content{padding:26px 18px 100px}
  .menu-btn{display:inline-flex}
  .sidebar{position:fixed;left:0;top:var(--nav-h);z-index:55;background:var(--bg);
    transform:translateX(-102%);transition:transform .28s;box-shadow:var(--shadow);height:calc(100vh - var(--nav-h))}
  .sidebar.open{transform:none}
  .backdrop{position:fixed;inset:0;top:var(--nav-h);background:rgba(0,0,0,.45);z-index:50;opacity:0;
    pointer-events:none;transition:opacity .25s}
  .backdrop.on{opacity:1;pointer-events:auto}
  .nav-game{padding:0;width:34px;height:34px;justify-content:center;border-radius:9px}
  .nav-game .txt{display:none}
}

/* ---------- 左侧三级目录 ---------- */
.sb-group{margin-bottom:6px}
.sb-gt{font-size:13.5px;font-weight:700;color:var(--t1);padding:8px 10px 6px;letter-spacing:.02em}
.sb-link{display:flex;align-items:center;gap:7px;padding:6px 10px;border-radius:7px;font-size:13.5px;
  color:var(--t2);cursor:pointer}
.sb-link:hover{background:var(--bg-soft);color:var(--brand-t);text-decoration:none}
.sb-cat{margin:1px 0}
.sb-cat-h{display:flex;align-items:center;gap:7px;width:100%;padding:7px 10px;border:none;background:none;
  border-radius:7px;font-size:13.5px;color:var(--t2);text-align:left}
.sb-cat-h:hover{background:var(--bg-soft);color:var(--brand-t)}
.sb-cat-h .ci{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sb-cat-h .cn{font-size:11.5px;color:var(--t3);background:var(--bg-soft);border-radius:999px;padding:0 7px;line-height:17px}
.sb-cat-h .chev{width:12px;height:12px;color:var(--t3);flex:none;transition:transform .2s}
.sb-cat.open > .sb-cat-h{color:var(--brand-t);font-weight:600;background:var(--brand-soft)}
.sb-cat.open > .sb-cat-h .chev{transform:rotate(90deg)}
.sb-arts{display:none;padding:1px 0 3px 14px;border-left:1px solid var(--divider-soft);margin-left:14px}
.sb-cat.open > .sb-arts{display:block}
.sb-art{display:flex;gap:7px;padding:4px 9px;border-radius:6px;font-size:12.8px;color:var(--t2);cursor:pointer;line-height:1.45}
.sb-art:hover{color:var(--brand-t);background:var(--bg-soft);text-decoration:none}
.sb-art i{font-style:normal;color:var(--t3);font-size:11px;flex:none;padding-top:1px;font-variant-numeric:tabular-nums}
.sb-art span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sb-art.active{color:var(--brand-t);font-weight:600;background:var(--brand-soft)}

/* ---------- 正文头部 ---------- */
.doc-head h1{font-size:32px;line-height:1.25;margin:0 0 10px;font-weight:700;letter-spacing:-.01em}
.doc-head .sub{font-size:16.5px;color:var(--t2);margin:0 0 8px}
.doc-head .stat{color:var(--t3);font-size:13.5px;margin:0 0 12px}
.doc-links{color:var(--t3);font-size:13px;margin:0 0 6px;line-height:1.9}
.doc-links b{color:var(--t2);font-weight:600}
.doc-links a{color:var(--brand-t)}
.rules{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin:18px 0 14px}
.rule{border:1px solid var(--divider);border-radius:10px;padding:12px 14px;background:var(--bg-elv)}
.rule b{display:block;font-size:14.5px;margin-bottom:4px;color:var(--brand-t)}
.rule span{font-size:12.8px;color:var(--t2);line-height:1.65;display:block}
.hot{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin:4px 0 20px}
.hot-l{font-size:12.5px;color:var(--t3)}
.chip{border:1px solid var(--divider);background:var(--bg);color:var(--t2);border-radius:999px;
  padding:2px 12px;font-size:12.5px;line-height:20px;transition:all .15s}
.chip:hover{border-color:var(--brand);color:var(--brand-t)}
.chip[aria-pressed="true"]{background:var(--brand);border-color:var(--brand);color:#fff}

/* ---------- 筛选条 ---------- */
.fbar{border:1px solid var(--divider);border-radius:12px;padding:12px 14px;margin:0 0 20px;background:var(--bg-elv)}
.fbar-row{display:flex;align-items:center;gap:10px;padding:4px 0;flex-wrap:wrap}
.fbar-row .fl{font-size:12.5px;color:var(--t3);width:34px;flex:none}
.fbar-row .chips{display:flex;flex-wrap:wrap;gap:6px}
.fbar-row .chip{padding:1px 11px}
.toggle{display:inline-flex;align-items:center;gap:7px;font-size:13px;color:var(--t2);cursor:pointer}
.toggle input{accent-color:var(--brand);width:15px;height:15px}
.reset{border:none;background:none;color:var(--t3);font-size:12.5px;text-decoration:underline;padding:4px 6px}
.reset:hover{color:var(--brand-t)}

/* ---------- 文章卡片 ---------- */
.card{border:1px solid var(--divider);border-radius:12px;background:var(--bg);padding:18px 22px 14px;
  margin-bottom:16px;transition:border-color .2s}
.card:hover{border-color:var(--brand)}
.card[open]{border-color:var(--brand);box-shadow:var(--shadow)}
.card.flash{animation:flash 1.6s}
@keyframes flash{0%,60%{box-shadow:0 0 0 3px var(--brand-soft)}100%{box-shadow:none}}
.card-h{display:flex;align-items:baseline;gap:10px;cursor:pointer}
.card-h .no{font-size:12.5px;font-weight:700;color:var(--brand-t);font-variant-numeric:tabular-nums;flex:none}
.card-h h3{margin:0;font-size:17.5px;line-height:1.45;font-weight:650;color:var(--t1);flex:1}
.card[open] .card-h h3{color:var(--brand-t)}
.badges{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 2px}
.badge{font-size:11.5px;border-radius:999px;padding:0 9px;line-height:20px;border:1px solid var(--divider);color:var(--t2);white-space:nowrap}
.badge.cat{background:var(--brand-soft);border-color:transparent;color:var(--brand-t);font-weight:600}
.badge.risk-red{color:#c0392b;border-color:rgba(192,57,43,.35);background:rgba(192,57,43,.06)}
.badge.risk-amber{color:#b07d15;border-color:rgba(176,125,21,.35);background:rgba(176,125,21,.07)}
.badge.risk-gray{color:var(--t3)}
.badge.risk-blue{color:#2563a8;border-color:rgba(37,99,168,.35);background:rgba(37,99,168,.06)}
html.dark .badge.risk-red{color:#ff8a7a}
html.dark .badge.risk-amber{color:#e5b567}
html.dark .badge.risk-blue{color:#7ab4ff}
.lead{color:var(--t2);font-size:14.5px;margin:8px 0 4px}
.points{list-style:none;margin:10px 0 4px;padding:0;display:grid;gap:6px}
.points li{display:flex;gap:9px;font-size:13.8px;color:var(--t2);line-height:1.6}
.points i{flex:none;width:20px;height:20px;border-radius:50%;background:var(--brand-soft);color:var(--brand-t);
  font-style:normal;font-size:11.5px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:2px}
.guard{margin:10px 0 2px;padding:9px 13px;border-left:3px solid var(--brand);background:var(--brand-soft);
  border-radius:0 8px 8px 0;font-size:13.8px;color:var(--t1)}
.card-f{display:flex;align-items:center;gap:14px;margin-top:12px;padding-top:10px;border-top:1px dashed var(--divider-soft)}
.more{display:inline-flex;align-items:center;gap:4px;border:none;background:none;color:var(--brand-t);
  font-size:13.5px;font-weight:600;padding:4px 2px}
.more svg{width:15px;height:15px;transition:transform .2s}
.card[open] .more svg{transform:rotate(180deg)}
.meta{flex:1;font-size:12.3px;color:var(--t3)}
.copybtn{border:1px solid var(--divider);background:var(--bg);color:var(--t2);border-radius:7px;
  font-size:12.3px;padding:4px 12px}
.copybtn:hover{border-color:var(--brand);color:var(--brand-t)}

/* ---------- 展开的全文 ---------- */
.full{margin-top:16px;border-top:1px solid var(--divider-soft);padding-top:14px}
.blk{margin:10px 0;font-size:14.8px;line-height:1.85;color:var(--t1)}
.blk.sec{font-weight:700;font-size:15.5px;margin:22px 0 6px;color:var(--t1);
  padding-left:11px;border-left:3px solid var(--brand)}
.blk.step{display:flex;gap:10px}
.blk.step em{flex:none;width:22px;height:22px;border-radius:6px;background:var(--brand);color:#fff;
  font-style:normal;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:4px}
.blk.money{font-size:14.8px;color:var(--t1);background:var(--code-bg);border-radius:8px;padding:8px 13px}
.cb{border-radius:10px;padding:11px 14px;margin:12px 0;font-size:14.2px;line-height:1.8}
.cb-t{font-weight:700;font-size:13.5px;display:flex;align-items:center;gap:6px;margin-bottom:4px}
.cb-t .cb-i{font-style:normal}
.cb p{margin:0}
.cb.trap{background:rgba(235,84,84,.07);border:1px solid rgba(235,84,84,.25)}
.cb.trap .cb-t{color:#d64545}
.cb.warn{background:rgba(230,162,60,.08);border:1px solid rgba(230,162,60,.3)}
.cb.warn .cb-t{color:#c07a15}
.cb.tip{background:var(--brand-soft);border:1px solid rgba(66,184,131,.35)}
.cb.tip .cb-t{color:var(--brand-t)}
.cb.end{background:rgba(60,60,67,.06);border:1px solid var(--divider)}
.cb.end .cb-t{color:var(--t1)}
.cb.law{background:rgba(37,99,168,.06);border:1px solid rgba(37,99,168,.28)}
.cb.law .cb-t{color:#2563a8}
html.dark .cb.trap .cb-t{color:#ff8a7a}
html.dark .cb.warn .cb-t{color:#e5b567}
html.dark .cb.law .cb-t{color:#7ab4ff}
.tagline{margin-top:14px;display:flex;flex-wrap:wrap;gap:6px}
.tg{font-size:12px;color:var(--t3);background:var(--bg-soft);border-radius:5px;padding:1px 8px}
.refs{margin-top:16px;border:1px solid var(--divider);border-radius:10px;background:var(--bg-elv);padding:12px 14px}
.refs-h{font-size:13px;font-weight:700;color:var(--t1);margin-bottom:8px}
.ref{display:block;padding:8px 10px;border-radius:8px;text-decoration:none;transition:background .2s}
.ref:hover{background:var(--bg-soft);text-decoration:none}
.ref-t{display:block;font-size:13.5px;font-weight:600;color:var(--brand-t);line-height:1.6}
.ref:hover .ref-t{text-decoration:underline}
.ref-n{display:block;font-size:12.5px;color:var(--t2);line-height:1.6;margin-top:2px}
.ref-s{display:inline-block;margin-top:4px;font-size:11.5px;color:var(--t3);border:1px solid var(--divider);
  border-radius:999px;padding:0 8px;line-height:17px}
.refs-tip{margin-top:8px;font-size:11.5px;color:var(--t3);line-height:1.5}
.pager{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap}
.pager a{flex:1;min-width:200px;border:1px solid var(--divider);border-radius:10px;padding:10px 14px;cursor:pointer}
.pager a:hover{border-color:var(--brand);text-decoration:none}
.pager .p-d{display:block;font-size:11.5px;color:var(--t3)}
.pager .p-t{display:block;font-size:13.2px;color:var(--t2);margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pager .next{text-align:right}

/* ---------- 右侧本页目录 ---------- */
.aside-h{font-size:12.5px;font-weight:700;color:var(--t1);margin-bottom:10px;letter-spacing:.03em}
#aside a{display:block;padding:3px 0 3px 12px;border-left:2px solid var(--divider-soft);color:var(--t2);
  font-size:12.6px;line-height:1.55;cursor:pointer;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#aside a:hover{color:var(--brand-t);border-left-color:var(--brand);text-decoration:none}
.quick a{display:block;padding:5px 0;color:var(--t2);font-size:12.8px}
.quick a:hover{color:var(--brand-t)}

/* ---------- 其他 ---------- */
.empty{border:1px dashed var(--divider);border-radius:12px;padding:40px 20px;text-align:center;color:var(--t2);font-size:14px}
.foot{margin-top:36px;padding-top:18px;border-top:1px solid var(--divider-soft);color:var(--t3);font-size:12.8px;line-height:1.9}
.foot b{color:var(--t2)}
#top{position:fixed;right:22px;bottom:26px;z-index:40;width:40px;height:40px;border-radius:50%;
  border:1px solid var(--divider);background:var(--bg);color:var(--t2);box-shadow:var(--shadow);
  display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .25s}
#top:hover{color:var(--brand-t);border-color:var(--brand)}
#top svg{width:18px;height:18px}
#top.on{opacity:1;pointer-events:auto}
"""

JS = r"""
(function(){
  const D = window.__GP__;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (s) => s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

  const RISK_CLASS = {'刑责风险':'risk-red','钱财损失':'risk-amber','人身安全':'risk-red',
                      '账号封禁':'risk-gray','隐私泄露':'risk-blue','征信受损':'risk-gray'};
  const RISK_ICON = {'刑责风险':'⛓️','钱财损失':'💸','人身安全':'🚨','账号封禁':'🚫','隐私泄露':'🔓','征信受损':'📉'};

  const CAT_ICON = {}; D.cats.forEach(c => CAT_ICON[c.name] = c.icon);
  const BY_CAT = {}; D.cats.forEach(c => BY_CAT[c.name] = []);
  D.arts.forEach(a => {
    a.catIcon = CAT_ICON[a.cat] || '\uD83D\uDD0E';
    (BY_CAT[a.cat] = BY_CAT[a.cat] || []).push(a);
    const rows = a.body.map(s => { const i = s.indexOf('|'); return {k: s.slice(0, i), t: s.slice(i + 1)}; });
    a.body = rows;
    a.hay = [a.title, a.cat, a.col, a.lead, a.points.join(' '), a.guards.join(' '),
             a.tags.join(' '), rows.map(r => r.t).join(' ')].join(' ').toLowerCase();
  });

  const state = { q:'', cat:'', risks:new Set(), tgts:new Set(), onlyRisk:false };

  /* ================= 左侧三级目录 ================= */
  const sb = $('#sb-toc');
  function linkRow(href, txt){ return '<a class="sb-link" href="' + href + '">' + txt + '</a>'; }
  const CHEV = '<svg class="chev" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6z"/></svg>';
  sb.innerHTML =
    '<div class="sb-group"><div class="sb-gt">速览</div>' +
      '<a class="sb-link" data-go="top">三条铁律与使用说明</a>' +
      linkRow('selfcheck.html','📋 生活自查（45 题）') +
    '</div>' +
    '<div class="sb-group"><div class="sb-gt">骗局分类 · 16 类</div>' +
      '<div id="sb-cats">' + D.cats.map(c =>
        '<div class="sb-cat" data-cat="' + esc(c.name) + '">' +
          '<button class="sb-cat-h" type="button" data-cat="' + esc(c.name) + '">' +
            '<span class="ci">' + c.icon + ' ' + esc(c.name) + '</span>' +
            '<span class="cn">' + c.n + '</span>' + CHEV +
          '</button>' +
          '<div class="sb-arts">' + (BY_CAT[c.name] || []).map(a =>
            '<a class="sb-art" data-id="' + a.id + '" title="' + esc(a.title) + '">' +
              '<i>' + String(a.id).padStart(3, '0') + '</i><span>' + esc(a.title) + '</span></a>').join('') +
          '</div>' +
        '</div>').join('') +
      '</div>' +
    '</div>' +
    '<div class="sb-group"><div class="sb-gt">查阅</div>' +
      linkRow('docs/目录.md','📖 全书目录') +
      linkRow('docs/术语表.md','🔤 黑话术语表') +
      linkRow('docs/核实记录.md','✅ 报道核实记录') +
      linkRow('docs/案例与报道.md','📰 案例与报道总表') +
      linkRow('docs/分篇与标注口径.md','⚙️ 分篇与标注口径') +
    '</div>' +
    '<div class="sb-group"><div class="sb-gt">长文</div>' +
      linkRow('docs/长文-骗子的五板斧.md','🎭 骗子的五板斧') +
      linkRow('docs/长文-帮信罪红线.md','⛓️ 帮信罪红线') +
      linkRow('docs/长文-给爸妈的守卫手册.md','🧓 给爸妈的守卫手册') +
    '</div>' +
    '<div class="sb-group"><div class="sb-gt">下载</div>' +
      linkRow('downloads/人间防骗指南.pdf','📕 PDF') +
      linkRow('downloads/人间防骗指南.epub','📗 EPUB') +
      linkRow('downloads/人间防骗指南.apkg','🃏 Anki 牌组') +
      linkRow('index.html','💾 离线单文件 HTML') +
    '</div>';

  sb.addEventListener('click', e => {
    const go = e.target.closest('[data-go="top"]');
    if (go) { e.preventDefault(); scrollTo({top:0, behavior:'smooth'}); closeDrawer(); return; }
    const h = e.target.closest('.sb-cat-h');
    if (h) {
      const cat = h.dataset.cat;
      const box = h.closest('.sb-cat');
      const opening = !box.classList.contains('open');
      $$('.sb-cat').forEach(x => x.classList.remove('open'));
      box.classList.toggle('open', opening);
      state.cat = opening ? cat : '';
      render();
      scrollTo({top:0, behavior:'smooth'});
      return;
    }
    const art = e.target.closest('.sb-art');
    if (art) {
      e.preventDefault();
      const a = D.arts.find(x => x.id === +art.dataset.id);
      if (!a) return;
      if (!match(a)) { resetFilters(false); }
      $$('.sb-cat').forEach(x => x.classList.toggle('open', x.dataset.cat === a.cat));
      jump('p' + a.id, true);
      closeDrawer();
    }
  });
  function closeDrawer(){
    const s = $('#sidebar'); if (s) { s.classList.remove('open'); $('#backdrop').classList.remove('on'); }
  }

  /* ================= 筛选条 ================= */
  function buildChips(sel, list, key){
    $(sel).innerHTML = list.map(x => '<button class="chip" data-v="' + esc(x.name) + '" aria-pressed="false">' +
      x.icon + ' ' + esc(x.name) + '</button>').join('');
    $(sel).addEventListener('click', e => {
      const b = e.target.closest('.chip'); if (!b) return;
      const v = b.dataset.v;
      state[key].has(v) ? state[key].delete(v) : state[key].add(v);
      render();
    });
  }
  buildChips('#f-risk', D.risks, 'risks');
  buildChips('#f-tgt', D.targets, 'tgts');
  $('#only-risk').addEventListener('change', e => { state.onlyRisk = e.target.checked; render(); });
  $('#reset').addEventListener('click', () => resetFilters(true));
  $('#reset2').addEventListener('click', () => resetFilters(true));
  function resetFilters(scroll){
    state.q = ''; state.cat = ''; state.risks.clear(); state.tgts.clear(); state.onlyRisk = false;
    $('#q').value = ''; $('#only-risk').checked = false;
    render();
    if (scroll) scrollTo({top:0, behavior:'smooth'});
  }

  /* ================= 搜索 ================= */
  let timer = null;
  $('#q').addEventListener('input', e => {
    clearTimeout(timer); const v = e.target.value.trim();
    timer = setTimeout(() => { state.q = v.toLowerCase(); render(); }, 120);
  });
  addEventListener('keydown', e => {
    if (e.key === '/' && document.activeElement !== $('#q')) { e.preventDefault(); $('#q').focus(); }
    if (e.key === 'Escape' && document.activeElement === $('#q')) { $('#q').value=''; state.q=''; render(); $('#q').blur(); }
  });

  /* ================= 匹配与渲染 ================= */
  function match(a){
    if (state.cat && a.cat !== state.cat) return false;
    if (state.onlyRisk && !a.risks.includes('刑责风险')) return false;
    for (const r of state.risks) if (!a.risks.includes(r)) return false;
    for (const t of state.tgts) if (!a.targets.includes(t)) return false;
    if (state.q && a.hay.indexOf(state.q) === -1) return false;
    return true;
  }

  function cb(k, icon, title, t){
    return '<div class="cb ' + k + '"><div class="cb-t"><span class="cb-i">' + icon + '</span>' +
      title + '</div><p>' + t + '</p></div>';
  }
  const CB_KINDS = ['trap', 'warn', 'tip', 'end', 'law'];
  // 原文里「⚖️ 法律红线」这类行只是小标题，去掉行首图标后短、且没有句末标点，就当小标题。
  function isHeadline(r){
    const t = r.t.replace(/^[^\u4e00-\u9fffA-Za-z0-9\s]{1,4}\s*/, '').trim();
    if (t.length > 14) return false;
    if (/[，。；！？,!?]/.test(t)) return false;
    return true;
  }
  function rowsHtml(a){
    let stepNo = 0, secNo = 0;
    return a.body.map(r => {
      const t = esc(r.t);
      if (r.k === 'sec') return '<p class="blk sec" id="sec-' + a.id + '-' + (++secNo) + '">' + t + '</p>';
      if (CB_KINDS.includes(r.k) && isHeadline(r)) return '<p class="blk sec" id="sec-' + a.id + '-' + (++secNo) + '">' + t + '</p>';
      if (r.k === 'step') return '<p class="blk step"><em>' + (++stepNo) + '</em>' + t.replace(/^\d\S*️?\s*/, '') + '</p>';
      if (r.k === 'trap') return cb('trap', '⛔', '骗局关键点', t);
      if (r.k === 'warn') return cb('warn', '⚠️', '注意', t);
      if (r.k === 'tip') return cb('tip', '✅', '防身建议', t);
      if (r.k === 'end') return cb('end', '🛑', '醒脑总结', t);
      if (r.k === 'law') return cb('law', '⚖️', '法律依据', t);
      if (r.k === 'money') return '<p class="blk money">' + t + '</p>';
      return '<p class="blk">' + t + '</p>';
    }).join('');
  }
  function pagerHtml(a){
    const prev = D.arts.find(x => x.id === a.id - 1);
    const next = D.arts.find(x => x.id === a.id + 1);
    let h = '<div class="pager">';
    if (prev) h += '<a class="prev" data-go="' + prev.id + '"><span class="p-d">← 上一篇</span><span class="p-t">' + esc(prev.title) + '</span></a>';
    if (next) h += '<a class="next" data-go="' + next.id + '"><span class="p-d">下一篇 →</span><span class="p-t">' + esc(next.title) + '</span></a>';
    return h + '</div>';
  }
  function cardHtml(a){
    const badges = ['<span class="badge cat">' + esc(a.catIcon) + ' ' + esc(a.cat) + '</span>']
      .concat(a.col ? ['<span class="badge col">' + esc(a.col) + '</span>'] : [])
      .concat(a.risks.map(r => '<span class="badge ' + (RISK_CLASS[r] || 'risk-gray') + '">' + RISK_ICON[r] + ' ' + esc(r) + '</span>'))
      .concat(a.targets.map(t => '<span class="badge tgt">🎯 ' + esc(t) + '</span>'));
    const pts = a.points.length
      ? '<ul class="points">' + a.points.map((p, i) => '<li><i>' + (i + 1) + '</i><span>' + esc(p) + '</span></li>').join('') + '</ul>' : '';
    const guard = a.guards.length ? '<p class="guard">' + esc(a.guards[0]) + '</p>' : '';
    const tags = a.tags.slice(0, 8).map(t => '<span class="tg">#' + esc(t) + '</span>').join('');
    const refs = a.refs && a.refs.length
      ? '<div class="refs"><div class="refs-h">📰 相关案例与公开报道</div>' +
        a.refs.map(r => '<a class="ref" href="' + esc(r.u) + '" target="_blank" rel="noopener">' +
          '<span class="ref-t">' + esc(r.t) + '</span><span class="ref-n">' + esc(r.n) + '</span>' +
          '<span class="ref-s">' + esc(r.s) + ' ↗</span></a>').join('') +
        '<div class="refs-tip">以上为各级法院、检察院、公安机关及央媒公开发布的同类案例，点开可看原文。</div></div>' : '';
    const cnt = [a.n.step ? a.n.step + ' 步套路' : '', a.n.trap ? a.n.trap + ' 个坑' : '',
                 a.n.tip ? a.n.tip + ' 条防身' : '', a.refs && a.refs.length ? '📰 ' + a.refs.length + ' 条报道' : ''].filter(Boolean).join(' · ');
    return '<article class="card" id="p' + a.id + '" data-id="' + a.id + '">' +
      '<div class="card-h"><span class="no">#' + String(a.id).padStart(3, '0') + '</span><h3>' + esc(a.title) + '</h3></div>' +
      '<div class="badges">' + badges.join('') + '</div>' +
      '<p class="lead">' + esc(a.lead) + '</p>' + pts + guard +
      '<div class="card-f"><button class="more" type="button">看完整拆解<svg viewBox="0 0 24 24"><path d="M6 9l6 7 6-7z"/></svg></button>' +
      '<span class="meta">' + cnt + '</span>' +
      '<button class="copybtn" type="button">复制全文</button></div>' +
      '<div class="full" hidden><div class="full-b">' + rowsHtml(a) + '</div>' + refs +
      '<div class="tagline">' + tags + '</div>' + pagerHtml(a) + '</div>' +
      '</article>';
  }

  /* ================= 右侧本页目录 ================= */
  const aside = $('#aside');
  function buildAside(a){
    if (!a){
      aside.innerHTML = '<div class="aside-h">快捷入口</div><div class="quick">' +
        '<a href="downloads/人间防骗指南.pdf">📕 PDF 下载</a>' +
        '<a href="downloads/人间防骗指南.epub">📗 EPUB 下载</a>' +
        '<a href="downloads/人间防骗指南.apkg">🃏 Anki 牌组</a>' +
        '<a href="selfcheck.html">📋 生活自查（45 题）</a>' +
        '<a href="docs/案例与报道.md">📰 案例与报道总表</a>' +
        '<a href="docs/目录.md">📖 全书目录</a></div>';
      return;
    }
    const secs = a.body.filter(r => r.k === 'sec' || (CB_KINDS.includes(r.k) && isHeadline(r)));
    let h = '<div class="aside-h">本页目录</div>';
    secs.forEach((s, i) => { h += '<a data-sec="' + a.id + '-' + (i + 1) + '">' + esc(s.t) + '</a>'; });
    if (!secs.length) h += '<span style="color:var(--t3);display:block;padding:3px 0 3px 12px">（这篇没有小节标题）</span>';
    aside.innerHTML = h;
  }
  aside.addEventListener('click', e => {
    const a = e.target.closest('a[data-sec]'); if (!a) return;
    const el = document.getElementById('sec-' + a.dataset.sec);
    if (el && el.scrollIntoView) el.scrollIntoView({behavior:'smooth', block:'start'});
  });

  /* ================= 渲染 ================= */
  const list = $('#list'), empty = $('#empty'), cnt = $('#cnt');
  function render(){
    const hits = D.arts.filter(match);
    cnt.textContent = hits.length;
    empty.hidden = hits.length > 0;
    list.innerHTML = hits.map(cardHtml).join('');
    $$('.chip').forEach(x => {
      const on = state.risks.has(x.dataset.v) || state.tgts.has(x.dataset.v);
      x.setAttribute('aria-pressed', on);
    });
    buildAside(null);
    spy();
  }

  /* ================= 卡片交互 ================= */
  list.addEventListener('click', e => {
    const card = e.target.closest('.card');
    if (!card) return;
    const pg = e.target.closest('.pager a');
    if (pg){
      e.preventDefault();
      const a = D.arts.find(x => x.id === +pg.dataset.go);
      if (a && !match(a)) resetFilters(false);
      jump('p' + pg.dataset.go, true);
      return;
    }
    if (e.target.closest('.copybtn')) { copyFull(card); return; }
    const btn = e.target.closest('.more'); const wrap = $('.full', card);
    if (btn || e.target.closest('.card-h')) {
      const open = wrap.hidden;
      wrap.hidden = !open;
      card.toggleAttribute('open', open);
      $('.more', card).firstChild.nodeValue = open ? '收起' : '看完整拆解';
      const a = D.arts.find(x => x.id === +card.dataset.id);
      buildAside(open ? a : null);
      if (open) { try { history.replaceState(null, '', '#p' + card.dataset.id); } catch (err) {} }
    }
  });

  function plainOf(a){
    const refs = (a.refs || []).map(r => '· ' + r.t + '（' + r.s + '）\n  ' + r.u).join('\n');
    return '【' + a.cat + '】' + a.title + '\n' + (a.lead ? a.lead + '\n' : '') + '\n' +
      a.body.map(r => r.t).join('\n') + '\n' +
      (refs ? '\n【相关案例与公开报道】\n' + refs + '\n' : '') + '\n（人间防骗指南 #' + a.id + '）';
  }
  function copyFull(card){
    const a = D.arts.find(x => x.id === +card.dataset.id);
    const txt = plainOf(a);
    const done = (ok) => {
      const b = $('.copybtn', card); const old = b.textContent;
      b.textContent = ok ? '已复制 ✓' : '复制失败';
      setTimeout(() => b.textContent = old, 1400);
    };
    const fallback = () => {
      const ta = document.createElement('textarea');
      ta.value = txt; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      let ok = false; try { ok = document.execCommand('copy'); } catch (err) {}
      ta.remove(); done(ok);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(txt).then(() => done(true), fallback);
    } else { fallback(); }
  }

  /* ================= 跳转 / 随机 / 回到顶部 ================= */
  function jump(id, silent){
    const el = document.getElementById(id); if (!el) return;
    const wrap = $('.full', el);
    if (wrap && wrap.hidden) {
      wrap.hidden = false; el.toggleAttribute('open', true);
      $('.more', el).firstChild.nodeValue = '收起';
      const a = D.arts.find(x => x.id === +el.dataset.id);
      buildAside(a);
    }
    if (el.scrollIntoView) el.scrollIntoView({behavior:'smooth', block:'start'});
    el.classList.add('flash'); setTimeout(() => el.classList.remove('flash'), 1600);
    markActive(+el.dataset.id);
  }
  $('#rand').addEventListener('click', () => {
    const pool = D.arts.filter(match);
    const a = pool[Math.floor(Math.random() * pool.length)];
    if (a) jump('p' + a.id, true);
  });
  const topBtn = $('#top');
  addEventListener('scroll', () => { topBtn.classList.toggle('on', scrollY > 600); }, {passive:true});
  topBtn.addEventListener('click', () => scrollTo({top:0, behavior:'smooth'}));

  /* ================= 滚动高亮（目录联动） ================= */
  let spyTimer = null;
  function markActive(id){
    $$('.sb-art').forEach(x => x.classList.toggle('active', +x.dataset.id === id));
    if (id != null) {
      const cur = $('.sb-art.active');
      if (cur) {
        const p = cur.closest('.sb-cat');
        if (p && !p.classList.contains('open')) {
          $$('.sb-cat').forEach(x => x.classList.remove('open'));
          p.classList.add('open');
        }
      }
    }
  }
  function spy(){
    clearTimeout(spyTimer);
    spyTimer = setTimeout(() => {
      let cur = null;
      for (const el of $$('.card')) {
        if (el.getBoundingClientRect().top <= 120) cur = el; else break;
      }
      markActive(cur ? +cur.dataset.id : null);
    }, 120);
  }
  addEventListener('scroll', () => spy(), {passive:true});

  /* ================= 抽屉 / hash / 深浅色 ================= */
  const side = $('#sidebar'), back = $('#backdrop');
  $('#menu').addEventListener('click', () => { side.classList.toggle('open'); back.classList.toggle('on'); });
  back.addEventListener('click', () => { side.classList.remove('open'); back.classList.remove('on'); });
  addEventListener('hashchange', () => location.hash && jump(location.hash.slice(1), true));

  const root = document.documentElement;
  $('#theme').addEventListener('click', () => {
    const dark = root.classList.toggle('dark');
    try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (err) {}
  });

  render();
  if (location.hash) setTimeout(() => jump(location.hash.slice(1), true), 80);
})();
"""

GITHUB_ICON = ('<svg viewBox="0 0 24 24"><path d="M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8'
               '-1.4-1.8-1.1-.8.1-.8.1-.8 1.3.1 1.9 1.2 1.9 1.2 1.1 1.9 2.8 1.3 3.5 1 0-.8.4-1.3.8-1.6-2.7-.3-5.5-1.3'
               '-5.5-6 0-1.2.5-2.3 1.2-3.1-.1-.4-.5-1.6.1-3.2 0 0 1-.3 3.3 1.2a11.11 0 0 1 6 0C17.3 4.7 18.3 5 18.3 5c.6 1.6.2 2.8.1 3.2a4.4 4.4 0 0 1 1.2 3.1c0 4.7-2.8 5.7-5.5 6 .4.4.8 1.1.8 2.3v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .3z"/></svg>')
SUN = ('<svg class="sun" viewBox="0 0 24 24"><path d="M12 4a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0V5a1 1 0 0 1 1-1zm0 13a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0v-1a1 1 0 0 1 1-1zm8-6a1 1 0 1 1 0 2h-1a1 1 0 1 1 0-2zM5 11a1 1 0 0 1 1 1h-1a1 1 0 0 1 0-2zm11.7-4.3a1 1 0 0 1 1.4 1.4l-.7.7a1 1 0 0 1-1.4-1.4zM7.6 15.9a1 1 0 0 1 1.4 1.4l-.7.7a1 1 0 0 1-1.4-1.4zM12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8z"/></svg>')
MOON = ('<svg class="moon" viewBox="0 0 24 24"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>')
SEARCH_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/>'
               '<path d="m20 20-3.5-3.5" stroke-linecap="round"/></svg>')
SHIELD = ('<svg viewBox="0 0 24 24"><path d="M12 2l8 3v6c0 5-3.4 9.4-8 11-4.6-1.6-8-6-8-11V5l8-3z" fill="none" '
          'stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>')
UP = ('<svg viewBox="0 0 24 24"><path d="M12 6l7 7-1.4 1.4L12 8.8 6.4 14.4 5 13z"/></svg>')
DICE = ('<svg viewBox="0 0 24 24"><path d="M4 4h16v16H4z" fill="none" stroke="currentColor" stroke-width="2"/>'
        '<circle cx="9" cy="9" r="1.6"/><circle cx="15" cy="15" r="1.6"/><circle cx="12" cy="12" r="1.6"/></svg>')
MENU = ('<svg viewBox="0 0 24 24"><path d="M4 6h16v2H4zm0 5h16v2H4zm0 5h16v2H4z"/></svg>')

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' "
           "height='64' rx='14' fill='%2342b883'/%3E%3Cpath d='M32 12l16 6v14c0 10-7 18-16 20-9-2-16-10-16-20V18l16-6z' "
           "fill='none' stroke='white' stroke-width='4'/%3E%3Cpath d='M24 32l6 6 12-13' fill='none' stroke='white' "
           "stroke-width='5' stroke-linecap='round'/%3E%3C/svg%3E")


def main():
    arts = json.load(io.open(DATA, encoding="utf-8"))
    if not arts:
        raise SystemExit("articles.json 是空的，拒绝生成空站（防止覆盖已发布产物）。")
    cat_order = []
    counts = {}
    for a in arts:
        counts[a["cat"]] = counts.get(a["cat"], 0) + 1
        if a["cat"] not in cat_order:
            cat_order.append(a["cat"])
    cat_order.sort(key=lambda c: -counts[c])
    cats = [{"name": c, "n": counts[c], "icon": None} for c in cat_order]
    ICONS = {"网贷 · 套路贷": "🏦", "兼职 · 刷单": "🧾", "投资 · 虚拟币": "📈", "网赌 · 博彩": "🎰",
             "情感 · 色情陷阱": "💔", "AI · 盗号技术": "🤖", "洗钱 · 银行卡": "💳", "网购 · 二手快递": "🛒",
             "求职 · 加盟": "💼", "冒充 · 公检法": "🕵️", "隐私 · 信息黑市": "🔓", "老人 · 学生 · 宝妈": "🧓",
             "生活中的坑": "🧰", "黑灰产大盘": "🌑", "民生 · 缴费票务": "🎫", "应急 · 反诈工具": "🆘"}
    for c in cats:
        c["icon"] = ICONS.get(c["name"], "🔎")

    risks, targets = [], []
    for a in arts:
        for r in a["risks"]:
            risks.append(r)
        for t in a["targets"]:
            targets.append(t)
    RICON = {"刑责风险": "⛓️", "钱财损失": "💸", "账号封禁": "🚫", "隐私泄露": "🔓", "征信受损": "📉", "人身安全": "🚨"}
    TICON = {"中老年": "🧓", "女性": "👩", "学生党": "🎒", "商家店主": "🏪", "求职者": "💼", "负债人": "📉"}
    risk_list = [{"name": k, "n": risks.count(k), "icon": RICON.get(k, "•")}
                 for k in dict.fromkeys(risks)] if risks else []
    risk_list.sort(key=lambda x: -x["n"])
    tgt_list = [{"name": k, "n": targets.count(k), "icon": TICON.get(k, "•")}
                for k in dict.fromkeys(targets)] if targets else []
    tgt_list.sort(key=lambda x: -x["n"])

    news = json.load(io.open(os.path.join(HERE, "news.json"), encoding="utf-8"))["reports"]
    for a in arts:
        blob = a["title"] + "\n" + "\n".join(r["t"] for r in a["body"])
        hits = []
        for r in news:
            score = 0
            if a["cat"] in r["cats"]:
                score += 1
            ks = [k for k in r["keys"] if k in blob]
            if ks:
                score += 2 + len(ks)
            if score:
                hits.append((-score, r))
        hits.sort(key=lambda x: x[0])
        a["refs"] = [{"t": r["t"], "u": r["u"], "s": r["s"], "n": r["n"]} for _, r in hits[:4]]

    slim = []
    for a in arts:
        slim.append({
            "id": a["id"], "title": a["title"], "cat": a["cat"], "col": a["col"],
            "lead": a["lead"], "points": a["points"], "guards": a["guards"],
            "risks": a["risks"], "targets": a["targets"], "n": a["n"],
            "tags": a["tags"][:8],
            "refs": a["refs"],
            "body": [r["k"] + "|" + r["t"] for r in a["body"]],
        })
    arts = slim

    n = len(arts)
    n_risk = sum(1 for a in arts if "刑责风险" in a["risks"])
    n_rows = sum(len(a["body"]) for a in arts)
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    data = {"n": n, "cats": cats, "risks": risk_list, "targets": tgt_list, "arts": arts}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    noscript = "\n".join("  <li>%s %s</li>" % (a["cat"], a["title"]) for a in arts[:40])

    html = TEMPLATE
    for k, v in [
        ("@@CSS@@", CSS), ("@@JS@@", JS), ("@@DATA@@", payload), ("@@N@@", str(n)),
        ("@@NRISK@@", str(n_risk)), ("@@NROWS@@", str(n_rows)), ("@@TODAY@@", today),
        ("@@NOSCRIPT@@", noscript), ("@@FAVICON@@", FAVICON),
        ("@@SHIELD@@", SHIELD), ("@@SEARCH@@", SEARCH_ICON), ("@@SUN@@", SUN), ("@@MOON@@", MOON),
        ("@@UP@@", UP), ("@@DICE@@", DICE), ("@@MENU@@", MENU), ("@@BRAND@@", BRAND),
        ("@@GITHUB@@", GITHUB_ICON),
    ]:
        html = html.replace(k, v)
    io.open(OUT, "w", encoding="utf-8").write(html)
    print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
    print(" 文章 %d 篇，涉刑 %d 篇，正文 %d 行" % (n, n_risk, n_rows))


TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>人间防骗指南 · @@N@@ 种骗局，逐个拆开给你看</title>
<meta name="description" content="@@N@@ 个真实骗局逐个拆解：套路分几步、坑在哪、会损失什么、谁能一眼识破。左侧三级目录直接跳转，离线单文件，双击即开。">
<meta name="keywords" content="防骗,反诈,骗局拆解,刷单,杀猪盘,洗钱,帮信罪,套路贷,黑产,电信诈骗">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="@@BRAND@@" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1b1b1f" media="(prefers-color-scheme: dark)">
<link rel="icon" href="@@FAVICON@@">
<meta property="og:type" content="website">
<meta property="og:locale" content="zh_CN">
<meta property="og:title" content="人间防骗指南">
<meta property="og:description" content="@@N@@ 个真实骗局逐个拆解：套路分几步、坑在哪、会损失什么。">
<script>(function(){try{var s=localStorage.getItem('theme');var d=s?s==='dark':matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark')}catch(e){}})();</script>
<style>@@CSS@@</style>
</head>
<body>
<noscript>
  <div style="padding:80px 24px;max-width:760px;margin:0 auto">
    <h1>人间防骗指南</h1>
    <p>这是一个离线单文件的骗局拆解库，共 @@N@@ 篇，需要 JavaScript 才能检索和展开。下面是前 40 篇目录：</p>
    <ol>
@@NOSCRIPT@@
    </ol>
  </div>
</noscript>

<header class="nav">
  <div class="nav-in">
    <button class="icon-btn menu-btn" id="menu" aria-label="打开目录" aria-expanded="false">@@MENU@@</button>
    <a class="title" href="#"><span class="logo" aria-hidden="true">@@SHIELD@@</span><span>人间防骗指南</span></a>
    <label class="search">
      @@SEARCH@@
      <input id="q" type="search" placeholder="搜骗局：刷单、FaceTime、裸聊、验证码……" autocomplete="off" aria-label="搜索骗局">
      <kbd>/</kbd>
    </label>
    <div class="nav-r">
      <a class="nav-game" href="game/" title="玩一局《别被骗了啊》：12 个真实骗局，看你顶住几局"><span class="ico">🎮</span><span class="txt">玩一局</span></a>
      <a class="nav-game" href="game/murdoku.html" title="《识骗迷局》：九个人摆回案发现场，找出骗子和受害者的坐标"><span class="ico">🧩</span><span class="txt">识骗迷局</span></a>
      <button class="icon-btn" id="rand" title="随机翻一篇" aria-label="随机翻一篇">@@DICE@@</button>
      <button class="switch" id="theme" aria-label="切换深色模式" title="切换深色模式"><span class="knob">@@SUN@@@@MOON@@</span></button>
    </div>
  </div>
</header>

<div class="backdrop" id="backdrop"></div>

<div class="layout">
  <aside class="sidebar" id="sidebar">
    <nav id="sb-toc" aria-label="三级目录"></nav>
  </aside>

  <main class="content">
    <div class="doc">
      <div class="doc-head">
        <h1>人间防骗指南</h1>
        <p class="sub">@@N@@ 个骗局，逐个拆开：套路分几步、坑在哪、会损失什么、哪些话一听到就该挂电话。</p>
        <p class="stat">当前显示 <b id="cnt">–</b> 篇 · 共 @@N@@ 篇 · 正文 @@NROWS@@ 段 · 其中 @@NRISK@@ 篇碰了要负刑责</p>
        <div class="doc-links"><b>在线</b>：<a href="https://qerssd.github.io/HowToAvoidScams/">网页版 qerssd.github.io/HowToAvoidScams</a> · <a href="https://qerssd.github.io/HowToAvoidScams/game/">直接玩一局</a>——手机点开就能玩，不用下载、不用装任何东西</div>
        <div class="doc-links"><b>下载</b>：<a href="downloads/人间防骗指南.pdf">PDF</a> · <a href="downloads/人间防骗指南.epub">EPUB</a> · <a href="index.html">离线单文件（HTML）</a> · <a href="downloads/人间防骗指南.apkg">Anki 牌组</a></div>
        <div class="doc-links"><b>查阅</b>：<a href="docs/目录.md">目录</a> · <a href="docs/术语表.md">术语表</a> · <a href="docs/核实记录.md">核实记录</a> · <a href="docs/案例与报道.md">案例与报道</a></div>
        <div class="doc-links"><b>自查</b>：<a href="selfcheck.html">生活自查</a>——回答 45 道是否题，看看哪些事你还没做到、先做哪几件</div>
        <div class="doc-links"><b>玩一局</b>：<a href="game/">《别被骗了啊》</a>——12 个真实骗局改编的聊天式模拟，你只有 1 万块，局中不给答案，走完才复盘；每个选项都有自己的下场</div>
        <div class="doc-links"><b>烧脑</b>：<a href="game/murdoku.html">《识骗迷局》</a>——9×9 案发现场，九个人各占一格、每排每列每区块只有一人；按线索把人摆回原位，骗子和受害者的坐标就露出来了</div>
        <div class="doc-links"><b>长文</b>：<a href="docs/长文-骗子的五板斧.md">骗子的五板斧</a> · <a href="docs/长文-帮信罪红线.md">帮信罪红线</a> · <a href="docs/长文-给爸妈的守卫手册.md">给爸妈的守卫手册</a></div>
        <div class="rules">
          <div class="rule"><b>① 陌生链接不点、验证码不给</b><span>验证码是最后一道锁。真客服永远不会要你的验证码，也不会让你下载远程控制软件。</span></div>
          <div class="rule"><b>② 先掏钱的兼职都是骗</b><span>押金、保证金、培训费、解冻费——名目越多，跑得越快。正规工作不会让员工先交钱。</span></div>
          <div class="rule"><b>③ 96110 要接，110 要打</b><span>96110 是全国反诈专线，来电说明你正在被骗。已经转钱了立刻打 110，30 分钟内止付的概率最高。</span></div>
        </div>
        <div class="fbar">
          <div class="fbar-row"><span class="fl">损失</span><div class="chips" id="f-risk"></div></div>
          <div class="fbar-row"><span class="fl">人群</span><div class="chips" id="f-tgt"></div></div>
          <div class="fbar-row">
            <label class="toggle"><input type="checkbox" id="only-risk"> 只看可能背上刑责的</label>
            <button class="reset" id="reset" type="button">清空筛选</button>
          </div>
        </div>
      </div>
      <div id="list"></div>
      <div class="empty" id="empty" hidden>没有匹配的骗局。换个关键词，或去掉一个筛选条件。<div><button id="reset2">清空筛选</button></div></div>
      <div class="foot">
        <b>怎么用：</b>左侧目录按「板块 → 分类 → 文章」三级展开，点分类只看这一类，点文章直接跳到那一篇；心里没底时也可以先搜关键词（平台名、话术、要求），找到对应那篇看它的「第几步」，卡在同一个位置就立刻停手。<br><br>
        <b>关于内容：</b>正文来自口播稿《人间防骗指南》，由脚本按篇切分并标注类型，只做了分篇和结构标注，没有改写原意。标注的目的是方便检索，不代表个案的法律认定。<br>
        真遇到事：拨打 <b>110</b> 报案、<b>96110</b> 咨询，或通过「国家反诈中心」App 举报。本页离线可用，不联网、不上传任何输入。<br><br>
        生成于 @@TODAY@@（本地时间）。
      </div>
    </div>
  </main>

  <aside class="toc" id="aside"></aside>
</div>

<button id="top" title="回到顶部" aria-label="回到顶部">@@UP@@</button>

<script>window.__GP__=@@DATA@@;</script>
<script>@@JS@@</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
