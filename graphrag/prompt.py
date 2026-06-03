# -*- coding: utf-8 -*-
"""
提示词组装：把 RetrievalBundle 格式化为 graph_context / text_context，
填入用户给定的 System Prompt 模板（system_prompt.txt）。

输出：
  · build_prompt() -> {"system_prompt": <填好的完整提示词>, "messages": [...], 各分块}
"""
import os
from . import config as C

_TEMPLATE_PATH = os.path.join(C.PKG_DIR, "system_prompt.txt")
with open(_TEMPLATE_PATH, encoding="utf-8") as _f:
    SYSTEM_TEMPLATE = _f.read()

# 关系 → 箭头方向是否“谱主指向对方”（仅用于可读排版）
_ARROW = "→"


def _age_str(corp, year):
    a = corp.age_at(year) if isinstance(year, int) else None
    return f"约{a}岁" if a else ""


def format_graph_context(corp, bundle):
    triples = bundle["triples"]
    if not triples:
        return "（本次未在知识图谱中检索到与问题直接相关的结构化关系）"

    lines = []
    for d in triples:
        subj, rel, obj, yr = d["subj"], d["rel"], d["obj"], d["year"]
        # 通信带方向信息：A 致信 B
        if rel == "通信" and d.get("note") and "→" in d["note"]:
            a, b = d["note"].split("→", 1)
            head = f"（{a}）—[通信·致信]{_ARROW}（{b}）"
        else:
            head = f"（{subj}）—[{rel}]{_ARROW}（{obj}）"
        when = f"{yr}年" if isinstance(yr, int) else "年份不详"
        age = _age_str(corp, yr)
        meta = f"{when}" + (f"·谱主{age}" if age else "")
        lines.append(f"  · {head}　【{meta}】")

    # 可标记实体清单：告诉模型哪些名字需要用 [[人物:]]/[[地名:]] 包裹
    persons = sorted({e["name"] for e in bundle["entities"] if e["type"] == "人物"}
                     | {d["subj"] for d in triples if d["subj"] in corp.persons or d["subj"] == C.SUBJECT}
                     | {d["obj"] for d in triples if d["obj"] in corp.persons})
    places = sorted({e["name"] for e in bundle["entities"] if e["type"] == "地名"}
                    | {d["obj"] for d in triples if d["rel"] == "游历"})
    tag_hint = ""
    if persons or places:
        tag_hint = ("\n\n  【可在答复中标记的实体】（出现时请用规定标签包裹）\n"
                    f"   - 人物：{ '、'.join(persons) if persons else '无' }\n"
                    f"   - 地名：{ '、'.join(places) if places else '无' }")

    return "\n".join(lines) + tag_hint


def format_text_context(corp, bundle):
    chunks = bundle["chunks"]
    if not chunks:
        return "（本次未检索到相关年谱切片）"
    out = []
    for i, ch in enumerate(chunks, 1):
        yr = ch["year"]
        when = f"{yr}年" if isinstance(yr, int) else (ch.get("date") or "年份不详")
        age = _age_str(corp, yr)
        src = ch.get("source_type") or "年谱"
        page = ch.get("source_page")
        page_s = f"·年谱第{page}页" if page else ""
        age_s = f"·谱主{age}" if age else ""
        meta = f"{when}{age_s}·来源：{src}{page_s}"
        out.append(f"  · 文献切片 [{i}]（{meta}）：\n    {ch['text']}")
    return "\n".join(out)


def format_era_context(bundle):
    era = bundle.get("era") or []
    if not era:
        return ""
    items = "；".join(f"{e.get('date')} {e.get('event')}" for e in era)
    return f"\n\n  【同期时代背景（供历史语境参照，非谱主个人事迹）】\n   {items}"


def build_prompt(corp, bundle):
    graph_ctx = format_graph_context(corp, bundle) + format_era_context(bundle)
    text_ctx = format_text_context(corp, bundle)
    query = bundle["query"]

    full = (SYSTEM_TEMPLATE
            .replace("{graph_context}", graph_ctx)
            .replace("{text_context}", text_ctx)
            .replace("{user_query}", query))

    # 同时给出 chat 风格 messages：system 含上下文与规范，user 为问句
    system_only = (SYSTEM_TEMPLATE
                   .replace("{graph_context}", graph_ctx)
                   .replace("{text_context}", text_ctx)
                   .replace("用户提问：{user_query}", "").rstrip())
    messages = [
        {"role": "system", "content": system_only},
        {"role": "user", "content": query},
    ]
    return {
        "system_prompt": full,
        "messages": messages,
        "graph_context": graph_ctx,
        "text_context": text_ctx,
    }
