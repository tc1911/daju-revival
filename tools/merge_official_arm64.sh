#!/usr/bin/env bash
# 用官方 6.12 包做底包，补上 arm64-v8a 游戏库。
#
# 优先使用仓库内 compat/arm64-v8a/（7 个库，见 compat/libs.txt），
# 这样只需要官方 APK；compat 不完整时才回退到 OPPO 6.12 APK。
#
# 回退规则：只合并「官方 armeabi-v7a 里已有」且「OPPO arm64-v8a 里也有」的 .so，
# 自动跳过 OPPO 渠道 SDK 独有库（libads-c / libnearmelog 等）。
# 官方独有的 libsgcore.so 在 arm64 没有对应版本，会给出警告（当前不影响启动）。
#
# 用法：tools/merge_official_arm64.sh [official.apk] [oppo.apk] [out.apk]
#       OPPO 参数在 compat 完整时可省略/填任意不存在路径。
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OFFICIAL=${1:-"$ROOT/源文件/橘猫侦探社_6.12_官方official.apk"}
OPPO=${2:-"$ROOT/源文件/橘猫侦探社_6.12_OPPO.apk"}
OUT=${3:-"$ROOT/work/out/official-arm64.apk"}
OVERLAY="$ROOT/work/build/official-arm64"
COMPAT_DIR="${COMPAT_DIR:-$ROOT/compat/arm64-v8a}"
COMPAT_LIST="${COMPAT_LIST:-$ROOT/compat/libs.txt}"

[[ -f "$OFFICIAL" ]] || { echo "缺少官方 APK: $OFFICIAL" >&2; exit 1; }

official_v7a=$(unzip -Z1 "$OFFICIAL" | grep -E '^lib/armeabi-v7a/[^/]+\.so$' | xargs -n1 basename | sort)

compat=0
merge=()
if [[ -f "$COMPAT_LIST" && -d "$COMPAT_DIR" ]]; then
    while IFS= read -r lib; do
        [[ -z "$lib" || "$lib" == \#* ]] && continue
        [[ -f "$COMPAT_DIR/$lib" ]] || {
            echo "缺少 compat 库: $COMPAT_DIR/$lib" >&2
            exit 1
        }
        merge+=("$lib")
    done < "$COMPAT_LIST"
    [[ ${#merge[@]} -gt 0 ]] && compat=1
fi

if [[ $compat -eq 0 ]]; then
    [[ -f "$OPPO" ]] || {
        echo "缺少 OPPO APK，且 compat 库不完整: $OPPO" >&2
        echo "请补齐 compat/arm64-v8a/ 或提供 OPPO 6.12 包。" >&2
        exit 1
    }
    oppo_arm64=$(unzip -Z1 "$OPPO" | grep -E '^lib/arm64-v8a/[^/]+\.so$' | xargs -n1 basename | sort)
    mapfile -t merge < <(comm -12 <(printf '%s\n' "$official_v7a") <(printf '%s\n' "$oppo_arm64"))
    [[ ${#merge[@]} -gt 0 ]] || { echo "官方 v7a 与 OPPO arm64 没有交集库" >&2; exit 1; }
fi

rm -rf "$OVERLAY"
mkdir -p "$OVERLAY/lib/arm64-v8a"

echo "== 合并 arm64-v8a 库 =="
if [[ $compat -eq 1 ]]; then
    echo "  来源: $COMPAT_DIR（无需 OPPO 包）"
    for lib in "${merge[@]}"; do
        cp "$COMPAT_DIR/$lib" "$OVERLAY/lib/arm64-v8a/$lib"
        printf '  %-24s %s\n' "$lib" "$(stat -c%s "$OVERLAY/lib/arm64-v8a/$lib")"
    done
else
    echo "  来源: $OPPO"
    for lib in "${merge[@]}"; do
        unzip -p "$OPPO" "lib/arm64-v8a/$lib" > "$OVERLAY/lib/arm64-v8a/$lib"
        printf '  %-24s %s\n' "$lib" "$(stat -c%s "$OVERLAY/lib/arm64-v8a/$lib")"
    done
fi

if [[ $compat -eq 1 ]]; then
    merged_list=$(printf '%s\n' "${merge[@]}" | sort)
else
    merged_list="$oppo_arm64"
fi
missing=$(comm -23 <(printf '%s\n' "$official_v7a") <(printf '%s\n' "$merged_list"))
if [[ -n "$missing" ]]; then
    echo "WARNING: 官方 v7a 有、arm64 侧没有的库（未合并）:" >&2
    printf '  %s\n' $missing >&2
fi

echo "== 重打包并签名 =="
"$ROOT/tools/repack_apk.sh" "$OFFICIAL" "$OVERLAY" "$OUT"
echo "完成: $OUT"
