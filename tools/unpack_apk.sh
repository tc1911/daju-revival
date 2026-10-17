#!/usr/bin/env bash
# 解包 APK，并把它 assets/src 里的 .jsc 全部解成 js。
# 用法: JSC_KEY=<key> tools/unpack_apk.sh <apk> <输出目录>
set -euo pipefail

APK="${1:?用法: JSC_KEY=<key> unpack_apk.sh <apk> <outdir>}"
OUT="${2:?缺输出目录}"
KEY="${JSC_KEY:?请先 export JSC_KEY=<解密 key>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$OUT"
unzip -o -q "$APK" -d "$OUT"
echo "解包完成: $OUT"

if [ -d "$OUT/assets/src" ]; then
  python3 "$HERE/jsc.py" -k "$KEY" decrypt-all "$OUT/assets/src" "$OUT/assets/src-js"
else
  echo "警告: $OUT/assets/src 不存在，跳过 jsc 解密" >&2
fi
