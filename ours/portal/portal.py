#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""朋友用的算力池小站：注册 / 共用额度看板 / 添加账号 / 生成 API Key。

独立进程，只监听 127.0.0.1:8790，由 nginx 挂在 /join/。
与主面板的边界：只调用
    GET  /accounts            池子概况
    GET  /usage/remaining     各模型剩余
    POST /accounts/login/start  |  GET /accounts/login/poll   加号授权
    GET/POST /settings        生成 API Key
删除账号、改他人配额、看别人 key —— 一个都不暴露。
"""
import hashlib
import json
import os
import re
import secrets
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = "http://127.0.0.1:8788"
PASS_FILE = "/opt/join-panel/panel-pass"
UPSTREAMS_FILE = "/opt/join-panel/upstreams.json"
DB = "/opt/join-panel/portal.db"
PANEL_JS = "/opt/join-panel/panel-ext.js"
LOG_FILE = "/var/log/join-panel.log"
LISTEN = ("127.0.0.1", 8790)

RATE_WINDOW, RATE_MAX = 600, 40
_lock = threading.Lock()
_rate = {}

RE_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_panel = {"token": None}


def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


# ── wb-proxy 调用 ────────────────────────────────────────────────
def panel_token(force=False):
    if _panel["token"] and not force:
        return _panel["token"]
    pw = open(PASS_FILE, encoding="utf-8").read().strip()
    req = urllib.request.Request(
        UPSTREAM + "/panel/login",
        data=json.dumps({"password": pw}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        token = json.loads(r.read().decode()).get("token")
    if not token:
        raise RuntimeError("panel login failed")
    _panel["token"] = token
    return token


def api(method, path, payload=None, query=None):
    url = UPSTREAM + path + ("?" + urllib.parse.urlencode(query) if query else "")
    data = json.dumps(payload).encode() if payload is not None else None

    def once(token):
        req = urllib.request.Request(url, data=data, method=method, headers={
            "X-Panel-Token": token, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())

    try:
        return once(panel_token())
    except urllib.error.HTTPError as exc:
        if exc.code != 401:
            raise
        return once(panel_token(force=True))


# ── 数据库 ──────────────────────────────────────────────────────
def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            salt TEXT NOT NULL,
            hash TEXT NOT NULL,
            created REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions(
            token TEXT PRIMARY KEY, uid INTEGER NOT NULL, exp REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS login_states(
            state TEXT PRIMARY KEY, uid INTEGER NOT NULL, at REAL NOT NULL,
            platform TEXT NOT NULL DEFAULT 'workbuddy'
        );
        CREATE TABLE IF NOT EXISTS contrib(
            account_uid TEXT PRIMARY KEY, uid INTEGER NOT NULL, at REAL NOT NULL,
            platform TEXT NOT NULL DEFAULT 'workbuddy'
        );
        CREATE TABLE IF NOT EXISTS user_keys(
            uid INTEGER PRIMARY KEY, key TEXT NOT NULL, name TEXT NOT NULL,
            created REAL NOT NULL, key_id TEXT
        );
        """)
        # 老库补列（2026-11-28 支持多家平台加号）
        for tbl in ("contrib", "login_states"):
            cols = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % tbl)]
            if "platform" not in cols:
                conn.execute("ALTER TABLE %s ADD COLUMN platform TEXT NOT NULL DEFAULT 'workbuddy'" % tbl)


def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 120_000).hex()
    return salt, h


def rate_ok(ip):
    now = time.time()
    with _lock:
        hits = [t for t in _rate.get(ip, []) if now - t < RATE_WINDOW]
        if len(hits) >= RATE_MAX:
            _rate[ip] = hits
            return False
        hits.append(now)
        _rate[ip] = hits
        return True


# ── 页面 ────────────────────────────────────────────────────────
CSS = """
:root{--bg:#efebe0;--panel:#ffffff;--line:#d5cfbc;--fg:#1f1e1b;--muted:#6f685a;
      --acc:#a14427;--warn:#a0691c;--ok:#2f6b46;--bad:#a14427}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.nav{display:flex;gap:4px;align-items:center;padding:12px 20px;border-bottom:1px solid var(--line);background:var(--panel)}
.nav b{color:var(--acc);margin-right:14px;font-size:15px;letter-spacing:.02em}
.nav a{color:var(--muted);text-decoration:none;padding:6px 12px;border-radius:7px;font-size:13.5px}
.nav a.on{background:#f3ede0;color:var(--fg);border:1px solid var(--line)}
.nav a:hover{color:var(--fg)}
.nav .sp{flex:1}.nav .who{color:var(--muted);font-size:12.5px;margin-right:8px}
.wrap{max-width:900px;margin:24px auto;padding:0 20px 60px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:20px;margin-bottom:14px}
h1{font-size:18px;margin:0 0 4px;font-weight:600}
h2{font-size:14px;margin:0 0 12px;font-weight:600;color:var(--muted)}
.sub{color:var(--muted);font-size:13px;margin-bottom:16px}
.hero{display:flex;align-items:baseline;gap:10px;margin-top:4px}
.big{font-size:42px;font-weight:700;color:var(--acc);letter-spacing:-.02em;line-height:1.1}
.unit{color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:18px}
.stat{background:#faf7f0;border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.stat .n{font-size:19px;font-weight:600}
.stat .l{color:var(--muted);font-size:12px;margin-top:2px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--muted);font-weight:600;padding:8px 8px;border-bottom:1px solid var(--line);font-size:12.5px}
td{padding:10px 8px;border-bottom:1px solid #f1ece1;vertical-align:middle}
tr:last-child td{border-bottom:0}
.bar{height:6px;border-radius:3px;background:#eee7d8;overflow:hidden;min-width:90px}
.bar i{display:block;height:100%;background:var(--ok)}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;border:1px solid var(--line);
  font-size:12px;color:var(--muted);white-space:nowrap}
.pill.ok{color:var(--ok);border-color:#bfd8c8;background:#f2f8f4}
.pill.warn{color:var(--warn);border-color:#e3d1a8;background:#fdf7ea}
label{display:block;font-size:12.5px;color:var(--muted);margin:12px 0 6px}
input{width:100%;padding:9px 11px;border:1px solid var(--line);border-radius:7px;
  background:#fdfcf8;color:var(--fg);font-size:14px}
input:focus{border-color:var(--acc);outline:none}
button{background:var(--acc);color:#fff;border:0;border-radius:7px;padding:9px 16px;font-size:14px;cursor:pointer;font-weight:500}
button.ghost{background:#f3ede0;color:var(--fg);border:1px solid var(--line)}
button:disabled{opacity:.5;cursor:default}
.hint{font-size:13px;color:var(--muted);margin-top:10px;min-height:18px}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
code{background:#f3ede0;border:1px solid var(--line);padding:1px 6px;border-radius:5px;font-size:13px}
a.link{color:var(--acc);word-break:break-all}
pre{background:#f3ede0;border:1px solid var(--line);border-radius:8px;padding:12px 14px;
  overflow:auto;font-size:12.5px;line-height:1.55;margin:10px 0;
  font-family:ui-monospace,Consolas,"Courier New",monospace}
.steps{counter-reset:s;margin:6px 0 0;padding:0;list-style:none}
.steps li{counter-increment:s;position:relative;padding-left:32px;margin:12px 0;font-size:13.5px}
.steps li:before{content:counter(s);position:absolute;left:0;top:0;width:21px;height:21px;
  border-radius:50%;background:var(--acc);color:#fff;font-size:12px;text-align:center;line-height:21px}
.steps li .hint{margin-top:4px;line-height:1.6}
.kv{display:grid;grid-template-columns:96px 1fr;gap:8px 12px;align-items:center;font-size:13.5px;margin:10px 0 0}
.kv .k{color:var(--muted);font-size:12.5px}
.btnrow{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:12px}
.big-key{font-family:ui-monospace,Consolas,"Courier New",monospace;font-size:13.5px;
  background:#f3ede0;border:1px solid var(--line);border-radius:8px;padding:10px 12px;
  word-break:break-all;line-height:1.5}
.faq{font-size:13.5px;margin:0;padding-left:18px}
.faq li{margin:8px 0}
@media (max-width:520px){
  .wrap{padding:0 12px 40px;margin:12px auto}
  .card{padding:14px;border-radius:9px}
  .nav{padding:10px 12px;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}
  .nav b{margin-right:8px}
  .nav .who{display:none}
  .big{font-size:34px}
  .grid{grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px}
  .stat{padding:10px 12px}
  table{font-size:12px}
  th,td{padding:8px 5px}
  .kv{grid-template-columns:78px 1fr}
  button{padding:9px 14px}
  .btnrow button{flex:1 1 auto}
  input,textarea{font-size:16px}
}
"""


ADMIN_EMAILS = {"2088330643@qq.com"}


def is_admin(user):
    return user is not None and str(user["email"]).lower() in ADMIN_EMAILS


def admin_body(user):
    """管理总览：多少人注册、多少人贡献了账号、每人今天用了多少。只读，不给删人能力。"""
    with db() as conn:
        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        contribs = {r["uid"]: r["n"] for r in conn.execute(
            "SELECT uid, count(*) AS n FROM contrib GROUP BY uid")}
        keys = {r["uid"]: r["key_id"] for r in conn.execute(
            "SELECT uid, key_id FROM user_keys")}
    per_key = today_by_key()
    owner_of = {}
    for u in users:
        kid = keys.get(u["id"])
        if kid:
            owner_of[kid] = u

    usage_by_uid = {}
    outside = {"credit": 0.0, "n": 0}
    for kid, rec in per_key.items():
        u = owner_of.get(kid)
        if u is None:
            outside["credit"] += rec["credit"]
            outside["n"] += rec["n"]
            continue
        a = usage_by_uid.setdefault(u["id"], {"credit": 0.0, "n": 0})
        a["credit"] += rec["credit"]
        a["n"] += rec["n"]

    rows = ""
    active = 0
    total_contrib = sum(contribs.values())
    today_total = outside["credit"]
    for u in users:
        us = usage_by_uid.get(u["id"], {"credit": 0.0, "n": 0})
        today_total += us["credit"]
        if us["n"] > 0:
            active += 1
        has_key = "有" if keys.get(u["id"]) else "—"
        n_con = contribs.get(u["id"], 0)
        rows += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%.2f</td><td>%d</td>"
                 "<td>%s</td></tr>"
                 % (u["nickname"], u["email"], n_con, has_key, us["credit"], us["n"],
                    time.strftime("%m-%d %H:%M", time.localtime(u["created"]))))

    return f"""
<div class="card">
  <h1>用户总览</h1>
  <div class="sub">只有管理员能看。数据来自本站注册表、贡献登记与网关用量日志。</div>
  <div class="grid">
    <div class="stat"><div class="n">{len(users)}</div><div class="l">注册用户</div></div>
    <div class="stat"><div class="n">{active}</div><div class="l">今天有请求的人</div></div>
    <div class="stat"><div class="n">{sum(1 for u in users if keys.get(u['id']))}</div><div class="l">已领 Key</div></div>
    <div class="stat"><div class="n">{total_contrib}</div><div class="l">贡献的账号数</div></div>
    <div class="stat"><div class="n">{today_total:,.2f}</div><div class="l">今日全站消耗积分</div></div>
  </div>
</div>
<div class="card">
  <h2>注册用户</h2>
  <table>
    <tr><th>昵称</th><th>邮箱</th><th>贡献账号</th><th>Key</th><th>今日积分</th><th>今日请求</th><th>注册时间</th></tr>
    {rows or '<tr><td colspan="7" class="hint">还没有用户</td></tr>'}
  </table>
  <div class="hint">站外 Key（你自己 DSH 用的那把）今天用了 {outside['credit']:.2f} 积分、{outside['n']} 次请求，未计入上表。</div>
</div>"""


def panel_ok(token):
    """拿面板自己的令牌问一次 /panel/status，authenticated 为真才算面板管理员。

    这样面板里能看的人 = 知道面板密码的人，不用再造一套密码；
    算力池自己的站长账号只是额外的一条备用通道。
    """
    tok = (token or "").strip()
    if not tok:
        return False
    try:
        req = urllib.request.Request(UPSTREAM + "/panel/status",
                                     headers={"X-Panel-Token": tok})
        with urllib.request.urlopen(req, timeout=10) as r:
            return bool(json.loads(r.read().decode()).get("authenticated"))
    except Exception as exc:
        log("panel status probe failed: %s" % exc)
        return False


def _parse_ts(s):
    try:
        return time.mktime(time.strptime(str(s), "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return None


def expiry_watch(pkgs):
    """快过期的积分：只算还有余额、会过期、还没过期的包。

    积分包按到期时间从早到晚被消耗，所以「快过期」就是真正会被扔掉的那部分，
    不是账面数字。no_expiry 的长期包（2035 年那种）不参与。
    """
    now = time.time()
    rows = []
    for p in pkgs:
        remain = p.get("remain")
        if not isinstance(remain, (int, float)) or remain <= 0.001:
            continue
        if p.get("no_expiry") or p.get("is_expired"):
            continue
        ts = _parse_ts(p.get("expire_time"))
        if ts is None or ts <= now:
            continue
        rows.append({
            "ts": ts,
            "remain": round(remain, 2),
            "label": p.get("label") or "",
            "name": str(p.get("grant_reason") or p.get("name") or "")[:40],
            "at": time.strftime("%m-%d %H:%M", time.localtime(ts)),
        })
    rows.sort(key=lambda r: r["ts"])
    buckets = []
    for label, days in (("24 小时内", 1), ("3 天内", 3), ("7 天内", 7), ("30 天内", 30)):
        sel = [r for r in rows if (r["ts"] - now) <= days * 86400]
        buckets.append({"label": label,
                        "credit": round(sum(r["remain"] for r in sel), 2),
                        "packages": len(sel)})
    return {
        "buckets": buckets,
        "soon": rows[:12],
        "open_total": round(sum(r["remain"] for r in rows), 2),
        "open_packages": len(rows),
    }


# ── 多上游：把几家网关的数字摆在同一页 ─────────────────────────────
# 配置文件 /opt/join-panel/upstreams.json 是一个数组，每项：
#   {"id","name","base","pass_file","enabled","note",
#    "auth_header","auth_prefix","login_path","login_field"}
# 后四个是给别的家族的网关留的适配位（默认 X-Panel-Token + /panel/login + password）。
DEFAULT_UPSTREAMS = [{
    "id": "workbuddy", "name": "WorkBuddy", "base": UPSTREAM,
    "pass_file": PASS_FILE, "enabled": True, "note": "国际/国内双区",
}]
_up_tokens = {}
_up_cache = {"at": 0.0, "data": None}
_up_lock = threading.Lock()


def load_upstreams():
    try:
        with open(UPSTREAMS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return DEFAULT_UPSTREAMS
    except Exception as exc:
        log("upstreams.json unreadable: %s" % exc)
        return DEFAULT_UPSTREAMS
    out = []
    for e in raw if isinstance(raw, list) else []:
        if not isinstance(e, dict) or not e.get("base"):
            continue
        out.append({
            "id": str(e.get("id") or e.get("name") or "up"),
            "name": str(e.get("name") or e.get("id") or "up"),
            "base": str(e["base"]).rstrip("/"),
            "pass_file": str(e.get("pass_file") or ""),
            "note": str(e.get("note") or ""),
            "enabled": bool(e.get("enabled", True)),
            "auth_header": str(e.get("auth_header") or "X-Panel-Token"),
            "auth_prefix": str(e.get("auth_prefix") or ""),
            "login_path": str(e.get("login_path") or "/panel/login"),
            "login_field": str(e.get("login_field") or "password"),
            # 只有实现了 /accounts/login/callback 的网关才显示「粘贴回调」框
            "callback": bool(e.get("callback", False)),
        })
    return out or DEFAULT_UPSTREAMS


def _up_token(e, force=False):
    key = e["base"]
    if not force and _up_tokens.get(key):
        return _up_tokens[key]
    if not e["pass_file"]:
        raise RuntimeError("未配置面板密码文件")
    try:
        pw = open(e["pass_file"], encoding="utf-8").read().strip()
    except OSError:
        raise RuntimeError("读不到面板密码文件")
    if not pw:
        raise RuntimeError("面板密码文件是空的")
    req = urllib.request.Request(
        e["base"] + e["login_path"],
        data=json.dumps({e["login_field"]: pw}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        tok = json.loads(r.read().decode()).get("token")
    if not tok:
        raise RuntimeError("面板登录没拿到 token")
    _up_tokens[key] = tok
    return tok


def _up_call(e, method, path, payload=None, query=None, timeout=30):
    url = e["base"] + path + ("?" + urllib.parse.urlencode(query) if query else "")
    body = json.dumps(payload).encode() if payload is not None else None

    def once(tok):
        hdr = {e["auth_header"]: (e["auth_prefix"] + tok).strip(),
               "Content-Type": "application/json"}
        req = urllib.request.Request(url, data=body, headers=hdr, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    try:
        return once(_up_token(e))
    except urllib.error.HTTPError as exc:
        if exc.code != 401:
            raise
        return once(_up_token(e, force=True))


def _up_get(e, path, query=None):
    return _up_call(e, "GET", path, None, query)


def _up_post(e, path, payload=None):
    return _up_call(e, "POST", path, payload if payload is not None else {})


def up_by_id(uid):
    for e in load_upstreams():
        if e["id"] == uid:
            return e
    return None


def platform_detail(e):
    """一家平台的账号明细（管理视角，显示昵称；朋友那页仍然是匿名的）。"""
    out = {"id": e["id"], "name": e["name"], "note": e["note"],
           "callback": e.get("callback", False),
           "state": "ok", "accounts": [], "usage": {"used": 0.0, "requests": 0}}
    try:
        data = _up_get(e, "/accounts")
        rows = []
        for a in data.get("accounts") or []:
            c = a.get("credits") or {}
            ck = c.get("checkin") or {}
            rows.append({
                "uid": a.get("uid") or "",
                "nickname": a.get("nickname") or "（无昵称）",
                "remain": c.get("remain"),
                "size": c.get("size"),
                "checked": bool(ck.get("today_checked_in")),
                "streak": ck.get("streak_days") or 0,
                "today_credit": ck.get("today_credit") or 0,
                "need_relogin": bool(a.get("needRelogin") or a.get("tokenExpired")),
                "cooldown": bool(a.get("inCooldown")),
                "enabled": bool(a.get("enabled", True)),
            })
        out["accounts"] = rows
        try:
            an = _up_get(e, "/usage/analytics", {"range": "today", "realm": "cn"})
            w = (an.get("summary") or {}).get("window") or {}
            out["usage"] = {"used": round(w.get("credit") or 0, 2),
                            "requests": int(w.get("requests") or 0)}
        except Exception:
            pass
    except Exception as exc:
        log("platform %s detail failed: %s" % (e["id"], exc))
        out["state"] = "error"
        out["error"] = str(exc)[:120]
    return out


def platform_checkin(e, uid=None):
    payload = {"uid": uid} if uid else {}
    r = _up_post(e, "/accounts/checkin", payload)
    res = r.get("results") or []
    ok = sum(1 for x in res if x.get("ok"))
    return {"ok": True, "checked": ok, "total": len(res),
            "message": r.get("message") or r.get("msg") or ""}


LOGIN_START_PAYLOADS = ({"platform": "CLI", "realm": "cn"}, {})


def platform_login_start(e):
    """不同家族的发号接口形状不一样：先试带 platform 的，再试空体；
    链接字段也兼容 authUrl / authorization_url。"""
    last = ""
    for pl in LOGIN_START_PAYLOADS:
        try:
            r = _up_post(e, "/accounts/login/start", pl)
        except Exception as exc:
            last = str(exc)[:120]
            continue
        st = str(r.get("status") or "").lower()
        if st in ("failed", "error"):
            last = json.dumps(r, ensure_ascii=False)[:150]
            continue
        url = r.get("authUrl") or r.get("authorization_url") or r.get("url")
        state = r.get("state")
        if url and state:
            return {"ok": True, "state": state, "authUrl": url}
        last = json.dumps(r, ensure_ascii=False)[:150]
    return {"ok": False, "error": last or "上游没给授权链接"}


def platform_login_callback(e, state, callback_url):
    """把浏览器里那条回调 URL 交给网关完成换取令牌（远程浏览器场景）。"""
    if not state or not callback_url:
        raise RuntimeError("缺少 state 或回调地址")
    return _up_post(e, "/accounts/login/callback",
                    {"state": state, "callback_url": callback_url})


def platform_login_poll(e, state):
    try:
        r = _up_get(e, "/accounts/login/poll", {"state": state})
    except Exception:
        r = _up_post(e, "/accounts/login/poll", {"state": state})
    return {"ok": True, "status": str(r.get("status") or "unknown"),
            "message": str(r.get("message") or "")[:160]}


def upstreams_overview(ttl=15):
    """每家上游一份摘要：账号数、健康数、今日用量、剩余积分；失败的单独标出来。"""
    with _up_lock:
        if _up_cache["data"] is not None and time.time() - _up_cache["at"] < ttl:
            return _up_cache["data"]
        items = []
        for e in load_upstreams():
            base = {"id": e["id"], "name": e["name"], "note": e["note"]}
            if not e["enabled"]:
                items.append(dict(base, state="off", accounts=0, healthy=0,
                                  used=0.0, requests=0, remain=0.0))
                continue
            try:
                acc = _up_get(e, "/accounts").get("accounts") or []
                an = _up_get(e, "/usage/analytics", {"range": "today", "realm": "cn"})
                w = (an.get("summary") or {}).get("window") or {}
                remain = 0.0
                for a in acc:
                    r0 = (a.get("credits") or {}).get("remain")
                    if isinstance(r0, (int, float)):
                        remain += r0
                healthy = sum(1 for a in acc
                              if a.get("enabled", True) and not a.get("needRelogin")
                              and not a.get("tokenExpired") and not a.get("inCooldown"))
                items.append(dict(base, state="ok", accounts=len(acc), healthy=healthy,
                                  used=round(w.get("credit") or 0, 2),
                                  requests=int(w.get("requests") or 0),
                                  remain=round(remain, 2)))
            except Exception as exc:
                log("upstream %s failed: %s" % (e["id"], exc))
                items.append(dict(base, state="error", accounts=0, healthy=0,
                                  used=0.0, requests=0, remain=0.0,
                                  error=str(exc)[:100]))
        total = {
            "accounts": sum(i["accounts"] for i in items),
            "used": round(sum(i["used"] for i in items), 2),
            "requests": sum(i["requests"] for i in items),
            "remain": round(sum(i["remain"] for i in items), 2),
        }
        data = {"items": items, "total": total}
        _up_cache["data"] = data
        _up_cache["at"] = time.time()
        return data


def account_list():
    """账号快照，展示用数字一律走这里。

    网关的 /accounts 读的是内存里现成的账号表（实测 7 毫秒）；
    /accounts/credits 会逐个账号去腾讯那边现拉余额和积分包（实测 10 秒）。
    页面只是把数字摆出来，不该为此等十秒，所以统一读快照。
    """
    return api("GET", "/accounts").get("accounts") or []


# 「刷新余额」后台任务：网关的全池扫是拟人间隔（每个号多等 ~1.7 秒），
# 单号刷新不排队（实测 1.2 秒）。所以这里按号拆开、两路并发、每次错峰 200ms，
# 5 个号约 2.5 秒刷完，结果与全池扫一致。
_credits_job = {"running": False, "done": 0, "total": 0, "started": 0.0,
                "error": "", "at": 0.0}
_job_lock = threading.Lock()


def _credits_refresh_worker(uids):
    done = 0
    err = ""
    try:
        def one(uid):
            return api("POST", "/accounts/credits", {"uid": uid})

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = []
            for uid in uids:
                futures.append(pool.submit(one, uid))
                time.sleep(0.2)
            for f in futures:
                try:
                    f.result(timeout=60)
                except Exception as exc:
                    err = str(exc)[:120]
                with _job_lock:
                    _credits_job["done"] = _credits_job["done"] + 1
                done += 1
    except Exception as exc:
        err = str(exc)[:120]
    finally:
        with _job_lock:
            _credits_job["running"] = False
            _credits_job["error"] = err
            _credits_job["at"] = time.time()
        # 刷完作废面板快照的缓存，否则页面还会拿到刷新前那份
        with _lock:
            _overview["at"] = 0.0
        log("credits refresh done=%d err=%s" % (done, err))


def start_credits_refresh():
    """起一次后台刷新；已经在跑就直接回当前进度。"""
    with _job_lock:
        if _credits_job["running"]:
            return dict(_credits_job)
        uids = [a.get("uid") for a in account_list() if a.get("uid")]
        _credits_job.update({"running": True, "done": 0, "total": len(uids),
                             "started": time.time(), "error": ""})
    threading.Thread(target=_credits_refresh_worker, args=(uids,), daemon=True).start()
    log("credits refresh start n=%d" % len(uids))
    with _job_lock:
        return dict(_credits_job)


def credits_job_state():
    with _job_lock:
        return dict(_credits_job)


def overview_data():
    """面板「算力池」页要的全部数字，一次算完给前端。"""
    errors = []
    usage = today_usage()

    used = usage["credit"]
    requests = usage["requests"]
    tokens = usage["tokens"]

    accounts = []
    raw_pkgs = []
    try:
        for a in account_list():
            c = a.get("credits") or {}
            ck = c.get("checkin") or {}
            remain = c.get("remain")
            size = c.get("size")
            per = usage["by_account"].get(a.get("uid")) or {"credit": 0.0, "n": 0}
            for p in c.get("packages") or []:
                raw_pkgs.append((a.get("uid"), p))
            accounts.append({
                "uid": a.get("uid") or "",
                "remain": remain if isinstance(remain, (int, float)) else None,
                "size": size if isinstance(size, (int, float)) else None,
                "daily_credit": ck.get("daily_credit") or 0,
                "today_credit": ck.get("today_credit") or 0,
                "checked": bool(ck.get("today_checked_in")),
                "streak": ck.get("streak_days") or 0,
                "today_credit_used": round(per["credit"], 2),
                "today_requests": per["n"],
                "enabled": bool(a.get("enabled", True)),
                "need_relogin": bool(a.get("needRelogin") or a.get("tokenExpired")),
                "cooldown": bool(a.get("inCooldown")),
            })
    except Exception as exc:
        log("overview credits failed: %s" % exc)
        errors.append("账号余额读不到")

    with db() as conn:
        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        contribs = {r["uid"]: r["n"] for r in conn.execute(
            "SELECT uid, count(*) AS n FROM contrib GROUP BY uid")}
        keys = {r["uid"]: r["key_id"] for r in conn.execute(
            "SELECT uid, key_id FROM user_keys")}
        providers = {r["account_uid"]: r["nickname"] for r in conn.execute(
            "SELECT c.account_uid, u.nickname FROM contrib c JOIN users u ON u.id = c.uid")}

    # 账号匿名：只说「谁提供的第几号账号」，不吐 workbuddy 那边的昵称
    seen = {}
    for idx, a in enumerate(accounts, 1):
        owner = providers.get(a["uid"])
        if owner:
            n = seen[owner] = seen.get(owner, 0) + 1
            a["label"] = "%s 提供的第%s号账号" % (owner, _cn_num(n))
        else:
            a["label"] = "池内第%s号账号（未登记提供者）" % _cn_num(idx)

    remain_sum = sum(a["remain"] for a in accounts if a["remain"] is not None)
    gain_sum = sum(a["today_credit"] for a in accounts)
    pending = sum(a["daily_credit"] for a in accounts if not a["checked"] and a["enabled"])
    healthy = sum(1 for a in accounts if a["enabled"] and not a["need_relogin"] and not a["cooldown"])

    label_of = {a["uid"]: a["label"] for a in accounts}
    expiring = expiry_watch([dict(p, label=label_of.get(uid, "")) for uid, p in raw_pkgs])

    owner_of = {}
    for u in users:
        kid = keys.get(u["id"])
        if kid:
            owner_of[kid] = u["id"]
    per_user = {}
    outside = {"credit": 0.0, "requests": 0}
    for kid, rec in usage["by_key"].items():
        uid = owner_of.get(kid)
        if uid is None:
            outside["credit"] += rec["credit"]
            outside["requests"] += rec["n"]
        else:
            a = per_user.setdefault(uid, {"credit": 0.0, "requests": 0})
            a["credit"] += rec["credit"]
            a["requests"] += rec["n"]

    user_rows = []
    active = 0
    for u in users:
        s = per_user.get(u["id"], {"credit": 0.0, "requests": 0})
        if s["requests"]:
            active += 1
        user_rows.append({
            "nickname": u["nickname"],
            "email": u["email"],
            "contrib": contribs.get(u["id"], 0),
            "has_key": bool(keys.get(u["id"])),
            "credit": round(s["credit"], 2),
            "requests": s["requests"],
            "created": time.strftime("%m-%d %H:%M", time.localtime(u["created"])),
        })

    return {
        "ok": True,
        "now": time.strftime("%H:%M:%S"),
        "pool": {
            "used": round(used, 2),
            "requests": int(requests),
            "tokens": int(tokens),
            "log_requests": usage["requests"],
            "remain": round(remain_sum, 2),
            "today_gain": round(gain_sum, 2),
            "pending_signin": round(pending, 2),
            "available": round(remain_sum + pending, 2),
            "account_count": len(accounts),
            "healthy": healthy,
            "accounts": accounts,
            "errors": errors,
        },
        "users": {
            "total": len(users),
            "active": active,
            "keys": sum(1 for u in users if keys.get(u["id"])),
            "contribs": sum(contribs.values()),
        },
        "user_rows": user_rows,
        "outside": {"credit": round(outside["credit"], 2), "requests": outside["requests"]},
        "expiring": expiring,
        "upstreams": upstreams_overview(),
    }


_overview = {"at": 0.0, "data": None}


def overview_cached(ttl=15):
    """面板 20 秒轮询一次，翻用量日志不便宜，15 秒内的请求共用同一份结果。"""
    with _lock:
        if _overview["data"] is not None and time.time() - _overview["at"] < ttl:
            return _overview["data"], True
    data = overview_data()
    with _lock:
        _overview["data"] = data
        _overview["at"] = time.time()
    return data, False


def nav(user=None, active=""):
    if user is None:
        return f'<div class="nav"><b>算力池</b></div>'
    items = [("dashboard", "共用额度"), ("accounts", "添加账号"), ("keys", "API Key")]
    if is_admin(user):
        items.append(("admin", "用户总览"))
    links = "".join(f'<a href="/join/{k}" class="{"on" if k==active else ""}">{t}</a>' for k, t in items)
    return (f'<div class="nav"><b>算力池</b>{links}<span class="sp"></span>'
            f'<span class="who">{user["nickname"]} · {user["email"]}</span>'
            f'<a href="#" onclick="logout();return false">退出</a></div>')


def page(title, body, user=None, active=""):
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>{CSS}</style></head><body>{nav(user, active)}<div class="wrap">{body}</div>
<script>
async function post(p,b){{const r=await fetch(p,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(b||{{}})}});return r.json();}}
async function logout(){{await post('/join/api/logout');location.href='/join/';}}
</script></body></html>"""


AUTH_PAGE = """
<div class="card" style="max-width:420px;margin:60px auto">
  <h1>算力池</h1>
  <div class="sub">和朋友共用一个模型池子：注册后可以添加账号、领自己的 API Key。</div>
  <div id="tabs" style="display:flex;gap:8px;margin-bottom:8px">
    <button id="tab-login" onclick="switchTab('login')">登录</button>
    <button id="tab-reg" class="ghost" onclick="switchTab('reg')">注册</button>
  </div>
  <div id="form-reg" style="display:none">
    <label>昵称</label><input id="r-nick" placeholder="怎么称呼你">
    <label>邮箱</label><input id="r-mail" type="email" placeholder="you@example.com">
    <label>密码</label><input id="r-pass" type="password" placeholder="至少 6 位">
    <button style="margin-top:16px;width:100%" onclick="reg()">注册并登录</button>
  </div>
  <div id="form-login">
    <label>邮箱</label><input id="l-mail" type="email" placeholder="you@example.com">
    <label>密码</label><input id="l-pass" type="password" placeholder="密码">
    <button style="margin-top:16px;width:100%" onclick="doLogin()">登录</button>
  </div>
  <div class="hint" id="h"></div>
</div>
<script>
function switchTab(t){
  const reg = t==='reg';
  document.getElementById('form-reg').style.display = reg?'block':'none';
  document.getElementById('form-login').style.display = reg?'none':'block';
  document.getElementById('tab-reg').className = reg?'':'ghost';
  document.getElementById('tab-login').className = reg?'ghost':'';
}
async function doLogin(){
  const h=document.getElementById('h');
  const r = await post('/join/api/login',{
      email: document.getElementById('l-mail').value.trim(),
      password: document.getElementById('l-pass').value});
  if(r.ok){location.href='/join/dashboard';}else{h.textContent=r.error||'登录失败';h.className='hint bad';}
}
switchTab('login');
async function reg(){
  const h=document.getElementById('h');
  const r = await post('/join/api/register',{
      nickname: document.getElementById('r-nick').value.trim(),
      email: document.getElementById('r-mail').value.trim(),
      password: document.getElementById('r-pass').value});
  if(r.ok){location.href='/join/dashboard';}else{h.textContent=r.error||'注册失败';h.className='hint bad';}
}
// 任何未捕获的脚本错误都显示出来，别再出现「点了没反应」
window.addEventListener('error', function(e){
  const h=document.getElementById('h');
  if(h){ h.textContent='页面出错：'+e.message; h.className='hint bad'; }
});
</script>
"""


def attribute_account(state, platform='workbuddy'):
    """poll 成功后，把「最近新加、还没登记」的那个账号记到发起者名下。

    并发添加时可能认错人，所以只用来做「谁提供的第一号」这种展示，不参与权限判断。
    """
    try:
        with db() as conn:
            row = conn.execute("SELECT uid FROM login_states WHERE state=?", (state,)).fetchone()
            known = {r["account_uid"] for r in conn.execute(
                "SELECT account_uid FROM contrib WHERE platform=?", (platform,))}
        if not row:
            return
        e = up_by_id(platform)
        pool = (platform_detail(e)["accounts"] if (e and e["enabled"]) else account_list())
        cands = [a for a in pool if a.get("uid") not in known]
        if not cands:
            return
        best = max(cands, key=lambda a: a.get("addedAt") or 0)
        with db() as conn:
            conn.execute("INSERT OR REPLACE INTO contrib(account_uid,uid,at,platform) VALUES(?,?,?,?)",
                         (best["uid"], row["uid"], time.time(), platform))
        log("attributed %s (%s) -> uid %s" % (best.get("uid", "")[:8], platform, row["uid"]))
    except Exception as exc:
        log("attribute failed: %s" % exc)

_usage_cache = {"at": 0.0, "data": None}
_usage_lock = threading.Lock()


def _fetch_today_usage():
    """网关已经把今天的账聚合好了，一次拿全：总量 / 按 Key / 按账号。

    /usage/analytics 实测 7 毫秒、200KB；翻 /usage/recent 要好几百行、1.2MB、
    每页 40 毫秒，而且每多一个人同时打开页面就多解析一遍 —— 那才是「人一多就卡」
    的真正原因。这里换成聚合接口，外面再加 5 秒共享缓存。
    """
    d = api("GET", "/usage/analytics", query={"range": "today", "realm": "cn"})
    w = (d.get("summary") or {}).get("window") or {}
    by_key, by_account = {}, {}
    for k in d.get("keys") or []:
        kw = k.get("window") or {}
        by_key[k.get("key") or "?"] = {"credit": kw.get("credit") or 0,
                                       "n": kw.get("requests") or 0}
    for a in d.get("accounts") or []:
        aw = a.get("window") or {}
        by_account[a.get("uid") or "?"] = {"credit": aw.get("credit") or 0,
                                           "n": aw.get("requests") or 0}
    return {"by_key": by_key, "by_account": by_account,
            "requests": w.get("requests") or 0,
            "tokens": w.get("total_tokens") or 0,
            "credit": w.get("credit") or 0}


def today_usage(ttl=5):
    """带共享缓存的今日用量；并发访问时只让一个人去取，其余直接读结果。"""
    with _usage_lock:
        cached = _usage_cache["data"]
        if cached is not None and time.time() - _usage_cache["at"] < ttl:
            return cached
        data = _fetch_today_usage()
        _usage_cache["data"] = data
        _usage_cache["at"] = time.time()
        return data


def today_by_key():
    """按 API Key 汇总今天的消耗（key 的 id -> credit / 请求数）。"""
    return today_usage()["by_key"]

def _cn_num(n):
    names = "零一二三四五六七八九十"
    if n <= 10:
        return names[n]
    if n < 20:
        return "十" + names[n - 10]
    if n < 100:
        return names[n // 10] + "十" + (names[n % 10] if n % 10 else "")
    return str(n)


def _provider_nicknames():
    """account_uid -> 提供者昵称。没登记进 contrib 的账号，显示成「池内 N 号账号」。"""
    try:
        with db() as conn:
            rows = conn.execute(
                "SELECT c.account_uid, u.nickname FROM contrib c JOIN users u ON u.id = c.uid").fetchall()
        return {r["account_uid"]: r["nickname"] for r in rows}
    except Exception:
        return {}


def dashboard_body(user):
    """今日视角 + 匿名化的账号列表：只说「谁提供的第一号账号」，不暴露账号昵称。"""
    today_used = today_requests = today_tokens = 0.0
    today_gain = 0.0
    total_remain = 0.0
    rows = ""
    errors = []
    providers = _provider_nicknames()
    per_owner = {}
    raw_pkgs = []

    try:
        u = today_usage()
        today_used = u["credit"]
        today_requests = u["requests"]
        today_tokens = u["tokens"]
    except Exception as exc:
        log("dashboard usage failed: %s" % exc)
        errors.append("今日用量读不到")

    try:
        idx = 0
        for a in account_list():
            idx += 1
            c = a.get("credits") or {}
            remain = c.get("remain")
            if not isinstance(remain, (int, float)):
                errors.append("第 %d 号账号余额读取失败" % idx)
                continue
            total_remain += remain
            ck = c.get("checkin") or {}
            gain = ck.get("today_credit") or 0
            today_gain += gain if isinstance(gain, (int, float)) else 0

            owner = providers.get(a.get("uid"))
            if owner:
                per_owner[owner] = per_owner.get(owner, 0) + 1
                label = "%s 提供的第%s号账号" % (owner, _cn_num(per_owner[owner]))
            else:
                label = "池内第%s号账号（未登记提供者）" % _cn_num(idx)
            for p in c.get("packages") or []:
                raw_pkgs.append(dict(p, label=label))

            pct = remain / (c.get("size") or remain or 1) * 100
            if ck.get("today_checked_in"):
                mark = '<span class="pill ok">已签 %s 天</span>' % ck.get("streak_days", "")
            else:
                mark = '<span class="pill warn">未签到</span>'
            if a.get("needRelogin") or a.get("tokenExpired"):
                health = '<span class="pill warn">需重新授权</span>'
            elif a.get("inCooldown"):
                health = '<span class="pill warn">冷却中</span>'
            elif not a.get("enabled"):
                health = '<span class="pill">已停用</span>'
            else:
                health = '<span class="pill ok">正常</span>'
            rows += (
                "<tr><td>%s</td><td>%.1f</td>"
                '<td><div class="bar"><i style="width:%.0f%%"></i></div></td>'
                "<td>%s</td><td>%s</td></tr>"
                % (label, remain, max(0, min(100, pct)), mark, health))
    except Exception as exc:
        log("dashboard credits failed: %s" % exc)
        errors.append("账号余额读不到")

    if not rows:
        rows = '<tr><td colspan="5" class="hint">池子里还没有可读余额的账号</td></tr>'

    # 今日各用户用量：按 key_id 找到用户
    user_rows = ""
    try:
        with db() as conn:
            owners = {r["key_id"]: r["nickname"] for r in conn.execute(
                "SELECT k.key_id, u.nickname FROM user_keys k JOIN users u ON u.id = k.uid WHERE k.key_id IS NOT NULL")}
        per_key = today_by_key()
        agg = {}
        for kid, rec in per_key.items():
            who = owners.get(kid, "站外 Key（管理员）")
            a = agg.setdefault(who, {"credit": 0.0, "n": 0})
            a["credit"] += rec["credit"]
            a["n"] += rec["n"]
        for who, a in sorted(agg.items(), key=lambda kv: -kv[1]["credit"]):
            user_rows += "<tr><td>%s</td><td>%.2f</td><td>%d</td></tr>" % (who, a["credit"], a["n"])
    except Exception as exc:
        log("per-user usage failed: %s" % exc)
    if not user_rows:
        user_rows = '<tr><td colspan="3" class="hint">今天还没有人用</td></tr>'

    available_today = total_remain + today_gain
    note = ('<div class="hint warn">%s</div>' % "；".join(errors[:3])) if errors else ""

    expiring = expiry_watch(raw_pkgs)
    exp_rows = ""
    for r in expiring["soon"]:
        exp_rows += ("<tr><td>%s</td><td>%.2f</td><td>%s</td><td>%s</td></tr>"
                     % (r["at"], r["remain"], r["label"], r["name"]))
    if not exp_rows:
        exp_rows = '<tr><td colspan="4" class="hint">没有带到期时间的余额</td></tr>'
    bk = {b["label"]: b for b in expiring["buckets"]}

    def _bstat(label):
        b = bk.get(label) or {"credit": 0, "packages": 0}
        return ('<div class="stat"><div class="n">%.1f</div>'
                '<div class="l">%s（%d 个包）</div></div>'
                % (b["credit"], label, b["packages"]))

    # 多平台总览：同一个页面把各家网关的数字摆在一起
    up = upstreams_overview()
    up_rows = ""
    for it in up["items"]:
        if it["state"] == "ok":
            pill = '<span class="pill ok">在线</span>'
            nums = ("<td>%d（可用 %d）</td><td>%.1f</td><td>%d</td><td>%.1f</td>"
                    % (it["accounts"], it["healthy"], it["used"], it["requests"], it["remain"]))
        elif it["state"] == "off":
            pill = '<span class="pill">未接入</span>'
            nums = '<td>—</td><td>—</td><td>—</td><td>—</td>'
        else:
            pill = '<span class="pill warn">读取失败</span>'
            nums = ('<td>—</td><td>—</td><td>—</td><td>—</td>')
        up_rows += ("<tr><td>%s<div class=\"hint\" style=\"margin:2px 0 0;min-height:0\">%s</div></td>"
                    "<td>%s</td>%s</tr>"
                    % (it["name"], it.get("note") or "", pill, nums))
    up_total = up["total"]
    up_note = ""
    if any(i["state"] in ("off", "error") for i in up["items"]):
        up_note = ('<div class="hint">灰色的那几家还没接网关，所以只有占位；接上后同一个页面自动出数。'
                   '在 <code>/opt/join-panel/upstreams.json</code> 里加一条就能多一家。</div>')

    return f"""
<div class="card">
  <div class="sub" style="margin-bottom:2px">今天这个池子用了多少</div>
  <div class="hero"><span class="big">{today_used:,.2f}</span>
    <span class="unit">积分 · 今日累计（{int(today_requests)} 次请求、{today_tokens / 10000:,.0f} 万 tokens）</span></div>
  <div class="grid">
    <div class="stat"><div class="n">{total_remain:,.1f}</div><div class="l">池子剩余积分</div></div>
    <div class="stat"><div class="n">+{today_gain:,.0f}</div><div class="l">今日签到到账</div></div>
    <div class="stat"><div class="n">{available_today:,.1f}</div><div class="l">今天还能用（剩余+签到）</div></div>
  </div>
  {note}
</div>
<div class="card">
  <h2>多平台总览</h2>
  <div class="sub" style="margin:0 0 10px">几家网关的数字摆在一块看；合计那行只算已接入的。</div>
  <table>
    <tr><th>平台</th><th>状态</th><th>账号</th><th>今日消耗</th><th>今日请求</th><th>剩余积分</th></tr>
    {up_rows}
    <tr><td><b>合计</b></td><td></td><td>{up_total['accounts']}</td><td>{up_total['used']:,.1f}</td><td>{up_total['requests']}</td><td>{up_total['remain']:,.1f}</td></tr>
  </table>
  {up_note}
</div>
<div class="card">
  <h2>快过期的积分</h2>
  <div class="sub" style="margin:0 0 10px">积分包按到期时间从早到晚被消耗，下面是还有余额的包什么时候到期——这部分不用掉就真浪费了。</div>
  <div class="grid">{_bstat("24 小时内")}{_bstat("3 天内")}{_bstat("7 天内")}{_bstat("30 天内")}</div>
  <table>
    <tr><th>什么时候过期</th><th>还剩</th><th>账号</th><th>来源</th></tr>
    {exp_rows}
  </table>
  <div class="hint">会过期的包共 {expiring['open_packages']} 个、合计 {expiring['open_total']:,.1f} 积分；无到期日的长期包不计。</div>
</div>
<div class="card">
  <h2>今日各用户用量</h2>
  <table>
    <tr><th>用户</th><th>今日消耗积分</th><th>请求数</th></tr>
    {user_rows}
  </table>
  <div class="hint">按每个人自己的 API Key 统计今天产生的消耗；站外 Key（如管理员自用）单列。</div>
</div>
<div class="card">
  <h2>账号明细（已隐去账号名）</h2>
  <table>
    <tr><th>账号</th><th>剩余积分</th><th>剩余比例</th><th>今日签到</th><th>状态</th></tr>
    {rows}
  </table>
  <div class="hint">只显示「谁提供的第几号账号」，不显示账号本身的昵称与 ID。
  workbuddy 的额度按周期包算，每天签到给每个账号补一笔，没有「每天只能用 X」的硬上限。</div>
</div>"""


def accounts_body(user):
    plats = [e for e in load_upstreams() if e["enabled"]]
    rows = ""
    for e in plats:
        try:
            d = platform_detail(e)
            n = len(d["accounts"]) if d.get("state") == "ok" else 0
            state = d.get("state")
        except Exception:
            n, state = 0, "error"
        pill = ('<span class="pill ok">在线</span>' if state == "ok"
                else ('<span class="pill warn">读取失败</span>' if state == "error" else '<span class="pill">未接入</span>'))
        cbflag = "true" if e["callback"] else "false"
        rows += (
            '<div class="card">'
            '<h2 style="display:flex;align-items:center;gap:8px">%s %s</h2>'
            '<div class="sub" style="margin:0 0 10px">%s</div>'
            '<div class="btnrow">'
            '<button id="go-%s" onclick="startAdd(\'%s\',%s)">添加 %s 账号</button>'
            '<span class="hint" id="h-%s" style="margin:0"></span>'
            '</div>'
            '<div id="stage-%s"></div>'
            '<div class="hint">这家现在有 <b>%d</b> 个账号在你的池子里。</div>'
            '</div>'
            % (e["name"], pill, e["note"] or "用官方授权把账号并进池子，密码不经过这里",
               e["id"], e["id"], cbflag, e["name"], e["id"], e["id"], n)
        )

    return """
<div class="card">
  <h1>添加账号</h1>
  <div class="sub">三家都能加：每家单独授权，密码都在官方页面输入，这里只拿授权凭证。
  加进来的账号供池子里所有人共用，你也能用别人加的号。</div>
</div>
""" + rows + """
<div class="card">
  <h2>加号之后</h2>
  <ul class="faq">
    <li>授权完成会自动并入池子，页面上那家账号数会 +1，不用你手动刷新页面。</li>
    <li>加进来只加不用的账号，调度器每天会帮它签到领额度。</li>
    <li>同一家可以加多个号；不同家互不影响。</li>
  </ul>
</div>
<div class="card">
  <h2>卡住时看这里</h2>
  <ul class="faq">
    <li><b>点了「添加」没反应</b>：等两三秒，按钮下面会出官方链接；一直不出多半是被限流，等一分钟再来。</li>
    <li><b>官方页面打不开或登录不上</b>：换浏览器或关掉代理再试。</li>
    <li><b>提示「操作太频繁」</b>：同一出口 IP 十分钟内点太多次，歇一会儿。</li>
  </ul>
</div>
<script>
var timers = {};
async function submitCb(pid, state){
  var h = document.getElementById('h-' + pid);
  var ta = document.getElementById('cb-' + pid);
  var url = (ta && ta.value || '').trim();
  if (!url) { h.textContent = '先把地址栏那条网址粘进来'; h.className = 'hint bad'; return; }
  h.textContent = '正在提交回调…'; h.className = 'hint';
  var r = await post('/join/api/account/callback', { state: state, callback_url: url });
  if (!r.ok) { h.textContent = r.error || '提交失败'; h.className = 'hint bad'; return; }
  h.textContent = '已提交，等网关换取令牌…'; h.className = 'hint';
}
async function startAdd(pid, canPaste){
  var h = document.getElementById('h-' + pid);
  var stage = document.getElementById('stage-' + pid);
  var btn = document.getElementById('go-' + pid);
  if (timers[pid]) { clearInterval(timers[pid]); timers[pid] = null; }
  if (btn) btn.disabled = true;
  h.textContent = '正在申请授权链接…'; h.className = 'hint';
  var r = await post('/join/api/account/start', { platform: pid });
  if (!r.ok) {
    h.textContent = r.error || '申请失败'; h.className = 'hint bad';
    if (btn) btn.disabled = false;
    return;
  }
  var html = '<div class="btnrow"><a class="link" target="_blank" rel="noopener" href="' + r.authUrl
    + '">打开 ' + (r.name || pid) + ' 官方页面登录并授权 →</a></div>';
  if (canPaste) {
    html += '<div class="hint" style="margin-top:10px">在手机或别的电脑上打开的：登录完会跳到 127.0.0.1 报「拒绝连接」，'
      + '把那时地址栏里整条网址复制下来贴到下面就行。</div>'
      + '<div style="display:flex;gap:8px;margin-top:6px;align-items:flex-start">'
      + '<textarea id="cb-' + pid + '" rows="2" placeholder="粘贴 http://127.0.0.1:xxxxx/authorize?... 整条网址" '
      + 'style="flex:1;font-size:12px;padding:8px;border:1px solid var(--line);border-radius:7px;background:#fdfcf8"></textarea>'
      + '<button class="ghost" data-cb="' + pid + '" data-state="' + r.state + '">提交回调</button></div>';
  } else {
    html += '<div class="hint" style="margin-top:10px">手机、电脑都能开：登录并同意后直接回到本页，'
      + '这里会自动变成「已加入」，不用复制任何网址。'
      + '要是官方页面最后跳到 127.0.0.1 报「拒绝连接」，授权其实已经记下了，直接回这一页等着就行。</div>';
  }
  stage.innerHTML = html;
  h.textContent = '等你完成授权…（页面别关）'; h.className = 'hint';
  if (canPaste) {
    var cbBtn = stage.querySelector('button[data-cb]');
    if (cbBtn) cbBtn.addEventListener('click', function () {
      submitCb(cbBtn.getAttribute('data-cb'), cbBtn.getAttribute('data-state'));
    });
  }
  if (btn) { btn.disabled = false; btn.textContent = '重新发起'; }
  var state = r.state, n = 0;
  timers[pid] = setInterval(async function(){
    n++;
    var q;
    try { q = await post('/join/api/account/poll', { state: state }); } catch (e) { return; }
    if (q.status === 'pending') { h.textContent = '等你完成授权…（页面别关）'; return; }
    clearInterval(timers[pid]); timers[pid] = null;
    if (q.status === 'ok') {
      h.textContent = '已加入池子，谢谢！'; h.className = 'hint ok';
      stage.innerHTML = '';
      setTimeout(function(){ location.reload(); }, 1200);
    } else if (n < 40) {
      h.textContent = (q.message || '授权没走完') + '，可以点「重新发起」再来一次。';
      h.className = 'hint warn';
    }
  }, 3000);
}
</script>"""

KEY_JS = """
<script>
async function make(){
  const h=document.getElementById('h');
  const btn=document.getElementById('mk');
  if(btn)btn.disabled=true;
  h.textContent='正在生成…';h.className='hint';
  const r=await post('/join/api/key/create',{});
  if(!r.ok){
    h.textContent=r.error||'生成失败';h.className='hint bad';
    if(btn)btn.disabled=false;
    return;
  }
  h.textContent='生成好了，下面是完整 Key——只给这一次，先复制走。';h.className='hint ok';
  document.getElementById('show').innerHTML=
    '<div class="big-key" id="mykey">'+r.key+'</div>'
    +'<div class="btnrow"><button class="ghost" onclick="copyKey()">复制 Key</button></div>';
}
async function copyText(t){
  // 站点是 http，navigator.clipboard 在非安全上下文里没有，先试老办法
  const ta=document.createElement('textarea');
  ta.value=t;ta.style.position='fixed';ta.style.top='-1000px';
  document.body.appendChild(ta);ta.select();
  let ok=false;
  try{ok=document.execCommand('copy');}catch(e){}
  ta.remove();
  if(ok)return true;
  if(navigator.clipboard&&navigator.clipboard.writeText){
    try{await navigator.clipboard.writeText(t);return true;}catch(e){}
  }
  return false;
}
function selectEl(el){
  try{
    const r=document.createRange();r.selectNodeContents(el);
    const s=getSelection();s.removeAllRanges();s.addRange(r);
  }catch(e){}
}
async function copyKey(){
  const h=document.getElementById('h');
  const el=document.getElementById('mykey');
  if(!el)return;
  let t=el.textContent.trim();
  if(t.indexOf('…')>=0){
    const r=await post('/join/api/key/show',{});
    if(!r.ok){h.textContent=r.error||'取不到完整 Key';h.className='hint bad';return;}
    t=r.key;el.textContent=t;
  }
  const ok=await copyText(t);
  if(ok){
    h.textContent='已复制到剪贴板';h.className='hint ok';
  }else{
    selectEl(el);
    h.textContent='浏览器不让自动复制，已经帮你选中了，按 Ctrl+C（Mac 是 Command+C）就行';h.className='hint warn';
  }
}
async function revealKey(){
  const h=document.getElementById('h');
  const el=document.getElementById('mykey');
  if(!el)return;
  if(el.dataset.revealed==='1'){
    el.textContent=el.dataset.mask||'';el.dataset.revealed='0';return;
  }
  const r=await post('/join/api/key/show',{});
  if(!r.ok){h.textContent=r.error||'取不到完整 Key';h.className='hint bad';return;}
  if(!el.dataset.mask)el.dataset.mask=el.textContent.trim();
  el.textContent=r.key;el.dataset.revealed='1';
  h.textContent='完整 Key 已展开，别截图发群里。';h.className='hint warn';
}
</script>"""


def keys_body(user, public_base=""):
    # 站点域名不写死：默认用请求里的 Host，部署在别的域名/端口也能对；
    # 反向代理改了 Host 时用环境变量 PUBLIC_BASE 覆盖，例如 https://pool.example.com
    base = (public_base.rstrip("/") if public_base else "") + "/wb/v1"
    with db() as conn:
        row = conn.execute("SELECT * FROM user_keys WHERE uid=?", (user["id"],)).fetchone()
        contribs = conn.execute("SELECT count(*) FROM contrib WHERE uid=?", (user["id"],)).fetchone()[0]

    if row:
        own = (
            '<div class="sub">这把 Key 就是你调池子的凭证，用量按它单独算。'
            '默认只显示前缀，需要完整值时点「显示完整 Key」或直接「复制」。</div>'
            f'<div class="big-key" id="mykey">{row["key"][:14]}…</div>'
            '<div class="btnrow">'
            '<button class="ghost" onclick="revealKey()">显示完整 Key</button>'
            '<button class="ghost" onclick="copyKey()">复制</button>'
            '<span class="pill ok">已领取</span>'
            f'<span class="pill">名称：{row["name"]}</span>'
            '</div>'
            '<div class="hint" id="h">别把 Key 贴到群里或提交到 GitHub；谁拿到它，用掉的额度都记在你名下。</div>'
        )
    else:
        gate = ('' if (contribs or is_admin(user)) else
                '<div class="hint warn">领 Key 之前先用「添加账号」贡献一个账号——'
                '池子是大家凑出来的，谁加了账号谁才能领。</div>')
        own = (
            '<div class="sub">生成一把只属于你的 Key，用它调这个池子。额度是大家共用的，'
            '但用量按 Key 分开统计，所以别把自己的 Key 给别人用。</div>'
            + gate +
            '<div class="btnrow"><button id="mk" onclick="make()">生成我的 API Key</button>'
            '<span class="hint" id="h"></span></div>'
            '<div style="margin-top:14px" id="show"></div>'
        )

    return f"""
<div class="card"><h1>API Key</h1>{own}</div>

<div class="card">
  <h2>三步接入</h2>
  <ol class="steps">
    <li><b>填 API Key</b>
      <div class="hint">客户端要的是 <code>Authorization: Bearer 你的key</code>；多数软件只让你粘 key，它自己补 Bearer。</div>
    </li>
    <li><b>填 Base URL</b>
      <div class="hint">就是 <code>{base}</code>，填到 <code>/wb/v1</code> 为止。有的客户端会自动补 <code>/chat/completions</code>，不用你加。</div>
    </li>
    <li><b>选模型</b>
      <div class="hint"><code>deepseek-v4.1-flash</code> 快且便宜，日常写代码够用；<code>deepseek-v4-pro</code> 更聪明也更费积分。
      池子里现在还挂着哪些模型，看 <a class="link" href="/wb/v1/models" target="_blank" rel="noopener">/wb/v1/models</a>（要带 key 才给看）。</div>
    </li>
  </ol>
</div>

<div class="card">
  <h2>先拿命令行试通，再接客户端</h2>
  <div class="sub">把 &lt;你的key&gt; 换成上面那串，能回一条 JSON 就说明通了：</div>
  <pre>curl {base}/chat/completions \\
  -H "Authorization: Bearer &lt;你的key&gt;" \\
  -H "Content-Type: application/json" \\
  -d '{{"model":"deepseek-v4.1-flash","messages":[{{"role":"user","content":"你好"}}]}}'</pre>
  <div class="hint">Windows 的 PowerShell 里 curl 是别名，换成 <code>curl.exe</code>；引号也别用中文引号。</div>
</div>

<div class="card">
  <h2>报错对不上时看这里</h2>
  <table>
    <tr><th>你看到</th><th>多半是什么</th><th>怎么处理</th></tr>
    <tr><td><code>401</code> Unauthorized</td><td>key 贴错、少写 <code>Bearer </code>、或者 key 被删了</td><td>回上面重新复制一次；还是不行就重生成</td></tr>
    <tr><td><code>404</code> model not found</td><td>模型名拼错，或用了池子里没有的模型</td><td>照 <a class="link" href="/wb/v1/models" target="_blank" rel="noopener">模型清单</a> 里的名字填</td></tr>
    <tr><td><code>429</code> / 余额不足</td><td>key 被多人共用，或池里账号都在冷却</td><td>等几十秒重试；一直这样找管理员</td></tr>
    <tr><td>400 上下文太长</td><td>一次塞了太多历史，超过单次上限</td><td>新开会话，或把长文件分几次喂</td></tr>
    <tr><td>502 / 转圈超时</td><td>池子里账号临时不可用</td><td>过一会儿再试，失败不扣积分</td></tr>
  </table>
</div>

<div class="card">
  <h2>用之前知道三件事</h2>
  <ul class="faq">
    <li>额度是全池共享的：你多用一点，别人就少一点；签到送的日额度当天不用会过期，看「共用额度」页的「快过期的积分」。</li>
    <li>Key 一人一把、不能重建：删了旧的才能生成新的，所以别随手删。</li>
    <li>这是朋友的私下池子，别公开、别拿去接商用业务；出问题找管理员。</li>
  </ul>
</div>
""" + KEY_JS


class Handler(BaseHTTPRequestHandler):
    server_version = "pool-portal/1.0"

    # ── 通用 ──
    def _cookie_uid(self):
        raw = self.headers.get("Cookie") or ""
        m = re.search(r"(?:^|;\s*)sid=([A-Za-z0-9_-]+)", raw)
        if not m:
            return None
        with db() as conn:
            row = conn.execute("SELECT uid, exp FROM sessions WHERE token=?", (m.group(1),)).fetchone()
        if not row or row["exp"] < time.time():
            return None
        with db() as conn:
            return conn.execute("SELECT * FROM users WHERE id=?", (row["uid"],)).fetchone()

    def _send(self, code, body, ctype="text/html; charset=utf-8", cookie=None, location=None,
              extra=None):
        data = body.encode() if isinstance(body, str) else body
        # 曾经把 "Location: /x" 当 ctype 传进来过：302 没头、浏览器白屏。
        # 以后谁再写成那种形式，这里直接纠正并记账，别让页面默默变白。
        if ctype and ctype.lower().startswith("location:"):
            log("BUG redirect header passed as ctype: %r" % ctype)
            location = ctype.split(":", 1)[1].strip()
            ctype = "text/plain; charset=utf-8"
        if 300 <= code < 400 and not location:
            log("BUG %d without Location: %s" % (code, self.path))
        self.send_response(code)
        if location:
            self.send_header("Location", location)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def _client_ip(self):
        return ((self.headers.get("X-Real-IP") or "").strip()
                or (self.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
                or self.client_address[0])

    def _public_base(self):
        """站点对外的地址，用来在页面上写示例；不写死域名。

        PUBLIC_BASE 环境变量优先（反代改了 Host 时用），否则拿请求的 Host。
        """
        env = (os.environ.get("PUBLIC_BASE") or "").strip().rstrip("/")
        if env:
            return env
        host = (self.headers.get("Host") or "").strip() or "127.0.0.1"
        return "http://" + host

    # ── GET ──
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"
        # nginx 的 location /join/ 带尾斜杠会把前缀剥掉，后端收到的是 /dashboard；
        # 两种写法都认，免得内页 404。
        if path.startswith("/join"):
            path = path[5:] or "/"
        user = self._cookie_uid()
        # 面板注入脚本：从磁盘读，改文件即刻生效，不用重启服务
        if path == "/panel-ext.js":
            try:
                with open(PANEL_JS, "rb") as f:
                    js = f.read()
            except OSError as exc:
                log("panel-ext read failed: %s" % exc)
                return self._send(404, "/* panel-ext.js missing */",
                                  "application/javascript; charset=utf-8")
            return self._send(200, js, "application/javascript; charset=utf-8",
                              extra={"Cache-Control": "no-store"})

        # 面板里那张「算力池」页的数据口：认面板自己的 X-Panel-Token
        if path == "/admin/api/overview":
            tok = self.headers.get("X-Panel-Token") or ""
            if not (panel_ok(tok) or is_admin(user)):
                return self._json({"ok": False, "error": "panel auth required"}, 401)
            try:
                data, cached = overview_cached()
            except Exception as exc:
                log("overview failed: %s" % exc)
                return self._json({"ok": False, "error": "上游没读出来：%s" % str(exc)[:120]}, 502)
            out = dict(data)
            out["cached"] = cached
            return self._json(out)

        if path == "/admin/api/refresh-status":
            tok = self.headers.get("X-Panel-Token") or ""
            if not (panel_ok(tok) or is_admin(user)):
                return self._json({"ok": False, "error": "panel auth required"}, 401)
            return self._json({"ok": True, "job": credits_job_state()})

        if path == "/admin/api/platforms":
            tok = self.headers.get("X-Panel-Token") or ""
            if not (panel_ok(tok) or is_admin(user)):
                return self._json({"ok": False, "error": "panel auth required"}, 401)
            items = []
            for e in load_upstreams():
                if e["enabled"]:
                    items.append(platform_detail(e))
                else:
                    items.append({"id": e["id"], "name": e["name"], "note": e["note"],
                                  "state": "off", "accounts": [],
                                  "usage": {"used": 0.0, "requests": 0}})
            return self._json({"ok": True, "platforms": items})

        if path in ("/", "/join", ""):
            if user:
                return self._send(302, "", "text/plain", location="/join/dashboard")
            return self._send(200, page("算力池", AUTH_PAGE))
        if path == "/dashboard":
            if not user:
                return self._send(302, "", "text/plain", location="/join/")
            return self._send(200, page("共用额度", dashboard_body(user), user, "dashboard"))
        if path == "/accounts":
            if not user:
                return self._send(302, "", "text/plain", location="/join/")
            return self._send(200, page("添加账号", accounts_body(user), user, "accounts"))
        if path == "/admin":
            if not is_admin(user):
                return self._send(302, "", "text/plain", location="/join/")
            return self._send(200, page("用户总览", admin_body(user), user, "admin"))
        if path == "/keys":
            if not user:
                return self._send(302, "", "text/plain", location="/join/")
            return self._send(200, page("API Key", keys_body(user, self._public_base()), user, "keys"))
        return self._json({"ok": False, "error": "not found"}, 404)

    # ── POST ──
    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        ip = self._client_ip()
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json({"ok": False, "error": "bad json"}, 400)

        if path == "/admin/api/credits-refresh":
            tok = self.headers.get("X-Panel-Token") or ""
            if not (panel_ok(tok) or is_admin(self._cookie_uid())):
                return self._json({"ok": False, "error": "panel auth required"}, 401)
            try:
                st = start_credits_refresh()
            except Exception as exc:
                log("credits refresh start failed: %s" % exc)
                return self._json({"ok": False, "error": "起不来：%s" % str(exc)[:120]}, 502)
            return self._json({"ok": True, "job": st})

        if path.startswith("/admin/api/platform/"):
            tok = self.headers.get("X-Panel-Token") or ""
            if not (panel_ok(tok) or is_admin(self._cookie_uid())):
                return self._json({"ok": False, "error": "panel auth required"}, 401)
            action = path[len("/admin/api/platform/"):]
            e = up_by_id(str(body.get("id") or ""))
            if not e:
                return self._json({"ok": False, "error": "没有这家平台"}, 404)
            if not e["enabled"]:
                return self._json({"ok": False, "error": "%s 还没接入" % e["name"]}, 400)
            try:
                if action == "checkin":
                    return self._json(platform_checkin(e, body.get("uid")))
                if action == "login-start":
                    return self._json(platform_login_start(e))
                if action == "login-poll":
                    return self._json(platform_login_poll(e, str(body.get("state") or "")))
                if action == "login-callback":
                    if not e.get("callback"):
                        return self._json({"ok": False,
                                           "error": "%s 不需要粘贴回调：打开授权链接登录同意即可" % e["name"]}, 400)
                    res = platform_login_callback(e, str(body.get("state") or ""),
                                                  str(body.get("callback_url") or "").strip())
                    return self._json({"ok": True, "upstream": res})
            except Exception as exc:
                log("platform %s %s failed: %s" % (e["id"], action, exc))
                return self._json({"ok": False, "error": str(exc)[:120]}, 502)
            return self._json({"ok": False, "error": "unknown action"}, 404)

        if path == "/api/register":
            log(f"register attempt email={body.get('email')!r} ip={ip}")
            nick = str(body.get("nickname") or "").strip()[:24]
            email = str(body.get("email") or "").strip().lower()[:120]
            pw = str(body.get("password") or "")
            if not nick:
                return self._json({"ok": False, "error": "昵称不能为空"}, 400)
            if not RE_EMAIL.match(email):
                return self._json({"ok": False, "error": "邮箱格式不对"}, 400)
            if len(pw) < 6:
                return self._json({"ok": False, "error": "密码至少 6 位"}, 400)
            if not rate_ok(ip):
                return self._json({"ok": False, "error": "操作太频繁，稍后再试"}, 429)
            salt, h = hash_pw(pw)
            try:
                with db() as conn:
                    cur = conn.execute(
                        "INSERT INTO users(nickname,email,salt,hash,created) VALUES(?,?,?,?,?)",
                        (nick, email, salt, h, time.time()))
                    uid = cur.lastrowid
            except sqlite3.IntegrityError:
                return self._json({"ok": False, "error": "这个邮箱已经注册过了"}, 400)
            token = secrets.token_urlsafe(32)
            with db() as conn:
                conn.execute("INSERT INTO sessions(token,uid,exp) VALUES(?,?,?)",
                             (token, uid, time.time() + 7 * 86400))
            log(f"register email={email} ip={ip}")
            return self._send(200, json.dumps({"ok": True}), "application/json; charset=utf-8",
                              cookie=f"sid={token}; Path=/; HttpOnly; Max-Age={7*86400}")

        if path == "/api/login":
            email = str(body.get("email") or "").strip().lower()
            pw = str(body.get("password") or "")
            if not rate_ok(ip):
                return self._json({"ok": False, "error": "操作太频繁，稍后再试"}, 429)
            with db() as conn:
                row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if not row:
                return self._json({"ok": False, "error": "邮箱或密码不对"}, 401)
            _, h = hash_pw(pw, row["salt"])
            if not secrets.compare_digest(h, row["hash"]):
                return self._json({"ok": False, "error": "邮箱或密码不对"}, 401)
            token = secrets.token_urlsafe(32)
            with db() as conn:
                conn.execute("INSERT INTO sessions(token,uid,exp) VALUES(?,?,?)",
                             (token, row["id"], time.time() + 7 * 86400))
            return self._send(200, json.dumps({"ok": True}), "application/json; charset=utf-8",
                              cookie=f"sid={token}; Path=/; HttpOnly; Max-Age={7*86400}")

        if path == "/api/logout":
            raw = self.headers.get("Cookie") or ""
            m = re.search(r"(?:^|;\s*)sid=([A-Za-z0-9_-]+)", raw)
            if m:
                with db() as conn:
                    conn.execute("DELETE FROM sessions WHERE token=?", (m.group(1),))
            return self._send(200, json.dumps({"ok": True}), "application/json; charset=utf-8",
                              cookie="sid=; Path=/; Max-Age=0")

        user = self._cookie_uid()
        if not user:
            return self._json({"ok": False, "error": "请先登录"}, 401)

        if path == "/api/key/show":
            with db() as conn:
                row = conn.execute("SELECT key, name FROM user_keys WHERE uid=?",
                                   (user["id"],)).fetchone()
            if not row:
                return self._json({"ok": False, "error": "你还没有 Key，先在上面生成一把"}, 404)
            log(f"key reveal uid={user['id']} ip={ip}")
            return self._json({"ok": True, "key": row["key"], "name": row["name"]})

        if path == "/api/account/start":
            if not rate_ok(ip):
                return self._json({"ok": False, "error": "操作太频繁，稍后再试"}, 429)
            pid = str(body.get("platform") or "workbuddy").strip()
            e = up_by_id(pid)
            if not e:
                return self._json({"ok": False, "error": "没有这家平台"}, 404)
            if not e["enabled"]:
                return self._json({"ok": False, "error": "%s 还没接入" % e["name"]}, 400)
            try:
                res = platform_login_start(e)
            except Exception as exc:
                log(f"start failed uid={user['id']} platform={pid} err={exc}")
                return self._json({"ok": False, "error": "上游拒绝了这次申请：%s" % str(exc)[:80]}, 502)
            if not res.get("ok"):
                return self._json({"ok": False, "error": res.get("error") or "授权链接没拿到"}, 502)
            with db() as conn:
                conn.execute("INSERT OR REPLACE INTO login_states(state,uid,at,platform) VALUES(?,?,?,?)",
                             (res["state"], user["id"], time.time(), pid))
            log(f"start ok uid={user['id']} platform={pid} ip={ip}")
            return self._json({"ok": True, "state": res["state"], "authUrl": res["authUrl"],
                               "platform": pid, "name": e["name"]})

        if path == "/api/account/poll":
            state = str(body.get("state") or "").strip()
            if not state:
                return self._json({"status": "unknown", "message": "缺少 state"}, 400)
            with db() as conn:
                row = conn.execute("SELECT platform FROM login_states WHERE state=?", (state,)).fetchone()
            pid = (row["platform"] if row and row["platform"] else "workbuddy")
            e = up_by_id(pid)
            if not e:
                return self._json({"status": "error", "message": "这家平台已下线"}, 400)
            try:
                res = platform_login_poll(e, state)
            except Exception as exc:
                return self._json({"status": "error", "message": str(exc)[:120]}, 502)
            if str(res.get("status")) == "ok":
                log(f"joined uid={user['id']} platform={pid}")
                attribute_account(state, pid)
            return self._json({"status": res.get("status"), "message": res.get("message", ""),
                               "platform": pid})

        if path == "/api/account/callback":
            state = str(body.get("state") or "").strip()
            cb = str(body.get("callback_url") or "").strip()
            if not state or not cb:
                return self._json({"ok": False, "error": "缺少 state 或回调地址"}, 400)
            with db() as conn:
                row = conn.execute("SELECT platform FROM login_states WHERE state=?", (state,)).fetchone()
            pid = (row["platform"] if row and row["platform"] else "workbuddy")
            e = up_by_id(pid)
            if not e:
                return self._json({"ok": False, "error": "这家平台已下线"}, 400)
            if not e.get("callback"):
                return self._json({"ok": False,
                                   "error": "%s 不需要粘贴回调：打开授权链接、在手机上登录同意就行，页面会自己刷新" % e["name"]}, 400)
            try:
                platform_login_callback(e, state, cb)
            except Exception as exc:
                log(f"callback failed uid={user['id']} platform={pid} err={exc}")
                return self._json({"ok": False, "error": str(exc)[:140]}, 502)
            return self._json({"ok": True, "platform": pid})

        if path == "/api/key/create":
            with db() as conn:
                has = conn.execute("SELECT 1 FROM user_keys WHERE uid=?", (user["id"],)).fetchone()
                contribs = conn.execute("SELECT count(*) FROM contrib WHERE uid=?", (user["id"],)).fetchone()[0]
            if has:
                return self._json({"ok": False, "error": "你已经有一个 Key 了"}, 400)
            if contribs == 0 and not is_admin(user):
                return self._json({"ok": False, "error": "先用「添加账号」贡献一个账号，才能领取 Key"}, 403)
            new_key = "wb-" + secrets.token_urlsafe(24)
            name = f"portal-{user['nickname']}-{user['id']}"
            try:
                settings = api("GET", "/settings")
                entries = []
                for e in settings.get("api_keys") or []:
                    # 不传 key，让网关沿用已存值
                    entries.append({"id": e["id"], "name": e.get("name", ""),
                                    "realm": e.get("realm", ""),
                                    "models": e.get("models") or [],
                                    "accounts": e.get("accounts") or [],
                                    "enabled": bool(e.get("enabled", True))})
                key_id = secrets.token_hex(6)
                entries.append({"id": key_id, "name": name, "key": new_key,
                                "realm": "", "models": [], "accounts": [], "enabled": True})
                api("POST", "/settings/save", {"api_keys": entries})
            except Exception as exc:
                log(f"key create failed uid={user['id']} err={exc}")
                return self._json({"ok": False, "error": "网关没接受这次创建，稍后再试"}, 502)
            with db() as conn:
                conn.execute("INSERT INTO user_keys(uid,key,name,created,key_id) VALUES(?,?,?,?,?)",
                             (user["id"], new_key, name, time.time(), key_id))
            log(f"key created uid={user['id']} name={name}")
            return self._json({"ok": True, "key": new_key})

        return self._json({"ok": False, "error": "not found"}, 404)

    def log_message(self, fmt, *args):
        return


class Portal(ThreadingHTTPServer):
    """默认 listen backlog 只有 5：几十个人同时打开会有连接被拒、再重试，
    表现就是「有时候卡一下」。这里放宽到 256，线程都设成 daemon。"""
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 256


if __name__ == "__main__":
    init_db()
    try:
        with db() as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(user_keys)")]
        if "key_id" not in cols:
            with db() as conn:
                conn.execute("ALTER TABLE user_keys ADD COLUMN key_id TEXT")
    except Exception as exc:
        log("migrate key_id failed: %s" % exc)
    log("portal started")
    Portal(LISTEN, Handler).serve_forever()
