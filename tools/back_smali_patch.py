#!/usr/bin/env python3
"""修改官方 AppActivity 的返回键处理：转发给 JS window.onAndroidBack，而不是直接退出。

用法：tools/back_smali_patch.py <official_full/smali_classes2>
"""
import os
import sys

BRIDGE = '''.class public Lorg/cocos2dx/javascript/AndroidBackBridge;
.super Ljava/lang/Object;
.source "AndroidBackBridge.java"

.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static onBack()V
    .locals 1

    new-instance v0, Lorg/cocos2dx/javascript/AndroidBackBridge$1;

    invoke-direct {v0}, Lorg/cocos2dx/javascript/AndroidBackBridge$1;-><init>()V

    invoke-static {v0}, Lorg/cocos2dx/lib/Cocos2dxHelper;->runOnGLThread(Ljava/lang/Runnable;)V

    return-void
.end method
'''

BRIDGE1 = '''.class Lorg/cocos2dx/javascript/AndroidBackBridge$1;
.super Ljava/lang/Object;
.source "AndroidBackBridge.java"

.implements Ljava/lang/Runnable;

.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public run()V
    .locals 1

    const-string v0, "window.onAndroidBack && window.onAndroidBack()"

    invoke-static {v0}, Lorg/cocos2dx/lib/Cocos2dxJavascriptJavaBridge;->evalString(Ljava/lang/String;)I

    return-void
.end method
'''



def replace_method(text, signature, replacement):
    start = text.find(signature)
    if start < 0:
        return text
    end = text.find(".end method", start)
    if end < 0:
        raise SystemExit(f"method end not found: {signature}")
    end += len(".end method")
    return text[:start] + replacement + text[end:]


AD_DISABLE = {
    ".method private premissionDeal()Z": """.method private premissionDeal()Z
    .locals 1

    const/4 v0, 0x0

    return v0
.end method""",
    ".method public static initAD()V": """.method public static initAD()V
    .locals 0

    return-void
.end method""",
    ".method private initADs()V": """.method private initADs()V
    .locals 0

    return-void
.end method""",
}

def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: tools/back_smali_patch.py <smali_classes2>")
    root = sys.argv[1]
    app = os.path.join(root, "org/cocos2dx/javascript/AppActivity.smali")
    text = open(app, encoding="utf-8").read()

    old_exit = "invoke-static {}, Lcom/happyelements/hei/common/SdkClient;->exit()V"
    new_back = "invoke-static {}, Lorg/cocos2dx/javascript/AndroidBackBridge;->onBack()V"
    if text.count(old_exit) == 1:
        text = text.replace(old_exit, new_back)
    elif text.count(new_back) < 1:
        sys.exit(f"AppActivity SdkClient.exit: unexpected state")

    old_super = "invoke-super {p0}, Lorg/cocos2dx/javascript/HeSDKActivity;->onBackPressed()V"
    if text.count(old_super) == 1:
        text = text.replace(old_super, new_back)
    elif text.count(new_back) < 1:
        sys.exit(f"AppActivity onBackPressed super: unexpected state")

    for sig, repl in AD_DISABLE.items():
        text = replace_method(text, sig, repl)

    # offlined 后 GspDcAgent 可能未初始化；skip setConsent 防 NPE。
    consent = """const/4 v0, 0x1

    .line 199
    invoke-static {v0}, Lcom/happyelements/hei/common/SdkClient;->setConsent(Z)V"""
    if consent in text:
        text = text.replace(consent, """const/4 v0, 0x1

    .line 199
    nop""", 1)

    open(app, "w", encoding="utf-8").write(text)

    # 退出确认回调原本会再调一次 onBackPressed()；返回键已改为转发 JS，
    # 继续调会重新弹 ExitGameDialog，形成“点确定反复弹窗”。
    # 这里改成直接 finish()。
    app3_path = os.path.join(root, "org/cocos2dx/javascript/AppActivity$3.smali")
    app3 = open(app3_path, encoding="utf-8").read()
    old_exit_back = "invoke-virtual {p1}, Lorg/cocos2dx/javascript/AppActivity;->onBackPressed()V"
    new_finish = "invoke-virtual {p1}, Lorg/cocos2dx/javascript/AppActivity;->finish()V"
    if app3.count(old_exit_back) == 1:
        app3 = app3.replace(old_exit_back, new_finish)
        open(app3_path, "w", encoding="utf-8").write(app3)
    elif app3.count(new_finish) != 1:
        sys.exit(f"AppActivity$3 exit callback: unexpected state")

    open(os.path.join(root, "org/cocos2dx/javascript/AndroidBackBridge.smali"), "w", encoding="utf-8").write(BRIDGE)
    open(os.path.join(root, "org/cocos2dx/javascript/AndroidBackBridge$1.smali"), "w", encoding="utf-8").write(BRIDGE1)
    print(f"back smali patched: {app}")


if __name__ == "__main__":
    main()
