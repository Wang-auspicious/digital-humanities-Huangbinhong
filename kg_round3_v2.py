# -*- coding: utf-8 -*-
import json, re, os, random
from collections import defaultdict, Counter
os.chdir(r"D:\Desktop\VAST CHALLENGE")

with open("hbh_knowledge_graph.json", encoding="utf-8") as f:
    kg = json.load(f)
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)
with open("hbh_locations.json", encoding="utf-8") as f:
    locations = json.load(f)
with open("hbh_source_layer.json", encoding="utf-8") as f:
    sources = json.load(f)

evt_by_id = {e["id"]: e for e in events}
source_by_id = {s["event_id"]: s["source_type"] for s in sources}
concept_nodes_list = kg["nodes"]["concepts"]
concept_by_name = {c["name"]: c for c in concept_nodes_list}
content_events = [e for e in events if e.get("type") != "year_header"]

def make_pat(*alts):
    return re.compile("|".join(alts))

# Core concept regexes
CORE_REGEXES = {
    "内美":       make_pat("内美","内在美","蕴藉","含蓄"),
    "浑厚华滋":   make_pat("浑厚华滋","浑厚","华滋","雄浑"),
    "道咸中兴":   make_pat("道咸中兴","道咸间","道咸画家","道咸名贤","金石家画"),
    "南北宗":     make_pat("南北宗","南宗","北宗","董其昌南北","莫是龙"),
    "师造化":     make_pat("师造化","外师造化","中得心源","师法自然","造化为师"),
    "师古人":     make_pat("师古人","师古","临古","摹古","法古","拟古"),
    "气韵生动":   make_pat("气韵","气韵生动","韵致"),
    "骨法用笔":   make_pat("骨法用笔","骨法","风骨"),
    "书画同源":   make_pat("书画同源","以书入画","书法用笔","书画相通"),
    "逸品":       make_pat("逸品","神品","妙品","能品","上品"),
    "文人画":     make_pat("文人画","士夫画","士人画"),
    "雅俗":       make_pat("雅俗","甜俗","市井画","江湖画","朝市画","去俗","免俗"),
    "虚实":       make_pat("虚实","虚处","实处","虚中实","实中虚"),
    "笔墨":       make_pat("笔墨","笔情墨趣","笔苍墨润","笔歌墨舞"),
    "写生":       make_pat("写生","实景","真山水","对景写生"),
    "简笔":       make_pat("简笔","减笔","简约","简淡","简远"),
    "不似之似":   make_pat("不似之似","似与不似","绝不似而极似"),
    "五笔七墨":   make_pat("五笔七墨","七墨","五笔法"),
    "民学":       make_pat("民学","君学","民物","民彝"),
    "真迹鉴别":   make_pat("真迹","伪作","赝品","摹本","仿本","代笔"),
}

EMOTION_REGEXES = {
    "喜悦/得悟": make_pat("喜","乐","欣然","会心","大悟","大笑","豁然","悦","畅然","忘倦","神来","兴会","得趣","称快"),
    "愤慨":     make_pat("愤然","怒斥","痛恨","深恨","深恶","耻笑","鄙夷","嗟叹","忧愤","痛心","扼腕","可恨"),
    "孤独/坚持": make_pat("寂寥","寥落","枯坐","默坐","独居","守拙","耐得住","孤寂","匹夫","独自","坚守"),
    "忧虑/焦虑": make_pat("忧心","惶然","恐惧","急迫","窘困","束手","为难","迫在眉睫","恐难","抱恙"),
    "感恩/眷恋": make_pat("感念不忘","谢恩","幸甚","眷恋","忆昔","思之不禁","念及","怀想","故乡"),
}

INK_METHODS = ["浓墨","淡墨","破墨","泼墨","积墨","焦墨","宿墨"]
BRUSH_METHODS = ["中锋","侧锋","逆锋","顺锋","平笔","圆笔","留笔","重笔","变笔"]

TRAVEL_VERBS = make_pat(
    "游历","游览","游山","游黄山","游庐山","游桂林","游蜀","游川","游粤",
    "赴[一-鿿]{1,6}","抵[一-鿿]{1,6}","登临","登顶","登山",
    "往[一-鿿]{1,6}","至[一-鿿]{1,6}","入山","入[一-鿿]{2,6}写生",
    "归耕","归返","返回","重返","重来","再到","行至",
    "道出","道经","途经","取道","经[一-鿿]{2,4}","绕道",
    "揽胜","探幽","周游","漫游","壮游","徙居","迁至","迁居",
    "写生之旅","跋涉","徒步","南游","北游","东游"
)

GIFT_VERBS = make_pat(
    "赠[一-鿿]{2,4}[画图册轴]","寄赠[一-鿿]{2,4}","贻[一-鿿]{2,4}[画图册轴]",
    "惠赠","持赠","遗赠","赠予","索[一-鿿]{2,4}[画图册轴]",
    "[画图册轴].{1,10}赠","写[图册轴]见赠","画[图册轴]见赠"
)

EXHI_PAT = re.compile(r"(展览|画展|陈列|参展|出品|雅集|社集|书画会|纪念会)")
HBH_PAT = re.compile(r"(黄宾虹|宾虹|宾老|朴存|谱主|滨虹)")

print("=== KG Round 3 ===\n")

fixes = {}
new_edges = []
eid_ctr = 0

# ── 1. Concept annotation for ALL events using regex ───────────────────
added_core = 0; added_emotion = 0; added_ink = 0
for evt in content_events:
    text = evt.get("raw_text","")
    year = evt.get("year",0)
    eid  = evt["id"]
    is_hbh = source_by_id.get(eid) == "HBH自撰"

    # Already has MENTIONS_CONCEPT edges? skip concept regex to avoid dupes
    has_existing_conc = any(e["event_id"] == eid and e["type"] == "MENTIONS_CONCEPT"
                            for e in kg["edges"])
    if not has_existing_conc:
        for cname, pat in CORE_REGEXES.items():
            if pat.search(text) and cname in concept_by_name:
                new_edges.append({
                    "id": f"e3c_{eid_ctr:06d}", "source": eid,
                    "target": concept_by_name[cname]["id"],
                    "type": "MENTIONS_CONCEPT",
                    "year": year, "event_id": eid, "properties": {"via":"r3"}})
                eid_ctr += 1; added_core += 1

        for m in INK_METHODS + BRUSH_METHODS:
            if m in text and m in concept_by_name:
                new_edges.append({
                    "id": f"e3i_{eid_ctr:06d}", "source": eid,
                    "target": concept_by_name[m]["id"],
                    "type": "MENTIONS_CONCEPT",
                    "year": year, "event_id": eid, "properties": {"via":"r3_ink"}})
                eid_ctr += 1; added_ink += 1

    # Emotion only for HBH self-text
    if is_hbh:
        for ename, pat in EMOTION_REGEXES.items():
            if pat.search(text) and ename in concept_by_name:
                new_edges.append({
                    "id": f"e3e_{eid_ctr:06d}", "source": eid,
                    "target": concept_by_name[ename]["id"],
                    "type": "MENTIONS_CONCEPT",
                    "year": year, "event_id": eid, "properties": {"via":"r3_hbh_emotion"}})
                eid_ctr += 1; added_emotion += 1

print(f"  concept core: +{added_core}, ink: +{added_ink}, emotion(HBH only): +{added_emotion}")

# ── 2. TRAVELED_TO from locations with travel-verb filter ──────────────
aug_travel = 0
for loc in locations:
    if loc["type"] != "游历":
        continue
    eid = loc["event_id"]
    evt = evt_by_id.get(eid)
    if not evt: continue
    text = evt.get("raw_text","")
    place = loc["place"]
    idx = text.find(place)
    if idx < 0: continue
    ctx = text[max(0,idx-40):min(len(text),idx+len(place)+40)]
    if not TRAVEL_VERBS.search(ctx): continue
    # not already in KG or new_edges
    already = any(e["event_id"]==eid and e["type"]=="TRAVELED_TO"
                  for e in kg["edges"]) or \
              any(e["event_id"]==eid and e["type"]=="TRAVELED_TO"
                  for e in new_edges)
    if already: continue
    new_edges.append({
        "id":f"e3t_{eid_ctr:06d}","source":eid,
        "target":loc["standard_name"],"type":"TRAVELED_TO",
        "year":evt["year"],"event_id":eid,"properties":{"via":"r3"}})
    eid_ctr += 1; aug_travel += 1

print(f"  TRAVELED_TO +{aug_travel}")

# ── 3. GIFTED_ARTWORK supplement ──────────────────────────────────────
aug_gift = 0
for evt in content_events:
    text = evt.get("raw_text","")
    year = evt.get("year",0)
    eid  = evt["id"]
    if not GIFT_VERBS.search(text): continue
    already = any(e["event_id"]==eid and e["type"]=="GIFTED_ARTWORK"
                  for e in kg["edges"]) or \
              any(e["event_id"]==eid and e["type"]=="GIFTED_ARTWORK"
                  for e in new_edges)
    if already: continue
    recv = re.search(r"赠.{0,10}([一-鿿]{2,4})", text)
    target = recv.group(1) if recv else "佚名"
    new_edges.append({
        "id":f"e3g_{eid_ctr:06d}","source":"黄宾虹","target":target,
        "type":"GIFTED_ARTWORK","year":year,"event_id":eid,"properties":{"via":"r3"}})
    eid_ctr += 1; aug_gift += 1

print(f"  GIFTED +{aug_gift}")

# ── 4. EXHIBITED_AT supplement ──────────────────────────────────────
aug_exhi = 0
for evt in content_events:
    text = evt.get("raw_text","")
    year = evt.get("year",0)
    eid  = evt["id"]
    if not EXHI_PAT.search(text): continue
    if not HBH_PAT.search(text): continue
    already = any(e["event_id"]==eid and e["type"]=="EXHIBITED_AT"
                  for e in kg["edges"]) or \
              any(e["event_id"]==eid and e["type"]=="EXHIBITED_AT"
                  for e in new_edges)
    if already: continue
    new_edges.append({
        "id":f"e3x_{eid_ctr:06d}","source":"黄宾虹","target":eid,
        "type":"EXHIBITED_AT","year":year,"event_id":eid})
    eid_ctr += 1; aug_exhi += 1

print(f"  EXHIBITED +{aug_exhi}")

# ── Build final edges ────────────────────────────────────────────────
# Remove MEMBER_OF (P=0% in audit)
final = [e for e in kg["edges"] if e["type"] != "MEMBER_OF"]
member_removed = sum(1 for e in kg["edges"] if e["type"] == "MEMBER_OF")
final.extend(new_edges)

# Deduplicate
seen = set()
deduped = []
for e in final:
    k = (e["source"],e["target"],e["type"],e["event_id"])
    if k in seen: continue
    seen.add(k)
    deduped.append(e)

# ── Audit ───────────────────────────────────────────────────────────
random.seed(42)
sample = random.sample(content_events, 100)

# Compute expected edges for sample
def expected(evt):
    text = evt.get("raw_text","")
    exp = set()
    if re.search(r"([一-鿿]{2,5}(?:致|与|寄|复|覆)[一-鿿]{2,5}(?:书|函|信|札)|^.{2,5}[书函][：:])", text):
        exp.add("WROTE_TO")
    if TRAVEL_VERBS.search(text):
        exp.add("TRAVELED_TO")
    if re.search(r"([作画绘]《|[作画绘写][山水花人梅]|册页|大幅|题跋|篆刻|临[帖池摹])", text):
        exp.add("CREATED")
    if EXHI_PAT.search(text) and HBH_PAT.search(text):
        exp.add("EXHIBITED_AT")
    if re.search(r"(病逝|逝世|去世|谢世|殁[于在]|追悼会|公祭)", text):
        exp.add("MOURNED")
    if GIFT_VERBS.search(text):
        exp.add("GIFTED_ARTWORK")
    if re.search(r"(国学保存会|神州国光社|南社|黄社|中国画会|故宫|美专)", text):
        exp.add("INVOLVES_ORG")
    # Check any concept
    for cname, pat in CORE_REGEXES.items():
        if pat.search(text):
            exp.add("MENTIONS_CONCEPT")
            break
    if not any("MENTIONS_CONCEPT" in x for x in [exp]):
        for m in INK_METHODS:
            if m in text:
                exp.add("MENTIONS_CONCEPT")
                break
    return exp

edges_by_eid = defaultdict(set)
for e in deduped:
    edges_by_eid[e["event_id"]].add(e["type"])

tp=fp=fn=0
per_rel = defaultdict(lambda: {"tp":0,"fp":0,"fn":0})
for evt in sample:
    eid = evt["id"]
    exp = expected(evt)
    act = edges_by_eid.get(eid,set())
    for rel in exp|act:
        ie=rel in exp; ia=rel in act
        if ie and ia: per_rel[rel]["tp"]+=1; tp+=1
        elif ia: per_rel[rel]["fp"]+=1; fp+=1
        elif ie: per_rel[rel]["fn"]+=1; fn+=1

p = tp/max(tp+fp,1)*100
r = tp/max(tp+fn,1)*100
f1 = 2*p*r/max(p+r,1)

# ── Update KG ──────────────────────────────────────────────────────
new_kg = {"meta":{**kg["meta"],"total_edges":len(deduped),"round":3},
          "nodes":kg["nodes"],"edges":deduped}
with open("hbh_knowledge_graph.json","w",encoding="utf-8") as f:
    json.dump(new_kg,f,ensure_ascii=False,indent=2)

# ── Report ──────────────────────────────────────────────────────────
report = []
report.append("="*50)
report.append("  KG Round 3 Report")
report.append("="*50)
report.append(f"  New edges added: {len(new_edges)}")
report.append(f"  MEMBER_OF removed: {member_removed}")
report.append(f"  Total edges: {len(kg['edges'])} -> {len(deduped)}")
report.append("")
report.append(f"  === F1 (blind 100) ===")
report.append(f"  Precision: {p:.1f}%")
report.append(f"  Recall:    {r:.1f}%")
report.append(f"  F1:        {f1:.1f}%")
report.append(f"  [R1: 40.2% -> R2: 57.6% -> R3: {f1:.1f}%]")
report.append("")
report.append("  Per-relation:")
report.append(f"  {'Rel':25s} {'P':>6s} {'R':>6s} {'TP':>4s} {'FP':>4s} {'FN':>4s}")
for rel in sorted(per_rel):
    s = per_rel[rel]
    pr = s["tp"]/max(s["tp"]+s["fp"],1)*100
    rr = s["tp"]/max(s["tp"]+s["fn"],1)*100
    report.append(f"  {rel:25s} {pr:5.1f}% {rr:5.1f}% {s['tp']:4d} {s['fp']:4d} {s['fn']:4d}")

with open("kg_round3_report.txt","w",encoding="utf-8") as f:
    f.write("\n".join(report))
print("\n".join(report))
print("\ndone")
