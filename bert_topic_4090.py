# -*- coding: utf-8 -*-
"""
BERTopic 无监督主题模型 —— 在 4090 服务器上运行
目的：发现年谱中自然涌现的主题，验证规则分类 + 寻找意外主题

运行环境：
  conda activate bert  （或 deep_plaque，需安装 bertopic sentence-transformers jieba）
  pip install bertopic sentence-transformers jieba umap-learn hdbscan -i https://pypi.tuna.tsinghua.edu.cn/simple
  CUDA_VISIBLE_DEVICES=0 python bert_topic_4090.py

输入：  hbh_events_raw.json（同目录）
输出：  bertopic_results.json, bertopic_report.txt
"""
import json, os, re
import jieba
import numpy as np
from collections import defaultdict

# ── 1. 加载数据 ────────────────────────────────────────────────────────────────
print("Loading data...")
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "hbh_events_raw.json"), encoding="utf-8") as f:
    events = json.load(f)

docs = []
doc_ids = []
doc_years = []
for evt in events:
    if evt.get("type") == "year_header":
        continue
    text = evt.get("raw_text", "").strip()
    if len(text) < 10:
        continue
    docs.append(text)
    doc_ids.append(evt["id"])
    doc_years.append(evt["year"])

print(f"Documents: {len(docs)}")

# ── 2. 中文分词 ────────────────────────────────────────────────────────────────
# 自定义词典（年谱专有词）
HBH_WORDS = [
    "黄宾虹","宾虹","朴存","国学保存会","神州国光社","神州日报",
    "金石","篆刻","碑学","笔法","墨法","皴法","山水","花鸟",
    "题跋","金陵","北平","歙县","潭渡","黄山","新安","徽州",
    "同盟会","辛亥","戊戌","义和团","北伐","抗战",
    "写生","山水画","花鸟画","书法","隶书","篆书",
]
for w in HBH_WORDS:
    jieba.add_word(w)

STOPWORDS = set([
    "的","了","在","是","和","有","与","于","为","其","之","以","也","而",
    "不","到","从","说","年","月","日","该","此","这","那","被","由","对",
    "等","中","后","前","上","下","里","出","入","来","去","时","即",
    "余","先生","其","之","而","亦","且","或","则","乃","所","按","云",
    "曰","谱","主","见","注","如","如此","可","当","已","曾","将","能",
])

def tokenize(text):
    # 清理数字、英文、标点
    text = re.sub(r"[0-9a-zA-Z《》【】「」（）\(\)，。；：！？、""''…—\-·]", " ", text)
    words = jieba.lcut(text)
    return [w for w in words if len(w) >= 2 and w not in STOPWORDS]

print("Tokenizing...")
tokenized = [" ".join(tokenize(doc)) for doc in docs]

# ── 3. BERTopic ────────────────────────────────────────────────────────────────
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer

print("Loading sentence transformer model...")
# 使用中文 BERT 模型
model = SentenceTransformer("shibing624/text2vec-base-chinese")

print("Encoding documents...")
embeddings = model.encode(docs, show_progress_bar=True, batch_size=64, device="cuda")
print(f"Embeddings shape: {embeddings.shape}")

# UMAP 降维
umap_model = UMAP(
    n_neighbors=15,
    n_components=5,
    min_dist=0.0,
    metric="cosine",
    random_state=42,
)

# HDBSCAN 聚类
hdbscan_model = HDBSCAN(
    min_cluster_size=20,
    min_samples=5,
    metric="euclidean",
    cluster_selection_method="eom",
    prediction_data=True,
)

# 中文分词向量化（直接用 jieba tokenizer，传入原始文本）
vectorizer = CountVectorizer(
    tokenizer=tokenize,
    min_df=3,
    max_df=0.9,
)

topic_model = BERTopic(
    embedding_model=model,
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=vectorizer,
    top_n_words=10,
    nr_topics="auto",
    calculate_probabilities=True,
    verbose=True,
)

print("Fitting BERTopic...")
topics, probs = topic_model.fit_transform(docs, embeddings)

# ── 4. 输出结果 ────────────────────────────────────────────────────────────────
topic_info = topic_model.get_topic_info()
print(f"Found {len(topic_info)-1} topics (excl. outliers)")

# 按年代分析主题分布
results = []
for i, (doc_id, year, topic_id, prob) in enumerate(zip(doc_ids, doc_years, topics, probs)):
    top_topic = int(topic_id)
    top_prob  = float(prob[top_topic]) if top_topic >= 0 and top_topic < len(prob) else 0.0
    results.append({
        "event_id": doc_id,
        "year":     year,
        "topic_id": top_topic,
        "prob":     round(top_prob, 4),
    })

topic_words = {}
for tid in topic_info["Topic"].tolist():
    if tid == -1:
        continue
    words = topic_model.get_topic(tid)
    topic_words[str(tid)] = [w for w, _ in words[:10]]

output = {
    "total_docs":    len(docs),
    "total_topics":  len(topic_info) - 1,
    "topic_info":    topic_info.to_dict(orient="records"),
    "topic_words":   topic_words,
    "doc_topics":    results,
}

out_path = os.path.join(script_dir, "bertopic_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"Saved: {out_path}")

# 文本报告
report_lines = []
report_lines.append(f"Total docs: {len(docs)}")
report_lines.append(f"Total topics: {len(topic_info)-1}")
report_lines.append("")
report_lines.append("── Topic Overview ──")
for _, row in topic_info.iterrows():
    tid = row["Topic"]
    if tid == -1:
        report_lines.append(f"  Outliers (-1): {row['Count']} docs")
        continue
    words = topic_words.get(str(tid), [])
    report_lines.append(f"  Topic {tid:3d} ({row['Count']:4d} docs): {', '.join(words[:8])}")
report_lines.append("")

# 年代 × 主题热图
report_lines.append("── Topic × Decade Heatmap ──")
decade_topic = defaultdict(lambda: defaultdict(int))
for r in results:
    if r["topic_id"] >= 0:
        decade = (r["year"] // 10) * 10
        decade_topic[decade][r["topic_id"]] += 1

top_topics_by_count = [row["Topic"] for _, row in topic_info.iterrows()
                       if row["Topic"] >= 0][:15]
header = f"{'Decade':8s}" + "".join(f"T{t:3d}" for t in top_topics_by_count)
report_lines.append(header)
for dec in sorted(decade_topic.keys()):
    row = f"{dec}s     "
    for t in top_topics_by_count:
        row += f"{decade_topic[dec].get(t,0):5d}"
    report_lines.append(row)

report_path = os.path.join(script_dir, "bertopic_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))
print(f"Report: {report_path}")
print("Done.")
