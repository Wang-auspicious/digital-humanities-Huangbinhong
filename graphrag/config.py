# -*- coding: utf-8 -*-
"""GraphRAG 全局配置：路径、模型、检索参数。"""
import os

# ── 路径 ──
PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(PKG_DIR)            # 仓库根目录（JSON 数据所在）
DATA_DIR = ROOT
INDEX_DIR = os.path.join(PKG_DIR, "index")

# ── 数据文件 ──
KG_JSON       = os.path.join(DATA_DIR, "hbh_knowledge_graph.json")
PERSONS_JSON  = os.path.join(DATA_DIR, "hbh_persons.json")
ALIAS_JSON    = os.path.join(DATA_DIR, "alias_map.json")
ERA_JSON      = os.path.join(DATA_DIR, "era_timeline.json")
JOURNEY_JSON  = os.path.join(DATA_DIR, "life_journey.json")
CARDS_JSON    = os.path.join(DATA_DIR, "hbh_knowledge_cards.json")   # 人工画史知识卡片（补年谱所缺：画风/评价/聚合类）

# ── 主角 ──
SUBJECT = "黄宾虹"
BIRTH_YEAR = 1865          # 谱主生年（用于年龄换算；旧俗堕地即二岁，此处按公历计岁差 +1）
DEATH_YEAR = 1955

# ── 模型（本地缓存，离线可用）──
EMB_MODEL    = "BAAI/bge-small-zh-v1.5"       # 稠密向量
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"      # 交叉编码重排（可选）
# bge 检索建议给查询加指令前缀以提升召回
EMB_QUERY_INSTRUCTION = "为这个问题检索相关的黄宾虹年谱史料："

# ── 检索参数 ──
DENSE_TOPK   = 40          # 稠密召回
BM25_TOPK    = 40          # 词法召回
RRF_K        = 60          # Reciprocal Rank Fusion 常数
FUSE_TOPK    = 30          # 融合后送入重排的候选数
FINAL_TOPK   = 8           # 最终进入提示词的文本切片数
KG_MAX_TRIPLES = 28        # 进入提示词的三元组上限
GRAPH_ANCHOR_BOOST = True  # 是否把图谱命中边对应的事件文本注入候选
# 画史知识卡片定向注入：按稠密相似度，仅强相关的卡片必入上下文（评价/画风/聚合类问题的关键补足）
CARD_INJECT_SIM1 = 0.58    # top-1 卡片注入阈值
CARD_INJECT_SIM2 = 0.63    # top-2 卡片注入阈值（更严，避免塞入弱相关卡片）

# 是否默认启用重排。bge-reranker-v2-m3 为 568M XLM-R-large，CPU 上每问约 4 分钟，
# 而稠密+BM25+RRF 仅约 1-2s 且质量已很好 —— 故默认关闭，按需用 --rerank 开启（离线批处理求极致质量时）。
USE_RERANKER = False

# ── 关系类型 → 中文可读标签 ──
REL_CN = {
    "WROTE_TO":         "通信",
    "CREATED":          "创作",
    "TRAVELED_TO":      "游历",
    "MENTIONS_CONCEPT": "论及画学",
    "INVOLVES_ORG":     "参与社团",
    "EXHIBITED_AT":     "展览",
    "GIFTED_ARTWORK":   "赠画",
    "MOURNED":          "悼念",
    "TAUGHT":           "师承",
}
