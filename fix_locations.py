# -*- coding: utf-8 -*-
"""
修正版：地理轨迹提取
修正点：
1. 山岳/名胜强制标为 游历
2. 居所汇总按传记四大段整理，不再做算法聚合
3. 增加 note 字段（旅行→创作延迟观察）
"""

import json, re
from collections import defaultdict, Counter

# ── 1. 强制"游历"的地点 ──────────────────────────────────────────────────────
# 这些地方客观上不可能是长期居所
SCENIC_ONLY = {
    "黄山","庐山","泰山","峨眉山","雁荡山","普陀山","齐云山",
    "天目山","焦山","西湖","栖霞山","庐山","泰安","泰山",
}

# ── 2. 地名词表（与 extract_locations.py 相同）────────────────────────────────
GAZETTEER = {
    "歙县":    ("歙县",  29.8634, 118.4152),
    "歙中":    ("歙县",  29.8634, 118.4152),
    "潭渡":    ("潭渡",  29.7900, 118.3400),
    "徽州":    ("徽州",  29.8634, 118.4152),
    "黄山":    ("黄山",  30.1301, 118.1561),
    "休宁":    ("休宁",  29.7867, 118.1937),
    "祁门":    ("祁门",  29.8554, 117.7178),
    "绩溪":    ("绩溪",  30.0673, 118.5786),
    "黟县":    ("黟县",  29.9207, 117.9337),
    "芜湖":    ("芜湖",  31.3385, 118.3832),
    "安庆":    ("安庆",  30.5083, 117.0633),
    "合肥":    ("合肥",  31.8206, 117.2272),
    "金华":    ("金华",  29.1028, 119.6496),
    "杭州":    ("杭州",  30.2741, 120.1551),
    "西湖":    ("西湖",  30.2424, 120.1551),
    "苏州":    ("苏州",  31.2989, 120.5853),
    "绍兴":    ("绍兴",  30.0020, 120.5752),
    "宁波":    ("宁波",  29.8683, 121.5440),
    "温州":    ("温州",  28.0005, 120.6724),
    "嘉兴":    ("嘉兴",  30.7522, 120.7514),
    "湖州":    ("湖州",  30.8923, 120.0864),
    "天目山":  ("天目山", 30.3328, 119.4395),
    "上海":    ("上海",  31.2304, 121.4737),
    "南京":    ("南京",  32.0603, 118.7969),
    "金陵":    ("南京",  32.0603, 118.7969),
    "扬州":    ("扬州",  32.3947, 119.4127),
    "镇江":    ("镇江",  32.1878, 119.4250),
    "无锡":    ("无锡",  31.5680, 120.2888),
    "常州":    ("常州",  31.7714, 119.9741),
    "南通":    ("南通",  32.0305, 120.8756),
    "北平":    ("北京",  39.9042, 116.4074),
    "北京":    ("北京",  39.9042, 116.4074),
    "天津":    ("天津",  39.3434, 117.3616),
    "保定":    ("保定",  38.8671, 115.4645),
    "太原":    ("太原",  37.8706, 112.5489),
    "开封":    ("开封",  34.7966, 114.3075),
    "洛阳":    ("洛阳",  34.6197, 112.4541),
    "西安":    ("西安",  34.3416, 108.9398),
    "泰安":    ("泰山",  36.2057, 117.1023),
    "泰山":    ("泰山",  36.2553, 117.1058),
    "济南":    ("济南",  36.6512, 117.1201),
    "武汉":    ("武汉",  30.5928, 114.3055),
    "汉口":    ("武汉",  30.5928, 114.3055),
    "武昌":    ("武汉",  30.5488, 114.3430),
    "长沙":    ("长沙",  28.2278, 112.9388),
    "南昌":    ("南昌",  28.6820, 115.8579),
    "庐山":    ("庐山",  29.5728, 115.9917),
    "九江":    ("九江",  29.7286, 116.0027),
    "广州":    ("广州",  23.1291, 113.2644),
    "广东":    ("广州",  23.1291, 113.2644),
    "桂林":    ("桂林",  25.2736, 110.2900),
    "福州":    ("福州",  26.0745, 119.2965),
    "厦门":    ("厦门",  24.4798, 118.0894),
    "重庆":    ("重庆",  29.5630, 106.5516),
    "成都":    ("成都",  30.5723, 104.0665),
    "峨眉":    ("峨眉山", 29.6013, 103.4792),
    "峨眉山":  ("峨眉山", 29.6013, 103.4792),
    "昆明":    ("昆明",  25.0389, 102.7183),
    "雁荡山":  ("雁荡山", 28.3672, 120.9897),
    "普陀":    ("普陀山", 29.9656, 122.3839),
    "普陀山":  ("普陀山", 29.9656, 122.3839),
    "焦山":    ("焦山",  32.2063, 119.4596),
    "栖霞":    ("栖霞山", 32.1372, 118.9419),
    "栖霞山":  ("栖霞山", 32.1372, 118.9419),
    "齐云山":  ("齐云山", 29.8048, 118.1576),
    "福建":    ("福建",  26.0745, 119.2965),
}

STRICT_ALIASES = {
    "沪":  ("上海",  31.2304, 121.4737),
    "杭":  ("杭州",  30.2741, 120.1551),
    "苏":  ("苏州",  31.2989, 120.5853),
    "穗":  ("广州",  23.1291, 113.2644),
}

RESIDENCE_WORDS = re.compile(
    r"(居[住]?|住|寓|旅居|定居|迁居|移居|迁沪|迁京|迁杭|侨居|寄寓|旅寓|来[沪京杭]|抵沪|抵京|留居|暂住|客居|卜居)"
)
TRAVEL_WORDS = re.compile(
    r"(游|游历|游览|游山|登|泛舟|赴|往|抵|至|行至|写生|观山|揽胜|探幽|跋山|途经|经由|入山)"
)
CORRESPONDENCE_WORDS = re.compile(
    r"(寄|致书|去函|致函|去信|来信|复[书信]|手书|奉函|邮寄)"
)

# 传记四大居住段 —— 来自文献记录，不靠算法推算
KNOWN_RESIDENCES = [
    {
        "place": "歙县",  "standard_name": "歙县",
        "lat": 29.8634, "lng": 118.4152,
        "start_year": 1865, "end_year": 1907,
        "notes": "祖籍潭渡村，幼年至青壮年主居徽州歙县；1907年星夜出逃上海"
    },
    {
        "place": "上海", "standard_name": "上海",
        "lat": 31.2304, "lng": 121.4737,
        "start_year": 1907, "end_year": 1937,
        "notes": "自1907年逃沪起长居上海，从事国学保存会、《神州日报》、美专教学等；1937年七七事变后因局势迁北平"
    },
    {
        "place": "北平", "standard_name": "北京",
        "lat": 39.9042, "lng": 116.4074,
        "start_year": 1937, "end_year": 1948,
        "notes": "1937年迁北平，任北平艺专教授；1948年应邀赴杭任国立艺专之职"
    },
    {
        "place": "杭州", "standard_name": "杭州",
        "lat": 30.2741, "lng": 120.1551,
        "start_year": 1948, "end_year": 1955,
        "notes": "1948年迁杭州，任国立艺专（后改浙江美术学院）教授，直至1955年逝世"
    },
]

def get_context(text, start, end, window=15):
    return text[max(0,start-window):start], text[end:min(len(text),end+window)]

def classify_type(pre, post, std_name, year):
    # 山岳名胜强制游历
    if std_name in SCENIC_ONLY:
        return "游历"
    context = pre + post
    if CORRESPONDENCE_WORDS.search(pre):
        return "通信去向"
    if RESIDENCE_WORDS.search(pre) or RESIDENCE_WORDS.search(post[:5]):
        return "居住"
    if TRAVEL_WORDS.search(pre) or TRAVEL_WORDS.search(post[:5]):
        return "游历"
    # 默认保守归类
    return "游历"

def find_places_in_event(evt):
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    results = []
    seen_spans = []

    def add_if_nonoverlap(start, end, place, std, lat, lng, ptype, snippet):
        for (s, e) in seen_spans:
            if not (end <= s or start >= e):
                return
        seen_spans.append((start, end))
        results.append({
            "place": place, "standard_name": std,
            "lat": lat, "lng": lng,
            "type": ptype, "raw_text": snippet
        })

    sorted_places = sorted(GAZETTEER.items(), key=lambda x: len(x[0]), reverse=True)
    for place, (std, lat, lng) in sorted_places:
        for m in re.finditer(re.escape(place), text):
            pre, post = get_context(text, m.start(), m.end())
            ptype = classify_type(pre, post, std, year)
            snippet = text[max(0,m.start()-20):min(len(text),m.end()+20)]
            add_if_nonoverlap(m.start(), m.end(), place, std, lat, lng, ptype, snippet)

    for alias, (std, lat, lng) in STRICT_ALIASES.items():
        for m in re.finditer(re.escape(alias), text):
            pre, post = get_context(text, m.start(), m.end(), window=6)
            strict_ctx = pre + post[:3]
            if not re.search(r"[赴居旅抵在游往至迁寓]", strict_ctx):
                continue
            ptype = classify_type(pre, post, std, year)
            snippet = text[max(0,m.start()-15):min(len(text),m.end()+15)]
            add_if_nonoverlap(m.start(), m.end(), alias, std, lat, lng, ptype, snippet)

    return results

def extract_locations(events):
    locations = []
    per_year = defaultdict(lambda: defaultdict(list))

    for evt in events:
        if evt.get("type") == "year_header":
            continue
        for p in find_places_in_event(evt):
            entry = {
                "event_id":      evt["id"],
                "year":          evt["year"],
                "date":          evt.get("date", str(evt["year"])),
                "place":         p["place"],
                "standard_name": p["standard_name"],
                "lat":           p["lat"],
                "lng":           p["lng"],
                "type":          p["type"],
                "raw_text":      p["raw_text"],
            }
            locations.append(entry)
            per_year[evt["year"]][p["standard_name"]].append(evt["id"])

    return locations, per_year

def build_residences(locations, events):
    """
    居所 = 使用 KNOWN_RESIDENCES 作基础框架，
    再从 locations 数据补充 event_count。
    """
    # 统计每个时段内各标准名的事件数
    place_year_evts = defaultdict(lambda: defaultdict(set))  # std → year → event_ids
    for loc in locations:
        place_year_evts[loc["standard_name"]][loc["year"]].add(loc["event_id"])

    residences = []
    for r in KNOWN_RESIDENCES:
        std = r["standard_name"]
        cnt = sum(len(ids) for yr, ids in place_year_evts[std].items()
                  if r["start_year"] <= yr <= r["end_year"])
        residences.append({
            "place":          r["place"],
            "standard_name":  std,
            "lat":            r["lat"],
            "lng":            r["lng"],
            "start_year":     r["start_year"],
            "end_year":       r["end_year"],
            "duration_years": r["end_year"] - r["start_year"] + 1,
            "event_count":    cnt,
            "notes":          r["notes"],
        })
    return residences

def detect_travel_art_delay(locations, events):
    """
    黄山案例：检测"游黄山"→"画黄山题款"之间的年份差。
    保守策略：只收集有明确"游"字上下文的黄山记录，
    与有"图"/"画"/"册"字样的黄山记录配对。
    """
    travel_years = []
    art_years    = []

    for loc in locations:
        if loc["standard_name"] != "黄山":
            continue
        txt = loc["raw_text"]
        if re.search(r"[游登上赴]", txt[:30]):
            travel_years.append(loc["year"])
        if re.search(r"[画图册作写]", txt[:30]):
            art_years.append(loc["year"])

    # 也从原始事件里找"黄山"+"画"的年份
    with open("hbh_events_raw.json", encoding="utf-8") as f:
        evts = json.load(f)
    for e in evts:
        t = e.get("raw_text","")
        if "黄山" in t and re.search(r"[画图册写]", t):
            art_years.append(e["year"])

    travel_years = sorted(set(travel_years))
    art_years    = sorted(set(art_years))
    pairs = []
    for ty in travel_years:
        # 找首个晚于该游历年的创作年
        later_art = [ay for ay in art_years if ay >= ty]
        if later_art:
            pairs.append({
                "travel_year": ty,
                "earliest_art_year": later_art[0],
                "delay_years": later_art[0] - ty,
            })
    return pairs

def detect_radius_collapse(per_year):
    obs = []
    yearly = {yr: len(places) for yr, places in per_year.items()}
    years = sorted(yearly.keys())
    for i in range(1, len(years)):
        yr, prev = years[i], years[i-1]
        if yr - prev > 3:
            continue
        c, p = yearly[yr], yearly[prev]
        if p >= 5 and c / max(p,1) < 0.45:
            obs.append({
                "type": "活动半径骤变",
                "year": yr,
                "from_count": p,
                "to_count": c,
                "drop_pct": round((1 - c/p)*100),
                "note": f"{prev}→{yr} 地点从{p}降至{c}（骤降{round((1-c/p)*100)}%）"
            })
    # 沉默年
    for yr in years:
        if yearly.get(yr,0) < 2 and yr > 1870:
            obs.append({
                "type": "沉默期",
                "year": yr,
                "place_count": yearly.get(yr,0),
                "note": f"{yr}年地点仅{yearly.get(yr,0)}处"
            })
    return obs

# ── 主程序 ───────────────────────────────────────────────────────────────────
import os
os.chdir(r"D:\Desktop\VAST CHALLENGE")

print("加载数据...")
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

locations, per_year = extract_locations(events)
residences = build_residences(locations, events)
radius_obs = detect_radius_collapse(per_year)
travel_delay = detect_travel_art_delay(locations, events)

print(f"locations: {len(locations)}")
print(f"residences: {len(residences)}")
print(f"observations: {len(radius_obs)}")
print(f"travel-art pairs: {len(travel_delay)}")

with open("hbh_locations.json",      "w", encoding="utf-8") as f:
    json.dump(locations,  f, ensure_ascii=False, indent=2)
with open("hbh_residences.json",     "w", encoding="utf-8") as f:
    json.dump(residences, f, ensure_ascii=False, indent=2)
with open("hbh_observations.json",   "w", encoding="utf-8") as f:
    json.dump({"radius_changes": radius_obs, "travel_art_delay": travel_delay},
              f, ensure_ascii=False, indent=2)

# 写诊断报告
report = []
report.append(f"locations: {len(locations)}")
report.append(f"residences: {len(residences)}")
report.append("")

report.append("── 居所（4大段）──")
for r in residences:
    report.append(f"  {r['place']:4s} {r['start_year']}-{r['end_year']} {r['duration_years']}年 {r['event_count']}事件")
    report.append(f"    {r['notes']}")
report.append("")

report.append("── 类型分布 ──")
tc = Counter(l["type"] for l in locations)
for t,c in sorted(tc.items()): report.append(f"  {t}: {c}")
report.append("")

report.append("── TOP25 高频地点 ──")
pc = Counter(l["standard_name"] for l in locations)
for p,c in pc.most_common(25): report.append(f"  {p}: {c}")
report.append("")

report.append("── 山岳被标居住验证（修正后应为0）──")
bad = [l for l in locations if l["type"]=="居住" and l["standard_name"] in SCENIC_ONLY]
report.append(f"  剩余错误: {len(bad)}")
report.append("")

report.append("── 旅行→创作延迟（黄山案例）──")
for pair in travel_delay[:10]:
    report.append(f"  游山年:{pair['travel_year']} → 最早创作年:{pair['earliest_art_year']} 延迟:{pair['delay_years']}年")
report.append("")

report.append("── 活动半径骤变 ──")
collapses = [o for o in radius_obs if o["type"]=="活动半径骤变"]
for o in collapses: report.append(f"  {o['note']}")
report.append("")

report.append("── 沉默期 ──")
silent = [o for o in radius_obs if o["type"]=="沉默期"]
for o in silent: report.append(f"  {o['note']}")
report.append("")

report.append("── 每年地点分布 ──")
for yr in sorted(per_year.keys()):
    pls = list(per_year[yr].keys())
    report.append(f"  {yr}: {len(pls)} -> {', '.join(pls[:12])}")

with open("location_report_v2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))
print("done -> location_report_v2.txt")
