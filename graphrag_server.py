# -*- coding: utf-8 -*-
"""
黄宾虹 GraphRAG 本地服务 —— 供前端「数字书童」调用。

特点：
  · 一次加载 GraphRAG（bge 混合检索 + 提示词组装），常驻复用；
  · 大模型默认走 DeepSeek 的 Anthropic 兼容端点、flash 模型；
  · API key 存在本地 deepseek_key.txt，**每次请求都重新读取** —— 改这个 txt 即换 key，无需重启；
  · CORS 全开，file:// 打开的 HBH.html 可直接 fetch；
  · 多轮：前端把对话历史一起发来，服务端拼进 messages。

启动：  python graphrag_server.py        （默认 http://localhost:8765）
"""
import os
import io
import sys
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# —— 大模型后端配置（key 不在此，见 KEY_FILE）——
# 强制使用本服务自己的配置，**不继承** shell 里可能已存在的 ANTHROPIC_* （如本机 Claude Code 的代理凭据）
ROOT = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(ROOT, "deepseek_key.txt")
LLM_BASE = os.environ.get("HBH_LLM_BASE", "https://api.deepseek.com/anthropic")
LLM_MODEL = os.environ.get("HBH_LLM_MODEL", "deepseek-v4-flash")
os.environ["ANTHROPIC_BASE_URL"] = LLM_BASE       # 强制覆盖，避免继承到别处代理
os.environ["ANTHROPIC_MODEL"] = LLM_MODEL
os.environ.pop("ANTHROPIC_API_KEY", None)         # 清掉可能继承的旧 key
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)      # 由 load_key() 从本地 txt 注入

PORT = int(os.environ.get("HBH_RAG_PORT", "8765"))
MAX_HISTORY_TURNS = 6      # 仅保留最近若干轮，控制上下文与时延

# —— 心跳看门狗：网页每隔几秒 GET /heartbeat；一旦页面关闭、心跳中断超过 GRACE 秒，服务自动退出 ——
# 容忍刷新（刷新只会短暂断流，几秒内恢复）；首次心跳到达前永不退出（等待浏览器加载 + 模型载入）。
import threading
import time
HEARTBEAT_GRACE = float(os.environ.get("HBH_HEARTBEAT_GRACE", "12"))
_last_beat = [0.0]
_connected = [False]


def _watchdog():
    while True:
        time.sleep(3)
        if _connected[0] and (time.time() - _last_beat[0] > HEARTBEAT_GRACE):
            print("页面已关闭（心跳中断 %.0fs），服务自动退出。" % HEARTBEAT_GRACE)
            os._exit(0)

from graphrag.pipeline import GraphRAG
from graphrag import llm as L
from graphrag.prompt import build_prompt

print("加载 GraphRAG（首次约 20s 载入向量模型）…")
RAG = GraphRAG()           # 默认快速模式（无重排）
print("就绪。监听 http://localhost:%d" % PORT)


def load_key():
    """每次请求读取 key 文件 —— 改文件即换 key。"""
    try:
        k = open(KEY_FILE, encoding="utf-8").read().strip()
        if k:
            os.environ["ANTHROPIC_AUTH_TOKEN"] = k
            return True
    except Exception:
        pass
    return False


def answer(message, history):
    bundle = RAG.retriever.retrieve(message)
    prompt = build_prompt(RAG.corp, bundle)
    sys_msg = prompt["messages"][0]                 # system（含本轮检索上下文）
    user_msg = prompt["messages"][1]                # 当前问题
    # 多轮：system + 最近历史 + 当前问题
    hist = [m for m in (history or []) if m.get("role") in ("user", "assistant") and m.get("content")]
    hist = hist[-2 * MAX_HISTORY_TURNS:]
    messages = [sys_msg] + hist + [user_msg]

    has_key = load_key()
    if not has_key or not L.available():
        # 无 key/后端 → 检索证据兜底，书童仍可用
        ev = "；".join(f"{t['subj']}{t['rel']}{t['obj']}（{t['year']}年）"
                       for t in bundle["triples"][:5] if t.get("year"))
        chunks = "\n".join(f"· {c['text'][:90]}…" for c in bundle["chunks"][:3])
        txt = ("（未配置大模型 key，以下为检索到的依据）\n"
               + (ev + "\n" if ev else "") + chunks)
        return {"answer": txt, "backend": "retrieval-only",
                "entities": bundle["entities"]}

    out = L.generate(messages, temperature=0.2, max_tokens=2048)
    return {"answer": out, "backend": L.backend_info()[0],
            "entities": bundle["entities"]}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        if self.path.startswith("/heartbeat"):
            _connected[0] = True
            _last_beat[0] = time.time()
            return self._json(200, {"ok": True, "beat": True})
        self._json(200, {"ok": True, "model": os.environ.get("ANTHROPIC_MODEL"),
                         "service": "黄宾虹 GraphRAG"})

    def do_POST(self):
        if self.path.rstrip("/") not in ("/chat", ""):
            return self._json(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            msg = (data.get("message") or "").strip()
            if not msg:
                return self._json(400, {"error": "empty message"})
            res = answer(msg, data.get("history"))
            self._json(200, res)
        except Exception as e:
            self._json(500, {"error": str(e), "answer": "（书童后台出错：%s）" % e})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    threading.Thread(target=_watchdog, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
