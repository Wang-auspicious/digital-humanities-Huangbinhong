# -*- coding: utf-8 -*-
"""最终验证：三个输出文件结构完整性"""
import json

with open("hbh_locations.json", encoding="utf-8") as f:
    locs = json.load(f)
with open("hbh_residences.json", encoding="utf-8") as f:
    res = json.load(f)
with open("era_timeline.json", encoding="utf-8") as f:
    era = json.load(f)
with open("hbh_observations.json", encoding="utf-8") as f:
    obs = json.load(f)

lines = []
lines.append("=== 输出文件验证报告 ===")
lines.append("")

# 1. hbh_locations.json 字段完整性
req_fields = {"event_id","year","date","place","standard_name","lat","lng","type","raw_text"}
missing_fields = [l for l in locs if not req_fields.issubset(l.keys())]
lines.append(f"hbh_locations.json")
lines.append(f"  记录数: {len(locs)}")
lines.append(f"  字段缺失: {len(missing_fields)}")

# 坐标范围校验（中国境内大致：lat 18-53, lng 73-135）
bad_coords = [l for l in locs if not (18 <= l["lat"] <= 53 and 73 <= l["lng"] <= 135)]
lines.append(f"  坐标越界: {len(bad_coords)}")

# date 格式校验
import re
bad_date = [l for l in locs if not re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", str(l["date"]))]
lines.append(f"  date格式异常: {len(bad_date)}")
if bad_date:
    for b in bad_date[:3]:
        lines.append(f"    {b['event_id']} date={b['date']}")

# type 枚举校验
valid_types = {"居住","游历","通信去向"}
bad_type = [l for l in locs if l["type"] not in valid_types]
lines.append(f"  type异常: {len(bad_type)}")

# 年份范围
years = [l["year"] for l in locs]
lines.append(f"  年份范围: {min(years)}-{max(years)}")
lines.append("")

# 2. hbh_residences.json
lines.append(f"hbh_residences.json")
lines.append(f"  记录数: {len(res)}")
for r in res:
    lines.append(f"  {r['place']:4s} {r['start_year']}-{r['end_year']} {r['duration_years']}年 {r['event_count']}事件")
    lines.append(f"    lat={r['lat']} lng={r['lng']}")

# 检查时段不重叠
lines.append("  时段重叠检查:")
for i in range(len(res)):
    for j in range(i+1, len(res)):
        a, b = res[i], res[j]
        if a["standard_name"] == b["standard_name"]:
            if not (a["end_year"] < b["start_year"] or b["end_year"] < a["start_year"]):
                lines.append(f"    重叠: {a['place']} {a['start_year']}-{a['end_year']} vs {b['start_year']}-{b['end_year']}")
lines.append("    (无重叠则上方空白)")
lines.append("")

# 3. era_timeline.json
lines.append(f"era_timeline.json")
lines.append(f"  记录数: {len(era)}")
valid_cats = {"政治","战争","文化","社会"}
bad_cat = [e for e in era if e["category"] not in valid_cats]
lines.append(f"  category异常: {len(bad_cat)}")
bad_imp = [e for e in era if e["importance"] not in [1,2,3]]
lines.append(f"  importance异常: {len(bad_imp)}")
lines.append("")

# 4. 样本抽检 - 3 条 hbh_locations
lines.append("样本抽检（hbh_locations 第1/1000/2000条）:")
for idx in [0, 1000, 2000]:
    if idx < len(locs):
        l = locs[idx]
        lines.append(f"  [{idx}] {l['event_id']} {l['year']} {l['standard_name']} [{l['type']}]")
        lines.append(f"       lat={l['lat']} lng={l['lng']} | {l['raw_text'][:60]}")

lines.append("")
lines.append("=== 验证完成 ===")

with open("geo_verify.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> geo_verify.txt")
