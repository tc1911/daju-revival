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


SHOP_DAILY_JS = """
(function() {
function dajuDayKey() {
var d = new Date();
return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
}
function dajuDaily() {
var key = dajuDayKey(), o = {};
try { o = JSON.parse(cc.sys.localStorage.getItem("daju_shop_daily") || "{}") || {}; } catch (e) {}
if (o.date != key) o = { date: key, counts: {} };
if (!o.counts) o.counts = {};
return o;
}
window.__dajuShopUsed = function(id) {
var o = dajuDaily();
return Number(o.counts[String(id)] || 0);
};
window.__dajuShopAdd = function(id, n) {
var o = dajuDaily(), k = String(id), v = Number(o.counts[k] || 0) + Number(n || 0);
o.counts[k] = Math.min(3, v);
cc.sys.localStorage.setItem("daju_shop_daily", JSON.stringify(o));
return o.counts[k];
};
})();
"""


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/remove_rmb_shop_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    # 1) 今日特价：每日 2 礼物 + 1 功能道具，半价，限购 3
    pool_old = '''for (_ in m) (v = m[_]).onSale && "50100023" != v.serverId && (y == v.discountDay ? e.push(v) : t.push(v));'''
    pool_new = '''var __gifts = [], __funcs = [];
for (_ in m) {
v = m[_];
if (!v || "cash" == v.currencyType) continue;
var __sid = String(v.serverId);
if (__sid >= "50000101" && __sid <= "50000110") __gifts.push(v);
else if ("50000001" == __sid || "50000003" == __sid || "50000004" == __sid || "50000005" == __sid || "50000007" == __sid) __funcs.push(v);
}
var __now = new Date(u.default.userInfo().serverTime || Date.now());
var __seed = __now.getFullYear() * 372 + __now.getMonth() * 31 + __now.getDate();
var __mk = function(v) {
var q = {};
for (var k in v) q[k] = v[k];
var p = Number(v.price) || 0;
q.price = p;
q.discountPrice = Math.floor(p / 2);
q.originPrice = p;
q.discountDay = __now.getDay() || 7;
q.dailyLimit = 3;
q.dailyBought = window.__dajuShopUsed ? window.__dajuShopUsed(v.serverId) : 0;
q.description = (v.description || "") + " · 每日限购3";
return q;
};
if (__gifts.length >= 2 && __funcs.length >= 1) {
var __g1 = __gifts[__seed % __gifts.length];
var __g2 = __gifts[(__seed + 1 + (__seed % (__gifts.length - 1))) % __gifts.length];
var __f1 = __funcs[__seed % __funcs.length];
e = [__mk(__g1), __mk(__g2), __mk(__f1)];
}
var __specialIds = {};
for (var __ei = 0; __ei < e.length; __ei++) __specialIds[String(e[__ei].serverId)] = 1;
for (_ in m) {
v = m[_];
if (v && v.onSale && "50100023" != v.serverId && "cash" != v.currencyType && !__specialIds[String(v.serverId)]) t.push(v);
}'''
    if text.count(pool_old) != 1:
        sys.exit(f"shop daily pool anchor: expected 1, found {text.count(pool_old)}")
    text = text.replace(pool_old, pool_new)
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
    refresh_new = '''if (!this.shopItem3) {
var __si = this.shopItem1.node.parent;
var __n = cc.instantiate(this.shopItem1.node);
__n.name = "shopItem3";
__si.addChild(__n);
this.shopItem3 = __n.getComponent("shop_item");
this.shopItem1.node.setPosition(0, -162.5);
this.shopItem2.node.setPosition(0, -251.5);
this.shopItem3.node.setPosition(0, -340.5);
var __kids = __si.children;
for (var __i = 0; __i < __kids.length; __i++) {
if (__kids[__i].name == "shop_lab_001" && Math.abs(__kids[__i].y + 98) < 8) {
__kids[__i].active = true;
__kids[__i].setPosition(-190, -98.295);
}
if (__kids[__i].name == "shop_lab_001" && Math.abs(__kids[__i].y + 325) < 8) {
__kids[__i].active = true;
__kids[__i].setPosition(-190, -415);
this.__dajuHotTitle = __kids[__i];
}
if (__kids[__i].name == "line_4") {
__kids[__i].active = true;
__kids[__i].setPosition(0, -395);
this.__dajuHotLine = __kids[__i];
}
}
var __info = this.node.getChildByName("container").getChildByName("shopInfo");
if (__info) __info.height = 870;
var __sv = this.node.getChildByName("container").getChildByName("ScrollView");
if (__sv) {
this.__dajuScroll = __sv;
__sv.y = -40;
__sv.height = 400;
var __view = __sv.getChildByName("view");
if (__view) __view.height = 400;
}
}
var s1 = this.specialItemList[0], s2 = this.specialItemList[1], s3 = this.specialItemList[2];
this.shopItem1.node.active = !!s1;
this.shopItem2.node.active = !!s2;
this.shopItem3.node.active = !!s3;
if (s1) this.shopItem1.refreshItem(s1, this.buyItemId);
if (s2) this.shopItem2.refreshItem(s2, this.buyItemId);
if (s3) this.shopItem3.refreshItem(s3, this.buyItemId);
var __markSold = function(item, comp) {
if (!item || !comp) return;
var __dl = Number(item.dailyLimit || 0);
var __sold = __dl > 0 && (window.__dajuShopUsed ? window.__dajuShopUsed(item.serverId) : 0) >= __dl;
comp.node.opacity = __sold ? 150 : 255;
var __btn = null, __soldLbl = null;
for (var __ci = 0; __ci < comp.node.children.length; __ci++) {
var __ch = comp.node.children[__ci];
if (__ch.name == "button") __btn = __ch;
if (__ch.name == "__dajuSoldLbl") __soldLbl = __ch;
}
if (__btn) __btn.active = !__sold;
if (!__soldLbl) {
__soldLbl = new cc.Node("__dajuSoldLbl");
__soldLbl.setContentSize(130, 70);
__soldLbl.setPosition(200, 0);
var __sl = __soldLbl.addComponent(cc.Label);
__sl.string = "已售罄";
__sl.fontSize = 26;
__sl.lineHeight = 34;
__sl.horizontalAlign = 1;
__sl.verticalAlign = 1;
comp.node.addChild(__soldLbl, 10);
}
__soldLbl.active = __sold;
if (__soldLbl.active) {
__soldLbl.opacity = 255;
__soldLbl.color = cc.color(90, 90, 90);
}
};
__markSold(s1, this.shopItem1);
__markSold(s2, this.shopItem2);
__markSold(s3, this.shopItem3);
window.__dajuShopMarkSold = function() {
__markSold(s1, this.shopItem1);
__markSold(s2, this.shopItem2);
__markSold(s3, this.shopItem3);
}.bind(this);
if (this.__dajuScroll) {
var __scroll = this.__dajuScroll.getComponent(cc.ScrollView);
if (__scroll && __scroll.scrollToTop) {
this.scheduleOnce(function() {
__scroll.scrollToTop(0);
}, 0);
}
}'''
    if text.count(refresh_old) != 1:
        sys.exit(f"shop refreshView anchor: expected 1, found {text.count(refresh_old)}")
    text = text.replace(refresh_old, refresh_new)

    # 2.1) ShopSell.show：特价商品按剩余数量默认选中，最大一次买 3
    show_old = """this.maxCount = Math.floor(r.default.userInfo().getItemCount(e.currencyType) / this.singlePrice);
"50100023" == e.serverId && (this.maxCount = 1);
this.buyCount >= this.maxCount ? this.add.interactable = !1 : this.add.interactable = !0;
};"""
    show_new = """this.maxCount = Math.floor(r.default.userInfo().getItemCount(e.currencyType) / this.singlePrice);
"50100023" == e.serverId && (this.maxCount = 1);
var __dl = Number(e.dailyLimit || 0);
if (__dl > 0) {
var __used = window.__dajuShopUsed ? window.__dajuShopUsed(e.serverId) : 0;
var __left = Math.max(0, __dl - __used);
this.maxCount = Math.min(this.maxCount, __left);
this.buyCount = this.maxCount > 0 ? 1 : 0;
this.buyCnt.string = this.buyCount + "";
this.totalCost.string = this.singlePrice * this.buyCount + "";
this.reduce.interactable = this.buyCount > 1;
this.add.interactable = this.buyCount > 0 && this.buyCount < this.maxCount;
if (__left <= 0) this.item_dec.string = (e.description || "") + "（今日已售罄）";
} else {
this.buyCount >= this.maxCount ? this.add.interactable = !1 : this.add.interactable = !0;
}
};"""
    if text.count(show_old) != 1:
        sys.exit(f"shop sell show anchor: expected 1, found {text.count(show_old)}")
    text = text.replace(show_old, show_new, 1)

    cnt_old = """this.buyCount = t > 0 ? this.buyCount + 1 : this.buyCount - 1;
this.buyCount = Math.max(1, Math.min(this.maxCount, this.buyCount));
this.buyCount <= 1 ? this.reduce.interactable = !1 : this.reduce.interactable = !0;"""
    cnt_new = """this.buyCount = t > 0 ? this.buyCount + 1 : this.buyCount - 1;
var __min = this.maxCount > 0 ? 1 : 0;
this.buyCount = Math.max(__min, Math.min(this.maxCount, this.buyCount));
this.buyCount <= __min ? this.reduce.interactable = !1 : this.reduce.interactable = !0;"""
    if text.count(cnt_old) != 1:
        sys.exit(f"shop sell changeCnt anchor: expected 1, found {text.count(cnt_old)}")
    text = text.replace(cnt_old, cnt_new, 1)

    # 3) 隐藏后不再刷新特惠位
    item_old = '''this.shopItem1.refreshLabel();
this.shopItem2.refreshLabel();'''
    item_new = '''if (this.shopItem1.node.active) this.shopItem1.refreshLabel();
if (this.shopItem2.node.active) this.shopItem2.refreshLabel();
if (this.shopItem3 && this.shopItem3.node.active) this.shopItem3.refreshLabel();'''
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

    # 6) 今日特价限购 3：ShopSell 购买前检查，成功后记账
    buy_old = '''t.prototype.buyItem = function() {
var e = this;
if (r.default.canClick()) if (r.default.userInfo().getItemCount(this.itemInfo.currencyType) < this.buyCount * this.singlePrice) {'''
    buy_new = '''t.prototype.buyItem = function() {
var e = this;
if (this.maxCount <= 0) return;
if (r.default.canClick()) if (r.default.userInfo().getItemCount(this.itemInfo.currencyType) < this.buyCount * this.singlePrice) {'''
    if text.count(buy_old) != 1:
        sys.exit(f"shop sell guard anchor: expected 1, found {text.count(buy_old)}")
    text = text.replace(buy_old, buy_new, 1)

    buy_cb_old = '''r.default.userInfo().buyItem(this.itemInfo.serverId, this.buyCount, this.itemInfo.currencyType, this.buyCount * this.singlePrice, function() {
"50100023" != e.itemInfo.serverId'''
    buy_cb_new = '''r.default.userInfo().buyItem(this.itemInfo.serverId, this.buyCount, this.itemInfo.currencyType, this.buyCount * this.singlePrice, function() {
window.__dajuShopAdd && window.__dajuShopAdd(e.itemInfo.serverId, e.buyCount);
window.__dajuShopMarkSold && window.__dajuShopMarkSold();
"50100023" != e.itemInfo.serverId'''
    if text.count(buy_cb_old) != 1:
        sys.exit(f"shop sell callback anchor: expected 1, found {text.count(buy_cb_old)}")
    text = text.replace(buy_cb_old, buy_cb_new, 1)

    # 6.1) shop_item 的 originPrice 分支对缺失节点做空值保护
    origin_old = '''if (e.originPrice) {
u.y = -7;
f.y = -7;
d.y = -7;
y.y = -7;
p.active = !0;
p.getComponent(cc.Label).string = l.default.strfmt(getText("shop_item_1"), e.originPrice);
h.active = !0;
} else {
u.y = 0;
f.y = 0;
y.y = 0;
if (d) {
d.y = 0;
p.active = !1;
h.active = !1;
}
}'''
    origin_new = '''if (e.originPrice) {
u.y = -7;
f.y = -7;
if (d) d.y = -7;
y.y = -7;
if (p) {
p.active = !0;
p.getComponent(cc.Label).string = l.default.strfmt(getText("shop_item_1"), e.originPrice);
}
if (h) h.active = !0;
} else {
u.y = 0;
f.y = 0;
y.y = 0;
if (d) d.y = 0;
if (p) p.active = !1;
if (h) h.active = !1;
}'''
    if text.count(origin_old) != 1:
        sys.exit(f"shop_item originPrice anchor: expected 1, found {text.count(origin_old)}")
    text = text.replace(origin_old, origin_new, 1)

    # 7) 人民币礼包弹窗直接 toast
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

    text += SHOP_DAILY_JS
    open(out, "w", encoding="utf-8").write(text)
    print(f"shop trimmed: {src} -> {out}")


if __name__ == "__main__":
    main()
