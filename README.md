# 大橘为重（daju-revival）

《橘猫侦探社》（乐元素，`com.happyelements.xstorycncatdetective`）的离线复刻/修补工程。
目标：脱离已停运的官方服务器，在 **Android arm64** 与 **桌面** 上离线运行。

- `daju-revival` 来自公告原文「大橘为重」
- 底包：官方 6.12 + `compat/arm64-v8a/`（从 OPPO 6.12 提取的 7 个 arm64 库）
- 原包在 `源文件/`，勿提交

## 当前状态

- Android arm64 主链已跑通，产物 `work/out/official-arm64-profile-native.apk`
- 构建由 `tools/pipeline.toml` 一张表驱动，`tools/build.py` 执行
- 离线启动：跳过 `login_getClientConfig` 与热更检查，不再等 102 秒
- 本地 mock 账号 + 业务协议兜底，重启自动进主场景
- 持久化根修复：`UserDefault` 默认本地落盘；背包/货币/道具写入 `daju_bag_items`，重启保留
- 商城保留入口、只留游戏内货币商品；“今日行程”改为每日签到：每天 5000 银币 + 500 金币
- 开局不再送 5 个充电宝；道具 50000002 标为「充电宝（已废弃）」，下架且不可用
- 相册分帧、返回键层级、设置页精简、资料编辑、电量 HUD、聊天图片离线兜底

产物哈希、实机状态、验证命令见 `docs/修改列表.md`。

## 加密事实

`assets/src/*.jsc` **不是** JS 字节码，是 **XXTEA（含长度字）→ gzip → JS 源码**：

```
project.jsc       339,332 B  --XXTEA+gzip-->  project.js     1,726,534 B  游戏逻辑
settings.jsc       45,532 B  ------------->  settings.js      107,497 B  Creator 资源表
cocos2d-jsb.jsc   256,608 B  ------------->  cocos2d-jsb.js 1,089,784 B  引擎胶水层
```

## 环境变量

解密 key 不写死在代码里，用 `JSC_KEY` 传入（XXTEA 只用前 16 字节）：

```bash
export JSC_KEY='f309100a-33de-4c'
```

签名密钥和密码也不随仓库分发：

```bash
export KS="$PWD/work/keystore/daju.jks"   # 指向你自己的 keystore
export KS_PASS='<你的签名密码>'
export KS_ALIAS=daju
```

## 开源范围

本仓库**不包含**：完整游戏 APK、解包后的 JS/资源、签名密钥、构建产物、中间产物。
使用前需要自备官方 6.12 APK；签名 key 由使用者自己生成/保管。

例外：`compat/arm64-v8a/` 是 7 个从 OPPO 6.12 提取的 native 兼容库（约 18 MB），
用于“只提供官方 APK”时补 arm64；版权归原权利人，来源和风险见 `compat/README.md`。

## 快速开始

```bash
# 解包 + 解出 JS（已解过可复用；JSC_KEY 必须已 export）
# 官方包和 OPPO 包游戏内容一致；这里把官方包解到历史路径 work/extracted/oppo
tools/unpack_apk.sh 源文件/橘猫侦探社_6.12_官方official.apk work/extracted/oppo

# 构建：阶段/补丁顺序都在 tools/pipeline.toml，build.py 按表执行
tools/build.py list
tools/build.py                      # 默认 profile-native
tools/build.py back                 # 分阶段；会先重跑 nopay
tools/build.py profile-native --force   # 改上游后整链重跑

# 验证与装机
apksigner verify --print-certs work/out/official-arm64-profile-native.apk
adb install -r work/out/official-arm64-profile-native.apk
```

## 目录

```
源文件/                   原始 APK（勿提交）
compat/                   7 个 OPPO 6.12 arm64 兼容库 + 来源/校验和
tools/                    解包/加密/打包/patch + pipeline.toml + build.py
docs/                     修改列表、原版代码分析、代码文档、游戏代码文档
work/extracted/           解包现场（gitignore）
work/build/               overlay（gitignore）
work/out/                 成品 APK（gitignore）
work/tmp/                 构建缓存 + 调试现场（gitignore）
work/keystore/           本地签名密钥（gitignore，不提交）
```

## 文档

| 文档 | 内容 |
|---|---|
| `docs/修改列表.md` | 当前产物、构建链、改了什么、已知问题、验证 |
| `docs/代码文档.md` | tools 逐文件实现、补丁锚点、引用矩阵 |
| `docs/游戏代码文档.md` | 264 个游戏模块 + 331 个依赖模块 |
| `docs/原版代码分析.md` | 原版机制、资源事实、踩坑 |

## 下一步

- 深度清理氪金/充电残留（剧情购买按钮、累计充值展示、自动充电宝设置）
- `main.js` 彻底去热更引导
- HeSDK/渠道 SDK 登录支付、广告 SDK 与联网行为
- 桌面路线未定：web 壳复用度最高，Creator 2.x 无 Linux native 构建

> 仅供个人研究与离线保存，本工程不分发游戏素材与原版代码。
