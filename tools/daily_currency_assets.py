#!/usr/bin/env python3
"""生成本地日程/货币化的资产 overlay（扫描所有 locale 变体）。"""
import glob
import json
import os
import sys


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: tools/daily_currency_assets.py <overlay_dir>")
    root = sys.argv[1]
    count = {"plan": 0, "item": 0, "string": 0}

    for p in glob.glob("work/extracted/oppo/assets/res/import/*/*.json"):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        name = d.get("_name")
        changed = False

        if name == "plan":
            task = d.get("json", {}).get("8")
            if isinstance(task, dict):
                task["itemID"] = "50001002"
                task["itemCount"] = 5000
                changed = True
                count["plan"] += 1

        elif name == "item":
            item = d.get("json", {}).get("50000002")
            if isinstance(item, dict):
                item["name"] = "银币袋"
                item["description"] = "使用即可获得5000银币"
                item["icon"] = "50001002"
                item["onSale"] = False
                changed = True
                count["item"] += 1

        elif name == "string":
            for k, v in d.get("json", {}).items():
                if isinstance(v, str) and "全部完成可获得充电宝" in v:
                    d["json"][k] = v.replace("全部完成可获得充电宝", "全部完成可获得银币")
                    changed = True
            if changed:
                count["string"] += 1

        if changed:
            rel = p.split("work/extracted/oppo/")[-1]
            out = os.path.join(root, rel)
            write_json(out, d)
            print("asset ->", out)

    print("changed", count)


if __name__ == "__main__":
    main()
