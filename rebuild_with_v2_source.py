# -*- coding: utf-8 -*-
"""Rebuild KG with v2 source layer: strip emotion from non-HBH, add back clean"""
import json, re, os, random
from collections import defaultdict, Counter

os.chdir(r"D:\Desktop\VAST CHALLENGE")

with open("hbh_knowledge_graph.json", encoding="utf-8") as f:
    kg = json.load(f)
with open("hbh_source_layer.json", encoding="utf-8") as f:
    sources = json.load(f)
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

source_by_id = {s["event_id"]: s["source_type"] for s in sources}
content_events = [e for e in events if e.get("type") != "year_header"]
evt_by_id = {e["id"]: e for e in events}

emotion_names = {"喜悦/得悟","愤慨","孤独/坚持","忧虑/焦虑","感恩/眷恋"}
concept_nodes = {c["name"]: c for c in kg["nodes"]["concepts"]}

# ── Step 1: Strip ALL emotion edges ──────────────────────────────────
stripped = 0
clean = []
for e in kg["edges"]:
    if e["type"] == "MENTIONS_CONCEPT":
        cnode = None
        for c in kg["nodes"]["concepts"]:
            if c["id"] == e["target"]:
                cnode = c; break
        if cnode and cnode["name"] in emotion_names:
            stripped += 1
            continue
    clean.append(e)

print(f"Stripped {stripped} old emotion edges")

# ── Step 2: Add emotion edges ONLY to verified HBH自撰 ───────────────
EMOTIONS = {
    "喜悦/得悟": re.compile(r"(喜|乐|欣然|会心|大悟|大笑|豁然|悦|畅然|忘倦|神来|兴会|得趣|称快)"),
    "愤慨":     re.compile(r"(愤然|怒斥|痛恨|深恨|深恶|耻笑|鄙夷|嗟叹|忧愤|痛心|扼腕|可恨)"),
    "孤独/坚持": re.compile(r"(寂寥|寥落|枯坐|默坐|独居|守拙|耐得住|孤寂|匹夫|独自|坚守)"),
    "忧虑/焦虑": re.compile(r"(忧心|惶然|恐惧|急迫|窘困|束手|为难|迫在眉睫|恐难|抱恙)"),
    "感恩/眷恋": re.compile(r"(感念不忘|谢恩|幸甚|眷恋|忆昔|思之不禁|念及|怀想|故乡)"),
}

added_emotion = 0
for evt in content_events:
    eid = evt["id"]
    if source_by_id.get(eid) != "HBH自撰":
        continue
    text = evt["raw_text"]
    year = evt["year"]
    for ename, pat in EMOTIONS.items():
        if pat.search(text) and ename in concept_nodes:
            clean.append({
                "id": f"ev2_{added_emotion:05d}",
                "source": eid, "target": concept_nodes[ename]["id"],
                "type": "MENTIONS_CONCEPT",
                "year": year, "event_id": eid,
                "properties": {"via": "source_v2_emotion"}})
            added_emotion += 1

print(f"Added {added_emotion} emotion edges (HBH自撰 only)")

# ── Step 3: Add core concept edges to ALL events ────────────────────
CORE_REGEXES = {
    "内美":     re.compile(r"(内美|内在美|蕴藉|含蓄)"),
    "浑厚华滋": re.compile(r"(浑厚华滋|浑厚|华滋|雄浑)"),
    "道咸中兴": re.compile(r"(道咸中兴|道咸间|道咸画家|道咸名贤|金石家画)"),
    "南北宗":   re.compile(r"(南北宗|南宗|北宗|董其昌|莫是龙)"),
    "师造化":   re.compile(r"(师造化|外师造化|中得心源|师法自然|造化为师)"),
    "师古人":   re.compile(r"(师古人|师古|临古|摹古|法古|拟古)"),
    "气韵生动": re.compile(r"(气韵|气韵生动|韵致)"),
    "骨法用笔": re.compile(r"(骨法用笔|骨法|风骨)"),
    "书画同源": re.compile(r"(书画同源|以书入画|书法用笔|书画相通)"),
    "逸品":     re.compile(r"(逸品|神品|妙品|能品|上品)"),
    "文人画":   re.compile(r"(文人画|士夫画|士人画)"),
    "雅俗":     re.compile(r"(雅俗|甜俗|市井画|江湖画|朝市画|去俗|免俗)"),
    "虚实":     re.compile(r"(虚实|虚处|实处|虚中实|实中虚)"),
    "笔墨":     re.compile(r"(笔墨|笔情墨趣|笔苍墨润|笔歌墨舞)"),
    "写生":     re.compile(r"(写生|实景|真山水|对景写生)"),
    "简笔":     re.compile(r"(简笔|减笔|简约|简淡|简远)"),
    "不似之似": re.compile(r"(不似之似|似与不似|绝不似而极似)"),
    "五笔七墨": re.compile(r"(五笔七墨|七墨|五笔法)"),
    "民学":     re.compile(r"(民学|君学|民物|民彝)"),
    "真迹鉴别": re.compile(r"(真迹|伪作|赝品|摹本|仿本|代笔)"),
}
INK_METHODS_LIST = ["浓墨","淡墨","破墨","泼墨","积墨","焦墨","宿墨"]
BRUSH_METHODS_LIST = ["中锋","侧锋","逆锋","顺锋","平笔","圆笔","留笔","重笔","变笔"]

existing_concept_eids = {e["event_id"] for e in clean if e["type"] == "MENTIONS_CONCEPT"}
added_core = 0
for evt in content_events:
    text = evt["raw_text"]
    year = evt["year"]
    eid  = evt["id"]
    for cname, pat in CORE_REGEXES.items():
        if pat.search(text) and cname in concept_nodes:
            clean.append({
                "id": f"cv2_{added_core:05d}",
                "source": eid, "target": concept_nodes[cname]["id"],
                "type": "MENTIONS_CONCEPT",
                "year": year, "event_id": eid, "properties": {"via": "source_v2"}})
            added_core += 1
    for m in INK_METHODS_LIST + BRUSH_METHODS_LIST:
        if m in text and m in concept_nodes:
            clean.append({
                "id": f"iv2_{added_core:05d}",
                "source": eid, "target": concept_nodes[m]["id"],
                "type": "MENTIONS_CONCEPT",
                "year": year, "event_id": eid, "properties": {"via": "source_v2_ink"}})
            added_core += 1

print(f"Added {added_core} core concept edges")

# ── Dedup ──────────────────────────────────────────────────────────
seen = set()
deduped = []
for e in clean:
    k = (e["source"], e["target"], e["type"], e["event_id"])
    if k in seen: continue
    seen.add(k)
    deduped.append(e)

# ── Save ───────────────────────────────────────────────────────────
new_kg = {"meta": {**kg["meta"], "total_edges": len(deduped), "source": "v2"},
          "nodes": kg["nodes"], "edges": deduped}
with open("hbh_knowledge_graph.json","w",encoding="utf-8") as f:
    json.dump(new_kg,f,ensure_ascii=False,indent=2)

# ── F1 ─────────────────────────────────────────────────────────────
random.seed(42)
sample = random.sample(content_events, 150)

L2 = re.compile(
    r"([一-鿿]{2,5}(?:致|与|寄|复|覆|答)[一-鿿]{2,5}(?:书|函|信|札|尺牍|手翰|手启|公启|手书|信函|书札))|"
    r"(^[一-鿿]{2,5}[书函][：:])|(与[一-鿿]{2,5}[书函信][：:])"
)
C2 = re.compile(
    r"([作为画绘写]《|为.{1,6}[作为画绘写].{0,15}[图册轴帧幅卷屏景]|"
    r"写生[山水花人]|临[摹写仿习]|自题[：:。，]|"
    r"作山水|作大幅|作花卉|作人物|作[松竹梅菊荷]|"
    r"题跋[《]|作[画绘]《|绘《|画《[^》]{1,30}[图册轴]》)"
)
G2 = re.compile(
    r"([赠贻惠持寄][赠予遗献送交呈给].{0,10}[画图册轴帧幅卷屏]|"
    r"[画图册轴帧幅卷屏].{0,10}[赠贻惠持寄][赠予遗献送交呈给]|"
    r"见赠|持赠|惠赠|遗赠|[赠贻][一-鿿]{2,4}[画图册轴]|"
    r"写.{1,10}见赠|画.{1,10}见赠|索画[一-鿿]{2,4}|嘱画[一-鿿]{2,4}|属画[一-鿿]{2,4})"
)
E2 = re.compile(r"(展览|画展|陈列|参展|出品|雅集|社集|书画会|同人展|联展|纪念展)")
H2 = re.compile(r"(黄宾虹|宾虹|宾老|朴存|谱主|滨虹)")
M2 = re.compile(r"(病逝|逝世|去世|谢世|殁[于在]|遽归道山|追悼会|公祭|噩耗|仙逝|辞世)")

eid_edges = defaultdict(set)
for e in deduped:
    eid_edges[e["event_id"]].add(e["type"])

tp=fp=fn=0
st=defaultdict(lambda:{"tp":0,"fp":0,"fn":0})
for evt in sample:
    t=evt["raw_text"]; eid=evt["id"]; act=eid_edges.get(eid,set())
    for rel,ok in [
        ("WROTE_TO",bool(L2.search(t))),
        ("CREATED",bool(C2.search(t))),
        ("EXHIBITED_AT",bool(E2.search(t) and H2.search(t))),
        ("MOURNED",bool(M2.search(t))),
        ("GIFTED_ARTWORK",bool(G2.search(t)))]:
        ie=ok; ia=rel in act
        if ie and ia: st[rel]["tp"]+=1; tp+=1
        elif ia: st[rel]["fp"]+=1; fp+=1
        elif ie: st[rel]["fn"]+=1; fn+=1

p=tp/max(tp+fp,1)*100; r=tp/max(tp+fn,1)*100; f1=2*p*r/max(p+r,0.1)

et = Counter(e["type"] for e in deduped)
print(f"\nEdges: {len(deduped)}  F1: {f1:.1f}% (P={p:.1f}% R={r:.1f}%)")
for rel in sorted(st):
    s=st[rel]
    print(f"  {rel:22s} P={s['tp']/max(s['tp']+s['fp'],1)*100:5.1f}% R={s['tp']/max(s['tp']+s['fn'],1)*100:5.1f}%")
print(f"\nEdge dist: {dict(et.most_common())}")
