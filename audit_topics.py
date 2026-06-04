# -*- coding: utf-8 -*-
"""
主题分类自查脚本
每个主题抽取20条样本，按年代分布，人工可读
"""
import json, random
from collections import defaultdict, Counter

with open("hbh_topics.json", encoding="utf-8") as f:
    topics = json.load(f)
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

evt_map = {e["id"]: e for e in events}

# 按主题分组
by_topic = defaultdict(list)
for t in topics:
    for topic in t["topics"]:
        by_topic[topic].append(t)

lines = []

# 每个主题：总数 + 按年代分布 + 20条样本（均匀跨时期）
all_topics = sorted(by_topic.keys(), key=lambda x: -len(by_topic[x]))

for topic in all_topics:
    items = by_topic[topic]
    lines.append(f"\n{'='*60}")
    lines.append(f"主题: {topic}  ({len(items)} 条)")

    # 按年代分布
    decade_cnt = Counter((t["year"]//10)*10 for t in items)
    dist = "  ".join(f"{d}s:{c}" for d,c in sorted(decade_cnt.items()))
    lines.append(f"年代分布: {dist}")
    lines.append("")

    # 均匀抽样：每10年段取2条
    by_decade = defaultdict(list)
    for t in items:
        by_decade[(t["year"]//10)*10].append(t)

    samples = []
    for dec in sorted(by_decade.keys()):
        bucket = by_decade[dec]
        n = min(2, len(bucket))
        samples.extend(random.sample(bucket, n))

    # 最多取20条
    if len(samples) > 20:
        samples = samples[:20]

    for s in samples:
        raw = evt_map[s["event_id"]].get("raw_text", "")
        lines.append(f"  [{s['year']}] {s['event_id']}")
        lines.append(f"  关键词: {s['keywords']}")
        lines.append(f"  原文: {raw[:150]}")
        lines.append("")

with open("topic_audit.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> topic_audit.txt")
