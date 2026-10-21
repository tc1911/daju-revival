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
var __dajuNextExp = [ 50, 150, 200, 250, 400, 350, 400, 450, 500, 550, 1300, 1500, 1700, 1900, 2100, 2300, 2500, 2700, 2900, 3100, 5100, 5550, 6000, 6450, 6900, 7350, 7800, 8250, 8700, 9150, 13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000, 21000, 22000, 30000, 32500, 35000, 37500, 40000, 42500, 45000, 47500, 50000, 52500, 52500 ];
var __dajuAddExp = [ 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250, 250 ];
var __dajuMaxStage = { 1: 1883, 2: 3214, 3: 341, 4: 50, 5: 3368 };
var __dajuStageOf = function(t) {
var m = __dajuMaxStage[t] || 1;
var i = 0;
try {
i = Number(cc.sys.localStorage.getItem("daju_train_stage_" + t)) || 0;
} catch (e) {}
return i % m;
};
var __dajuTrain = {};
try {
var __dajuTrainRaw = cc.sys.localStorage.getItem("daju_train_attrs");
if (__dajuTrainRaw) {
var __dajuTrainObj = JSON.parse(__dajuTrainRaw);
if (__dajuTrainObj && "object" == typeof __dajuTrainObj) __dajuTrain = __dajuTrainObj;
}
} catch (e) {}
var __dajuSaveTrain = function() {
try {
cc.sys.localStorage.setItem("daju_train_attrs", JSON.stringify(__dajuTrain));
} catch (e) {}
};
var __dajuGetAttr = function(t) {
var a = __dajuTrain[t] || {};
var lv = Number(a.lv) || 1;
var exp = Number(a.exp) || 0;
return {
lv: lv,
exp: exp,
dayUseCnt: Number(a.dayUseCnt) || 0,
dayAddExp: 0,
dayBuyCnt: Number(a.dayBuyCnt) || 0,
clgTimes: __dajuStageOf(t),
redBagNum: 0,
redBagStartTime: 0,
nextExp: __dajuNextExp[lv] || 100,
premaxExp: __dajuNextExp[lv] || 100
};
};
var __dajuAttrs = { 1: __dajuGetAttr(1), 2: __dajuGetAttr(2), 3: __dajuGetAttr(3), 4: __dajuGetAttr(4), 5: __dajuGetAttr(5) };
if ("getUserInfoByAdditionalOrder" == this.method) {
this.handler.onResponseInfoSuccess({});
return;
}
if ("getAttrInfo" == this.method) {
for (var __ti = 1; __ti < 6; __ti++) __dajuAttrs[__ti].clgTimes = __dajuStageOf(__ti);
this.handler.onResponseInfoSuccess({
fiveAttrInfos: __dajuAttrs,
upgradeLv: 1
});
return;
}
if ("startLevel" == this.method) {
var __p = {};
try {
__p = JSON.parse(this.buildParams)[1][0] || {};
} catch (e) {}
var __t = Number(__p.type);
if (!__t) {
try {
var __m = /"type"\s*:\s*(\d+)/.exec(this.buildParams || "");
if (__m) __t = Number(__m[1]);
} catch (e) {}
}
var __max = __dajuMaxStage[__t] || 1;
var __i = __dajuStageOf(__t);
console.log("DAJU_TRAIN_START", __t, __i, __max, this.buildParams);
this.handler.onResponseInfoSuccess({
msgCode: 1,
stageIndex: __i,
stageList: [ 4 == __t ? __i : 10000001 + __i ]
});
return;
}
if ("passLevel" == this.method) {
var __pp = {};
try {
__pp = JSON.parse(this.buildParams)[1][0] || {};
} catch (e) {}
var __pt = Number(__pp.type);
if (!__pt) {
try {
var __pm = /"type"\s*:\s*(\d+)/.exec(this.buildParams || "");
if (__pm) __pt = Number(__pm[1]);
} catch (e) {}
}
var __pr = Number(__pp.result);
if (!__pr) {
try {
var __prm = /"result"\s*:\s*(\d+)/.exec(this.buildParams || "");
if (__prm) __pr = Number(__prm[1]);
} catch (e) {}
}
var __pa = __dajuGetAttr(__pt);
var __padd = 0;
var __prewards = [];
if (__pr >= 1) {
__padd = __dajuAddExp[__pa.lv] || 50;
__pa.exp = __pa.exp + __padd;
while (__pa.lv < 6 && __pa.exp >= __dajuNextExp[__pa.lv]) {
__pa.exp = __pa.exp - __dajuNextExp[__pa.lv];
__pa.lv = __pa.lv + 1;
}
__pa.nextExp = __dajuNextExp[__pa.lv] || 100;
__pa.premaxExp = __dajuNextExp[__pa.lv] || 100;
__pa.dayUseCnt = __pa.dayUseCnt + 1;
var __pkey = "daju_train_stage_" + __pt;
var __pmax = __dajuMaxStage[__pt] || 1;
var __pnow = __dajuStageOf(__pt);
try {
cc.sys.localStorage.setItem(__pkey, String((__pnow + 1) % __pmax));
} catch (e) {}
__pa.clgTimes = (__pnow + 1) % __pmax;
__dajuTrain[__pt] = {
lv: __pa.lv,
exp: __pa.exp,
dayUseCnt: __pa.dayUseCnt,
dayBuyCnt: __pa.dayBuyCnt
};
__dajuSaveTrain();
__prewards = [ {
itemId: 50001002,
num: 10000
}, {
itemId: 50001001,
num: 1000
} ];
}
var __ptime = Number(__pp.passTime) || 0;
console.log("DAJU_TRAIN_PASS", __pt, __pr, __padd, __pa.lv, __pa.exp, __ptime, this.buildParams);
this.handler.onResponseInfoSuccess({
msgCode: 1,
rewards: __prewards,
addExp: __padd,
attrInfoBean: __pa,
passTime: __ptime
});
return;
}
if ("getRank" == this.method) {
this.handler.onResponseInfoSuccess({
monthStartTime: Date.now() - 86400000,
monthEndTime: Date.now() + 86400000,
score: 0,
selfRank: 0,
rankInfos: [],
lastMonthRewards: [],
lastMonthRank: 0
});
return;
}
if ("getRedBag" == this.method) {
this.handler.onResponseInfoSuccess({
rewards: [],
attrInfoBean: __dajuGetAttr(1)
});
return;
}
if ("buyClgTimes" == this.method) {
var __bp2 = {};
try {
__bp2 = JSON.parse(this.buildParams)[1][0] || {};
} catch (e) {}
var __bt2 = Number(__bp2.type);
if (!__bt2) {
try {
var __bm2 = /"type"\s*:\s*(\d+)/.exec(this.buildParams || "");
if (__bm2) __bt2 = Number(__bm2[1]);
} catch (e) {}
}
var __ba2 = __dajuGetAttr(__bt2);
__ba2.dayBuyCnt = (__ba2.dayBuyCnt || 0) + 1;
__dajuTrain[__bt2] = {
lv: __ba2.lv,
exp: __ba2.exp,
dayUseCnt: __ba2.dayUseCnt,
dayBuyCnt: __ba2.dayBuyCnt
};
__dajuSaveTrain();
console.log("DAJU_TRAIN_BUY", __bt2, __ba2.dayBuyCnt, this.buildParams);
this.handler.onResponseInfoSuccess({
msgCode: 1,
attrInfoBean: __ba2
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

CONSUME_OLD = """t.prototype.consumeItemLocal = function(e, t) {
if ("50000002" == e) {
this._powerBank -= t;
this._powerBank = Math.max(this._powerBank, 0);
} else if ("50000003" == e) {
this._alarmClock -= t;
this._alarmClock = Math.max(this._alarmClock, 0);
} else if ("50000005" == e) {
this._coffee -= t;
this._coffee = Math.max(this._coffee, 0);
} else {
this._itemList[e].count -= t;
this._itemList[e].count = Math.max(this._itemList[e].count, 0);
}
c.default.EventManager.fire(l.EventItemRefresh.goodsChange);
c.default.EventManager.fire(l.EventName.refreshShop);
};"""

CONSUME_NEW = """t.prototype.consumeItemLocal = function(e, t) {
var id = Number(e);
if (50000002 == id) {
this._powerBank -= t;
this._powerBank = Math.max(this._powerBank, 0);
} else if (50000003 == id) {
this._alarmClock -= t;
this._alarmClock = Math.max(this._alarmClock, 0);
} else if (50000005 == id) {
this._coffee -= t;
this._coffee = Math.max(this._coffee, 0);
} else {
var found = null;
for (var k in this._itemList) {
var it = this._itemList[k];
if (it && Number(it.id) == id) {
found = it;
break;
}
}
if (found) found.count = Math.max(0, Number(found.count) - t);
else console.log("consumeItemLocal missing item", id, JSON.stringify(this._itemList));
}
c.default.EventManager.fire(l.EventItemRefresh.goodsChange);
c.default.EventManager.fire(l.EventName.refreshShop);
};"""

TICKET_CONSUME_OLD = """h.default.Instance.addBoughtExtraList(Number(n.serverId));
t.getChildByName("get_node").active = !0;
t.getChildByName("cost_node").active = !1;
p.default.Instance.dcUnlockExtra_101(n.serverId, "1", n.tickets);
a.default.userInfo().consumeItemLocal(a.ItemType.ticket, n.tickets);"""

TICKET_CONSUME_NEW = """h.default.Instance.addBoughtExtraList(Number(n.serverId));
try {
a.default.userInfo().consumeItemLocal(a.ItemType.ticket, n.tickets);
} catch (err) {
console.log("extra ticket consume failed", err);
}
t.getChildByName("get_node").active = !0;
t.getChildByName("cost_node").active = !1;
p.default.Instance.dcUnlockExtra_101(n.serverId, "1", n.tickets);"""

EXTRA_OLD = """t.prototype.setBoughtExtraList = function(e) {
this._boughtExtraList = e;
};
t.prototype.addBoughtExtraList = function(e) {
this._boughtExtraList.push(e);
};
t.prototype.isBoughtExtraList = function(e) {
return this._boughtExtraList.indexOf(e) >= 0;
};"""

EXTRA_NEW = """t.prototype._loadBoughtExtraList = function() {
if (this._boughtExtraLoaded) return;
this._boughtExtraLoaded = !0;
try {
var s = cc.sys.localStorage.getItem("daju_bought_extra_list");
if (s) {
var a = JSON.parse(s);
if (a && a.length) for (var i = 0; i < a.length; i++) {
var v = Number(a[i]);
if (this._boughtExtraList.indexOf(v) < 0) this._boughtExtraList.push(v);
}
}
} catch (e) {}
};
t.prototype._saveBoughtExtraList = function() {
try {
cc.sys.localStorage.setItem("daju_bought_extra_list", JSON.stringify(this._boughtExtraList));
} catch (e) {}
};
t.prototype.setBoughtExtraList = function(e) {
this._loadBoughtExtraList();
var a = Array.isArray(e) ? e : [];
for (var i = 0; i < a.length; i++) {
var v = Number(a[i]);
if (this._boughtExtraList.indexOf(v) < 0) this._boughtExtraList.push(v);
}
this._saveBoughtExtraList();
};
t.prototype.addBoughtExtraList = function(e) {
this._loadBoughtExtraList();
var v = Number(e);
if (this._boughtExtraList.indexOf(v) < 0) this._boughtExtraList.push(v);
this._saveBoughtExtraList();
};
t.prototype.isBoughtExtraList = function(e) {
this._loadBoughtExtraList();
return this._boughtExtraList.indexOf(Number(e)) >= 0;
};"""

END_VIEW_OLD = """this.end.getChildByName("label4_e").getComponent(cc.Label).string = "s";
}
};"""
END_VIEW_NEW = """this.end.getChildByName("label4_e").getComponent(cc.Label).string = "s";
}
var __dajuEnd = this.end;
if (1 == h.AttrType[this.gameType]) {
[ "label4", "pro4", "label4_e" ].forEach(function(n) {
var x = __dajuEnd.getChildByName(n);
if (x) x.active = !1;
});
} else {
[ "label3", "pro3", "label3_e", "label4", "pro4", "label4_e" ].forEach(function(n) {
var x = __dajuEnd.getChildByName(n);
if (x) x.active = !1;
});
}
};"""

PASS_TIME_OLD = """l.default.Http.request("passLevel", {
type: o,
result: t,
answers: e.answers,
operations: e.operations
}, function(r) {"""
PASS_TIME_NEW = """l.default.Http.request("passLevel", {
type: o,
result: t,
passTime: n.gameTime,
answers: e.answers,
operations: e.operations
}, function(r) {"""

STAGE_LABEL_OLD = """this.game.getChildByName("level").getComponent(cc.Label).string = m.default.strfmt("第{0}关", this.attriInfo.clgTimes + 1);"""
STAGE_LABEL_NEW = """var __dajuStageIdx = e && "number" == typeof e.stageIndex ? e.stageIndex : this.attriInfo.clgTimes;
this.game.getChildByName("level").getComponent(cc.Label).string = m.default.strfmt("第{0}关", __dajuStageIdx + 1);"""

NPC_FAVOR_OLD = """t.prototype.setNpcFavors = function(e) {
this._npcFavors = e;
};
t.prototype.getNpcFavor = function(e) {
var t = this._npcFavors[e];
return t ? t.itemCnt : 0;
};
t.prototype.addNpcFavor = function(e, t, n) {
var o = this._npcFavors[e];
if (o) {
o.itemCnt = o.itemCnt + t;
n && o.giftIdList.push(n);
} else {
var i = {
itemCnt: 0,
giftIdList: []
};
i.itemCnt = t;
n && (i.giftIdList = [ n ]);
this._npcFavors[e] = i;
}
};
t.prototype.getNpcGiftCnt = function(e) {
var t = this._npcFavors[e];
return t && t.giftIdList ? t.giftIdList.length : 0;
};
t.prototype.getNpcGiftItem = function(e, t) {
var n = this._npcFavors[e];
t = t || n.giftIdList.length;
return n && n.giftIdList && n.giftIdList[t - 1] ? n.giftIdList[t - 1] : 50000101;
};"""
NPC_FAVOR_NEW = """t.prototype._loadNpcFavors = function() {
if (this._npcFavorsLoaded) return;
this._npcFavorsLoaded = !0;
try {
var s = cc.sys.localStorage.getItem("daju_npc_favors");
if (s) {
var o = JSON.parse(s);
if (o && "object" == typeof o) {
this._npcFavors = o;
return;
}
}
} catch (e) {}
if (this._npcFavors instanceof Map) {
var m = {};
this._npcFavors.forEach(function(v, k) {
m[k] = v;
});
this._npcFavors = m;
}
};
t.prototype._saveNpcFavors = function() {
try {
cc.sys.localStorage.setItem("daju_npc_favors", JSON.stringify(this._npcFavors));
} catch (e) {}
};
t.prototype.setNpcFavors = function(e) {
this._npcFavors = e || {};
this._saveNpcFavors();
};
t.prototype.getNpcFavor = function(e) {
this._loadNpcFavors();
var t = this._npcFavors[e];
return t ? t.itemCnt : 0;
};
t.prototype.addNpcFavor = function(e, t, n) {
this._loadNpcFavors();
var o = this._npcFavors[e];
if (o) {
o.itemCnt = o.itemCnt + t;
n && o.giftIdList.push(n);
} else {
var i = {
itemCnt: 0,
giftIdList: []
};
i.itemCnt = t;
n && (i.giftIdList = [ n ]);
this._npcFavors[e] = i;
}
this._saveNpcFavors();
};
t.prototype.getNpcGiftCnt = function(e) {
this._loadNpcFavors();
var t = this._npcFavors[e];
return t && t.giftIdList ? t.giftIdList.length : 0;
};
t.prototype.getNpcGiftItem = function(e, t) {
this._loadNpcFavors();
var n = this._npcFavors[e];
if (!n || !n.giftIdList) return 50000101;
t = t || n.giftIdList.length;
return n.giftIdList[t - 1] ? n.giftIdList[t - 1] : 50000101;
};"""

CHAT_RED_OLD = """t.prototype.setRedEnvelopeList = function(e) {
this._redEnvelopeList = e;
};
t.prototype.addRedEnvelopeList = function(e) {
this._redEnvelopeList.push(e);
};
t.prototype.isGetRedEnvelope = function(e) {
return this._redEnvelopeList.indexOf(e) >= 0;
};
t.prototype.setChatEmotionStatus = function(e) {
this._chatEmotionStatus = e;
};
t.prototype.addChatEmotionStatus = function(e) {
this._chatEmotionStatus.push(e);
};
t.prototype.isChatEmotionStatus = function(e) {
return this._chatEmotionStatus.indexOf(e) >= 0;
};"""

CHAT_RED_NEW = """t.prototype._loadChatState = function() {
if (this.__dajuChatStateLoaded) return;
this.__dajuChatStateLoaded = !0;
var arr = function(k) {
try {
var v = cc.sys.localStorage.getItem(k);
if (!v) return null;
var a = JSON.parse(v);
return Array.isArray(a) ? a : null;
} catch (e) { return null; }
};
var a = arr("daju_red_envelope_list");
if (a) this._redEnvelopeList = a;
a = arr("daju_chat_emotion_status");
if (a) this._chatEmotionStatus = a;
a = arr("daju_gossip_list");
if (a) this._gossipList = a;
a = arr("daju_intelligence_list");
if (a) this._intelligenceList = a;
a = arr("daju_watch_ad_list");
if (a) this._watchAdList = a;
a = arr("daju_red_envelope_ad_list");
if (a) this._redEnvelopeAdList = a;
try {
var rt = cc.sys.localStorage.getItem("daju_npc_rest_time");
if (rt != null && rt != "") this._npcRestTime = Number(rt) || 0;
var ri = cc.sys.localStorage.getItem("daju_npc_rest_id");
if (ri != null && ri != "") this._npcRestId = Number(ri) || 0;
} catch (e) {}
};
t.prototype._saveChatState = function() {
try {
cc.sys.localStorage.setItem("daju_red_envelope_list", JSON.stringify(this._redEnvelopeList));
cc.sys.localStorage.setItem("daju_chat_emotion_status", JSON.stringify(this._chatEmotionStatus));
cc.sys.localStorage.setItem("daju_gossip_list", JSON.stringify(this._gossipList));
cc.sys.localStorage.setItem("daju_intelligence_list", JSON.stringify(this._intelligenceList));
cc.sys.localStorage.setItem("daju_watch_ad_list", JSON.stringify(this._watchAdList));
cc.sys.localStorage.setItem("daju_red_envelope_ad_list", JSON.stringify(this._redEnvelopeAdList));
cc.sys.localStorage.setItem("daju_npc_rest_time", String(this._npcRestTime || 0));
cc.sys.localStorage.setItem("daju_npc_rest_id", String(this._npcRestId || 0));
} catch (e) {}
};
t.prototype.setRedEnvelopeList = function(e) {
this._loadChatState();
this._redEnvelopeList = e || [];
this._saveChatState();
};
t.prototype.addRedEnvelopeList = function(e) {
this._loadChatState();
this._redEnvelopeList.push(e);
this._saveChatState();
};
t.prototype.isGetRedEnvelope = function(e) {
this._loadChatState();
return this._redEnvelopeList.indexOf(e) >= 0;
};
t.prototype.setChatEmotionStatus = function(e) {
this._loadChatState();
this._chatEmotionStatus = e || [];
this._saveChatState();
};
t.prototype.addChatEmotionStatus = function(e) {
this._loadChatState();
this._chatEmotionStatus.push(e);
this._saveChatState();
};
t.prototype.isChatEmotionStatus = function(e) {
this._loadChatState();
return this._chatEmotionStatus.indexOf(e) >= 0;
};"""

CHAT_REST_OLD = """t.prototype.setNpcRestTime = function(e) {
this._npcRestTime = e;
};
t.prototype.npcRestTime = function() {
return this._npcRestTime;
};
t.prototype.setNpcRestId = function(e) {
this._npcRestId = e;
};
t.prototype.npcRestId = function() {
return this._npcRestId;
};"""

CHAT_REST_NEW = """t.prototype.setNpcRestTime = function(e) {
this._loadChatState();
this._npcRestTime = Number(e) || 0;
this._saveChatState();
};
t.prototype.npcRestTime = function() {
this._loadChatState();
return this._npcRestTime;
};
t.prototype.setNpcRestId = function(e) {
this._loadChatState();
this._npcRestId = Number(e) || 0;
this._saveChatState();
};
t.prototype.npcRestId = function() {
this._loadChatState();
return this._npcRestId;
};"""

CHAT_GOSSIP_OLD = """t.prototype.setBuyGossipList = function(e) {
this._gossipList = e;
};
t.prototype.addBuyGossipId = function(e) {
this._gossipList.push(e);
};
t.prototype.isBuyGossipId = function(e) {
return !!this._gossipList && this._gossipList.indexOf(e) >= 0;
};"""

CHAT_GOSSIP_NEW = """t.prototype.setBuyGossipList = function(e) {
this._loadChatState();
this._gossipList = e || [];
this._saveChatState();
};
t.prototype.addBuyGossipId = function(e) {
this._loadChatState();
this._gossipList.push(e);
this._saveChatState();
};
t.prototype.isBuyGossipId = function(e) {
this._loadChatState();
return !!this._gossipList && this._gossipList.indexOf(e) >= 0;
};"""

CHAT_INTEL_OLD = """t.prototype.setIntelligenceList = function(e) {
e && (this._intelligenceList = e);
};
t.prototype.addIntelligenceId = function(e) {
this._intelligenceList.push(e);
};
t.prototype.isBuyIntelligence = function(e) {
return !!this._intelligenceList && this._intelligenceList.indexOf(e) >= 0;
};"""

CHAT_INTEL_NEW = """t.prototype.setIntelligenceList = function(e) {
this._loadChatState();
if (e) this._intelligenceList = e;
this._saveChatState();
};
t.prototype.addIntelligenceId = function(e) {
this._loadChatState();
this._intelligenceList.push(e);
this._saveChatState();
};
t.prototype.isBuyIntelligence = function(e) {
this._loadChatState();
return !!this._intelligenceList && this._intelligenceList.indexOf(e) >= 0;
};"""

CHAT_AD_OLD = """t.prototype.setWatchAdList = function(e) {
e && (this._watchAdList = e);
};
t.prototype.addWatchAd = function(e) {
this._watchAdList.push(e);
};
t.prototype.isWatchAd = function(e) {
return !!this._watchAdList && this._watchAdList.indexOf(e) >= 0;
};"""

CHAT_AD_NEW = """t.prototype.setWatchAdList = function(e) {
this._loadChatState();
if (e) this._watchAdList = e;
this._saveChatState();
};
t.prototype.addWatchAd = function(e) {
this._loadChatState();
this._watchAdList.push(e);
this._saveChatState();
};
t.prototype.isWatchAd = function(e) {
this._loadChatState();
return !!this._watchAdList && this._watchAdList.indexOf(e) >= 0;
};"""

CHAT_REDAD_OLD = """t.prototype.setRedEnvelopAdList = function(e) {
e && (this._redEnvelopeAdList = e);
};
t.prototype.addRedEnvelopAd = function(e) {
this._redEnvelopeAdList.push(e);
};
t.prototype.isRedEnvelopeAd = function(e) {
return !!this._redEnvelopeAdList && this._redEnvelopeAdList.indexOf(e) >= 0;
};"""

CHAT_REDAD_NEW = """t.prototype.setRedEnvelopAdList = function(e) {
this._loadChatState();
if (e) this._redEnvelopeAdList = e;
this._saveChatState();
};
t.prototype.addRedEnvelopAd = function(e) {
this._loadChatState();
this._redEnvelopeAdList.push(e);
this._saveChatState();
};
t.prototype.isRedEnvelopeAd = function(e) {
this._loadChatState();
return !!this._redEnvelopeAdList && this._redEnvelopeAdList.indexOf(e) >= 0;
};"""

PATCHES = [
    ("getLoginSNS", OLD_SNS, NEW_SNS),
    ("getChannelNameSNS", OLD_CHANNEL, NEW_CHANNEL),
    ("sendMessage", OLD_SEND, NEW_SEND),
    ("training pass time", PASS_TIME_OLD, PASS_TIME_NEW),
    ("training end stats", END_VIEW_OLD, END_VIEW_NEW),
    ("training stage label", STAGE_LABEL_OLD, STAGE_LABEL_NEW),
    ("chatStorage red/emotion persistence", CHAT_RED_OLD, CHAT_RED_NEW),
    ("chatStorage rest persistence", CHAT_REST_OLD, CHAT_REST_NEW),
    ("chatStorage gossip persistence", CHAT_GOSSIP_OLD, CHAT_GOSSIP_NEW),
    ("chatStorage intelligence persistence", CHAT_INTEL_OLD, CHAT_INTEL_NEW),
    ("chatStorage watch ad persistence", CHAT_AD_OLD, CHAT_AD_NEW),
    ("chatStorage red ad persistence", CHAT_REDAD_OLD, CHAT_REDAD_NEW),
    ("chatStorage npc favors persistence", NPC_FAVOR_OLD, NPC_FAVOR_NEW),
    ("chatStorage early return", OLD_EARLY, NEW_EARLY),
    ("launchOption", OLD_LAUNCH, NEW_LAUNCH),
    ("HttpRequest.load", OLD_LOAD, NEW_LOAD),
    ("chatStorage boughtExtraList", EXTRA_OLD, EXTRA_NEW),
    ("UserInfo.consumeItemLocal", CONSUME_OLD, CONSUME_NEW),
    ("hidden story ticket consume", TICKET_CONSUME_OLD, TICKET_CONSUME_NEW),
]



SAVE_API_JS = r"""
(function() {
var KEY = "daju_save_v1";
var BACKUP = "daju_save_v1_backup";
var KNOWN = [
"daju_bag_items",
"daju_npc_favors",
"daju_train_attrs",
"daju_shop_daily",
"daju_bought_extra_list",
"daju_daily_sign_date",
"daju_profile_name",
"daju_profile_head",
"daju_red_envelope_list",
"daju_chat_emotion_status",
"daju_gossip_list",
"daju_intelligence_list",
"daju_watch_ad_list",
"daju_red_envelope_ad_list",
"daju_npc_rest_time",
"daju_npc_rest_id"
];
var rawLS = null, rawGet = null, rawSet = null, rawRemove = null;
try {
rawLS = cc.sys.localStorage;
rawGet = rawLS.getItem.bind(rawLS);
rawSet = rawLS.setItem.bind(rawLS);
rawRemove = rawLS.removeItem ? rawLS.removeItem.bind(rawLS) : null;
} catch (e) {}
function rg(k) {
try {
if (rawGet) return rawGet(k);
return cc.sys.localStorage.getItem(k);
} catch (e) { return null; }
}
function rs(k, v) {
try {
if (rawSet) rawSet(k, v);
else cc.sys.localStorage.setItem(k, v);
} catch (e) {}
}
function rr(k) {
try {
if (rawRemove) rawRemove(k);
else cc.sys.localStorage.removeItem(k);
} catch (e) {}
}
var state = null;
function persist() {
if (!state) return;
try { rs(KEY, JSON.stringify(state)); } catch (e) {}
}
function migrate() {
var data = {};
for (var i = 0; i < KNOWN.length; i++) {
var v = rg(KNOWN[i]);
if (v !== null && v !== undefined) data[KNOWN[i]] = String(v);
}
for (var t = 1; t <= 5; t++) {
var k = "daju_train_stage_" + t;
var v2 = rg(k);
if (v2 !== null && v2 !== undefined) data[k] = String(v2);
}
var s = { version: 1, savedAt: Date.now(), data: data };
try { rs(BACKUP, JSON.stringify(s)); } catch (e) {}
try { rs(KEY, JSON.stringify(s)); } catch (e) {}
return s;
}
function load() {
if (state) return state;
var raw = rg(KEY);
if (raw) {
try {
var s = JSON.parse(raw);
if (s && s.version === 1 && s.data && typeof s.data === "object") {
state = s;
return state;
}
} catch (e) {}
}
state = migrate();
return state;
}
function managed(k) {
return typeof k === "string" && k.indexOf("daju_") === 0 && k.indexOf("daju_save_v1") !== 0;
}
function get(k, d) {
var s = load();
var raw = rg(k);
if (Object.prototype.hasOwnProperty.call(s.data, k)) {
if (raw !== null && raw !== undefined && String(raw) !== String(s.data[k])) {
s.data[k] = String(raw);
s.savedAt = Date.now();
persist();
}
return s.data[k];
}
if (raw !== null && raw !== undefined) {
s.data[k] = String(raw);
s.savedAt = Date.now();
persist();
return s.data[k];
}
return d;
}
function set(k, v) {
var s = load();
var sv = String(v);
rs(k, sv);
s.data[k] = sv;
s.savedAt = Date.now();
persist();
}
function remove(k) {
var s = load();
rr(k);
try { delete s.data[k]; } catch (e) {}
s.savedAt = Date.now();
persist();
}
window.__dajuSaveGet = get;
window.__dajuSaveSet = set;
window.__dajuSaveRemove = remove;
window.__dajuSaveLoad = load;
window.__dajuSaveReset = function() { state = null; };
try {
if (rawLS) {
rawLS.getItem = function(k) { if (managed(k)) return get(k, null); return rawGet(k); };
rawLS.setItem = function(k, v) { if (managed(k)) { set(k, v); return; } rawSet(k, v); };
rawLS.removeItem = function(k) { if (managed(k)) { remove(k); return; } if (rawRemove) rawRemove(k); };
}
} catch (e) {}
try { load(); } catch (e) {}
})();
"""


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
    text = text + SAVE_API_JS

    open(out, "w", encoding="utf-8").write(text)
    print(f"local-account patched {src} -> {out}")


if __name__ == "__main__":
    main()
