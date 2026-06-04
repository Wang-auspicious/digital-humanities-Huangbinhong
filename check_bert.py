# -*- coding: utf-8 -*-
import json
with open("bertopic_results.json", encoding="utf-8") as f:
    r = json.load(f)

print(f"总文档: {r['total_docs']}, 主题数: {r['total_topics']}")
print()
print("── topic_words ──")
for tid, words in list(r["topic_words"].items())[:10]:
    print(f"  Topic {tid}: {words}")

print()
# 看 doc_topics 分布
from collections import Counter
tc = Counter(d["topic_id"] for d in r["doc_topics"])
print("── 主题文档数分布 ──")
for tid, cnt in sorted(tc.items()):
    print(f"  Topic {tid:3d}: {cnt}")
