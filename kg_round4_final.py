# -*- coding: utf-8 -*-
"""KG Round 4: final precision pass"""
import json, re, os, random
from collections import defaultdict

os.chdir(r"D:\Desktop\VAST CHALLENGE")

with open("hbh_knowledge_graph.json", encoding="utf-8") as f:
    kg = json.load(f)
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

evt_by_id = {e["id"]: e for e in events}
content_events = [e for e in events if e.get("type") != "year_header"]

# Clean: remove edges on clearly wrong events
# 1. Remove emotion concept edges from non-HBH text
#    (events where the text starts with another person's letter pattern)
NON_HBH_LETTER = re.compile(r"^([一-鿿]{2,5})[书函][：:]")
emotion_names = {"喜悦/得悟","愤慨","孤独/坚持","忧虑/焦虑","感恩/眷恋"}
removed_emotion_fp = 0
removed_mourn_fp = 0
removed_gift_fp = 0

clean_edges = []
for e in kg["edges"]:
    eid = e["event_id"]
    evt = evt_by_id.get(eid)
    text = evt.get("raw_text","") if evt else ""

    # Check: emotion concept on non-HBH events
    if e["type"] == "MENTIONS_CONCEPT":
        cnode = None
        for c in kg["nodes"]["concepts"]:
            if c["id"] == e["target"]:
                cnode = c; break
        if cnode and cnode["name"] in emotion_names:
            # Emotions should only be on HBH self-text
            m = NON_HBH_LETTER.match(text)
            if m and m.group(1) not in {"黄宾虹","宾虹","朴存","滨虹","谱主"}:
                removed_emotion_fp += 1
                continue  # skip this edge

    # Check: MOURNED on wrong events (e.g., "追悼会" as art society name)
    if e["type"] == "MOURNED":
        if re.search(r"(追悼会.*展览|纪念会.*画展|追悼.*书画)", text):
            removed_mourn_fp += 1
            continue

    # Check: GIFTED_ARTWORK on events that are just poetry about gifting
    if e["type"] == "GIFTED_ARTWORK":
        if e["source"] not in {"黄宾虹","宾虹","朴存"} or \
           e["target"] in {"佚名","未识别","某","舍弟","家大人"}:
            removed_gift_fp += 1
            continue

    clean_edges.append(e)

print(f"Removed: emotion_FP={removed_emotion_fp} mourn_FP={removed_mourn_fp} gift_FP={removed_gift_fp}")

# 2. Add missing WROTE_TO edges (2 FNs from audit)
aug_wrote = 0
LETTER_RE = re.compile(r"([一-鿿]{2,5})(?:致|与|寄|复|覆)([一-鿿]{2,5})(?:书|函|信|札|尺牍|手翰|手札)")
for evt in content_events:
    text = evt.get("raw_text","")
    eid = evt["id"]
    year = evt["year"]
    # skip if WROTE_TO already exists for this event
    if any(e["event_id"]==eid and e["type"]=="WROTE_TO" for e in clean_edges):
        continue
    m = LETTER_RE.search(text)
    if not m: continue
    src, tgt = m.group(1), m.group(2)
    if src == tgt: continue
    clean_edges.append({
        "id":f"e4w_{aug_wrote:04d}","source":src,"target":tgt,
        "type":"WROTE_TO","year":year,"event_id":eid,
        "properties":{"direction":f"{src}->{tgt}","via":"r4"}})
    aug_wrote += 1

print(f"WROTE_TO +{aug_wrote}")

# Update KG
new_kg = {"meta":{**kg["meta"],"total_edges":len(clean_edges),"round":4},
          "nodes":kg["nodes"],"edges":clean_edges}
with open("hbh_knowledge_graph.json","w",encoding="utf-8") as f:
    json.dump(new_kg,f,ensure_ascii=False,indent=2)

# Final audit
random.seed(42)
sample = random.sample(content_events, 150)

L_PAT = re.compile(r"([一-鿿]{2,5}(?:致|与|寄|复|覆)[一-鿿]{2,5}(?:书|函|信|札)|^[一-鿿]{2,5}[书函][：:])")
C_PAT = re.compile(r"([作画绘]《|[作画绘写][山水花人梅]|册页[0-9]|大幅|题跋[《]|篆刻[印]|临[帖池摹])")
E_PAT = re.compile(r"(展览|画展|陈列|参展|出品|雅集|社集|书画会)")
M_PAT = re.compile(r"(病逝|逝世|去世|谢世|殁[于在]|追悼会|公祭)")
G_PAT = re.compile(r"([赠贻惠持寄][赠予遗献送交呈给].{0,15}[画图册轴帧幅卷屏])")

edges_by_eid = defaultdict(set)
for e in clean_edges:
    edges_by_eid[e["event_id"]].add(e["type"])

tp=fp=fn=0
stats = defaultdict(lambda:{"tp":0,"fp":0,"fn":0})
for evt in sample:
    t = evt["raw_text"]
    eid = evt["id"]
    act = edges_by_eid.get(eid,set())
    checks = {
        "WROTE_TO": L_PAT.search(t),
        "CREATED": C_PAT.search(t),
        "EXHIBITED_AT": E_PAT.search(t) and bool(re.search(r"(黄宾虹|宾虹|宾老|朴存|谱主)",t)),
        "MOURNED": M_PAT.search(t),
        "GIFTED_ARTWORK": G_PAT.search(t),
    }
    for rel, ok in checks.items():
        ie=bool(ok); ia=rel in act
        if ie and ia: stats[rel]["tp"]+=1; tp+=1
        elif ia: stats[rel]["fp"]+=1; fp+=1
        elif ie: stats[rel]["fn"]+=1; fn+=1

# Also count concept coverage
mc_eids = {e["event_id"] for e in clean_edges if e["type"]=="MENTIONS_CONCEPT"}
tt_eids = {e["event_id"] for e in clean_edges if e["type"]=="TRAVELED_TO"}
all_eids = {e["id"] for e in content_events}

p = tp/max(tp+fp,1)*100
r = tp/max(tp+fn,1)*100
f1 = 2*p*r/max(p+r,0.1)

lines = []
lines.append("="*50)
lines.append("  KG Round 4 FINAL")
lines.append("="*50)
lines.append(f"  Edges: {len(clean_edges)}")
lines.append(f"  Emotion FP removed: {removed_emotion_fp}")
lines.append(f"  MOURNED FP removed: {removed_mourn_fp}")
lines.append(f"  GIFTED FP removed: {removed_gift_fp}")
lines.append(f"  WROTE_TO added: {aug_wrote}")
lines.append("")
lines.append(f"  === Subset F1 (reliably-testable relations, n=150) ===")
lines.append(f"  Precision: {p:.1f}%")
lines.append(f"  Recall:    {r:.1f}%")
lines.append(f"  F1:        {f1:.1f}%")
lines.append("")
for rel in sorted(stats):
    s=stats[rel]
    pr=s["tp"]/max(s["tp"]+s["fp"],1)*100
    rr=s["tp"]/max(s["tp"]+s["fn"],1)*100
    lines.append(f"  {rel:20s} P:{pr:5.1f}% R:{rr:5.1f}% tp={s['tp']} fp={s['fp']} fn={s['fn']}")
lines.append("")
lines.append(f"  === Coverage ===")
lines.append(f"  Events with >=1 edge: {len(set(e['event_id'] for e in clean_edges))}/{len(all_eids)} ({len(set(e['event_id'] for e in clean_edges))/len(all_eids)*100:.1f}%)")
lines.append(f"  MENTIONS_CONCEPT:     {len(mc_eids)} events ({len(mc_eids)/len(all_eids)*100:.1f}%)")
lines.append(f"  TRAVELED_TO:          {len(tt_eids)} events ({len(tt_eids)/len(all_eids)*100:.1f}%)")
lines.append("")
lines.append(f"  === Combined Quality Score ===")
# Overall: average of subset F1 and concept/travel coverage ratio
cov = (len(mc_eids) + len(tt_eids)) / (2*len(all_eids))
quality = f1 * 0.6 + cov * 100 * 0.4
lines.append(f"  Quality = F1*0.6 + Coverage*0.4 = {f1:.1f}*0.6 + {cov*100:.1f}*0.4 = {quality:.1f}")

with open("kg_round4_report.txt","w",encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))
