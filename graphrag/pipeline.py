# -*- coding: utf-8 -*-
"""
GraphRAG 端到端管线：检索 → 组装提示词 →（可选）调用大模型。

    from graphrag.pipeline import GraphRAG
    rag = GraphRAG()                      # 加载一次，复用
    res = rag.answer("黄宾虹晚年与傅雷的交往？")
    print(res["prompt"]["system_prompt"]) # 始终可得：组装好的提示词
    print(res["answer"])                  # 若配置了大模型则为答复，否则 None
"""
from . import prompt as P
from . import llm as L
from .retriever import GraphRAGRetriever


class GraphRAG:
    def __init__(self, use_reranker=None):
        self.retriever = GraphRAGRetriever(use_reranker=use_reranker)
        self.corp = self.retriever.corp

    def answer(self, query, generate="auto", final_k=None, **gen_kwargs):
        """
        generate: "auto"=有后端就生成 / True=强制(无后端则报错) / False=只组装提示词
        返回 {query, bundle, prompt, answer, backend}
        """
        bundle = self.retriever.retrieve(query, final_k=final_k)
        prompt = P.build_prompt(self.corp, bundle)

        ans = None
        backend = L.backend_info()[0]
        do_gen = (generate is True) or (generate == "auto" and L.available())
        if do_gen:
            if not L.available():
                raise RuntimeError("未配置 LLM 后端（设置 GRAPHRAG_LLM_BASE 或 ANTHROPIC_API_KEY）")
            ans = L.generate(prompt["messages"], **gen_kwargs)

        return {
            "query": query,
            "bundle": bundle,
            "prompt": prompt,
            "answer": ans,
            "backend": backend,
        }
