#!/usr/bin/env python3
"""daju-revival 项目版本号。

与游戏主版本 6.12 并行，独立用于移植版构建/发布：
  code = main * 100 + revision

示例：
  main=2 revision=0 -> 200
  main=2 revision=1 -> 201
  main=3 revision=0 -> 300
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "version.toml"


def read() -> tuple[int, int]:
    if not VERSION_FILE.exists():
        return 2, 0
    text = VERSION_FILE.read_text(encoding="utf-8")
    main = re.search(r"^main\s*=\s*(\d+)", text, re.M)
    revision = re.search(r"^revision\s*=\s*(\d+)", text, re.M)
    if not main or not revision:
        sys.exit(f"{VERSION_FILE} 缺少 main/revision")
    return int(main.group(1)), int(revision.group(1))


def code(main: int, revision: int) -> int:
    return main * 100 + revision


def write(main: int, revision: int) -> None:
    if main < 0 or not 0 <= revision <= 99:
        sys.exit("版本范围：main >= 0，0 <= revision <= 99")
    VERSION_FILE.write_text(
        "[version]\n"
        f"main = {main}\n"
        f"revision = {revision}\n",
        encoding="utf-8",
    )


def show(main: int, revision: int) -> None:
    print(f"main={main} revision={revision} code={code(main, revision)}")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="daju-revival 项目版本号")
    p.add_argument("action", nargs="?", default="show", choices=["show", "dev", "release", "check"])
    p.add_argument("--main", type=int, help="set 时指定主版本")
    p.add_argument("--revision", type=int, help="set 时指定修订号")
    p.add_argument("--set", action="store_true", help="手工设置版本")
    args = p.parse_args(argv)

    cur_main, cur_rev = read()
    if args.set:
        if args.main is None and args.revision is None:
            sys.exit("--set 需要 --main 或 --revision")
        write(args.main if args.main is not None else cur_main,
              args.revision if args.revision is not None else cur_rev)
    elif args.action == "show":
        pass
    elif args.action == "dev":
        if cur_rev >= 99:
            sys.exit("revision 已到 99，不能再加开发版；请发布主版本")
        write(cur_main, cur_rev + 1)
    elif args.action == "release":
        write(cur_main + 1, 0)
    elif args.action == "check":
        if not 0 <= cur_rev <= 99:
            sys.exit("revision 超出范围")
    show(*read())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
