#!/usr/bin/env python3
"""把 overlay 目录里的文件覆盖进原 APK，其余条目原样搬运。

- 保持每个条目的压缩方式、时间戳、权限位
- 丢掉旧的 v1 签名文件（META-INF/*.SF|RSA|DSA|MF|EC），签名交给 apksigner
- overlay 里的相对路径 == APK 内的路径，例如 assets/src/project.jsc

用法: repack_zip.py <原apk> <overlay目录> <输出apk>
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

SIGN_SUFFIXES = (".SF", ".RSA", ".DSA", ".MF", ".EC")


def is_old_signature(name: str) -> bool:
    return name.upper().startswith("META-INF/") and name.upper().endswith(SIGN_SUFFIXES)


def repack(apk: Path, overlay: Path, out: Path) -> tuple[int, int]:
    files = {
        p.relative_to(overlay).as_posix(): p
        for p in overlay.rglob("*")
        if p.is_file()
    }
    replaced: set[str] = set()
    copied = 0

    with zipfile.ZipFile(apk) as zin, zipfile.ZipFile(out, "w") as zout:
        for info in zin.infolist():
            name = info.filename
            if is_old_signature(name):
                continue
            src = files.get(name)
            if src is not None:
                data = src.read_bytes()
                replaced.add(name)
            else:
                data = zin.read(name)
            new = zipfile.ZipInfo(name, date_time=info.date_time)
            new.compress_type = info.compress_type
            new.external_attr = info.external_attr
            new.internal_attr = info.internal_attr
            new.create_system = info.create_system
            new.flag_bits = info.flag_bits & ~0x08  # 去掉 data descriptor
            zout.writestr(new, data)
            copied += 1
        for name, path in sorted(files.items()):
            if name in replaced:
                continue
            zout.writestr(zipfile.ZipInfo(name), path.read_bytes())
            replaced.add(name)

    return copied, len(replaced)


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2
    apk, overlay, out = (Path(a) for a in argv[1:])
    copied, replaced = repack(apk, overlay, out)
    print(f"条目 {copied} 条（覆盖/新增 {replaced} 条）-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
