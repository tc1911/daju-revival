#!/usr/bin/env python3
"""注入 JS 的 Android 返回键处理：优先返回上一页，主界面才退出。

配合 tools/back_smali_patch.py：native 返回键会 evalString 到 window.onAndroidBack。
"""
import sys

JS = '''
window.onAndroidBack = function() {
    try {
        var app = window.__require("App").default;
        var ui = app && app.UIManager;
        if (!ui || ui.isAnimation) return;
        var cur = ui.getTopUI();
        var main = "prefabs/ui/gameui/MainUI";
        if (cur && cur !== main) {
            ui.popUI(cur, true);
            return;
        }
        if (cur === main) {
            var mainUI = ui.getUI(main);
            if (mainUI && mainUI.preBtnName && mainUI.preBtnName !== "chat") {
                mainUI.clickButtonHandler("chat");
                return;
            }
        }
        jsb.reflection.callStaticMethod("com/happyelements/hei/common/SdkClient", "exit", "()V");
    } catch (e) {
        try {
            jsb.reflection.callStaticMethod("com/happyelements/hei/common/SdkClient", "exit", "()V");
        } catch (e2) {
        }
    }
};
'''


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: tools/back_button_patch.py <decrypted-project.js> <output.js>")
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()
    if "window.onAndroidBack" in text:
        sys.exit("window.onAndroidBack already present")
    text = text + JS
    open(out, "w", encoding="utf-8").write(text)
    print(f"back button JS patched: {src} -> {out}")


if __name__ == "__main__":
    main()
