# -*- coding: utf-8 -*-
"""
样例演示：对一组代表性问题跑完整 GraphRAG（检索+提示词组装），
把每题的「检索结果 + 组装提示词」导出到 demo_outputs/，并汇总成一份 Markdown 供审阅。

用法：  python -m graphrag.demo
"""
import os
import io
import sys
import json
import time

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

from . import config as C
from .pipeline import GraphRAG

OUT_DIR = os.path.join(C.ROOT, "demo_outputs")

QUERIES = [
    "黄宾虹晚年在杭州与傅雷的交往是怎样的？",          # 晚期：知音/通信/赠画
    "黄宾虹早年与南社、邓实、黄节等人的革命交游",        # 早年：南社激进
    "1933年入蜀游青城山、嘉陵江对黄宾虹画风的影响",      # 空间+画风转折（白宾虹→黑宾虹）
    "黄宾虹晚年对李可染等后辈学生的影响与传承",          # 晚期：传薪
    "黄宾虹关于‘五笔七墨’等笔墨画学的论述",             # 画学概念
    "黄宾虹是否与西班牙画家毕加索有过会面或通信？",       # 诚实性/负样本（应回答暂无法回答）
]


def run():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("加载 GraphRAG（默认快速模式：稠密+BM25+RRF，无重排）…")
    t0 = time.time()
    rag = GraphRAG()                       # 用默认配置（与 CLI 一致）
    print("就绪，用时 %.1fs\n" % (time.time() - t0))

    md = ["# 黄宾虹年谱 GraphRAG · 样例检索与组装提示词\n",
          f"> 嵌入模型 `{C.EMB_MODEL}` + BM25(jieba) 混合召回 → `{C.RERANK_MODEL}` 重排；",
          "> 知识图谱三元组与年谱文献切片联合组装。以下为**检索+提示词组装**结果（未接大模型）。\n",
          "---\n"]

    for i, q in enumerate(QUERIES, 1):
        t = time.time()
        res = rag.answer(q, generate=False)
        dt = time.time() - t
        b = res["bundle"]
        # 落盘 JSON
        with open(os.path.join(OUT_DIR, f"q{i}.json"), "w", encoding="utf-8") as f:
            json.dump({
                "query": q,
                "entities": b["entities"],
                "triples": b["triples"],
                "chunks": b["chunks"],
                "prompt": res["prompt"]["system_prompt"],
            }, f, ensure_ascii=False, indent=2)
        # 落盘完整提示词
        with open(os.path.join(OUT_DIR, f"q{i}_prompt.txt"), "w", encoding="utf-8") as f:
            f.write(res["prompt"]["system_prompt"])

        print(f"[{i}] {q}")
        print(f"    实体：{'、'.join(e['name'] for e in b['entities']) or '无'}"
              f" | 三元组 {len(b['triples'])} | 切片 {len(b['chunks'])} | {dt:.1f}s")

        # Markdown 摘要
        ent_names = "、".join(e["name"] for e in b["entities"]) or "（无）"
        md.append(f"## {i}. {q}\n")
        md.append(f"**命中实体**：{ent_names}　"
                  f"｜ 三元组 {len(b['triples'])} 条 ｜ 文献切片 {len(b['chunks'])} 条\n")
        md.append("**结构化关系（节选）**：\n")
        for tr in b["triples"][:8]:
            yr = f"{tr['year']}年" if isinstance(tr["year"], int) else "年份不详"
            md.append(f"- {tr['subj']} —[{tr['rel']}]→ {tr['obj']}（{yr}）")
        md.append("\n**召回文献切片**：\n")
        for j, ch in enumerate(b["chunks"], 1):
            yr = ch["year"]
            src = ch.get("source_type", "")
            pg = f"·第{ch['source_page']}页" if ch.get("source_page") else ""
            md.append(f"{j}. ［{yr}·{src}{pg}］{ch['text'][:80]}…")
        md.append(f"\n> 完整组装提示词见 `demo_outputs/q{i}_prompt.txt`\n")
        md.append("---\n")

    with open(os.path.join(OUT_DIR, "README_demo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("\n已写出 demo_outputs/（每题 qN.json + qN_prompt.txt，汇总 README_demo.md）")


if __name__ == "__main__":
    run()
