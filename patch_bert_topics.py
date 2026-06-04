# -*- coding: utf-8 -*-
"""
根据 BERTopic 结果，把 Topic 8（寿辰贺画）和 Topic 17（赈灾义卖）
的事件 ID 从 bertopic_results.json 里提出，
打进 hbh_topics.json 的对应条目里。
"""
import json, os
os.chdir(r"D:\Desktop\VAST CHALLENGE")

with open("bertopic_results.json", encoding="utf-8") as f:
    bert = json.load(f)
with open("hbh_topics.json", encoding="utf-8") as f:
    topics = json.load(f)

# 从 BERTopic 取 Topic 8 / 17 的 event_id
topic8_ids  = {d["event_id"] for d in bert["doc_topics"] if d["topic_id"] == 8}
topic17_ids = {d["event_id"] for d in bert["doc_topics"] if d["topic_id"] == 17}
print(f"Topic 8 寿辰贺画: {len(topic8_ids)} 条")
print(f"Topic 17 赈灾义卖: {len(topic17_ids)} 条")

# 打标签
added8, added17 = 0, 0
for t in topics:
    eid = t["event_id"]
    if eid in topic8_ids and "寿辰贺画" not in t["topics"]:
        t["topics"].append("寿辰贺画")
        if "其他" in t["topics"] and len(t["topics"]) > 1:
            t["topics"].remove("其他")
        added8 += 1
    if eid in topic17_ids and "赈灾义卖" not in t["topics"]:
        t["topics"].append("赈灾义卖")
        if "其他" in t["topics"] and len(t["topics"]) > 1:
            t["topics"].remove("其他")
        added17 += 1

with open("hbh_topics.json", "w", encoding="utf-8") as f:
    json.dump(topics, f, ensure_ascii=False, indent=2)

print(f"新增 寿辰贺画 标注: {added8} 条")
print(f"新增 赈灾义卖 标注: {added17} 条")
