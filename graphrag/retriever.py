# -*- coding: utf-8 -*-
"""
GraphRAG 混合检索引擎。

一次检索的流程：
  1. 实体链接：在问句中识别已知人物/地点/概念/社团/作品；
  2. KG 子图：取这些实体相关的清洗后三元组，并收集其 event_id（图→文锚定）；
  3. 文本召回：稠密(bge) + 词法(BM25) 各取 TopK → RRF 融合；
  4. 注入锚定：把 KG 命中边对应的年谱切片并入候选（GraphRAG 的关键一跳）；
  5. 重排：bge-reranker 交叉编码精排（可关闭）→ 取 FINAL_TOPK；
  6. 汇总三元组（实体相关 + 最终切片所在事件的边），按年排序、去重、截断。

返回一个 RetrievalBundle，交给 prompt.py 组装。
"""
import os
import re
import json
import pickle

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import jieba

from . import config as C
from .corpus import Corpus

jieba.setLogLevel(20)
_YEAR_RE = re.compile(r"(1[89]\d{2})")


def _triple_to_dict(t):
    """corpus.edge_to_triple 的元组 → 统一 dict。"""
    subj, rel, obj, year, eid = t[0], t[1], t[2], t[3], t[4]
    note = t[5] if len(t) > 5 else ""
    return {"subj": subj, "rel": rel, "obj": obj, "year": year,
            "event_id": eid, "note": note}


class RetrievalBundle(dict):
    """检索结果容器：entities / triples / chunks / years / era。"""
    pass


class GraphRAGRetriever:
    def __init__(self, use_reranker=None):
        self.corp = Corpus()
        # 索引
        self.chunks = []
        with open(os.path.join(C.INDEX_DIR, "chunks.jsonl"), encoding="utf-8") as f:
            for line in f:
                self.chunks.append(json.loads(line))
        self.dense = np.load(os.path.join(C.INDEX_DIR, "dense.npy"))
        with open(os.path.join(C.INDEX_DIR, "bm25.pkl"), "rb") as f:
            self.bm25 = pickle.load(f)
        assert len(self.chunks) == self.dense.shape[0], "切片与向量行数不一致，请重建索引"

        self.use_reranker = C.USE_RERANKER if use_reranker is None else use_reranker
        self._emb = None
        self._reranker = None
        # 画史知识卡片切片下标（用于定向注入）
        self.card_cids = [i for i, c in enumerate(self.chunks)
                          if c.get("source_type") == "画史综述"]

    # ── 懒加载模型 ──
    @property
    def emb(self):
        if self._emb is None:
            from sentence_transformers import SentenceTransformer
            self._emb = SentenceTransformer(C.EMB_MODEL)
        return self._emb

    @property
    def reranker(self):
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(C.RERANK_MODEL)
        return self._reranker

    # ── 单路召回 ──
    def _encode_query(self, query):
        return self.emb.encode([C.EMB_QUERY_INSTRUCTION + query],
                               normalize_embeddings=True, convert_to_numpy=True)[0]

    def _inject_cards(self, qv, final_cids):
        """按稠密相似度，把强相关的画史卡片注入最终上下文（top-1/top-2，阈值从严）。"""
        out = list(final_cids)
        if not self.card_cids:
            return out
        scored = sorted(((float(self.dense[c] @ qv), c) for c in self.card_cids),
                        reverse=True)
        for rank, (s, c) in enumerate(scored[:2]):
            thr = C.CARD_INJECT_SIM1 if rank == 0 else C.CARD_INJECT_SIM2
            if s >= thr and c not in out:
                out.append(c)
        return out

    def _dense(self, query, k, qv=None):
        if qv is None:
            qv = self._encode_query(query)
        sims = self.dense @ qv
        idx = np.argpartition(-sims, min(k, len(sims) - 1))[:k]
        idx = idx[np.argsort(-sims[idx])]
        return [(int(i), float(sims[i])) for i in idx]

    def _bm25(self, query, k):
        toks = [t for t in jieba.lcut(query) if t.strip()]
        scores = self.bm25.get_scores(toks)
        idx = np.argpartition(-scores, min(k, len(scores) - 1))[:k]
        idx = idx[np.argsort(-scores[idx])]
        return [(int(i), float(scores[i])) for i in idx]

    @staticmethod
    def _rrf(rank_lists, k=C.RRF_K):
        agg = {}
        for rl in rank_lists:
            for rank, (cid, _) in enumerate(rl):
                agg[cid] = agg.get(cid, 0.0) + 1.0 / (k + rank + 1)
        return sorted(agg.items(), key=lambda x: -x[1])

    # ── KG 子图 ──
    def _gather_triples(self, entities, extra_event_ids=()):
        triples, seen = [], set()

        def add(t):
            d = _triple_to_dict(t)
            key = (d["subj"], d["rel"], d["obj"], d["year"])
            if key not in seen:
                seen.add(key)
                triples.append(d)

        anchor_eids = set()
        for ent in entities:
            # 跳过谱主本人：否则每个问题都会灌入他一生 2343 条边，淹没真正被问及的实体
            if ent["name"] == C.SUBJECT:
                continue
            for t in self.corp.entity_triples(ent["name"], ent["type"]):
                add(t)
                if t[4]:
                    anchor_eids.add(t[4])
        # 来自指定事件（最终命中切片）的边，确保图谱与正文呼应
        for eid in extra_event_ids:
            for e in self.corp.eid2edges.get(eid, []):
                t = self.corp.edge_to_triple(e)
                if t:
                    add(t)
        return triples, anchor_eids

    # ── 主入口 ──
    def retrieve(self, query, final_k=None, fuse_k=None):
        final_k = final_k or C.FINAL_TOPK
        fuse_k = fuse_k or C.FUSE_TOPK
        years = [int(y) for y in _YEAR_RE.findall(query)]
        entities = self.corp.link_entities(query)

        # 1) 实体三元组 + 图谱锚定事件
        ent_triples, anchor_eids = self._gather_triples(entities)
        anchor_cids = [self.corp.eid2cid[e] for e in anchor_eids
                       if e in self.corp.eid2cid]

        # 2) 文本召回 + 融合
        qv = self._encode_query(query)
        dense = self._dense(query, C.DENSE_TOPK, qv=qv)
        bm25 = self._bm25(query, C.BM25_TOPK)
        fused = self._rrf([dense, bm25])
        cand = [cid for cid, _ in fused[:fuse_k]]

        # 3) 注入图谱锚定切片（去重）
        if C.GRAPH_ANCHOR_BOOST:
            for cid in anchor_cids:
                if cid not in cand:
                    cand.append(cid)

        # 4) 重排
        if self.use_reranker and cand:
            try:
                pairs = [[query, self.chunks[cid]["text"][:480]] for cid in cand]
                scores = self.reranker.predict(pairs)
                order = np.argsort(-np.asarray(scores))
                ranked = [cand[i] for i in order]
            except Exception as ex:
                print("[warn] reranker 不可用，回退 RRF 顺序：", ex)
                ranked = cand
        else:
            ranked = cand
        final_cids = ranked[:final_k]

        # 4.5) 定向注入强相关画史卡片（补足年谱所缺的画风/评价/聚合类知识）
        final_cids = self._inject_cards(qv, final_cids)

        # 5) 汇总三元组（实体相关 + 最终切片事件的边），分层排序去重并截断
        final_eids = [self.chunks[cid]["event_id"] for cid in final_cids]
        all_triples, _ = self._gather_triples(entities, extra_event_ids=final_eids)
        triples = self._rank_triples(all_triples, entities, years)[:C.KG_MAX_TRIPLES]

        # 6) 时代背景（厚重感）：围绕“问题焦点年份”取相近大事
        chunk_years = [self.chunks[c]["year"] for c in final_cids
                       if isinstance(self.chunks[c]["year"], int)]
        # 焦点优先级：问句年份 > 命中实体三元组年份（更贴合所问的人/事）> 切片年份
        triple_years = [t["year"] for t in triples if isinstance(t["year"], int)]
        focus_years = years or triple_years or chunk_years
        era = self._era_near(focus_years)

        return RetrievalBundle(
            query=query,
            entities=entities,
            triples=triples,
            chunks=[self.chunks[c] for c in final_cids],
            years=sorted(set(focus_years)),
            era=era,
        )

    # 关系优先级：人际社交 > 社团 > 画学 > 游历 > 创作
    _REL_RANK = {"通信": 0, "悼念": 0, "师承（教导）": 0, "赠画": 0,
                 "参与社团": 1, "论及画学": 2, "游历": 3, "创作": 4}

    def _rank_triples(self, triples, entities, years):
        """分层排序：①是否牵涉被问及的实体 ②关系类型 ③与问句年份的接近度。"""
        focus = {e["name"] for e in entities if e["name"] != C.SUBJECT}
        y0 = years[0] if years else None

        def involves(d):
            return (d["subj"] in focus) or (d["obj"] in focus)

        def yr_key(d):
            if d["year"] is None:
                return 10 ** 6
            return abs(d["year"] - y0) if y0 is not None else d["year"]

        return sorted(
            triples,
            key=lambda d: (0 if involves(d) else 1,
                           self._REL_RANK.get(d["rel"], 5),
                           yr_key(d)),
        )

    def _era_near(self, focus_years, span=8, limit=4):
        if not focus_years:
            return []
        fy = sorted(focus_years)
        center = fy[len(fy) // 2]                # 焦点中位年
        lo, hi = min(fy) - span, max(fy) + span
        out = []
        for e in self.corp.era:
            m = _YEAR_RE.search(str(e.get("date", "")))
            if not m:
                continue
            ey = int(m.group(1))
            if lo <= ey <= hi:
                out.append((abs(ey - center), -e.get("importance", 0), e))
        out.sort(key=lambda x: (x[0], x[1]))     # 先近后要
        return [e for _, _, e in out[:limit]]


if __name__ == "__main__":
    r = GraphRAGRetriever()
    b = r.retrieve("黄宾虹晚年在杭州与傅雷的交往")
    print("entities:", b["entities"])
    print("triples:", len(b["triples"]))
    for t in b["triples"][:6]:
        print("  ", t)
    print("chunks:", len(b["chunks"]))
    for ch in b["chunks"][:3]:
        print("  [{}] {} | {}".format(ch["year"], ch["source_type"], ch["text"][:60]))
