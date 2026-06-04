# -*- coding: utf-8 -*-
"""列出全部101条疾病健康事件，供人工逐条复核"""
import json
from collections import defaultdict

with open("hbh_topics.json", encoding="utf-8") as f:
    topics = json.load(f)
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)
evt_map = {e["id"]: e for e in events}

disease = [t for t in topics if "疾病健康" in t["topics"]]
disease.sort(key=lambda x: x["year"])

lines = [f"疾病健康 共 {len(disease)} 条\n"]
for i, t in enumerate(disease, 1):
    raw = evt_map[t["event_id"]].get("raw_text", "")
    lines.append(f"[{i:03d}] {t['event_id']} [{t['year']}]")
    lines.append(f"  关键词: {t['keywords']}")
    lines.append(f"  原文: {raw[:300]}")
    lines.append("")

with open("disease_audit.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done")
