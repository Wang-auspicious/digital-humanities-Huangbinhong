# -*- coding: utf-8 -*-
"""
检测年谱中潜在的意外主题（佛/禅/道/易等）
为 BERTopic 运行前提供先验线索
"""
import json, re
from collections import Counter

with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

content = [e for e in events if e.get("type") != "year_header"]

patterns = {
    "佛禅": re.compile(r"(佛|禅|禅宗|禅画|佛法|禅意|菩萨|观音|罗汉|金刚|佛像|寺院|寺|庙|法师|居士|禅院|禅堂|念佛|参禅)"),
    "道易": re.compile(r"(道家|老庄|易经|周易|卦|阴阳|五行|道教|道士|太极|八卦|道法|丹道|道观)"),
    "诗词": re.compile(r"(诗|词|律诗|绝句|诗稿|诗集|吟诗|诗社|诗会|题诗|联诗|唱和|酬唱)"),
    "音乐": re.compile(r"(音乐|乐器|琴|箫|笛|筝|丝竹|古琴|鼓|演奏)"),
    "西洋": re.compile(r"(西洋|西方|油画|水彩|素描|透视|写实|西画|洋画|留学|东洋|日本画)"),
    "民间": re.compile(r"(民间|木版|年画|剪纸|民俗|刺绣|织锦|蜡染|工艺)"),
    "经济": re.compile(r"(生计|谋生|贫困|艰难|鬻画|卖画|润例|润格|稿费|版税|经济)"),
    "自然科学": re.compile(r"(化学|物理|数学|天文|地理|科学|医学|生物|植物|地质)"),
}

lines = []
for label, pat in patterns.items():
    matches = [(e["year"], e["raw_text"][:120]) for e in content if pat.search(e.get("raw_text",""))]
    year_dist = Counter(m[0] for m in matches)
    lines.append(f"── {label}: {len(matches)} 条 ──")
    # 年份分布（按10年段）
    decade_dist = Counter((y//10)*10 for y in (m[0] for m in matches))
    dist_str = "  ".join(f"{d}s:{c}" for d,c in sorted(decade_dist.items()))
    lines.append(f"  年代分布: {dist_str}")
    # 样本5条
    for yr, snippet in matches[:5]:
        lines.append(f"  [{yr}] {snippet[:100]}")
    lines.append("")

# 特别统计：佛禅按年份
lines.append("── 佛禅 按年详细分布 ──")
buf = re.compile(r"(佛|禅|禅宗|禅画|佛法|禅意|菩萨|观音|罗汉|佛像|寺院|寺|庙|居士|参禅)")
bud_by_year = Counter(e["year"] for e in content if buf.search(e.get("raw_text","")))
for yr in sorted(bud_by_year):
    if bud_by_year[yr] >= 2:
        lines.append(f"  {yr}: {bud_by_year[yr]}")

with open("unexpected_themes.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> unexpected_themes.txt")
