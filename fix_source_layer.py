# -*- coding: utf-8 -*-
"""Source layer v2 — deeper classification, fixing ~40% false positives"""
import json, re, os

os.chdir(r"D:\Desktop\VAST CHALLENGE")

with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

content_events = [e for e in events if e.get("type") != "year_header"]

# ── 新分类器: 多模式分层判断 ──────────────────────────────────────

# 编者按语 — high confidence
EDITOR_START = re.compile(
    r"^(按[：:]|存考[：:]|附记[：:]|拙文|赘语|赘言|"
    r"王谱|汪谱|赵谱|陈谱|黄警吾|"
    r"笔者[：:曾随]|"
    r"又[：:][「“])"
)

# 引用文献
CITATION_START = re.compile(
    r"^(录自|摘自|引自|据《|见《|参见《|"
    r"又《|\[[0-9]+\]|《[^》]{1,20}》[：:]「|"
    r"《[^》]{1,10}》[：:]“)"
)

# HBH 自撰 — 只需要这些强信号
# 核心原则: 必须能确认说话人是黄宾虹本人，而非推测
HBH_SELF_STRONG = [
    re.compile(r"^(自题[：:。，]|自题《|自题曰)"),                    # 画上自题
    re.compile(r"^(与[一-鿿]{2,5}[书函信笺][：:].{0,50}[余仆鄙吾])"), # 与XX书, 但正文自称"余/仆/鄙人"
    re.compile(r"^《自撰年谱》"),                                     # 自撰年谱
    re.compile(r"^《九十杂述》|《八十自述》|《八十感言》"),            # 自述文
    re.compile(r"^(余[年月近曾尝将乃所见作画游居归往致与购置题书曰之在于自以每素力时少])"), # 余开头
    re.compile(r"^.{0,8}(?<![一-鿿])(仆|鄙人|贱[目恙躯]|拙[笔画著稿])"),       # 谦称
    re.compile(r"^黄宾虹[书曰]"),                                    # 自署
]

# 他人来信 — 明确的非 HBH 信号
OTHERS_LETTER = re.compile(
    r"^([一-鿿]{2,5})[书函笺][：:].*(?!余[年月近曾]).*$"  # XX书：且不包含HBH第一人称
)

# 他人文字的HBH引用 — 虽是HBH语句但嵌入在他人文本中
HBH_QUOTE_IN_OTHERS = re.compile(
    r"^[一-鿿]{2,5}[书函笺][：:].{0,100}「[^」]*黄宾虹[^」]*」"  # 他人信中间接引用
)

fixes = {"editor": 0, "citation": 0, "hbh_self": 0, "others_letter": 0, "default_others": 0}

def classify_v2(evt):
    """返回 (source_type, confidence)"""
    text = evt.get("raw_text", "").strip()
    if not text:
        return ("未知", 1.0)

    # Layer 1: 编者
    if EDITOR_START.match(text):
        fixes["editor"] += 1
        return ("编者按语", 0.95)

    # Layer 2: 引用
    if CITATION_START.match(text):
        fixes["citation"] += 1
        return ("引用文献", 0.90)

    # Layer 3: HBH 自撰 — 强信号
    for pat in HBH_SELF_STRONG:
        if pat.match(text):
            fixes["hbh_self"] += 1
            return ("HBH自撰", 0.90)

    # Layer 4: 他人来信 — 提取"XX书："模式
    letter_match = re.match(r"^([一-鿿]{2,5})([书函笺])[：:]", text)
    if letter_match:
        writer = letter_match.group(1)
        # 排除 HBH 常用的署名
        if writer in {"黄宾虹", "宾虹", "朴存", "滨虹", "宾老", "黄质", "谱主"}:
            # 但如果文本里有第一人称，仍是 HBH 自撰
            if re.search(r"(余[年月近曾将乃所]|仆[近以]|鄙人|拙[笔画])", text[:150]):
                fixes["hbh_self"] += 1
                return ("HBH自撰", 0.85)
            # 否则是他人引用的 HBH 文本
            fixes["others_letter"] += 1
            return ("他人记述", 0.70)

        # 检查是不是"与XX书"然后HBH在说话
        if re.match(r"^与[一-鿿]{2,5}[书函信笺][：:]", text):
            if re.search(r"(余[年月近曾将乃所]|仆[近以]|鄙人|拙[笔画])", text[:150]):
                fixes["hbh_self"] += 1
                return ("HBH自撰", 0.85)
            # "与XX书"格式但无第一人称 → 可能是编者按
            fixes["others_letter"] += 1
            return ("他人记述", 0.60)

        # 其他人写的信 → 他人记述
        fixes["others_letter"] += 1
        return ("他人记述", 0.85)

    # Layer 5: 默认 — 他人记述
    fixes["default_others"] += 1
    return ("他人记述", 0.60)


# ── 应用并验证 ──────────────────────────────────────────────────────
changed = 0
output = []
for evt in content_events:
    new_type, conf = classify_v2(evt)
    output.append({
        "event_id": evt["id"],
        "year": evt["year"],
        "source_type": new_type,
        "confidence": round(conf, 2),
        "raw_text": evt.get("raw_text", "")[:200],
    })

with open("hbh_source_layer.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# ── 统计 ──────────────────────────────────────────────────────────
from collections import Counter
sc = Counter(s["source_type"] for s in output)
lines = []
lines.append("=== Source Layer v2 分布 ===")
for t, c in sc.most_common():
    lines.append(f"  {t}: {c} ({round(c/len(output)*100,1)}%)")
lines.append("")
lines.append("=== 分类器内部计数 ===")
for k, v in fixes.items():
    lines.append(f"  {k}: {v}")

# 抽样验证 — 各类型 10 条
lines.append("\n=== HBH自撰 抽样 (10条) ===")
hbh_samples = [s for s in output if s["source_type"] == "HBH自撰"][:10]
for s in hbh_samples:
    lines.append(f"  {s['event_id']} [{s['year']}] conf={s['confidence']}: {s['raw_text'][:100]}")

lines.append("\n=== 他人记述 抽样 (10条) ===")
others_samples = [s for s in output if s["source_type"] == "他人记述"][:10]
for s in others_samples:
    lines.append(f"  {s['event_id']} [{s['year']}] conf={s['confidence']}: {s['raw_text'][:100]}")

lines.append("\n=== 编者按语 抽样 (10条) ===")
editor_samples = [s for s in output if s["source_type"] == "编者按语"][:10]
for s in editor_samples:
    lines.append(f"  {s['event_id']} [{s['year']}] conf={s['confidence']}: {s['raw_text'][:100]}")

with open("source_v2_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))
print("\ndone")
