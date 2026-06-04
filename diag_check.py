# -*- coding: utf-8 -*-
import json
from collections import Counter

with open("hbh_locations.json", encoding="utf-8") as f:
    locs = json.load(f)

lines = []

# 检查1：山岳被错误标为居住
MOUNTAINS = {"黄山","庐山","泰山","峨眉山","雁荡山","普陀山","齐云山","天目山","西湖","栖霞山","焦山"}
mountain_res = [l for l in locs if l["type"]=="居住" and l["standard_name"] in MOUNTAINS]
lines.append(f"山岳/名胜被标居住: {len(mountain_res)} 条")
for r in mountain_res[:15]:
    lines.append(f"  {r['event_id']} {r['year']} {r['standard_name']} | {r['raw_text'][:80]}")

lines.append("")

# 检查2：通信去向样本
comms = [l for l in locs if l["type"]=="通信去向"]
lines.append(f"通信去向共 {len(comms)} 条，样本:")
for c in comms[:10]:
    lines.append(f"  {c['event_id']} {c['year']} {c['standard_name']} | {c['raw_text'][:80]}")

lines.append("")

# 检查3：1865年7个地点，是否合理
y1865 = [l for l in locs if l["year"] == 1865]
lines.append(f"1865年地点 {len(y1865)} 条:")
for r in y1865:
    lines.append(f"  {r['event_id']} {r['standard_name']} [{r['type']}] | {r['raw_text'][:80]}")

lines.append("")

# 检查4：上海1007条，查几个样本
sh_sample = [l for l in locs if l["standard_name"]=="上海"][:5]
lines.append("上海样本:")
for r in sh_sample:
    lines.append(f"  {r['event_id']} {r['year']} [{r['type']}] | {r['raw_text'][:80]}")

lines.append("")

# 检查5：查 广州 123→205 变化是否合理（1921-1929 五年50事件）
gz = [l for l in locs if l["standard_name"]=="广州"]
gz_by_year = Counter(r["year"] for r in gz)
lines.append("广州 按年分布 (TOP15):")
for yr, cnt in gz_by_year.most_common(15):
    lines.append(f"  {yr}: {cnt}")

lines.append("")

# 检查6：1896 / 1903 沉默年 — 查原事件数
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)
for yr in [1896, 1903, 1901]:
    evts = [e for e in events if e["year"]==yr and e.get("type")!="year_header"]
    lines.append(f"{yr}年原始事件数: {len(evts)}, 样本: {evts[0]['raw_text'][:80] if evts else '无'}")

with open("diag_check1.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done")
