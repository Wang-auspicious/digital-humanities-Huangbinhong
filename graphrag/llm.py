# -*- coding: utf-8 -*-
"""
可插拔 LLM 客户端（仅用标准库，无额外依赖）。

通过环境变量配置后端，三选一：
  · OpenAI 兼容（含本地 Ollama / LM Studio / vLLM / one-api）：
        GRAPHRAG_LLM_BASE   例如 http://localhost:11434/v1  或  http://localhost:1234/v1
        GRAPHRAG_LLM_MODEL  例如 qwen2.5:14b
        GRAPHRAG_LLM_KEY    本地可留空；云端填 key
  · Anthropic：
        ANTHROPIC_API_KEY=...   （可选 GRAPHRAG_LLM_MODEL，默认 claude-... ）
  · 未配置 → dry-run：generate() 返回 None，由上层只输出“组装好的提示词”。

设计目的：即便没有运行任何大模型，本 RAG 也能交付（产出可直接喂给模型的提示词）。
"""
import os
import json
import urllib.request


def _post(url, payload, headers, timeout=120):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def backend_info():
    if os.environ.get("GRAPHRAG_LLM_BASE"):
        return ("openai", os.environ["GRAPHRAG_LLM_BASE"],
                os.environ.get("GRAPHRAG_LLM_MODEL", "local-model"))
    if os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY"):
        base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        model = (os.environ.get("ANTHROPIC_MODEL")
                 or os.environ.get("GRAPHRAG_LLM_MODEL")
                 or "claude-3-5-sonnet-latest")
        return ("anthropic", base, model)
    return (None, None, None)


def available():
    return backend_info()[0] is not None


def generate(messages, temperature=0.3, max_tokens=1500):
    """messages: [{'role','content'}...] → 文本；后端不可用返回 None。"""
    kind, base, model = backend_info()
    if kind == "openai":
        url = base.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        key = os.environ.get("GRAPHRAG_LLM_KEY")
        if key:
            headers["Authorization"] = "Bearer " + key
        payload = {"model": model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        out = _post(url, payload, headers)
        return out["choices"][0]["message"]["content"]

    if kind == "anthropic":
        url = base.rstrip("/") + "/v1/messages"
        token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
        headers = {"Content-Type": "application/json",
                   "x-api-key": token,                       # Anthropic 原生
                   "Authorization": "Bearer " + token,       # 兼容 DeepSeek 等网关
                   "anthropic-version": "2023-06-01"}
        sys = "\n".join(m["content"] for m in messages if m["role"] == "system")
        usr = [{"role": m["role"], "content": m["content"]}
               for m in messages if m["role"] != "system"]
        payload = {"model": model, "system": sys, "messages": usr,
                   "max_tokens": max_tokens, "temperature": temperature}
        out = _post(url, payload, headers)
        return "".join(b.get("text", "") for b in out.get("content", []))

    return None
