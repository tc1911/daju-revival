# OPPO 6.12 arm64 兼容库

这里的 7 个 `.so` 来自 OPPO 6.12 APK 的 `lib/arm64-v8a/`，用来给官方 6.12 底包补上 arm64 支持。
OPPO 原包已失传，本目录的库由项目维护者从旧手机 adb 提取；原始 APK 不随仓库分发。

## 文件

| 文件 | 大小 |
|---|---:|
| `lib39285EFA.so` | 154,192 B |
| `libbreakpad-hei.so` | 276,712 B |
| `libbuffer_pg.so` | 14,104 B |
| `libcocos2djs.so` | 17,260,808 B |
| `libfile_lock_pg.so` | 10,008 B |
| `libnms.so` | 183,368 B |
| `libtobEmbedEncrypt.so` | 10,416 B |

校验和见 `SHA256SUMS`，合并清单见 `libs.txt`。

## 用法

`tools/merge_official_arm64.sh` 会优先使用本目录：

```bash
export KS_PASS='<你的签名密码>'
tools/build.py nopay
```

这样只需要官方 6.12 APK，不再要求 OPPO APK。若本目录或 `libs.txt` 不完整，脚本会回退到 OPPO APK。

## 来源与版权

- 这些是 **原版游戏的 native 库**，不是本项目的原创代码。
- 版权归原权利人；本目录仅用于离线保存/互操作研究。
- 公开分发这些二进制可能收到 DMCA 或违反当地法律；作者不对使用后果负责。
- 不包含 OPPO 渠道 SDK 独有库（`libads-c`、`libnearmelog` 等），也不包含 `libsgcore.so` 的 arm64 版本。
