# -*- coding: utf-8 -*-
"""
黄宾虹 v2 人物识别召回率交叉验证 5 件套
完全不依赖 jieba，避免循环论证。
输出全部写到 recall_verification.txt（Python 直写，避免 PowerShell 乱码）。
"""
import json, re, random, sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(r"D:\Desktop\VAST CHALLENGE")
OUT = ROOT / "recall_verification.txt"

# ---------- 加载数据 ----------
text = (ROOT / "huangbinhong_simplified.txt").read_text(encoding="utf-8")
events = json.loads((ROOT / "hbh_events_raw.json").read_text(encoding="utf-8"))
alias_map = json.loads((ROOT / "alias_map.json").read_text(encoding="utf-8"))
persons = json.loads((ROOT / "hbh_persons.json").read_text(encoding="utf-8"))

# v2 识别集合 = 所有标准名 + 所有别名
v2_standard = set(alias_map.keys())
v2_alias = set()
for v in alias_map.values():
    v2_alias.update(v)
v2_tokens = v2_standard | v2_alias  # 字符串匹配 token

# 反向映射: 别名 -> 标准名
alias2std = {}
for std, al in alias_map.items():
    alias2std[std] = std
    for a in al:
        alias2std[a] = std

OUT_LINES = []
def W(s=""):
    OUT_LINES.append(s)

W("=" * 80)
W("黄宾虹 v2 人物识别召回率交叉验证报告")
W("=" * 80)
W(f"v2 标准名: {len(v2_standard)}  v2 别名: {len(v2_alias)}  合集 token: {len(v2_tokens)}")
W(f"v2 人物档案数 (hbh_persons.json): {len(persons)}")
W(f"事件总数: {len(events)}")
W(f"全文字符: {len(text):,}")
W()

# ============================================================
# 方法 1: 生卒年括注黄金标准
# ============================================================
W("=" * 80)
W("【方法 1】生卒年括注黄金标准 (X（YYYY—YYYY）)")
W("=" * 80)

# 严格格式: 中文名 2-4 字 + （YYYY—YYYY 或 YYYY-YYYY 或 ?—YYYY 等）
# 注意原文用全角破折号—
gold_pat = re.compile(r"([一-鿿]{2,4})（(\d{4})[—\-－](\d{4})）")

# 伪前缀过滤（这些字常出现在"…位是X（…）"等结构里，X 不是真姓名）
FALSE_PREFIX = set("位是即长子次子三子四子五子六子七子八子幼子嫡子季子伯仲女曰名字其乃皆为有及于而又或此那这一二三四五六七八九十百千万号谥讳子者所与其")
# 名字末字过滤（这些字常作为称呼后缀，不应是姓名一部分）
BAD_LAST = set("等君公翁氏兄弟先生人氏者也乎哉矣焉")

gold_hits = []
for m in gold_pat.finditer(text):
    name, by, dy = m.group(1), int(m.group(2)), int(m.group(3))
    if not (1750 <= by <= 1950 and 1750 <= dy <= 1960):
        continue
    if dy < by or dy - by > 110:
        continue
    # 检查名字前一个字符是否伪前缀
    pos = m.start(1)
    if pos > 0 and text[pos-1] in FALSE_PREFIX:
        continue
    # 名字尾字过滤
    if name[-1] in BAD_LAST:
        continue
    gold_hits.append((name, by, dy, m.start()))

# 去重: 同一名字多次出现取首位
seen_gold = {}
for name, by, dy, pos in gold_hits:
    if name not in seen_gold:
        seen_gold[name] = (by, dy, pos)

W(f"生卒年括注命中 (去重后): {len(seen_gold)} 个名字")

# 黄金标准覆盖检查
covered = []
uncovered = []
for name, (by, dy, pos) in seen_gold.items():
    if name in v2_tokens:
        covered.append((name, by, dy, alias2std.get(name, name)))
    else:
        # 还要检查 v2 是否以子串方式覆盖（如 v2 只收"王伯敏"全名，名字也是"王伯敏"）
        uncovered.append((name, by, dy, pos))

cov_rate = len(covered) / max(1, len(seen_gold)) * 100
W(f"被 v2 覆盖: {len(covered)} / {len(seen_gold)} = {cov_rate:.1f}%")
W()
W("--- 未被 v2 覆盖的生卒年人物 (这是真漏识别) ---")
for name, by, dy, pos in sorted(uncovered, key=lambda x: x[1]):
    ctx = text[max(0,pos-30):pos+40].replace("\n"," ")
    W(f"  {name}（{by}—{dy}） ctx: ...{ctx}...")
W()

# ============================================================
# 方法 2: 百家姓 + 名字模式穷举（不用 jieba）
# ============================================================
W("=" * 80)
W("【方法 2】百家姓正则穷举 vs v2")
W("=" * 80)

BAIJIAXING = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁"
xing_set = set(BAIJIAXING)

# 名字尾字黑名单（敬称、虚词、地名后缀）
TAIL_BLACK = set("公翁氏兄弟君老先生人也之乎哉矣焉者所与而於于其此那这下里村庄县镇城乡道路街桥山河江湖海岛省州府郡国部社院校堂寺庙塔园馆居所局会党军营帐处部处师士兵卒民众朝代年月日时分秒上中下东西南北左右内外前后大小多少高低长短")
# 第二字黑名单（"X等"、"X之"）
SINGLE_TAIL_BLACK = set("等也之乎哉矣焉者上中下年月日时人氏氏家国")

xing_candidates = Counter()
for m in re.finditer(rf"([{BAIJIAXING}])([一-鿿]{{1,3}})", text):
    full = m.group(0)
    tail = m.group(2)
    # 单字尾过滤
    if len(tail) == 1 and tail in SINGLE_TAIL_BLACK:
        continue
    # 尾字过滤
    if tail[-1] in TAIL_BLACK:
        continue
    # 全是数字字符不要
    if any(c.isdigit() for c in full):
        continue
    xing_candidates[full] += 1

# 频次过滤
HIGH_FREQ = 5
freq_candidates = {n: c for n, c in xing_candidates.items() if c >= HIGH_FREQ}
W(f"百家姓+1~3字 候选 (频次≥{HIGH_FREQ}): {len(freq_candidates)}")

# 与 v2 token 差集
not_in_v2 = {n: c for n, c in freq_candidates.items() if n not in v2_tokens}
W(f"其中不在 v2 token 集: {len(not_in_v2)}")

# 进一步用启发式排除（地名/常见词/明显非人物的）
COMMON_NONPERSON = set([
    "黄宾虹","黄宾鸿","黄宾翁","黄宾老","黄先生","黄老",  # 自指
])

# 按频次排序，取 top 100
sorted_cand = sorted(not_in_v2.items(), key=lambda x: -x[1])
W()
W(f"--- 不在 v2 的高频候选 (按频次降序，top 80) ---")
shown = 0
suspect_persons = []  # 可能是真漏识别的
for name, cnt in sorted_cand:
    if name in COMMON_NONPERSON:
        continue
    # 找一个 ctx
    pos = text.find(name)
    if pos < 0:
        continue
    ctx = text[max(0,pos-25):pos+35].replace("\n"," ")
    W(f"  {cnt:>4}  {name:6s}  ctx: ...{ctx}...")
    suspect_persons.append((name, cnt))
    shown += 1
    if shown >= 80:
        break
W()

# ============================================================
# 方法 3: 强上下文模式 NER
# ============================================================
W("=" * 80)
W("【方法 3】强上下文模式 NER vs v2")
W("=" * 80)

# 3.1 著作引用 X《Y》
pat_work = re.compile(r"([一-鿿]{2,4})《([^》]{2,40})》")
# 排除黄宾虹本人写的著作
SELF_NAMES = {"黄宾虹","宾虹","宾老","朴存","予向","黄朴存","予老","黄","虹","黄先生","黄老"}
# 名字尾字黑名单
WORK_TAIL_BLACK = set("先生君公翁老兄弟氏们的之与及和或还又即又再亦也之乎所其此那为为了由从向往就还又是即与又再为及和于在的地得")

work_authors = Counter()
for m in pat_work.finditer(text):
    name, work = m.group(1), m.group(2)
    if name in SELF_NAMES:
        continue
    if name[-1] in WORK_TAIL_BLACK:
        continue
    # 排除以年份开头
    if name[0].isdigit():
        continue
    work_authors[name] += 1

W(f"著作引用作者候选: {len(work_authors)} 个")
work_not_v2 = {n:c for n,c in work_authors.items() if n not in v2_tokens and c >= 2}
W(f"  不在 v2 (频次≥2): {len(work_not_v2)}")
W("  top 30:")
for n, c in sorted(work_not_v2.items(), key=lambda x:-x[1])[:30]:
    pos = text.find(n + "《")
    ctx = text[max(0,pos-20):pos+45].replace("\n"," ")
    W(f"    {c:>3}  {n:5s}  ...{ctx}...")
W()

# 3.2 交友模式
pat_friend = re.compile(r"(?:与|偕|及|和|同)([一-鿿]{2,4})(?:订交|订定|相识|相见|相会|订约|结识|相交|订盟)")
friend_cand = Counter()
for m in pat_friend.finditer(text):
    name = m.group(1)
    if name[-1] in WORK_TAIL_BLACK:
        continue
    friend_cand[name] += 1
friend_not_v2 = {n:c for n,c in friend_cand.items() if n not in v2_tokens}
W(f"交友模式候选: {len(friend_cand)}  不在 v2: {len(friend_not_v2)}")
for n, c in sorted(friend_not_v2.items(), key=lambda x:-x[1])[:20]:
    W(f"    {c:>2}  {n}")
W()

# 3.3 作画对象 (为/赠/寄/题/属 X 作/写/画/书/题)
pat_paint = re.compile(r"(?:为|致|赠|寄|题|属|遗)([一-鿿]{2,4})(?:作|写|画|书|题|绘|撰)")
paint_cand = Counter()
for m in pat_paint.finditer(text):
    name = m.group(1)
    if name in SELF_NAMES or name[-1] in WORK_TAIL_BLACK:
        continue
    paint_cand[name] += 1
paint_not_v2 = {n:c for n,c in paint_cand.items() if n not in v2_tokens and c >= 2}
W(f"作画对象候选: {len(paint_cand)}  不在 v2 (≥2): {len(paint_not_v2)}")
for n, c in sorted(paint_not_v2.items(), key=lambda x:-x[1])[:30]:
    W(f"    {c:>2}  {n}")
W()

# 3.4 字号定义 X，字Y 或 X，号Y
pat_zihao = re.compile(r"([一-鿿]{2,4})[，,](?:字|号|名|讳)([一-鿿]{1,3})")
zihao_cand = Counter()
for m in pat_zihao.finditer(text):
    name = m.group(1)
    if name[-1] in WORK_TAIL_BLACK or name in SELF_NAMES:
        continue
    zihao_cand[name] += 1
zihao_not_v2 = {n:c for n,c in zihao_cand.items() if n not in v2_tokens}
W(f"字号定义候选: {len(zihao_cand)}  不在 v2: {len(zihao_not_v2)}")
for n, c in sorted(zihao_not_v2.items(), key=lambda x:-x[1])[:30]:
    pos = text.find(n)
    ctx = text[max(0,pos-15):pos+40].replace("\n"," ")
    W(f"    {c:>2}  {n}   ctx: ...{ctx}...")
W()

# 3.5 汇总: 上下文模式新发现的"高置信"漏人 (>= 2 个模式同时命中 或单一模式频次>=3)
context_all = defaultdict(int)
for name in work_not_v2: context_all[name] += 1
for name in friend_not_v2: context_all[name] += 1
for name in paint_not_v2: context_all[name] += 1
for name in zihao_not_v2: context_all[name] += 1

high_conf_missed = [n for n, c in context_all.items() if c >= 2]
W(f"--- 上下文模式高置信漏识别 (≥2 类模式命中): {len(high_conf_missed)} 个 ---")
for n in high_conf_missed:
    W(f"    {n}")
W()

# ============================================================
# 方法 4: 饱和度曲线
# ============================================================
W("=" * 80)
W("【方法 4】饱和度曲线 (按时间顺序累积识别人数)")
W("=" * 80)

# 对每条事件 raw_text，用 v2 token 做匹配（贪婪：长 token 优先避免子串误吞）
tokens_sorted = sorted(v2_tokens, key=lambda x: -len(x))

def detect_persons(s):
    """返回该 raw_text 命中的标准名集合 (通过 alias2std 归并)"""
    hit_std = set()
    tmp = s
    for tk in tokens_sorted:
        if tk in tmp:
            std = alias2std.get(tk, tk)
            hit_std.add(std)
            # 删除已匹配 (避免短 token 重复在同一位置命中)
            tmp = tmp.replace(tk, "▢" * len(tk))
    return hit_std

# 按 id 切 20 段
events_sorted = sorted(events, key=lambda e: e["id"])
n_seg = 20
seg_size = len(events_sorted) // n_seg
cum_persons = set()
W(f"段数={n_seg}, 每段约 {seg_size} 条事件")
W(f"{'段':>3}  {'区间':>14}  {'累积人数':>8}  {'ΔX':>5}")
prev = 0
seg_deltas = []
for i in range(n_seg):
    lo = i * seg_size
    hi = (i+1) * seg_size if i < n_seg - 1 else len(events_sorted)
    for e in events_sorted[lo:hi]:
        cum_persons |= detect_persons(e.get("raw_text",""))
    delta = len(cum_persons) - prev
    seg_deltas.append(delta)
    W(f"{i+1:>3}  {lo+1:>5}-{hi:<5}  {len(cum_persons):>8}  {delta:>+5}")
    prev = len(cum_persons)

tail_delta = sum(seg_deltas[-3:]) / 3
W()
W(f"末 3 段平均 ΔX = {tail_delta:.1f} 人/段")
if tail_delta < 5:
    W("→ 已饱和 (末段增量 <5)，说明 v2 token 集对全文已基本覆盖")
elif tail_delta < 10:
    W("→ 接近饱和但仍有少量新增")
else:
    W("→ 未饱和，token 集仍漏不少人")
W()

# 最终累积识别的标准名数
final_count = len(cum_persons)
W(f"最终累积识别独立标准名: {final_count}")
W(f"v2 alias_map 标准名数: {len(v2_standard)}")
if final_count < len(v2_standard):
    not_hit = v2_standard - cum_persons
    W(f"alias_map 中存在但全文匹配未命中的标准名: {len(not_hit)} 个 (说明 v2 收录了一些零提及的名字)")
    for n in sorted(not_hit)[:30]:
        W(f"    {n}")
W()

# ============================================================
# 方法 5: 人工抽样包
# ============================================================
W("=" * 80)
W("【方法 5】人工抽样包 (seed=42, n=30)")
W("=" * 80)

random.seed(42)
# 只抽有实质文本的事件（raw_text 长度 >= 50）
substantive = [e for e in events if len(e.get("raw_text","")) >= 50 and e.get("type") != "year_header"]
sample = random.sample(substantive, 30)

# 上下文+百家姓候选合集（作为可能漏识别提示）
all_suspect = set([n for n,_ in suspect_persons]) | set(context_all.keys()) | set([n for n,_,_,_ in uncovered])

W(f"已抽 30 条。下方每条三列: 原文 / v2 识别 / 候选可能漏识别")
W()
for i, e in enumerate(sample, 1):
    txt = e["raw_text"][:300]
    v2_hits = detect_persons(e["raw_text"])
    # 候选漏识别 = 该事件文本中包含 suspect 但不在 v2_hits
    missed_in_event = [n for n in all_suspect if n in e["raw_text"] and alias2std.get(n,n) not in v2_hits]
    W(f"--- 样本 {i} (id={e['id']}, year={e.get('year')}) ---")
    W(f"原文: {txt}")
    W(f"v2 识别 ({len(v2_hits)}): {sorted(v2_hits)}")
    W(f"候选漏 ({len(missed_in_event)}): {missed_in_event}")
    W()

# ============================================================
# 汇总: 可信区间
# ============================================================
W("=" * 80)
W("【汇总】v2 召回率估计区间")
W("=" * 80)

# L (低估漏识别): 仅黄金标准 + 高置信上下文
strict_missed = set([n for n,_,_,_ in uncovered]) | set(high_conf_missed)
L = len(strict_missed)

# U (高估漏识别): + 方法2 高频候选 + 方法3 单一模式高频
loose_missed = strict_missed | set([n for n, c in suspect_persons[:60]]) | set(context_all.keys())
U = len(loose_missed)

total_v2 = len(v2_standard)
W(f"v2 识别标准名: {total_v2}")
W(f"  黄金标准未覆盖: {len([1 for _,_,_,_ in uncovered])} 人 ({100-cov_rate:.1f}% miss)")
W(f"  上下文高置信漏: {len(high_conf_missed)} 人")
W(f"  百家姓高频候选（含噪）: top {len(suspect_persons)} 个")
W()
W(f"漏识别人数估计区间: [{L}, {U}]")
recall_low = total_v2 / (total_v2 + U) * 100
recall_high = total_v2 / (total_v2 + L) * 100
W(f"召回率区间估计: [{recall_low:.1f}%, {recall_high:.1f}%]")
W()
W("注: L 偏严格 (黄金标准+多模式互证)，U 偏宽松 (含百家姓单模式高频，可能含噪)。")
W("    真实召回率落在区间内，建议人工核查方法 5 抽样包以收窄估计。")
W()

# 写入文件
OUT.write_text("\n".join(OUT_LINES), encoding="utf-8")
print(f"DONE -> {OUT}")
print(f"lines: {len(OUT_LINES)}")
