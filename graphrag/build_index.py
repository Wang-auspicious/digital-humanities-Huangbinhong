# -*- coding: utf-8 -*-
"""
构建并持久化检索索引（一次性，离线）：
  · 稠密向量：BAAI/bge-small-zh-v1.5 对每条年谱切片编码 → index/dense.npy
  · 词法索引：jieba 分词 + BM25Okapi → index/bm25.pkl
  · 切片元数据：index/chunks.jsonl（行号 == cid == dense 行号）
  · 构建信息：index/build_meta.json

用法：  python -m graphrag.build_index
"""
import os
import json
import pickle
import time

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import jieba
from rank_bm25 import BM25Okapi

from . import config as C
from .corpus import Corpus

jieba.setLogLevel(20)


def bm25_tokens(chunk):
    """词法文档 = 正文 + 实体名（增强人名/地名的字面召回）。"""
    parts = [chunk["text"]]
    for k in ("persons", "places", "concepts", "orgs"):
        parts.extend(chunk.get(k, []))
    toks = []
    for seg in parts:
        toks.extend([t for t in jieba.lcut(seg) if t.strip()])
    return toks


def main():
    os.makedirs(C.INDEX_DIR, exist_ok=True)
    t0 = time.time()
    print("[1/4] 加载语料 + 知识图谱 …")
    corp = Corpus()
    chunks = corp.chunks
    print(f"      切片 {len(chunks)} 条")

    # —— 持久化切片元数据 ——
    chunks_path = os.path.join(C.INDEX_DIR, "chunks.jsonl")
    with open(chunks_path, "w", encoding="utf-8") as f:
        for ch in chunks:
            f.write(json.dumps(ch, ensure_ascii=False) + "\n")

    # —— BM25 ——
    print("[2/4] 分词 + 构建 BM25 …")
    tokenized = [bm25_tokens(ch) for ch in chunks]
    bm25 = BM25Okapi(tokenized)
    with open(os.path.join(C.INDEX_DIR, "bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)

    # —— 稠密向量 ——
    print(f"[3/4] 加载 {C.EMB_MODEL} 并编码（CPU，可能数分钟）…")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(C.EMB_MODEL)
    passages = [ch["text"][:480] for ch in chunks]
    emb = model.encode(
        passages, batch_size=64, normalize_embeddings=True,
        show_progress_bar=True, convert_to_numpy=True,
    ).astype("float32")
    np.save(os.path.join(C.INDEX_DIR, "dense.npy"), emb)

    # —— 构建信息 ——
    print("[4/4] 写出构建信息 …")
    meta = {
        "n_chunks": len(chunks),
        "emb_model": C.EMB_MODEL,
        "emb_dim": int(emb.shape[1]),
        "n_edges": len(corp.edges),
        "n_persons": len(corp.persons),
        "n_places": len(corp.places),
        "build_seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(C.INDEX_DIR, "build_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("完成：", json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
