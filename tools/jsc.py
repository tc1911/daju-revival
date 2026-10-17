#!/usr/bin/env python3
"""《橘猫侦探社》assets/src/*.jsc 解密 / 加密工具。

格式：XXTEA（含长度字）+ gzip
  - 数据按小端打包成 n = ceil(len/4) 个 uint32，最后一个字是原始字节长度
  - key 由 -k/--key 或 JSC_KEY 环境变量提供，算法只用前 16 字节
  - 解密结果若以 1f 8b 开头还要 gunzip
"""
from __future__ import annotations

import argparse
import gzip
import os
import struct
import sys
from pathlib import Path

DELTA = 0x9E3779B9
MASK = 0xFFFFFFFF
DEFAULT_KEY = os.environ.get("JSC_KEY", "")


def _key_words(key: str) -> list[int]:
    if not key:
        sys.exit("缺少解密 key：用 -k/--key 传入，或 export JSC_KEY=...")
    raw = (key.encode() + b"\x00" * 16)[:16]
    return list(struct.unpack("<4I", raw))


def _mx(sum_: int, y: int, z: int, p: int, e: int, k: list[int]) -> int:
    return (
        ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4)) ^ ((sum_ ^ y) + (k[(p & 3) ^ e] ^ z))
    ) & MASK


def xxtea_decrypt(data: bytes, key: str = DEFAULT_KEY) -> bytes:
    k = _key_words(key)
    n = (len(data) + 3) // 4
    if n < 2:
        raise ValueError("密文太短")
    v = list(struct.unpack("<%dI" % n, (data + b"\x00" * (n * 4 - len(data)))[: n * 4]))
    sum_ = ((6 + 52 // n) * DELTA) & MASK
    y = v[0]
    while sum_:
        e = (sum_ >> 2) & 3
        for p in range(n - 1, 0, -1):
            z = v[p - 1]
            y = v[p] = (v[p] - _mx(sum_, y, z, p, e, k)) & MASK
        z = v[n - 1]
        y = v[0] = (v[0] - _mx(sum_, y, z, 0, e, k)) & MASK
        sum_ = (sum_ - DELTA) & MASK
    length = v[n - 1]
    if not n * 4 - 7 <= length <= n * 4 - 4:
        raise ValueError("长度字校验失败，密钥不对？")
    return struct.pack("<%dI" % n, *v)[:length]


def xxtea_encrypt(data: bytes, key: str = DEFAULT_KEY) -> bytes:
    k = _key_words(key)
    length = len(data)
    n = (length + 3) // 4
    v = list(struct.unpack("<%dI" % n, (data + b"\x00" * (n * 4 - length))[: n * 4]))
    v.append(length)
    n += 1
    rounds = 6 + 52 // n
    sum_ = 0
    z = v[n - 1]
    while rounds:
        sum_ = (sum_ + DELTA) & MASK
        e = (sum_ >> 2) & 3
        for p in range(n - 1):
            y = v[p + 1]
            z = v[p] = (v[p] + _mx(sum_, y, z, p, e, k)) & MASK
        y = v[0]
        z = v[n - 1] = (v[n - 1] + _mx(sum_, y, z, n - 1, e, k)) & MASK
        rounds -= 1
    return struct.pack("<%dI" % n, *v)


def decrypt_file(src: Path, key: str = DEFAULT_KEY) -> bytes:
    raw = src.read_bytes()
    plain = xxtea_decrypt(raw, key)
    return gzip.decompress(plain) if plain[:2] == b"\x1f\x8b" else plain


def encrypt_file(src: Path, key: str = DEFAULT_KEY, compress: bool = True) -> bytes:
    data = src.read_bytes()
    if compress:
        data = gzip.compress(data, mtime=0)
    return xxtea_encrypt(data, key)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="橘猫侦探社 jsc 加解密")
    ap.add_argument("-k", "--key", default=DEFAULT_KEY, help="XXTEA key；也可用 JSC_KEY 环境变量")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("decrypt", help="jsc -> js")
    p.add_argument("src", type=Path)
    p.add_argument("dst", type=Path)

    p = sub.add_parser("encrypt", help="js -> jsc")
    p.add_argument("src", type=Path)
    p.add_argument("dst", type=Path)
    p.add_argument("--no-gzip", action="store_true")

    p = sub.add_parser("decrypt-all", help="目录（含子目录）里所有 jsc -> dst/js")
    p.add_argument("src", type=Path)
    p.add_argument("dst", type=Path)

    p = sub.add_parser("selftest", help="验证 解密->加密 能否逐字节还原")
    p.add_argument("src", type=Path)

    args = ap.parse_args(argv)

    if args.cmd == "decrypt":
        args.dst.write_bytes(decrypt_file(args.src, args.key))
        print(f"{args.src} -> {args.dst} ({args.dst.stat().st_size} B)")
    elif args.cmd == "encrypt":
        args.dst.write_bytes(encrypt_file(args.src, args.key, not args.no_gzip))
        print(f"{args.src} -> {args.dst} ({args.dst.stat().st_size} B)")
    elif args.cmd == "decrypt-all":
        args.dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(args.src.rglob("*.jsc")):
            rel = f.relative_to(args.src).with_suffix(".js")
            out = args.dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(decrypt_file(f, args.key))
            print(f"{f.relative_to(args.src)} -> {rel} ({out.stat().st_size} B)")
    elif args.cmd == "selftest":
        raw = args.src.read_bytes()
        plain = xxtea_decrypt(raw, args.key)
        again = xxtea_encrypt(plain, args.key)
        ok = again == raw
        print(f"{args.src.name}: 解密 {len(raw)} -> {len(plain)} B, 重新加密一致 = {ok}")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
