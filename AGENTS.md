# AGENTS.md

《橘猫侦探社》（乐元素）离线复刻/修补工程。目标：脱离已停运的官方服务器，让游戏在
Android arm64 与桌面跑起来。

- 包名：`com.happyelements.xstorycncatdetective`
- 底包路线：官方 6.12 + `compat/arm64-v8a/`（OPPO 6.12 的 7 个 arm64 库）；两包游戏内容逐字节相同，只差渠道外壳
- 没有通用构建系统、测试套件、CI、包管理器；构建由 `tools/pipeline.toml` + `tools/build.py` 驱动
- 原包在 `源文件/`，勿提交
- 许可证：`LICENSE`（Daju Revival Non-Commercial License 1.0，禁止商用）；游戏素材/原版代码/`compat/` 不在授权范围内
- 公开仓库不包含：完整 APK、解包 JS/资源、签名密钥、构建产物、中间产物；`compat/` 是唯一例外

## 术语陷阱

- `blackjack` 不是别的游戏：远程资源目录就叫 `blackjack-remote-asset`
- `daju-revival` = 公告原文「大橘为重」
- `.jsc` 不是 JS 字节码，是 **XXTEA(含长度字) → gzip → JS 源码**
- 6.12 官方与 OPPO 游戏内容一致；6.9 小米是旧版

## JS 工作流

```bash
# 1. 解包；解密 JS 落在 assets/src-js/（带 -js），不是 assets/src/
# 官方与 OPPO 游戏内容一致，把官方包解到历史路径 work/extracted/oppo 即可
export JSC_KEY='f309100a-33de-4c'
tools/unpack_apk.sh 源文件/橘猫侦探社_6.12_官方official.apk work/extracted/oppo

# 2. 改 work/extracted/oppo/assets/src-js/project.js

# 3. 回加密；overlay 内路径必须与 APK 内路径逐字一致
tools/jsc.py encrypt <project.js> work/build/.../assets/src/project.jsc
tools/jsc.py selftest work/extracted/oppo/assets/src/project.jsc

# 4. 打包：优先走构建表；手工 overlay 才直接调 repack_apk.sh
tools/build.py <stage>
tools/repack_apk.sh <原apk> <overlay目录> work/out/xxx.apk
```

易错点：

- overlay 相对路径 == APK 内路径；放错层级会静默变成「新增文件」
- `jsc.py` 从 `JSC_KEY` 或 `-k` 读 key；加密默认 gzip，不要关
- `repack_apk.sh` 会丢弃旧 v1 签名，重新签 v1/v2/v3；需要 `KS_PASS`，装机前看 `apksigner verify`
- 解包产物可复用；`repack_apk.sh` 第一个参数只是承载 overlay 的原包

## 构建链

`tools/pipeline.toml` 是唯一构建映射表；`tools/build.py` 只负责按表执行。
不要再新增 `build_official_arm64_*.sh`。

```bash
tools/build.py list                       # 列出 stage/patch/输出
tools/build.py                            # 默认 profile-native
tools/build.py nopay
tools/build.py back                       # 会先重跑 nopay
tools/build.py daily --no-deps             # 只用现有 back，不重跑上游
tools/build.py profile-native --force      # 整链重跑
tools/build.py daily --out work/out/x.apk  # 覆盖输出
```

流水线（表里顺序）：

```text
nopay（merge + offline + local + monetization + album）
  → back（JS 返回键 + native smali，重编 dex）
  → daily（每日签到 + 资源 JSON）
  → shop（3 个每日特价：2 礼物 + 1 功能，半价/限购3）
  → profile（资料/设置/图片 + main.js 清热更）
  → profile-native（ProfileBridge → classes3.dex）
```

| stage | 表里的步骤 | 产物 |
|---|---|---|
| `nopay` | `offline → local → monetization → album` | `official-arm64-local-nopay.apk` |
| `back` | `back_button` + `native = "back"` | `official-arm64-back.apk` |
| `daily` | `daily_currency` + `assets.daily_currency` | `official-arm64-daily.apk` |
| `shop` | `rmb_shop` | `official-arm64-shop.apk` |
| `profile` | `custom_profile → settings_cleanup → chat_image` + `main_js` | `official-arm64-profile.apk` |
| `profile-native` | `dex = "profile_bridge"` | `official-arm64-profile-native.apk` |

历史 stage 也在表里：`offline`、`local`、`profile-js`、`noshop`；不需要就别构建。

规则：

- 改补丁先改 `[patches.<id>]`，再把 id 加到对应 `stage.patches`；补丁顺序就是 JS 链顺序
- 改资源/原生步骤：`[assets.*]`、`[native.*]`、stage 的 `assets`/`main_js`/`native`/`dex` 字段
- `back.rebuild_base = true`：构建 back 时自动重跑 nopay；`profile-native.rebuild_base = true`：默认重跑 profile 的 JS 链再打 dex；`--force` 从 merge 起重跑整链
- `--no-deps`：只用现有 base APK/JS，不重跑上游
- `profile-native` 的 d8 默认用 `/usr/lib/jvm/zulu-11/bin/java` + `/opt/android-sdk/build-tools/37.0.0/lib/d8.jar`；找不到时退回 PATH 的 `d8`
- `work/tmp` 保留：`project.*.js`、`main_nohot.js`、`native_profile/android.jar`、
  `official_back_full/`、`apktool_framework/`；截图/日志/中间 APK 可删

## 环境变量

```bash
export JSC_KEY='f309100a-33de-4c'   # .jsc 解密/加密
export KS="$PWD/work/keystore/daju.jks"
export KS_PASS='<你的签名密码>'      # 不要提交
export KS_ALIAS=daju
```

## 签名 / 环境

- 签名密钥放在 `work/keystore/`（gitignore，**不要提交**）；密码只通过 `KS_PASS` 传入
- 换签名密钥会导致已装包无法覆盖升级
- `python3` 需 3.11+（`build.py` 用 `tomllib`）
- 默认 `java` 是 8；`d8` 需要 Java 11
- 实机：arm64-v8a Android 设备，adb 直连
- 反汇编 ARM `.so` 用 `llvm-objdump`，系统 `objdump` 不认 ARM

## 目录

```text
源文件/                 原始 APK（勿提交）
compat/                 7 个 OPPO 6.12 arm64 兼容库（来源/校验和见 compat/README.md）
tools/                  解包/加密/打包/patch + pipeline.toml + build.py
docs/                   修改列表、原版代码分析、代码文档、游戏代码文档
LICENSE / NOTICE.md     非商用许可证与授权范围
work/extracted/         解包现场（gitignore；oppo/assets/src-js = 解密后 JS）
work/build/             overlay（gitignore）
work/out/               成品 APK（gitignore）
work/tmp/               构建缓存 + 调试现场（gitignore）
work/keystore/          本地签名密钥（gitignore，不提交）
```

## 资源与热更（事实，不是 bug）

- 包内资源：`assets/res/raw-assets/*` + `assets/res/import/*.json`（明文 Cocos 资源定义）
- `assets/main.js` 是热更引导；远程目录 `writablePath + blackjack-remote-asset`
- CDN：`https://staticxplan.happyelements.cn/static/app_cn/remote_assets/6.12.0/`
- 包内 manifest 描述服务器端资源包，与 APK 文件本就对不上（6.12 约 69% 吻合）

## 当前状态

- Android arm64 主链已跑通，产物 `work/out/official-arm64-profile-native.apk`；
  构建由 `tools/pipeline.toml` 一张表驱动，`tools/build.py` 执行；
  大小/SHA256/签名/实机状态见 `docs/修改列表.md` 第 0 节
- 已完成：离线启动、本地账号与协议兜底、持久化根修复（含背包/货币/道具）、保留商城入口、
  每日签到（5000 银 + 500 金）、商城内购本地成交、3 个每日特价（半价/限购3）、成就本地领取、隐藏故事购买/完成持久化、商城隐藏娃娃机、个人信息页去账号/广告/充值、“我”页去客服、开局不送充电宝、默认资料恢复原版（调查员A/原版头像）、相册分帧、返回键层级、
  设置页精简（含关于页）、资料编辑、电量 HUD、聊天图片离线兜底
- 未完成：深度氪金/充电残留、`main.js` 彻底去热更、HeSDK/广告 SDK、桌面路线
- 已知近似：电池 HUD 是自绘覆盖；头像裁剪是自动居中，不是可拖动框

## 文档分工

| 文档 | 负责 |
|---|---|
| `docs/修改列表.md` | 当前产物、构建链、改了什么、已知问题、验证命令 |
| `docs/代码文档.md` | tools 逐文件实现、补丁锚点、引用矩阵 |
| `docs/游戏代码文档.md` | `project.js` 264 个游戏模块 + 331 个依赖模块的阅读索引 |
| `docs/原版代码分析.md` | 原版机制、资源事实、踩坑，不记录补丁实现 |

维护规则：修改记录只进修改列表；工具/补丁实现只进代码文档；游戏模块只进游戏代码文档；
原版机制只进原版分析。不再新增分散文档。
