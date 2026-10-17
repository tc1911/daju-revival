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


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: tools/back_smali_patch.py <smali_classes2>")
    root = sys.argv[1]
    app = os.path.join(root, "org/cocos2dx/javascript/AppActivity.smali")
    text = open(app, encoding="utf-8").read()

    old_exit = "invoke-static {}, Lcom/happyelements/hei/common/SdkClient;->exit()V"
    new_back = "invoke-static {}, Lorg/cocos2dx/javascript/AndroidBackBridge;->onBack()V"
    if text.count(old_exit) != 1:
        sys.exit(f"AppActivity SdkClient.exit: expected 1, found {text.count(old_exit)}")
    text = text.replace(old_exit, new_back)

    old_super = "invoke-super {p0}, Lorg/cocos2dx/javascript/HeSDKActivity;->onBackPressed()V"
    if text.count(old_super) != 1:
        sys.exit(f"AppActivity onBackPressed super: expected 1, found {text.count(old_super)}")
    text = text.replace(old_super, new_back)

    open(app, "w", encoding="utf-8").write(text)
    open(os.path.join(root, "org/cocos2dx/javascript/AndroidBackBridge.smali"), "w", encoding="utf-8").write(BRIDGE)
    open(os.path.join(root, "org/cocos2dx/javascript/AndroidBackBridge$1.smali"), "w", encoding="utf-8").write(BRIDGE1)
    print(f"back smali patched: {app}")


if __name__ == "__main__":
    main()
