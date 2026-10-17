#!/usr/bin/env python3
"""修复今日行程本地数据，并把充电宝改为给银币。

JS：
  1. HttpRequest.load 拦截 getTaskNew：返回 3 个本地任务（1/4/6）+ 完成奖励(8)，
     进度直接给满，可领取；用 window.__dailyClaimed 记录已领取。
  2. HttpRequest.load 拦截 getTaskReward：按 taskId 返回本地奖励，完成奖励给银币。
  3. usePowerBank / 背包使用充电宝：不再加电量，改为加 5000 银币（50001002）。
  4. 今日行程顶部“全部完成可获得充电宝”是烘焙的图片节点，运行时隐藏并替换成
     “全部完成可获得银币”文字 + 银币图标 + 5000 数量。

资产（由 tools/daily_currency_assets.py 处理）：
  - item 50000002 改名“银币袋”、描述、银币图标
"""
import sys

TASK_STUB = '''if ("getTaskNew" == this.method) {
var claimed = window.__dailyClaimed || {};
this.handler.onResponseInfoSuccess({
msgCode: 1,
watchAdCount: 0,
specifivInvite: 0,
tasklist: {
"1": { progress: 5, count: claimed[1] ? 1 : 0 },
"4": { progress: 1, count: claimed[4] ? 1 : 0 },
"6": { progress: 3, count: claimed[6] ? 1 : 0 },
"8": { progress: 3, count: claimed[8] ? 1 : 0 }
}
});
return;
}
if ("getTaskReward" == this.method) {
var params = {};
try { params = JSON.parse(this.buildParams); } catch (e) {}
var taskId = params && params[1] && params[1][0] ? String(params[1][0].taskId) : "";
window.__dailyClaimed = window.__dailyClaimed || {};
window.__dailyClaimed[taskId] = 1;
var rewards = [];
if ("1" == taskId) rewards = [ { itemId: "50001001", num: 25 } ];
else if ("4" == taskId) rewards = [ { itemId: "50001002", num: 320 } ];
else if ("6" == taskId) rewards = [ { itemId: "50001002", num: 300 } ];
else if ("8" == taskId) rewards = [ { itemId: "50001002", num: 5000 } ];
this.handler.onResponseInfoSuccess({ rewards: rewards });
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
lab.string = "全部完成可获得银币";
lab.fontSize = 24;
lab.lineHeight = 28;
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

    old_power = 'o.addElectricity(e.getGeneralParam("bankPower"));'
    n = text.count(old_power)
    if n < 1:
        sys.exit("power bank addElectricity: none found")
    text = text.replace(old_power, "o.addItemCountLocal(s.gold, 5000);")

    old_bag = 't.addElectricity(u.default.getGeneralParam("bankPower"));'
    if text.count(old_bag) != 1:
        sys.exit(f"bag power bank addElectricity: expected 1, found {text.count(old_bag)}")
    text = text.replace(old_bag, "t.addItemCountLocal(u.ItemType.gold, 5000);")

    old_toast = 'u.default.showToast("您使用了1个充电宝，补充了60%的电量");'
    if text.count(old_toast) != 1:
        sys.exit(f"bag toast: expected 1, found {text.count(old_toast)}")
    text = text.replace(old_toast, 'u.default.showToast("您使用了1个银币袋，获得5000银币");')

    old_top = 'this.taskNode.getChildByName("common_prop_bg_6").off(cc.Node.EventType.TOUCH_END);'
    if text.count(old_top) != 1:
        sys.exit(f"daily top icon anchor: expected 1, found {text.count(old_top)}")
    text = text.replace(old_top, TOP_PATCH + old_top)

    open(out, "w", encoding="utf-8").write(text)
    print(f"daily/currency patched: {src} -> {out}")


if __name__ == "__main__":
    main()
