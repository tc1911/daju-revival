#!/usr/bin/env python3
"""设置页精简 + 空白关于页。

- 隐藏：使用自己的头像/昵称、个性化推荐、自动使用充电宝、隐私政策、用户协议、注销账号
- 保留：点屏幕出新消息、好友打字速度2倍、关闭音效、游戏说明
- 底部“隐私政策”位置改成“关于”，点击打开一个空白关于页
- 收紧布局：音频设置上移，底部容器上移
"""
import tomllib
import sys
from pathlib import Path

REFRESH_OLD = '''this.useNickName.active = !1;
this.disableRmd.active = !1;
if (this.nickTip) this.nickTip.node.active = !1;'''

REFRESH_NEW = '''this.useNickName.active = !1;
this.disableRmd.active = !1;
if (this.autoUse && this.autoUse.parent) this.autoUse.parent.active = !1;
else if (this.autoUse) this.autoUse.active = !1;
if (this.cosplayNode) this.cosplayNode.active = !1;
if (this.nickTip) this.nickTip.node.active = !1;
var gsContainer = this.node.getChildByName("container");
var gsBottom = gsContainer && gsContainer.getChildByName("bottomContainer");
if (gsBottom) gsBottom.active = !1;
if (this.offMusic) this.offMusic.setPosition(210, 233.5);
if (!this.node.__dajuSettingsFooter) {
this.node.__dajuSettingsFooter = !0;
var self = this;
var footer = new cc.Node("dajuSettingsFooter");
gsContainer.addChild(footer);
footer.setPosition(0, -330);
function dajuFooterRow(text, y, action) {
var row = new cc.Node(text);
footer.addChild(row);
row.setContentSize(540, 50);
row.setPosition(0, y);
var bg = row.addComponent(cc.Graphics);
bg.fillColor = cc.color(255, 250, 242, 255);
bg.rect(-270, -25, 540, 50);
bg.fill();
var btn = row.addComponent(cc.Button);
btn.transition = cc.Button.Transition.NONE;
var labNode = new cc.Node("label");
row.addChild(labNode);
var lab = labNode.addComponent(cc.Label);
lab.string = text;
lab.fontSize = 24;
lab.lineHeight = 28;
labNode.color = cc.color(90, 70, 50);
labNode.setPosition(0, 0);
row.on(cc.Node.EventType.TOUCH_END, action);
}
dajuFooterRow("游戏说明", 29, function() { self.onClickButton({ name: "btn_1<Button>" }); });
dajuFooterRow("关于", -29, function() { self.onClickButton({ name: "btn_2<Button>" }); });
function dajuFooterPair(t1, t2, y, a1, a2) {
var row = new cc.Node("dajuSavePair");
footer.addChild(row);
row.setContentSize(540, 50);
row.setPosition(0, y);
var bg = row.addComponent(cc.Graphics);
bg.fillColor = cc.color(255, 250, 242, 255);
bg.rect(-270, -25, 540, 50);
bg.fill();
var btn = row.addComponent(cc.Button);
btn.transition = cc.Button.Transition.NONE;
var l1 = new cc.Node("label1");
row.addChild(l1);
var a = l1.addComponent(cc.Label);
a.string = t1;
a.fontSize = 24;
a.lineHeight = 28;
l1.color = cc.color(90, 70, 50);
l1.setPosition(-135, 0);
var l2 = new cc.Node("label2");
row.addChild(l2);
var b = l2.addComponent(cc.Label);
b.string = t2;
b.fontSize = 24;
b.lineHeight = 28;
l2.color = cc.color(90, 70, 50);
l2.setPosition(135, 0);
row.on(cc.Node.EventType.TOUCH_END, function(ev) {
var p = ev.getLocation();
var local = row.convertToNodeSpaceAR(cc.v2(p.x, p.y));
if (local.x < 0) a1(); else a2();
});
}
dajuFooterPair("导出存档", "导入存档", -87,
function() { window.__dajuExportSave && window.__dajuExportSave(); },
function() { window.__dajuImportSave && window.__dajuImportSave(); });
}
if (this.offMusic) this.offMusic.setPosition(210, 233.5);'''

BTN2_OLD = '''case "btn_2<Button>":
g.AudioPlayer.getInst().playSound(h.AudioUrls.common_sound);
c.default.Platform.isNative() ? y.default.getInstance().clickUserProtal() : "wxgame" == c.default.Platform.name && wx.openTencentPrivacyContract();
break;'''

BTN2_NEW = '''case "btn_2<Button>":
g.AudioPlayer.getInst().playSound(h.AudioUrls.common_sound);
window.openAboutPage && window.openAboutPage();
break;'''

def project_version_name() -> str:
    try:
        with open(Path(__file__).resolve().parent.parent / "version.toml", "rb") as f:
            v = tomllib.load(f)["version"]
        game = str(v.get("game", "6.12"))
        code = int(v["main"]) * 100 + int(v["revision"])
        return f"{game}.{code}"
    except Exception:
        return "6.12.200"


ABOUT_JS = '''
window.openAboutPage = function() {
var scene = cc.director.getScene();
if (!scene || scene.getChildByName("aboutPage")) return;
var root = new cc.Node("aboutPage");
scene.addChild(root, 2000);
root.setContentSize(cc.winSize);
root.setPosition(cc.winSize.width / 2, cc.winSize.height / 2);
try { root.addComponent(cc.BlockInputEvents); } catch (e) {}
var mask = new cc.Node("mask");
root.addChild(mask);
mask.setContentSize(cc.winSize);
var g = mask.addComponent(cc.Graphics);
g.fillColor = cc.color(248, 244, 236, 255);
g.rect(-cc.winSize.width / 2, -cc.winSize.height / 2, cc.winSize.width, cc.winSize.height);
g.fill();
mask.on(cc.Node.EventType.TOUCH_END, function() { root.destroy(); });
var title = new cc.Node("title");
root.addChild(title);
title.setPosition(0, cc.winSize.height / 2 - 90);
var tl = title.addComponent(cc.Label);
tl.string = "关于";
tl.fontSize = 34;
title.color = cc.color(70, 55, 40);

var addLine = function(text, size, y) {
var n = new cc.Node("aboutLine");
root.addChild(n);
n.setPosition(0, y);
var l = n.addComponent(cc.Label);
l.string = text;
l.fontSize = size;
l.lineHeight = Math.round(size * 1.4);
l.horizontalAlign = 1;
l.enableWrapText = false;
try { l.overflow = cc.Label.Overflow.NONE; } catch (e) {}
n.color = cc.color(70, 55, 40);
};

var y = cc.winSize.height / 2 - 170;
addLine("《橘猫侦探社》离线复刻版", 26, y); y -= 46;
addLine("版本 6.12 · versionCode 12", 20, y); y -= 40;
addLine("Android arm64 离线版", 18, y); y -= 36;
addLine("许可：禁止商用（Non-Commercial）", 18, y); y -= 38;
addLine("—— 制作与修改 ——", 18, y); y -= 36;
addLine("daju-revival 项目", 20, y); y -= 38;
addLine("逆向开发者：tc1911", 20, y); y -= 34;
addLine("仓库：https://github.com/tc1911/daju-revival", 16, y); y -= 34;
addLine("GitHub：https://github.com/tc1911", 16, y); y -= 38;
addLine("AI 助手：大肥鱼", 20, y); y -= 44;
addLine("—— 版权与免责声明 ——", 18, y); y -= 36;
addLine("原作与素材版权归 乐元素（Happy Elements）所有。", 18, y); y -= 34;
addLine("本工程仅供个人研究与离线保存，", 18, y); y -= 30;
addLine("不分发游戏素材与原版代码，与乐元素无关。", 18, y);

var back = new cc.Node("back");
root.addChild(back);
back.setPosition(-cc.winSize.width / 2 + 60, cc.winSize.height / 2 - 90);
var bl = back.addComponent(cc.Label);
bl.string = "返回";
bl.fontSize = 24;
back.color = cc.color(70, 55, 40);
back.setContentSize(120, 60);
back.on(cc.Node.EventType.TOUCH_END, function() { root.destroy(); });
};
'''



BACK_JS = """
(function() {
var prevBack = window.onAndroidBack;
window.onAndroidBack = function() {
var scene = cc.director.getScene();
if (scene) {
var about = scene.getChildByName("aboutPage");
if (about) { about.destroy(); return; }
var guide = scene.getChildByName("guide");
if (guide) { guide.destroy(); return; }
var tips = scene.getChildByName("commonTips");
if (tips) { tips.destroy(); return; }
var img = scene.getChildByName("ImageView");
if (img) { img.destroy(); return; }
}
if (prevBack) return prevBack.apply(this, arguments);
};
})();
"""


BATT_OLD = """t.prototype.refreshElectricity = function() {
var e = a.default.DataManager.getInfo(r.InfoType.USER_INFO);
this.node.getChildByName("electricity_lb").getComponent(cc.Label).string = e.electricity.toString() + "%";
this.node.getChildByName("electricity").setContentSize(35 * e.electricity / 100, 14);
};"""

BATT_NEW = """t.prototype.refreshElectricity = function() {
var lvl = 100;
try {
lvl = jsb.reflection.callStaticMethod("org/cocos2dx/javascript/ProfileBridge", "getBatteryLevel", "()I");
} catch (e) {}
if (!lvl || lvl < 0 || lvl > 100) lvl = 100;
this.node.getChildByName("electricity_lb").getComponent(cc.Label).string = lvl + "%";
var oldA = this.node.getChildByName("chat_img_power_a");
var oldB = this.node.getChildByName("chat_img_power_b");
if (oldA) oldA.active = !1;
if (oldB) oldB.active = !1;
var custom = this.node.getChildByName("dajuBattery");
if (!custom) {
custom = new cc.Node("dajuBattery");
this.node.addChild(custom);
var oldPos = oldA ? oldA.getPosition() : cc.v2(-239.4, 9.2);
custom.setPosition(oldPos);
custom.addComponent(cc.Graphics);
}
var bg = custom.getComponent(cc.Graphics);
if (bg) {
bg.clear();
bg.lineWidth = 2;
bg.strokeColor = cc.color(90, 70, 50, 255);
bg.fillColor = cc.color(245, 166, 35, 255);
bg.rect(-17, -8, 34, 16);
bg.stroke();
bg.fillRect(-15, -6, 30 * lvl / 100, 12);
bg.rect(17, -3, 4, 6);
bg.fill();
}
if (!this.node.__batteryTimer) this.node.__batteryTimer = setInterval(this.refreshElectricity.bind(this), 60000);
};"""

FULL_POWER_JS = """
(function() {
var App = window.__require("App").default;
var InfoType = { USER_INFO: 0 };
try { InfoType = window.__require("InfoType").default; } catch (e) {}
function batteryHud() {
try {
var scene = cc.director.getScene();
if (!scene) return;
function hide(n) {
if (n.name == "chat_img_power_a" || n.name == "chat_img_power_b" || n.name == "electricity_lb" || n.name == "PowerOff" || n.name == "electricity_tip") n.active = !1;
for (var i = 0; i < n.children.length; i++) hide(n.children[i]);
}
hide(scene);
var lvl = 100;
try { lvl = jsb.reflection.callStaticMethod("org/cocos2dx/javascript/ProfileBridge", "getBatteryLevel", "()I"); } catch (e) {}
if (lvl < 0 || lvl > 100) lvl = 100;
var hud = scene.getChildByName("dajuBatteryHud");
if (!hud) {
hud = new cc.Node("dajuBatteryHud");
scene.addChild(hud, 9999);
hud.setPosition(cc.winSize.width / 2, cc.winSize.height / 2);
hud.addComponent(cc.Graphics);
}
var g = hud.getComponent(cc.Graphics);
if (!g) return;
g.clear();
var x = -cc.winSize.width / 2 + 22;
var y = cc.winSize.height / 2 - 16;
g.lineWidth = 2;
g.strokeColor = cc.color(90, 70, 50, 255);
g.fillColor = cc.color(245, 166, 35, 255);
g.rect(x, y - 6, 24, 12);
g.stroke();
g.fillRect(x + 2, y - 4, 20 * lvl / 100, 8);
g.rect(x + 24, y - 3, 3, 6);
g.stroke();
} catch (e) {}
}
setInterval(batteryHud, 100);
batteryHud();
})();
"""


PERSIST_JS = """
(function() {
var LS = window.__require("LocalStorage").default;
var Common = window.__require("Common").default;
var path = jsb.fileUtils.getWritablePath() + "daju_state.json";
var chatStorePath = jsb.fileUtils.getWritablePath() + "daju_chat_store.json";
function readState() {
try {
var raw = jsb.fileUtils.getStringFromFile(path);
if (!raw) return null;
return JSON.parse(raw);
} catch (e) { return null; }
}
function currentState() {
return {
chat: String(LS.getLastChatId() || "0"),
speed: Number(LS.getIsSpeedUp()),
trigger: LS.getOffTriggerMessage() ? 1 : 0,
music: LS.getOffMusic() ? 1 : 0
};
}
function applyState(st) {
if (!st) return;
try {
var curChat = LS.getLastChatId();
if (st.chat && st.chat !== "0" && (!curChat || curChat === "0")) LS.setLastChatId(st.chat);
} catch (e) {}
try { if (typeof st.speed !== "undefined") LS.setIsSpeedUp(st.speed); } catch (e) {}
try { if (typeof st.trigger !== "undefined") LS.setOffTriggerMessage(!!st.trigger); } catch (e) {}
try { if (typeof st.music !== "undefined") LS.setOffMusic(!!st.music); } catch (e) {}
}
function saveState() {
try { jsb.fileUtils.writeStringToFile(JSON.stringify(currentState()), path); } catch (e) {}
try {
var oldStore = {};
try {
var oldRaw = jsb.fileUtils.getStringFromFile(chatStorePath);
if (oldRaw) oldStore = JSON.parse(oldRaw);
} catch (e2) {}
var list = Common.chatInfo().getChatList();
for (var i = 0; i < list.length; i++) oldStore[list[i].key] = list[i].value;
jsb.fileUtils.writeStringToFile(JSON.stringify(oldStore), chatStorePath);
} catch (e) {}
}
var st = readState();
setTimeout(function() { applyState(st); }, 3000);
setTimeout(function() { applyState(st); }, 4200);
setTimeout(function() { applyState(st); }, 5400);
setTimeout(function() {
setInterval(saveState, 1000);
saveState();
}, 6000);
})();
"""


BAG_FUNCS = '''
t.prototype._loadLocalBag = function() {
try {
var raw = cc.sys.localStorage.getItem("daju_bag_items");
if (raw) {
var data = JSON.parse(raw);
if (data && data.itemList) {
this._itemList = {};
for (var k in data.itemList) {
var it = data.itemList[k];
if (it && null != it.id) this._itemList[it.id] = { id: Number(it.id), count: Number(it.count) || 0 };
}
}
if (data && null != data.powerBank) this._powerBank = data.powerBank;
if (data && null != data.alarmClock) this._alarmClock = data.alarmClock;
if (data && null != data.coffee) this._coffee = data.coffee;
}
} catch (e) {}
this._bagLoaded = !0;
};
t.prototype._saveLocalBag = function() {
if (!this._bagLoaded) return;
try {
var items = {};
for (var k in this._itemList) {
var it = this._itemList[k];
if (it && null != it.id) items[it.id] = { id: Number(it.id), count: it.count };
}
cc.sys.localStorage.setItem("daju_bag_items", JSON.stringify({
itemList: items,
powerBank: this._powerBank,
alarmClock: this._alarmClock,
coffee: this._coffee
}));
} catch (e) {}
};
'''




SAVE_TRANSFER_JS = r"""
function __dajuB64Enc(data) {
var bytes = data instanceof Uint8Array ? data : new Uint8Array(data);
var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
var out = "";
for (var i = 0; i < bytes.length; i += 3) {
var a = bytes[i], b = i + 1 < bytes.length ? bytes[i + 1] : 0, c = i + 2 < bytes.length ? bytes[i + 2] : 0;
out += chars.charAt(a >> 2) + chars.charAt(((a & 3) << 4) | (b >> 4)) + chars.charAt(((b & 15) << 2) | (c >> 6)) + chars.charAt(c & 63);
}
var pad = bytes.length % 3;
if (pad == 1) out = out.substring(0, out.length - 2) + "==";
else if (pad == 2) out = out.substring(0, out.length - 1) + "=";
return out;
}
function __dajuB64Dec(str) {
var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
var map = {};
for (var i = 0; i < chars.length; i++) map[chars.charAt(i)] = i;
var clean = String(str || "").replace(/[^A-Za-z0-9+/=]/g, "");
var out = [];
for (var j = 0; j < clean.length; j += 4) {
var a = map[clean.charAt(j)], b = map[clean.charAt(j + 1)];
var c = clean.charAt(j + 2) == "=" ? 0 : map[clean.charAt(j + 2)];
var d = clean.charAt(j + 3) == "=" ? 0 : map[clean.charAt(j + 3)];
out.push((a << 2) | (b >> 4));
if (clean.charAt(j + 2) != "=") out.push(((b & 15) << 4) | (c >> 2));
if (clean.charAt(j + 3) != "=") out.push(((c & 3) << 6) | d);
}
return new Uint8Array(out);
}
function __dajuFilePath(name) {
try { return jsb.fileUtils.getWritablePath() + name; } catch (e) { return name; }
}
window.__dajuExportSave = function() {
try {
var s = window.__dajuSaveSnapshot ? window.__dajuSaveSnapshot() : null;
if (!s || 1 !== Number(s.version) || !s.data) {
window.__require("Common").default.showToast("没有可导出的 v1 存档");
return;
}
s.files = {};
try {
var st = jsb.fileUtils.getStringFromFile(__dajuFilePath("daju_state.json"));
if (st) s.files.state = st;
var chat = jsb.fileUtils.getStringFromFile(__dajuFilePath("daju_chat_store.json"));
if (chat) s.files.chat = chat;
} catch (e) {}
try {
var head = s.data.daju_profile_head;
if (head) {
var raw = jsb.fileUtils.getDataFromFile(head);
if (raw) s.files.avatar = { path: head, b64: __dajuB64Enc(raw) };
}
} catch (e) {}
var text = JSON.stringify(s);
if (typeof jsb === "undefined" || !jsb.reflection) {
window.__require("Common").default.showToast("仅支持 Android 导出");
return;
}
jsb.reflection.callStaticMethod("org/cocos2dx/javascript/ProfileBridge", "exportSave", "(Ljava/lang/String;)V", text);
} catch (e) {
window.__require("Common").default.showToast("导出失败: " + (e.message || e));
}
};
window.__dajuImportSave = function() {
try {
console.log("DAJU_SAVE_IMPORT_TAP");
window.__require("Common").default.showToast("正在打开文件选择器");
if (typeof jsb === "undefined" || !jsb.reflection) {
window.__require("Common").default.showToast("仅支持 Android 导入");
return;
}
jsb.reflection.callStaticMethod("org/cocos2dx/javascript/ProfileBridge", "importSave", "()V");
} catch (e) {
window.__require("Common").default.showToast("导入失败: " + (e.message || e));
}
};
window.onDajuSaveExported = function(ok, msg) {
window.__require("Common").default.showToast(ok ? "存档已导出（全量）" : (msg || "导出失败"));
};
window.onDajuSaveImportError = function(msg) {
window.__require("Common").default.showToast(msg || "存档读取失败");
};
window.onDajuSaveImported = function(text) {
var Common = window.__require("Common").default;
console.log("DAJU_IMPORT_TEXT", text ? text.length : -1, text ? text.substring(0, 120) : "");
var KEY = "daju_save_v1";
try {
var s = JSON.parse(text);
console.log("DAJU_IMPORT_PARSED", s && s.version, s && typeof s.data);
if (!s || 1 !== Number(s.version) || !s.data || "object" != typeof s.data) {
throw new Error("不是 v1 存档格式");
}
var data = s.data;
var files = s.files || {};
var cur = cc.sys.localStorage.getItem(KEY);
if (cur) cc.sys.localStorage.setItem(KEY + "_import_backup", cur);
if (files.state) {
try { jsb.fileUtils.writeStringToFile(String(files.state), __dajuFilePath("daju_state.json")); } catch (e) {}
}
if (files.chat) {
try { jsb.fileUtils.writeStringToFile(String(files.chat), __dajuFilePath("daju_chat_store.json")); } catch (e) {}
}
if (files.avatar && files.avatar.b64) {
var target = files.avatar.path || __dajuFilePath("profile_avatar_import.png");
try {
var bytes = __dajuB64Dec(files.avatar.b64);
var ok = jsb.fileUtils.writeDataToFile(bytes, target);
if (!ok) {
target = __dajuFilePath("profile_avatar_import.png");
jsb.fileUtils.writeDataToFile(bytes, target);
}
data.daju_profile_head = target;
} catch (e) {}
}
cc.sys.localStorage.setItem(KEY, JSON.stringify(s));
if (window.__dajuSaveReset) window.__dajuSaveReset();
var seen = window.__dajuSaveSeen ? window.__dajuSaveSeen() : [];
for (var k in data) {
if (k.indexOf("daju_save") === 0) continue;
cc.sys.localStorage.setItem(k, String(data[k]));
}
if (s.full) for (var i = 0; i < seen.length; i++) {
var sk = seen[i];
if (sk.indexOf("daju_save") === 0) continue;
if (!Object.prototype.hasOwnProperty.call(data, sk)) cc.sys.localStorage.removeItem(sk);
}
if (window.__dajuSaveSetSeen) window.__dajuSaveSetSeen(data);
if (window.__dajuSaveLock) window.__dajuSaveLock(true);
Common.showToast("全量存档导入成功，正在重启");
setTimeout(function() { cc.game.restart(); }, 50);
} catch (e) {
Common.showToast("存档导入失败: " + (e.message || e));
}
};
"""


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/settings_cleanup_patch.py <in.js> <out.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    if text.count(REFRESH_OLD) != 1:
        sys.exit(f"settings refresh anchor: expected 1, found {text.count(REFRESH_OLD)}")
    text = text.replace(REFRESH_OLD, REFRESH_NEW)

    if text.count(BTN2_OLD) != 1:
        sys.exit(f"btn_2 anchor: expected 1, found {text.count(BTN2_OLD)}")
    text = text.replace(BTN2_OLD, BTN2_NEW)

    UD_SETTERS = [
        ("t.setBool = function(e, t, n) {\nvoid 0 === n && (n = !1);", "t.setBool = function(e, t, n) {\nvoid 0 === n && (n = !0);"),
        ("t.getBool = function(e, t) {\nvoid 0 === t && (t = !1);", "t.getBool = function(e, t) {\nvoid 0 === t && (t = !0);"),
        ("t.setNumber = function(e, t, n) {\nvoid 0 === n && (n = !1);", "t.setNumber = function(e, t, n) {\nvoid 0 === n && (n = !0);"),
        ("t.getNumber = function(e, t) {\nvoid 0 === t && (t = !1);", "t.getNumber = function(e, t) {\nvoid 0 === t && (t = !0);"),
        ("t.setString = function(e, t, n) {\nvoid 0 === n && (n = !1);", "t.setString = function(e, t, n) {\nvoid 0 === n && (n = !0);"),
        ("t.getString = function(e, t) {\nvoid 0 === t && (t = !1);", "t.getString = function(e, t) {\nvoid 0 === t && (t = !0);")
    ]
    for old, new in UD_SETTERS:
        if text.count(old) != 1:
            sys.exit(f"UserDefault anchor not unique: {old!r} -> {text.count(old)}")
        text = text.replace(old, new)

    AUDIO_OLD = """e.prototype.init = function() {
var e = a.UserDefault.getNumber(r.Game.soundVol), t = a.UserDefault.getNumber(r.Game.musicVol);
this.setMusicMute(0 != t);
this.setMusicVolumn(1);
this.setSoundMute(0 != e);
this.setSoundVolumn(1);
};"""
    AUDIO_NEW = """e.prototype.init = function() {
var e = a.UserDefault.getNumber(r.Game.soundVol), t = a.UserDefault.getNumber(r.Game.musicVol);
this.setMusicMute(0 != t);
this.setMusicVolumn(1);
this.setSoundMute(0 != e);
this.setSoundVolumn(1);
if (a.UserDefault.getBool("off_music")) {
this.setMusicMute(!0);
this.setSoundMute(!0);
}
};"""
    if text.count(AUDIO_OLD) != 1:
        sys.exit(f"AudioPlayer.init anchor: {text.count(AUDIO_OLD)}")
    text = text.replace(AUDIO_OLD, AUDIO_NEW)

    ADD_OLD = """t.prototype.addElectricity = function(e, t) {
if (!(t && this._electricity >= 1e4)) {"""
    ADD_NEW = """t.prototype.addElectricity = function(e, t) {
if (e < 0) return;
if (!(t && this._electricity >= 1e4)) {"""
    if text.count(ADD_OLD) != 1:
        sys.exit(f"addElectricity anchor: {text.count(ADD_OLD)}")
    text = text.replace(ADD_OLD, ADD_NEW)

    if text.count(BATT_OLD) != 1:
        sys.exit(f"battery refresh anchor: expected 1, found {text.count(BATT_OLD)}")
    text = text.replace(BATT_OLD, BATT_NEW)

    # 背包/道具持久化：_itemList 和三种特殊道具计数写 LocalStorage，setData 时恢复。
    BAG_METHOD_ANCHOR = "t.prototype.getItemCount = function(e) {"
    if text.count(BAG_METHOD_ANCHOR) != 1:
        sys.exit(f"bag method anchor: {text.count(BAG_METHOD_ANCHOR)}")
    text = text.replace(BAG_METHOD_ANCHOR, BAG_FUNCS + BAG_METHOD_ANCHOR, 1)

    ITEMLIST_ANCHOR = "void 0 != e.itemList && (this._itemList = e.itemList);"
    if text.count(ITEMLIST_ANCHOR) != 1:
        sys.exit(f"bag itemList anchor: {text.count(ITEMLIST_ANCHOR)}")
    text = text.replace(ITEMLIST_ANCHOR, ITEMLIST_ANCHOR + "\nthis._loadLocalBag();", 1)

    ADDEND_ANCHOR = """n || (this._itemList[e] = {
id: Number(e),
count: t
});
}
};"""
    if text.count(ADDEND_ANCHOR) != 1:
        sys.exit(f"bag add end anchor: {text.count(ADDEND_ANCHOR)}")
    text = text.replace(ADDEND_ANCHOR, """n || (this._itemList[e] = {
id: Number(e),
count: t
});
}
this._saveLocalBag();
};""", 1)

    CONSUMEEND_ANCHOR = """}
c.default.EventManager.fire(l.EventItemRefresh.goodsChange);
c.default.EventManager.fire(l.EventName.refreshShop);
};
t.prototype.setData"""
    if text.count(CONSUMEEND_ANCHOR) != 1:
        sys.exit(f"bag consume end anchor: {text.count(CONSUMEEND_ANCHOR)}")
    text = text.replace(CONSUMEEND_ANCHOR, """}
this._saveLocalBag();
c.default.EventManager.fire(l.EventItemRefresh.goodsChange);
c.default.EventManager.fire(l.EventName.refreshShop);
};
t.prototype.setData""", 1)

    about = ABOUT_JS.replace("版本 6.12 · versionCode 12",
                             f"版本 {project_version_name()}")
    text += about
    text += SAVE_TRANSFER_JS
    text += BACK_JS
    text += FULL_POWER_JS
    open(out, "w", encoding="utf-8").write(text)
    print(f"settings cleaned: {src} -> {out}")


if __name__ == "__main__":
    main()
