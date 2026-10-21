#!/usr/bin/env python3
"""按 tools/pipeline.toml 构建 APK。

映射表是唯一事实来源：阶段、补丁顺序、资源步骤、原生步骤都写死在表里，
本脚本只负责解析依赖、执行补丁、生成 overlay、调用 repack。

用法：
  tools/build.py list
  tools/build.py [stage] [--out PATH] [--dry-run]
  tools/build.py --force             # 重跑依赖链
  tools/build.py daily --no-deps     # 只用现有 base，不重跑上游
"""
from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
import sys

try:
    import tomllib
except ModuleNotFoundError as exc:
    raise SystemExit("错误: 需要 Python 3.11+（标准库 tomllib）") from exc

import zipfile
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "tools" / "pipeline.toml"
VERSION_FILE = ROOT / "version.toml"


def project_version() -> tuple[str, int, str]:
    try:
        with open(VERSION_FILE, "rb") as f:
            v = tomllib.load(f)["version"]
        game = str(v.get("game", "6.12"))
        code = int(v["main"]) * 100 + int(v["revision"])
        channel = str(v.get("channel", "release"))
        return game, code, channel
    except Exception:
        return "6.12", 200, "release"


def final_artifact_name() -> str:
    _, code, channel = project_version()
    return f"daju-all-{channel}-{code}.apk"



def die(msg: str) -> NoReturn:
    raise SystemExit(f"错误: {msg}")


def load_table() -> dict:
    if not TABLE.is_file():
        die(f"找不到映射表 {TABLE}")
    with TABLE.open("rb") as f:
        cfg = tomllib.load(f)
    if cfg.get("version") != 1:
        die(f"不支持的映射表版本: {cfg.get('version')!r}")
    return cfg


def validate_table(cfg: dict) -> None:
    stages = cfg.get("stages")
    if not stages:
        die("映射表没有 [[stages]]")
    ids: set[str] = set()
    for s in stages:
        sid = s.get("id")
        if not sid:
            die("stage 缺少 id")
        if sid in ids:
            die(f"stage id 重复: {sid}")
        ids.add(sid)
    default = cfg.get("default_stage")
    if default and default not in ids:
        die(f"default_stage 不存在: {default}")
    patches = cfg.get("patches", {})
    assets = cfg.get("assets", {})
    native = cfg.get("native", {})
    for s in stages:
        sid = s["id"]
        base = s.get("base")
        if base != "merged" and base not in ids:
            die(f"stage {sid} 的 base 不存在: {base}")
        for pid in s.get("patches", []):
            if pid not in patches:
                die(f"stage {sid} 引用了未知 patch: {pid}")
        for aid in s.get("assets", []):
            if aid not in assets:
                die(f"stage {sid} 引用了未知 asset: {aid}")
        if s.get("main_js") and "main_js" not in cfg:
            die(f"stage {sid} 需要 [main_js]，但映射表没有")
        if s.get("native") and s["native"] not in native:
            die(f"stage {sid} 引用了未知 native: {s['native']}")
        if s.get("dex") and s["dex"] not in native:
            die(f"stage {sid} 引用了未知 dex: {s['dex']}")
        if not s.get("apk_out"):
            die(f"stage {sid} 缺少 apk_out")


def path_of(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def run(cmd: list[object], dry: bool) -> None:
    cmd = [str(x) for x in cmd]
    print("  $ " + " ".join(shlex.quote(x) for x in cmd), flush=True)
    if dry:
        return
    subprocess.run(cmd, cwd=ROOT, check=True)


def run_py(path: str | Path, *args: object, dry: bool) -> None:
    run([sys.executable, path_of(path), *args], dry)


def run_bash(path: str | Path, *args: object, dry: bool) -> None:
    run(["bash", path_of(path), *args], dry)


def require(path: Path, what: str) -> None:
    if not path.is_file():
        die(f"缺少{what}: {path}")


def stage_map(cfg: dict) -> dict[str, dict]:
    return {s["id"]: s for s in cfg["stages"]}


def stage_js_out(cfg: dict, stage: dict) -> Path | None:
    if stage.get("js_out"):
        return path_of(stage["js_out"])
    patches = stage.get("patches", [])
    if patches:
        return path_of(cfg["patches"][patches[-1]]["out"])
    return None


def stage_apk_out(stage: dict) -> Path:
    return path_of(stage["apk_out"])


def show_list(cfg: dict) -> None:
    stages = cfg["stages"]
    print(f"{'STAGE':16} {'BASE':16} {'PATCHES':48} OUTPUT")
    for s in stages:
        patches = " -> ".join(s.get("patches", [])) or "-"
        extra = []
        if s.get("assets"):
            extra.append("assets=" + ",".join(s["assets"]))
        if s.get("main_js"):
            extra.append("main_js")
        if s.get("native"):
            extra.append("native=" + s["native"])
        if s.get("dex"):
            extra.append("dex=" + s["dex"])
        suffix = ""
        if extra:
            suffix = "  [" + " ".join(extra) + "]"
        legacy = " (legacy)" if s.get("legacy") else ""
        print(f"{s['id']:16} {s['base']:16} {patches:48} {s['apk_out']}{legacy}{suffix}")


def compat_ready(cfg: dict) -> bool:
    merge = cfg.get("merge", {})
    compat_dir = path_of(merge.get("compat_dir", "compat/arm64-v8a"))
    manifest = path_of(merge.get("compat_manifest", "compat/libs.txt"))
    if not compat_dir.is_dir() or not manifest.is_file():
        return False
    names = [
        line.strip()
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return bool(names) and all((compat_dir / name).is_file() for name in names)


def ensure_merged(cfg: dict, dry: bool, no_deps: bool) -> Path:
    paths = cfg["paths"]
    official = path_of(paths["official_apk"])
    oppo = path_of(paths["oppo_apk"])
    merged = path_of(paths["merged_apk"])
    if no_deps:
        if not merged.is_file():
            die(f"缺少 merged APK {merged}，且指定了 --no-deps")
        print(f"== 跳过 merge（--no-deps）: {merged}")
        return merged
    require(official, "官方底包")
    if not compat_ready(cfg):
        require(oppo, "OPPO 包")
        print("== 合并官方底包 + OPPO arm64 库")
    else:
        print("== 合并官方底包 + compat/arm64-v8a 库")
    run_bash(cfg["merge"]["script"], official, oppo, merged, dry=dry)
    return merged


def build_stage(
    cfg: dict,
    stage_id: str,
    *,
    out_override: str | None = None,
    force: bool = False,
    no_deps: bool = False,
    dry: bool = False,
    keep_overlay: bool = False,
    force_native: bool = False,
) -> Path:
    stages = stage_map(cfg)
    if stage_id not in stages:
        die(f"未知 stage: {stage_id}（可用: {', '.join(stages)}）")
    stage = stages[stage_id]
    base_id = stage["base"]

    # 1) 解析 base APK / base JS
    if base_id == "merged":
        merged = path_of(cfg["paths"]["merged_apk"])
        if no_deps and merged.is_file():
            print(f"== 跳过 merge（--no-deps）: {merged}")
        else:
            merged = ensure_merged(cfg, dry=dry, no_deps=no_deps)
        base_apk = merged
        base_js = path_of(cfg["paths"]["base_js"])
    else:
        if base_id not in stages:
            die(f"stage {stage_id} 的 base 不存在: {base_id}")
        bstage = stages[base_id]
        base_apk = stage_apk_out(bstage)
        base_js = stage_js_out(cfg, bstage)
        need_js = bool(stage.get("patches")) or bool(stage.get("main_js"))
        rebuild = force or bool(stage.get("rebuild_base")) or not base_apk.is_file()
        if need_js and (base_js is None or not base_js.is_file()):
            rebuild = True
        if rebuild:
            if no_deps:
                if not base_apk.is_file():
                    die(f"缺少 base APK {base_apk}，且指定了 --no-deps")
                if need_js and (base_js is None or not base_js.is_file()):
                    die(f"缺少 base JS {base_js}，且指定了 --no-deps")
            else:
                print(f"== 先构建上游 stage: {base_id}")
                build_stage(
                    cfg,
                    base_id,
                    force=force,
                    no_deps=False,
                    dry=dry,
                    keep_overlay=keep_overlay,
                    force_native=force_native,
                )
                base_apk = stage_apk_out(bstage)
                base_js = stage_js_out(cfg, bstage)
        if not base_apk.is_file() and not dry:
            die(f"缺少 base APK: {base_apk}")

    # 2) 打 JS 补丁链
    js_in: Path | None = base_js
    if stage.get("patches"):
        if js_in is None or (not js_in.is_file() and not dry):
            die(f"stage {stage_id} 需要 JS 输入，但 base 没有 js_out/文件: {js_in}")
        for pid in stage["patches"]:
            if pid not in cfg["patches"]:
                die(f"stage {stage_id} 引用了未知 patch: {pid}")
            p = cfg["patches"][pid]
            js_out = path_of(p["out"])
            print(f"== 补丁 {pid}: {js_in.name} -> {js_out.name}")
            run_py(p["script"], js_in, js_out, dry=dry)
            if not dry and not js_out.is_file():
                die(f"补丁 {pid} 没有生成输出: {js_out}")
            js_in = js_out
    final_js = js_in if stage.get("patches") else None

    # 3) 生成 overlay
    overlay = path_of(stage.get("overlay") or f"work/build/official-arm64-{stage_id}")
    print(f"== overlay: {overlay.relative_to(ROOT) if overlay.is_relative_to(ROOT) else overlay}")
    if not dry:
        if overlay.exists() and not keep_overlay:
            shutil.rmtree(overlay)
        overlay.mkdir(parents=True, exist_ok=True)

    if final_js is not None:
        jsc = overlay / "assets" / "src" / "project.jsc"
        if not dry:
            jsc.parent.mkdir(parents=True, exist_ok=True)
        run_py("tools/jsc.py", "encrypt", final_js, jsc, dry=dry)

    for aid in stage.get("assets", []):
        if aid not in cfg["assets"]:
            die(f"stage {stage_id} 引用了未知 assets 步骤: {aid}")
        a = cfg["assets"][aid]
        print(f"== 资源步骤 {aid}")
        run_py(a["script"], overlay, dry=dry)

    if stage.get("main_js"):
        if "main_js" not in cfg:
            die("映射表缺少 [main_js]")
        src = path_of(cfg["paths"]["base_main_js"])
        tmp = path_of(cfg["paths"]["main_nohot"])
        require(src, "assets/main.js")
        print("== main.js：清 HotUpdateSearchPaths / 远程资源目录")
        run_py(cfg["main_js"]["script"], src, tmp, dry=dry)
        if not dry:
            dst = overlay / "assets" / "main.js"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tmp, dst)

    if stage.get("native") == "back":
        prepare_back(cfg, overlay, dry=dry, force_native=force_native)
    elif stage.get("dex"):
        prepare_dex(cfg, overlay, stage["dex"], dry=dry)
    elif stage.get("native"):
        die(f"未知 native 步骤: {stage['native']}")

    # 4) 重打包
    out = path_of(out_override) if out_override else stage_apk_out(stage)
    if not dry:
        require(base_apk, "base APK")
        if not overlay.exists():
            die(f"overlay 不存在: {overlay}")
        out.parent.mkdir(parents=True, exist_ok=True)
    print(f"== 重打包: {base_apk.name} + overlay -> {out}")
    run_bash(
        cfg["paths"]["repack_script"],
        base_apk,
        overlay,
        out,
        dry=dry,
    )
    if not dry:
        if not out.is_file():
            die(f"repack 没有生成输出: {out}")
        print(f"完成: {out} ({out.stat().st_size} B)")
        if stage.get("strip_ads"):
            script = path_of(stage.get("strip_ads_script") or "tools/strip_ads_apk.py")
            tmp = out.with_name(out.stem + ".adsfree.tmp.apk")
            print("== 剥离广告 SDK / 设备信息库")
            run_py(script, out, tmp, dry=dry)
            if not tmp.is_file():
                die(f"广告剥离没有生成输出: {tmp}")
            tmp.replace(out)
            sig = out.with_name(out.name + ".idsig")
            if sig.exists():
                sig.unlink()
            print(f"广告剥离完成: {out} ({out.stat().st_size} B)")
    else:
        print(f"完成（dry-run）: {out}")
    return out


def prepare_back(cfg: dict, overlay: Path, *, dry: bool, force_native: bool) -> None:
    c = cfg["native"]["back"]
    official = path_of(c.get("official_apk") or cfg["paths"]["official_apk"])
    full = path_of(c["apktool_dir"])
    frame = path_of(c["apktool_framework"])
    built = path_of(c["build_apk"])

    if force_native and not dry and full.exists():
        print(f"== --force-native: 删除 {full}")
        shutil.rmtree(full)

    print("== 原生返回键：apktool 解包 / smali / 重编")
    if not full.is_dir():
        require(official, "官方底包")
        if not dry:
            frame.mkdir(parents=True, exist_ok=True)
        run(["apktool", "d", "-f", "-p", frame, "-o", full, official], dry=dry)

    marker = full / c["smali_dir"] / "org" / "cocos2dx" / "javascript" / "AndroidBackBridge.smali"
    if not marker.is_file():
        run_py(c["smali_patch"], full / c["smali_dir"], dry=dry)
    else:
        print(f"  已存在 smali 桥: {marker.relative_to(ROOT)}")

    # apktool 会复用 full/build 里的旧 dex；清掉，避免 classes2.dex 少类
    if not dry:
        cache = full / "build"
        if cache.exists():
            shutil.rmtree(cache)
    run(["apktool", "b", "-p", frame, full, "-o", built], dry=dry)

    if dry:
        for name in c["dex"]:
            print(f"  $ unzip -p {built} {name} > {overlay / name}")
        return
    require(built, "apktool 重编产物")
    with zipfile.ZipFile(built) as z:
        names = set(z.namelist())
        for name in c["dex"]:
            if name not in names:
                die(f"apktool 产物里没有 {name}")
            z.extract(name, overlay)
            print(f"  + {overlay / name}")


def prepare_dex(cfg: dict, overlay: Path, dex_id: str, *, dry: bool) -> None:
    if dex_id not in cfg["native"]:
        die(f"未知 dex 步骤: {dex_id}")
    c = cfg["native"][dex_id]
    java = path_of(c["java"])
    api = path_of(c["android_jar"])
    classes = path_of(c["classes_dir"])
    jar = path_of(c["classes_jar"])
    dexdir = path_of(c["dex_dir"])
    require(java, "Java 源文件")

    if not api.is_file():
        print("== 下载 Android API jar")
        url = c.get("android_jar_url")
        if not url:
            die(f"缺少 {api}，且映射表没有 android_jar_url")
        if not dry:
            api.parent.mkdir(parents=True, exist_ok=True)
        run(["curl", "-sL", "--max-time", "120", url, "-o", api], dry=dry)

    if not dry:
        for d in (classes, dexdir):
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True)
    print(f"== 编译 {java.name} -> {c['dex_name']}")
    run([
        "javac", "-source", "8", "-target", "8",
        "-classpath", api, "-d", classes, java,
    ], dry=dry)
    run(["jar", "cf", jar, "-C", classes, "."], dry=dry)

    java11 = Path(c["java11"]) if c.get("java11") else None
    d8jar = Path(c["d8_jar"]) if c.get("d8_jar") else None
    if java11 and d8jar and java11.is_file() and d8jar.is_file():
        run([
            java11, "-cp", d8jar, "com.android.tools.r8.D8",
            "--lib", api, "--min-api", "21", "--output", dexdir, jar,
        ], dry=dry)
    else:
        run(["d8", "--lib", api, "--min-api", "21", "--output", dexdir, jar], dry=dry)

    target = overlay / c["dex_name"]
    if dry:
        print(f"  $ cp {dexdir / 'classes.dex'} {target}")
        return
    require(dexdir / "classes.dex", "d8 产物")
    shutil.copy2(dexdir / "classes.dex", target)
    print(f"  + {target}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="按 tools/pipeline.toml 构建 APK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("stage", nargs="?", help="stage id（默认 default_stage）")
    p.add_argument("--list", action="store_true", help="列出 stage")
    p.add_argument("--out", help="覆盖最终 APK 输出路径")
    p.add_argument("--force", action="store_true", help="连同依赖链一起重跑")
    p.add_argument("--no-deps", action="store_true", help="不重跑上游，只使用现有产物")
    p.add_argument("--dry-run", action="store_true", help="只打印命令，不落盘")
    p.add_argument("--keep-overlay", action="store_true", help="保留 overlay 目录里的旧文件")
    p.add_argument("--force-native", action="store_true", help="重新 apktool 解包/重编 native")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    cfg = load_table()
    validate_table(cfg)

    if args.list or args.stage == "list":
        show_list(cfg)
        return 0

    stage_id = args.stage or cfg.get("default_stage")
    if not stage_id:
        die("映射表没有 default_stage，也没有指定 stage")
    if stage_id == "all":
        stage_id = cfg.get("default_stage")
        print(f"== all -> {stage_id}")

    if args.force and args.no_deps:
        die("--force 与 --no-deps 不能同时使用")

    out = build_stage(
        cfg,
        stage_id,
        out_override=args.out,
        force=args.force,
        no_deps=args.no_deps,
        dry=args.dry_run,
        keep_overlay=args.keep_overlay,
        force_native=args.force_native,
    )
    if not args.out and not args.dry_run and stage_id == "profile-native":
        target = out.parent / final_artifact_name()
        if target != out:
            if out.exists():
                out.replace(target)
            sig = out.with_name(out.name + ".idsig")
            if sig.exists():
                sig.unlink()
            print(f"成品命名: {target} ({target.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
