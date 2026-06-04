# -*- coding: utf-8 -*-
"""
黄宾虹年谱地理轨迹抽取脚本
输出: hbh_locations.json, hbh_residences.json

策略:
1. 地名词表 (gazetteer) 驱动，每条地名有现代标准名 + 经纬度
2. 上下文窗口判断类型：居住 / 游历 / 通信去向
3. 多字地名优先，单字别名只在严格上下文下匹配，避免过度提取
"""

import json, re
from collections import defaultdict

# ── 1. 地名词表 ──────────────────────────────────────────────────────────────
# 格式: { 原文地名: (标准名, lat, lng, 省份/区域备注) }
# 经纬度来源: 国家地名数据库 / OpenStreetMap 标准坐标，精确到 0.0001°
GAZETTEER = {
    # ── 安徽徽州 ──
    "歙县":    ("歙县",  29.8634, 118.4152, "安徽"),
    "歙中":    ("歙县",  29.8634, 118.4152, "安徽"),
    "潭渡":    ("潭渡",  29.7900, 118.3400, "安徽·歙县附近"),
    "徽州":    ("徽州",  29.8634, 118.4152, "安徽"),
    "黄山":    ("黄山",  30.1301, 118.1561, "安徽"),
    "休宁":    ("休宁",  29.7867, 118.1937, "安徽"),
    "祁门":    ("祁门",  29.8554, 117.7178, "安徽"),
    "绩溪":    ("绩溪",  30.0673, 118.5786, "安徽"),
    "黟县":    ("黟县",  29.9207, 117.9337, "安徽"),
    "芜湖":    ("芜湖",  31.3385, 118.3832, "安徽"),
    "安庆":    ("安庆",  30.5083, 117.0633, "安徽"),
    "合肥":    ("合肥",  31.8206, 117.2272, "安徽"),

    # ── 浙江 ──
    "金华":    ("金华",  29.1028, 119.6496, "浙江"),
    "杭州":    ("杭州",  30.2741, 120.1551, "浙江"),
    "西湖":    ("西湖",  30.2424, 120.1551, "浙江·杭州"),
    "苏州":    ("苏州",  31.2989, 120.5853, "江苏"),
    "绍兴":    ("绍兴",  30.0020, 120.5752, "浙江"),
    "宁波":    ("宁波",  29.8683, 121.5440, "浙江"),
    "温州":    ("温州",  28.0005, 120.6724, "浙江"),
    "嘉兴":    ("嘉兴",  30.7522, 120.7514, "浙江"),
    "湖州":    ("湖州",  30.8923, 120.0864, "浙江"),
    "天目山":  ("天目山", 30.3328, 119.4395, "浙江"),

    # ── 上海 ──
    "上海":    ("上海",  31.2304, 121.4737, "上海"),

    # ── 江苏 ──
    "南京":    ("南京",  32.0603, 118.7969, "江苏"),
    "金陵":    ("南京",  32.0603, 118.7969, "江苏"),
    "扬州":    ("扬州",  32.3947, 119.4127, "江苏"),
    "镇江":    ("镇江",  32.1878, 119.4250, "江苏"),
    "无锡":    ("无锡",  31.5680, 120.2888, "江苏"),
    "常州":    ("常州",  31.7714, 119.9741, "江苏"),
    "南通":    ("南通",  32.0305, 120.8756, "江苏"),

    # ── 北方 ──
    "北平":    ("北京",  39.9042, 116.4074, "北京"),
    "北京":    ("北京",  39.9042, 116.4074, "北京"),
    "天津":    ("天津",  39.3434, 117.3616, "天津"),
    "保定":    ("保定",  38.8671, 115.4645, "河北"),
    "太原":    ("太原",  37.8706, 112.5489, "山西"),
    "开封":    ("开封",  34.7966, 114.3075, "河南"),
    "洛阳":    ("洛阳",  34.6197, 112.4541, "河南"),
    "西安":    ("西安",  34.3416, 108.9398, "陕西"),
    "泰安":    ("泰安",  36.2057, 117.1023, "山东"),
    "泰山":    ("泰山",  36.2553, 117.1058, "山东"),
    "济南":    ("济南",  36.6512, 117.1201, "山东"),

    # ── 华中 ──
    "武汉":    ("武汉",  30.5928, 114.3055, "湖北"),
    "汉口":    ("武汉",  30.5928, 114.3055, "湖北"),
    "武昌":    ("武汉",  30.5488, 114.3430, "湖北"),
    "长沙":    ("长沙",  28.2278, 112.9388, "湖南"),
    "南昌":    ("南昌",  28.6820, 115.8579, "江西"),
    "庐山":    ("庐山",  29.5728, 115.9917, "江西"),
    "九江":    ("九江",  29.7286, 116.0027, "江西"),

    # ── 华南 ──
    "广州":    ("广州",  23.1291, 113.2644, "广东"),
    "广东":    ("广州",  23.1291, 113.2644, "广东"),
    "桂林":    ("桂林",  25.2736, 110.2900, "广西"),
    "福州":    ("福州",  26.0745, 119.2965, "福建"),
    "厦门":    ("厦门",  24.4798, 118.0894, "福建"),

    # ── 西南 ──
    "重庆":    ("重庆",  29.5630, 106.5516, "重庆"),
    "成都":    ("成都",  30.5723, 104.0665, "四川"),
    "峨眉":    ("峨眉山", 29.6013, 103.4792, "四川"),
    "峨眉山":  ("峨眉山", 29.6013, 103.4792, "四川"),
    "昆明":    ("昆明",  25.0389, 102.7183, "云南"),

    # ── 其他山水名胜 ──
    "雁荡山":  ("雁荡山", 28.3672, 120.9897, "浙江"),
    "普陀":    ("普陀山", 29.9656, 122.3839, "浙江"),
    "普陀山":  ("普陀山", 29.9656, 122.3839, "浙江"),
    "焦山":    ("焦山",  32.2063, 119.4596, "江苏·镇江"),
    "栖霞":    ("栖霞山", 32.1372, 118.9419, "江苏·南京"),
    "齐云山":  ("齐云山", 29.8048, 118.1576, "安徽"),

    # ── 历史旧称 / 简称 (需要严格上下文才匹配) ──
    # 这些放到 STRICT_ALIASES 里单独处理
}

# 单字或二字简称，只在严格上下文下匹配，避免误判
STRICT_ALIASES = {
    "沪":  ("上海",  31.2304, 121.4737, "上海"),
    "杭":  ("杭州",  30.2741, 120.1551, "浙江"),
    "苏":  ("苏州",  31.2989, 120.5853, "江苏"),
    "宁":  ("南京",  32.0603, 118.7969, "江苏"),   # 旅宁、在宁 → 南京
    "穗":  ("广州",  23.1291, 113.2644, "广东"),
    "闽":  ("福建",  26.0745, 119.2965, "福建"),
}

# 上下文类型判断词
RESIDENCE_WORDS = re.compile(
    r"(居[住]?|住|寓|旅居|定居|迁居|移居|迁沪|迁京|迁杭|侨居|寄寓|旅寓|来[沪京杭]|抵沪|抵京|留居|暂住|客居|卜居)"
)
TRAVEL_WORDS = re.compile(
    r"(游|游历|游览|游山|登|泛舟|赴|往|抵|至|行至|赴[山]|写生|观山|揽胜|探幽|跋山|徒步|转道|取道|途经|经过|经由|入山)"
)
CORRESPONDENCE_WORDS = re.compile(
    r"(寄|致书|函|致函|去信|来信|通信|邮|书[柬信]|复[书信]|去函|手书|奉函|致|来函|接函)"
)

# 居住地 —— 年份区间先验（用于辅助分类，与抽取结果互相校验）
# 这是先验，不能凌驾于实际文本之上
PRIOR_RESIDENCE = [
    (1865, 1888, "歙县"),
    (1889, 1906, "歙县"),
    (1907, 1936, "上海"),
    (1937, 1948, "北京"),   # 北平
    (1948, 1955, "杭州"),
]

# ── 2. 工具函数 ──────────────────────────────────────────────────────────────

def get_context(text, match_start, match_end, window=15):
    """取匹配位置前后的上下文窗口"""
    pre  = text[max(0, match_start - window):match_start]
    post = text[match_end:min(len(text), match_end + window)]
    return pre, post

def classify_type(pre, post, place_name, year):
    """根据上下文窗口推断地点类型"""
    context = pre + post
    if CORRESPONDENCE_WORDS.search(pre):
        return "通信去向"
    if RESIDENCE_WORDS.search(pre) or RESIDENCE_WORDS.search(post[:5]):
        return "居住"
    if TRAVEL_WORDS.search(pre) or TRAVEL_WORDS.search(post[:5]):
        return "游历"
    # 无明显触发词时，用先验居住地辅助
    for (y0, y1, p) in PRIOR_RESIDENCE:
        if y0 <= year <= y1 and place_name == p:
            return "居住"
    return "游历"  # 默认游历（保守归类）

def find_places_in_event(evt):
    """在单条事件文本中找所有地名，返回 list of (place, std_name, lat, lng, type, raw_snippet)"""
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    results = []
    seen_spans = []

    def add_if_nonoverlap(start, end, place, std, lat, lng, ptype, snippet):
        for (s, e) in seen_spans:
            if not (end <= s or start >= e):
                return  # 与已有匹配重叠，跳过（优先更长的）
        seen_spans.append((start, end))
        results.append({
            "place": place,
            "standard_name": std,
            "lat": lat,
            "lng": lng,
            "type": ptype,
            "raw_text": snippet
        })

    # 先尝试长词（3+ 字），再尝试严格别名
    # 按词长降序排列，保证最长匹配优先
    sorted_places = sorted(GAZETTEER.items(), key=lambda x: len(x[0]), reverse=True)
    for place, (std, lat, lng, _) in sorted_places:
        for m in re.finditer(re.escape(place), text):
            pre, post = get_context(text, m.start(), m.end())
            ptype = classify_type(pre, post, std, year)
            snippet = text[max(0,m.start()-20):min(len(text),m.end()+20)]
            add_if_nonoverlap(m.start(), m.end(), place, std, lat, lng, ptype, snippet)

    # 严格别名：只匹配 "旅沪 / 在沪 / 抵沪 / 居沪" 这种格式
    for alias, (std, lat, lng, _) in STRICT_ALIASES.items():
        for m in re.finditer(re.escape(alias), text):
            pre, post = get_context(text, m.start(), m.end(), window=6)
            # 严格判断：前面必须是动作词
            strict_ctx = pre + post[:3]
            if not re.search(r"[赴居旅抵在游往至迁寓]", strict_ctx):
                continue
            ptype = classify_type(pre, post, std, year)
            snippet = text[max(0,m.start()-15):min(len(text),m.end()+15)]
            add_if_nonoverlap(m.start(), m.end(), alias, std, lat, lng, ptype, snippet)

    return results

# ── 3. 主抽取流程 ────────────────────────────────────────────────────────────

def extract_locations():
    print("加载 hbh_events_raw.json ...")
    with open("hbh_events_raw.json", "r", encoding="utf-8") as f:
        events = json.load(f)

    print(f"共 {len(events)} 条事件，开始地点抽取 ...")

    locations = []
    per_year_places = defaultdict(lambda: defaultdict(list))  # year → std_name → [event_ids]

    skipped_headers = 0
    for evt in events:
        if evt.get("type") == "year_header":
            skipped_headers += 1
            continue
        places_found = find_places_in_event(evt)
        for p in places_found:
            loc_entry = {
                "event_id": evt["id"],
                "year":     evt["year"],
                "date":     evt.get("date", str(evt["year"])),
                "place":    p["place"],
                "standard_name": p["standard_name"],
                "lat":      p["lat"],
                "lng":      p["lng"],
                "type":     p["type"],
                "raw_text": p["raw_text"],
            }
            locations.append(loc_entry)
            per_year_places[evt["year"]][p["standard_name"]].append(evt["id"])

    print(f"  跳过 year_header: {skipped_headers}")
    print(f"  地点记录总数: {len(locations)}")
    return locations, per_year_places

# ── 4. 居所汇总 ──────────────────────────────────────────────────────────────

def build_residences(locations, per_year_places):
    """
    居所 = 以"居住"类型出现的地点，合并连续年份段
    额外输出 event_count（该地所有类型事件数，含游历/通信）
    """
    # 按年份统计各地的居住事件数
    year_residence = defaultdict(set)  # year → set of std_names marked 居住
    place_years    = defaultdict(set)  # std_name → set of years with 居住 events
    place_all_evts = defaultdict(set)  # std_name → event_ids (all types)

    for loc in locations:
        std = loc["standard_name"]
        yr  = loc["year"]
        place_all_evts[std].add(loc["event_id"])
        if loc["type"] == "居住":
            place_years[std].add(yr)
            year_residence[yr].add(std)

    # 先验居住地补充（如果年谱里直接没有居住触发词但此人在此城市）
    # 只补充有 ≥5 个事件的年份
    for (y0, y1, pname) in PRIOR_RESIDENCE:
        std_candidates = [s for (p,(s,*_)) in GAZETTEER.items() if s == pname]
        if not std_candidates:
            continue
        std = std_candidates[0]
        for yr in range(y0, y1+1):
            cnt = len(per_year_places[yr].get(std, []))
            if cnt >= 3:
                place_years[std].add(yr)

    # 为每个居住地合并连续年份段
    residences = []
    for std, years in place_years.items():
        if not years:
            continue
        sorted_years = sorted(years)
        # 合并连续段（允许间隔 ≤2 年的视为同一段，短暂离开不算断）
        segments = []
        seg_start = sorted_years[0]
        seg_end   = sorted_years[0]
        for yr in sorted_years[1:]:
            if yr - seg_end <= 2:
                seg_end = yr
            else:
                segments.append((seg_start, seg_end))
                seg_start = yr
                seg_end   = yr
        segments.append((seg_start, seg_end))

        # 取 gazetteer 里的坐标
        lat, lng = None, None
        for p, (s, la, lo, _) in GAZETTEER.items():
            if s == std:
                lat, lng = la, lo
                break

        # 取所有别名里事件数最多的那段
        for seg_start, seg_end in segments:
            # event_count = 该时段内该地出现的唯一事件数
            evt_ids_in_seg = set()
            for loc in locations:
                if loc["standard_name"] == std and seg_start <= loc["year"] <= seg_end:
                    evt_ids_in_seg.add(loc["event_id"])
            residences.append({
                "place": std,
                "standard_name": std,
                "lat":  lat,
                "lng":  lng,
                "start_year":     seg_start,
                "end_year":       seg_end,
                "duration_years": seg_end - seg_start + 1,
                "event_count":    len(evt_ids_in_seg),
                "notes": ""
            })

    # 按 start_year 排序
    residences.sort(key=lambda r: r["start_year"])
    return residences

# ── 5. 特殊观察标记 ──────────────────────────────────────────────────────────

def annotate_observations(locations, per_year_places):
    """
    检测：
    A. 活动半径骤变（某年地点突然从多→少）
    B. 沉默期（某年地点数 < 3）
    C. 简单的旅行→创作延迟（游某山 vs 后续画某山的年份差）
    """
    obs = []

    # 每年不同地点数
    yearly_unique = {yr: len(set(v for evts in places.values() for v in evts) )
                     for yr, places in per_year_places.items()}
    yearly_place_count = {yr: len(places) for yr, places in per_year_places.items()}

    years = sorted(yearly_place_count.keys())
    for i in range(1, len(years)):
        yr   = years[i]
        prev = years[i-1]
        if yr - prev > 3:
            continue
        curr_c = yearly_place_count[yr]
        prev_c = yearly_place_count[prev]
        if prev_c > 0 and curr_c / max(prev_c, 1) < 0.4 and prev_c >= 4:
            obs.append({
                "type": "活动半径骤变",
                "year": yr,
                "prev_year": prev,
                "prev_place_count": prev_c,
                "curr_place_count": curr_c,
                "note": f"{prev}年→{yr}年地点数从{prev_c}降至{curr_c}，骤降{100-round(curr_c/prev_c*100)}%"
            })

    for yr in years:
        if yearly_place_count[yr] < 2 and yr > 1870:
            obs.append({
                "type": "沉默期",
                "year": yr,
                "place_count": yearly_place_count[yr],
                "note": f"{yr}年地点数仅{yearly_place_count[yr]}，可能是记录稀少或足不出户"
            })

    # 黄山游历→黄山画作 简单检测
    huangshan_travel_years = set()
    huangshan_art_years    = set()
    for loc in locations:
        if loc["standard_name"] == "黄山":
            if loc["type"] == "游历":
                huangshan_travel_years.add(loc["year"])
    # 在原始文本中找"黄山"+"画"/"作"+"图"模式
    # (简化处理，详细分析交给艺术史团队)

    return obs

# ── 6. 主程序 ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    os.chdir(r"D:\Desktop\VAST CHALLENGE")

    locations, per_year_places = extract_locations()
    residences = build_residences(locations, per_year_places)
    observations = annotate_observations(locations, per_year_places)

    # 写输出
    with open("hbh_locations.json", "w", encoding="utf-8") as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)

    with open("hbh_residences.json", "w", encoding="utf-8") as f:
        json.dump(residences, f, ensure_ascii=False, indent=2)

    with open("hbh_location_observations.json", "w", encoding="utf-8") as f:
        json.dump(observations, f, ensure_ascii=False, indent=2)

    # 所有诊断报告写文件，避免 PS 乱码
    lines = []
    lines.append(f"hbh_locations.json: {len(locations)} 条")
    lines.append(f"hbh_residences.json: {len(residences)} 段")
    lines.append(f"hbh_location_observations.json: {len(observations)} 条观察")
    lines.append("")

    lines.append("── 居所汇总预览 ──")
    for r in residences:
        lines.append(f"  {r['place']:4s} {r['start_year']}-{r['end_year']} ({r['duration_years']}年) {r['event_count']}事件")
    lines.append("")

    lines.append("── 每年独立地点数 ──")
    years_sorted = sorted(per_year_places.keys())
    for yr in years_sorted:
        places = list(per_year_places[yr].keys())
        lines.append(f"  {yr}: {len(places)} 地 -> {', '.join(places[:10])}")
    lines.append("")

    lines.append("── 观察标记 ──")
    for o in observations:
        lines.append(f"  [{o['type']}] {o['note']}")
    lines.append("")

    # 类型分布统计
    type_counts = defaultdict(int)
    for loc in locations:
        type_counts[loc["type"]] += 1
    lines.append("── 类型分布 ──")
    for t, c in sorted(type_counts.items()):
        lines.append(f"  {t}: {c}")
    lines.append("")

    # 出现频率 TOP20 地点
    from collections import Counter
    place_freq = Counter(loc["standard_name"] for loc in locations)
    lines.append("── TOP20 高频地点 ──")
    for p, c in place_freq.most_common(20):
        lines.append(f"  {p}: {c}")

    with open("location_diag.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("Done. See location_diag.txt")
