> 这是上游仓库原始 README，为了给本 fork 的 README 让位，从仓库根移动到这里。文中的相对链接（如 `CONTRIBUTING.md`、`docs/…`）以**仓库根**为基准。

# WorkBuddy2API-Hub 鈥?鍥介檯鐗堛€佸浗鍐呯増澶氳处鍙风綉鍏充腑鏋?
> [!IMPORTANT]
> **瀹樻柟缇よ亰**锛歔https://t.me/wb2apihub](https://t.me/wb2apihub)
>
> **鍑瘉瀹夊叏**锛氭湰椤圭洰鏄湰鍦伴儴缃茬綉鍏筹紝杩愯鏃堕渶瑕佸湪鏈湴璇诲彇鐢ㄦ埛鑷瀵煎叆鐨勮处鍙峰嚟璇侊紝鎵嶈兘璋冪敤瀹樻柟鎺ュ彛锛涘嚟璇佷繚瀛樺湪鐢ㄦ埛鑷繁鐨?`accounts/` 鐩綍銆傞」鐩笉浼氭妸鍑瘉涓婁紶鍒版湰椤圭洰鐨勭涓夋柟鏈嶅姟鍣紝涔熸病鏈夐殣钘忕殑鍑瘉鏀堕泦鎴栦笂浼犻€昏緫銆傝绔嬪嵆鍏抽棴鍏綉鏆撮湶锛岃仈绯诲畼鏂瑰悐閿€鍏ㄩ儴 OAuth / 璁惧鎺堟潈锛岀‘璁ゆ棫 token 杩斿洖 `401` 鍚庡啀閲嶆柊鎺堟潈銆?
> [!WARNING]
> **WorkBuddy 涓婃父姝ｅ湪鏀剁揣瀵归潪瀹樻柟瀹㈡埛绔殑璇嗗埆涓庢嫤鎴€?*
>
> - **灏佺**锛?026-10-23 涓嬪崍璧凤紝闈炲畼鏂瑰鎴风鐨勮瘑鍒笌鎷︽埅鏄庢樉鏀剁揣銆?> - **缁存姢鑰?*锛氳繎鏈熷伐浣滃帇鍔涘澶э紝鏃犳硶淇濊瘉鍙婃椂鏇存柊涓庡搷搴斻€?> - **鍙敤鎬?*锛氫笂娓稿彲鑳介殢鏃惰繘涓€姝ユ敹绱э紝瀵艰嚧鏈」鐩笉鍙敤銆?> - **璐﹀彿椋庨櫓**锛氫娇鐢ㄩ潪瀹樻柟瀹㈡埛绔€犳垚鐨勯鎺с€侀檺娴佹垨灏佺锛岀敱浣跨敤鑰呰嚜琛屾壙鎷呫€?>
> **Upstream enforcement** tightened detection and blocking of unofficial clients from the afternoon of 2026-10-23. The maintainer is under increased workload and cannot guarantee timely updates or replies. The upstream may tighten further at any time; rate limits, account restrictions or bans caused by using an unofficial client are the user's responsibility.

鏈」鐩粎鐢ㄤ簬鍗忚瀛︿範銆佺爺绌朵笌涓汉鑷敤銆傝浼樺厛浣跨敤瀹樻柟瀹㈡埛绔紝涓嶈浣跨敤涓昏处鍙凤紝涓嶈鍏变韩璐﹀彿锛屼篃涓嶈鐢ㄤ簬鍟嗕笟杞敭銆?
This project is for protocol research and personal use only. Prefer the official client, do not use your primary account, and do not resell or share access.

<p align="center">
  <a href="https://github.com/niyouqianma/workbuddy2api-hub/releases"><img src="https://img.shields.io/badge/Release-v2.2.1-2496ED?style=flat-square" alt="Version 2.2.1"></a>
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/API-OpenAI_Compatible-412991?style=flat-square" alt="OpenAI API">
  <img src="https://img.shields.io/badge/Dual_Realm-Intl_&_CN-0DBD8B?style=flat-square" alt="Dual Realm">
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Maintenance-Resumed-0DBD8B?style=flat-square" alt="Maintenance resumed">
</p>

## 鏍稿績鐗规€?
- **鏍囧噯 API 鍏煎**锛氬皢 WorkBuddy锛堝浗闄呯増/鍥藉唴鐗堬級涓?CodeArts 灏佽涓烘爣鍑?OpenAI 鏍煎紡锛圕hat Completions / Responses锛夛紝鏃犵紳鏀寔 Codex銆丆laude Code銆丯extChat 绛夊悇绫诲鎴风銆?- **寮€绠卞嵆鐢ㄤ笌澶氱閮ㄧ讲**锛氫究鎼虹増鍏嶈鐜锛圵indows 鑷甫绮剧畝杩愯鏃讹級锛屾敮鎸?Docker銆丯AS锛堢兢鏅?椋炵墰锛変竴閿儴缃插強 OpenWrt 璺敱鍣ㄥ浐浠躲€?- **澶氳处鍙锋睜涓庡嚭鍙ｉ殧绂?*锛氭敮鎸佹祻瑙堝櫒 OAuth 蹇€熷鍏ャ€佹瘡璐﹀彿鐙珛鍑哄彛浠ｇ悊妲界粦瀹氥€佽澶囨寚绾归殧绂汇€佽嚜鍔ㄦ晠闅滆浆绉讳笌閰嶉杞浆銆?- **鑷姩鍖栫鍒╀笌绛惧埌**锛氬唴缃浗鍐呯増鎴愰暱浠诲姟銆佹槦宸村厠 / 璁拌€呰妭杩愯惀娲诲姩銆佸皬绋嬪簭浠诲姟銆佸姞娌圭珯绛惧埌涓庣尗鐚梾琛岋紝鏀寔鍥介檯鐗堟瘡鏃ユ椿璺冧細璇濅笌 CodeArts 鑷姩绛惧埌锛涙墜鏈?App 瀵硅瘽銆佸叕浼楀彿鍏虫敞涓庡叕鐩婃崘璧犵瓑蹇呴』鐪熷疄瀹屾垚鐨勪换鍔″彧鎻愮ず銆佷笉浼€犮€?- **鍙鍖栫鐞嗙湅鏉?*锛氭彁渚?Web 浠〃鐩橈紝鏀寔瀹炴椂璇锋眰鏃ュ織銆乀oken/绉垎閫忚銆佸 API Key 鏉冮檺鍒嗗彂锛堟ā鍨?璐﹀彿鐧藉悕鍗曪級涓庨搴︽姢鏍忋€?- **涓€閿伐浣滃彴鍚姩**锛歚start-workbuddy-all.bat` 鍏堢敤 `--probe-only` 妫€鏌ョ鍙ｄ笂鐨勫疄渚嬫槸鍚﹀仴搴凤紝鏈繍琛屾墠鎷夎捣缃戝叧骞舵墦寮€ WorkBuddy 宸ヤ綔鍙帮紝閬垮厤閲嶅鍚姩鎴栬杩為檶鐢熸湇鍔°€?
### 绀惧尯 Rust 鐗堟湰

[YTjungle666/workbuddy2api-hub](https://github.com/YTjungle666/workbuddy2api-hub) 鏄ぞ鍖虹嫭绔嬬淮鎶ょ殑 Rust 閲嶅啓鍒嗘敮銆傜綉鍏冲悗绔笌鍚姩鍣ㄥ潎浣跨敤 Rust 瀹炵幇锛屾彁渚涘崟鏂囦欢闈欐€佷簩杩涘埗锛屼笉渚濊禆 Python 杩愯鏃讹紱鍔熻兘浠ヤ笂娓?`v2.0.1` 涓哄榻愬熀绾裤€傚畠涓嶆槸鏈粨搴撶殑瀹樻柟鍙戝竷鐗╋紝闂鍙嶉涓庣増鏈洿鏂拌鍓嶅線瀵瑰簲浠撳簱銆?
> 鈿?**Vibe Coding 浜х墿**锛氭湰椤圭洰涓?100% Vibe Coding 鍗忓悓浜х墿鈥斺€斾汉绫诲紑鍙戣€呮彁鍑烘灦鏋勪笌涓氬姟鎰忓浘锛孉I 鍔╂墜绔埌绔畬鎴愰€嗗悜鍒嗘瀽銆侀摼璺皟搴︺€乄AF 鎸囩汗鑴辨晱涓庣晫闈㈢紪鍐欍€?
> 馃搶 **鎻愪氦浠ｇ爜璐＄尞鍓?*锛氳鍏堟煡鐪嬪苟**涓ユ牸閬靛惊**璐＄尞鎵嬪唽 [`CONTRIBUTING.md`](CONTRIBUTING.md)鈥斺€旀彁浜ゆ牸寮忋€佹祴璇曢棬绂佷笌绔埌绔啋鐑熻姹傞兘鍦ㄩ偅閲岋紙AI / 鏅鸿兘浣撹鐗瑰埆娉ㄦ剰鍏朵腑鐨勭‖鎬ц鍒欒妭锛夈€?
---

## 馃挅 璧炲姪鍟?
> 鎯冲嚭鐜板湪杩欓噷锛熻仈绯?[ardeyouxipianyi@gmail.com](mailto:ardeyouxipianyi@gmail.com)

<table>
<tr>
<td width="180" align="center" valign="middle">
  <a href="https://agentrouter.org/register?aff=unrV"><img src="https://raw.githubusercontent.com/88lin/picx-images-hosting/master/90C5FAD072EA247822CB88BB32512A41.webp" alt="Agent Router" width="150"></a>
</td>
<td valign="middle"><b><a href="https://agentrouter.org/register?aff=unrV">Agent Router</a></b>&nbsp;鏄厤璐瑰叕鐩婂ぇ妯″瀷 API 骞冲彴锛屾敮鎸?Claude-opus-5.5銆丟PT-6 Astra銆丟PT-6.1 Sol銆乨eepseek-v4-flash 绛変富娴佹ā鍨嬶紝鍥藉唴鐩磋繛銆傛敞鍐岄€?锛?75锛堟瘡鏃ョ鍒板緱 锛?5锛岃閭€寰?锛?0锛夛紝鏀寔 GitHub / LinuxDo 鐧诲綍銆?/td>
</tr>
</table>


---

## 涓€銆佸揩閫熷惎鍔?
### 1. 鏈満杩愯

- **Windows**锛氬弻鍑?`start-wb-proxy.bat`锛堥潤榛樺悗鍙拌繍琛?+ 鐙珛鏃ュ織绐楀彛锛夛紱濡傞渶鍓嶅彴鎺у埗鍙扮獥鍙ｏ紝鍙屽嚮 `start-wb-proxy-visible.bat`銆?- **macOS / Linux**锛氬弻鍑?`start-wb-proxy.command` 鎴栧湪缁堢鎵ц `./start-wb-proxy.sh [绔彛]`锛堥粯璁?8788锛岄渶瑕?Python 3.9+锛夈€?- **灞€鍩熺綉鍏变韩妯″紡**锛氳繍琛?`start-wb-proxy-lan.bat`锛圵indows锛夋垨 `./start-wb-proxy-lan.sh`锛坢acOS/Linux锛夛紝棣栨鍚姩灏嗚嚜鍔ㄧ敓鎴愰珮寮哄害 API Key 骞跺湪鎺у埗鍙版墦鍗般€?- 鍚姩鍚庤闂細
  - **Web 鐪嬫澘**锛歚http://127.0.0.1:8788/`锛堥粯璁よ闂瘑鐮?`admin`锛岄娆＄櫥褰曡鍦ㄨ缃腑淇敼锛?  - **API 鍦板潃**锛歚http://127.0.0.1:8788/v1`

### 2. Docker 閮ㄧ讲

棰勭紪璇戝鏋舵瀯闀滃儚鍙戝竷鍦?GHCR锛屾棤闇€鏈湴鏋勫缓锛?
**鏂瑰紡涓€锛氫竴閿剼鏈紙鎺ㄨ崘锛?*

```bash
# 瀹樻柟婧愶紙鐩磋繛 GitHub 鐜锛夛細
curl -fsSL https://raw.githubusercontent.com/niyouqianma/workbuddy2api-hub/main/quick-deploy.sh | bash

# 鍥藉唴缃戠粶 / NAS 鍔犻€燂細
curl -fsSL https://gh-proxy.com/https://raw.githubusercontent.com/niyouqianma/workbuddy2api-hub/main/quick-deploy.sh | sudo bash
```

> 鍏綉閮ㄧ讲鎴栭厤鍚堝弽鍚戜唬鐞嗭細鍦ㄧ閬撳墠鎸囧畾 `WB_DEPLOY_MODE=public bash`锛屽苟鎼厤 Nginx / Caddy / Cloudflare Tunnel 閰嶇疆 TLS銆?
**鏂瑰紡浜岋細鍗曟枃浠?Docker Compose**

```yaml
services:
  wb-proxy:
    image: ghcr.io/niyouqianma/workbuddy2api-hub:latest
    container_name: wb-proxy
    restart: unless-stopped
    ports:
      - "8788:8788"
    environment:
      - HOST=0.0.0.0
      - PORT=8788
      - TZ=Asia/Shanghai
    volumes:
      - ./accounts:/app/accounts    # 璐﹀彿鍑嵁涓庨厤缃紙鎸佷箙鍖栵級
      - ./usage:/app/usage          # 鐢ㄩ噺娴佹按鏃ュ織锛堟寔涔呭寲锛?```

鏇存柊闀滃儚锛歚docker compose pull && docker compose up -d`銆?
Docker 闀滃儚鍦ㄦ瀯寤洪樁娈靛凡缁忕紪璇戝ソ褰撳墠鏋舵瀯鐨?Go/uTLS 妗ワ紝瀹瑰櫒鍐呬笉闇€瑕?Go銆?鏈缃?`WB_TLS_FINGERPRINT` 鏃堕粯璁?`auto`锛涘闇€褰诲簳鍏抽棴妗ワ紝鍙姞
`- WB_TLS_FINGERPRINT=python`锛屽嵎涓殑璐﹀彿銆佽缃拰鐢ㄩ噺涓嶄細鍥犳鏀瑰彉銆?
### 3. 鍚姩鍏ュ彛锛氫紭鍏堢敤 `-m`

鍚屼竴浠戒唬鐮併€佸悓涓€涓处鍙锋睜锛宍python3 wb_proxy.py` 涓?`python3 -m wb_proxy` 鐨勫父椹诲唴瀛樺樊 **47-54 MB**
锛圵indows 11 / aarch64銆丳ython 3.12-3.14 鍥涘鐜瀹炴祴涓€鑷达紝瑙?#702锛夈€傛垚鍥犱粛鍦ㄦ帓鏌ワ紝
浣嗗彧瑕佹崲鎴?`-m` 灏辫兘鎷垮埌杩欐鏀剁泭鈥斺€?12 MB 鐨勮澶囦笂绾?10%銆?
```bash
cd /path/to/workbuddy2api-hub        # 蹇呴』鍏堣繘鍏?wb_proxy.py 鎵€鍦ㄧ洰褰?python3 -m wb_proxy --port 8788
```

`-m` 鎶?*褰撳墠鐩綍**鏀捐繘 `sys.path`锛岃€岃剼鏈柟寮忔斁鐨勬槸鑴氭湰鎵€鍦ㄧ洰褰曪紝鎵€浠ュ姟蹇呭厛 `cd`銆?浠撳簱鍐呯殑璧勬簮璺緞閮藉熀浜?`__file__` 瑙ｆ瀽锛屼笉鍙楀奖鍝嶃€侱ocker 闀滃儚鍜?OpenWrt 鍖呭凡鏀圭敤 `-m`锛?Windows / macOS 鐨?`start-wb-proxy.*` 鍚姩鑴氭湰鏆傛湭鏀瑰姩銆?
### 4. TLS 鍑虹珯妗ワ紙榛樿 `auto`锛?
浠庢湰鐗堟湰璧凤紝鏈樉寮忛厤缃?TLS 妯″紡鐨勫畨瑁呴粯璁や娇鐢?`WB_TLS_FINGERPRINT=auto`锛?缃戝叧浼氬厛灏濊瘯闅忓寘 Go/uTLS 妗ワ紱妗ヤ簩杩涘埗缂哄け銆佹灦鏋勪笉鏀寔銆佸惎鍔ㄥけ璐ャ€佹ˉ杩涚▼杩愯涓?閫€鍑猴紝鎴栧綋鍓嶈姹備娇鐢ㄨ嚜瀹氫箟 CA / 涓嶅吋瀹逛唬鐞嗘椂锛岃嚜鍔ㄥ洖閫€ Python/OpenSSL銆?鍥為€€鍙彂鐢熷湪褰撳墠杩涚▼鍐咃紝涓嶄細鍙嶅鎷夎捣澶辫触鐨勬ˉ锛屼篃涓嶄細鏀瑰彉鍘熸潵鐨勪唬鐞嗗嚭鍙ｅ拰璇佷功
鏍￠獙銆備究鎹风増銆丏ocker 鍜?OpenWrt 鐨勫彈鏀寔鏋舵瀯鍖呴兘鑷甫瀵瑰簲妗ワ紝鐢ㄦ埛涓嶉渶瑕佸畨瑁?Go銆?
闇€瑕佸己鍒舵寚瀹氭椂锛?
```sh
WB_TLS_FINGERPRINT=python   # 寮哄埗 Python/OpenSSL
WB_TLS_FINGERPRINT=node     # 寮哄埗妗ワ紱妗ヤ笉鍙敤鏃舵姤鏄庣‘閿欒
```

`node` 妯″紡涓嬩笉瑕佽缃?`WB_TLS_BRIDGE=off`锛屽惁鍒欎細鎸夋樉寮忓叧闂ˉ澶勭悊鑰岃蛋 Python銆?OpenWrt 浣跨敤 `uci set workbuddy2api.main.tls_mode='auto'`銆乣'node'` 鎴?`'python'`銆?瀹為檯妯″紡銆佹渶杩戣矾绾垮拰鍥為€€鍘熷洜鍙湪 `/health`銆乣/settings` 鍙婇潰鏉跨綉缁滆缃腑鏌ョ湅銆?闄嶇骇鍒颁笉璇嗗埆 `auto` 鐨勬棫鐗堟湰鍓嶏紝璇蜂复鏃惰缃?`WB_TLS_FINGERPRINT=python`銆?閫愯矾寰勫ご椤哄簭銆佷唬鐞?妗ュご闅旂鍜屾湭淇敼椤硅
[`docs/OUTBOUND-HEADER-AUDIT.md`](docs/OUTBOUND-HEADER-AUDIT.md)銆?
### 5. CodeArts 鍘熺敓绗笁鍑哄彛

缃戝叧鍐呯疆杩涚▼鍐呯洿杩炲崕涓轰簯 CodeArts锛屾敮鎸佽亰澶?SSE 鍗忚杞崲涓庤嚜鍔ㄧ鍒帮紝鏃犻渶鍗曠嫭杩愯绗笁鏂规ˉ鎺ユ湇鍔★細
1. 鎵撳紑鐪嬫澘 鈫掋€岃缃?鈫?CodeArts 鎺ュ叆銆嶏紝鍕鹃€夈€屽惎鐢?CodeArts 鍑哄彛銆嶅苟淇濆瓨锛?2. 鍒囨崲鑷崇湅鏉块《閮ㄣ€孋odeArts銆嶈鍥撅紝鐐瑰嚮銆? 娣诲姞璐﹀彿 (OAuth)銆嶅畬鎴愬崕涓轰簯鎺堟潈锛?3. 鍦ㄣ€岃缃?鈫?API Key銆嶄腑鏂板缓 Key 骞剁粦瀹氬嚭鍙ｄ负 `CodeArts`锛堟垨鍏ㄥ眬閫氱敤锛夊嵆鍙皟鐢ㄣ€?
CodeArts 鐨勬ā鍨?ID 鎸変笂娓哥洰褰?*绮剧‘鍖归厤**锛歚deepseek-v4.1-flash` 涓?`deepseek-v4.1-flash-1017` 鏄袱涓嫭绔嬫ā鍨嬶紝涓嶄細浜掔浉鍒悕鎴栭潤榛樺洖閫€銆?`/v1/models?realm=codearts` 杩斿洖鐨勬槸璐﹀彿褰撳墠鍙敤鐨勭湡瀹炵洰褰?ID锛涜皟鐢ㄦ椂璇风洿鎺ヤ娇鐢?杩斿洖鐨勫畬鏁?ID銆?
---

## 浜屻€佽处鍙锋帴鍏ヤ笌 API Key 鏉冮檺

### 1. 璐﹀彿娣诲姞涓庝唬鐞嗗嚭鍙ｇ粦瀹?- 鎵撳紑鐪嬫澘 `http://127.0.0.1:8788/`锛岀偣鍑汇€? 娣诲姞璐﹀彿 (OAuth)銆嶏紝鍦ㄦ祻瑙堝櫒涓畬鎴愬畼鏂圭櫥褰曟巿鏉冨嵆鍙嚜鍔ㄥ叆搴撱€?- **鐙珛浠ｇ悊鍑哄彛妲斤紙Proxy Slot锛?*锛氬湪鐪嬫澘涓彲鎸夐渶閰嶇疆骞跺懡鍚?HTTP/SOCKS5 鍑哄彛浠ｇ悊锛堟敮鎸佽处鍙峰瘑鐮佽璇侊級锛屾敮鎸佸皢璐﹀彿涓庣壒瀹氫唬鐞嗘Ы浣嶇粦瀹氾紝璐﹀彿韬唤璇锋眰涓庡嚭绔欒皟鐢ㄥ潎鑷姩璧拌浠ｇ悊銆?
### 2. 澶?API Key 鏉冮檺绠＄悊
- 銆岃缃€嶉〉鏀寔鍒涘缓澶氫釜鐙珛 API Key锛?  - **鍑哄彛缁戝畾**锛氬彲鍥哄畾璧板浗闄呯増銆佸浗鍐呯増鎴?CodeArts锛?  - **妯″瀷闄愬埗**锛氭敮鎸侀€氶厤绗︾櫧鍚嶅崟锛堝 `deepseek*`, `gpt-6-astra`锛夛紝杩濊璇锋眰鏈満鐩存帴杩斿洖 400锛?  - **璐﹀彿鐧藉悕鍗?*锛氬彲绮剧‘闄愬畾璇?Key 浠呭厑璁歌皟搴︾殑璐﹀彿鑼冨洿锛?  - **鐢ㄩ噺閫忚**锛氭暟鎹湅鏉挎寜 Key 鐙珛缁熻璋冪敤娆℃暟銆乀oken 娑堣€椼€佺紦瀛樺懡涓笌绉垎銆?
---

## 涓夈€佸鎴风鎺ュ叆閰嶇疆

- **Base URL**锛歚http://127.0.0.1:8788/v1`锛堝眬鍩熺綉涓?`http://<灞€鍩熺綉IP>:8788/v1`锛?- **API Key**锛氱湅鏉裤€岃缃€嶄腑娣诲姞骞剁粦瀹氱殑 Key
- **妯″瀷鍚嶇О**锛氳皟鐢?`/v1/models` 涓垪鍑虹殑浠绘剰瀹樻柟瀵归綈妯″瀷 ID锛堝 `deepseek-v4.1-flash`, `gpt-6-astra`, `hy3`锛?
**Codex CLI / Responses API**

```bash
export OPENAI_BASE_URL="http://127.0.0.1:8788/v1"
export OPENAI_API_KEY="浣犲湪鐪嬫澘璁剧疆涓坊鍔犲苟缁戝畾鐨凙PI_Key"
```

**Claude Code / Anthropic Messages锛堝疄楠屾€э級**

缃戝叧鏀寔瀹為獙鎬?Messages 鍗忚閫傞厤锛屽洜闀夸細璇濈紦瀛樺懡涓巼宸紓锛岄粯璁ゅ叧闂細
```bash
# 缃戝叧绔缃?WB_ENABLE_ANTHROPIC_MESSAGES=1 寮€鍚悗鐢熸晥锛?export ANTHROPIC_BASE_URL="http://127.0.0.1:8788"
export ANTHROPIC_API_KEY="浣犲湪鐪嬫澘璁剧疆涓坊鍔犲苟缁戝畾鐨凙PI_Key"
```

---

## 鍥涖€佸父鐢ㄧ幆澧冨彉閲?
| 鐜鍙橀噺 | 榛樿鍊?| 璇存槑 |
|---|---|---|
| `PORT` | `8788` | 缃戝叧鐩戝惉绔彛 |
| `API_KEY` | 鑷姩鐢熸垚 | 鍒濆 API Key锛堢湅鏉块厤缃 Key 鍚庝紭鍏堢敱鐪嬫澘绠＄悊锛?|
| `WB_DEPLOY_MODE` | `lan` | 閮ㄧ讲妯″紡锛歚lan`锛?.0.0.0锛夈€乣local`锛?27.0.0.1锛夈€乣public` |
| `WB_MAX_PAYLOAD_BYTES` | `16777216` | 鍗曡姹備綋涓婇檺锛堝瓧鑺傦紝榛樿 16MB锛屾敮鎸?1鈥?56 MB锛?|
| `WB_USAGE_ROTATE_BYTES` | `8388608` | 鐢ㄩ噺鏃ュ織鐨勮疆杞槇鍊硷紙瀛楄妭锛岄粯璁?8 MiB锛夈€俙0` 鍋滄鏂拌疆杞€傚浠藉拰闄嶇骇瑙?[鐢ㄩ噺鐩綍璇存槑](usage/README.txt) |
| `WB_CHAT_SLOT_WAIT` | `30` | 骞跺彂妲戒綅鐨勭瓑寰呯鏁帮細鍏ㄥ眬瀵硅瘽妲戒綅涓?Key 绾?`concurrency_limit` 鍏辩敤杩欎釜棰勭畻锛岀瓑鍒版墠鏈夊悕棰濓紝瓒呮椂浠嶆寜 429 鎷掔粷 |
| `WB_ENABLE_ANTHROPIC_MESSAGES` | `0` | 鏄惁寮€鍚疄楠屾€?Anthropic Messages 鍗忚杞崲 |
| `WB_BACKGROUND_MODEL_TARGET` | 鐣欑┖ | 鍚庡彴妯″瀷鍒悕鏀瑰啓鐩爣锛堝 DSH 瀹㈡埛绔嚜鍔ㄦ槧灏勶級 |
| `WB_CA_BUNDLE` | 鐣欑┖ | 鑷鏍硅瘉涔﹁矾寰勶紙渚涙姄鍖呰皟璇曟垨涓棿浠ｇ悊浣跨敤锛?|
| `WB_CN_CHAT_UPSTREAM` | 瀹樻柟榛樿 | 鍥藉唴鐗堝嚭绔欎唬鐞嗗湴鍧€ |
| `WB_IDENTITY_OS` | 瀹夸富绯荤粺 | 浠?CLI 韬唤锛氳鐩?`x-stainless-os`锛堝 `Linux` / `Windows`锛?|
| `WB_IDENTITY_ARCH` | 瀹夸富鏋舵瀯 | 浠?CLI 韬唤锛氳鐩?`x-stainless-arch`锛堝 `x64` / `arm64`锛?|
| `WB_IDENTITY_NODE_VERSION` | 瀹樻柟榛樿 | 浠?CLI 韬唤锛氳鐩?`x-stainless-runtime-version` |
| `WB_SANITIZE_LOOSE_BILLING` | `0` | 璁¤垂澶寸殑瀹芥澗鍏滃簳锛氫弗鏍艰В鏋愯涓嶅嚭鏃讹紝鎸夈€屽儚璁¤垂澶淬€嶏紙鍚?鈮? 涓?`cc_*=` / `cch=` 閿€笺€佷笖涓嶈秴杩?400 瀛楃锛夋暣娈靛垹闄ゃ€傞粯璁ゅ叧闂紝淇濇寔 #853 涔嬪悗鐨勪弗鏍艰涔夛紱瀹㈡埛绔敼瀛楁鍚嶅鑷存瘡杞墠缂€鍛戒腑鐜囧綊闆舵椂鎵嶉渶瑕佹墦寮€ |
| `WB_MSGSTAT_SHARDS` | `0` | 鍗曞彂 `/v1/messages` 璇锋眰鏀舵暃鍒板嚑涓处鍙蜂笂锛? = 鍏抽棴锛夈€傛墦寮€鍚庡悓涓€ *(key, 妯″瀷, system, tools)* 缁勫悎鐨勪竴娆℃€ц皟鐢ㄥ浐瀹氬鐢?鈮 涓处鍙凤紝閬垮厤琚鏉?user 鏂囨湰鎵撴暎鍒版暣姹狅紱涓婃父 prompt 缂撳瓨鎸夎处鍙峰瓨鏀撅紝鎹㈠彿鍗虫暣娈甸噸浠?|
| `WB_MSGSTAT_DAILY_SALT` | `1` | 涓婁竴鏉＄殑浜插拰閿甫褰撳ぉ鏃ユ湡鐩愶紝姣忓ぉ鍚勬《閲嶆柊寮€涓€娆★紱`0` 鍏抽棴锛堥敭璺ㄥぉ涓嶅彉锛?|

閬囧埌涓婃父 `400 / 11-128` 鏃讹紝鍏堟寜 [`docs/TROUBLESHOOTING-11-128.md`](docs/TROUBLESHOOTING-11-128.md) 鏀堕泦鍚屼竴璇锋眰鐨?韬唤銆佹渶灏忚姹傚拰鎻愮ず璇嶅鐓х粨鏋滐紱涓嶈鍏堣疆鎹㈣处鍙枫€?
---

## 浜斻€佷富瑕?API 绔偣

| 鎺ュ彛 | 鏂规硶 | 绔偣 | 璇存槑 |
|---|---|---|---|
| 鑱婂ぉ琛ュ叏 | `POST` | `/v1/chat/completions` | 鏍囧噯 OpenAI 鑱婂ぉ鎺ュ彛锛堟敮鎸佹祦寮?SSE 涓庢€濈淮閾惧洖濉級 |
| 浜や簰寮忓搷搴?| `POST` | `/v1/responses` | OpenAI Responses 鍗忚鎺ュ彛锛圕odex 涓撶敤锛?|
| 璇煶鍚堟垚 | `POST` | `/v1/audio/speech` | OpenAI 鍏煎 TTS锛圵AV / PCM锛岄渶鍦ㄥ獟浣撻〉寮€鍚級 |
| 璇煶杞啓 | `POST` | `/v1/audio/transcriptions` | OpenAI 鍏煎 ASR锛坢ultipart锛岄渶鍦ㄥ獟浣撻〉寮€鍚級 |
| 妯″瀷鐩綍 | `GET` | `/v1/models` | 鑾峰彇褰撳墠鍑哄彛瀵归綈鐨勫畼鏂瑰彲鐢ㄦā鍨嬪垪琛?|
| 鐢熷浘 | `POST` | `/v1/images/generations` | 鏂囩敓鍥?/ 鍥剧敓鍥撅紙濮嬬粓鍙敤锛屾寜濯掍綋鍙锋睜鑷姩閫夊嚭鍙ｏ級 |
| 鐢熻棰?| `POST` | `/v1/videos` | 寮傛鐢熻棰戜换鍔℃彁浜わ紙鏈湴骞跺彂鎺掗槦涓庣┖闂茶皟搴︼級 |
| 瑙嗛鐘舵€?| `GET` | `/v1/videos/<id>` | 杞瑙嗛鐢熸垚杩涘害涓庣粨鏋?|
| 浜х墿涓嬭浇 | `GET` | `/v1/videos/<id>/content` | 涓嬭浇瑙嗛 MP4 浜х墿鐩撮摼 |
| 鍋ュ悍妫€鏌?| `GET` | `/health` | 缃戝叧杩愯鐘舵€併€佸彲鐢ㄨ处鍙锋暟涓庡氨缁ā鍨嬪垎甯?|
| 鍒涘缓璐﹀彿鎺堟潈璇锋眰 | `POST` | `/v1/accounts/authorize` | 鎸?`realm=cn` 鎴?`intl` 鐢熸垚涓€娆℃€ф祻瑙堝櫒鎺堟潈閾炬帴 |
| 鏌ヨ鎺堟潈鐘舵€?| `GET` | `/v1/accounts/authorize/<request_id>` | 鏌ヨ娴忚鍣ㄧ櫥褰曠粨鏋滐紱鎴愬姛鍚庤处鍙疯嚜鍔ㄥ啓鍏ヨ处鍙峰垪琛?|
| 璇诲彇璐﹀彿鍒楄〃 | `GET` | `/v1/accounts?realm=cn\|intl` | 杩斿洖鎸囧畾鐗堟湰鐨勮劚鏁忚处鍙峰垪琛?|

---

## 鍏€佹祴璇曢獙璇?
```bash
python tests/run_all.py            # 鍏ㄩ儴濂椾欢
python tests/run_all.py realm      # 鍙窇鍚嶅瓧閲屽惈 realm 鐨?```

- 312 涓浠讹細234 涓?Python + 78 涓?JS锛汮S 闇€瑕?PATH 涓婃湁 `node`锛岀己澶辨椂浼氳烦杩囧苟鎻愮ず銆?- `tests/_mobile_check.py` 鏄嫭绔嬬殑 Playwright 鎵嬫満/妗岄潰甯冨眬妫€鏌ュ櫒锛堥渶鑷瀹夎 Playwright锛夛紝鎸夐渶鎵嬪姩杩愯锛屼笉鍦ㄤ笂闈㈢殑濂椾欢闆嗛噷銆?- `tests/_visual_recent.py` 鏄悓涓€绫绘墜鍔ㄦ鏌ュ櫒锛氱敤鍚堟垚 fixture 璧蜂竴浠?1480 瀹界殑銆岃姹傚垪琛ㄣ€嶏紝楠岃瘉澶辫触寰界珷鐐瑰紑鐨勮鎯呭脊绐椼€佸洓涓繃婊や笅鎷夌湡鐨勬妸鍙傛暟鍙戝埌 `/usage/recent`锛屽苟鎶婂垪琛?/ 寮圭獥 / 绛涢€夋潯鎴浘鍐欏埌绯荤粺涓存椂鐩綍鐨?`wb-visual-recent/`銆?- CI锛坄.github/workflows/tests.yml`锛夎窇鍚屼竴鏉″懡浠わ細Ubuntu 涓?python 3.9 涓?3.12锛?.9 鏄湰椤圭洰澹扮О鐨勬渶浣庣増鏈級锛學indows 涓?python 3.12锛涙帹閫?`v*` tag 鏃堕澶栨柇瑷€ **tag == 婧愮爜鐗堟湰**锛坄-ci` 婕旂粌 tag 璞佸厤锛夈€?
---

## 涓冦€佺増鏈洿鏂拌褰?(Changelog)

瀹屾暣鏇存柊璁板綍璇锋煡闃?**[docs/CHANGELOG.md](docs/CHANGELOG.md)**銆?
---

## 鍏€佽嚧璋笌寮曠敤澹版槑 (Credits & References)

鍦ㄥ崗璁€嗗悜銆侀鎺ц閬裤€佷换鍔￠摼璺笌宸ョ▼鍖栬璁¤繃绋嬩腑锛屾湰椤圭洰鍙傝€冦€佸惛绾冲苟鑷磋阿浠ヤ笅浼樼寮€婧愰」鐩笌鎶€鏈垚鏋滐紙鎺掑悕涓嶅垎鍏堝悗锛夛細

### 鏍稿績閫嗗悜涓庡崗璁弬鑰?- **[Sliverkiss/workbuddy2api](https://github.com/Sliverkiss/workbuddy2api)**锛氭垚闀夸换鍔￠€嗗悜銆佽澶囨寚绾规淳鐢燂紙`derive_id`锛夈€佽皟搴﹀櫒锛坄Scheduler`锛変笌 `reasoning_content` 鍥炲～璁捐锛?- **[L0NE-6/WorkBuddy-Daily](https://github.com/L0NE-6/WorkBuddy-Daily)**锛氬浗鍐呯増寰俊灏忕▼搴忎笓灞炰簨浠舵寚绾逛笌鍔ㄦ€佷笓瀹舵繁閾句换鍔℃ā鍨嬶紱
- **[88lin/workbuddy-auto-signin](https://github.com/88lin/workbuddy-auto-signin)**锛氱尗鐚棩甯告梾琛屼笌鎴愰暱鑳介噺寮€鐩茬洅锛圔uddy 鐩茬洅锛夊畨鍏ㄧ敓鍛藉懆鏈燂紱
- **[linguo2625469/workbuddy2api-panel](https://github.com/linguo2625469/workbuddy2api-panel)**锛氬浗鍐呯増杩炵櫥绠″闂幆閫昏緫涓庤交閲忓璇濇椿璺冧笂鎶ヤ簨浠讹紱
- **[misakano7545/workbuddy2api-panel](https://github.com/misakano7545/workbuddy2api-panel)**锛欸o/uTLS Node/OpenSSL ClientHello 鎸囩汗鍙傛暟涓庢ˉ鎺ュ疄鐜板弬鑰冿紙18 Cipher銆?0 Extension銆佹棤 ALPN锛夛紱
- **[Zhengyuuuui/workbuddy2api](https://github.com/Zhengyuuuui/workbuddy2api)**锛氬浗闄呯増 11140 璐﹀彿灏佺璇嗗埆銆佸喎鍗磋閬夸笌鏁呴殰鎺掓煡娓呭崟锛?- **[yuanyuanyuan430/workbuddy2api-hub](https://github.com/yuanyuanyuan430/workbuddy2api-hub)**锛氬浗闄呯増 EdgeOne CDN 璇佷功閿欓厤鎺掓煡涓庢椿璺冧笂鎶ヤ紭闆呴檷绾ф柟妗堬紱
- **[CangShui/workbuddy-cliproxy-fix](https://github.com/CangShui/workbuddy-cliproxy-fix)** & **[lovingfish/workbuddy-cliproxy](https://github.com/lovingfish/workbuddy-cliproxy)**锛氭棭鏈熷鎴风浠ｇ悊淇涓庣綉鍏抽€氫俊鍘熷瀷锛?- **[mmqz/cpa-multi-plugins](https://github.com/mmqz/cpa-multi-plugins)**锛氬鎻掍欢绠＄悊涓庡嚭绔欒皟搴︾粨鏋勫弬鑰冿紱
- **[ardeyouxipianyi/workbuddy2api](https://github.com/ardeyouxipianyi/workbuddy2api)**锛氬浗鍐呯増鏃╂湡鍒嗗彂鍖呴€嗗悜鍒嗘瀽涓庡嚭绔?User-Agent 瑙勮寖锛?
### 宸ョ▼鍖栦笌鐢熸€佸熀纭€
- **[aodianjun/workbuddy2api-hub](https://github.com/aodianjun/workbuddy2api-hub)**锛歄penWrt 璺敱鍣ㄦ墦鍖呴厤鏂癸紙`.ipk` / `.apk`锛変笌绯荤粺鏈嶅姟鏀寔锛?- **[YTjungle666/workbuddy2api-hub](https://github.com/YTjungle666/workbuddy2api-hub)**锛氱ぞ鍖虹淮鎶ょ殑 Rust 鍚庣涓庡惎鍔ㄥ櫒閲嶅啓鍒嗘敮锛屾彁渚涙棤 Python 杩愯鏃朵緷璧栫殑鍗曟枃浠堕潤鎬佷簩杩涘埗锛?- **[astral-sh/python-build-standalone](https://github.com/astral-sh/python-build-standalone)**锛歐indows 渚挎惡鐗堝厤瀹夎绮剧畝鐙珛 Python 杩愯鏃舵瀯寤哄熀鐭筹紱
- **[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)**锛欴SH 瀹㈡埛绔崗璁笌鎻愮ず璇嶆寚绾规竻娲楄閬垮弬鑰冦€?
鎰熻阿鎵€鏈夊悜鏈」鐩彁浜?PR銆佸弽棣?Issue 涓庡垎浜疄娴嬫牱鏈殑绀惧尯璐＄尞鑰咃紒

---

## 涔濄€佸厤璐ｅ０鏄?(Disclaimer)

鏈」鐩粎鐢ㄤ簬鍗忚瀛︿範涓庝釜浜哄紑鍙戞祴璇曪紝涓嶆彁渚涗换浣曞晢涓氭湇鍔℃垨鍙敤鎬ф媴淇濄€傚洜浣跨敤闈炲畼鏂瑰鎴风浜х敓鐨勮处鍙烽鎺с€侀檺鍒舵垨灏佺鐢变娇鐢ㄨ€呰嚜琛屾壙鎷咃紝璇蜂紭鍏堜娇鐢ㄥ畼鏂瑰鎴风銆?
## 猸?Star 瓒嬪娍

<p align="center">
  <a href="https://star-history.com/#niyouqianma/workbuddy2api-hub&Date">
    <img src="https://api.star-history.com/svg?repos=niyouqianma/workbuddy2api-hub&type=Date" alt="Star History Chart" width="760">
  </a>
</p>
