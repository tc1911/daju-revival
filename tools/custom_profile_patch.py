#!/usr/bin/env python3
"""原生资料编辑：系统对话框改昵称、系统相册选头像并裁剪。

- “我”页加“编辑资料”，弹层只做展示/入口，不再用运行时 cc.EditBox。
- 昵称：调用 ProfileBridge.showNickname(current) 弹系统 AlertDialog+EditText，
  输入框会显示当前昵称，保存后回调 window.onNativeNickname。
- 头像：调用 ProfileBridge.pickAvatar() 打开系统相册，选图后自动居中裁剪成
  256x256 PNG，回调 window.onNativeAvatar(path)。
- 原生 Content_list_item.setOwnInfo 直接读本地键（daju_profile_name/head）渲染，
  外部路径走 LoaderManager.loadExternalAsset，内置头像走 setHeadSprite。
"""
import sys

JS = '''
(function() {
var LS = window.__require("LocalStorage").default;
var Common = window.__require("Common").default;
var App = window.__require("App").default;
var InfoType = { USER_INFO: 0 };
try { InfoType = window.__require("InfoType").default; } catch (e) {}

function customName() {
try { return cc.sys.localStorage.getItem("daju_profile_name") || LS.getSnsUserName(); } catch (e) { return LS.getSnsUserName(); }
}
function defaultHead() {
try {
var npcConfig = App.ConfigManager.getConfig("npcInfo");
var npc = npcConfig && npcConfig[20000001];
return npc && npc.headId ? "headImg_" + npc.headId : "";
} catch (e) { return ""; }
}
function customHead() {
try { return cc.sys.localStorage.getItem("daju_profile_head") || defaultHead(); } catch (e) { return defaultHead(); }
}

var origPlayerName = Common.getPlayerName;
Common.getPlayerName = function() {
var n = customName();
return n || origPlayerName.apply(this, arguments);
};
var origGroupName = Common.getGroupNickName;
Common.getGroupNickName = function() {
var n = customName();
return n || origGroupName.apply(this, arguments);
};
var origSnsHead = LS.getSnsUserHead;
LS.getSnsUserHead = function() {
var h = customHead();
return h || origSnsHead.apply(this, arguments);
};
function applyUserInfo() {
try {
try { LS.setUseNickNameAndIcon(true); } catch (e) {}
var ui = App.DataManager.getInfo(InfoType.USER_INFO);
if (!ui) return;
var n = customName();
if (n) { ui.nickName = n; ui._nickName = n; }
var h = customHead();
if (h) ui.headIcon = h;
} catch (e) {}
}
setTimeout(applyUserInfo, 500);
setInterval(applyUserInfo, 1000);
function refreshNative() {
var scene = cc.director.getScene();
if (!scene) return;
function walk(n) {
var comps = n.getComponents(cc.Component);
for (var i = 0; i < comps.length; i++) {
var c = comps[i];
if (c && c.setOwnInfo && c._data && c._data.id === 12) {
try { c.setOwnInfo(); } catch (e) {}
}
}
var ch = n.children;
for (var j = 0; j < ch.length; j++) walk(ch[j]);
}
walk(scene);
}
window.refreshNativeProfile = refreshNative;

function showHead(sprite, head, size) {
var sz = size || 96;
if (!sprite || !head) return;
if (0 == head.indexOf("headImg_")) {
try {
Common.setHeadSprite(sprite, head);
sprite.sizeMode = cc.Sprite.SizeMode.CUSTOM;
sprite.node.setContentSize(sz, sz);
} catch (e) {}
return;
}
try {
cc.loader.load({ url: head, type: "png" }, function(err, tex) {
if (!err && tex) {
sprite.spriteFrame = new cc.SpriteFrame(tex);
sprite.sizeMode = cc.Sprite.SizeMode.CUSTOM;
sprite.node.setContentSize(sz, sz);
}
});
} catch (e) {}
}

window.onNativeNickname = function(name) {
if (!name) return;
try { cc.sys.localStorage.setItem("daju_profile_name", name); } catch (e) {}
try { LS.setUseNickNameAndIcon(true); } catch (e) {}
LS.setSnsUserName(name);
try {
var ui = App.DataManager.getInfo(InfoType.USER_INFO);
if (ui) { ui.nickName = name; ui._nickName = name; }
} catch (e) {}
refreshNative();
if (window.__profileEditorRefresh) window.__profileEditorRefresh();
Common.showToast("昵称已保存");
};

window.onNativeAvatar = function(path) {
if (!path) return;
try { cc.sys.localStorage.setItem("daju_profile_head", path); } catch (e) {}
try { LS.setUseNickNameAndIcon(true); } catch (e) {}
LS.setSnsUserHead(path);
try {
var ui = App.DataManager.getInfo(InfoType.USER_INFO);
if (ui) ui.headIcon = path;
} catch (e) {}
refreshNative();
if (window.__profileEditorRefresh) window.__profileEditorRefresh();
Common.showToast("头像已更新");
};

window.openProfileEditor = function() {
var scene = cc.director.getScene();
if (!scene || scene.getChildByName("profileEditor")) return;
var root = new cc.Node("profileEditor");
scene.addChild(root, 2000);
root.setContentSize(cc.winSize);
root.setPosition(cc.winSize.width / 2, cc.winSize.height / 2);
try { root.addComponent(cc.BlockInputEvents); } catch (e) {}
var mask = new cc.Node("mask");
root.addChild(mask);
mask.setContentSize(cc.winSize);
mask.on(cc.Node.EventType.TOUCH_END, function() { root.destroy(); });
var g = mask.addComponent(cc.Graphics);
g.fillColor = cc.color(0, 0, 0, 170);
g.rect(-cc.winSize.width / 2, -cc.winSize.height / 2, cc.winSize.width, cc.winSize.height);
g.fill();
var panel = new cc.Node("panel");
root.addChild(panel);
panel.setContentSize(560, 620);
panel.setPosition(0, 0);
var pg = panel.addComponent(cc.Graphics);
pg.fillColor = cc.color(248, 244, 236, 255);
pg.roundRect(-280, -310, 560, 620, 24);
pg.fill();
function lab(text, x, y, size) {
var n = new cc.Node("lab");
panel.addChild(n);
n.setPosition(x, y);
var l = n.addComponent(cc.Label);
l.string = text;
l.fontSize = size || 24;
l.lineHeight = (size || 24) + 6;
n.color = cc.color(90, 70, 50);
return n;
}
lab("编辑资料", 0, 230, 32);
var nameBtn = lab(customName(), 0, 130, 30);
nameBtn.setContentSize(420, 90);
nameBtn.on(cc.Node.EventType.TOUCH_END, function() {
try {
jsb.reflection.callStaticMethod("org/cocos2dx/javascript/ProfileBridge", "showNickname", "(Ljava/lang/String;)V", customName());
} catch (e) {
Common.showToast("系统输入不可用");
}
});
var avatarNode = new cc.Node("avatar");
panel.addChild(avatarNode);
avatarNode.setPosition(0, -30);
avatarNode.setContentSize(160, 160);
var avatarSprite = avatarNode.addComponent(cc.Sprite);
avatarSprite.sizeMode = cc.Sprite.SizeMode.CUSTOM;
var avatarButton = avatarNode.addComponent(cc.Button);
avatarButton.transition = cc.Button.Transition.NONE;
avatarNode.on(cc.Node.EventType.TOUCH_END, function() {
try {
jsb.reflection.callStaticMethod("org/cocos2dx/javascript/ProfileBridge", "pickAvatar", "()V");
} catch (e) {
Common.showToast("相册不可用");
}
});
var closeX = lab("×", 245, 245, 34);
closeX.setContentSize(80, 80);
closeX.on(cc.Node.EventType.TOUCH_END, function() { root.destroy(); });

var catcher = new cc.Node("catcher");
root.addChild(catcher);
catcher.setContentSize(cc.winSize);
catcher.setPosition(0, 0);
var catcherBtn = catcher.addComponent(cc.Button);
catcherBtn.transition = cc.Button.Transition.NONE;
catcher.on(cc.Node.EventType.TOUCH_END, function(ev) {
var p = catcher.convertToNodeSpaceAR(ev.getLocation());
if (Math.abs(p.x) < 120 && Math.abs(p.y + 30) < 100) {
try {
jsb.reflection.callStaticMethod("org/cocos2dx/javascript/ProfileBridge", "pickAvatar", "()V");
} catch (e) { Common.showToast("相册不可用"); }
return;
}
if (Math.abs(p.x) < 230 && Math.abs(p.y - 130) < 60) {
try {
jsb.reflection.callStaticMethod("org/cocos2dx/javascript/ProfileBridge", "showNickname", "(Ljava/lang/String;)V", customName());
} catch (e) { Common.showToast("系统输入不可用"); }
return;
}
if (p.x > 180 && p.y > 200) {
root.destroy();
return;
}
root.destroy();
});
function refreshEditor() {
nameBtn.string = customName();
showHead(avatarSprite, customHead(), 160);
}
window.__profileEditorRefresh = function() {
if (cc.isValid(root)) refreshEditor();
};
refreshEditor();
};
})();
'''

SET_OWN_START = "t.prototype.setOwnInfo = function() {"
SET_OWN_END = "t.prototype.freeRecharge = function() {"

SET_OWN_NEW = '''t.prototype.setOwnInfo = function() {
var e = l.default.DataManager.getInfo(h.InfoType.USER_INFO), t = this.node.getChildByName("mask").getChildByName("head"), n = this.node.getChildByName("label");
var exNode = this.node.getChildByName("exchange");
if (exNode) exNode.active = !1;
var customName = null, customHead = null;
try {
customName = cc.sys.localStorage.getItem("daju_profile_name");
customHead = cc.sys.localStorage.getItem("daju_profile_head");
} catch (e) {}
if (customHead) {
if (0 == customHead.indexOf("headImg_")) {
u.default.setHeadSprite(t.getComponent(cc.Sprite), customHead);
} else {
l.default.LoaderManager.loadExternalAsset(customHead, function(e) {
t.getComponent(cc.Sprite).spriteFrame = new cc.SpriteFrame(e);
}, "png");
}
} else {
var o = l.default.ConfigManager.getConfig(g.ConfigType.NpcInfo)[20000001];
if (o) {
var i = o.nickName, r = "headImg_" + o.headId;
u.default.setHeadSprite(t.getComponent(cc.Sprite), r);
if (!customName) customName = i;
}
}
if (!customName) customName = u.default.getGroupNickName();
n.getComponent(cc.Label).string = customName;
var uidNode = this.node.getChildByName("uid");
if (uidNode) {
uidNode.active = !0;
var uidLabel = uidNode.getComponent(cc.Label);
if (uidLabel) uidLabel.string = "";
uidNode.setContentSize(360, 110);
uidNode.off(cc.Node.EventType.TOUCH_END);
uidNode.on(cc.Node.EventType.TOUCH_END, function() {
window.openProfileEditor && window.openProfileEditor();
});
}
try {
if (!this.node.__profileTapBound) {
this.node.__profileTapBound = true;
this.node.on(cc.Node.EventType.TOUCH_END, function() {
window.openProfileEditor && window.openProfileEditor();
});
}
} catch (e) {}
};
'''

BAG_ANCHOR = '''e.push({
name: getText("MainView_17"),
height: 80,
id: p.contentItemType.Bag,
noLine: !1,
icon: "icon_bag",
showArrow: !0
});'''

CLICK_ANCHOR = "this._data.onclick && this._data.onclick();"


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/custom_profile_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    uid_start = text.find("t.prototype.getUid = function() {")
    uid_end = text.find("t.prototype.getRmb = function() {", uid_start)
    if uid_start < 0 or uid_end < 0:
        sys.exit("getUid block boundaries not found")
    text = text[:uid_start] + 't.prototype.getUid = function() {\n window.openProfileEditor && window.openProfileEditor();\n};\n' + text[uid_end:]

    gs_pos = text.find("GameSetting: [")
    rv_pos = text.find("t.prototype.refreshView = function() {", gs_pos)
    if gs_pos < 0 or rv_pos < 0:
        sys.exit("GameSetting.refreshView not found")
    rv_brace = text.find("{", rv_pos) + 1
    text = text[:rv_brace] + '\nthis.useNickName.active = !1;\nthis.disableRmd.active = !1;\nif (this.nickTip) this.nickTip.node.active = !1;\n' + text[rv_brace:]

    own_start = text.find(SET_OWN_START)
    own_end = text.find(SET_OWN_END, own_start)
    if own_start < 0 or own_end < 0:
        sys.exit("setOwnInfo block boundaries not found")
    text = text[:own_start] + SET_OWN_NEW + text[own_end:]

    friend_old = """} else {
this.verification.active = !1;
this.container.active = !0;
}
this.refreshDynamicIcon();"""
    friend_new = """} else {
this.verification.active = !1;
this.container.active = !0;
this.container.setPosition(0, this.container.y);
this.verification.setPosition(540, 0);
}
this.refreshDynamicIcon();"""
    if text.count(friend_old) != 1:
        sys.exit("FriendUI refreshView reset: expected 1 match, found %d" % text.count(friend_old))
    text = text.replace(friend_old, friend_new, 1)

    text = text + JS
    open(out, "w", encoding="utf-8").write(text)
    print(f"native profile bridge UI patched: {src} -> {out}")


if __name__ == "__main__":
    main()
