# 我们对这个项目做了什么

上游 `workbuddy2api-hub` 一行没改。我们的东西全在镜像外面，做成 `ours/` 这一层。

## 1. 朋友自助小站 `/join/`

`portal/portal.py`：独立 Python 进程（`ThreadingHTTPServer`，只监听 `127.0.0.1:8790`），
被 nginx 挂在 `/join/`。四页 + 一个管理页：

| 页面 | 干什么 |
|---|---|
| `/` | 昵称 / 邮箱 / 密码注册登录（无验证码，按原话「都无所谓」） |
| `/dashboard` | 共用额度：今日已用、剩余、签到到账、还要多少能用；**快过期的积分**按 24 小时 / 3 天 / 7 天 / 30 天分档，列出最近到期的包 |
| `/accounts` | 加号：走官方 OAuth（`/accounts/login/start` + `poll`），密码不经过本站；带步骤说明和四条 FAQ |
| `/keys` | 领 Key：没贡献过账号不给领；一把 key 一人，页面写明 Base URL、Bearer 头、模型名、报错对照表 |
| `/admin` | 只有管理员邮箱能看：注册用户、今日活跃、已领 key、贡献账号数、今日全站消耗、每人用量 |

账号一律匿名显示成「谁谁提供的第几号账号」，不吐 workbuddy 那边的昵称。

## 2. 面板里多一页「算力池」

`portal/panel-ext.js` 由 nginx 在 `/wb/` 的 HTML 末尾注入，自己的事自己做：

- 侧栏、手机底部导航各加一项；点开是一个 `main-page`，与面板自己的页签互不串
- 鉴权直接复用面板的 `X-Panel-Token`（先查 sessionStorage，再查 localStorage），
  服务端拿它回问 `/panel/status` 的 `authenticated` 才放行，不另造密码
- 数据来自 `/join/admin/api/overview`（我们自己的接口，15 秒缓存）
- 「刷新余额」按钮：后台逐号去腾讯重取，页面显示 `刷新中 2/5`，不阻塞

## 3. 三个性能坑（都是实测出来的）

| 问题 | 数据 | 处理 |
|---|---|---|
| 页面等腾讯 | `/accounts/credits` 现拉 5 个号要 **10.35 秒**；`/accounts` 读内存快照只要 **7 毫秒**，同样 182KB | 展示一律读 `/accounts` |
| 翻用量日志 | `/usage/recent` 两页 1.2MB、每页 40ms，N 个人同时开就解析 N 遍，GIL 排队 | 换 `/usage/analytics`（7ms、200KB）+ 5 秒共享缓存 |
| 连接排队 | 默认 listen backlog 只有 5，几十个并发连接被拒后重试 | `request_queue_size=256` |

改完的效果（本机压测，同一台服务器）：

```
              改前            改后
 1 人        0.105s          0.105s
10 人同时    1.15s           0.080s
30 人同时    2.5s            0.18s   (p95 0.30s)
60 人同时    6.3s            0.36s   (p95 0.57s)
```

## 4. 一个真 bug

`/join/` 对已登录用户返回 302 时，把 `"Location: /join/dashboard"` 当成了 `Content-Type` 参数传，
响应里根本没有 Location 头 → 浏览器白屏。已修，并在 `_send()` 里加了自检：
3xx 没 Location、或 Location 被误传成别的头，都写一条 `BUG` 到日志。

## 5. 回滚

- nginx：`/etc/nginx/sites-available/default.bak-ours-*`，删掉 `/wb/` 里三行 `sub_filter` 即回到原样
- portal：`/opt/join-panel/portal.py.bak-*`
- 一条命令：`sudo bash ours/deploy/install.sh --rollback`

## 6. 多平台：几家网关的数字摆在一块

配置文件 `/opt/join-panel/upstreams.json` 是一个数组，每项一家网关（样例见
`ours/deploy/upstreams.example.json`）：

```json
{"id": "workbuddy", "name": "WorkBuddy", "base": "http://127.0.0.1:8788",
 "pass_file": "/opt/join-panel/panel-pass", "enabled": true, "note": "国际/国内双区"}
```

- `enabled: false` 的那家显示成灰的「未接入」，不阻塞其它家
- 读取失败只把那一行标成「读取失败」，合计行只算正常接通的
- 跨家族网关（qoder2api-hub / trae2api-hub 之类）认证头不一样时，用
  `auth_header` / `auth_prefix` / `login_path` / `login_field` 适配，
  默认是 `X-Panel-Token` + `/panel/login` + `password`

页面效果：`/join/dashboard` 多一张「多平台总览」，面板「算力池」页多一张「多平台」，
同一份数据（15 秒缓存），合计行只算已接入的。

实测（2026-11-25）：WorkBuddy 一家在线（5 个号、今日 203.4 积分、剩余 17,626），
Qoder 与 Trae 按未接入显示占位；面板页与朋友页都验过，18 项回归全过。


## 7. 一个面板管三家（2026-11-26 加）

面板「算力池」页多一张「平台管理」：tab 切 WorkBuddy / Qoder / Trae，每家一屏——

- 账号表：昵称、剩余积分、今日签到（连签天数）、状态（正常/冷却中/需重新授权/已停用）
- 「签到」单号｜「全部签到」批量
- 「添加账号」：门户代发 `POST /accounts/login/start`，把官方授权链接直接给出来，
  每 3 秒轮询 `login/poll`，成功自动刷新（不用再去各家的 127.0.0.1 看板）

后端只加了三类透传接口（都要面板令牌）：`/admin/api/platforms`、
`/admin/api/platform/checkin`、`/admin/api/platform/login-start|login-poll`。
不同家族的发号体不一样，做了适配：先试 `{"platform":"CLI","realm":"cn"}`，失败再试 `{}`；
链接字段兼容 `authUrl` / `authorization_url`；轮询先 GET 再 POST。

实测：三家 tab 切换正常，WorkBuddy 5 个号明细/签到/连签天数都对，Qoder 与 Trae 空态提示正确；
门户代发两家的授权链接都拿到了（qoder.com.cn 设备码、trae.cn authorization）。
## 8. 侧栏平台下拉（2026-11-28 加）

品牌区下面多了一个自绘下拉：**全部平台 / WorkBuddy / Qoder / Trae**，每项后面带「N 个号」或状态。
选一家 → 自动跳到「算力池」页并把平台管理切到那家；选「全部平台」→ 显示三家汇总表。
选择记在 localStorage（`wb-pool-platform`），下次打开还在。

避坑记录：一开始用的是原生 `<select>`，被面板自带的「自绘下拉」增强接管（它把原生控件
`opacity:0; pointer-events:none` 藏起来、用触发器接管），程序化改值会被它回弹，表现是
「选了没反应」。改成纯 div + 按钮的自绘菜单后正常，也不受面板 DOM 变动影响。
### 修正（2026-11-28 当天）

用户反馈「点开没有显示东西」。两个原因，都已修：

1. 菜单是 `position:absolute` 挂在侧栏里，侧栏有 `overflow`，窄窗口下会被裁掉 → 改成挂到
   `document.body` 的 `position:fixed` 菜单，按按钮的 `getBoundingClientRect()` 定位，滚动/缩放时自动收起。
2. 平台数据是异步拉的，菜单先开、数据后到的那一瞬是空盒子 → 打开时先渲染「正在读取平台…」
   并主动触发一次拉取；数据为空时显示「还没有可选的平台」，不再留白。

实测（1000×900 窄窗口、真实鼠标点击）：菜单展开在按钮下方 20,113、169×141，四项齐全，
`elementFromPoint` 确认没有被别的东西盖住；点 WorkBuddy 后菜单收起、表格出 5 个号。
### 修正 2（2026-11-28）：选某一家后，整页只显示那一家

用户反馈：下拉选 Qoder 后，页面顶部还是 18,000 多积分（那是 WorkBuddy 的池子）。原因是下拉当时只切了
「平台管理」的小表，页面主体（今日已用 / 剩余 / 快过期 / 今日各用户 / 账号明细）依旧是 WorkBuddy 的。

现在：
- 选 **WorkBuddy** 或 **全部平台** → 走原来的完整视图（WorkBuddy 池子 + 多平台卡）
- 选 **Qoder / Trae** → 整页切成「单平台视图」：今日消耗该家的、账号数/可用数/剩余积分合计/今日已签到，
  下面是该家的账号表（含单号签到、全部签到、添加账号），不再出现 WorkBuddy 的卡片
- 选择写进 localStorage，刷新后仍停在那一家；数据没到时先显示「正在从 X 网关取数…」

实测：选 Qoder 后整页显示 `0.00 积分 · 0 次请求 / 账号 0 个 / 剩余 0.0 / 今日已签到 0/0`，
并且 `多平台`「快过期的积分」两张 WorkBuddy 卡不再出现；切回 WorkBuddy 恢复 18,081.7。