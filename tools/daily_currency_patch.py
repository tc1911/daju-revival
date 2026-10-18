#!/usr/bin/env python3
"""把“今日行程”改成每日签到：每天领 5000 银币 + 500 金币。

JS：
  1. HttpRequest.load 拦截 getTaskNew / getTaskReward；
     每天一条签到，日期记在 cc.sys.localStorage，跨天重置。
  2. refreshView：隐藏三行日常任务，只保留“今日全部完成”宝箱作为签到按钮。
  3. 宝箱图标/文案改成“每日签到：5000银币 + 500金币”。
  4. 旧存档里的充电宝：背包使用只提示“已废弃”，不再提示“电量已满”。

资产（由 tools/daily_currency_assets.py 处理）：
  - item 50000002 恢复原名并标“（已废弃）”，下架
  - DailyTask 相关字符串改成“每日签到”，plan 8 改成签到奖励
"""
import sys

TASK_STUB = '''if ("getTaskNew" == this.method) {
var now = new Date();
var today = now.getFullYear() + "-" + (now.getMonth() + 1) + "-" + now.getDate();
var lastSign = cc.sys.localStorage.getItem("daju_daily_sign_date") || "";
this.handler.onResponseInfoSuccess({
msgCode: 1,
watchAdCount: 0,
specifivInvite: 0,
tasklist: {
"8": { progress: 3, count: lastSign == today ? 1 : 0 }
}
});
return;
}
if ("getTaskReward" == this.method) {
var params = {};
try { params = JSON.parse(this.buildParams); } catch (e) {}
var taskId = params && params[1] && params[1][0] ? String(params[1][0].taskId) : "";
var now = new Date();
var today = now.getFullYear() + "-" + (now.getMonth() + 1) + "-" + now.getDate();
var lastSign = cc.sys.localStorage.getItem("daju_daily_sign_date") || "";
if ("8" == taskId && lastSign != today) {
cc.sys.localStorage.setItem("daju_daily_sign_date", today);
this.handler.onResponseInfoSuccess({ rewards: [
{ itemId: "50001002", num: 5000 },
{ itemId: "50001001", num: 500 }
] });
return;
}
this.handler.onResponseInfoSuccess({ rewards: [] });
return;
}
'''

TOP_PATCH = '''try {
var oldTitle = this.taskNode.getChildByName("txt_title_16");
var titlePos = oldTitle ? oldTitle.getPosition() : cc.v2(0, 200);
if (oldTitle) oldTitle.active = false;
var iconNode = this.taskNode.getChildByName("item_icom");
if (iconNode) {
u.default.setItemSprite(iconNode.getComponent(cc.Sprite), "50001002");
var cntNode = iconNode.getChildByName("cnt");
if (cntNode) cntNode.getComponent(cc.Label).string = "5000";
}
var titleNode = this.taskNode.getChildByName("local_reward_title");
if (!titleNode) {
titleNode = new cc.Node("local_reward_title");
titleNode.parent = this.taskNode;
var lab = titleNode.addComponent(cc.Label);
lab.string = "每日签到：5000银币 + 500金币";
lab.fontSize = 22;
lab.lineHeight = 26;
titleNode.color = cc.color(109, 94, 79);
titleNode.setPosition(titlePos);
}
} catch (e) {}
'''


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/daily_currency_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    anchor = 'if (this.url && this.url.indexOf("happyelements.cn") >= 0) {'
    if text.count(anchor) != 1:
        sys.exit(f"daily patch anchor: expected 1, found {text.count(anchor)}")
    text = text.replace(anchor, TASK_STUB + anchor)

    # 旧存档里的充电宝：使用入口不再走“电量已满”分支，直接提示已废弃。
    old_full = '''if (t.electricity > 8e3) {
u.default.showToast(getText("BagUI_3"));
return [ 2 ];
}'''
    if text.count(old_full) != 1:
        sys.exit(f"bag full check: expected 1, found {text.count(old_full)}")
    text = text.replace(old_full, '''u.default.showToast("该充电宝已废弃，不再提供电量");
return [ 2 ];''', 1)

    old_power = 'o.addElectricity(e.getGeneralParam("bankPower"));'
    n = text.count(old_power)
    if n < 1:
        sys.exit("power bank addElectricity: none found")
    text = text.replace(old_power, "o.addItemCountLocal(s.gold, 5000);")

    old_bag = 't.addElectricity(u.default.getGeneralParam("bankPower"));'
    if text.count(old_bag) != 1:
        sys.exit(f"bag power bank addElectricity: expected 1, found {text.count(old_bag)}")
    text = text.replace(old_bag, "t.addItemCountLocal(u.ItemType.gold, 5000);")

    ach_old = """} else r.default.Http.request("getTaskReward", {
type: 2,
taskId: this._data.achieveId
}, function(e) {
if (e.rewards && e.rewards.length > 0) {
var n = getText("user_list_item_6");
"60000006" == t._data.achieveId && 50001001 == e.rewards[0].itemId && (n = "您已无需永恒电池组件，转换为以下商品");
a.default.userInfo().getRewards(e.rewards, n, "achievement");
a.default.userInfo().addItemCountLocal(t._data.achieveId, 1);
}
});"""
    ach_new = """} else {
var localReward = n ? [ { itemId: n.itemID, num: n.itemCount || 1 } ] : [];
if (localReward.length > 0) {
var rewardTitle = getText("user_list_item_6");
a.default.userInfo().getRewards(localReward, rewardTitle, "achievement");
a.default.userInfo().addItemCountLocal(this._data.achieveId, 1);
}
}"""
    if text.count(ach_old) != 1:
        sys.exit(f"achievement claim anchor: expected 1, found {text.count(ach_old)}")
    text = text.replace(ach_old, ach_new, 1)

    old_top = 'this.taskNode.getChildByName("common_prop_bg_6").off(cc.Node.EventType.TOUCH_END);'
    if text.count(old_top) != 1:
        sys.exit(f"daily top icon anchor: expected 1, found {text.count(old_top)}")
    text = text.replace(old_top, TOP_PATCH + old_top)

    # 隐藏三行日常任务，只保留宝箱作为每日签到按钮。
    old_list = 'e = u.default.userInfo().dailyTaskList;'
    if text.count(old_list) != 1:
        sys.exit(f"daily task list anchor: expected 1, found {text.count(old_list)}")
    text = text.replace(old_list, old_list + '''
for (var zi = 1; zi <= 3; zi++) { var zr = this.taskNode.getChildByName("user_list_item" + zi); if (zr) zr.active = !1; }''', 1)

    old_desc = '''this.taskNode.getChildByName("desc").getComponent(cc.Label).string = h.default.strfmt("完成今日全部行程（{0}/3）", i.progress + "");'''
    if text.count(old_desc) != 1:
        sys.exit(f"daily desc anchor: expected 1, found {text.count(old_desc)}")
    text = text.replace(old_desc, '''this.taskNode.getChildByName("desc").getComponent(cc.Label).string = "每日签到：5000银币 + 500金币";''', 1)

    open(out, "w", encoding="utf-8").write(text)
    print(f"daily sign-in patched: {src} -> {out}")


if __name__ == "__main__":
    main()
