/* WorkBuddy 控制台 · 算力池扩展
   由 nginx 在 /wb/ 的 HTML 末尾注入，不改第三方镜像。
   数据来自算力池服务 /join/admin/api/overview，鉴权直接用面板自己的
   X-Panel-Token —— 能进面板的人才能看，不额外多一个密码。
   幂等：重复注入只跑一次；面板没有新壳节点时安静退出。 */
(function () {
  'use strict';
  if (window.__poolExtLoaded) return;
  window.__poolExtLoaded = true;

  var TOKEN_KEY = 'wb-proxy-panel-token';
  var API_URL = '/join/admin/api/overview';
  var REFRESH_MS = 20000;
  var timer = null;
  var busy = false;

  function token() {
    // 面板默认把令牌放 sessionStorage（勾了「保持登录」才落 localStorage），两处都要认
    try {
      return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || '';
    } catch (e) {
      try { return localStorage.getItem(TOKEN_KEY) || ''; } catch (e2) { return ''; }
    }
  }

  function esc(v) {
    return String(v === null || v === undefined ? '' : v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function nfmt(v, d) {
    if (v === null || v === undefined || isNaN(v)) return '—';
    d = (d === undefined) ? 2 : d;
    var parts = Number(v).toFixed(d).split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
  }

  function wan(v) {
    if (!v && v !== 0) return '—';
    return v >= 10000 ? nfmt(v / 10000, 1) + ' 万' : nfmt(v, 0);
  }

  function stat(k, v, s, color) {
    return '<div><div style="font-size:11px;color:var(--dim);font-weight:600;margin-bottom:4px">' + esc(k) + '</div>'
      + '<div style="font-size:19px;font-weight:700;letter-spacing:-.4px;font-variant-numeric:tabular-nums;color:' + (color || 'var(--fg)') + '">' + v + '</div>'
      + (s ? '<div style="font-size:10.5px;color:var(--dim-light);margin-top:2px">' + esc(s) + '</div>' : '')
      + '</div>';
  }

  function kpi(k, v, s) {
    return '<div class="card"><div class="k">' + esc(k) + '</div>'
      + '<div class="v">' + v + '</div>'
      + '<div class="s">' + esc(s || '') + '</div></div>';
  }

  function bar(pct, color) {
    var w = Math.max(0, Math.min(100, Number(pct) || 0));
    return '<div style="height:6px;border-radius:999px;background:var(--panel3);overflow:hidden;min-width:64px">'
      + '<i style="display:block;height:100%;width:' + w + '%;background:' + color + '"></i></div>';
  }

  function card(title, sub, inner) {
    return '<div class="card" style="padding:16px 20px;margin-bottom:14px">'
      + '<div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin-bottom:10px">'
      + '<span style="font-size:13px;font-weight:700;color:var(--fg)">' + esc(title) + '</span>'
      + (sub ? '<span style="font-size:11px;color:var(--dim-light)">' + esc(sub) + '</span>' : '')
      + '</div>' + inner + '</div>';
  }

  function skeleton() {
    // 标题和说明由面板顶栏给（setChrome），这里只留操作条，避免同一个标题出现两次
    return '<div style="display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-bottom:12px">'
      + '<span id="poolUpdated" style="font-size:11px;color:var(--dim-light)">—</span>'
      + '<button type="button" class="sec mini" id="poolRefreshBtn">刷新</button>'
      + '<button type="button" class="sec mini" id="poolCreditsBtn" title="真的去腾讯重取一次余额，约 2-3 秒">刷新余额</button>'
      + '</div>'
      + '<div id="poolBody"></div>';
  }

  function ensureStyle() {
    if (document.getElementById('poolStyle')) return;
    var st = document.createElement('style');
    st.id = 'poolStyle';
    // 面板老壳层的页脚和上下文条对本页没意义；进本页时收掉，离开时还原
    st.textContent = 'html.pool-active #nextContent .console-shell > main > footer,'
      + 'html.pool-active #nextContent .console-shell > main > .console-contextbar{display:none!important}'
      + 'html.pool-active #poolBody table td{vertical-align:middle}'
      + 'html.pool-active #poolBody .card .v{white-space:nowrap}';
    (document.head || document.documentElement).appendChild(st);
  }

  function table(inner) {
    return '<div style="overflow-x:auto;-webkit-overflow-scrolling:touch">' + inner + '</div>';
  }


  // ── 侧栏顶部的平台下拉（自绘 + 挂到 body 固定定位，避免被侧栏裁切） ──
  var PLAT_STORE = 'wb-pool-platform';

  function platSaved() {
    try { return localStorage.getItem(PLAT_STORE) || 'all'; } catch (e) { return 'all'; }
  }

  function applyPlatform(v) {
    try { localStorage.setItem(PLAT_STORE, v); } catch (e) { }
    plat.tab = (v === 'all') ? '' : v;
    // 选具体某一家（且不是 WorkBuddy，WorkBuddy 就是原面板的池子）时，整页只显示那家的数据
    plat.scoped = (v !== 'all' && v !== 'workbuddy');
    closePlatMenu();
    goPool();
    loadPlatforms(true);
    load(true);
  }

  function closePlatMenu() {
    var m = document.getElementById('poolPlatMenu');
    if (m) m.style.display = 'none';
  }

  function openPlatMenu() {
    var btn = document.getElementById('poolPlatBtn');
    var m = document.getElementById('poolPlatMenu');
    if (!btn || !m) return;
    var r = btn.getBoundingClientRect();
    m.style.left = Math.round(r.left) + 'px';
    m.style.top = Math.round(r.bottom + 6) + 'px';
    m.style.width = Math.round(Math.max(160, r.width)) + 'px';
    m.style.display = 'block';
    if (!m.dataset.filled) {
      m.innerHTML = '<div style="padding:8px 10px;font-size:12px;color:var(--dim)">正在读取平台…</div>';
      loadPlatforms(true);
    }
  }

  function mountPlatformSelect() {
    var sv = platSaved();
    if (plat.tab === null && sv && sv !== 'all') {
      plat.tab = sv;
      plat.scoped = (sv !== 'workbuddy');
    }
    var brand = document.querySelector('#nextSidebar .next-brand');
    if (!brand || document.getElementById('poolPlatBtn')) return false;
    var wrap = document.createElement('div');
    wrap.id = 'poolPlatWrap';
    wrap.style.cssText = 'padding:0 8px 14px';
    wrap.innerHTML = ''
      + '<button type="button" id="poolPlatBtn" style="width:100%;display:flex;align-items:center;justify-content:space-between;gap:6px;'
      + 'padding:6px 10px;border-radius:7px;border:1px solid var(--line);background:var(--panel2);color:var(--fg);'
      + 'font:inherit;font-size:12.5px;cursor:pointer">'
      + '<span id="poolPlatLabel">全部平台</span><span style="opacity:.5">▾</span></button>';
    brand.parentNode.insertBefore(wrap, brand.nextSibling);

    // 菜单挂到 body，position:fixed，谁也别想裁掉它
    var menu = document.createElement('div');
    menu.id = 'poolPlatMenu';
    menu.style.cssText = 'display:none;position:fixed;z-index:9999;background:var(--panel,#fff);'
      + 'border:1px solid var(--line,#d5cfbc);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.16);overflow:hidden';
    document.body.appendChild(menu);

    var btn = wrap.querySelector('#poolPlatBtn');
    btn.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var m = document.getElementById('poolPlatMenu');
      if (m && m.style.display === 'block') closePlatMenu();
      else openPlatMenu();
    });
    document.addEventListener('click', function (ev) {
      var m = document.getElementById('poolPlatMenu');
      if (!m || m.style.display !== 'block') return;
      if (m.contains(ev.target)) return;
      closePlatMenu();
    });
    window.addEventListener('resize', closePlatMenu);
    window.addEventListener('scroll', closePlatMenu, true);
    return true;
  }

  function fillPlatformSelect(items) {
    var menu = document.getElementById('poolPlatMenu');
    var label = document.getElementById('poolPlatLabel');
    if (!menu) return;
    if (!items || !items.length) {
      menu.innerHTML = '<div style="padding:8px 10px;font-size:12px;color:var(--dim)">还没有可选的平台</div>';
      menu.dataset.filled = '1';
      return;
    }
    var cur = (plat.tab === null) ? platSaved() : (plat.tab || 'all');
    if (plat.tab === null) {
      var known = false;
      for (var k0 = 0; k0 < items.length; k0++) if (items[k0].id === cur) known = true;
      plat.tab = known ? cur : '';
      cur = plat.tab || 'all';
    }
    var list = [{ id: 'all', name: '全部平台', state: 'ok', accounts: [] }].concat(items);
    var html = '';
    for (var i = 0; i < list.length; i++) {
      var it = list[i];
      var on = (it.id === 'all' ? (plat.tab === '') : (plat.tab === it.id));
      var suffix = '';
      if (it.id !== 'all') {
        if (it.state === 'ok') suffix = ' · ' + (it.accounts ? it.accounts.length : 0) + ' 个号';
        else if (it.state === 'off') suffix = ' · 未接入';
        else suffix = ' · 读取失败';
      }
      html += '<div data-plat="' + esc(it.id) + '" style="padding:8px 10px;font-size:12.5px;cursor:pointer;'
        + (on ? 'background:var(--accent-soft,rgba(161,68,39,.09));color:var(--accent,#a14427);font-weight:600' : 'color:var(--fg,#1f1e1b)') + '">'
        + esc(it.name) + esc(suffix) + '</div>';
    }
    menu.innerHTML = html;
    menu.dataset.filled = '1';
    var picked = null;
    for (var m2 = 0; m2 < list.length; m2++) if (list[m2].id === (plat.tab === '' ? 'all' : plat.tab)) picked = list[m2];
    if (label) label.textContent = (picked ? picked.name : '全部平台');
    var rows = menu.querySelectorAll('[data-plat]');
    for (var r = 0; r < rows.length; r++) {
      rows[r].addEventListener('click', function (ev) {
        ev.stopPropagation();
        applyPlatform(this.getAttribute('data-plat'));
      });
    }
  }
  // ── 平台管理：三家共用一套界面 ─────────────────────────────
  var plat = { data: null, at: 0, tab: null, poll: null, scoped: false };  // null=没选过，''=全部；scoped=整页只看某一家

  function platAction(action, body) {
    return fetch('/join/admin/api/platform/' + action, {
      method: 'POST',
      headers: { 'X-Panel-Token': token(), 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {})
    }).then(function (r) {
      if (r.status === 401) throw new Error('面板会话失效');
      return r.json();
    });
  }

  function loadPlatforms(force) {
    if (!force && plat.data && Date.now() - plat.at < 10000) { renderPlatformTabs(); return; }
    fetch('/join/admin/api/platforms', { headers: { 'X-Panel-Token': token() }, cache: 'no-store' })
      .then(function (r) {
        if (r.status === 401) throw new Error('面板会话失效');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (d) {
        plat.data = d.platforms || [];
        plat.at = Date.now();
        mountPlatformSelect();
        fillPlatformSelect(plat.data);
        if (plat.tab === null && plat.data.length) plat.tab = plat.data[0].id;
        renderPlatformTabs();
        if (plat.scoped) {
          var pg = document.getElementById('pagePool');
          var pb = document.getElementById('poolBody');
          if (pg && pb && pg.classList.contains('active')) pb.innerHTML = renderScopedBody(scopedPlatform());
        }
      })
      .catch(function (e) {
        var b = document.getElementById('poolPlatformBody');
        if (b) b.innerHTML = '<span style="color:var(--bad)">平台明细取不到：' + esc(e.message) + '</span>';
      });
  }

  function renderPlatformTabs() {
    var tabs = document.getElementById('poolPlatformTabs');
    var body = document.getElementById('poolPlatformBody');
    if (!tabs || !body) return;
    var h = '';
    for (var i = 0; i < (plat.data || []).length; i++) {
      var p = plat.data[i];
      var label = p.name;
      if (p.state === 'ok') label += ' · ' + p.accounts.length + ' 个号';
      else if (p.state === 'off') label += ' · 未接入';
      else label += ' · 读取失败';
      var on = p.id === plat.tab;
      h += '<button type="button" class="sec mini" data-plat="' + esc(p.id) + '"'
        + (on ? ' style="border-color:var(--accent);color:var(--accent)"' : '') + '>' + esc(label) + '</button>';
    }
    tabs.innerHTML = h;
    var btns = tabs.querySelectorAll('[data-plat]');
    for (var j = 0; j < btns.length; j++) {
      btns[j].addEventListener('click', function () {
        plat.tab = this.getAttribute('data-plat');
        renderPlatformTabs();
        if (plat.scoped) {
          var pg = document.getElementById('pagePool');
          var pb = document.getElementById('poolBody');
          if (pg && pb && pg.classList.contains('active')) pb.innerHTML = renderScopedBody(scopedPlatform());
        }
      });
    }
    renderPlatformBody();
  }

  function renderPlatformBody() {
    var body = document.getElementById('poolPlatformBody');
    if (!body) return;
    var p = null;
    for (var i = 0; i < (plat.data || []).length; i++) if (plat.data[i].id === plat.tab) p = plat.data[i];
    if (!p) {
      // 选「全部平台」时给一张汇总表，别留空白
      var srows = '';
      for (var si = 0; si < (plat.data || []).length; si++) {
        var sp = plat.data[si];
        srows += '<tr><td>' + esc(sp.name) + '</td>'
          + '<td>' + (sp.state === 'ok' ? '<span class="badge ok mini">在线</span>'
            : (sp.state === 'off' ? '<span class="badge off mini">未接入</span>' : '<span class="badge warn mini">读取失败</span>')) + '</td>'
          + '<td>' + (sp.state === 'ok' ? sp.accounts.length : '—') + '</td>'
          + '<td style="font-variant-numeric:tabular-nums">' + (sp.state === 'ok' ? nfmt(sp.usage.used) : '—') + '</td>'
          + '<td>' + (sp.state === 'ok' ? sp.usage.requests : '—') + '</td></tr>';
      }
      body.innerHTML = '<div style="font-size:12px;color:var(--dim);margin-bottom:8px">上面下拉选一个平台，这里就切到那家的账号明细；现在显示的是三家汇总。</div>'
        + table('<table><tr><th>平台</th><th>状态</th><th>账号</th><th>今日消耗</th><th>今日请求</th></tr>' + srows + '</table>');
      return;
    }
    if (p.state === 'off') {
      body.innerHTML = '<div style="color:var(--dim)">' + esc(p.name)
        + ' 还没接入。在 <code>/opt/join-panel/upstreams.json</code> 里把它的 enabled 改成 true。</div>';
      return;
    }
    if (p.state === 'error') {
      body.innerHTML = '<div style="color:var(--bad)">' + esc(p.name) + ' 读取失败：' + esc(p.error || '') + '</div>';
      return;
    }

    var rows = '';
    for (var k = 0; k < p.accounts.length; k++) {
      var a = p.accounts[k];
      var badge = a.need_relogin ? '<span class="badge warn mini">需重新授权</span>'
        : (!a.enabled ? '<span class="badge off mini">已停用</span>'
          : (a.cooldown ? '<span class="badge warn mini">冷却中</span>' : '<span class="badge ok mini">正常</span>'));
      rows += '<tr><td>' + esc(a.nickname) + '</td>'
        + '<td style="font-variant-numeric:tabular-nums">' + (a.remain === null ? '—' : nfmt(a.remain, 1)) + '</td>'
        + '<td>' + (a.checked ? '已签 ' + a.streak + ' 天' : '<span style="color:var(--warn)">未签到</span>') + '</td>'
        + '<td>' + badge + '</td>'
        + '<td><button type="button" class="sec mini" data-checkin="' + esc(a.uid) + '">签到</button></td></tr>';
    }
    if (!rows) rows = '<tr><td colspan="5" style="color:var(--dim)">这家还没有账号，点下面的「添加账号」授权一个</td></tr>';

    body.innerHTML = '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px">'
      + '<button type="button" class="sec mini" id="platAddBtn">添加账号</button>'
      + '<button type="button" class="sec mini" id="platCheckAll">全部签到</button>'
      + '<span id="platMsg" style="font-size:11.5px;color:var(--dim)"></span></div>'
      + '<div id="platAuth"></div>'
      + table('<table><tr><th>账号</th><th>剩余积分</th><th>今日签到</th><th>状态</th><th></th></tr>' + rows + '</table>')
      + '<div style="font-size:11px;color:var(--dim-light);margin-top:8px">今日消耗 ' + nfmt(p.usage.used)
      + ' 积分 · ' + p.usage.requests + ' 次请求；这是管理视角，朋友那页仍然匿名。</div>';

    var msg = document.getElementById('platMsg');
    function say(text, bad) {
      if (!msg) return;
      msg.textContent = text || '';
      msg.style.color = bad ? 'var(--bad)' : 'var(--dim)';
    }

    var addBtn = document.getElementById('platAddBtn');
    if (addBtn) addBtn.addEventListener('click', function () {
      say('正在申请授权链接…');
      platAction('login-start', { id: p.id }).then(function (d) {
        if (!d.ok) { say(d.error || '申请失败', true); return; }
        var box = document.getElementById('platAuth');
        box.innerHTML = '<div style="margin:6px 0 10px"><a class="link" target="_blank" rel="noopener" href="'
          + esc(d.authUrl) + '">打开 ' + esc(p.name) + ' 官方授权页 →</a>'
          + '<div style="font-size:11.5px;color:var(--dim);margin-top:4px">在上面登录并同意后，这里会自动变成「已加入」；本页别关。</div></div>';
        say('等你完成授权…');
        var n = 0;
        if (plat.poll) clearInterval(plat.poll);
        plat.poll = setInterval(function () {
          n++;
          platAction('login-poll', { id: p.id, state: d.state }).then(function (r) {
            if (r.status === 'ok') {
              clearInterval(plat.poll); plat.poll = null;
              say('已加入'); loadPlatforms(true); load(true);
            } else if (r.status === 'expired' || r.status === 'error') {
              clearInterval(plat.poll); plat.poll = null;
              say('授权没走完：' + (r.message || r.status), true);
            } else if (n >= 40) {
              clearInterval(plat.poll); plat.poll = null;
              say('等太久了，可以重新点「添加账号」', true);
            }
          }).catch(function () { });
        }, 3000);
      }).catch(function (e) { say(String(e.message || e), true); });
    });

    var allBtn = document.getElementById('platCheckAll');
    if (allBtn) allBtn.addEventListener('click', function () {
      say('正在签到…');
      platAction('checkin', { id: p.id }).then(function (d) {
        if (!d.ok) { say(d.error || '签到失败', true); return; }
        say('签到完成：' + (d.checked || 0) + '/' + (d.total || 0));
        loadPlatforms(true);
      }).catch(function (e) { say(String(e.message || e), true); });
    });

    var oneBtns = body.querySelectorAll('[data-checkin]');
    for (var m = 0; m < oneBtns.length; m++) {
      oneBtns[m].addEventListener('click', function () {
        var uid = this.getAttribute('data-checkin');
        this.disabled = true;
        say('签到中…');
        platAction('checkin', { id: p.id, uid: uid }).then(function (d) {
          say(d.ok ? ('签到完成：' + (d.checked || 0) + '/' + (d.total || 0)) : (d.error || '失败'), !d.ok);
          loadPlatforms(true);
        }).catch(function (e) { say(String(e.message || e), true); });
      });
    }
  }


  function scopedPlatform() {
    for (var i = 0; i < (plat.data || []).length; i++) {
      if (plat.data[i].id === plat.tab) return plat.data[i];
    }
    return null;
  }

  function renderScopedBody(p) {
    if (!p) {
      return card('读取中…', '', '<div style="font-size:12.5px;color:var(--dim)">正在从 ' + esc(plat.tab || '') + ' 网关取数…</div>');
    }
    if (p.state === 'off') {
      return card(p.name + ' 未接入', '', '<div style="font-size:12.5px;color:var(--dim)">在 <code>/opt/join-panel/upstreams.json</code> 里把它的 enabled 改成 true。</div>');
    }
    if (p.state === 'error') {
      return card(p.name + ' 读取失败', '', '<div style="font-size:12.5px;color:var(--bad)">' + esc(p.error || '') + '</div>');
    }
    var rows = '';
    var remainSum = 0, healthy = 0, checked = 0;
    for (var k = 0; k < p.accounts.length; k++) {
      var a = p.accounts[k];
      if (typeof a.remain === 'number') remainSum += a.remain;
      if (a.enabled && !a.need_relogin && !a.cooldown) healthy++;
      if (a.checked) checked++;
      var badge = a.need_relogin ? '<span class="badge warn mini">需重新授权</span>'
        : (!a.enabled ? '<span class="badge off mini">已停用</span>'
          : (a.cooldown ? '<span class="badge warn mini">冷却中</span>' : '<span class="badge ok mini">正常</span>'));
      rows += '<tr><td>' + esc(a.nickname) + '</td>'
        + '<td style="font-variant-numeric:tabular-nums">' + (typeof a.remain === 'number' ? nfmt(a.remain, 1) : '—') + '</td>'
        + '<td>' + (a.checked ? '已签 ' + a.streak + ' 天' : '<span style="color:var(--warn)">未签到</span>') + '</td>'
        + '<td>' + badge + '</td>'
        + '<td><button type="button" class="sec mini" data-scoped-checkin="' + esc(a.uid) + '">签到</button></td></tr>';
    }
    if (!rows) rows = '<tr><td colspan="5" style="color:var(--dim)">这家还没有账号，点「添加账号」授权一个</td></tr>';

    var html = '';
    html += '<div class="card" style="padding:18px 20px;margin-bottom:14px">'
      + '<div style="font-size:12px;color:var(--dim)">' + esc(p.name) + ' · 今日消耗</div>'
      + '<div style="display:flex;align-items:baseline;gap:8px;margin-top:6px;flex-wrap:wrap">'
      + '<span style="font-size:34px;font-weight:750;letter-spacing:-1.2px;color:var(--accent);font-variant-numeric:tabular-nums">' + nfmt(p.usage.used) + '</span>'
      + '<span style="font-size:12px;color:var(--dim)">积分 · ' + p.usage.requests + ' 次请求</span></div>'
      + '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)">'
      + stat('账号', p.accounts.length + ' 个', '可用 ' + healthy + ' 个')
      + stat('剩余积分', nfmt(remainSum, 1), '这家所有账号之和')
      + stat('今日已签到', checked + ' / ' + p.accounts.length, '')
      + '</div></div>';
    html += card(p.name + ' 的账号', '只看这一家；点右上角下拉可以换平台或回到全部',
      '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">'
      + '<button type="button" class="sec mini" id="scopedAddBtn">添加账号</button>'
      + '<button type="button" class="sec mini" id="scopedCheckAll">全部签到</button>'
      + '<span id="scopedMsg" style="font-size:11.5px;color:var(--dim)"></span></div>'
      + '<div id="scopedAuth"></div>'
      + table('<table><tr><th>账号</th><th>剩余积分</th><th>今日签到</th><th>状态</th><th></th></tr>' + rows + '</table>'));

    setTimeout(function () { bindScopedActions(p); }, 0);
    return html;
  }

  function bindScopedActions(p) {
    var msg = document.getElementById('scopedMsg');
    function say(text, bad) {
      if (!msg) return;
      msg.textContent = text || '';
      msg.style.color = bad ? 'var(--bad)' : 'var(--dim)';
    }
    var add = document.getElementById('scopedAddBtn');
    if (add) add.addEventListener('click', function () {
      say('正在申请授权链接…');
      platAction('login-start', { id: p.id }).then(function (d) {
        if (!d.ok) { say(d.error || '申请失败', true); return; }
        document.getElementById('scopedAuth').innerHTML =
          '<div style="margin:6px 0 6px"><a class="link" target="_blank" rel="noopener" href="' + esc(d.authUrl) + '">打开 ' + esc(p.name) + ' 官方授权页 →</a></div>'
          + '<div style="font-size:11.5px;color:var(--dim)">手机或别的机器打开时，登录完会跳 127.0.0.1 报拒绝连接——把地址栏整条网址粘到下面：</div>'
          + '<div style="display:flex;gap:8px;margin:6px 0 10px"><textarea id="scopedCbUrl" rows="2" placeholder="http://127.0.0.1:xxxxx/authorize?..." style="flex:1;font-size:12px;padding:8px;border:1px solid var(--line);border-radius:7px;background:#fdfcf8"></textarea><button type="button" class="sec mini" id="scopedCbBtn">提交回调</button></div>';
        var cbBtn = document.getElementById('scopedCbBtn');
        if (cbBtn) cbBtn.addEventListener('click', function () {
          var ta = document.getElementById('scopedCbUrl');
          var url = (ta && ta.value || '').trim();
          if (!url) { say('先把地址栏那条网址粘进来', true); return; }
          say('正在提交回调…');
          platAction('login-callback', { id: p.id, state: d.state, callback_url: url }).then(function (r) {
            if (!r.ok) { say(r.error || '提交失败', true); return; }
            say('已提交，等网关换取令牌…');
          }).catch(function (e) { say(String(e.message || e), true); });
        });
        say('等你在官方页面同意…');
        var n = 0;
        if (plat.poll) clearInterval(plat.poll);
        plat.poll = setInterval(function () {
          n++;
          platAction('login-poll', { id: p.id, state: d.state }).then(function (r) {
            if (r.status === 'ok') { clearInterval(plat.poll); plat.poll = null; say('已加入'); loadPlatforms(true); load(true); }
            else if (r.status === 'expired' || r.status === 'error') { clearInterval(plat.poll); plat.poll = null; say('授权没走完：' + (r.message || r.status), true); }
            else if (n >= 40) { clearInterval(plat.poll); plat.poll = null; say('等太久了，重新点一次', true); }
          }).catch(function () { });
        }, 3000);
      }).catch(function (e) { say(String(e.message || e), true); });
    });
    var all = document.getElementById('scopedCheckAll');
    if (all) all.addEventListener('click', function () {
      say('正在签到…');
      platAction('checkin', { id: p.id }).then(function (d) {
        say(d.ok ? ('签到完成：' + (d.checked || 0) + '/' + (d.total || 0)) : (d.error || '失败'), !d.ok);
        loadPlatforms(true);
      }).catch(function (e) { say(String(e.message || e), true); });
    });
    var one = document.querySelectorAll('[data-scoped-checkin]');
    for (var i = 0; i < one.length; i++) {
      one[i].addEventListener('click', function () {
        var uid = this.getAttribute('data-scoped-checkin');
        this.disabled = true;
        say('签到中…');
        platAction('checkin', { id: p.id, uid: uid }).then(function (d) {
          say(d.ok ? ('签到完成：' + (d.checked || 0) + '/' + (d.total || 0)) : (d.error || '失败'), !d.ok);
          loadPlatforms(true);
        }).catch(function (e) { say(String(e.message || e), true); });
      });
    }
  }

  // ── 全部平台：三家看板（每家一块，数字各自独立） ──────────────
  function plUsed(it) { return (it.usage && typeof it.usage.used === 'number') ? it.usage.used : (typeof it.used === 'number' ? it.used : 0); }
  function plReq(it) { return (it.usage && typeof it.usage.requests === 'number') ? it.usage.requests : (typeof it.requests === 'number' ? it.requests : 0); }
  function plAccs(it) { return Array.isArray(it.accounts) ? it.accounts : []; }
  function plCount(it) { return Array.isArray(it.accounts) ? it.accounts.length : (typeof it.accounts === 'number' ? it.accounts : 0); }
  function plRemain(it) {
    if (typeof it.remain === 'number') return it.remain;
    var accs = plAccs(it), s = 0;
    for (var k = 0; k < accs.length; k++) if (typeof accs[k].remain === 'number') s += accs[k].remain;
    return s;
  }

  function renderThreeBoard(items, fallback) {
    var list = (items && items.length) ? items : (fallback || []);
    var tot = { accounts: 0, used: 0, requests: 0, remain: 0 };
    for (var i = 0; i < list.length; i++) {
      var it = list[i];
      tot.accounts += plCount(it);
      tot.used += plUsed(it);
      tot.requests += plReq(it);
      tot.remain += plRemain(it);
    }
    var html = '';
    html += '<div class="card" style="padding:18px 20px;margin-bottom:14px">'
      + '<div style="font-size:12px;color:var(--dim)">三家合计 · 今天用了多少</div>'
      + '<div style="display:flex;align-items:baseline;gap:8px;margin-top:6px;flex-wrap:wrap">'
      + '<span style="font-size:34px;font-weight:750;letter-spacing:-1.2px;color:var(--accent);font-variant-numeric:tabular-nums">' + nfmt(tot.used) + '</span>'
      + '<span style="font-size:12px;color:var(--dim)">积分 · ' + tot.requests + ' 次请求</span></div>'
      + '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)">'
      + stat('账号合计', tot.accounts + ' 个', '三家加在一起')
      + stat('剩余积分合计', nfmt(tot.remain, 1), '三家账号余额之和', 'var(--accent2)')
      + stat('已接入', (function () { var n = 0; for (var k = 0; k < list.length; k++) if (list[k].state === 'ok') n++; return n + ' / ' + list.length; })(), '')
      + '</div></div>';

    for (var j = 0; j < list.length; j++) {
      var p = list[j];
      var ok = p.state === 'ok';
      var badge = ok ? '<span class="badge ok mini">在线</span>'
        : (p.state === 'off' ? '<span class="badge off mini">未接入</span>' : '<span class="badge warn mini">读取失败</span>');
      var accs = plAccs(p);
      var remainSum = 0, checkedSum = 0;
      for (var a = 0; a < accs.length; a++) {
        if (typeof accs[a].remain === 'number') remainSum += accs[a].remain;
        if (accs[a].checked) checkedSum++;
      }
      var rows = '';
      for (var r = 0; r < accs.length && r < 8; r++) {
        var x = accs[r];
        rows += '<tr><td>' + esc(x.nickname) + '</td>'
          + '<td style="font-variant-numeric:tabular-nums">' + (typeof x.remain === 'number' ? nfmt(x.remain, 1) : '—') + '</td>'
          + '<td>' + (x.checked ? '已签 ' + x.streak + ' 天' : '<span style="color:var(--warn)">未签到</span>') + '</td></tr>';
      }
      if (!rows) rows = '<tr><td colspan="3" style="color:var(--dim)">还没有账号</td></tr>';
      html += '<div class="card" style="padding:16px 20px;margin-bottom:14px">'
        + '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px">'
        + '<span style="font-size:13px;font-weight:700">' + esc(p.name) + '</span>' + badge
        + (p.note ? '<span style="font-size:11px;color:var(--dim-light)">' + esc(p.note) + '</span>' : '')
        + '</div>'
        + '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:10px">'
        + stat('今日消耗', ok ? nfmt(plUsed(p)) : '—', ok ? (plReq(p) + ' 次请求') : '')
        + stat('剩余积分', ok ? nfmt(remainSum, 1) : '—', ok ? ('今日已签 ' + checkedSum + '/' + accs.length) : '')
        + stat('账号', ok ? accs.length + ' 个' : '—', '')
        + '</div>'
        + (ok ? table('<table><tr><th>账号</th><th>剩余</th><th>今日签到</th></tr>' + rows + '</table>') : '')
        + '</div>';
    }
    return html;
  }
  function render(d) {
    var p = d.pool, u = d.users;
    var html = '';
    var allMode = (plat.tab === '');
    if (allMode) html += renderThreeBoard(plat.data, (d.upstreams && d.upstreams.items) || []);
    if (plat.scoped) {
      var bodyEl = document.getElementById('poolBody');
      if (bodyEl) {
        bodyEl.innerHTML = renderScopedBody(scopedPlatform());
        var up0 = document.getElementById('poolUpdated');
        if (up0) up0.textContent = '更新于 ' + (d.now || '刚刚');
      }
      return;
    }

    html += '<div class="card" style="padding:18px 20px;margin-bottom:14px">'
      + '<div style="font-size:12px;color:var(--dim)">今天这个池子用了多少</div>'
      + '<div style="display:flex;align-items:baseline;gap:8px;margin-top:6px;flex-wrap:wrap">'
      + '<span style="font-size:34px;font-weight:750;letter-spacing:-1.2px;color:var(--accent);font-variant-numeric:tabular-nums">' + nfmt(p.used) + '</span>'
      + '<span style="font-size:12px;color:var(--dim)">积分 · 今日累计（' + p.requests + ' 次请求 · ' + wan(p.tokens) + ' tokens）</span>'
      + '</div>'
      + '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px;margin-top:16px;padding-top:14px;border-top:1px solid var(--line)">'
      + stat('今天还能用', nfmt(p.available, 1), '剩余 + 未签到的今日额度', 'var(--accent2)')
      + stat('池子剩余积分', nfmt(p.remain, 1), '所有账号余额之和')
      + stat('今日签到到账', '+' + nfmt(p.today_gain, 0), '已经算在剩余里')
      + stat('未签到待领', '+' + nfmt(p.pending_signin, 0), '还没签到的账号今天还能再领')
      + (d.expiring ? stat('7 天内到期', nfmt((d.expiring.buckets[2] || {}).credit || 0, 1), '不用掉就作废', 'var(--warn)') : '')
      + '</div></div>';

    // 快过期的积分：积分包按到期时间从早到晚消耗，这部分是会真被扔掉的
    if (d.expiring) {
      var ex = d.expiring;
      var bstats = '';
      for (var bi = 0; bi < ex.buckets.length; bi++) {
        var bb = ex.buckets[bi];
        bstats += stat(bb.label, nfmt(bb.credit, 1), bb.packages + ' 个包', bb.credit > 0 ? 'var(--warn)' : null);
      }
      var erows = '';
      var nowSec = Date.now() / 1000;
      for (var ei = 0; ei < ex.soon.length; ei++) {
        var xi = ex.soon[ei];
        var hot = (xi.ts - nowSec) < 86400;
        erows += '<tr><td' + (hot ? ' style="color:var(--bad);font-weight:700"' : '') + '>' + esc(xi.at) + (hot ? ' · 24 小时内' : '') + '</td>'
          + '<td style="font-variant-numeric:tabular-nums">' + nfmt(xi.remain) + '</td>'
          + '<td>' + esc(xi.label) + '</td>'
          + '<td style="color:var(--dim);font-size:11.5px">' + esc(xi.name) + '</td></tr>';
      }
      if (!erows) erows = '<tr><td colspan="4" style="color:var(--dim)">目前没有带到期时间的余额</td></tr>';
      html += card('快过期的积分', '积分包按到期时间从早到晚消耗，这些不用掉就真没了',
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px;margin-bottom:12px">' + bstats + '</div>'
        + table('<table><tr><th>什么时候过期</th><th>还剩</th><th>账号</th><th>来源</th></tr>' + erows + '</table>')
        + '<div style="font-size:11px;color:var(--dim-light);margin-top:10px">会过期的包共 ' + ex.open_packages + ' 个、合计 '
        + nfmt(ex.open_total, 1) + ' 积分；无到期日的长期包不计。</div>');
    }

    html += '<div class="cards" style="margin-bottom:14px">'
      + kpi('注册用户', u.total, '在算力池注册过的人')
      + kpi('今天在用的朋友', u.active, '今天真用过池子的人')
      + kpi('已领 API Key', u.keys, '领了 key 才算真接入')
      + kpi('贡献的账号数', u.contribs, '所有人加进来的账号总数')
      + kpi('池内账号', p.account_count, '当前可用 ' + p.healthy + ' 个')
      + '</div>';

    // 多平台：几家网关的数字摆在一块看（全部平台视图已用三家看板替代）
    if (!allMode && d.upstreams && d.upstreams.items && d.upstreams.items.length) {
      var urows = '';
      for (var ui = 0; ui < d.upstreams.items.length; ui++) {
        var it = d.upstreams.items[ui];
        var ok = it.state === 'ok';
        var badge = ok ? '<span class="badge ok mini">在线</span>'
          : (it.state === 'off' ? '<span class="badge off mini">未接入</span>'
            : '<span class="badge warn mini">读取失败</span>');
        urows += '<tr><td>' + esc(it.name)
          + (it.note ? '<div style="font-size:11px;color:var(--dim-light)">' + esc(it.note) + '</div>' : '')
          + '</td><td>' + badge + '</td>'
          + '<td>' + (ok ? it.accounts + '（可用 ' + it.healthy + '）' : '—') + '</td>'
          + '<td style="font-variant-numeric:tabular-nums">' + (ok ? nfmt(it.used) : '—') + '</td>'
          + '<td>' + (ok ? it.requests : '—') + '</td>'
          + '<td style="font-variant-numeric:tabular-nums">' + (ok ? nfmt(it.remain, 1) : '—') + '</td></tr>';
      }
      var ut = d.upstreams.total;
      urows += '<tr><td><b>合计</b></td><td></td><td>' + ut.accounts + '</td><td>' + nfmt(ut.used, 1)
        + '</td><td>' + ut.requests + '</td><td>' + nfmt(ut.remain, 1) + '</td></tr>';
      html += card('多平台', '几家网关摆在一块看；合计那行只算已接入的',
        table('<table><tr><th>平台</th><th>状态</th><th>账号</th><th>今日消耗</th><th>今日请求</th><th>剩余积分</th></tr>'
          + urows + '</table>'));
    }

    html += card('平台管理', '同一个界面管三家：看账号、签到、加号',
      '<div id="poolPlatformTabs" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px"></div>'
      + '<div id="poolPlatformBody" style="font-size:12.5px;color:var(--dim)">正在读取…</div>');
    // 今日各用户用量
    var rows = '';
    var totalUsed = p.used || 0;
    function shareOf(c) { return totalUsed > 0 ? (c / totalUsed * 100) : 0; }
    var by = d.user_rows.slice().sort(function (a, b) { return b.credit - a.credit; });
    for (var i = 0; i < by.length; i++) {
      var r = by[i];
      if (!r.requests && !r.credit) continue;
      rows += '<tr><td>' + esc(r.nickname) + '</td>'
        + '<td style="font-variant-numeric:tabular-nums">' + nfmt(r.credit) + '</td>'
        + '<td>' + r.requests + '</td>'
        + '<td style="color:var(--dim)">' + nfmt(shareOf(r.credit), 1) + '%</td></tr>';
    }
    if (!rows) rows = '<tr><td colspan="4" style="color:var(--dim)">今天还没有朋友用</td></tr>';
    if (d.outside && (d.outside.requests || d.outside.credit)) {
      rows += '<tr style="color:var(--dim)"><td>站外 Key（管理员自用）</td>'
        + '<td style="font-variant-numeric:tabular-nums">' + nfmt(d.outside.credit) + '</td>'
        + '<td>' + d.outside.requests + '</td>'
        + '<td>' + nfmt(shareOf(d.outside.credit), 1) + '%</td></tr>';
    }
    html += card('今日各用户用量', '按每个人自己的 API Key 统计，站外那把不算朋友头上',
      table('<table><tr><th>用户</th><th>今日积分</th><th>请求数</th><th>占全站</th></tr>' + rows + '</table>'));

    // 注册用户
    var urows = '';
    for (var j = 0; j < d.user_rows.length; j++) {
      var x = d.user_rows[j];
      urows += '<tr><td>' + esc(x.nickname) + '<div style="font-size:11px;color:var(--dim-light)">' + esc(x.email) + '</div></td>'
        + '<td>' + x.contrib + ' 个</td>'
        + '<td>' + (x.has_key ? '<span class="badge ok mini">已领</span>' : '<span class="badge off mini">未领</span>') + '</td>'
        + '<td style="font-variant-numeric:tabular-nums">' + nfmt(x.credit) + '</td>'
        + '<td>' + x.requests + '</td>'
        + '<td style="color:var(--dim);font-size:11.5px;white-space:nowrap">' + esc(x.created) + '</td></tr>';
    }
    if (!urows) urows = '<tr><td colspan="6" style="color:var(--dim)">还没有人注册</td></tr>';
    html += card('注册用户', '谁注册了、加了几个号、今天用了多少', table('<table><tr><th>昵称 / 邮箱</th><th>贡献账号</th><th>Key</th><th>今日积分</th><th>今日请求</th><th>注册时间</th></tr>' + urows + '</table>'));

    // 账号明细
    var arows = '';
    for (var k = 0; k < p.accounts.length; k++) {
      var a = p.accounts[k];
      var pct = (a.size && a.remain !== null) ? (a.remain / a.size * 100) : 0;
      var badge = a.need_relogin ? '<span class="badge warn mini">需重新授权</span>'
        : (!a.enabled ? '<span class="badge off mini">已停用</span>'
          : (a.cooldown ? '<span class="badge warn mini">冷却中</span>' : '<span class="badge ok mini">正常</span>'));
      arows += '<tr><td>' + esc(a.label) + '</td>'
        + '<td style="font-variant-numeric:tabular-nums">' + nfmt(a.remain, 1) + '</td>'
        + '<td>' + bar(pct, 'var(--accent2)') + '</td>'
        + '<td style="font-variant-numeric:tabular-nums">' + nfmt(a.today_credit_used) + '</td>'
        + '<td style="font-size:11.5px;color:var(--dim)">' + (a.checked ? '已签 ' + a.streak + ' 天' : '未签到') + '</td>'
        + '<td>' + badge + '</td></tr>';
    }
    if (!arows) arows = '<tr><td colspan="6" style="color:var(--dim)">池子里还没有账号</td></tr>';
    html += card('账号明细', '只显示「谁提供的第几号账号」，不暴露账号本身的名字',
      table('<table><tr><th>账号</th><th>剩余积分</th><th>剩余比例</th><th>今日消耗</th><th>今日签到</th><th>状态</th></tr>' + arows + '</table>')
      + '<div style="font-size:11px;color:var(--dim-light);margin-top:10px;line-height:1.6">'
      + 'workbuddy 的额度按周期包发放，每天签到给每个账号补一笔，没有「每天只能用 X」的硬上限。'
      + '所以「今天还能用」= 现在所有账号的剩余 + 今天还没签到的那些账号能补的额度。'
      + '平时读的是网关的现成快照（7 毫秒），点右上角「刷新余额」才真的去腾讯重取一次（约 2–3 秒）。</div>');

    if (d.pool.errors && d.pool.errors.length) {
      html += '<div class="card" style="padding:12px 18px;margin-bottom:14px;border-color:rgba(183,121,31,.35);background:var(--warn-soft)">'
        + '<span style="font-size:12px;color:var(--warn)">部分数据没读到：' + esc(d.pool.errors.join('；')) + '</span></div>';
    }

    var body = document.getElementById('poolBody');
    if (body) body.innerHTML = html;
    if (document.getElementById('poolPlatformTabs')) loadPlatforms(false);
    var up = document.getElementById('poolUpdated');
    if (up) up.textContent = '更新于 ' + (d.now || '刚刚');
  }

  function fail(msg) {
    var body = document.getElementById('poolBody');
    if (!body) return;
    body.innerHTML = '<div class="card" style="padding:16px 20px">'
      + '<div style="font-size:13px;font-weight:700;color:var(--bad);margin-bottom:6px">算力池数据没取到</div>'
      + '<div style="font-size:12px;color:var(--dim);line-height:1.7">' + esc(msg) + '</div>'
      + '<div style="font-size:11.5px;color:var(--dim-light);margin-top:8px">'
      + '面板本身没问题；这一步是面板向算力池服务要数据，走的是面板登录后的令牌。</div></div>';
  }

  function load(force) {
    var body = document.getElementById('poolBody');
    if (!body) return;
    if (busy) return;
    busy = true;
    var btn = document.getElementById('poolRefreshBtn');
    if (btn) { btn.disabled = true; btn.textContent = '刷新中'; }
    var t = token();
    if (!t) {
      busy = false;
      if (btn) { btn.disabled = false; btn.textContent = '刷新'; }
      fail('面板还没登录。先在面板输入密码，登录后这里会自动出数。');
      return;
    }
    fetch(API_URL + (force ? '?t=' + Date.now() : ''), {
      headers: { 'X-Panel-Token': t },
      cache: 'no-store'
    }).then(function (r) {
      if (r.status === 401) throw new Error('401');
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (d) {
      if (!d || !d.ok) throw new Error((d && d.error) || '返回内容不对');
      render(d);
    }).catch(function (e) {
      var m = String(e && e.message || e);
      if (m === '401') fail('面板会话失效了，刷新页面重新输一次面板密码即可。');
      else if (m.indexOf('HTTP 404') === 0) fail('没找到 /join/admin/api/overview。请用 http://120.55.100.130/wb/ 打开面板（算力池服务挂在同一个域名的 /join/ 下）。');
      else fail('请求失败：' + m);
    }).then(function () {
      busy = false;
      if (btn) { btn.disabled = false; btn.textContent = '刷新'; }
    });
  }

  // 「刷新余额」：后台逐号去腾讯重取，页面不阻塞，进度从 /refresh-status 拉
  function pollCredits() {
    var btn = document.getElementById('poolCreditsBtn');
    var t = token();
    fetch('/join/admin/api/refresh-status', { headers: { 'X-Panel-Token': t }, cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var j = (d && d.job) || {};
        if (j.running) {
          if (btn) btn.textContent = '刷新中 ' + (j.done || 0) + '/' + (j.total || 0);
          setTimeout(pollCredits, 700);
          return;
        }
        if (btn) { btn.disabled = false; btn.textContent = '刷新余额'; }
        load(true);
      })
      .catch(function () {
        if (btn) { btn.disabled = false; btn.textContent = '刷新余额'; }
      });
  }

  function refreshCredits() {
    var btn = document.getElementById('poolCreditsBtn');
    if (!btn || btn.disabled) return;
    btn.disabled = true;
    btn.textContent = '刷新中…';
    fetch('/join/admin/api/credits-refresh', {
      method: 'POST',
      headers: { 'X-Panel-Token': token(), 'Content-Type': 'application/json' },
      body: '{}'
    }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (d) {
      if (!d || !d.ok) throw new Error((d && d.error) || '没起来');
      pollCredits();
    }).catch(function (e) {
      btn.disabled = false;
      btn.textContent = '刷新余额';
      fail('刷新余额失败：' + (e && e.message || e));
    });
  }

  function setChrome(title, desc) {
    var t1 = document.getElementById('nextPageTitle');
    var d1 = document.getElementById('nextPageDesc');
    if (t1) t1.textContent = title;
    if (d1) d1.textContent = desc;
    var c = document.getElementById('consoleCurrentPage');
    if (c) c.textContent = title;
  }

  function markNav(on) {
    var items = document.querySelectorAll('#nextNav .next-nav-item, #nextBottomNav button, .main-nav .main-nav-btn, .main-nav .console-nav-link');
    for (var i = 0; i < items.length; i++) {
      var el = items[i];
      if (el.id === 'poolNavBtn' || el.id === 'poolBottomBtn') continue;
      el.classList.remove('active');
      el.removeAttribute('aria-current');
    }
    var ids = ['poolNavBtn', 'poolBottomBtn'];
    for (var j = 0; j < ids.length; j++) {
      var mine = document.getElementById(ids[j]);
      if (!mine) continue;
      mine.classList.toggle('active', !!on);
      if (on) mine.setAttribute('aria-current', 'page');
      else mine.removeAttribute('aria-current');
    }
  }

  function goPool() {
    var page = document.getElementById('pagePool');
    if (!page) return;
    var all = document.querySelectorAll('.main-page');
    for (var i = 0; i < all.length; i++) all[i].classList.remove('active');
    page.classList.add('active');
    document.documentElement.classList.add('pool-active');
    markNav(true);
    setChrome('算力池', '朋友的账号都并在这里，共用一个额度；今日用了多少、谁在用，一屏看完。');
    if (typeof window.nextOpenSidebar === 'function') { try { window.nextOpenSidebar(false); } catch (e) { } }
    load(false);
    try { window.scrollTo(0, 0); } catch (e) { }
  }
  window.__poolGo = goPool;

  function wrapRouter() {
    if (typeof window.switchMainTab === 'function' && !window.switchMainTab.__poolWrapped) {
      var orig = window.switchMainTab;
      var w = function (tab) {
        if (tab === 'pool') { goPool(); return; }
        var page = document.getElementById('pagePool');
        if (page) page.classList.remove('active');
        document.documentElement.classList.remove('pool-active');
        markNav(false);
        return orig.apply(this, arguments);
      };
      w.__poolWrapped = true;
      window.switchMainTab = w;
    }
    if (typeof window.nextGo === 'function' && !window.nextGo.__poolWrapped) {
      var origGo = window.nextGo;
      var wg = function (tab) {
        if (tab === 'pool') { goPool(); return; }
        var page = document.getElementById('pagePool');
        if (page) page.classList.remove('active');
        document.documentElement.classList.remove('pool-active');
        return origGo.apply(this, arguments);
      };
      wg.__poolWrapped = true;
      window.nextGo = wg;
    }
  }

  function addNav() {
    if (document.getElementById('poolNavBtn')) return;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'poolNavBtn';
    btn.setAttribute('data-pool-nav', '1');
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">'
      + '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/></svg>'
      + '<span>算力池</span>';
    btn.addEventListener('click', function (ev) { if (ev) ev.preventDefault(); goPool(); });

    var nav = document.getElementById('nextNav');
    if (nav) {
      btn.className = 'next-nav-item';
      var anchor = nav.querySelector('[data-next-tab="analytics"]') || nav.querySelector('[data-next-tab="accounts"]');
      if (anchor && anchor.parentNode === nav) nav.insertBefore(btn, anchor.nextSibling);
      else nav.appendChild(btn);
      return;
    }
    var legacy = document.querySelector('.main-nav');
    if (legacy) {
      btn.className = 'main-nav-btn';
      legacy.appendChild(btn);
      return;
    }
    var bottom = document.getElementById('nextBottomNav');
    if (bottom) {
      var sample = bottom.querySelector('button');
      btn.className = sample ? sample.className : 'next-bottom-item';
      var more = bottom.querySelector('#nextMoreBtn') || bottom.lastElementChild;
      if (more && more.parentNode === bottom) bottom.insertBefore(btn, more);
      else bottom.appendChild(btn);
    }
  }

  // 手机端底部导航是面板运行时生成的，晚一步再补一次
  function addBottomNav() {
    var bottom = document.getElementById('nextBottomNav');
    if (!bottom || document.getElementById('poolBottomBtn')) return;
    var sample = bottom.querySelector('button');
    if (!sample) return;
    var b = document.createElement('button');
    b.type = 'button';
    b.id = 'poolBottomBtn';
    b.className = sample.className;
    b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">'
      + '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/></svg><span>池子</span>';
    b.addEventListener('click', function (ev) { if (ev) ev.preventDefault(); goPool(); });
    var more = bottom.querySelector('#nextMoreBtn') || bottom.lastElementChild;
    if (more && more.parentNode === bottom) bottom.insertBefore(b, more);
    else bottom.appendChild(b);
  }

  function buildPage() {
    if (document.getElementById('pagePool')) return;
    var page = document.createElement('div');
    page.id = 'pagePool';
    page.className = 'main-page';
    page.innerHTML = skeleton();
    var anchorPage = document.getElementById('pageOverview') || document.getElementById('pageGateway');
    var host = (anchorPage && anchorPage.parentNode) || document.getElementById('nextContent') || document.body;
    host.appendChild(page);
    var btn = document.getElementById('poolRefreshBtn');
    if (btn) btn.addEventListener('click', function () { load(true); });
    var cbtn = document.getElementById('poolCreditsBtn');
    if (cbtn) cbtn.addEventListener('click', function () { refreshCredits(); });
  }

  function tick() {
    var page = document.getElementById('pagePool');
    if (!page || !page.classList.contains('active')) return;
    if (document.visibilityState && document.visibilityState !== 'visible') return;
    load(false);
  }

  function boot() {
    if (!document.getElementById('nextShell') && !document.querySelector('.main-nav')) return;
    ensureStyle();
    buildPage();
    addNav();
    mountPlatformSelect();
    addBottomNav();
    wrapRouter();
    if (timer) clearInterval(timer);
    timer = setInterval(tick, REFRESH_MS);
    var page = document.getElementById('pagePool');
    if (page && page.classList.contains('active')) load(false);
    if (!boot.__resize) {
      boot.__resize = true;
      var t = null;
      window.addEventListener('resize', function () {
        if (t) clearTimeout(t);
        t = setTimeout(function () {
          addBottomNav();
          var pg = document.getElementById('pagePool');
          if (pg && pg.classList.contains('active')) load(true);
        }, 400);
      });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { setTimeout(boot, 0); });
  else setTimeout(boot, 0);

  // 面板可能在登录后重建 DOM（闸门收起），再兜一次
  setTimeout(function () {
    try {
      if (!document.getElementById('poolNavBtn')) boot();
      else addBottomNav();
    } catch (e) { }
  }, 2500);
})();
