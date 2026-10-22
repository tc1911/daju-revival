# 大橘为重（daju-revival）

《橘猫侦探社》（乐元素，`com.happyelements.xstorycncatdetective`）的离线复刻/修补工程。
目标：脱离已停运的官方服务器，在 **Android arm64** 与 **桌面** 上离线运行。

- `daju-revival` 来自公告原文「大橘为重」
- 底包：官方 6.12 + `compat/arm64-v8a/`（从 OPPO 6.12 提取的 7 个 arm64 库）
- 原包在 `源文件/`，勿提交

## 当前状态

- Android 主链已跑通，产物 `work/out/daju-all-release-300.apk`
- 构建由 `tools/pipeline.toml` 一张表驱动，`tools/build.py` 执行
- 离线启动可用，修复大部分功能，可能有部分我没测试到，请发issues（推荐）或评论区
- 修复大部分已知恶性bug

版本号

移植版与游戏 6.12 分开编号：

```bash
tools/version.py show       # 当前 6.12.300 release
tools/version.py dev        # 下一个开发版：6.12.301
tools/version.py release    # 下一个正式主版本 → 6.12.400
```

规则：`code = main * 100 + revision`，显示为 `<game>.<code>`；当前 `main=3`、`revision=0`（release），即 **6.12.300**。
最终 APK 命名：`daju-<arch>-<channel>-<code>.apk`，当前 `daju-all-release-300.apk`。
关于页会显示「版本 6.12.300」。Android manifest 仍是游戏原版 `6.12/12`。

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

## 公开范围

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
apksigner verify --print-certs work/out/daju-all-release-300.apk
adb install -r work/out/daju-all-release-300.apk
```

## 目录

```
源文件/                   原始 APK（勿提交）
compat/                   7 个 OPPO 6.12 arm64 兼容库 + 来源/校验和
tools/                    解包/加密/打包/patch + pipeline.toml + build.py
docs/                     修改列表、原版代码分析、代码文档、游戏代码文档
LICENSE / NOTICE.md       非商用许可证与授权范围
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

## 许可证

本仓库的原创代码、补丁、构建脚本与文档采用 **Daju Revival Non-Commercial License 1.0**：
允许个人学习、研究、离线保存和修改，**禁止任何商业用途**。

《橘猫侦探社》的游戏素材、原版游戏代码、APK 内的第三方内容以及 `compat/` 下的
native 库**不在**本许可证授权范围内，权利归乐元素或各自权利人所有。

详见 `LICENSE`（英文正文）、`LICENSE.zh-CN.md`（中文参考）和 `NOTICE.md`（范围说明）。
如需商业授权，请通过 https://github.com/tc1911 联系。

> 仅供个人研究与离线保存，本工程不分发游戏素材与原版代码。
