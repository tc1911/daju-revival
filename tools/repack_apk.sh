#!/usr/bin/env bash
# 覆盖 -> 对齐 -> 签名 -> 校验。
# 用法: KS=<keystore> KS_PASS=<密码> [KS_ALIAS=daju] tools/repack_apk.sh <原apk> <overlay目录> <输出apk>
#
# 签名密钥和密码不随仓库分发；KS 未设置时默认 work/keystore/daju.jks。
# overlay 目录里的相对路径要和 APK 内一致，例如:
#   work/build/oppo/assets/src/project.jsc
#   work/build/oppo/assets/main.js
set -euo pipefail

APK="${1:?用法: KS=<keystore> KS_PASS=<密码> repack_apk.sh <原apk> <overlay目录> <输出apk>}"
OVERLAY="${2:?缺 overlay 目录}"
OUT="${3:?缺输出 apk}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

TMP="$ROOT/work/tmp"
KS="${KS:-$ROOT/work/keystore/daju.jks}"
ALIAS="${KS_ALIAS:-daju}"
PASS="${KS_PASS:?请先 export KS_PASS=<签名密钥密码>}"

mkdir -p "$TMP" "$(dirname "$OUT")"

if [ ! -f "$KS" ]; then
  echo "缺少签名密钥: $KS" >&2
  echo "请设置 KS 指向已有 keystore，或自行生成（密码用 KS_PASS 传入，不要写进仓库）：" >&2
  echo "  keytool -genkeypair -keystore \"$KS\" -alias \"$ALIAS\" -keyalg RSA -keysize 4096 -validity 10000 -dname \"CN=Daju Revival\"" >&2
  exit 1
fi

BASE="$(basename "$OUT" .apk)"
UNSIGNED="$TMP/$BASE.unsigned.apk"
ALIGNED="$TMP/$BASE.aligned.apk"

echo "== 覆盖文件 =="
python3 "$HERE/repack_zip.py" "$APK" "$OVERLAY" "$UNSIGNED"

echo "== 对齐 =="
zipalign -f -p 4 "$UNSIGNED" "$ALIGNED"

echo "== 签名 =="
apksigner sign --ks "$KS" --ks-key-alias "$ALIAS" \
  --ks-pass "pass:$PASS" --key-pass "pass:$PASS" \
  --v1-signing-enabled true --v2-signing-enabled true \
  --out "$OUT" "$ALIGNED"

echo "== 校验 =="
apksigner verify --verbose --print-certs "$OUT" | head -20
echo
echo "成品: $OUT ($(stat -c %s "$OUT") B)"
echo "（中间产物留在 $TMP，要清就手动清）"
