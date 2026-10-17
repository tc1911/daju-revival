#!/usr/bin/env bash
# 用官方 6.12 包做底包，把 OPPO 6.12 包里的 arm64-v8a 游戏库合并进去。
#
# 规则：只合并「官方 armeabi-v7a 里已有」且「OPPO arm64-v8a 里也有」的 .so，
# 自动跳过 OPPO 渠道 SDK 独有库（libads-c / libnearmelog 等）。
# 官方独有的 libsgcore.so 在 OPPO arm64 中没有对应版本，会给出警告（当前不影响启动）。
#
# 用法：tools/merge_official_arm64.sh [official.apk] [oppo.apk] [out.apk]
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OFFICIAL=${1:-"$ROOT/源文件/橘猫侦探社_6.12_官方official.apk"}
OPPO=${2:-"$ROOT/源文件/橘猫侦探社_6.12_OPPO.apk"}
OUT=${3:-"$ROOT/work/out/official-arm64.apk"}
OVERLAY="$ROOT/work/build/official-arm64"

for f in "$OFFICIAL" "$OPPO"; do
    [[ -f "$f" ]] || { echo "缺少 APK: $f" >&2; exit 1; }
done

rm -rf "$OVERLAY"
mkdir -p "$OVERLAY/lib/arm64-v8a"

official_v7a=$(unzip -Z1 "$OFFICIAL" | grep -E '^lib/armeabi-v7a/[^/]+\.so$' | xargs -n1 basename | sort)
oppo_arm64=$(unzip -Z1 "$OPPO" | grep -E '^lib/arm64-v8a/[^/]+\.so$' | xargs -n1 basename | sort)
merge=$(comm -12 <(printf '%s\n' "$official_v7a") <(printf '%s\n' "$oppo_arm64"))

echo "== 合并 arm64-v8a 库 =="
for lib in $merge; do
    unzip -p "$OPPO" "lib/arm64-v8a/$lib" > "$OVERLAY/lib/arm64-v8a/$lib"
    printf '  %-24s %s\n' "$lib" "$(stat -c%s "$OVERLAY/lib/arm64-v8a/$lib")"
done

missing=$(comm -23 <(printf '%s\n' "$official_v7a") <(printf '%s\n' "$oppo_arm64"))
if [[ -n "$missing" ]]; then
    echo "WARNING: 官方 v7a 有、OPPO arm64 没有的库（未合并）:" >&2
    printf '  %s\n' $missing >&2
fi

echo "== 重打包并签名 =="
"$ROOT/tools/repack_apk.sh" "$OFFICIAL" "$OVERLAY" "$OUT"
echo "完成: $OUT"
