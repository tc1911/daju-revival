#!/usr/bin/env python3
"""对解密后的 project.js 打「离线启动」补丁。

作用：
  1. 跳过 Launcher.init 里的 login_getClientConfig 网络请求（服务器已停，否则要等 102s 超时）。
  2. 跳过 HotUpdate 的 checkUpdate 网络检查，直接置 hotUpdateStatus=1，让 Launcher 进入 gameInit。

不做：不伪造登录/getUser/getServerData 协议响应（那部分晚点处理）。

用法：tools/offline_skip_launcher.py <decrypted-project.js> <output.js>
"""
import sys

OLD_LOGIN = '''new l.default("login_getClientConfig", {
pf: s.default.userInfo().platform,
gid: c.default.getGid(),
bigVersion: s.default.userInfo().versionName
}, n).load();'''

NEW_LOGIN = '''console.log("!!!!HotUpdate skip login_getClientConfig (offline)");
e.initCb("6.12");'''

OLD_HOT = '''t.prototype.initCb = function(e) {
console.log("!!!!HotUpdate initCb newVersion=" + e);
var t = this;
if (cc.sys.isNative) {
t.loadingLabel.active = !1;'''

NEW_HOT = '''t.prototype.initCb = function(e) {
console.log("!!!!HotUpdate initCb newVersion=" + e);
var t = this;
if (cc.sys.isNative) {
s.default.clientAssetsVersion = "6.12";
s.default.hotUpdateStatus = 1;
console.log("!!!!HotUpdate skipped (offline)");
return;
t.loadingLabel.active = !1;'''


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/offline_skip_launcher.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        text = f.read()

    for name, old in (("login_getClientConfig", OLD_LOGIN), ("initCb", OLD_HOT)):
        n = text.count(old)
        if n != 1:
            sys.exit(f"patch {name}: expected 1 match, found {n} (source changed?)")

    text = text.replace(OLD_LOGIN, NEW_LOGIN).replace(OLD_HOT, NEW_HOT)
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"patched {src} -> {out}")


if __name__ == "__main__":
    main()
