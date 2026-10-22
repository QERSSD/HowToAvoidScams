/* 《识骗迷局》冒烟测试：用 jsdom 把单文件跑起来，点完一整关
   用法： NODE_PATH=<workspace>/node_modules node tools/test_murdoku.js
*/
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const FILE = path.join(__dirname, "..", "game", "murdoku.html");
const html = fs.readFileSync(FILE, "utf8");

let failed = 0;
function ok(cond, msg) {
  if (cond) console.log("  ✓ " + msg);
  else { console.log("  ✗ " + msg); failed++; }
}

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  url: "http://localhost/",
  pretendToBeVisual: true,
});

const w = dom.window, d = w.document;
w.onerror = (m) => { console.log("  ✗ 运行时错误：" + m); failed++; };

function q(sel) { return d.querySelector(sel); }
function qa(sel) { return [...d.querySelectorAll(sel)]; }

setTimeout(() => {
  try {
    console.log("== 首页 ==");
    const cards = qa(".card");
    ok(cards.length === 12, "首页 12 张关卡卡片（实际 " + cards.length + "）");
    ok(qa(".chap").length === 2, "两个章节");
    ok(q("#pagePlay").classList.contains("hidden"), "起始停在章节地图");

    console.log("== 进入第 1 关 ==");
    cards[0].click();
    ok(!q("#pagePlay").classList.contains("hidden"), "关卡页已显示");
    ok(qa("#grid .cell").length === 81, "网格 81 格（实际 " + qa("#grid .cell").length + "）");
    ok(qa("#people .p").length === 9, "底部九人名牌（实际 " + qa("#people .p").length + "）");

    const DATA = w.eval("DATA");
    const lv = DATA.levels[0];
    ok(lv.clues.length >= 6, "线索条数 " + lv.clues.length);
    ok(qa("#clues .clue").length === lv.clues.length, "线索卡渲染完整");

    // 硬规则：往已有人的同排落子必须被拦住
    const given = lv.given[0];
    const freeName = lv.roles.find(r => !lv.given.some(g => g.name === r.name)).name;
    qa("#people .p").find(p => p.querySelector(".n").textContent === freeName).click();
    const blockedCell = qa("#grid .cell").find(c => +c.dataset.r === given.r && +c.dataset.c !== given.c);
    blockedCell.click();
    ok(!blockedCell.querySelector(".nm"), "同排已有人的格子拒绝落子");

    function esc() { d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true })); }
    function findPerson(n) { return qa("#people .p").find(p => p.querySelector(".n").textContent === n); }
    function findCell(r, c) { return qa("#grid .cell").find(x => +x.dataset.r === r && +x.dataset.c === c); }
    function cellOf(n) {
      return qa("#grid .cell").find(c => c.querySelector(".nm") && c.querySelector(".nm").textContent === n);
    }
    function fillAll() {
      q("#clear").click();   // 回到开局给定的状态，避免残留
      esc();
      lv.roles.forEach(role => {
        if (lv.given.some(g => g.name === role.name)) return;
        const s = lv.sol[role.name];
        findPerson(role.name).click();
        findCell(s.r, s.c).click();     // 放到正确位置
        esc();
      });
    }

    // 按标准答案把所有没给定的人摆好
    fillAll();
    ok(+q("#cnt").textContent === 9, "九个人全部就位（实际 " + q("#cnt").textContent + "）");

    console.log("== 提交（先故意错一次）==");
    const zf = (r, c) => Math.floor(r / 3) * 3 + Math.floor(c / 3);
    // 造一个「行列区都合法、但不是答案」的完整摆法：先固定 given，其余回溯找非答案解
    function buildWrong() {
      const fixed = {}, usedR = new Set(), usedC = new Set(), usedZ = new Set();
      lv.given.forEach(g => { fixed[g.name] = { r: g.r, c: g.c };
        usedR.add(g.r); usedC.add(g.c); usedZ.add(zf(g.r, g.c)); });
      const rest = lv.roles.map(r => r.name).filter(n => !fixed[n]);
      const out = Object.assign({}, fixed);
      function bt(i) {
        if (i === rest.length) {
          return rest.some(n => out[n].r !== lv.sol[n].r || out[n].c !== lv.sol[n].c);
        }
        const n = rest[i];
        for (let r = 0; r < 9; r++) for (let c = 0; c < 9; c++) {
          const z = zf(r, c);
          if (usedR.has(r) || usedC.has(c) || usedZ.has(z)) continue;
          out[n] = { r, c }; usedR.add(r); usedC.add(c); usedZ.add(z);
          if (bt(i + 1)) return true;
          usedR.delete(r); usedC.delete(c); usedZ.delete(z);
        }
        return false;
      }
      return bt(0) ? out : null;
    }
    const wrong = buildWrong();
    ok(!!wrong, "能构造出“合法但不是答案”的摆法（证明唯一解不是靠规则本身）");
    if (wrong) {
      q("#clear").click();
      esc();
      lv.roles.forEach(role => {
        if (lv.given.some(g => g.name === role.name)) return;
        const p = wrong[role.name];
        findPerson(role.name).click();
        findCell(p.r, p.c).click();
        esc();
      });
      ok(+q("#cnt").textContent === 9, "错误摆法也摆满了九个人");
      q("#submit").click();
      ok(/有人站错了/.test(d.body.textContent), "摆错时只提示“有人站错了”，不指出是谁");
      ok(!/第 \d+ 排/.test(q("#modalHost").textContent), "错误判定不泄露坐标");
      ok(/算了，看答案/.test(d.body.textContent), "给“看答案”的退路");
      q("#modalHost").innerHTML = "";      // 关掉弹窗，回去重摆
    }

    // 还原成正确答案再交
    fillAll();
    q("#submit").click();
    ok(!!q("#goPick"), "正确答案 → 结案并出现“哪句话露了破绽”");

    console.log("== 破绽问答 + 复盘 ==");
    ok(!!q("#goPick"), "出现“哪句话露了破绽”入口");
    q("#goPick").click();
    ok(qa(".pick").length === 4, "四个候选句");
    qa(".pick")[lv.pick.answer].click();
    ok(/正是这句/.test(d.body.textContent), "答对给解析");
    q("#goReview2").click();
    ok(/结案复盘/.test(d.body.textContent), "进入复盘");
    ok(d.body.textContent.includes(lv.review.guard), "复盘里有防身金句");
    ok(d.body.textContent.includes("第 " + lv.article + " 篇"), "复盘标了原文出处");

    console.log("== 存档与关卡推进 ==");
    const save = JSON.parse(w.localStorage.getItem("shimian.save.v1") || "{}");
    ok(!!save[lv.id] && save[lv.id].solved === true, "本机存档记录了结案");
    ok(!!save[lv.id].stars, "记录了星级 " + save[lv.id].stars);
    const next = q("#nextLv");
    ok(!!next, "提供下一关入口");
    next.click();
    ok(/第 2 关|《拆不完的手串》|拆不完的手串/.test(d.body.textContent), "进入下一关");

    console.log("== 线索勾选 / 提示 / 清空 ==");
    qa("#clues .clue")[0].click();
    ok(qa("#clues .clue")[0].classList.contains("used"), "线索可以勾成“已用”");
    q("#hint").click();
    ok(!!q(".hintbox"), "提示能弹出来");
    q("#clear").click();
    ok(+q("#cnt").textContent === 3, "清空后回到开局给定的 3 人");
  } catch (e) {
    console.log("  ✗ 测试异常：" + e.stack);
    failed++;
  }
  console.log(failed ? "\n✗ 失败 " + failed + " 项" : "\n✓ 冒烟测试全部通过");
  process.exit(failed ? 1 : 0);
}, 300);
