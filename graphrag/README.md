# 黄宾虹年谱 · GraphRAG（图增强检索增强生成）

一套**离线、自包含**的 GraphRAG 问答后端：把年谱的「非结构化文献（RAG）」与「结构化关系链（KG）」联合检索，
组装成你指定的学术书童 System Prompt，供任意本地大模型生成「可被前端拦截高亮」的答复。

> 本目录只做到「检索 + 提示词组装（+ 可选生成）」。**尚未接入前端**，符合“先做完 RAG”的交付要求。

---

## 1. 它解决什么

输入一个自然语言问题 → 输出一段**已填好上下文的提示词**（或直接的答复），其中：

- **结构化关系链（KG）**：谱主与人物/地点/作品/社团/画学概念之间清洗过的三元组，带**年份与谱主年龄**，
  按「是否牵涉所问实体 → 关系类型（社交>社团>画学>游历>创作）→ 年份接近度」分层排序，天然呈现
  “92 岁长周期内交游网络的动态演变”。
- **非结构化文献（RAG）**：bge 稠密向量 + BM25 词法**混合召回**，再用 `bge-reranker` 交叉编码精排，
  每条切片标注**年份·谱主年龄·来源类型·年谱页码**。
- **图→文锚定**：KG 命中边携带 `event_id`，对应的年谱原文被强制并入候选——这是 GraphRAG 的关键一跳，
  保证“图谱事实”与“文献证据”相互印证。
- **诚实与可标记**：System Prompt 要求模型只依据上下文作答、冲突需指出、无据则明确拒答，并把关键
  人物/地名用 `[[人物:傅雷]]` / `[[地名:歙县]]` 标签包裹，供前端联动。

---

## 2. 目录结构

```
graphrag/
  config.py          全局配置（路径 / 模型 / 检索参数 / 关系中文标签）
  corpus.py          数据层：年谱切片 + KG 图 + 实体别名链接（无重型依赖）
  build_index.py     一次性构建：bge 稠密向量 + BM25(jieba) → index/
  retriever.py       混合检索：实体链接→KG子图→稠密+BM25+RRF→reranker→图文锚定
  prompt.py          组装 graph_context / text_context，填入 system_prompt.txt
  system_prompt.txt  你给定的学术书童 System Prompt（含 {graph_context}{text_context}{user_query}）
  llm.py             可插拔大模型客户端（OpenAI 兼容 / Anthropic / dry-run；仅标准库）
  pipeline.py        端到端：GraphRAG().answer(query)
  demo.py            6 个代表性问题的样例跑批 → demo_outputs/
  index/             持久化索引（chunks.jsonl / dense.npy / bm25.pkl / build_meta.json）
../graphrag_qa.py    命令行入口
../demo_outputs/     样例输出（每题 JSON + 组装提示词 + 汇总 README_demo.md）
```

数据来源（仓库根目录现有 JSON，无需改动）：
`hbh_knowledge_graph.json`（节点5类+边4731）、`alias_map.json`（315标准名/别名）、
`hbh_persons.json`（302人）、`era_timeline.json`（时代背景）。

---

## 3. 快速开始

```bash
# (1) 一次性构建索引（约 70s，CPU，离线；模型已在本地 HF 缓存）
python -m graphrag.build_index

# (2) 提问（默认快速模式：稠密+BM25+RRF，约1-2s；未接大模型 → 只输出组装好的提示词）
python graphrag_qa.py "黄宾虹晚年与傅雷的交往是怎样的？" --show-prompt

# 追求极致召回质量时再开重排（CPU 上每问约4分钟）
python graphrag_qa.py "1933年入蜀对其画风的影响" --rerank

# 导出检索结果+提示词为 JSON
python graphrag_qa.py "他与南社的关系" --json out.json

# 跑样例集（默认快速模式，约20s 出全部6题）
python -m graphrag.demo
```

> 首个问题约 18s 是一次性加载 bge 向量模型；之后每问亚秒级。服务化时在启动期预热即可。

> Windows 终端如遇中文乱码，设 `set PYTHONUTF8=1`；首次运行设 `set HF_HUB_OFFLINE=1` 强制用本地缓存。

---

## 4. 接入本地大模型（可选）

`llm.py` 只用标准库，通过环境变量选后端，**无需改代码**：

```bash
# Ollama / LM Studio / vLLM / one-api 等 OpenAI 兼容端点
set GRAPHRAG_LLM_BASE=http://localhost:11434/v1
set GRAPHRAG_LLM_MODEL=qwen2.5:14b
# set GRAPHRAG_LLM_KEY=...        # 本地可省略

python graphrag_qa.py "黄宾虹与傅雷的交往" --generate
```

或在代码中：

```python
from graphrag.pipeline import GraphRAG
rag = GraphRAG()
res = rag.answer("黄宾虹晚年与李可染的师承", generate="auto")
print(res["prompt"]["system_prompt"])   # 始终可得
print(res["answer"])                     # 配置了后端才有
```

未配置后端时 `answer()` 仍返回完整提示词与检索结构，可直接喂给任何框架（LangChain/LlamaIndex/裸脚本）。

---

## 5. 前端如何承接（待后续接入）

System Prompt 已强制模型输出 `[[人物:X]]` / `[[地名:Y]]` 标签。前端把流式文本里的标签替换为可点击元素：

```javascript
let html = llmText
  .replace(/\[\[人物:(.*?)\]\]/g,
    '<span class="mention person" onclick="highlightNetwork(\'$1\')">$1</span>')
  .replace(/\[\[地名:(.*?)\]\]/g,
    '<span class="mention place"  onclick="flyToMap(\'$1\')">$1</span>');
```

于是点击答复中的“傅雷”即可高亮社交网络时序流线、点击“青城山”即可在生命舆图飞跳——
数据·视觉·智能问答三者打通。**本步骤尚未实施，待你回来确认接入位置后再做。**

---

## 6. 关键参数（`config.py`）

| 参数 | 默认 | 含义 |
|---|---|---|
| `DENSE_TOPK` / `BM25_TOPK` | 40 / 40 | 两路召回深度 |
| `FUSE_TOPK` | 30 | RRF 融合后送入重排的候选数 |
| `FINAL_TOPK` | 8 | 进入提示词的文献切片数 |
| `KG_MAX_TRIPLES` | 28 | 进入提示词的三元组上限 |
| `USE_RERANKER` | False | 是否默认启用 bge-reranker 精排（慢，opt-in） |
| `BIRTH_YEAR` | 1865 | 年龄按虚岁换算（卒年=享寿92岁） |

---

## 7. 设计要点与已知边界

- **三元组只保留可清洗的边**：端点须为已知实体（302人/55地/概念/社团/作品）或谱主；图中残留的噪声
  端点（如“那些/深受骈体文”）不进提示词，但其 `event_id` 仍可锚定文献。
- **实体链接**为最长匹配的词典法（基于 `alias_map` + 各类节点名），轻量稳健；少数未标准化地名
  （如“青城山”不在 55 个地点节点中）走文本召回兜底。
- **重排默认关闭**：`bge-reranker-v2-m3` 是 568M XLM-R-large，CPU 上每问约 4 分钟，对已很好的 RRF 结果
  提升有限，故默认走「稠密+BM25+RRF」（亚秒级）。离线批处理求极致质量时再 `--rerank`。
- **谱主不作为三元组焦点**：实体链接总会命中“黄宾虹”，若把他作为焦点会灌入其一生 2343 条边淹没所问对象；
  因此三元组只围绕「被问及的其他实体」+「最终命中文献所在事件的边」展开（既相关又与正文呼应）。
- **召回恒返回 Top-K 切片**：即便问题无关（如毕加索），仍会给出最相近的切片，但 graph_context 为空/无关，
  叠加 System Prompt 的诚实原则，模型应据此明确拒答而非杜撰。
