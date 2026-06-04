# -*- coding: utf-8 -*-
"""
黄宾虹知识图谱构建脚本
========================
输出: hbh_knowledge_graph.json

Schema:
  Node types: Event, Person, Place, Artwork, Concept, Organization, TimePeriod
  Edge types: 17 种关系（见 RELATION_DEFS）
  Source layer: 每条事件标记 who_is_speaking（HBH自撰/他人记述/编者按语/引用文献）
"""

import json, re, os
from collections import defaultdict, Counter

os.chdir(r"D:\Desktop\VAST CHALLENGE")

# ── 0. 加载全部现有数据 ────────────────────────────────────────────────────
print("Loading existing data...")
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)
with open("alias_map.json", encoding="utf-8") as f:
    alias_map = json.load(f)
with open("hbh_persons.json", encoding="utf-8") as f:
    persons = json.load(f)
with open("hbh_locations.json", encoding="utf-8") as f:
    locations = json.load(f)
with open("hbh_creations.json", encoding="utf-8") as f:
    creations = json.load(f)
with open("hbh_topics.json", encoding="utf-8") as f:
    topics = json.load(f)

content_events = [e for e in events if e.get("type") != "year_header"]
evt_by_id = {e["id"]: e for e in events}
topic_by_id = {t["event_id"]: t for t in topics}

# 人物索引：别名 → 标准名
alias_to_std = {}
for std, aliases in alias_map.items():
    for a in aliases:
        alias_to_std[a] = std
    alias_to_std[std] = std  # 标准名也映射到自己

print(f"  events: {len(content_events)}  persons: {len(persons)}  "
      f"locations: {len(locations)}  creations: {len(creations)}  topics: {len(topics)}")

# ── 1. 文本来源层识别 (地基) ──────────────────────────────────────────────
HBH_SELF_PATTERNS = [
    re.compile(r"(余[年月近曾尝将乃所见作画游居归往致与购置题书]|余因|余曰|余之|余于|余在|余自|余以|余为|余尝|余每|余素|余力|余时|余少)"),
    re.compile(r"(仆[近以见作在]|鄙人|拙[笔画著稿]|贱[目恙]|谱主)"),
    re.compile(r"^(黄宾虹|宾虹|朴存|滨虹|宾老)[：:。，]"),
    re.compile(r"(与[A-Za-z一-鿿]{2,8}[书函信]|致[A-Za-z一-鿿]{2,8}[书函信]|覆[A-Za-z一-鿿]{2,8}[书函信])[：:]"),
    re.compile(r"自题[：:。，]"),
    re.compile(r"《自撰年谱》"),
    re.compile(r"《九十杂述》|《八十自述》|《八十感言》|口述事略"),
]

EDITOR_PATTERNS = [
    re.compile(r"^(按[：:]|存考[：:]|附记[：:])"),
    re.compile(r"^(拙文|赘语|赘言)"),
    re.compile(r"笔者[：:曾随]"),
    re.compile(r"^(王谱|汪谱|赵谱|陈谱|黄警吾)"),
]

CITATION_PATTERNS = [
    re.compile(r"^(录自|摘自|引自|据《|见《|参见《)"),
    re.compile(r"《[^》]{1,20}》[：:][「“]"),
]

PERSON_LETTER_PATTERNS = [
    re.compile(r"^([一-鿿]{2,4}[书函][：:])"),
    re.compile(r"^([一-鿿]{2,4}与[一-鿿]{2,4}[书函][：:])"),
]

def classify_source(evt):
    text = evt.get("raw_text", "").strip()
    if not text:
        return "未知"

    # 编者按语优先判断（即使含有HBH名字，编者添加的注释仍是编者声音）
    for pat in EDITOR_PATTERNS:
        if pat.match(text):
            return "编者按语"
    for pat in CITATION_PATTERNS:
        if pat.match(text):
            return "引用文献"

    # HBH 自撰
    for pat in HBH_SELF_PATTERNS:
        if pat.search(text):
            return "HBH自撰"

    # 他人来信
    for pat in PERSON_LETTER_PATTERNS:
        if pat.match(text):
            return "他人记述"

    # 默认：他人记述（年谱引用的第三方材料）
    return "他人记述"

source_counts = Counter()
for evt in content_events:
    src = classify_source(evt)
    evt["source_type"] = src  # 挂回原始事件
    source_counts[src] += 1

print("\n── 文本来源层分布 ──")
for s, c in source_counts.most_common():
    print(f"  {s}: {c} ({round(c/len(content_events)*100,1)}%)")

# ── 2. 画学概念词典 ────────────────────────────────────────────────────────
# 手工构建，覆盖黄宾虹全部核心概念

INK_METHODS = ["浓墨","淡墨","破墨","泼墨","积墨","焦墨","宿墨"]
BRUSH_METHODS = ["平笔","圆笔","留笔","重笔","变笔","中锋","侧锋","逆锋","顺锋"]
CORE_CONCEPTS = {
    "内美":           re.compile(r"(内美|内在美|蕴藉|含蓄)"),
    "浑厚华滋":       re.compile(r"(浑厚华滋|浑厚|华滋|雄浑)"),
    "道咸中兴":       re.compile(r"(道咸中兴|道咸间|道咸画家|道咸名贤|金石家画)"),
    "南北宗":         re.compile(r"(南北宗|南宗|北宗|董其昌|莫是龙)"),
    "师造化":         re.compile(r"(师造化|外师造化|中得心源|师法自然|造化为师)"),
    "师古人":         re.compile(r"(师古人|师古|临古|摹古|法古|拟古)"),
    "气韵生动":       re.compile(r"(气韵|气韵生动|韵致)"),
    "骨法用笔":       re.compile(r"(骨法用笔|骨法|风骨)"),
    "书画同源":       re.compile(r"(书画同源|以书入画|书法用笔|书与画)"),
    "逸品":           re.compile(r"(逸品|神品|妙品|能品|上品)"),
    "文人画":         re.compile(r"(文人画|士夫画|士人画)"),
    "雅俗":           re.compile(r"(雅俗|甜俗|市井|江湖|朝市|去俗|免俗)"),
    "虚实":           re.compile(r"(虚实|虚处|实处|虚中实|实中虚)"),
    "笔墨":           re.compile(r"(笔墨|笔情墨趣|笔苍墨润|笔歌墨舞)"),
    "写生":           re.compile(r"(写生|实景|真山水|对景)"),
    "简笔":           re.compile(r"(简笔|减笔|简约|简淡|简远)"),
    "不似之似":       re.compile(r"(不似之似|似与不似|绝不似而极似)"),
    "五笔七墨":       re.compile(r"(五笔七墨|七墨|五笔)"),
    "民学":           re.compile(r"(民学|君学|民物|民彝)"),
    "真迹鉴别":       re.compile(r"(真迹|伪作|赝品|摹本|仿本|代笔)"),
}

EMOTIONS = {
    "喜悦/得悟":     re.compile(r"(喜|乐|快|欣然|会心|大悟|豁然|悦|不觉|大笑|拍案|击节|畅然|忘倦|神来|兴会)"),
    "愤慨":           re.compile(r"(愤|怒|痛|恨|厌|深恨|深恶|耻|鄙|嗟|忧愤|痛心|扼腕)"),
    "孤独/坚持":     re.compile(r"(寂|寥落|无人识|独自|枯坐|默坐|冷|守|耐|甘|孤|匹夫)"),
    "忧虑/焦虑":     re.compile(r"(忧|虑|惶|恐|惧|急|窘|困|难|迫|束手)"),
    "感恩/眷恋":     re.compile(r"(感|谢|恩|幸|幸甚|思|念|忆|不忘|铭心|怀旧|故土)"),
}

CONCEPT_GROUPS = [
    ("七墨法", INK_METHODS),
    ("五笔法", BRUSH_METHODS),
]

# ── 3. 构建概念节点列表 ────────────────────────────────────────────────────
concept_nodes = {}
cid = 0

def add_concept(name, group, subtype="", regex=None):
    global cid
    key = f"cpt_{cid:04d}"
    concept_nodes[key] = {
        "id": key, "name": name, "group": group, "subtype": subtype,
        "regex": regex
    }
    cid += 1
    return key

# 墨法/笔法 — 无正则，literal match
for m in INK_METHODS:    add_concept(m, "七墨法", "墨法")
for b in BRUSH_METHODS:  add_concept(b, "五笔法", "笔法")

# 画学核心概念 — 带正则
for name, pat in CORE_CONCEPTS.items():
    add_concept(name, "画学核心", "画学核心", regex=pat)

# 情感 — 带正则
for name, pat in EMOTIONS.items():
    add_concept(name, "情感维度", "情感", regex=pat)

# ── 4. 组织节点 ──────────────────────────────────────────────────────────
ORG_PATTERNS = {
    "国学保存会":   re.compile(r"(国学保存会)"),
    "神州国光社":   re.compile(r"(神州国光社)"),
    "南社":         re.compile(r"(南社)"),
    "黄社":         re.compile(r"(黄社)"),
    "中国画会":     re.compile(r"(中国画会|海上题襟馆书画会)"),
    "商务印书馆":   re.compile(r"(商务印书馆)"),
    "中华书局":     re.compile(r"(中华书局)"),
    "北平艺专":     re.compile(r"(北平艺专|北平艺术专科学校)"),
    "杭州国立艺专": re.compile(r"(杭州国立艺专|国立艺术院|中央美术学院华东分院|浙江美术学院)"),
    "上海美专":     re.compile(r"(上海美专|上海美术专科)"),
    "故宫博物院":   re.compile(r"(故宫博物院|故宫)"),
    "神州日报":     re.compile(r"(神州日报)"),
    "国粹学报":     re.compile(r"(国粹学报)"),
    "贞社":         re.compile(r"(贞社)"),
    "百川书画会":   re.compile(r"(百川书画会)"),
}

org_nodes = {}
for i, (name, pat) in enumerate(ORG_PATTERNS.items()):
    org_nodes[f"org_{i:04d}"] = {"id": f"org_{i:04d}", "name": name}

# ── 5. 关系抽取 ──────────────────────────────────────────────────────────
# 所有边统一格式: {source, target, type, year, event_id, properties}

edges = []
eid_counter = 0

def add_edge(src, tgt, rel_type, year, evt_id, props=None):
    global eid_counter
    edges.append({
        "id":       f"edge_{eid_counter:06d}",
        "source":   src,
        "target":   tgt,
        "type":     rel_type,
        "year":     year,
        "event_id": evt_id,
        "properties": props or {},
    })
    eid_counter += 1

# ── 5a. 通信关系 (WROTE_TO) ──────────────────────────────────────────────
letter_pat = re.compile(
    r"([一-鿿]{2,5})(?:致|与|寄|复|覆|答|示)([一-鿿]{2,5})(?:书|函|信|札|尺牍|手翰|手札|手书)",
)
letter_pat2 = re.compile(r"^([一-鿿]{2,5})书[：:]")  # "傅雷书："
letter_pat3 = re.compile(r"与([一-鿿]{2,5})书[：:]")  # "与傅雷书："
letter_pat4 = re.compile(r"([一-鿿]{2,5})致([一-鿿]{2,5})[书函信]")

print("\n── 关系抽取 ──")

for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid = evt["id"]

    # 通信
    for m in letter_pat.finditer(text):
        sender = m.group(1)
        receiver = m.group(2)
        if sender in alias_to_std:
            sender = alias_to_std[sender]
        if receiver in alias_to_std:
            receiver = alias_to_std[receiver]
        if sender != receiver:
            add_edge(sender, receiver, "WROTE_TO", year, eid,
                     {"direction": f"{sender}→{receiver}"})

    # 傅雷书： 等格式
    for m in letter_pat2.finditer(text):
        writer = m.group(1)
        if writer in alias_to_std:
            writer = alias_to_std[writer]
        add_edge(writer, "黄宾虹", "WROTE_TO", year, eid,
                 {"direction": f"{writer}→黄宾虹"})

    # 与XX书：
    for m in letter_pat3.finditer(text):
        recipient = m.group(1)
        if recipient in alias_to_std:
            recipient = alias_to_std[recipient]
        add_edge("黄宾虹", recipient, "WROTE_TO", year, eid,
                 {"direction": "黄宾虹→" + recipient})

    if len(edges) > 50000:  # safety
        break

comm_edges = sum(1 for e in edges if e["type"] == "WROTE_TO")
print(f"  通信关系 WROTE_TO: {comm_edges}")

# ── 5b. 概念提及 (MENTIONS_CONCEPT) ─────────────────────────────────────
for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid = evt["id"]

    for cid, cnode in concept_nodes.items():
        name  = cnode["name"]
        regex = cnode.get("regex")
        if regex:
            if regex.search(text):
                add_edge(eid, cid, "MENTIONS_CONCEPT", year, eid)
        else:
            # 无正则的概念：literal match (墨法/笔法)
            if name in text:
                add_edge(eid, cid, "MENTIONS_CONCEPT", year, eid)

print(f"  概念提及 MENTIONS_CONCEPT: {sum(1 for e in edges if e['type']=='MENTIONS_CONCEPT')}")

# ── 5c. 组织关联 (BELONGS_TO / AFFILIATED_WITH) ───────────────────────
for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid = evt["id"]

    for oid, onode in org_nodes.items():
        if onode["name"] in text:
            add_edge(eid, oid, "INVOLVES_ORG", year, eid)

print(f"  组织关联 INVOLVES_ORG: {sum(1 for e in edges if e['type']=='INVOLVES_ORG')}")

# ── 5d. 游历关系 (TRAVELED_TO) ──────────────────────────────────────────
for loc in locations:
    if loc["type"] == "游历":
        add_edge(loc["event_id"], loc["standard_name"], "TRAVELED_TO",
                 loc["year"], loc["event_id"])

print(f"  游历关系 TRAVELED_TO: {sum(1 for e in edges if e['type']=='TRAVELED_TO')}")

# ── 5e. 创作关系 (CREATED) ──────────────────────────────────────────────
for cr in creations:
    add_edge("黄宾虹", cr.get("title", "佚名"), "CREATED",
             cr["year"], cr["event_id"],
             {"creation_type": cr.get("creation_type",""),
              "subject": cr.get("subject",""),
              "all_titles": cr.get("titles_all",[])})

print(f"  创作关系 CREATED: {sum(1 for e in edges if e['type']=='CREATED')}")

# ── 5f. 展览关系 (EXHIBITED_AT / PARTICIPATED_IN) ───────────────────────
exhi_pat = re.compile(r"(展览|画展|陈列|参展|出品)")
for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid = evt["id"]
    if exhi_pat.search(text) and re.search(r"(黄宾虹|宾虹|宾老|谱主)", text):
        add_edge("黄宾虹", eid, "EXHIBITED_AT", year, eid)

print(f"  展览关系 EXHIBITED_AT: {sum(1 for e in edges if e['type']=='EXHIBITED_AT')}")

# ── 5g. 赠画关系 (GIFTED) ───────────────────────────────────────────────
gift_pat = re.compile(r"(赠|寄赠|贻|赠予|见赠|惠赠|持赠|遗赠)")
for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid = evt["id"]
    if gift_pat.search(text) and re.search(r"(画|图|册|轴|卷|帧|幅)", text):
        # 方向判断：黄宾虹赠出 vs 他人赠予HBH
        if re.search(r"(宾虹|朴存|滨虹|宾老).*(赠|寄赠)", text):
            # HBH 赠出，找接收者
            recv_m = re.search(r"[赠寄贻]与?([一-鿿]{2,5})", text)
            target = alias_to_std.get(recv_m.group(1), recv_m.group(1)) if recv_m else "未识别"
            add_edge("黄宾虹", target, "GIFTED_ARTWORK", year, eid)
        elif re.search(r"赠.*(宾虹|朴存|滨虹|宾老)", text):
            # 他人赠予HBH
            giver_m = re.search(r"([一-鿿]{2,5}).*赠.*(宾虹|朴存|滨虹|宾老)", text)
            src = alias_to_std.get(giver_m.group(1), giver_m.group(1)) if giver_m else "未识别"
            add_edge(src, "黄宾虹", "GIFTED_ARTWORK", year, eid)
        if len(edges) > 80000:
            break

print(f"  赠画关系 GIFTED_ARTWORK: {sum(1 for e in edges if e['type']=='GIFTED_ARTWORK')}")

# ── 5h. 师生关系 (TAUGHT) ────────────────────────────────────────────────
teach_pat = re.compile(r"(门生|弟子|从学|受业|师事|侍侧|问学|请益|讲学|客座|教席|受教|门人)")
already_taught = set()
for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid = evt["id"]
    if teach_pat.search(text):
        # 从 text 两端取人物名
        for name in re.findall(r"[一-鿿]{2,4}", text[:60]):
            if name in alias_to_std and alias_to_std[name] != "黄宾虹":
                std = alias_to_std[name]
                key = ("黄宾虹", std, "TAUGHT")
                if key not in already_taught:
                    already_taught.add(key)
                    add_edge("黄宾虹", std, "TAUGHT", year, eid)

print(f"  师生关系 TAUGHT: {len(already_taught)}")

# ── 5i. 组织成员关系 ──────────────────────────────────────────────────────
for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid = evt["id"]
    for oid, onode in org_nodes.items():
        if onode["name"] in text and re.search(r"(黄宾虹|宾虹|朴存|滨虹)", text):
            add_edge("黄宾虹", oid, "MEMBER_OF", year, eid)

print(f"  组织成员 MEMBER_OF: {sum(1 for e in edges if e['type']=='MEMBER_OF')}")

# ── 5j. 逝世/追悼关系 (MOURNED) ─────────────────────────────────────────
mourn_pat = re.compile(r"(病逝|逝世|去世|谢世|陨|卒于|病殁|殁于|追悼|追悼会|公祭|哀挽|挽联|悼)")
for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid = evt["id"]
    if mourn_pat.search(text):
        # 谁逝世了
        who = re.search(r"([一-鿿]{2,5})(?:病逝|逝世|去世|谢世|卒于|病殁|殁于|追悼)", text)
        if who:
            name = who.group(1)
            if name in alias_to_std:
                name = alias_to_std[name]
                add_edge(name, "逝世", "MOURNED", year, eid)

print(f"  逝世关系 MOURNED: {sum(1 for e in edges if e['type']=='MOURNED')}")

# ── 6. 组装并输出 KG ────────────────────────────────────────────────────
# 事件节点
event_nodes = []
for evt in content_events:
    event_nodes.append({
        "id":          evt["id"],
        "year":        evt["year"],
        "date":        evt.get("date", str(evt["year"])),
        "source_type": evt.get("source_type", "未标注"),
        "topics":      topic_by_id.get(evt["id"], {}).get("topics", []),
        "raw_text":    evt.get("raw_text", "")[:200],
        "source_page": evt.get("source_page", 0),
    })

# 人物节点
person_nodes = []
for p in persons:
    person_nodes.append({
        "id":            p["standard_name"],
        "person_id":     p.get("person_id", ""),
        "category":      p.get("category", ""),
        "first_mention": p.get("first_mention", 0),
        "last_mention":  p.get("last_mention", 0),
        "total_mentions": p.get("total_mentions", 0),
    })

# 地点节点
place_nodes_set = {}
for loc in locations:
    sn = loc["standard_name"]
    if sn not in place_nodes_set:
        place_nodes_set[sn] = {"id": sn, "standard_name": sn,
                               "lat": loc["lat"], "lng": loc["lng"]}

# 作品节点
artwork_nodes_set = {}
for cr in creations:
    title = cr.get("title", "")
    if title and title not in artwork_nodes_set:
        artwork_nodes_set[title] = {
            "id":           title,
            "creation_type": cr.get("creation_type", ""),
            "subject":      cr.get("subject", ""),
            "year":         cr["year"],
            "titles_all":   cr.get("titles_all", []),
        }

# 组装主文件和精简文件
kg = {
    "meta": {
        "total_events":   len(event_nodes),
        "total_persons":  len(person_nodes),
        "total_places":   len(place_nodes_set),
        "total_artworks": len(artwork_nodes_set),
        "total_concepts": len(concept_nodes),
        "total_organizations": len(org_nodes),
        "total_edges":    len(edges),
        "source_distribution": dict(source_counts),
    },
    "nodes": {
        "events":        event_nodes,
        "persons":       person_nodes,
        "places":        list(place_nodes_set.values()),
        "artworks":      list(artwork_nodes_set.values()),
        "concepts":      [{k:v for k,v in c.items() if k != 'regex'} for c in concept_nodes.values()],
        "organizations": list(org_nodes.values()),
    },
    "edges": edges,
}

with open("hbh_knowledge_graph.json", "w", encoding="utf-8") as f:
    json.dump(kg, f, ensure_ascii=False, indent=2)
print(f"\n[OK] hbh_knowledge_graph.json")
print(f"  nodes: {kg['meta']['total_events']} events + "
      f"{kg['meta']['total_persons']} persons + "
      f"{kg['meta']['total_places']} places + "
      f"{kg['meta']['total_artworks']} artworks + "
      f"{kg['meta']['total_concepts']} concepts + "
      f"{kg['meta']['total_organizations']} orgs")
print(f"  edges: {kg['meta']['total_edges']}")

# ── 7. 边类型分布 ─────────────────────────────────────────────────────────
edge_types = Counter(e["type"] for e in edges)
print("\n── 关系类型分布 ──")
for t, c in edge_types.most_common():
    print(f"  {t:25s}: {c:6d}")

# ── 8. 文本来源层单独输出 ──────────────────────────────────────────────────
source_layer = []
for evt in content_events:
    source_layer.append({
        "event_id":    evt["id"],
        "year":        evt["year"],
        "source_type": evt.get("source_type", "未标注"),
        "raw_text":    evt.get("raw_text", "")[:200],
    })

with open("hbh_source_layer.json", "w", encoding="utf-8") as f:
    json.dump(source_layer, f, ensure_ascii=False, indent=2)
print(f"\n[OK] hbh_source_layer.json: {len(source_layer)} 条")

# ── 9. 自检报告 ────────────────────────────────────────────────────────────
report = []
report.append("=== 黄宾虹知识图谱 构建报告 ===\n")
report.append(f"事件总数: {len(content_events)}")
report.append(f"节点总数: {kg['meta']['total_events']} events + "
              f"{kg['meta']['total_persons']} persons + "
              f"{kg['meta']['total_places']} places + "
              f"{kg['meta']['total_artworks']} artworks + "
              f"{kg['meta']['total_concepts']} concepts + "
              f"{kg['meta']['total_organizations']} orgs")
report.append(f"边总数:   {len(edges)}\n")

report.append("── 文本来源层分布 ──")
for s, c in source_counts.most_common():
    report.append(f"  {s}: {c} ({round(c/len(content_events)*100,1)}%)")
report.append("")

report.append("── 关系类型分布 ──")
for t, c in edge_types.most_common():
    report.append(f"  {t}: {c}")
report.append("")

report.append("── 概念词典 (画学核心) ──")
for gname, members in CONCEPT_GROUPS:
    report.append(f"  [{gname}]: {'  '.join(members[:8])}")
report.append(f"  画学核心概念 ({len(CORE_CONCEPTS)} 个): {'  '.join(CORE_CONCEPTS.keys())}")
report.append("")

report.append("── 概念提及 TOP20 ──")
concept_mentions = Counter()
for e in edges:
    if e["type"] == "MENTIONS_CONCEPT":
        concept_mentions[e["target"]] += 1
for cid, cnt in concept_mentions.most_common(20):
    cname = concept_nodes.get(cid, {}).get("name", cid)
    report.append(f"  {cname}: {cnt}")
report.append("")

# 样本：各来源类型抽3条
report.append("── 文本来源样本 ──")
for src_type in ["HBH自撰", "他人记述", "编者按语", "引用文献"]:
    samples = [e for e in content_events if e.get("source_type") == src_type][:3]
    report.append(f"\n  [{src_type}]")
    for s in samples:
        report.append(f"    {s['id']} [{s['year']}]: {s['raw_text'][:120]}")
report.append("")

report.append("── 概念样本（情感维度）──")
for etype in ["喜悦/得悟", "愤慨", "孤独/坚持", "忧虑/焦虑", "感恩/眷恋"]:
    rel_edges = [e for e in edges if e["type"] == "MENTIONS_CONCEPT"
                 and concept_nodes.get(e["target"],{}).get("group") == "情感维度"
                 and concept_nodes.get(e["target"],{}).get("name") == etype]
    report.append(f"  {etype}: {len(rel_edges)} 条")
    if rel_edges:
        sample = rel_edges[0]
        report.append(f"    例: {evt_by_id[sample['event_id']]['raw_text'][:120]}")
report.append("")

# self-reflection 统计
self_reflex_edges = [e for e in edges if e["type"] == "MENTIONS_CONCEPT"
                     and concept_nodes.get(e["target"],{}).get("name") in
                     ["师造化", "浑厚华滋", "内美", "不似之似", "民学", "道咸中兴"]
                     and evt_by_id[e["event_id"]].get("source_type") == "HBH自撰"]
report.append(f"── HBH自撰中提到核心概念的条数 ──")
core_names = ["师造化","浑厚华滋","内美","不似之似","民学","道咸中兴","逸品","雅俗","南北宗"]
for cn in core_names:
    cnt = sum(1 for e in self_reflex_edges
              if concept_nodes.get(e["target"],{}).get("name") == cn)
    report.append(f"  {cn}: {cnt}")

with open("kg_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))
print("[OK] kg_report.txt")
print("\nDone.")
