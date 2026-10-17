#!/usr/bin/env python3
"""彻底关闭商店/内购入口。

- UIManager.pushUI：拦截 ShopUI，提示“商城已移除”，不加载商店。
- Common.showAppBuySpecialStatusDialog：直接 toast 并返回 1，不再弹购买弹窗。
"""
import sys


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/remove_shop_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    push_old = "e.prototype.pushUI = function(e) {"
    push_new = '''e.prototype.pushUI = function(e) {
if (e === s.GameSceneUIType.ShopUI) {
f.default.showToast("商城已移除");
return Promise.resolve();
}'''
    if text.count(push_old) != 1:
        sys.exit(f"pushUI anchor: expected 1, found {text.count(push_old)}")
    text = text.replace(push_old, push_new)

    start = text.find("e.showAppBuySpecialStatusDialog = function(t, n, o, i, r) {")
    end = text.find("e.friendIsAdd = function(e) {", start)
    if start < 0 or end < 0:
        sys.exit("showAppBuySpecialStatusDialog boundaries not found")
    stub = '''e.showAppBuySpecialStatusDialog = function(t, n, o, i, r) {
e.showToast("内购已移除");
return 1;
};
'''
    text = text[:start] + stub + text[end:]

    open(out, "w", encoding="utf-8").write(text)
    print(f"shop/IAP removed: {src} -> {out}")


if __name__ == "__main__":
    main()
