# -*- coding: utf-8 -*-
"""
KG 全面审计脚本 —— 蓝军自攻击
===========================
审计清单:
  A. 情感正则精度 — 单字词假阳性 (感/冷/守/念 等)
  B. 文本来源层 — 分类准确率抽查
  C. WROTE_TO — 方向错误检测
  D. GIFTED_ARTWORK — 假阳性
  E. MENTIONS_CONCEPT — 假阳性样本
  F. MOURNED — 为什么只有13条? 漏了吗?
  G. TAUGHT — 为什么只有42条? 查覆盖率
  H. 整体边质量 — 无效边/重复边
"""
import json, re, os, random
from collections import defaultdict, Counter

os.chdir(r"D:\Desktop\VAST CHALLENGE")

with open("hbh_knowledge_graph.json", encoding="utf-8") as f:
    kg = json.load(f)
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

evt_by_id = {e["id"]: e for e in events}
content_events = [e for e in events if e.get("type") != "year_header"]
edge_by_type = defaultdict(list)
for e in kg["edges"]:
    edge_by_type[e["type"]].append(e)

random.seed(42)
lines = []
lines.append("="*70)
lines.append("  黄宾虹知识图谱 蓝军审计报告")
lines.append("="*70)
lines.append("")

# ── A. 情感正则精度 ──────────────────────────────────────────────────────
lines.append("── A. 情感维度 假阳性审计 ──")
lines.append("")

# 五个情感的正则模式
EMOTION_PATTERNS = {
    "喜悦/得悟": re.compile(r"(喜|乐|快|欣然|会心|大悟|豁然|悦|不觉|大笑|拍案|击节|畅然|忘倦|神来|兴会)"),
    "愤慨":       re.compile(r"(愤|怒|痛|恨|厌|深恨|深恶|耻|鄙|嗟|忧愤|痛心|扼腕)"),
    "孤独/坚持": re.compile(r"(寂|寥落|无人识|独自|枯坐|默坐|冷|守|耐|甘|孤|匹夫)"),
    "忧虑/焦虑": re.compile(r"(忧|虑|惶|恐|惧|急|窘|困|难|迫|束手)"),
    "感恩/眷恋": re.compile(r"(感|谢|恩|幸|幸甚|思|念|忆|不忘|铭心|怀旧|故土)"),
}

# 对每个情感维度抽 30 条样本，人工判断级假阳性
# 快速版本: 检测"明显的非情感用法"
NON_EMOTION_CONTEXTS = {
    "感恩/眷恋": [
        (re.compile(r"(感[觉触]到|感言|有感|感?不胜感|感?[谢敬][函信呈示覆]|感[激荷佩]|深感|感谢)"), "感X词组-非情感"),
        (re.compile(r"(谢[允应谅却绝]|代谢|凋谢|谢世|谢[病老]|谢[恩邀]|谢绝|谢[步辞]|谢不能|谢事|推谢)"), "谢-非感恩义"),
        (re.compile(r"(恩[泽禄宠]|[沐蒙受]恩|恩[科榜选]|恩[赐赏]|奏恩|恩[典荣])"), "恩-非感恩义"),
        (re.compile(r"(思[想虑索量]|[苦深]思|三思|思[考辨]|未思|[岂何]思)"), "思-非怀念义"),
        (re.compile(r"(念[书诵读佛经卷文咒珠]|[挂悬]念|一念|念[及旧昔前]|回念|心念)"), "念-非眷恋义"),
        (re.compile(r"(不忘初|不忘[之其]|不可忘|勿忘|忘[其此以前乃]|忘[年岁]|忘归|忘返|忘食|忘倦)"), "不忘-非情感义"),
    ],
    "孤独/坚持": [
        (re.compile(r"(冷[淡漠峭僻泉涧石坞]|[冰清]冷|[寒霜]冷)"), "冷-温度/景观义"),
        (re.compile(r"(守[道法节正旧官业]|[坚固]守|守[土城寨边]|守株|守拙|守[制丧孝]|守[约贫]|太守)"), "守-非情感义"),
        (re.compile(r"(寂[寞寥然]|圆寂|寂照|寂灭|寂[静音])"), "寂-宗教/描述义"),
        (re.compile(r"(甘[泉露霖液]|甘[美旨]|不甘[示弱落后]|[味]甘)"), "甘-物质义"),
        (re.compile(r"(孤[峰山塔岛寺村楼城云雁鹤]|孤[傲本标高])"), "孤-非孤独义"),
        (re.compile(r"(匹夫[之]?[勇责志]|匹[配敌]|单枪匹马|无出其匹)"), "匹-非匹夫义"),
        (re.compile(r"(独自[成存立然有行在]|独自[能可]|独[立善创到绝步断有行居]|不独)"), "独-非孤独义"),
    ],
    "忧虑/焦虑": [
        (re.compile(r"(忧[国患民世烦]|内忧|分忧|解忧|[担]忧|忧[戚忡]|忧[劳勤]|忧虑|忧心)"), "忧-情感义不排除"),
        (re.compile(r"(艰难|困难|时艰|艰苦|险难|万难|难[免堪]|难[以说]|避难|患难|[进创]难)"), "难-非焦虑义"),
        (re.compile(r"(急[速流湍]|急[行驰走就]|[缓]急|急[需务用]|紧急|火急)"), "急-非忧虑义"),
        (re.compile(r"(困[境厄顿难苦乏]|[贫]困|困[守于在]|困[兽禽]|受困)"), "困-非情感义"),
    ],
    "愤慨": [
        (re.compile(r"(痛[苦心恨]|痛[哭涕]|[哀悲]痛|痛[惜斥]|痛[痒]|[绞]痛|抱痛|创痛)"), "痛-情感义不排除"),
        (re.compile(r"(耻[辱笑]|[可]耻|国耻|无耻|羞耻|耻[于与])"), "耻-情感义不排除"),
        (re.compile(r"(恨[不无其]|可恨|痛恨|深恨|悔恨|抱恨|遗恨|[怨]恨)"), "恨-情感义不排除"),
    ],
    "喜悦/得悟": [
        (re.compile(r"(快乐|快[意活适]|[愉]快|[爽]快|快[些点要]|快[递]|快[然]|快[慰乐感])"), "快-非喜悦义"),
        (re.compile(r"(欣然|欣[赏慰喜]|[欢]欣)"), "欣-情感义不排除"),
    ],
}

emotion_summary = []
for emo_name in EMOTION_PATTERNS:
    edges = [e for e in edge_by_type["MENTIONS_CONCEPT"]
             if any(c.get("name") == emo_name for c in kg["nodes"]["concepts"]
                    if c.get("id") == e["target"])]
    emotion_summary.append((emo_name, len(edges)))

lines.append("  情感维度覆盖量:")
for name, cnt in emotion_summary:
    lines.append(f"    {name:12s}: {cnt:5d} 条")
lines.append("")

# 对每个情感抽 10 条 + 分析假阳性模式
lines.append("  情感假阳性专项检测:")
lines.append("  (标记每条是否为明显非情感用法)")
lines.append("")

for emo_name, _ in emotion_summary:
    edges = [e for e in edge_by_type["MENTIONS_CONCEPT"]
             if any(c.get("name") == emo_name for c in kg["nodes"]["concepts"]
                    if c.get("id") == e["target"])]
    if not edges:
        continue

    # 统计假阳性率
    fp_count = 0
    tp_count = 0
    fp_examples = []
    tp_examples = []

    checks = NON_EMOTION_CONTEXTS.get(emo_name, [])

    for e in edges[:50]:  # 前50条样本
        text = evt_by_id[e["event_id"]].get("raw_text", "")
        is_fp = False
        fp_reason = ""
        for pat, reason in checks:
            if pat.search(text):
                is_fp = True
                fp_reason = reason
                break
        if is_fp:
            fp_count += 1
            if len(fp_examples) < 4:
                fp_examples.append((e["event_id"], text[:100], fp_reason))
        else:
            tp_count += 1
            if len(tp_examples) < 3:
                tp_examples.append((e["event_id"], text[:100]))

    fp_rate = round(fp_count / max(fp_count + tp_count, 1) * 100)
    lines.append(f"  [{emo_name}]")
    lines.append(f"    样本50条: 假阳性 {fp_count} ({fp_rate}%) / 真阳性 {tp_count}")
    lines.append(f"    假阳性样本:")
    for eid, txt, reason in fp_examples:
        lines.append(f"      {eid} [{reason}]: {txt}")
    lines.append(f"    真阳性样本:")
    for eid, txt in tp_examples:
        lines.append(f"      {eid}: {txt}")
    lines.append("")

# ── B. 文本来源层 抽查 ──────────────────────────────────────────────────
lines.append("── B. 文本来源层 抽查 ──")
source_events = {src: [e for e in kg["nodes"]["events"] if e["source_type"] == src]
                 for src in ["HBH自撰", "他人记述", "编者按语", "引用文献"]}
lines.append(f"  分布: HBH自撰={len(source_events['HBH自撰'])}, "
             f"他人={len(source_events['他人记述'])}, "
             f"编者={len(source_events['编者按语'])}, "
             f"引用={len(source_events['引用文献'])}")

# 抽查"他人记述"类——其中有些可能是嵌入式 HBH 引用被误判
others_sample = random.sample(source_events["他人记述"], min(20, len(source_events["他人记述"])))
lines.append("")
lines.append("  '他人记述'类抽查 (检是否有嵌入式HBH自述):")
lines.append("  规则: 文本含'余''仆''鄙人'但没被标为 HBH自撰")
maybe_hbh = 0
for e in others_sample:
    raw = e["raw_text"]
    has_hbh_marker = bool(re.search(r"(余[年月近曾将乃所见作画游居归往]|余曰|余之|余于|仆[近以])", raw))
    flag = " ← 疑为HBH自述" if has_hbh_marker else ""
    if has_hbh_marker:
        maybe_hbh += 1
    lines.append(f"    {e['id']} [{e['year']}]: {raw[:100]}{flag}")
lines.append(f"  疑似被误判为'他人记述'的HBH自述: {maybe_hbh}/{len(others_sample)}")

# 抽查"编者按语"类是否准确
editor_sample = random.sample(source_events["编者按语"], min(10, len(source_events["编者按语"])))
lines.append("")
lines.append("  '编者按语'类抽查:")
editor_ok = 0
for e in editor_sample:
    raw = e["raw_text"]
    is_editor = bool(re.match(r"^(按[：:]|存考[：:]|附记[：:]|拙文|赘语|赘言|王谱|汪谱|赵谱|陈谱|黄警吾|笔者)", raw))
    flag = " ✓" if is_editor else "?疑"
    if is_editor: editor_ok += 1
    lines.append(f"    {e['id']} [{e['year']}]: {raw[:100]}{flag}")
lines.append(f"  准确: {editor_ok}/{len(editor_sample)}")
lines.append("")

# ── C. WROTE_TO 抽样 ────────────────────────────────────────────────────
lines.append("── C. WROTE_TO 通信方向 抽查 ──")
wrote_edges = edge_by_type["WROTE_TO"]
sample_wt = random.sample(wrote_edges, min(20, len(wrote_edges)))
for e in sample_wt:
    src = e["source"]
    tgt = e["target"]
    direction = e["properties"].get("direction", "?")
    evt_text = evt_by_id[e["event_id"]].get("raw_text", "")[:100]
    lines.append(f"  {direction:30s} | {e['event_id']} [{e['year']}] | {evt_text}")
lines.append("")

# ── D. GIFTED_ARTWORK 抽样 ──────────────────────────────────────────────
lines.append("── D. GIFTED_ARTWORK 赠画方向 抽查 ──")
gift_edges = edge_by_type["GIFTED_ARTWORK"]
sample_gf = random.sample(gift_edges, min(15, len(gift_edges)))
for e in sample_gf:
    direction = f"{e['source']} -> {e['target']}"
    evt_text = evt_by_id[e["event_id"]].get("raw_text", "")[:120]
    lines.append(f"  {direction:40s} | {e['event_id']} [{e['year']}]")
    lines.append(f"    {evt_text}")
lines.append("")

# ── E. MOURNED — 为什么只有13条? ──────────────────────────────────────
lines.append("── E. MOURNED 覆盖分析 (为什么只有13条?) ──")
mourn_edges = edge_by_type["MOURNED"]
lines.append(f"  当前 MOURNED 边: {len(mourn_edges)}")
for e in mourn_edges:
    evt_text = evt_by_id[e["event_id"]].get("raw_text", "")[:120]
    lines.append(f"    {e['source']:12s} | {e['event_id']} [{e['year']}] | {evt_text}")

# 直接用更强的正则扫描全部事件，看看漏了多少
broad_mourn = re.compile(r"(病逝|逝世|去世|谢世|卒[于在]|殁[于在]|遽归道山|噩耗|卜告|仙逝|辞世)")
missing_mourn = []
for evt in content_events:
    if evt.get("type") == "year_header":
        continue
    text = evt.get("raw_text", "")
    eid = evt["id"]
    if broad_mourn.search(text):
        # 检查是不是已经在 MOURNED 里
        already = any(e["event_id"] == eid for e in mourn_edges)
        if not already:
            # 找谁去世了
            who = re.search(r"([一-鿿]{2,5})(?:病逝|逝世|去世|谢世|卒|殁|遽归道山)", text)
            name = who.group(1) if who else "未知"
            missing_mourn.append((eid, evt["year"], name, text[:100]))

lines.append("")
lines.append(f"  漏检的逝世事件 (扫描全部5180条): {len(missing_mourn)}")
for eid, yr, name, txt in missing_mourn[:20]:
    lines.append(f"    {eid} [{yr}] {name}: {txt}")
lines.append("")

# ── F. TAUGHT — 为什么只有42条? ──────────────────────────────────────
lines.append("── F. TAUGHT 覆盖分析 (为什么只有42条?) ──")
taught_edges = edge_by_type["TAUGHT"]
lines.append(f"  当前 TAUGHT 边: {len(taught_edges)}")
lines.append(f"  已确认师生对:")
seen_pairs = set()
for e in taught_edges:
    pair = (e["source"], e["target"])
    if pair not in seen_pairs:
        seen_pairs.add(pair)
        lines.append(f"    {e['source']:12s} -> {e['target']:12s} | {e['event_id']} [{e['year']}]")

# 从 persons 里找有"门生""弟子"标记的人，检查在 KG 里有无 TAUGHT 边
with open("hbh_persons.json", encoding="utf-8") as f:
    persons_data = json.load(f)

known_students = []
for p in persons_data:
    bio = " ".join(p.get("bio_snippets", []))
    if re.search(r"(门生|弟子|从学|受业|师事|学于)", bio):
        known_students.append(p["standard_name"])

lines.append("")
lines.append(f"  persons.json 里含'门生/弟子/从学/受业'的已知学生: {len(known_students)}")
for s in known_students[:15]:
    has_edge = any(e["target"] == s for e in taught_edges)
    lines.append(f"    {s:12s} -> 在KG中有TAUGHT边: {'是' if has_edge else '否'}")
lines.append("")

# ── G. 重复边检测 ─────────────────────────────────────────────────────
lines.append("── G. 重复边检测 ──")
edge_keys = []
for e in kg["edges"]:
    edge_keys.append((e["source"], e["target"], e["type"], e["event_id"]))

dup_counts = Counter(edge_keys)
dups = {k: v for k, v in dup_counts.items() if v > 1}
lines.append(f"  完全重复边 (same src+tgt+type+event): {len(dups)}")
for (src, tgt, typ, eid), cnt in list(dups.items())[:10]:
    lines.append(f"    {src} -> {tgt} [{typ}] x{cnt} in {eid}")
lines.append("")

# ── H. 孤立边检测 ─────────────────────────────────────────────────────
lines.append("── H. 整体质量总结 ──")
lines.append(f"  边总数: {len(kg['edges'])}")
lines.append(f"  唯一事件ID数: {len(set(e['event_id'] for e in kg['edges']))}")

# 各关系类型的 event 覆盖
for t in sorted(edge_by_type.keys()):
    unique_evts = len(set(e["event_id"] for e in edge_by_type[t]))
    lines.append(f"  {t:25s}: {len(edge_by_type[t]):5d} 边 / {unique_evts:4d} 唯一事件")

with open("kg_audit_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> kg_audit_report.txt")
