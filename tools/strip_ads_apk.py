#!/usr/bin/env python3
"""移除广告 SDK 的 manifest 组件/权限和 native 库，并重新签名。

用法: KS_PASS=... tools/strip_ads_apk.py <input.apk> <output.apk>
依赖: apktool / zipalign / apksigner / java
"""
import os
import re
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "work/tmp/ad_strip"
FRAME = ROOT / "work/tmp/apktool_framework"
KS = Path(os.environ.get("KS", ROOT / "work/keystore/daju.jks"))
ALIAS = os.environ.get("KS_ALIAS", "daju")
PASS = os.environ.get("KS_PASS", "")

PERMS = [
    "android.permission.READ_PHONE_STATE",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.ACCESS_WIFI_STATE",
    "android.permission.CHANGE_WIFI_STATE",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.FOREGROUND_SERVICE",
    "android.permission.BIND_JOB_SERVICE",
    "com.asus.msa.SupplementaryDID.ACCESS",
    "com.happyelements.xstorycncatdetective.permission.KW_SDK_BROADCAST",
]
AD_NAMES = [
    "com.kwad.", "com.bytedance.sdk.openadsdk", "com.bytedance.embedapplog",
    "com.bytedance.tea.crash", "com.qq.e.", "com.mintegral.", "com.pgl.",
    "com.anythink.", "com.ss.android.downloadlib",
    "org.cocos2dx.javascript.PremissionSplashActivity",
    "com.wind.sdk.", "com.wind.devicehelper", "com.bun.miitmdid",
    "com.asus.msa", "com.ta.utdid2",
]
LIBS = {
    "libnms.so", "libsgcore.so", "libtobEmbedEncrypt.so",
    "libbuffer_pg.so", "libfile_lock_pg.so",
    "lib39285EFA.so",
}


def run(cmd):
    print("$", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], check=True)


def strip_manifest(path: Path) -> None:
    A = "{http://schemas.android.com/apk/res/android}"
    ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
    tree = ET.parse(path)
    root = tree.getroot()
    for child in list(root):
        tag = child.tag.split("}")[-1]
        name = child.get(A + "name", "")
        if tag == "uses-permission" and name in PERMS:
            root.remove(child)
        elif tag == "permission" and "KW_SDK" in name:
            root.remove(child)

    app = root.find("application")
    if app is None:
        raise SystemExit("manifest has no application")
    app_activity = None
    for child in list(app):
        tag = child.tag.split("}")[-1]
        if tag not in ("activity", "activity-alias", "service", "receiver", "provider"):
            continue
        name = child.get(A + "name", "") or child.get(A + "authorities", "")
        if name.endswith(".AppActivity"):
            app_activity = child
        if any(n in name for n in AD_NAMES):
            app.remove(child)

    # 启动器原来在权限引导页上；删掉引导页后必须把 MAIN/LAUNCHER 挪到 AppActivity。
    if app_activity is None:
        raise SystemExit("AppActivity missing from manifest")
    app_activity.set(A + "exported", "true")
    has_main = False
    for f in app_activity.findall("intent-filter"):
        for a in f.findall("action"):
            if a.get(A + "name") == "android.intent.action.MAIN":
                has_main = True
    if not has_main:
        f = ET.SubElement(app_activity, "intent-filter")
        ET.SubElement(f, "action", {A + "name": "android.intent.action.MAIN"})
        ET.SubElement(f, "category", {A + "name": "android.intent.category.LAUNCHER"})
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("usage: strip_ads_apk.py <input.apk> <output.apk>")
    if not PASS:
        sys.exit("KS_PASS required")
    src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if not src.is_file():
        sys.exit(f"missing input: {src}")
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.parent.mkdir(parents=True, exist_ok=True)
    FRAME.mkdir(parents=True, exist_ok=True)

    run(["apktool", "d", "-f", "-s", "-p", FRAME, "-o", TMP, src])
    strip_manifest(TMP / "AndroidManifest.xml")
    for lib in TMP.glob("lib/*/*.so"):
        if lib.name in LIBS:
            print("remove", lib.relative_to(TMP))
            lib.unlink()

    built = TMP.parent / "ad_strip.built.apk"
    raw = TMP.parent / "ad_strip.unsigned.apk"
    aligned = TMP.parent / "ad_strip.aligned.apk"
    run(["apktool", "b", "-p", FRAME, TMP, "-o", built])
    # 只用 apktool 重编出的 AndroidManifest.xml，其他条目从原 APK 原样搬运，
    # 保留原有压缩方式/大小；只删广告 so。
    with zipfile.ZipFile(built) as zb:
        manifest = zb.read("AndroidManifest.xml")
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(raw, "w") as zout:
        for info in zin.infolist():
            name = info.filename
            if name == "AndroidManifest.xml":
                continue
            if name.upper().startswith("META-INF/") and name.upper().endswith((".SF", ".RSA", ".DSA", ".MF", ".EC")):
                continue
            if name.startswith("lib/") and Path(name).name in LIBS:
                continue
            data = zin.read(name)
            new = zipfile.ZipInfo(name, date_time=info.date_time)
            new.compress_type = info.compress_type
            new.external_attr = info.external_attr
            new.internal_attr = info.internal_attr
            new.create_system = info.create_system
            new.flag_bits = info.flag_bits & ~0x08
            zout.writestr(new, data)
        zi = zipfile.ZipInfo("AndroidManifest.xml", date_time=(1980, 1, 1, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        zout.writestr(zi, manifest)
    run(["zipalign", "-f", "-p", "4", raw, aligned])
    run([
        "apksigner", "sign", "--ks", KS, "--ks-key-alias", ALIAS,
        "--ks-pass", f"pass:{PASS}", "--key-pass", f"pass:{PASS}",
        "--v1-signing-enabled", "true", "--v2-signing-enabled", "true",
        "--out", out, aligned,
    ])
    run(["apksigner", "verify", "--verbose", out])
    print(f"ads stripped: {out} ({out.stat().st_size} B)")


if __name__ == "__main__":
    main()
