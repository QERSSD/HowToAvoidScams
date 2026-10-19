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
  <div style="text-align:center">
    <button class="btn primary" style="font-size:16px;padding:14px 32px" onclick="window.__G.nextRound()">🔕 手机响了，开始 →</button>
  </div>
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
    <div class="topbar">
      <span>💰 <b>${fmt(S.money)}</b></span>
      <span>🧠 ${S.alert}</span>
      <span>⚖️ ${S.criminal}</span>
      <button onclick="toggleTheme()">${document.documentElement.classList.contains('dark')?'☀️':'🌙'}</button>
    </div>
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
  const opts = [{t:CUR.correct, ok:true, back:null}]
    .concat((CUR.distractors||[]).map(d=>({t:d.t, ok:false, back:d.back})));
  const mixed = shuffle(opts);
  mixed.forEach((o,i)=>{ o._i = i; });
  bar.innerHTML = mixed.map(o=>
    `<button class="btn" onclick="window.__G.pick(${o.ok?1:0},'${esc(o.t).replace(/'/g,"\\'")}', ${o._i})">${esc(o.t)}</button>`).join('');
  CUR._mixed = mixed;
}

function onReal(ok, choiceText){
  appendMsg(myBubble(choiceText));
  if(ok){
    S.money += 200; S.alert += 3; floatText('+¥200', true);
    S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
      choice: choiceText, result:'走官方渠道试了，小钱到账。',
      correct: choiceText, bad:false, guard:CUR.guard, news:CUR.news, loss:0});
    appendMsg(`<div class="wx-row"><div class="avatar">📱</div><div class="wx-bubble">App 到账 ¥200。</div></div>`);
  } else {
    S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
      choice:choiceText, result:'没走。', correct:CUR.hook_label, bad:false, guard:CUR.guard, news:CUR.news, loss:0});
  }
  showAfterTurn('继续 →');
}
function onTool(ok, choiceText){
  appendMsg(myBubble(choiceText));
  if(ok){ S.app = true; S.alert += 6; floatText('装备+1', true); }
  S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
    choice: choiceText, result: ok?'装好了。':'继续裸奔。',
    correct:'当场安装', bad:!ok, guard:CUR.guard, news:CUR.news, loss:0});
  showAfterTurn('继续 →');
}
function onFamily(ok, choiceText){
  appendMsg(myBubble(choiceText));
  if(ok){ S.vacc = true; S.family = Math.min(100,S.family+15); }
  S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
    choice: choiceText, result: ok?'家人群里多了一条防骗文章。':'没转。',
    correct:'转到家庭群', bad:!ok, guard:CUR.guard, news:CUR.news, loss:0});
  showAfterTurn('继续 →');
}

function pick(ok, choiceText, mi){
  appendMsg(myBubble(choiceText));
  // 找到这个选项对应的对方回应
  const picked = (CUR._mixed||[])[mi] || null;
  const back = picked && picked.back ? picked.back : CUR.esc;

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
    S.log.push({title:CUR.title, cat:CUR.cat, arch:CUR.arch,
      choice:choiceText, result:'你挂了电话 / 退了群，去官方渠道查了一下，根本没这回事。',
      correct:CUR.correct, bad:false, guard:CUR.guard, news:CUR.news, loss:0});
    appendMsg(`<div class="wx-row"><div class="avatar">✅</div><div class="wx-bubble">官方渠道查了一下，根本没这回事。</div></div>`);
    showAfterTurn('继续 →');
    return;
  }
  // 选错 → 用这个选项专属的对方回应
  appendMsg(`<div class="wx-row"><div class="avatar">👤</div><div class="wx-bubble">${esc(back||'对方继续催你。')}</div></div>`);
  showStage2();
}

function showStage2(){
  const bar = document.getElementById('chatBar');
  const opts = (CUR.s2opts||[]).map(o=>({t:o[0], m:o[1]}));
  bar.innerHTML = `<p style="font-size:12px;color:var(--muted);margin:0 0 4px">${esc(CUR.s2prompt||'现在怎么办：')}</p>` +
    shuffle(opts).map(o=>
      `<button class="btn" onclick="window.__G.trap(${o.m},'${esc(o.t).replace(/'/g,"\\'")}')">${esc(o.t)}</button>`).join('');
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

function trap(loss, label){
  appendMsg(myBubble(label));
  const ev = CUR;
  loss = Math.max(0, Math.round(loss));

  // 钱不够 → 弹出借钱选择，不直接扣
  if(loss > S.money && loss > 0){
    appendMsg(`<div class="wx-row"><div class="avatar">💳</div><div class="wx-bubble">对方发来借钱链接："钱不够没关系，我们有合作的借款平台，秒到账。"</div></div>`);
    const bar = document.getElementById('chatBar');
    bar.innerHTML = `<p style="font-size:12px;color:var(--danger);margin:0 0 4px">你还差 ${fmt(loss - S.money)}：</p>
      <button class="btn" onclick="window.__G.borrowAndTrap(${loss},'${esc(label).replace(/'/g,"\\'")}')">借钱补窟窿（借 ${fmt(loss - S.money)}）</button>
      <button class="btn" onclick="window.__G.trap(0,'不借了，止损')">不借了，止损</button>`;
    scrollDown();
    return;
  }

  doTrap(loss, label, false);
}

function borrowAndTrap(loss, label){
  appendMsg(myBubble(`借钱补窟窿`));
  const short = Math.max(0, loss - S.money);
  S.money += short;              // 借来的钱先到账，再被对方拿走
  S.debt = (S.debt||0) + short;
  doTrap(loss, label, true);
}

function doTrap(loss, label, borrowed){
  const ev = CUR;
  let extra = '';
  S.money -= loss; S.lostTotal += loss; S.alert += 2;
  if(loss>0) floatText('-'+fmt(loss), false);
  if(ev.criminal){ S.criminal += ev.criminal; extra += `⚖️ 关联记录 +${ev.criminal}；`; }
  if(ev.credit){ S.credit = Math.max(0, S.credit + ev.credit); extra += `📇 信用 ${ev.credit}；`; }

  // 同一个局里被连续加码：只记一条，损失累加（复盘按"局"计，不按点击次数计）
  const wakeWords = ['挂断','挂掉','挂电话','报警','打110','拉黑','不去','取消','关掉','退出','拒绝共享','不玩了','不领了','停止聊天','不借了'];
  const isRealWake = loss === 0 && wakeWords.some(w=>label.includes(w));
  const last = S.log[S.log.length-1];
  if(last && last.eid === ev.id){
    last.loss += loss;
    last.choice += ' → ' + label;
    if(loss > 0){
      last.bad = true;
      last.result = `${extra}对方收了钱，回复越来越慢。${borrowed?'又借了钱补窟窿。':''}`;
    }
  } else {
    if(!isRealWake) S.scammed++;
    S.log.push({eid:ev.id, title:ev.title, cat:ev.cat, arch:ev.arch,
      choice:label,
      result: isRealWake ? '你及时止损，没有再掏钱。' : `${extra}对方收了钱，回复越来越慢。${borrowed?'你借了钱补窟窿。':''}`,
      correct:ev.correct, bad:!isRealWake, guard:ev.guard, news:ev.news, loss:loss});
  }

  if(loss>0) appendMsg(`<div class="wx-row"><div class="avatar">💸</div><div class="wx-bubble">账户少了 <b>${fmt(loss)}</b>${borrowed?`（其中 <b style="color:var(--danger)">借的钱</b>）`:''}。</div></div>`);

  // 更新顶部钱显示
  const topbar = document.querySelector('.topbar');
  if(topbar) topbar.innerHTML =
    `<span>💰 <b style="${S.money<0?'color:var(--danger)':''}">${fmt(S.money)}</b></span><span>🧠 ${S.alert}</span><span>⚖️ ${S.criminal}</span><button onclick="toggleTheme()">${document.documentElement.classList.contains('dark')?'☀️':'🌙'}</button>`;

  // 选了醒悟选项
  if(loss === 0){
    if(isRealWake){
      appendMsg(`<div class="wx-row"><div class="avatar">✅</div><div class="wx-bubble">你选择了止损，不再理会对方。</div></div>`);
      showAfterTurn();
      return;
    }
    const archWords = {
      refund: '理赔', authority: '案子', invest: '投资', gambling: '提现',
      romance: '你们的钱', loan: '贷款', chain: '追损', parttime: '佣金',
      bangxin: '流水', shopping: '退款', account: '账号', job: '签证',
      freegift: '放款', familytool: '疗程',
    };
    const word = archWords[CUR.arch] || '你的钱';
    const fakeReplies = {
      '让家人帮我查': `对方："家人查不到内部系统的，他们以为是诈骗挂了电话就完了，你的${word}就没人管了。"`,
      '找客服投诉': '客服："投诉要经理审批，经理下班了。你再充一笔流水到 VIP 客户，我让经理现在给你处理。"',
      '找闲鱼官方客服': '"客服"："官方客服下班了，你必须交保证金我才能给你处理，不然交易取消你钱货两空。"',
      '让买家自己联系快递改': '"客服"："买家说是你这边没改，快递不认。你必须交 2000 保证金我才能给你改地址。"',
      '把卡要回来': '对方："卡已经激活了，现在注销要赔违约金 5000。你再走两笔流水，佣金够赔了再还你。"',
      '要求退服务费': '"律师"："退钱要走法院程序，再交 3000 诉讼费才能立案退钱。"',
      '要求退钱': '"律师"："退钱要走法院程序，再交 3000 诉讼费才能立案退钱。"',
      '让 TA 自己操作别找我': `TA："我手机被限额了，你不帮我我就提现不了，你之前投的${word}也拿不回来。"`,
      '问朋友意见': '对方："朋友又不懂这个，他们只会劝你别干。机会不等人，先转一笔锁定名额。"',
      '让朋友帮我领': '"客服"："必须本人账号领，代领算违规会被封号。你自己扫码登录验证一下。"',
      '加对方微信问清楚': '对方微信："电话里说不清楚，你先转 1000 保证金，我发你正式合同。"',
      '退款不喝了': '"客服"："退款要扣 30% 手续费，再买一疗程我给你申请全额退款。"',
      '找大使馆': '对方："大使馆不管这事，你先交违约金才能走，不然不让你出园区。"',
      '反正包机票': 'HR："好，那你明天来公司面个试，先交 3000 安置费，机票签证马上订。"',
      '问清楚具体走多少': '对方："一天走个三五万吧，看你时间。你先把卡号给我，打一笔试试。"',
      '只借这一张': '对方："好，那你把卡号告诉我，我让人打一笔进来，你再转到指定账户。"',
      '先借一张': '对方："好，那你把卡号告诉我，我让人打一笔进来，你再转到指定账户。"',
      '把工资卡': '对方："好，那你把工资卡号也给我，佣金翻倍打你卡上。"',
      '接个电话听听': '对方："您好，您的快递丢了，我们给您理赔，您报一下银行卡号。"',
      '输入验证码': '"客服"："验证码是动态的，我念你输，把收到的 6 位数告诉我。"',
      '介绍给邻居': '对方："好，那你先把邻居那份钱一起交了，我给你两个优惠名额。"',
      '去办张新卡': '对方："好，你去银行办张新卡，办好拍给我，佣金翻倍。"',
    };
    let reply = '';
    for(const k in fakeReplies){
      if(label.includes(k)){ reply = fakeReplies[k]; break; }
    }
    if(!reply){
      const archReplies = {
        parttime: '对方："好，那你先做这一单，佣金做完立刻返你。"',
        bangxin: '对方："好，那你把卡号给我，我让人打一笔进来。"',
        shopping: '"客服"："好，那你按我说的操作，交保证金就能继续交易。"',
        invest: '老师："好，那你先充一笔试试，赚了就知道我没骗你。"',
        gambling: '客服："好，那你先充一笔解锁提现，赢了就知道平台是真的。"',
        romance: 'TA："好，那你先帮我操作这一笔，赚了我们一起提现。"',
        loan: '客服："好，那你按我说的交解冻金，贷款马上到账。"',
        refund: '客服："好，那你按我说的去 ATM 操作，理赔马上打你卡上。"',
        account: '"客服"："好，那你扫码登录验证一下，皮肤马上发到你账号。"',
        job: 'HR："好，那你明天来公司，先交安置费，机票签证马上订。"',
        freegift: '对方："好，那你按我说的交手续费，钱马上打你卡上。"',
        authority: '对方："好，那你按指引把钱转到安全账户，清查完就退你。"',
        chain: '"律师"："好，那你先交诉讼费，案子马上立案。"',
        familytool: '姑姑："好，那你按群里的链接下单，我帮你申请优惠。"',
      };
      reply = archReplies[CUR.arch] || '对方："好，那你按我说的操作，马上就能搞定。"';
    }
    appendMsg(`<div class="wx-row"><div class="avatar">👤</div><div class="wx-bubble">${esc(reply)}</div></div>`);
  }

  // 层层加码
  CUR._escalate = (CUR._escalate || 0) + 1;
  if(CUR._escalate < 5){
    showEscalate();
  } else {
    appendMsg(`<div class="wx-row"><div class="avatar">🚫</div><div class="wx-bubble">对方把你拉黑了，群也把你踢了。</div></div>`);
    if(rnd() < 0.6){
      S.chainPending = true;
      appendMsg(`<div class="wx-row"><div class="avatar">📱</div><div class="wx-bubble">当晚，一个陌生好友加了你："看到你之前报过案，我们专做追损，先帮你追回再说。"</div></div>`);
    }
    showAfterTurn();
  }
}

function showEscalate(){
  const round = CUR._escalate;  // 1,2,3,4
  const bar = document.getElementById('chatBar');
  const step = (CUR.escalate || [])[round-1];
  if(!step){
    // 通用兜底：根据 arch 生成加码话术
    const arch = CUR.arch;
    const generic = {
      parttime: ['对方："最后一单了，做完这单全部返你，再凑 1000。"', [['再凑 1000 收尾', 1000], ['报警', 0]]],
      bangxin: ['对方："流水还不够，再转 5000 过来走最后一笔。"', [['再转 5000', 5000], ['报警', 0]]],
      shopping: ['"客服"："最后一步，交 3000 通道费就能退款。"', [['交 3000 通道费', 3000], ['找平台', 0]]],
      invest: ['老师："最后一次机会，再充 10000 翻本。"', [['再充 10000', 10000], ['退群', 0]]],
      gambling: ['客服："最后一次解冻，再交 8000 就能全部提现。"', [['再交 8000', 8000], ['报警', 0]]],
      romance: ['TA："我把全部积蓄都投进去了，你再不补我就完了。再打 10000 过来。"', [['再打 10000', 10000], ['拉黑', 0]]],
      loan: ['客服："最后一步，再交 20000 验资就能放款。"', [['再交 20000 验资', 20000], ['取消', 0]]],
      refund: ['客服："最后一步，再交 5000 理赔服务费。"', [['交 5000 服务费', 5000], ['挂电话', 0]]],
      account: ['"客服"："最后一步，交 2000 账号保险费。"', [['交 2000 保险费', 2000], ['关页面', 0]]],
      job: ['HR："最后一步，交 5000 签证费就能出境。"', [['交 5000 签证费', 5000], ['不去了', 0]]],
      freegift: ['电话里："最后一步，交 1000 手续费就能放款。"', [['交 1000 手续费', 1000], ['挂电话', 0]]],
      authority: ['对方："最后一步，转 30000 到安全账户做结案保证金。"', [['转 30000 结案', 30000], ['打 110', 0]]],
      chain: ['"律师"："最后一步，再交 5000 执行费就能到账。"', [['再交 5000 执行费', 5000], ['报警', 0]]],
    };
    const g = generic[arch] || ['对方继续催你。', [['再补一笔', Math.round(S.money*0.2)], ['算了不玩了', 0]]];
    appendMsg(`<div class="wx-row"><div class="avatar">👤</div><div class="wx-bubble">${esc(g[0])}</div></div>`);
    bar.innerHTML = `<p style="font-size:12px;color:var(--muted);margin:0 0 4px">对方还在催（第 ${round} 轮）：</p>` +
      shuffle(g[1]).map(o=>
        `<button class="btn" onclick="window.__G.trap(${o[1]},'${esc(o[0]).replace(/'/g,"\\'")}')">${esc(o[0])}</button>`).join('');
    scrollDown();
    return;
  }
  appendMsg(`<div class="wx-row"><div class="avatar">👤</div><div class="wx-bubble">${esc(step.back)}</div></div>`);
  bar.innerHTML = `<p style="font-size:12px;color:var(--muted);margin:0 0 4px">对方还在催（第 ${round} 轮）：</p>` +
    shuffle(step.opts).map(o=>
      `<button class="btn" onclick="window.__G.trap(${o[1]},'${esc(o[0]).replace(/'/g,"\\'")}')">${esc(o[0])}</button>`).join('');
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
