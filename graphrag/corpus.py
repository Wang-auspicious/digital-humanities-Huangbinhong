# -*- coding: utf-8 -*-
"""
语料与知识图谱数据层。

职责：
  1. 把年谱事件（hbh_knowledge_graph.json 的 nodes.events）整理成可检索的【文本切片】，
     并用边把每条切片关联到出现的人物/地点/概念/社团/作品；
  2. 把节点与边装载成一张内存图（按实体名建邻接索引、按 event_id 建反查索引）；
  3. 基于 alias_map + 各类节点名，构建【实体链接】所需的别名→标准名索引。

本层不依赖任何重型库（无 numpy / torch），可独立使用。
"""
import json
import re
from collections import defaultdict

from . import config as C


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# 关系三元组合成：把一条边翻译成 (主语, 关系中文, 宾语, 年份, event_id) —— 仅保留可清洗的边
# ─────────────────────────────────────────────────────────────────────────────
_EVT_RE = re.compile(r"^evt_\d+$")


def _is_event_ref(x):
    return isinstance(x, str) and bool(_EVT_RE.match(x))


class Corpus:
    def __init__(self):
        kg = _load(C.KG_JSON)
        self.meta = kg.get("meta", {})
        self.nodes = kg["nodes"]
        self.edges = kg["edges"]

        # —— 节点 id → 显示名 / 元信息 ——
        self.persons = {p["id"]: p for p in self.nodes.get("persons", [])}
        self.places = {p["id"]: p for p in self.nodes.get("places", [])}
        self.concepts = {c["id"]: c for c in self.nodes.get("concepts", [])}
        self.orgs = {o["id"]: o for o in self.nodes.get("organizations", [])}
        self.artworks = {a["id"]: a for a in self.nodes.get("artworks", [])}
        self.events = {e["id"]: e for e in self.nodes.get("events", [])}

        # 概念/社团 id → 名称
        self.concept_name = {cid: c.get("name", cid) for cid, c in self.concepts.items()}
        self.org_name = {oid: o.get("name", oid) for oid, o in self.orgs.items()}

        # —— 别名 / 实体链接索引 ——
        self.alias_map = _load(C.ALIAS_JSON)          # 标准名 -> [别名...]
        self._build_entity_index()

        # —— 文本切片 + graph→text 反查 ——
        self._build_chunks()

        # —— 时代背景（用于历史厚重感）——
        try:
            self.era = _load(C.ERA_JSON)
        except Exception:
            self.era = []

    # ── 实体索引 ──────────────────────────────────────────────────────────────
    def _build_entity_index(self):
        # surface(别名/本名) -> (标准名, 类型)
        surf2ent = {}
        # 人物：alias_map 优先（315 条标准名，含别名）
        for std, aliases in self.alias_map.items():
            surf2ent.setdefault(std, (std, "人物"))
            for a in aliases:
                if a and len(a) >= 2:
                    surf2ent.setdefault(a, (std, "人物"))
        # 人物节点本名补充
        for pid in self.persons:
            surf2ent.setdefault(pid, (pid, "人物"))
        # 地点
        for pid, p in self.places.items():
            surf2ent.setdefault(pid, (pid, "地名"))
            sn = p.get("standard_name")
            if sn:
                surf2ent.setdefault(sn, (pid, "地名"))
        # 概念
        for cid, c in self.concepts.items():
            nm = c.get("name")
            if nm and len(nm) >= 2:
                surf2ent.setdefault(nm, (nm, "概念"))
        # 社团
        for oid, o in self.orgs.items():
            nm = o.get("name")
            if nm and len(nm) >= 2:
                surf2ent.setdefault(nm, (nm, "社团"))
        # 作品（标题，长度>=2 才纳入，避免噪声）
        for aid, a in self.artworks.items():
            for t in (a.get("titles_all") or [a.get("id")]):
                if t and len(t) >= 2:
                    surf2ent.setdefault(t, (aid, "作品"))

        self.surface2ent = surf2ent
        # 按长度降序的 surface 列表，便于最长匹配
        self.surfaces_by_len = sorted(surf2ent.keys(), key=len, reverse=True)

    def link_entities(self, text):
        """在查询串中识别已知实体，返回 [{surface, name, type}]（去重，最长匹配优先）。"""
        found = {}
        used_spans = []
        for surf in self.surfaces_by_len:
            idx = text.find(surf)
            if idx < 0:
                continue
            span = (idx, idx + len(surf))
            # 避免与更长的已匹配实体重叠
            if any(not (span[1] <= s or span[0] >= e) for s, e in used_spans):
                continue
            name, typ = self.surface2ent[surf]
            key = (name, typ)
            if key not in found:
                found[key] = {"surface": surf, "name": name, "type": typ}
                used_spans.append(span)
        return list(found.values())

    # ── 文本切片 ──────────────────────────────────────────────────────────────
    def _build_chunks(self):
        # 先按 event_id 归集边，给每条事件文本附上实体标签
        evt_persons = defaultdict(set)
        evt_places = defaultdict(set)
        evt_concepts = defaultdict(set)
        evt_orgs = defaultdict(set)
        evt_artworks = defaultdict(set)
        evt_rels = defaultdict(list)
        eid2edges = defaultdict(list)

        for e in self.edges:
            eid = e.get("event_id")
            if eid:
                eid2edges[eid].append(e)
            t = self.edge_to_triple(e)
            if t and eid:
                evt_rels[eid].append(t)
            # 实体标签归集
            for end in (e.get("source"), e.get("target")):
                if end in self.persons and end != C.SUBJECT:
                    evt_persons[eid].add(end)
                elif end in self.places:
                    evt_places[eid].add(self.places[end].get("standard_name", end))
                elif end in self.concepts:
                    evt_concepts[eid].add(self.concept_name[end])
                elif end in self.orgs:
                    evt_orgs[eid].add(self.org_name[end])
                elif end in self.artworks:
                    evt_artworks[eid].add(end)
        self.eid2edges = eid2edges

        chunks = []
        for eid, ev in self.events.items():
            txt = (ev.get("raw_text") or "").strip()
            if len(txt) < 6:
                continue
            # 跳过纯年份表头（如“公元1865年清穆宗 同治四年”）
            if re.match(r"^公元\s*\d{4}\s*年", txt) and len(txt) < 40:
                continue
            chunks.append({
                "cid": len(chunks),
                "event_id": eid,
                "year": ev.get("year"),
                "date": ev.get("date"),
                "source_type": ev.get("source_type", ""),
                "source_page": ev.get("source_page"),
                "topics": ev.get("topics", []),
                "text": txt,
                "persons": sorted(evt_persons.get(eid, [])),
                "places": sorted(evt_places.get(eid, [])),
                "concepts": sorted(evt_concepts.get(eid, [])),
                "orgs": sorted(evt_orgs.get(eid, [])),
                "artworks": sorted(evt_artworks.get(eid, [])),
            })
        # —— 追加：人工画史知识卡片（补足年谱所缺的画风/评价/聚合类知识，与年谱切片一同被检索）——
        for card in self._load_cards():
            txt = (card.get("text") or "").strip()
            if len(txt) < 6:
                continue
            chunks.append({
                "cid": len(chunks),
                "event_id": "card_" + str(card.get("id", len(chunks))),
                "year": card.get("year"),
                "date": None,
                "source_type": "画史综述",         # 与年谱事件区分，提示模型这是画史共识而非具体史料
                "source_page": None,
                "topics": card.get("topics", []),
                "title": card.get("title", ""),
                "text": (card.get("title", "") + "。" + txt) if card.get("title") else txt,
                "persons": [], "places": [], "concepts": [], "orgs": [], "artworks": [],
            })

        self.chunks = chunks
        self.eid2cid = {c["event_id"]: c["cid"] for c in chunks}

    def _load_cards(self):
        try:
            cards = _load(C.CARDS_JSON)
            return cards if isinstance(cards, list) else []
        except Exception:
            return []

    # ── 边 → 三元组 ───────────────────────────────────────────────────────────
    def edge_to_triple(self, e):
        """返回 (subj, rel_cn, obj, year, event_id) 或 None。仅保留端点可清洗的边。"""
        typ = e.get("type")
        src, tgt = e.get("source"), e.get("target")
        yr = e.get("year")
        eid = e.get("event_id")
        rel = C.REL_CN.get(typ, typ)
        S = C.SUBJECT

        if typ == "TRAVELED_TO":
            # source 为事件，target 为地名
            place = tgt
            if place in self.places:
                place = self.places[place].get("standard_name", place)
            if place and not _is_event_ref(place):
                return (S, "游历", place, yr, eid)
            return None

        if typ == "MENTIONS_CONCEPT":
            nm = self.concept_name.get(tgt, tgt)
            if nm and not _is_event_ref(nm):
                return (S, "论及画学", nm, yr, eid)
            return None

        if typ == "INVOLVES_ORG":
            nm = self.org_name.get(tgt, tgt)
            if nm and not _is_event_ref(nm):
                return (S, "参与社团", nm, yr, eid)
            return None

        if typ == "CREATED":
            if src == S or src in self.persons:
                title = tgt
                if tgt in self.artworks:
                    tl = self.artworks[tgt].get("titles_all")
                    title = tl[0] if tl else tgt
                if title and not _is_event_ref(title):
                    return (src if src == S else src, "创作", title, yr, eid)
            return None

        if typ == "MOURNED":
            # source 为逝者，谱主悼念之
            if src in self.persons:
                return (S, "悼念", src, yr, eid)
            return None

        if typ == "TAUGHT":
            if tgt in self.persons:
                return (S, "师承（教导）", tgt, yr, eid)
            return None

        if typ == "GIFTED_ARTWORK":
            if tgt in self.persons:
                return (S, "赠画", tgt, yr, eid)
            return None

        if typ == "WROTE_TO":
            # 仅保留与谱主之间、且两端均为已知人物的通信
            a_ok = src in self.persons or src == S
            b_ok = tgt in self.persons or tgt == S
            if a_ok and b_ok and (src == S or tgt == S):
                direction = (e.get("properties") or {}).get("direction", "")
                return (src, "通信", tgt, yr, eid, direction)
            return None

        return None  # EXHIBITED_AT 等暂不进三元组（其文本仍可被检索）

    # ── 给定实体，取其相关边/三元组 ─────────────────────────────────────────────
    def entity_triples(self, entity_name, entity_type):
        """返回该实体相关的三元组列表（已清洗、可读）。"""
        out = []
        seen = set()
        for e in self.edges:
            src, tgt = e.get("source"), e.get("target")
            # 概念/社团/作品端点是 id，需要做名称匹配
            touch = entity_name in (src, tgt)
            if entity_type == "概念":
                touch = touch or any(self.concept_name.get(x) == entity_name for x in (src, tgt))
            elif entity_type == "社团":
                touch = touch or any(self.org_name.get(x) == entity_name for x in (src, tgt))
            elif entity_type == "地名":
                pid = self._place_id(entity_name)
                touch = touch or pid in (src, tgt)
            if not touch:
                continue
            t = self.edge_to_triple(e)
            if not t:
                continue
            key = (t[0], t[1], t[2], t[3])
            if key in seen:
                continue
            seen.add(key)
            out.append(t)
        out.sort(key=lambda x: (x[3] is None, x[3]))
        return out

    def _place_id(self, name):
        for pid, p in self.places.items():
            if pid == name or p.get("standard_name") == name:
                return pid
        return name

    def person_meta(self, name):
        p = self.persons.get(name)
        if not p:
            return None
        return {
            "category": p.get("category"),
            "first": p.get("first_mention"),
            "last": p.get("last_mention"),
            "mentions": p.get("total_mentions"),
        }

    def age_at(self, year):
        if not isinstance(year, int):
            return None
        return year - C.BIRTH_YEAR + 2  # 旧俗堕地即二岁；1955卒=享寿92岁


if __name__ == "__main__":
    c = Corpus()
    print("chunks:", len(c.chunks))
    print("edges:", len(c.edges), "events:", len(c.events))
    print("persons:", len(c.persons), "places:", len(c.places),
          "concepts:", len(c.concepts), "orgs:", len(c.orgs), "artworks:", len(c.artworks))
    print("surfaces:", len(c.surface2ent))
    # 抽样实体链接
    for q in ["黄宾虹晚年与傅雷在杭州的交往", "1933年入蜀游青城山", "南社与陈师曾"]:
        print(q, "=>", c.link_entities(q))
    # 抽样三元组
    print("傅雷相关三元组 sample:", c.entity_triples("傅雷", "人物")[:5])
