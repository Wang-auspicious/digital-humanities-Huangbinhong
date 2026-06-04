# -*- coding: utf-8 -*-
"""
方法 1 修正版: 黄金标准覆盖率
- 对正则切出的名字，剥前 1/2 字再查 v2 token，避免"反衬阮元"被误判
- 输出真实漏识别清单
方法 5 修正版: 人工抽样的"候选漏"用更严格的过滤（必须看起来像姓名）
"""
import json, re, random
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(r"D:\Desktop\VAST CHALLENGE")
OUT = ROOT / "recall_verification_v2.txt"

text = (ROOT / "huangbinhong_simplified.txt").read_text(encoding="utf-8")
events = json.loads((ROOT / "hbh_events_raw.json").read_text(encoding="utf-8"))
alias_map = json.loads((ROOT / "alias_map.json").read_text(encoding="utf-8"))
persons = json.loads((ROOT / "hbh_persons.json").read_text(encoding="utf-8"))

v2_standard = set(alias_map.keys())
v2_alias = set()
for v in alias_map.values():
    v2_alias.update(v)
v2_tokens = v2_standard | v2_alias

alias2std = {}
for std, al in alias_map.items():
    alias2std[std] = std
    for a in al:
        alias2std[a] = std

OUT_LINES = []
def W(s=""):
    OUT_LINES.append(s)

# 百家姓
BAIJIAXING = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁"
XING_SET = set(BAIJIAXING)

W("=" * 80)
W("方法 1 修正版: 黄金标准覆盖率 (剥前缀重判)")
W("=" * 80)

gold_pat = re.compile(r"([一-鿿]{2,4})（(\d{4})[—\-－](\d{4})）")
FALSE_PREFIX = set("位是即长子次子三子四子五子六子七子八子幼子嫡子季子伯仲女曰名字其乃皆为有及于而又或此那这一二三四五六七八九十百千万号谥讳子者所与其")
BAD_LAST = set("等君公翁氏兄弟先生人氏者也乎哉矣焉")

# 收集所有命中
raw_hits = []
for m in gold_pat.finditer(text):
    name, by, dy = m.group(1), int(m.group(2)), int(m.group(3))
    if not (1750 <= by <= 1950 and 1750 <= dy <= 1960):
        continue
    if dy < by or dy - by > 110:
        continue
    pos = m.start(1)
    if pos > 0 and text[pos-1] in FALSE_PREFIX:
        continue
    if name[-1] in BAD_LAST:
        continue
    raw_hits.append((name, by, dy, pos))

# 去重 (同名取首位)
seen = {}
for name, by, dy, pos in raw_hits:
    if name not in seen:
        seen[name] = (by, dy, pos)
W(f"原始命中 (去重): {len(seen)}")

def normalize_name(name):
    """尝试剥前缀，返回所有可能的真实姓名候选 (按优先级排序)"""
    cands = [name]
    # 剥 1 个字: 末 (len-1) 字以姓开头
    if len(name) >= 3 and name[1] in XING_SET:
        cands.append(name[1:])
    # 剥 2 个字: 末 (len-2) 字以姓开头
    if len(name) >= 4 and name[2] in XING_SET:
        cands.append(name[2:])
    return cands

# 逐一判断覆盖
truly_covered = []
truly_missed = []
fixed_by_strip = []  # 剥前缀后命中

for name, (by, dy, pos) in seen.items():
    cands = normalize_name(name)
    matched = None
    for c in cands:
        if c in v2_tokens:
            matched = c
            break
    if matched == name:
        truly_covered.append((name, by, dy, matched))
    elif matched:  # 剥前缀后命中
        fixed_by_strip.append((name, matched, by, dy))
    else:
        truly_missed.append((name, by, dy, pos))

W(f"直接覆盖: {len(truly_covered)}")
W(f"剥前缀后覆盖: {len(fixed_by_strip)}")
W(f"真实未覆盖: {len(truly_missed)}")
total_real = len(seen)
real_covered = len(truly_covered) + len(fixed_by_strip)
cov_rate = real_covered / total_real * 100
W(f"修正后真实覆盖率: {real_covered}/{total_real} = {cov_rate:.1f}%")
W()

W("--- 剥前缀后命中的 (说明 v2 收录了但正则切错了边界): ---")
for name, matched, by, dy in fixed_by_strip:
    W(f"  正则切出『{name}』 → 真实姓名『{matched}』 ({by}—{dy})")
W()

W(f"--- 真实漏识别 ({len(truly_missed)} 个，按年份排序) ---")
W("(这些是带生卒年明确标注的真人，v2 完全没收)")
for name, by, dy, pos in sorted(truly_missed, key=lambda x: x[1]):
    ctx = text[max(0,pos-25):pos+45].replace("\n"," ")
    # 也尝试剥前缀给提示
    cands = normalize_name(name)
    extra = ""
    if len(cands) > 1:
        extra = f"  [候选真名: {cands[1:]}]"
    W(f"  {name}（{by}—{dy}）{extra}")
    W(f"      ctx: ...{ctx}...")
W()

# 进一步: 在真实漏识别里, 试着判断剥前缀后的候选是否是真人 (统计该候选作为整词在文中出现频次)
W("--- 真实漏识别的『剥后候选』在全文出现频次 (>=2 提示是真人) ---")
for name, by, dy, pos in sorted(truly_missed, key=lambda x: x[1]):
    cands = normalize_name(name)
    for c in cands[1:]:
        n_occur = text.count(c)
        if n_occur >= 2:
            W(f"  {name} → 剥后『{c}』 全文出现 {n_occur} 次")
W()

# ============================================================
# 综合区间估计
# ============================================================
W("=" * 80)
W("综合区间估计 (修正版)")
W("=" * 80)

# 真实漏识别人数 (黄金标准)
n_gold_missed = len(truly_missed)
# 但要注意: 部分"真实漏识别"也可能是剥不掉的前缀问题，比如"老师受过"实际上不是人
# 进一步过滤: 排除明显不是人名的 (如"识的形成"是文论)
suspicious_nonperson = []
likely_real_missed = []
for name, by, dy, pos in truly_missed:
    # 启发式: 如果名字开头不是姓 且 剥不出来 → 可能是文论碎片
    if name[0] not in XING_SET and len(normalize_name(name)) == 1:
        suspicious_nonperson.append((name, by, dy))
    else:
        likely_real_missed.append((name, by, dy))

W(f"真实漏识别细分:")
W(f"  高置信真人 (开头是姓 or 可剥前缀): {len(likely_real_missed)}")
for n, by, dy in sorted(likely_real_missed, key=lambda x: x[1]):
    W(f"    {n}（{by}—{dy}）")
W(f"  存疑 (可能文论碎片): {len(suspicious_nonperson)}")
for n, by, dy in sorted(suspicious_nonperson, key=lambda x: x[1]):
    W(f"    {n}（{by}—{dy}）")
W()

# 基于黄金标准外推
# 假设: 黄金标准覆盖率 ≈ 整体召回率 (因为黄金标准是"明确真人"，无歧义)
gold_recall = real_covered / total_real
# 假设全文真人总数 N，v2 识别 276 -> N ≈ 276 / gold_recall
est_total = 276 / gold_recall
est_missed = est_total - 276
W(f"以黄金标准覆盖率作召回率外推:")
W(f"  黄金标准覆盖率 = {gold_recall*100:.1f}%")
W(f"  假设整体召回率近似 = {gold_recall*100:.1f}%")
W(f"  → 估计真人总数 ≈ {est_total:.0f}")
W(f"  → 估计漏识别 ≈ {est_missed:.0f} 人")
W()

# 区间
# 下界: 严格漏识别数 = 高置信黄金标准漏 + 高置信上下文模式漏
# 上界: 加上百家姓候选 top 部分 (但需要人工核验)
L = len(likely_real_missed)
# 上界用"黄金标准未覆盖外推"的方式: 假设全部 likely_real_missed 是漏，且文本中还有低频未带生卒年的人物按 (整体真人/带生卒年真人) 比例放大
# 一般文献中带生卒年的人物占 30-50%
ratio_low = 0.5  # 保守: 50% 真人都带生卒年
ratio_high = 0.3  # 激进: 只 30% 带生卒年
U_low = int(L / ratio_low)
U_high = int(L / ratio_high)
W(f"漏识别区间估计:")
W(f"  下界 L = {L} (黄金标准实证)")
W(f"  上界 U:")
W(f"    - 若 50% 真人带生卒年: U ≈ {U_low}")
W(f"    - 若 30% 真人带生卒年: U ≈ {U_high}")
W()
total_v2 = 276
recall_low = total_v2 / (total_v2 + U_high) * 100
recall_high = total_v2 / (total_v2 + L) * 100
W(f"召回率区间: [{recall_low:.1f}%, {recall_high:.1f}%]")
W(f"对应漏识别区间: [{L}, {U_high}] 人")
W()

# 综合方法 4 (饱和度) 的强佐证
W("=" * 80)
W("方法 4 饱和度佐证")
W("=" * 80)
W("末 3 段累积 ΔX = 2.7 人/段，曲线已饱和。")
W("这说明: 在『v2 token 集合所定义的人物空间』内，已覆盖文本中绝大多数。")
W("但黄金标准发现 v2 token 集本身有漏 → 主要漏在 SEED_ALIASES 设计阶段，")
W("而非匹配阶段。修补办法是把上面列出的『真实漏识别』补进 alias_map.json。")
W()

# 写文件
OUT.write_text("\n".join(OUT_LINES), encoding="utf-8")
print(f"DONE -> {OUT}")
print(f"lines: {len(OUT_LINES)}")
