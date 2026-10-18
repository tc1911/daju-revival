#!/usr/bin/env python3
"""把账号/登录改成纯本地方案（不访问已停服务器）。

对解密后的 project.js 做以下替换：
  1. LocalStorage.getLoginSNS() 为空时回退 "mock" → 启动时自动本地 guest 登录，不弹登录选择。
  2. UserInfo.sendMessage()：拦截 getUser / getStoreDataV2 / storageChat，直接回调本地数据。
  3. Launcher.getChatStorage()：没有聊天记录时也调用 getSpecialStatus，继续进场景。
  4. Launcher.getSpecialStatus()：不再请求 getSpecialStatusV2，直接 changeScene()。
  5. 启动参数 launchOption 缺失时给默认值，避免 p.query 崩溃。
  6. HttpRequest.load()：拦截 getUserInfoByAdditionalOrder / getAttrInfo，返回本地空数据。

本地账号固定 gid=10001，昵称“调查员A”，已实名/成年（跳过防沉迷校验）。
不做：不伪造剧情/任务等其它业务协议（后续需要再补）。

用法：tools/local_account_patch.py <decrypted-project.js> <output.js>
"""
import sys

OLD_SNS = '''e.getLoginSNS = function() {
return o.UserDefault.getString(e.KEY_TOKEN_SNS, !0);
};'''

NEW_SNS = '''e.getLoginSNS = function() {
var v = o.UserDefault.getString(e.KEY_TOKEN_SNS, !0);
return v && "undefined" != v ? v : "mock";
};'''

OLD_CHANNEL = '''e.getChannelNameSNS = function() {
return o.UserDefault.getString(e.KEY_CHANNELNAME_SNS, !0);
};'''

NEW_CHANNEL = '''e.getChannelNameSNS = function() {
var v = o.UserDefault.getString(e.KEY_CHANNELNAME_SNS, !0);
return v && "undefined" != v ? v : "guest";
};'''

OLD_SEND = '''t.prototype.sendMessage = function(e, t, n, o) {
void 0 === t && (t = {});'''

NEW_SEND = '''t.prototype.sendMessage = function(e, t, n, o) {
void 0 === t && (t = {});
if ("getUser" == e) {
var localGid = s.default.getGid() || 10001;
s.default.setGid(localGid);
n && n({
fail: 0,
gid: localGid,
newUser: !s.default.getLastChatId(),
server_time: Math.floor(Date.now() / 1e3),
serverTime: Math.floor(Date.now() / 1e3),
userAuthBean: {
verified: !0,
age: 18,
adult: !0
},
tasklist: [],
canUseGacha: !1,
fiveAttrLvMap: {},
userInfo: {
nickName: "调查员A",
avatar: "",
electricity: 10000,
electricity_time: 0,
powerBank: 0,
coffee: 5,
alarmClock: 5,
maxChatId: s.default.chapterMaxChatId() || "0",
itemList: [],
cosplays: [],
others: {},
others2: {},
login_day: 0,
login_isGetReward: 0,
login_lastTime: 0
}
});
return;
}
if ("getStoreDataV2" == e) {
n && n({
data: {
last_chat_record_id: 0
}
});
return;
}
if ("storageChat" == e) {
n && n({
lastChatId: 0
});
return;
}'''

OLD_EARLY = 'if (!n.data || !n.data.last_chat_record_id) return [ 3, 2 ];'
NEW_EARLY = '''if (!n.data || !n.data.last_chat_record_id) {
t.getSpecialStatus();
return [ 3, 2 ];
}'''

OLD_LAUNCH = 'var p = s.default.Platform.launchOption, g = p && p.query && (p.query.channel || p.query["?channel"]), m = p.query, _ = "0";'
NEW_LAUNCH = '''var p = s.default.Platform.launchOption || {
query: {},
scene: ""
}, g = p && p.query && (p.query.channel || p.query["?channel"]), m = p.query || {}, _ = "0";
p.scene = p.scene || "";'''

OLD_LOAD = '''e.prototype.load = function() {
var e = this;
if (0 != cc.sys.getNetworkType()) t(); else {'''

NEW_LOAD = '''e.prototype.load = function() {
if ("getUserInfoByAdditionalOrder" == this.method) {
this.handler.onResponseInfoSuccess({});
return;
}
if ("getAttrInfo" == this.method) {
this.handler.onResponseInfoSuccess({
fiveAttrInfos: [],
upgradeLv: 1
});
return;
}
if ("getRewardInStorage" == this.method) {
this.handler.onResponseInfoSuccess({
msgCode: 1,
rewards: [],
itemList: [],
items: [],
server_time: Math.floor(Date.now() / 1e3)
});
return;
}
if ("buyItemV2" == this.method || "buyItem" == this.method) {
this.handler.onResponseInfoSuccess({
retCode: 200,
msgCode: 1,
rewards: [],
itemList: [],
items: [],
server_time: Math.floor(Date.now() / 1e3)
});
return;
}
if ("costElectricityV2" == this.method) {
this.handler.onResponseInfoSuccess({
retCode: 200,
electricity: 10000,
electricity_time: Math.floor(Date.now() / 1e3)
});
return;
}
if (this.url && this.url.indexOf("happyelements.cn") >= 0) {
this.handler.onResponseInfoSuccess({
msgCode: 1,
compenList: [],
rewards: [],
itemList: [],
items: [],
tasklist: []
});
return;
}
var e = this;
if (0 != cc.sys.getNetworkType()) t(); else {'''

PATCHES = [
    ("getLoginSNS", OLD_SNS, NEW_SNS),
    ("getChannelNameSNS", OLD_CHANNEL, NEW_CHANNEL),
    ("sendMessage", OLD_SEND, NEW_SEND),
    ("chatStorage early return", OLD_EARLY, NEW_EARLY),
    ("launchOption", OLD_LAUNCH, NEW_LAUNCH),
    ("HttpRequest.load", OLD_LOAD, NEW_LOAD),
]


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/local_account_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()

    for name, old, new in PATCHES:
        n = text.count(old)
        if n != 1:
            sys.exit(f"patch {name}: expected 1 match, found {n} (source changed?)")
        text = text.replace(old, new)

    start = text.find("t.prototype.getSpecialStatus = function() {")
    end = text.find("t.prototype.getChatStorage = function() {", start)
    if start < 0 or end < 0:
        sys.exit("patch getSpecialStatus: method boundaries not found")
    new_special = '''t.prototype.getSpecialStatus = function() {
h.default.userInfo().setSpecialStatus({
specialStatusMap: {},
limitPackageInfos: {},
timePackageEnd: 0,
timePackageId: 0,
chapterFreeChargerCnt: 0,
autoAwareFreeCnt: 0,
inferenceFreeCnt: 0,
totalPayValue: 0
});
this.changeScene();
};
'''
    text = text[:start] + new_special + text[end:]

    open(out, "w", encoding="utf-8").write(text)
    print(f"local-account patched {src} -> {out}")


if __name__ == "__main__":
    main()
