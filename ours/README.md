# ours — 我们自己的算力池层

这是 `workbuddy2api-hub` 的**外挂层**，不改上游一行代码：

```
ours/
├─ portal/portal.py          # 朋友自助小站（注册/共用额度/添加账号/API Key/用户总览）
├─ portal/panel-ext.js       # 注入到面板的「算力池」页（nginx sub_filter 注入）
├─ deploy/join-panel.service # systemd 单元
├─ deploy/nginx-ours.conf    # nginx 片段：/join/ 反代 + /wb/ 注入
├─ deploy/install.sh         # 幂等部署脚本（带备份，失败可回滚）
└─ docs/CHANGES-OURS.md      # 改了什么、为什么、怎么回滚
```

## 为什么不改上游

面板是第三方镜像（`workbuddy2api-hub`），watchtower 每天检查新版本。直接改镜像里的文件，
一次自动升级就白改，也说不清哪份代码在跑。所以我们的东西全部落在镜像外面：

- 页面：`portal.py` 挂在 nginx 的 `/join/`，独立进程、只监听 127.0.0.1
- 面板里的那一页：nginx 在 `/wb/` 的 HTML 末尾注入 `panel-ext.js`，扩展自己加导航项和页面
- 数据：只读上游的 `/accounts`、`/usage/analytics`，不碰账号池和 key 的写接口

## 安装

```bash
sudo bash ours/deploy/install.sh
```

脚本做四件事，每步都先备份：

1. 把 `portal/` 装到 `/opt/join-panel/`（已有文件先备份成 `*.bak-<时间>`）
2. 装 systemd 单元并启动 `join-panel.service`
3. 给 nginx 打两处补丁（`/join/` 反代、`/wb/` 注入脚本），`nginx -t` 通过才 reload
4. curl 自检：`/join/` 200、`/join/panel-ext.js` 200、`/join/admin/api/overview` 无令牌 401

## 回滚

```bash
sudo bash ours/deploy/install.sh --rollback
```

恢复 nginx 与 `/opt/join-panel/` 最近一次备份，停掉并禁用 `join-panel.service`。
只想去掉面板里那一页：删掉 `/wb/` 里那三行 `sub_filter`，其它不影响。
