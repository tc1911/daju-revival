#!/usr/bin/env python3
"""移除签到/充电/活动入口，保留商城。

处理：
  1. MainView.addMoodLayer：保留 朋友圈、今日行程、商城、案件记录、隐藏的故事；
     移除 7日福利(LoginBonus/签到)、睡前充电(ReserveRecharge)、
     共享充电宝(FreeRecharge)、活动(Activity_coin)、侦探训练营(Peripheral)。
     商城本体由 remove_rmb_shop_patch.py 精简。
  2. UserInfo.popLogin：置空，关掉每日签到/7日福利弹窗。

电量：本地账号补丁已让 costElectricityV2 每次都返回 100，读完消息不会掉电，
所以去掉充电入口后不会卡电量。

用法：tools/remove_monetization_patch.py <decrypted-project.js> <output.js>
"""
import sys

NEW_MOOD = '''t.prototype.addMoodLayer = function() {
this.mainScrollView.setGapY(0);
var e = [ {
name: getText("MainView_3"),
height: 90,
id: p.contentItemType.Tweet,
noLine: !0,
icon: "icon_social",
showArrow: !0
}, {
name: getText("MainView_6"),
height: 90,
id: p.contentItemType.Shop,
noLine: !0,
icon: "icon_store",
showArrow: !0
}, {
name: getText("MainView_9"),
height: 90,
id: p.contentItemType.DailyTask,
noLine: !0,
icon: "icon_target",
showArrow: !0
} ];
Number(d.default.chapterMaxChatId()) >= u.default.getGeneralParam("unlockBookMark") && e.push({
name: getText("MainView_19"),
height: 90,
id: p.contentItemType.bookMark,
noLine: !0,
icon: "icon_case",
showArrow: !0
});
e.push({
name: getText("MainView_12"),
height: 80,
id: p.contentItemType.Extra,
noLine: !0,
icon: "icon_morestory",
showArrow: !0
});
for (var n = 0; n < e.length; n++) {
var o = {
key: this.kContentItem,
data: e[n]
};
this.mainScrollView.appendData(o);
}
};
'''


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/remove_monetization_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    start = text.find("t.prototype.addMoodLayer = function() {")
    end = text.find("t.prototype.showTimeLimitPack = function(e, t) {", start)
    if start < 0 or end < 0:
        sys.exit("patch addMoodLayer: boundaries not found")
    text = text[:start] + NEW_MOOD + text[end:]

    start = text.find("t.prototype.popLogin = function() {")
    end = text.find("t.prototype.showTimeLimitPack = function(e, t, n) {", start)
    if start < 0 or end < 0:
        sys.exit("patch popLogin: boundaries not found")
    text = text[:start] + "t.prototype.popLogin = function() {};\n" + text[end:]

    # “我”页的问卷调查给充电宝，属于充电奖励，移除入口。
    old_feedback = '''e.push({
name: getText("FeedBack_1"),
height: 90,
id: p.contentItemType.FeedBack1,
noLine: !0,
icon: "common_btn_modify",
showArrow: !0
});
'''
    if text.count(old_feedback) != 1:
        sys.exit(f"patch feedback entry: expected 1 match, found {text.count(old_feedback)}")
    text = text.replace(old_feedback, "")

    # 服务器已停，客服入口一并移除。
    old_service = '''e.push({
name: getText("MainView_13"),
height: 80,
id: p.contentItemType.FeedBack,
noLine: !1,
icon: "icon_service",
showArrow: !0
});
'''
    if text.count(old_service) != 1:
        sys.exit(f"patch service entry: expected 1 match, found {text.count(old_service)}")
    text = text.replace(old_service, "")

    # “我”页成就列表：去掉“累计看广告充电次数”(60000005) 与“累计充值”(60000006)。
    ach_old = "for (o in n) {\ni = n[o];\nt.push({"
    ach_new = "for (o in n) {\ni = n[o];\nif (\"60000005\" == i.serverId || \"60000006\" == i.serverId) continue;\nt.push({"
    if text.count(ach_old) != 1:
        sys.exit(f"achievement list anchor: expected 1, found {text.count(ach_old)}")
    text = text.replace(ach_old, ach_new, 1)

    # “我”页底部的账号绑定 / 登出账号：整块不执行。
    bottom_old = 'if (c.default.Platform.isNative()) {\nif ("mock" == m.default.getLoginSNS()) {'
    bottom_new = 'if (!1) {\nif ("mock" == m.default.getLoginSNS()) {'
    if text.count(bottom_old) != 1:
        sys.exit(f"userview bottom anchor: expected 1, found {text.count(bottom_old)}")
    text = text.replace(bottom_old, bottom_new, 1)

    open(out, "w", encoding="utf-8").write(text)
    print(f"monetization removed: {src} -> {out}")


if __name__ == "__main__":
    main()
