# 这个 fork 是我们自己在跑的版本

上游：**[niyouqianma/workbuddy2api-hub](https://github.com/niyouqianma/workbuddy2api-hub)**（MIT）。
本 fork 不改上游一行代码，所有我们自己的东西都在 `ours/` 里，作为**外挂层**部署：

- `ours/portal/` — 朋友自助小站（`/join/`）：注册、共用额度、加号、领 API Key、用户总览
- `ours/portal/panel-ext.js` — 注入主面板的「算力池」页（nginx `sub_filter` 注入，不动镜像）
- `ours/deploy/` — systemd 单元、nginx 片段、幂等安装脚本（带备份与回滚）
- `ours/docs/CHANGES-OURS.md` — 改了什么、为什么、性能数据、回滚办法

## 快速安装

```bash
git clone git@github.com:Tieria-coder/workbuddy2api-hub.git
cd workbuddy2api-hub
sudo bash ours/deploy/install.sh
```

跑完：`http://<host>/join/`（朋友用）、`http://<host>/wb/`（面板，左侧多一页「算力池」）。

## 分支

- `main` — 跟随上游
- `ours` — 我们自己的层（本 README 与 `ours/` 在这里）

## 同步上游

```bash
git remote add upstream https://github.com/niyouqianma/workbuddy2api-hub.git
git fetch upstream
git checkout main && git merge --ff-only upstream/main && git push origin main
git checkout ours && git merge main
```
