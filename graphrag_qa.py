# -*- coding: utf-8 -*-
"""
黄宾虹年谱 GraphRAG —— 命令行入口。

示例：
    python graphrag_qa.py "黄宾虹晚年与傅雷的交往是怎样的？"
    python graphrag_qa.py "1933年入蜀对其画风有何影响？" --no-rerank
    python graphrag_qa.py "他与南社的关系" --generate          # 需先配置大模型后端
    python graphrag_qa.py "青城山写生" --json out.json          # 导出检索+提示词

默认（未配置大模型）只输出“组装好的提示词”，可直接复制到任意本地大模型框架。
"""
import sys
import io
import json
import argparse

# 保证中文在 Windows 终端正常输出
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser(description="黄宾虹年谱 GraphRAG 问答")
    ap.add_argument("query", help="用户问题")
    ap.add_argument("--rerank", action="store_true",
                    help="启用 bge-reranker 精排（质量略升，CPU 上每问约4分钟，默认关闭）")
    ap.add_argument("--no-rerank", action="store_true", help="（兼容旧用法）强制关闭重排")
    ap.add_argument("--generate", action="store_true", help="调用已配置的大模型生成答复")
    ap.add_argument("--final-k", type=int, default=None, help="进入提示词的文本切片数")
    ap.add_argument("--show-prompt", action="store_true", help="打印完整组装提示词")
    ap.add_argument("--json", dest="json_out", default=None, help="把结果导出为 JSON 文件")
    args = ap.parse_args()

    from graphrag.pipeline import GraphRAG
    use_rr = args.rerank and not args.no_rerank
    rag = GraphRAG(use_reranker=use_rr)
    res = rag.answer(args.query,
                     generate=True if args.generate else "auto",
                     final_k=args.final_k)
    b = res["bundle"]

    print("=" * 72)
    print("问题：", args.query)
    print("命中实体：", "、".join(f"{e['name']}({e['type']})" for e in b["entities"]) or "（无）")
    print(f"知识图谱三元组：{len(b['triples'])} 条   |   文献切片：{len(b['chunks'])} 条")
    print("-" * 72)
    print("【结构化关系（节选）】")
    for t in b["triples"][:12]:
        yr = f"{t['year']}年" if isinstance(t["year"], int) else "年份不详"
        note = f"  {t['note']}" if t.get("note") else ""
        print(f"  · {t['subj']} —[{t['rel']}]→ {t['obj']}  ({yr}){note}")
    print("-" * 72)
    print("【召回文献切片】")
    for i, ch in enumerate(b["chunks"], 1):
        yr = ch["year"]
        print(f"  [{i}] {yr}·{ch.get('source_type','')}：{ch['text'][:70]}…")
    print("=" * 72)

    if res["answer"]:
        print("【大模型答复】（后端：%s）\n" % res["backend"])
        print(res["answer"])
    else:
        if args.show_prompt:
            print("【组装好的提示词（可直接喂给大模型）】\n")
            print(res["prompt"]["system_prompt"])
        else:
            print("提示：未配置大模型后端，仅完成检索与提示词组装。")
            print("      加 --show-prompt 查看完整提示词；或配置 GRAPHRAG_LLM_BASE 后加 --generate。")

    if args.json_out:
        dump = {
            "query": args.query,
            "entities": b["entities"],
            "triples": b["triples"],
            "chunks": b["chunks"],
            "years": b["years"],
            "era": b["era"],
            "prompt": res["prompt"]["system_prompt"],
            "messages": res["prompt"]["messages"],
            "answer": res["answer"],
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(dump, f, ensure_ascii=False, indent=2)
        print("\n已导出：", args.json_out)


if __name__ == "__main__":
    main()
