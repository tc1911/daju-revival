#!/usr/bin/env python3
"""只移除商店里的人民币(cash)购买项，保留商城和游戏内货币购买。

- ShopUI.getUserInfo：过滤 specialItemList/soulItemList 中 currencyType == "cash"
  的商品（这些来自 product_allplatform，是真实货币内购）。
- Common.showAppBuySpecialStatusDialog：人民币礼包弹窗置为 toast + return 1。
- 不拦截 ShopUI，商城主界面继续可用。
"""
import sys


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/remove_rmb_shop_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    old = '''this.specialItemList = e;
this.soulItemList = t;'''
    new = '''this.specialItemList = e.filter(function(e) {
return "cash" != e.currencyType;
});
this.soulItemList = t.filter(function(e) {
return "cash" != e.currencyType;
});'''
    if text.count(old) != 1:
        sys.exit(f"shop item lists anchor: expected 1, found {text.count(old)}")
    text = text.replace(old, new)

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
    print(f"RMB shop options removed: {src} -> {out}")


if __name__ == "__main__":
    main()
