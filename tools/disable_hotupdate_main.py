#!/usr/bin/env python3
"""在 assets/main.js 最前面清掉热更搜索路径和缓存，强制使用 APK 内 project.jsc。"""
import sys

CLEAR = '''(function () {
    try {
        localStorage.removeItem("HotUpdateSearchPaths");
        if (typeof jsb === "object" && jsb.fileUtils) {
            var p = jsb.fileUtils.getWritablePath() + "blackjack-remote-asset/";
            jsb.fileUtils.removeDirectory(p);
            jsb.fileUtils.removeDirectory(p + "_temp/");
        }
    } catch (e) {}
})();
'''


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/disable_hotupdate_main.py <main.js> <out.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()
    open(out, "w", encoding="utf-8").write(CLEAR + text)
    print(f"hot-update disabled: {src} -> {out}")


if __name__ == "__main__":
    main()
