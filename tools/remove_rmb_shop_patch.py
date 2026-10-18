#!/usr/bin/env python3
"""精简商城本体：移除人民币内购与相关弹窗，保留游戏内货币商品。

- ShopUI.getUserInfo：过滤 specialItemList/soulItemList 中 currencyType == "cash"
  的商品（这些来自 product_allplatform，是真实货币内购）。
- Common.showAppBuySpecialStatusDialog：人民币礼包弹窗置为 toast + return 1。
- ShopUI.refreshView：特惠位为空时隐藏，避免 [0]/[1] 越界；余额数显不动。
- ShopUI.refreshItem：只刷新仍在显示的特惠位。
- ShopUI.onClickButton：返回不再触发“人民币不足”礼包弹窗。
- ShopUI.didOpen：隐藏娃娃机入口（gochaRed 的父节点 gacha）；
  这是旧广告营销抽奖入口，剥离广告 SDK 后没有意义。
- 不拦截 ShopUI，商城主界面继续可用。
"""
import sys


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/remove_rmb_shop_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    # 1) 过滤人民币商品
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

    # 2) 特惠位为空时隐藏，避免 refreshView 取 [0]/[1]
    refresh_old = '''this.shopItem1.refreshItem(this.specialItemList[0], this.buyItemId);
this.shopItem2.refreshItem(this.specialItemList[1], this.buyItemId);'''
    refresh_new = '''var s1 = this.specialItemList[0], s2 = this.specialItemList[1];
this.shopItem1.node.active = !!s1;
this.shopItem2.node.active = !!s2;
if (s1) this.shopItem1.refreshItem(s1, this.buyItemId);
if (s2) this.shopItem2.refreshItem(s2, this.buyItemId);'''
    if text.count(refresh_old) != 1:
        sys.exit(f"shop refreshView anchor: expected 1, found {text.count(refresh_old)}")
    text = text.replace(refresh_old, refresh_new)

    # 3) 隐藏后不再刷新特惠位
    item_old = '''this.shopItem1.refreshLabel();
this.shopItem2.refreshLabel();'''
    item_new = '''if (this.shopItem1.node.active) this.shopItem1.refreshLabel();
if (this.shopItem2.node.active) this.shopItem2.refreshLabel();'''
    if text.count(item_old) != 1:
        sys.exit(f"shop refreshItem anchor: expected 1, found {text.count(item_old)}")
    text = text.replace(item_old, item_new)

    # 4) 返回不再弹“人民币不足”礼包
    back_old = '''case "back<Button>":
if (!u.default.canClick()) return;
if (u.default.userInfo().getItemCount(u.ItemType.rmb) < 120) {
u.default.userInfo().showTimeLimitPack([ 1 ], function() {
c.default.UIManager.popUI(l.GameSceneUIType.ShopUI, !0);
});
return;
}
c.default.UIManager.popUI(l.GameSceneUIType.ShopUI, !0);
break;'''
    back_new = '''case "back<Button>":
if (!u.default.canClick()) return;
c.default.UIManager.popUI(l.GameSceneUIType.ShopUI, !0);
break;'''
    if text.count(back_old) != 1:
        sys.exit(f"shop back anchor: expected 1, found {text.count(back_old)}")
    text = text.replace(back_old, back_new)

    # 5) 隐藏娃娃机入口：gochaRed 是 gacha 节点下的红点，直接隐藏父节点
    gacha_old = 'u.default.userInfo().canUseGacha ? this.gochaRed.active = !0 : this.gochaRed.active = !1;'
    gacha_new = 'this.gochaRed && this.gochaRed.parent && (this.gochaRed.parent.active = !1);'
    if text.count(gacha_old) != 1:
        sys.exit(f"shop gacha anchor: expected 1, found {text.count(gacha_old)}")
    text = text.replace(gacha_old, gacha_new, 1)

    gacha_cb_old = 'u.default.userInfo().canUseGacha ? e.gochaRed.active = !0 : e.gochaRed.active = !1;'
    gacha_cb_new = 'e.gochaRed && e.gochaRed.parent && (e.gochaRed.parent.active = !1);'
    if text.count(gacha_cb_old) != 1:
        sys.exit(f"shop gacha callback anchor: expected 1, found {text.count(gacha_cb_old)}")
    text = text.replace(gacha_cb_old, gacha_cb_new, 1)

    # 6) 人民币礼包弹窗直接 toast
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
    print(f"shop trimmed: {src} -> {out}")


if __name__ == "__main__":
    main()
