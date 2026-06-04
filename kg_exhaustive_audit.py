# -*- coding: utf-8 -*-
"""
KG 穷尽性自检 — 五维正交验证
==============================
Method 1: Event coverage — 多少事件完全未被 KG 触及?
Method 2: Random blind sample — 抽 100 条原文, 人工级标注对照 KG, 算 precision/recall
Method 3: Pattern FNR scan — 每种关系扫原始文本, 找应标未标的漏网
Method 4: HBH 自撰深度 — 585 条黄金文本, 每条是否都有概念标注?
Method 5: Year gap — 哪些年份 KG 边密度异常低?
"""
import json, re, random, os
from collections import defaultdict, Counter

os.chdir(r"D:\Desktop\VAST CHALLENGE")

with open("hbh_knowledge_graph.json", encoding="utf-8") as f:
    kg = json.load(f)
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

content_events = [e for e in events if e.get("type") != "year_header"]
evt_by_id = {e["id"]: e for e in events}
edges_by_event = defaultdict(list)
for e in kg["edges"]:
    edges_by_event[e["event_id"]].append(e)

random.seed(42)
lines = []
lines.append("=" * 70)
lines.append("  KG 穷尽性自检 — 五维正交验证")
lines.append("=" * 70)

# ── Method 1: Event Coverage ───────────────────────────────────────────
lines.append("\n" + "=" * 50)
lines.append("METHOD 1: 事件覆盖率")
lines.append("=" * 50)

events_with_edges = len(edges_by_event)
events_without_edges = len(content_events) - events_with_edges
lines.append(f"  总内容事件: {len(content_events)}")
lines.append(f"  有KG边的: {events_with_edges} ({round(events_with_edges/len(content_events)*100,1)}%)")
lines.append(f"  零KG边的: {events_without_edges} ({round(events_without_edges/len(content_events)*100,1)}%)")

# 零边事件抽样 — 为什么它们没被KG触及?
zero_edge_events = [e for e in content_events if e["id"] not in edges_by_event]
sample_zero = random.sample(zero_edge_events, min(30, len(zero_edge_events)))
sample_zero.sort(key=lambda e: e["year"])
lines.append(f"\n  零边事件抽样（共{len(zero_edge_events)}条，抽30条）:")
for e in sample_zero:
    lines.append(f"    {e['id']} [{e['year']}]: {e['raw_text'][:120]}")
lines.append("")

# ── Method 2: Random Blind Sample ──────────────────────────────────────
lines.append("=" * 50)
lines.append("METHOD 2: 随机盲抽 100 条 — 人工级精确对照")
lines.append("=" * 50)

# 抽取 100 条，标注每条"应该有哪些关系"
sample = random.sample(content_events, 100)
sample.sort(key=lambda e: e["year"])

# 简单规则做"应标"判断
def expected_relations(evt):
    """对一条事件，用独立规则判断它应该有哪些KG关系"""
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    expected = set()

    # 通信
    if re.search(r"(与.{2,6}[书函信]|.{2,6}[书函][：:]|[致寄复覆].{2,6}[书函信])", text):
        expected.add("WROTE_TO")
    # 游历
    if re.search(r"(游[历览山]|登[临山]|赴[A-Za-z一-鿿]{2,4}$|往[A-Za-z一-鿿]{2,4}$|揽胜|探幽)", text):
        expected.add("TRAVELED_TO")
    # 创作
    if re.search(r"([作画绘]《|[作画绘写][山水花人梅]|册页|大幅|题跋|篆刻|临[帖池摹])", text):
        expected.add("CREATED")
    # 展览
    if re.search(r"(展览|画展|陈列|参展|出品|雅集|社集)", text):
        expected.add("EXHIBITED_AT")
    # 逝世
    if re.search(r"(病逝|逝世|去世|谢世|殁|遽归道山|追悼|公祭)", text):
        expected.add("MOURNED")
    # 赠画
    if re.search(r"(赠.{2,6}[画图册轴]|[画图册轴].{2,6}赠)", text):
        expected.add("GIFTED_ARTWORK")
    # 组织
    if re.search(r"(国学保存会|神州国光社|南社|中国画会|故宫|美专)", text):
        expected.add("INVOLVES_ORG")

    return expected

# Precision = KG标注中正确的 / KG标注总数
# Recall    = 应标中KG标了的 / 应标总数
tp_total = 0  # KG标了, 也应标
fp_total = 0  # KG标了, 不应标
fn_total = 0  # 应标了, KG没标
per_rel_stats = defaultdict(lambda: {"tp":0,"fp":0,"fn":0})

for evt in sample:
    eid = evt["id"]
    expected = expected_relations(evt)
    actual = {e["type"] for e in edges_by_event.get(eid, [])}

    # per-relation stats
    for rel in expected | actual:
        in_exp = rel in expected
        in_act = rel in actual
        if in_exp and in_act:
            per_rel_stats[rel]["tp"] += 1
        elif in_act and not in_exp:
            per_rel_stats[rel]["fp"] += 1
        elif in_exp and not in_act:
            per_rel_stats[rel]["fn"] += 1

    tp_total += len(expected & actual)
    fp_total += len(actual - expected)
    fn_total += len(expected - actual)

precision = tp_total / max(tp_total + fp_total, 1) * 100
recall    = tp_total / max(tp_total + fn_total, 1) * 100
f1        = 2 * precision * recall / max(precision + recall, 1)

lines.append(f"  样本: 100 条事件")
lines.append(f"  KG标注总边数: {tp_total + fp_total}")
lines.append(f"  应标总边数:   {tp_total + fn_total}")
lines.append(f"  Precision (KG标对率): {precision:.1f}%")
lines.append(f"  Recall    (应标命中率): {recall:.1f}%")
lines.append(f"  F1:        {f1:.1f}%")
lines.append("")
lines.append("  各关系类型细分:")
for rel in sorted(per_rel_stats):
    s = per_rel_stats[rel]
    p = s["tp"] / max(s["tp"]+s["fp"], 1) * 100
    r = s["tp"] / max(s["tp"]+s["fn"], 1) * 100
    lines.append(f"    {rel:25s} P:{p:5.1f}% R:{r:5.1f}%  TP:{s['tp']:3d} FP:{s['fp']:3d} FN:{s['fn']:3d}")
lines.append("")

# 假阳性样本
fp_samples = []
for evt in sample:
    eid = evt["id"]
    expected = expected_relations(evt)
    actual = {e["type"] for e in edges_by_event.get(eid, [])}
    extra = actual - expected
    if extra:
        fp_samples.append((evt, extra))
lines.append(f"  FP 样本（KG多标的，前10条）:")
for evt, extra in fp_samples[:10]:
    lines.append(f"    {evt['id']} [{evt['year']}] 多标:{extra} | {evt['raw_text'][:100]}")
lines.append("")

# 假阴性样本
fn_samples = []
for evt in sample:
    eid = evt["id"]
    expected = expected_relations(evt)
    actual = {e["type"] for e in edges_by_event.get(eid, [])}
    missing = expected - actual
    if missing:
        fn_samples.append((evt, missing))
lines.append(f"  FN 样本（KG漏标的，前10条）:")
for evt, missing in fn_samples[:10]:
    lines.append(f"    {evt['id']} [{evt['year']}] 漏标:{missing} | {evt['raw_text'][:100]}")
lines.append("")

# ── Method 3: Pattern FNR Scan ─────────────────────────────────────────
lines.append("=" * 50)
lines.append("METHOD 3: 各关系类型 漏标模式扫描")
lines.append("=" * 50)

# 对每种关系，用独立正则扫全部事件，找"明显应标但KG没标的"
FNR_PATTERNS = {
    "WROTE_TO": re.compile(r"([一-鿿]{2,5})(?:致|与|寄|复|覆)([一-鿿]{2,5})(?:书|函|信|札|尺牍|手翰|手札|手书)"),
    "GIFTED_ARTWORK": re.compile(r"(赠|寄赠|贻|赠予|见赠|惠赠|持赠|遗赠).{2,10}(画|图|册|轴|卷|帧|幅)"),
    "EXHIBITED_AT": re.compile(r"(展览|画展|陈列|参展|出品|观览).{0,10}(黄宾虹|宾虹|宾老|朴存)"),
}

for rel_name, pat in FNR_PATTERNS.items():
    existing_ids = {e["event_id"] for e in kg["edges"] if e["type"] == rel_name}
    missing = []
    for evt in content_events:
        eid = evt["id"]
        text = evt.get("raw_text", "")
        if eid not in existing_ids and pat.search(text):
            missing.append((evt, pat.search(text).group(0)))
    lines.append(f"\n  [{rel_name}]")
    lines.append(f"    KG已有: {len(existing_ids)} 条")
    lines.append(f"    模式扫出应标但漏标: {len(missing)} 条")
    for evt, m in missing[:8]:
        lines.append(f"    {evt['id']} [{evt['year']}] 命中'{m}': {evt['raw_text'][:100]}")
lines.append("")

# ── Method 4: HBH 自撰深度 ─────────────────────────────────────────────
lines.append("=" * 50)
lines.append("METHOD 4: HBH 自撰事件 — 黄金文本深度检查")
lines.append("=" * 50)

with open("hbh_source_layer.json", encoding="utf-8") as f:
    sources = json.load(f)

hbh_self_ids = {s["event_id"] for s in sources if s["source_type"] == "HBH自撰"}
hbh_self_events = [e for e in content_events if e["id"] in hbh_self_ids]

# 对每条 HBH 自撰事件，检查有无至少一种标注
hbh_no_annot = []
hbh_no_concept = []
for evt in hbh_self_events:
    eid = evt["id"]
    es = edges_by_event.get(eid, [])
    etypes = {e["type"] for e in es}
    # 检查有无概念边
    has_concept = "MENTIONS_CONCEPT" in etypes
    has_other   = len(etypes - {"MENTIONS_CONCEPT"}) > 0
    if not es:
        hbh_no_annot.append(evt)
    elif not has_concept:
        hbh_no_concept.append(evt)

lines.append(f"  HBH自撰事件总数: {len(hbh_self_events)}")
lines.append(f"  完全无任何KG边: {len(hbh_no_annot)} ({round(len(hbh_no_annot)/len(hbh_self_events)*100,1)}%)")
lines.append(f"  有KG边但无概念标注: {len(hbh_no_concept)} ({round(len(hbh_no_concept)/len(hbh_self_events)*100,1)}%)")
lines.append(f"\n  完全无标注的HBH自撰事件 (抽15条):")
for evt in hbh_no_annot[:15]:
    lines.append(f"    {evt['id']} [{evt['year']}]: {evt['raw_text'][:120]}")
lines.append(f"\n  有KG边但无概念标注的HBH自撰事件 (抽15条):")
for evt in hbh_no_concept[:15]:
    etypes = {e["type"] for e in edges_by_event.get(evt["id"], [])}
    lines.append(f"    {evt['id']} [{evt['year']}] 已有:{etypes} | {evt['raw_text'][:120]}")
lines.append("")

# ── Method 5: Year Gap ─────────────────────────────────────────────────
lines.append("=" * 50)
lines.append("METHOD 5: 年份边密度 vs 事件密度 偏差检测")
lines.append("=" * 50)

# 每年的事件数 vs 边数
year_evt_count = Counter(e["year"] for e in content_events)
year_edge_count = Counter(e["year"] for e in kg["edges"])
years = sorted(year_evt_count.keys())

# 找"事件多但边少"的异常年
lines.append(f"  {'年份':6s} {'事件数':6s} {'边数':6s} {'边/事件比':10s}")
anomalies = []
for yr in years:
    ec = year_evt_count[yr]
    ed = year_edge_count.get(yr, 0)
    ratio = ed / max(ec, 1)
    if ratio < 0.5 and ec >= 10:
        anomalies.append((yr, ec, ed, ratio))
    lines.append(f"  {yr:4d}  {ec:5d}  {ed:5d}  {ratio:8.2f}")

lines.append(f"\n  异常年 (事件≥10但边/事件<0.5): {len(anomalies)} 年")
for yr, ec, ed, ratio in anomalies[:15]:
    lines.append(f"    {yr}: {ec}事件 {ed}边 (比{ratio:.2f}) — 可能KG挖掘不足")
lines.append("")

# ── 总结 ────────────────────────────────────────────────────────────────
lines.append("=" * 70)
lines.append("  穷尽性自检总结")
lines.append("=" * 70)
judgment = ("KG挖掘已基本穷尽事件内容" if recall > 75 and len(hbh_no_annot) < 50
            else "存在可改善空间，尤其HBH自撰事件的标注深度")
lines.append(f"\n  整体判断: {judgment}")
print(f"done -> kg_exhaustive_report.txt ({len(lines)} lines)")

with open("kg_exhaustive_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> kg_exhaustive_report.txt")
