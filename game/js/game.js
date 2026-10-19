// 《别被骗了啊》v4：随机身份 + 随机事件 + 纯诱惑选择 + 结束后统一复盘
(function(){
'use strict';
const EVENTS = window.EVENTS || [];

const IDENTITIES = {
  '学生党':   {icon:'🎓', money:8000,  alert:30, credit:85, family:60, tags:['学生','学生党','求职者','年轻人'], desc:'大学生，生活费不多，想搞点副业'},
  '上班族':   {icon:'💼', money:150000,alert:40, credit:80, family:60, tags:['上班族','打工人','求职者'], desc:'工薪族，攒了几年钱'},
  '宝妈':     {icon:'👶', money:60000, alert:35, credit:75, family:70, tags:['女性','宝妈'], desc:'在家带娃，想找副业'},
  '退休老人': {icon:'🧓', money:300000,alert:20, credit:80, family:80, tags:['中老年','老人'], desc:'退休金 30 万'},
  '商家店主': {icon:'🏪', money:120000,alert:38, credit:70, family:55, tags:['商家店主','老板'], desc:'经营一家小店'},
  '负债人':   {icon:'💳', money:20000, alert:32, credit:40, family:40, tags:['负债人','欠债','年轻人'], desc:'背着债，急着翻身'},
};

const TOTAL_ROUNDS = 12;
const START_MONEY = 10000;  // 全局初始钱包，不论什么身份都只有这一笔

const S = {};
let CUR = null;
const ONLINE_HOME = 'https://qerssd.github.io/HowToAvoidScams/';
const ONLINE_GAME = 'https://qerssd.github.io/HowToAvoidScams/game/';
const IS_ONLINE = /^https?:$/.test(location.protocol) && /(^|\.)github\.io$/.test(location.hostname);
// 线上直接回线上首页；本地双击时仍走相对路径
const BACK_URL = IS_ONLINE ? ONLINE_HOME : '../index.html';

// 每个选项的专属回应：stage 0=工具/真机会的两选项，1=正解，2=下沉局，3=加码轮
function rp(stage, i, j){
  const r = (window.REPLIES || {})[CUR && CUR.id] || {};
  if(stage === 0) return (r.opt || [])[i] || '';
  if(stage === 1) return r.ok || '';
  if(stage === 2) return (r.s2 || [])[i] || '';
  if(stage === 3){ const row = (r.esc || {})[j] || []; return row[i] || ''; }
  if(stage === 9) return '你关掉了借款页面。对方连发三条："就差这一步，你甘心？"';
  return '';
}

function rnd(){ return Math.random(); }
function pickOne(arr){ return arr[Math.floor(rnd()*arr.length)]; }
function shuffle(a){
  const x=a.slice();
  for(let i=x.length-1;i>0;i--){ const j=Math.floor(rnd()*(i+1)); [x[i],x[j]]=[x[j],x[i]]; }
  return x;
}
function el(html){ document.getElementById('app').innerHTML = html; window.scrollTo(0,0); }
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function fmt(n){ return '¥' + Math.round(n).toLocaleString('zh-CN'); }
function floatText(t,up){
  const d=document.createElement('div'); d.className='float'; d.textContent=t;
  d.style.color = up ? 'var(--brand)' : 'var(--danger)';
  document.body.appendChild(d); setTimeout(()=>d.remove(),1300);
}
function toggleTheme(){
  document.documentElement.classList.toggle('dark');
  try{ localStorage.setItem('bbpl4_theme', document.documentElement.classList.contains('dark')?'d':'l'); }catch(e){}
}
try{ if(localStorage.getItem('bbpl4_theme')==='d') document.documentElement.classList.add('dark'); }catch(e){}

/* ============ 开始页：选身份 ============ */
function start(){
  // 完全重置
  for(const k in S) delete S[k];
  el(`<h1 style="text-align:center;font-size:24px;margin:60px 0 12px">别被骗了啊</h1>
  <p style="text-align:center;color:var(--muted);font-size:14px;line-height:2;margin:0 0 24px">
    你有 <b style="color:var(--brand)">¥10,000</b>。<br>
    随机给你推 12 个局，选错就扣钱。<br>
    骗子会连续催你加码，顶住就赢。<br>
    局中不告诉你对错——走完 12 局，一次性复盘你踩了哪些坑。
  </p>
  <div style="text-align:center;margin-top:18px">
    <button class="btn primary" style="font-size:16px;padding:14px 32px" onclick="window.__G.nextRound()">🔕 手机响了，开始 →</button>
  </div>
  <div style="text-align:center;margin-top:14px">
    <a class="back-link" href="${BACK_URL}">📖 先看《人间防骗指南》364 篇拆解</a>
  </div>
  ${IS_ONLINE?`<div style="text-align:center;margin-top:10px;font-size:12px;color:var(--muted)">在线地址：<a href="${ONLINE_GAME}" style="color:var(--brand)">qerssd.github.io/HowToAvoidScams/game</a></div>`:''}
  <footer>取材自《人间防骗指南》<br>遇真实诈骗：110 报案 · 96110 咨询</footer>`);
}

function begin(idKey){
  const id = IDENTITIES[idKey];
  S.identity = idKey;
  S.money = START_MONEY; S.startMoney = START_MONEY;
  S.alert = id.alert; S.credit = id.credit;
  S.criminal = 0; S.family = id.family;
  S.dealt = []; S.log = []; S.round = 0;
  S.scammed = 0; S.identified = 0; S.lostTotal = 0;
  S.chainPending = false; S.app = false; S.vacc = false;

  el(`<div class="identity-card">
    <div class="emoji">${id.icon}</div>
    <div class="name">你现在是：${idKey}</div>
    <div class="desc">${esc(id.desc)}<br>
      钱包里有 <b>${fmt(S.money)}</b></div>
  </div>
  <p style="text-align:center;color:var(--muted);font-size:12px;line-height:1.9">
    接下来随机给你推 ${TOTAL_ROUNDS} 个局。<br>
    局中只给你看结果，对错和原因留到最后一次说清。<br>
    <span style="color:var(--danger)">钱包输光就提前结束。</span>
  </p>
  <button class="btn primary" onclick="window.__G.nextRound()">🔕 手机响了，开始 →</button>`);
}

/* ============ 事件抽取：随机 + 身份权重 ============ */
function pickEvent(){
  // 连环追损优先（chain 事件可重复触发，不受 dealt 限制）
  if(S.chainPending){
    S.chainPending = false;
    const c = EVENTS.find(e=>e.arch==='chain');
    if(c) return c;
  }
  const pool = EVENTS.filter(e=>!S.dealt.includes(e.id) && e.arch!=='chain'
    && !(e.arch==='tool'&&S.app) && !(e.arch==='familytool'&&S.vacc));
  if(!pool.length) return null;
  const best = pickOne(pool);
  S.dealt.push(best.id);
  return best;
}

/* ============ 场景渲染：拟物 ============ */
function renderSceneHead(ev){
  return `<div class="scene-head">
    <span class="ch">${esc(ev.ch||'💬 消息')}</span>
    <span class="meta">${esc(ev.meta||'')}</span>
  </div>`;
}

function isChatScene(ev){
  const ch = ev.ch || '';
  return ch.includes('群') || ch.includes('私信') || ch.includes('微信') || ch.includes('好友')
      || ch.includes('闲鱼') || ch.includes('家庭群') || ch.includes('投资群');
}
function isCallScene(ev){
  const ch = ev.ch || '';
  return ch.includes('来电') || ch.includes('电话');
}
function isSmsScene(ev){
  const ch = ev.ch || '';
  return ch.includes('短信') || ch.includes('通知');
}
function isLiveScene(ev){
  const ch = ev.ch || '';
  return ch.includes('直播');
}

function renderLines(ev){
  const lines = ev.lines || [];
  if(isCallScene(ev)){
    // 来电界面 + 后续以"对方说"形式展开
    const rest = lines.slice(1);
    let html = `<div class="call">
      <div class="from">来自：${esc(ev.meta||'未知号码')}</div>
      <div class="num">${esc(lines[0]||'境外来电')}</div>
      <div class="danger-tag">⚠️ 境外号码 · 标记为高频呼叫</div>
      <div style="margin-top:14px;font-size:13px;color:#cfd8e3;line-height:1.8">对方在电话里说：</div>
    </div>`;
    rest.forEach(t=>{ html += `<div class="wx"><div class="wx-row"><div class="avatar">📞</div><div class="wx-bubble">${esc(t)}</div></div></div>`; });
    return html;
  }
  if(isLiveScene(ev)){
    let html = `<div class="live">
      <div class="room">● LIVE · 在线 ${Math.floor(2000+rnd()*30000)} 人</div>`;
    lines.forEach((t,i)=>{
      if(i===0) html += `<div class="host">🎙️ 主播：${esc(t)}</div>`;
      else html += `<div class="host">🎙️ ${esc(t)}</div>`;
    });
    html += `<div class="danmu">
      <span>@路过的人：上车了</span><span>@老粉：跟着老师稳</span><span>@小明：刚提现 5 万</span><br>
      <span>@匿名：真的假的？</span><span>@理财小白：求带</span>
    </div></div>`;
    return html;
  }
  if(isSmsScene(ev)){
    let html = `<div class="sms">`;
    lines.forEach(t=>{
      html += `<div class="sms-row"><div class="who">${esc(ev.ch||'通知')}</div><div class="b">${esc(t)}</div></div>`;
    });
    html += `</div>`;
    return html;
  }
  // 默认：微信群聊
  let html = `<div class="wx">`;
  lines.forEach(t=>{
    if(t.startsWith('§')){
      html += `<div style="text-align:center;color:#999;font-size:11px;margin:10px 0">— ${esc(t.slice(1))} —</div>`;
    } else {
      html += `<div class="wx-row"><div class="avatar">👤</div><div class="wx-bubble">${esc(t)}</div></div>`;
    }
  });
  html += `</div>`;
  return html;
}

/* ============ 回合流程：聊天窗口 ============ */
function scrollDown(){
  const m = document.getElementById('chatMsgs');
  if(m) m.scrollTop = m.scrollHeight;
}
function appendMsg(html){
  const m = document.getElementById('chatMsgs');
  if(m){ m.insertAdjacentHTML('beforeend', html); scrollDown(); }
}
function myBubble(text){
  return `<div class="wx-row me"><div class="avatar">我</div><div class="wx-bubble">${esc(text)}</div></div>`;
}

function barHTML(){
  return `<div class="topbar">
      <span>💰 <b style="${S.money<0?'color:var(--danger)':''}">${fmt(S.money)}</b></span>
      <span>🧠 ${S.alert}</span>
      <span>⚖️ ${S.criminal}</span>
      <a class="top-link" href="${BACK_URL}" title="回到《人间防骗指南》">📖 指南</a>
      <button onclick="toggleTheme()">${document.documentElement.classList.contains('dark')?'☀️':'🌙'}</button>
    </div>`;
}

function nextRound(){
  // 第一次进来初始化钱包
  if(typeof S.money !== 'number'){
    S.money = START_MONEY; S.startMoney = START_MONEY;
    S.alert = 40; S.criminal = 0; S.credit = 80;
    S.dealt = []; S.log = []; S.round = 0;
    S.scammed = 0; S.identified = 0; S.lostTotal = 0;
    S.chainPending = false; S.app = false; S.vacc = false;
  }
  if(typeof S.round !== 'number') S.round = 0;
  // 结束条件：钱输光 / 12 局走完 —— 都只在最后给解析
  if(S.money <= 0) return ending();
  if(S.round >= TOTAL_ROUNDS) return review();
  const ev = pickEvent();
  if(!ev){
    el(`<div class="card" style="text-align:center;padding:30px">
      <h2>所有骗局都遇到过了</h2>
      <p style="color:var(--muted);font-size:13px">看总结吧。</p>
      <button class="btn primary" onclick="window.__G.review()">📋 看总结 →</button>
      <button class="btn" onclick="window.__G.start()">🔄 重新开始</button>
    </div>`);
    return;
  }
  CUR = ev; CUR.li = 0; CUR._escalate = 0;

  el(`<div class="chat-wrap">
    ${barHTML()}
    <div style="text-align:center;color:var(--muted);font-size:11px;letter-spacing:2px;margin:6px 0">
      第 ${Math.min(S.round+1, TOTAL_ROUNDS)} / ${TOTAL_ROUNDS} 局
    </div>
    <div class="chat-msgs" id="chatMsgs">
      ${ev.arch==='chain' ? `<div style="text-align:center;color:var(--muted);font-size:11px;margin:8px 0">— 当晚，一个陌生好友主动加了你 —</div>` : ''}
      ${renderLines(ev)}
    </div>
    <div class="chat-bar" id="chatBar"></div>
  </div>`);
  scrollDown();
  showChoices();
}

function showChoices(){
  const bar = document.getElementById('chatBar');
  if(CUR.arch==='real'){
    bar.innerHTML = `
      <button class="btn" onclick="window.__G.onReal(true,'${esc(CUR.hook_label||'走官方渠道试试').replace(/'/g,"\\'")}')">${esc(CUR.hook_label||'走官方渠道试试')}</button>
      <button class="btn" onclick="window.__G.onReal(false,'太麻烦，算了')">太麻烦，算了</button>`;
    return;
  }
  if(CUR.arch==='tool'){
    bar.innerHTML = `
      <button class="btn" onclick="window.__G.onTool(true,'📱 当场安装')">📱 当场安装</button>
      <button class="btn" onclick="window.__G.onTool(false,'不用了，我小心点')">不用了，我小心点</button>`;
    return;
  }
  if(CUR.arch==='familytool'){
    bar.innerHTML = `
      <button class="btn" onclick="window.__G.onFamily(true,'💉 转到家庭群')">💉 转到家庭群</button>
      <button class="btn" onclick="window.__G.onFamily(false,'下次再说')">下次再说</button>`;
    return;
  }
  // 骗局卡：1 正解 + 3 迷惑项，打散。每个 distractor 带自己的 back（对方回应）
  const opts = [{t:CUR.correct, ok:true, back:null, src:0}]
    .concat((CUR.distractors||[]).map((d,di)=>({t:d.t, ok:false, back:d.back, src:di+1})));
  const mixed = shuffle(opts);
  mixed.forEach((o,i)=>{ o._i = i; });
  bar.innerHTML = mixed.map(o=>
    `<button class="btn" data-ok="${o.ok?1:0}" data-i="${o._i}" data-src="${o.src}" onclick="window.__G.pick(${o.ok?1:0},'${esc(o.t).replace(/'/g,"\\'")}', ${o._i})">${esc(o.t)}</button>`).join('');
  CUR._mixed = mixed;
}

function onReal(ok, choiceText){
  appendMsg(myBubble(choiceText));
  const reply = rp(0, ok?0:1);
  if(ok){ S.money += 200; S.alert += 3; floatText('+¥200', true); }
  appendMsg(`<div class="wx-row"><div class="avatar">${ok?'📱':'🚶'}</div><div class="wx-bubble">${esc(reply)}</div></div>`);
  S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
    choice: choiceText, result: reply,
    correct: CUR.hook_label||CUR.correct, bad:!ok, guard:CUR.guard, news:CUR.news, loss:0});
  showAfterTurn();
}
function onTool(ok, choiceText){
  appendMsg(myBubble(choiceText));
  const reply = rp(0, ok?0:1);
  if(ok){ S.app = true; S.alert += 6; floatText('装备+1', true); }
  appendMsg(`<div class="wx-row"><div class="avatar">${ok?'📱':'🚶'}</div><div class="wx-bubble">${esc(reply)}</div></div>`);
  S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
    choice: choiceText, result: reply,
    correct:'当场安装', bad:!ok, guard:CUR.guard, news:CUR.news, loss:0});
  showAfterTurn();
}
function onFamily(ok, choiceText){
  appendMsg(myBubble(choiceText));
  const reply = rp(0, ok?0:1);
  if(ok){ S.vacc = true; S.family = Math.min(100,S.family+15); }
  appendMsg(`<div class="wx-row"><div class="avatar">${ok?'👨‍👩‍👧':'🚶'}</div><div class="wx-bubble">${esc(reply)}</div></div>`);
  S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
    choice: choiceText, result: reply,
    correct:'转到家庭群', bad:!ok, guard:CUR.guard, news:CUR.news, loss:0});
  showAfterTurn();
}

function pick(ok, choiceText, mi){
  appendMsg(myBubble(choiceText));
  // 找到这个选项对应的对方回应
  const picked = (CUR._mixed||[])[mi] || null;
  const back = picked && picked.back ? picked.back : '';

  // 反诈 App 拦截
  if(!ok && S.app && ['authority','refund','parttime','chain'].includes(CUR.arch) && rnd()<0.4){
    S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
      choice:choiceText, result:'手机弹出预警，没转成账。',
      correct:CUR.correct, bad:false, guard:CUR.guard, news:CUR.news, loss:0});
    appendMsg(`<div class="wx-row"><div class="avatar">📱</div><div class="wx-bubble">反诈 App 预警：这个号码被标记为涉诈。</div></div>`);
    floatText('📱 拦截', true);
    showAfterTurn('继续 →');
    return;
  }
  if(ok){
    S.identified++; S.alert += CUR.alert_win||8;
    const reply = rp(1);
    S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
      choice:choiceText, result: reply,
      correct:CUR.correct, bad:false, guard:CUR.guard, news:CUR.news, loss:0});
    appendMsg(`<div class="wx-row"><div class="avatar">✅</div><div class="wx-bubble">${esc(reply)}</div></div>`);
    showAfterTurn('继续 →');
    return;
  }
  // 选错 → 用这个选项专属的对方回应
  appendMsg(`<div class="wx-row"><div class="avatar">👤</div><div class="wx-bubble">${esc(back)}</div></div>`);
  showStage2();
}

function showStage2(){
  const bar = document.getElementById('chatBar');
  const opts = (CUR.s2opts||[]).map((o,i)=>({t:o[0], m:o[1], i:i}));
  bar.innerHTML = `<p style="font-size:12px;color:var(--muted);margin:0 0 4px">${esc(CUR.s2prompt||'现在怎么办：')}</p>` +
    shuffle(opts).map(o=>
      `<button class="btn" data-stage="2" data-i="${o.i}" onclick="window.__G.trap(${o.m},'${esc(o.t).replace(/'/g,"\\'")}',2,${o.i})">${esc(o.t)}</button>`).join('');
  scrollDown();
}

function showAfterTurn(){
  // 局中不解析：只让玩家看到"结果"，对错与原因全部留到最后的复盘
  const bar = document.getElementById('chatBar');
  bar.innerHTML = `<button class="btn primary" onclick="window.__G.afterTurn()">继续 →</button>`;
  scrollDown();
}

function afterTurn(){
  S.round = (S.round||0) + 1;
  nextRound();
}

function trap(loss, label, stage, i, step){
  appendMsg(myBubble(label));
  loss = Math.max(0, Math.round(loss));

  // 钱不够 → 弹出借钱选择，不直接扣
  if(loss > S.money && loss > 0){
    appendMsg(`<div class="wx-row"><div class="avatar">💳</div><div class="wx-bubble">对方发来借钱链接："钱不够没关系，我们有合作的借款平台，秒到账。"</div></div>`);
    const bar = document.getElementById('chatBar');
    bar.innerHTML = `<p style="font-size:12px;color:var(--danger);margin:0 0 4px">你还差 ${fmt(loss - S.money)}：</p>
      <button class="btn" onclick="window.__G.borrowAndTrap(${loss},'${esc(label).replace(/'/g,"\\'")}',${stage},${i},${step==null?'null':step})">借钱补窟窿（借 ${fmt(loss - S.money)}）</button>
      <button class="btn" onclick="window.__G.trap(0,'不借了，止损',9)">不借了，止损</button>`;
    scrollDown();
    return;
  }

  doTrap(loss, label, false, rp(stage, i, step));
}

function borrowAndTrap(loss, label, stage, i, step){
  appendMsg(myBubble(`借钱补窟窿`));
  const short = Math.max(0, loss - S.money);
  S.money += short;              // 借来的钱先到账，再被对方拿走
  S.debt = (S.debt||0) + short;
  doTrap(loss, label, true, rp(stage, i, step));
}

function doTrap(loss, label, borrowed, reply){
  const ev = CUR;
  S.money -= loss; S.lostTotal += loss; S.alert += 2;
  if(loss>0) floatText('-'+fmt(loss), false);
  if(ev.criminal) S.criminal += ev.criminal;
  if(ev.credit) S.credit = Math.max(0, S.credit + ev.credit);

  // 这个选项专属的现场回应（不写分析，分析留到复盘）
  appendMsg(`<div class="wx-row"><div class="avatar">${loss>0?'💸':'🚪'}</div><div class="wx-bubble">${esc(reply)}</div></div>`);

  // 同一个局里被连续加码：只记一条，损失累加（复盘按"局"计，不按点击次数计）
  const last = S.log[S.log.length-1];
  if(last && last.eid === ev.id){
    last.loss += loss;
    last.choice += ' → ' + label;
    last.result = (last.result ? last.result + ' ' : '') + reply;
    if(loss > 0) last.bad = true;
  } else {
    if(loss > 0) S.scammed++;
    S.log.push({eid:ev.id, title:ev.title, cat:ev.cat, arch:ev.arch,
      choice:label, result:reply, correct:ev.correct, bad:loss>0,
      guard:ev.guard, news:ev.news, loss:loss});
  }

  if(loss>0){
    appendMsg(`<div class="wx-row"><div class="avatar">🏦</div><div class="wx-bubble">账户少了 <b>${fmt(loss)}</b>${borrowed?`（其中 <b style="color:var(--danger)">借的钱</b>）`:''}。</div></div>`);
  }

  // 更新顶部钱显示
  const topbar = document.querySelector('.topbar');
  if(topbar) topbar.outerHTML = barHTML();

  // 止损：这一局到此为止
  if(loss === 0){ showAfterTurn(); return; }

  // 层层加码：每个局都写好了两轮，每轮两个选项各有自己的回应
  CUR._escalate = (CUR._escalate || 0) + 1;
  if(CUR._escalate <= (ev.escalate||[]).length){
    showEscalate();
  } else {
    blackout();
  }
}

function blackout(){
  appendMsg(`<div class="wx-row"><div class="avatar">🚫</div><div class="wx-bubble">对方把你拉黑了，群也把你踢了。</div></div>`);
  if(rnd() < 0.6){
    S.chainPending = true;
    appendMsg(`<div class="wx-row"><div class="avatar">📱</div><div class="wx-bubble">当晚，一个陌生好友加了你："看到你之前报过案，我们专做追损，先帮你追回再说。"</div></div>`);
  }
  showAfterTurn();
}

function showEscalate(){
  const round = CUR._escalate;                       // 1,2（每个局都写满了，不用兜底话术）
  const bar = document.getElementById('chatBar');
  const step = (CUR.escalate || [])[round-1];
  if(!step){ return blackout(); }
  appendMsg(`<div class="wx-row"><div class="avatar">👤</div><div class="wx-bubble">${esc(step.back)}</div></div>`);
  const opts = step.opts.map((o,i)=>({t:o[0], m:o[1], i:i}));
  bar.innerHTML = `<p style="font-size:12px;color:var(--muted);margin:0 0 4px">对方还在催（第 ${round} 轮）：</p>` +
    shuffle(opts).map(o=>
      `<button class="btn" data-stage="3" data-i="${o.i}" onclick="window.__G.trap(${o.m},'${esc(o.t).replace(/'/g,"\\'")}',3,${o.i},${round-1})">${esc(o.t)}</button>`).join('');
  scrollDown();
}

/* ============ 结局（钱输光） + 复盘 ============ */
function ending(){
  const bad = S.log.filter(l=>l.bad);
  const ok = S.log.filter(l=>!l.bad);
  el(`<h1 style="text-align:center;margin:24px 0 6px">💸 钱包输光了</h1>
  <p style="text-align:center;color:var(--muted);font-size:13px">从 ${fmt(START_MONEY)} 到 ${fmt(Math.max(0,S.money))}${S.debt?` · 还欠 ${fmt(S.debt)}`:''}</p>
  <div style="text-align:center;margin:14px 0"><span class="badge bad">「被割了」</span></div>
  <div class="kpis">
    <div class="kpi"><b style="color:var(--danger)">${bad.length}</b><span>中招次数</span></div>
    <div class="kpi"><b style="color:var(--brand)">${ok.length}</b><span>顶住次数</span></div>
    <div class="kpi"><b style="color:var(--danger)">${fmt(S.lostTotal)}</b><span>累计损失</span></div>
    <div class="kpi"><b>${S.criminal}</b><span>刑责分</span></div>
  </div>
  <div style="margin:16px 0">
    <h3 style="font-size:15px;margin-bottom:8px">你参与的骗局：</h3>
    ${S.log.map((l,i)=>`<div class="rv ${l.bad?'bad':''}">
      <b>${i+1}. ${esc(l.title)}</b>
      <div style="font-size:12px;color:var(--muted);margin:2px 0">${esc(l.cat||'')}</div>
      <div>你选的：<span class="${l.bad?'no':'ok'}">${esc(l.choice)}</span></div>
      ${l.bad ? `<div style="margin-top:4px">正确做法：<span class="ok">${esc(l.correct)}</span></div>` : ''}
      <span class="gd">📌 ${esc(l.guard||'')}</span>
    </div>`).join('')}
  </div>
  <div style="display:flex;gap:10px;margin-top:14px">
    <button class="btn primary" onclick="window.__G.start()">🔄 再来一次（重置 ¥${START_MONEY.toLocaleString()}）</button>
  </div>
  <div style="text-align:center;margin-top:12px"><a class="back-link" href="${BACK_URL}">📖 回到《人间防骗指南》</a></div>
  <footer>取材自《人间防骗指南》· 遇真实诈骗：110 / 96110</footer>`);
}

function review(){
  const bad = S.log.filter(l=>l.bad);
  const ok = S.log.filter(l=>!l.bad);
  const g = {};
  bad.forEach(l=>{ const c=l.cat||'其他'; g[c]=g[c]||{n:0,s:0}; g[c].n++; g[c].s+=(l.loss||0); });
  const top = Object.entries(g).sort((a,b)=>b[1].s-a[1].s).slice(0,3);
  let summary = '';
  if(!bad.length){
    summary = `<div style="font-size:14px;line-height:1.9">✅ ${S.round} 个局，你一次都没上钩。<br>
      下面每一条，都是你当时顶住的那个瞬间——记住它，现实里用得上。</div>`;
  } else {
    summary = `<div style="font-size:14px;line-height:1.9">
      ❌ 你中招了 <b style="color:var(--danger)">${bad.length}</b> 次，共损失 <b style="color:var(--danger)">${fmt(S.lostTotal)}</b>。<br>
      下面每一条，告诉你当时该怎么做。</div>
      ${top.length?`<div style="margin-top:10px;padding-top:10px;border-top:1px dashed var(--line);font-size:13px;line-height:2">
        <b>你差在哪：</b><br>${top.map(([c,v])=>`· 「${esc(c)}」栽了 ${v.n} 次${v.s?`，亏 ${fmt(v.s)}`:''}`).join('<br>')}
        <br><span style="color:var(--muted)">补课顺序就按上面的排序来。</span></div>`:''}`;
  }
  const rows = S.log.map((l,i)=>`<div class="rv ${l.bad?'bad':''}">
    <b>${i+1}. ${esc(l.title)}</b>
    <div style="font-size:12px;color:var(--muted);margin:2px 0">${esc(l.cat||'')}</div>
    <div>你选的：<span class="${l.bad?'no':'ok'}">${esc(l.choice)}</span></div>
    <div style="font-size:13px;color:var(--muted);margin-top:3px">结果：${esc(l.result)}</div>
    ${l.bad ? `<div style="margin-top:4px">当时正确的做法：<span class="ok">${esc(l.correct)}</span></div>` : ''}
    <span class="gd">📌 ${esc(l.guard||'')}</span>
    ${l.news?`<a href="${esc(l.news.u)}" target="_blank" rel="noopener">📎 同类真实案例：${esc(l.news.t)}</a>`:''}
  </div>`).join('');

  el(`<h1 style="text-align:center;margin:20px 0 4px">复盘</h1>
  <p style="text-align:center;color:var(--muted);font-size:13px;margin:0 0 12px">
    ${S.money<=0?`钱包在第 ${S.round} 个局输光`:`${S.round} 个局全部走完`} · 中招 ${bad.length} 次 · 顶住 ${ok.length} 次
  </p>
  <div class="card">${summary}</div>
  ${rows}
  <div style="display:flex;gap:10px;margin-top:14px">
    <button class="btn primary" onclick="window.__G.newGame()">🎲 再来一局</button>
    <button class="btn" onclick="window.__G.start()">回到首页</button>
  </div>
  <div style="text-align:center;margin-top:12px"><a class="back-link" href="${BACK_URL}">📖 回到《人间防骗指南》</a></div>
  <footer>取材自《人间防骗指南》· github.com/QERSSD/HowToAvoidScams</footer>`);
}

// 暴露
window.__G = { start, begin,
  newGame: function(){ for(const k in S) delete S[k]; return begin(pickOne(Object.keys(IDENTITIES))); },
  nextRound, pick, onReal, onTool, onFamily, trap, borrowAndTrap, afterTurn, review, ending,
  state: function(){ return S; }, cur: function(){ return CUR; } };
window.toggleTheme = toggleTheme;
start();
})();
