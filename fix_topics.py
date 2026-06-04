# -*- coding: utf-8 -*-
"""
主题抽取修正版 v2
修正点：
1. 作画正则区分"作《...图/册/轴》"和"作《...篇/稿/文》"
2. 沉默期用年代内滑动窗口均值，而非全局均值
3. 输出 hbh_density.json 新增月度密度
"""
import json, re, os
from collections import defaultdict, Counter

os.chdir(r"D:\Desktop\VAST CHALLENGE")

# ── 主题词表（与 extract_topics.py 相同，不重复定义）────────────────────────
TOPIC_RULES = {
    "革命政治": {
        "required": re.compile(
            r"(革命|同盟会|起义|辛亥|民国|共和|政府|政治|军阀|北伐|国共|"
            r"清廷|清朝|帝制|康梁|变法|维新|护国|讨袁|国民党|光复|驱逐|"
            r"排满|义军|反清|秘密会|国学保存会|革命党|抗战|军事|战争|侵略)"
        ),
    },
    "金石考据": {
        "required": re.compile(
            r"(金石|考据|考证|铭文|碑帖|钟鼎|甲骨|铜器|玉器|瓦当|古印|"
            r"拓本|拓片|摩崖|石刻|砖文|封泥|汉砖|古玺|文字考|文字学|六书|"
            r"缪篆|鸟虫书|大篆|小篆|金文|古文字|古器物|考古|出土|碑学)"
        ),
    },
    "笔法墨法": {
        "required": re.compile(
            r"(笔法|墨法|画法|皴法|用笔|用墨|笔意|墨气|笔墨|笔致|笔力|笔趣|"
            r"积墨|宿墨|浓墨|淡墨|焦墨|渴笔|飞白|破墨|泼墨|晕染|勾勒|皴擦|"
            r"画诀|画理|画论|画境|丘壑|山法|树法|石法|气韵|格法|师古|临古|"
            r"摹古|笔锋|中锋|侧锋|骨法|写生[之的]?[法理])"
        ),
    },
    "教学育人": {
        "required": re.compile(
            r"(教授|执教|讲授|授课|学生|门生|弟子|学校|学堂|学院|讲学|"
            r"教学|师生|拜师|收徒|授徒|教席|教职|任教|课徒|传道|教员|"
            r"美术学校|美术学院|课程|学习绘画|学画|从学|受业)"
        ),
    },
    "收藏鉴定": {
        "required": re.compile(
            r"(收藏|鉴定|鉴赏|鉴别|真伪|赝品|藏品|古物|古玩|古书画|文物|"
            r"购得|购置|购入|索购|典卖|藏家|收藏家|鉴赏家|书画商|"
            r"过眼|寓目|品鉴|赏鉴|观摩|请鉴|题签|鉴定书|珍品|真迹)"
        ),
    },
    "出版编辑": {
        "required": re.compile(
            r"(出版|编辑|刊行|刊登|付印|印行|发行|书局|出版社|印刷|排版|"
            r"校订|校勘|编纂|著作出版|成书|刊刻|翻印|重印|"
            r"神州国光社|商务印书馆|中华书局|文明书局|有正书局|美术丛书|"
            r"《[^》]{1,15}》[刊出版印行]|[刊出版印行]《[^》]{1,15}》)"
        ),
    },
    "家事": {
        "required": re.compile(
            r"(父亲|母亲|妻子|夫人|儿子|女儿|兄弟|姊妹|祖父|祖母|"
            r"先父|先母|先妣|先考|先室|继室|亡妻|子女|孙子|长子|次子|"
            r"宋若婴|宋冰若|家事|家人|家属|岳父|岳母|内人|"
            r"病故|去世|亡故|殡葬|奔丧|守丧|丁忧|婚事|嫁娶)"
        ),
    },
    "疾病健康": {
        "required": re.compile(
            r"(患病|生病|大病|久病|病重|病危|病逝|卧病|养病|就医|就诊|"
            r"目疾|眼病|目盲|失明|眼疾|视力|手术|开刀|诊治|治疗|"
            r"医院|医生|病榻|病床|病中|病后|体弱|衰老|腿脚不便|"
            r"抱病|染病|百病)"
        ),
    },
    "游历": {
        "required": re.compile(
            r"(游历|游览|山水之游|游山|登山|登临|揽胜|探幽|名山|游记|"
            r"写生之旅|游黄山|游庐山|游桂林|游蜀|游川|游粤|漫游|周游|"
            r"万里行|壮游|旅行)"
        ),
    },
    "通信往来": {
        "required": re.compile(
            r"(致函|去函|复函|奉函|手书|来信|回信|去信|书信往来|函|致书|复书|"
            r"[致寄][一-鿿]{2,8}[书函信]|"
            r"[一-鿿]{2,8}[书函信]曰|"
            r"书曰：|函曰：|来函|接函|奉书)"
        ),
    },
    "展览社集": {
        "required": re.compile(
            r"(展览|画展|书画展|陈列|参展|联展|个展|出品|赴展|入展|"
            r"雅集|社集|书画社|画社|画会|诗社|结社|"
            r"文人雅集|聚会|同人集|书画会)"
        ),
    },
}

# ── 创作活动规则（修正版）────────────────────────────────────────────────────
# 关键修正：作画的书名必须是画作类（图/册/轴/卷/屏/幅），而非文章类（篇/稿/文/论）
CREATION_RULES = {
    "作画": re.compile(
        r"(作《[^》]{1,40}[图册轴卷屏幅景]》|"
        r"画《[^》]{1,40}》|绘《[^》]{1,40}》|"
        r"[作画绘]山水[画图]?|[作画]人物|[作画]花卉|[作画]花鸟|[作画]梅|"
        r"[作画绘写]山水册|写生[山水人物花鸟]|"
        r"册页[0-9零一二三四五六七八九十]{1,2}幅|大幅山水|巨幅|"
        r"作[山水花鸟人物松竹梅菊]画)"
    ),
    "题跋": re.compile(
        r"(为.*题跋|题跋《|[为].*作跋|应.*题|请.*题|"
        r"题[《〈「][^》〉」]{1,40}[》〉」]|"
        r"书题[《〈「]|题识|跋[《〈「]|题画诗|题画词)"
    ),
    "著述": re.compile(
        r"(著《[^》]{1,40}》|撰《[^》]{1,40}》|"
        r"著[述文]|撰[文稿]|论文|著稿|写稿|文稿|书稿|"
        r"《[^》]{1,40}》稿[本]?|完稿|成稿|草稿|定稿|"
        r"作《[^》]{1,40}[篇稿文论]》|写《[^》]{1,40}[篇稿文论]》)"
    ),
    "出版": re.compile(
        r"(出版《[^》]{1,40}》|刊行《[^》]{1,40}》|印行《[^》]{1,40}》|"
        r"付印|付梓|刻印出版|出书|成书|面世|问世|发行|刊印)"
    ),
    "篆刻": re.compile(
        r"(篆刻|刻印|治印|奏刀|刻[图私名]印|钤印|印谱|印章|"
        r"白文印|朱文印|边款|印款|铁线篆印|古玺印)"
    ),
    "书法": re.compile(
        r"(书《[^》]{1,40}》|临[帖池]|临写|书法创作|"
        r"隶书[作写]|行书[作写]|草书[作写]|楷书[作写]|篆书[作写]|"
        r"书扇|书屏|书轴|写经|抄经|录诗[于寄]|录文[于寄]|"
        r"[作书写][隶行草楷篆]书)"
    ),
}

SUBJECT_PATTERNS = {
    "山水": re.compile(r"(山水|山峰|云山|溪山|江山|峰峦|丘壑|烟云|黄山|庐山|山居|林壑|水墨山)"),
    "花鸟": re.compile(r"(花卉|花鸟|梅兰竹菊|梅花|兰花|竹[画图]|菊[画图]|松[画图]|荷花|草虫|翎毛)"),
    "人物": re.compile(r"(人物|肖像|白描|高士|仕女|罗汉|佛像|钟馗)"),
    "篆刻": re.compile(r"(篆刻|印[章谱]|刻[印石])"),
    "书法": re.compile(r"([隶行草楷篆]书|临帖|碑帖)"),
}

TITLE_RE = re.compile(r"《([^》]{2,40})》")

def extract_titles(text):
    titles = TITLE_RE.findall(text)
    return [t for t in titles if not re.search(
        r"(年谱|传记|日记|全集|选集|论丛|文集|词典|字典|辞典|指南|手册|"
        r"杂志|报|刊|学报|月刊|周刊|画报|丛书|汇编|类编|大典)", t
    )]

# ── 主程序 ────────────────────────────────────────────────────────────────────
print("加载数据...")
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

content_events = [e for e in events if e.get("type") != "year_header"]
print(f"内容事件: {len(content_events)}")

topics_out    = []
creations_out = []
density_year  = defaultdict(lambda: {"event_count": 0, "char_count": 0})
density_month = defaultdict(lambda: {"event_count": 0, "char_count": 0})
decade_topic  = defaultdict(lambda: defaultdict(int))

for evt in content_events:
    text = evt.get("raw_text", "").strip()
    year = evt.get("year", 0)
    date = evt.get("date", str(year))
    eid  = evt["id"]

    # 密度
    density_year[year]["event_count"] += 1
    density_year[year]["char_count"]  += len(text)
    # 月度：从date解析年月
    month_key = date[:7] if len(date) >= 7 else str(year)
    density_month[month_key]["event_count"] += 1
    density_month[month_key]["char_count"]  += len(text)

    # 主题
    matched_topics = []
    matched_kws    = []
    for topic, rule in TOPIC_RULES.items():
        if rule["required"].search(text):
            matched_topics.append(topic)
            m = rule["required"].search(text)
            if m:
                matched_kws.append(m.group(0)[:8])
    if not matched_topics:
        matched_topics = ["其他"]

    topics_out.append({
        "event_id": eid,
        "year":     year,
        "date":     date,
        "topics":   matched_topics,
        "keywords": list(dict.fromkeys(matched_kws))[:5],
        "raw_text": text[:200],
    })
    decade = (year // 10) * 10
    for t in matched_topics:
        decade_topic[decade][t] += 1

    # 创作活动
    for ctype, pattern in CREATION_RULES.items():
        if pattern.search(text):
            titles   = extract_titles(text)
            subj     = "其他"
            for s, sp in SUBJECT_PATTERNS.items():
                if sp.search(text):
                    subj = s
                    break
            m = pattern.search(text)
            snippet  = text[max(0,m.start()-25):min(len(text),m.end()+50)]
            creations_out.append({
                "event_id":      eid,
                "year":          year,
                "date":          date,
                "creation_type": ctype,
                "title":         titles[0] if titles else "",
                "titles_all":    titles[:5],
                "subject":       subj,
                "raw_text":      snippet,
            })
            break

# ── 密度 + 沉默期（滑动窗口版）────────────────────────────────────────────────
# 对早年(1865-1906)用早年均值；1907年之后用5年滑动窗口均值
all_years = sorted(density_year.keys())

# 分两段计算基准
early_years  = [y for y in all_years if y <= 1906]
modern_years = [y for y in all_years if y > 1906]

if early_years:
    early_avg = sum(density_year[y]["event_count"] for y in early_years) / len(early_years)
else:
    early_avg = 10

def get_window_avg(yr, window=5):
    prev = [y for y in all_years if y < yr and y >= yr - window]
    if not prev:
        return early_avg
    return sum(density_year[y]["event_count"] for y in prev) / len(prev)

density_out = []
for yr in all_years:
    d = density_year[yr]
    cnt = d["event_count"]
    chars = d["char_count"]

    if yr <= 1906:
        baseline = early_avg
        is_silent = cnt < early_avg * 0.3
    else:
        baseline = get_window_avg(yr, 5)
        # 事件数 < 基准40%，且字数/条数不超过平均200字（排除长文少条情况）
        is_silent = (cnt < baseline * 0.4 and
                     (cnt == 0 or chars / cnt < 800))

    note = ""
    if is_silent:
        if yr == 1896: note = "甲午战后动乱期，年谱空白"
        elif yr == 1903: note = "年谱确认空白年"
        elif 1915 <= yr <= 1916: note = "袁世凯帝制风波，蛰伏报社"
        elif yr == 1927: note = "北伐清党后局势紧张"
        elif 1944 <= yr <= 1945: note = "抗战末期北平封锁，行动受限"
        elif yr <= 1906: note = "早年年谱记录天然稀疏"
        else: note = "记录相对稀少，待查"

    density_out.append({
        "year":             yr,
        "event_count":      cnt,
        "char_count":       chars,
        "avg_chars_per_evt": chars // max(cnt, 1),
        "window_baseline":  round(baseline, 1),
        "is_silent_period": is_silent,
        "note":             note,
    })

# ── 月度密度 ──────────────────────────────────────────────────────────────────
monthly_out = []
for ym in sorted(density_month.keys()):
    d = density_month[ym]
    monthly_out.append({
        "year_month": ym,
        "year":  int(ym[:4]),
        "event_count": d["event_count"],
        "char_count":  d["char_count"],
    })

# ── 写输出 ────────────────────────────────────────────────────────────────────
with open("hbh_topics.json",    "w", encoding="utf-8") as f:
    json.dump(topics_out,    f, ensure_ascii=False, indent=2)
with open("hbh_creations.json", "w", encoding="utf-8") as f:
    json.dump(creations_out, f, ensure_ascii=False, indent=2)
with open("hbh_density.json",   "w", encoding="utf-8") as f:
    json.dump({
        "yearly":  density_out,
        "monthly": monthly_out,
    }, f, ensure_ascii=False, indent=2)

# ── 诊断报告 ──────────────────────────────────────────────────────────────────
lines = []
lines.append(f"hbh_topics.json:    {len(topics_out)} 条")
lines.append(f"hbh_creations.json: {len(creations_out)} 条")
lines.append(f"hbh_density yearly: {len(density_out)} 年")
lines.append(f"hbh_density monthly:{len(monthly_out)} 月")
lines.append("")

tc = Counter(t for evt in topics_out for t in evt["topics"])
lines.append("── 主题分布 ──")
for t, c in tc.most_common():
    lines.append(f"  {t:10s}: {c:5d} ({round(c/len(topics_out)*100,1)}%)")
lines.append("")

cc = Counter(c["creation_type"] for c in creations_out)
lines.append("── 创作类型分布 ──")
for ct, c in cc.most_common():
    lines.append(f"  {ct:6s}: {c}")
lines.append("")

cs = Counter(c["subject"] for c in creations_out)
lines.append("── 创作题材分布 ──")
for s, c in cs.most_common():
    lines.append(f"  {s}: {c}")
lines.append("")

# 沉默期（仅列1907年后的真实沉默期）
lines.append("── 真实沉默期（1907年后）──")
real_silent = [d for d in density_out if d["is_silent_period"] and d["year"] > 1906]
for d in real_silent:
    lines.append(f"  {d['year']}: {d['event_count']}事件 {d['char_count']}字  基准:{d['window_baseline']}  {d['note']}")
lines.append("")

lines.append("── 早年记录稀疏期（1865-1906）──")
early_silent = [d for d in density_out if d["is_silent_period"] and d["year"] <= 1906]
lines.append(f"  共 {len(early_silent)} 年记录稀疏（早年天然稀疏，非活动沉默）")
lines.append("")

# 密度峰值年
lines.append("── 密度峰值年（TOP15）──")
top_dense = sorted(density_out, key=lambda x: x["event_count"], reverse=True)[:15]
for d in top_dense:
    lines.append(f"  {d['year']}: {d['event_count']}条 {d['char_count']}字")
lines.append("")

# 年代际主题漂移
lines.append("── 年代际主题漂移 ──")
top_topics = [t for t, _ in tc.most_common(9) if t != "其他"]
header = f"{'年代':6s}" + "".join(f"{t[:4]:8s}" for t in top_topics)
lines.append(header)
for dec in sorted(decade_topic.keys()):
    total = sum(decade_topic[dec].values())
    if total < 5:
        continue
    row = f"{dec}s  "
    for t in top_topics:
        c = decade_topic[dec].get(t, 0)
        row += f"{c:3d}({round(c/total*100):2d}%)  "
    lines.append(row)
lines.append("")

# 主题漂移叙述
lines.append("── 主题漂移叙述（30/60/90岁）──")
brackets = [(1895,1905,"~30岁"), (1925,1935,"~60岁"), (1950,1955,"~90岁")]
for y0, y1, label in brackets:
    pt = Counter()
    for evt in topics_out:
        if y0 <= evt["year"] <= y1:
            for t in evt["topics"]:
                pt[t] += 1
    lines.append(f"  {label} ({y0}-{y1}):")
    for t, c in pt.most_common(6):
        lines.append(f"    {t}: {c}")
lines.append("")

# 创作活动样本（精选20条，排除明显误判）
lines.append("── 创作活动样本（前30条）──")
for c in creations_out[:30]:
    lines.append(f"  {c['event_id']} [{c['year']}] {c['creation_type']:4s} [{c['subject']:4s}] {c['title']}")
    lines.append(f"    {c['raw_text'][:80]}")
lines.append("")

with open("topics_report_v2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> topics_report_v2.txt")
