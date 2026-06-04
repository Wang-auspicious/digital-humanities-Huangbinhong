# -*- coding: utf-8 -*-
"""
主题抽取脚本（规则词表版）
产出: hbh_topics.json, hbh_creations.json, hbh_density.json
"""
import json, re, os
from collections import defaultdict, Counter

os.chdir(r"D:\Desktop\VAST CHALLENGE")

# ── 1. 主题词表 ──────────────────────────────────────────────────────────────
# 每个主题一个 (keywords_required, keywords_bonus, exclusion) 三元组
# 匹配逻辑：
#   - required 中出现任意1个 → 候选
#   - bonus 每出现1个 +1分（打分排序）
#   - exclusion 出现则排除此主题

TOPIC_RULES = {
    "革命政治": {
        "required": re.compile(
            r"(革命|同盟会|起义|辛亥|民国|共和|政府|政治|军阀|北伐|国共|党员|宣统|"
            r"清廷|清朝|皇帝|帝制|康梁|变法|维新|护国|讨袁|国民党|光复|驱逐|排满|"
            r"独立|政权|内阁|议会|宪法|新军|反清|义军|秘密会|国学保存会)"
        ),
        "bonus": re.compile(r"(政治|政府|革命|党|军|反|护)"),
        "exclude": None,
    },
    "金石考据": {
        "required": re.compile(
            r"(金石|篆刻|考据|考证|铭文|碑帖|钟鼎|甲骨|铜器|玉器|瓦当|古印|"
            r"拓本|拓片|摩崖|石刻|砖文|封泥|汉砖|古玺|文字考|文字学|六书|"
            r"缪篆|鸟虫书|大篆|小篆|金文|古文字|古器物|考古|出土)"
        ),
        "bonus": re.compile(r"(金石|印|碑|铭|考|古)"),
        "exclude": None,
    },
    "笔法墨法": {
        "required": re.compile(
            r"(笔法|墨法|画法|皴法|用笔|用墨|笔意|墨气|笔墨|笔致|笔力|笔趣|"
            r"积墨|宿墨|浓墨|淡墨|焦墨|渴笔|飞白|破墨|泼墨|晕染|勾勒|皴擦|"
            r"画诀|画理|画论|画意|画气|画格|画境|丘壑|山法|树法|石法|云法|"
            r"古法|师法|写生|传神|气韵|格法|师古|临古|摹古|笔锋|中锋|侧锋)"
        ),
        "bonus": re.compile(r"(笔|墨|法|画|皴|气韵)"),
        "exclude": None,
    },
    "教学育人": {
        "required": re.compile(
            r"(教授|执教|讲授|授课|学生|门生|弟子|学校|学堂|学院|讲学|教学|"
            r"师生|拜师|收徒|授徒|教席|教职|任教|兼教|函授|课徒|传道|教员|"
            r"专科学校|美术学校|大学|中学|课程|教材|学习绘画|学画)"
        ),
        "bonus": re.compile(r"(教|学|生|师|授|课)"),
        "exclude": None,
    },
    "收藏鉴定": {
        "required": re.compile(
            r"(收藏|鉴定|鉴赏|鉴别|真伪|赝品|藏品|古物|古玩|古书画|文物|"
            r"购得|购置|购入|索购|转让|出售|典卖|藏家|收藏家|鉴赏家|书画商|"
            r"过眼|过目|寓目|品鉴|赏鉴|观摩|看画|请鉴|题签|鉴定书)"
        ),
        "bonus": re.compile(r"(藏|鉴|购|古|玩)"),
        "exclude": None,
    },
    "出版编辑": {
        "required": re.compile(
            r"(出版|编辑|刊行|刊登|付印|印行|发行|书局|出版社|印刷|排版|"
            r"校订|校勘|编纂|著作|成书|刊刻|翻印|重印|传播|流传|"
            r"《[^》]{1,15}》.*[刊出版印行]|[刊出版印行].*《[^》]{1,15}》|"
            r"国学保存会|神州国光社|商务印书馆|中华书局|文明书局|有正书局)"
        ),
        "bonus": re.compile(r"(刊|出版|印|编|书局)"),
        "exclude": None,
    },
    "家事": {
        "required": re.compile(
            r"(父亲|母亲|妻子|夫人|儿子|女儿|兄弟|姊妹|祖父|祖母|外祖|"
            r"先父|先母|先妣|先考|先室|继室|亡妻|子女|孙子|长子|次子|"
            r"家事|家务|家中|家人|家属|岳父|岳母|内人|贤内助|宋若婴|宋冰若|"
            r"病故|去世|亡故|殡葬|奔丧|守丧|丁忧|婚事|婚姻|嫁娶|婚嫁)"
        ),
        "bonus": re.compile(r"(家|父|母|妻|子|女|兄|弟)"),
        "exclude": None,
    },
    "疾病健康": {
        "required": re.compile(
            r"(患病|生病|大病|久病|病重|病危|病逝|卧病|养病|就医|就诊|"
            r"目疾|眼病|目盲|失明|眼疾|视力|手术|开刀|诊治|治疗|药|"
            r"医院|医生|大夫|中医|西医|病榻|病床|病中|病后|"
            r"健康|体弱|衰老|精力|体力|腰腿|行走不便)"
        ),
        "bonus": re.compile(r"(病|疾|医|目|眼|养)"),
        "exclude": None,
    },
    "游历": {
        "required": re.compile(
            r"(游历|游览|山水之游|游山|登山|登临|揽胜|探幽|名山|游记|"
            r"写生之旅|游黄山|游庐山|游桂林|游蜀|游川|游粤|漫游|周游)"
        ),
        "bonus": re.compile(r"(游|山|登|览)"),
        "exclude": None,
    },
    "通信往来": {
        "required": re.compile(
            r"(致函|去函|复函|奉函|手书|来信|回信|去信|书信|函|致书|复书|"
            r"[致寄][A-Za-z一-鿿]{2,8}[书函信]|"
            r"[A-Za-z一-鿿]{2,8}[书函信].*曰|"
            r"书曰|函曰|信云|按语|跋云)"
        ),
        "bonus": re.compile(r"(函|信|书|致)"),
        "exclude": None,
    },
    "展览社集": {
        "required": re.compile(
            r"(展览|画展|书画展|陈列|参展|联展|个展|群展|出品|赴展|"
            r"雅集|社集|书画社|画社|画会|诗社|吟社|词社|文社|结社|"
            r"文人雅集|集会|聚会|座谈)"
        ),
        "bonus": re.compile(r"(展|社|集|会)"),
        "exclude": None,
    },
}

# ── 2. 创作活动规则 ──────────────────────────────────────────────────────────
# 目标：识别作画/题跋/著述/出版/篆刻/书法，并抽取作品名

CREATION_RULES = {
    "作画": re.compile(
        r"(作《[^》]{1,40}》|画《[^》]{1,40}》|绘《[^》]{1,40}》|"
        r"写《[^》]{1,40}》|[作画绘写]山水|[作画]人物|[作画]花卉|[作画]花鸟|"
        r"[作画]册[页页]|[作画]横幅|[作画]立轴|[作画绘写]图|"
        r"大幅山水|册页[0-9零一二三四五六七八九十百]{1,3}|写生)"
    ),
    "题跋": re.compile(
        r"(题跋|跋[《〈「「]|[为给].*题跋|题[《〈「「]|书题|题识|"
        r"题画|题诗|题词|题[于在][^，。；]{1,20}[上后]|"
        r"为.*作跋|应.*题|请.*题)"
    ),
    "著述": re.compile(
        r"(著《[^》]{1,40}》|撰《[^》]{1,40}》|作《[^》]{1,40}》[稿文篇]|"
        r"写《[^》]{1,40}》[稿文篇]|著述|著文|写文|作文|论文|著稿|写稿|"
        r"《[^》]{1,40}》稿|完稿|成稿|草稿|定稿)"
    ),
    "出版": re.compile(
        r"(出版《[^》]{1,40}》|刊行《[^》]{1,40}》|印行《[^》]{1,40}》|"
        r"付印|刊印|付梓|刻印|出书|成书|面世|问世|发行|流通)"
    ),
    "篆刻": re.compile(
        r"(篆刻|刻印|治印|奏刀|刻[图私名]印|刻石|钤印|用印|印谱|印章|"
        r"白文|朱文|边款|印款|铁线篆|玉著篆|缪篆|古印)"
    ),
    "书法": re.compile(
        r"(书《[^》]{1,40}》|临[帖池]|临写|书法|隶书|行书|草书|楷书|篆书|"
        r"正书|魏碑|北碑|书扇|书屏|书轴|写经|抄经|录诗|录文|手稿|"
        r"书写|笔墨书)"
    ),
}

# 山水/花鸟/人物 主题分类
SUBJECT_PATTERNS = {
    "山水": re.compile(r"(山水|山峰|云山|溪山|江山|峰峦|丘壑|烟云|黄山|庐山|山居|林壑)"),
    "花鸟": re.compile(r"(花卉|花鸟|梅兰竹菊|梅花|兰花|竹|菊|松|荷花|草虫|翎毛)"),
    "人物": re.compile(r"(人物|肖像|白描|高士|仕女|罗汉|佛像)"),
    "篆刻": re.compile(r"(印|篆刻|刻石|钤)"),
    "书法": re.compile(r"(隶|行|草|楷|篆|书|碑|帖)"),
}

# ── 3. 作品名抽取 ─────────────────────────────────────────────────────────────
TITLE_RE = re.compile(r"《([^》]{1,40})》")

def extract_titles(text):
    titles = TITLE_RE.findall(text)
    # 过滤太短或明显是书名的（含"年谱""传""记"等）
    filtered = []
    for t in titles:
        if len(t) < 2:
            continue
        # 排除：论文类、书信集等
        if re.search(r"(年谱|传记|日记|全集|选集|论丛|文集|词典|字典|辞典|指南|手册)", t):
            continue
        filtered.append(t)
    return filtered

# ── 4. 主程序 ─────────────────────────────────────────────────────────────────
print("加载数据...")
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

content_events = [e for e in events if e.get("type") != "year_header"]
print(f"内容事件: {len(content_events)}")

topics_out    = []
creations_out = []
density_year  = defaultdict(lambda: {"event_count": 0, "char_count": 0})

# 用于主题漂移分析
decade_topic_counts = defaultdict(lambda: defaultdict(int))

for evt in content_events:
    text = evt.get("raw_text", "")
    year = evt.get("year", 0)
    eid  = evt["id"]
    date = evt.get("date", str(year))

    # ── 密度统计
    density_year[year]["event_count"] += 1
    density_year[year]["char_count"]  += len(text)

    # ── 主题分类
    matched_topics = []
    matched_kws    = []
    for topic, rule in TOPIC_RULES.items():
        if rule["required"].search(text):
            if rule["exclude"] and rule["exclude"].search(text):
                continue
            matched_topics.append(topic)
            # 关键词提取：取 required 里首个命中词
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
        "keywords": list(dict.fromkeys(matched_kws))[:6],
        "raw_text": text[:200],
    })

    decade = (year // 10) * 10
    for t in matched_topics:
        decade_topic_counts[decade][t] += 1

    # ── 创作活动
    for ctype, pattern in CREATION_RULES.items():
        if pattern.search(text):
            titles = extract_titles(text)
            # 判断画作主题
            subj = "其他"
            for s, sp in SUBJECT_PATTERNS.items():
                if sp.search(text):
                    subj = s
                    break

            snippet_m = pattern.search(text)
            snippet = text[max(0,snippet_m.start()-20):min(len(text),snippet_m.end()+40)]

            creations_out.append({
                "event_id":      eid,
                "year":          year,
                "date":          date,
                "creation_type": ctype,
                "title":         titles[0] if titles else "",
                "titles_all":    titles,
                "subject":       subj,
                "raw_text":      snippet,
            })
            break  # 每条事件只取第一个创作类型（主要类型）

print(f"topics: {len(topics_out)}")
print(f"creations: {len(creations_out)}")

# ── 密度 + 沉默期判断 ────────────────────────────────────────────────────────
# 沉默期：event_count < 全局均值*0.35，或比前3年均值骤降60%
all_years = sorted(density_year.keys())
global_avg = sum(density_year[y]["event_count"] for y in all_years) / len(all_years)

density_out = []
for yr in all_years:
    d = density_year[yr]
    # 前3年均值（不含当年）
    prev3 = [density_year[y]["event_count"] for y in all_years if y < yr and y >= yr-3]
    prev_avg = sum(prev3)/len(prev3) if prev3 else global_avg

    is_silent = (
        d["event_count"] < global_avg * 0.35 or
        (prev_avg > 5 and d["event_count"] < prev_avg * 0.4)
    )

    note = ""
    if is_silent:
        # 对照历史大事（简单匹配）
        if 1895 <= yr <= 1896: note = "甲午战后，社会动荡，家事为重"
        elif yr == 1903: note = "年谱记录空白年"
        elif 1915 <= yr <= 1916: note = "袁世凯帝制风波，蛰伏期"
        elif 1944 <= yr <= 1945: note = "抗战末期，北平困守"
        else: note = "记录稀少，待查"

    density_out.append({
        "year":             yr,
        "event_count":      d["event_count"],
        "char_count":       d["char_count"],
        "avg_chars":        d["char_count"] // max(d["event_count"], 1),
        "is_silent_period": is_silent,
        "note":             note,
    })

# ── 写输出 ───────────────────────────────────────────────────────────────────
with open("hbh_topics.json",    "w", encoding="utf-8") as f:
    json.dump(topics_out,    f, ensure_ascii=False, indent=2)
with open("hbh_creations.json", "w", encoding="utf-8") as f:
    json.dump(creations_out, f, ensure_ascii=False, indent=2)
with open("hbh_density.json",   "w", encoding="utf-8") as f:
    json.dump(density_out,   f, ensure_ascii=False, indent=2)

# ── 诊断报告 ─────────────────────────────────────────────────────────────────
lines = []
lines.append(f"hbh_topics.json:    {len(topics_out)} 条")
lines.append(f"hbh_creations.json: {len(creations_out)} 条")
lines.append(f"hbh_density.json:   {len(density_out)} 年")
lines.append("")

# 主题分布
tc = Counter(t for evt in topics_out for t in evt["topics"])
lines.append("── 主题分布 ──")
for topic, cnt in tc.most_common():
    pct = round(cnt/len(topics_out)*100, 1)
    lines.append(f"  {topic:10s}: {cnt:5d} ({pct}%)")
lines.append("")

# 创作类型分布
cc = Counter(c["creation_type"] for c in creations_out)
lines.append("── 创作类型分布 ──")
for ctype, cnt in cc.most_common():
    lines.append(f"  {ctype:8s}: {cnt}")
lines.append("")

# 创作主题分布
cs = Counter(c["subject"] for c in creations_out)
lines.append("── 创作题材分布 ──")
for subj, cnt in cs.most_common():
    lines.append(f"  {subj:6s}: {cnt}")
lines.append("")

# 年代际主题漂移
lines.append("── 年代际主题分布（漂移分析）──")
decades = sorted(decade_topic_counts.keys())
top_topics = [t for t,_ in tc.most_common(8)]
header = f"{'年代':6s}" + "".join(f"{t:10s}" for t in top_topics)
lines.append(header)
for dec in decades:
    total = sum(decade_topic_counts[dec].values())
    if total == 0:
        continue
    row = f"{dec}s   "
    for t in top_topics:
        cnt = decade_topic_counts[dec].get(t, 0)
        row += f"{cnt:5d}({round(cnt/total*100):2d}%)  "
    lines.append(row)
lines.append("")

# 沉默期列表
lines.append("── 沉默期 ──")
silent = [d for d in density_out if d["is_silent_period"]]
for d in silent:
    lines.append(f"  {d['year']}: {d['event_count']}事件 {d['char_count']}字  {d['note']}")
lines.append("")

# 密度峰值年
lines.append("── 密度峰值年（TOP10）──")
top_dense = sorted(density_out, key=lambda x: x["event_count"], reverse=True)[:10]
for d in top_dense:
    lines.append(f"  {d['year']}: {d['event_count']}事件 {d['char_count']}字")
lines.append("")

# 创作活动样本
lines.append("── 创作活动样本（前20条）──")
for c in creations_out[:20]:
    lines.append(f"  {c['event_id']} [{c['year']}] {c['creation_type']} [{c['subject']}] {c['title']}")
    lines.append(f"    {c['raw_text'][:80]}")
lines.append("")

# 主题漂移文字说明（年龄段比较）
lines.append("── 主题漂移观察（30/60/90岁高频词）──")
age_brackets = [(1895,1905,"30岁前后"), (1925,1935,"60岁前后"), (1950,1955,"90岁前后")]
for y0, y1, label in age_brackets:
    period_topics = Counter()
    for evt in topics_out:
        if y0 <= evt["year"] <= y1:
            for t in evt["topics"]:
                period_topics[t] += 1
    lines.append(f"  {label} ({y0}-{y1}):")
    for t, c in period_topics.most_common(5):
        lines.append(f"    {t}: {c}")
lines.append("")

with open("topics_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> topics_report.txt")
