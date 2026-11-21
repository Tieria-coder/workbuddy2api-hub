#!/usr/bin/env bash
# ours 部署脚本：装 /opt/join-panel、装 systemd、给 nginx 打两处补丁、自检。
# 每一步都先备份；--rollback 回到最近一次备份。
#
#   sudo bash ours/deploy/install.sh
#   sudo bash ours/deploy/install.sh --rollback
set -euo pipefail

DEST=/opt/join-panel
UNIT=/etc/systemd/system/join-panel.service
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SRC=$(cd "$HERE/.." && pwd)
TS=$(date +%Y%m%d-%H%M%S)

say() { printf '\033[1m== %s\033[0m\n' "$*"; }
die() { printf '\033[31m!! %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" = "0" ] || die "用 root 跑：sudo bash $0"
command -v python3 >/dev/null || die "缺 python3"
command -v nginx >/dev/null || die "缺 nginx"

NGINX_CONF=$(nginx -T 2>/dev/null | head -20 | grep -o '/[^ ]*nginx.conf' | head -1)
for cand in /etc/nginx/sites-available/default /etc/nginx/conf.d/default.conf "$NGINX_CONF"; do
  [ -f "$cand" ] && grep -q 'location /wb/' "$cand" && NGINX_CONF="$cand" && break
done
[ -n "${NGINX_CONF:-}" ] && [ -f "$NGINX_CONF" ] || die "找不到含 location /wb/ 的 nginx 配置"

# ── 回滚 ─────────────────────────────────────────────────────────
if [ "${1:-}" = "--rollback" ]; then
  say "回滚"
  if [ -d "$DEST" ]; then
    LATEST=$(ls -1dt "$DEST".bak-* 2>/dev/null | head -1 || true)
    if [ -n "$LATEST" ]; then
      mv "$DEST" "$DEST.broken-$TS" && cp -a "$LATEST" "$DEST"
      echo "  恢复 $DEST <- $LATEST"
    fi
  fi
  LATEST_NG=$(ls -1dt "$NGINX_CONF".bak-ours-* 2>/dev/null | head -1 || true)
  if [ -n "$LATEST_NG" ]; then
    cp -a "$LATEST_NG" "$NGINX_CONF"
    echo "  恢复 $NGINX_CONF <- $LATEST_NG"
  fi
  systemctl disable --now join-panel 2>/dev/null || true
  nginx -t && systemctl reload nginx
  say "回滚完成（join-panel 已停止并禁用）"
  exit 0
fi

# ── 1. 装进程目录 ────────────────────────────────────────────────
say "安装 $DEST"
if [ -d "$DEST" ]; then cp -a "$DEST" "$DEST.bak-$TS"; echo "  备份 -> $DEST.bak-$TS"; fi
mkdir -p "$DEST"
install -m 0644 "$SRC/portal/portal.py" "$DEST/portal.py"
install -m 0644 "$SRC/portal/panel-ext.js" "$DEST/panel-ext.js"
if [ ! -f "$DEST/panel-pass" ]; then
  python3 -c 'import secrets;print(secrets.token_urlsafe(12))' > "$DEST/panel-pass"
  chmod 600 "$DEST/panel-pass"
  echo "  已生成面板密码文件 $DEST/panel-pass（内容就是主面板密码，portal 用它读账号余额）"
fi

# ── 2. systemd ──────────────────────────────────────────────────
say "安装 systemd 单元"
install -m 0644 "$HERE/join-panel.service" "$UNIT"
systemctl daemon-reload
systemctl enable --now join-panel
sleep 2
systemctl is-active --quiet join-panel || die "join-panel 起不来，看 journalctl -u join-panel -n 50"

# ── 3. nginx 补丁 ───────────────────────────────────────────────
say "给 nginx 打补丁：$NGINX_CONF"
cp -a "$NGINX_CONF" "$NGINX_CONF.bak-ours-$TS"
python3 - "$NGINX_CONF" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
changed = False

# 3.1 /wb/ 里注入 panel-ext.js
if 'panel-ext.js' not in s:
    m = re.search(r'^([ \t]*)location /wb/ \{\n', s, re.M)
    if not m:
        sys.exit('nginx 里没有 location /wb/，先确认面板反代在哪')
    ind = m.group(1) + '\t'
    ins = (ind + "sub_filter '</body>' '<script src=\"/join/panel-ext.js\" defer></script></body>';\n"
           + ind + 'sub_filter_once on;\n'
           + ind + 'proxy_set_header Accept-Encoding "";\n')
    s = s[:m.end()] + ins + s[m.end():]
    changed = True

# 3.2 /join/ 反代
if 'location /join/' not in s:
    anchor = re.search(r'^([ \t]*)location / \{\n', s, re.M)
    if not anchor:
        sys.exit('找不到 location / 作为插入点')
    ind = anchor.group(1) + '\t'
    block = (ind + 'location /join/ {\n'
             + ind + '\tproxy_pass http://127.0.0.1:8790/;\n'
             + ind + '\tproxy_http_version 1.1;\n'
             + ind + '\tproxy_set_header Host $host;\n'
             + ind + '\tproxy_set_header X-Real-IP $remote_addr;\n'
             + ind + '\tproxy_read_timeout 120s;\n'
             + ind + '}\n\n')
    s = s[:anchor.start()] + block + s[anchor.start():]
    changed = True

if changed:
    open(p, 'w', encoding='utf-8').write(s)
    print('  patched')
else:
    print('  already patched, nothing to do')
PY

nginx -t || die "nginx 配置校验失败，已备份：$NGINX_CONF.bak-ours-$TS（恢复：cp 回去再 nginx -t）"
systemctl reload nginx

# ── 4. 自检 ─────────────────────────────────────────────────────
say "自检"
check() { # url expect [extra curl args...]
  local url=$1 want=$2; shift 2
  local code
  code=$(curl -s -o /dev/null -w '%{http_code}' "$@" "http://127.0.0.1$url" || echo 000)
  printf '  %-34s %s (want %s)%s\n' "$url" "$code" "$want" "$([ "$code" = "$want" ] && echo '' || echo '  <-- 不对')"
}
check /join/ 200
check /join/panel-ext.js 200
check /join/admin/api/overview 401
check /wb/ 200
if curl -s "http://127.0.0.1/wb/" | grep -q 'panel-ext.js'; then
  echo "  面板 HTML 已注入 panel-ext.js"
else
  echo "  !! 面板 HTML 没看到注入，检查 location /wb/ 的 sub_filter 与 Accept-Encoding"
fi
say "完成：http://<这台机器>/join/  与  http://<这台机器>/wb/（左侧多一个「算力池」）"
