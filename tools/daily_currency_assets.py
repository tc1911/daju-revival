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
                task["description"] = "每日签到"
                task["itemID"] = "50001002"
                task["itemCount"] = 5000
                changed = True
                count["plan"] += 1

        elif name == "item":
            item = d.get("json", {}).get("50000002")
            if isinstance(item, dict):
                item["name"] = "充电宝（已废弃）"
                item["description"] = "已废弃，不再提供电量"
                item["icon"] = "50000002"
                item["onSale"] = False
                item["usable"] = False
                changed = True
                count["item"] += 1

        elif name == "string":
            replacements = {
                "MainView_9": "每日签到",
                "DailyTask_1": "每日签到",
                "DailyTask_2": "每日签到",
                "user_list_item_2": "每日签到",
                "user_list_item_3": "每日签到，获得以下奖励",
                "user_list_item_4": "每日签到，获得以下奖励",
                "pfb_DailyTask_1": "每日签到可获得 5000 银币 + 500 金币",
            }
            for k, v in d.get("json", {}).items():
                if k in replacements and v != replacements[k]:
                    d["json"][k] = replacements[k]
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
