# -*- coding: utf-8 -*-
"""
主题抽取 v3 — 修正主体性问题
核心修改：
1. 展览社集：要求含黄宾虹相关词，否则降为"旁证"标签
2. 疾病健康：要求主体是黄宾虹本人
3. 革命政治：去掉纯"民国"时间词触发
4. 通信往来："函"字要求动词前缀
5. 新增"诗词唱和"主题（869条已验证）
6. 新增"佛禅精神"主题（388条已验证）
"""
import json, re, os
from collections import defaultdict, Counter

os.chdir(r"D:\Desktop\VAST CHALLENGE")

# ── 黄宾虹主体词 ──────────────────────────────────────────────────────────────
HBH_SUBJECT = re.compile(
    r"(黄宾虹|宾虹|宾老|宾翁|谱主|朴存|滨虹|余(?:年|近|曾|尝|将|乃|所|见|作|画|游|居|归|往|致|与|购|藏|题|书)|"
    r"先生(?:画|书|作|游|居|题|收|鉴|致|与)|鄙人|仆(?:近|以|见|作)|"
    r"宾虹先生|黄先生|黄老)"
)

# ── 主题词表 v3 ──────────────────────────────────────────────────────────────
TOPIC_RULES_V3 = {
    "革命政治": {
        "required": re.compile(
            r"(革命|同盟会|起义|辛亥革命|清廷|帝制|康梁|戊戌变法|维新变法|护国|讨袁|"
            r"国民党|光复会|排满|反清|义军|反帝|北伐|抗战|日军|侵略|沦陷|"
            r"革命党|秘密会|共产党|解放|新中国|土改)"
            # 注意：单独"民国"不在此列，只在有实质词汇时才触发
        ),
        "exclude": None,
    },
    "金石考据": {
        "required": re.compile(
            r"(金石|考据|考证|铭文|碑帖|钟鼎|甲骨|铜器|玉器|瓦当|古印|"
            r"拓本|拓片|摩崖|砖文|封泥|汉砖|古玺|文字考|文字学|六书|"
            r"缪篆|大篆|小篆|金文|古文字|考古|出土|碑学|摩挲金石)"
        ),
        "exclude": None,
    },
    "笔法墨法": {
        "required": re.compile(
            r"(笔法|墨法|画法|皴法|用笔|用墨|笔意|墨气|笔墨|笔致|笔力|笔趣|"
            r"积墨|宿墨|浓墨|淡墨|焦墨|渴笔|飞白|破墨|泼墨|晕染|勾勒|皴擦|"
            r"画诀|画理|画论|画境|丘壑|气韵生动|格法|临古|摹古|笔锋|中锋|侧锋|"
            r"骨法用笔|写生[之的]法)"
        ),
        "exclude": None,
    },
    "教学育人": {
        "required": re.compile(
            r"(执教|讲授|授课|课徒|收徒|授徒|教席|任教|兼教|函授|传道|教员|"
            r"门生|弟子|从学|受业|学画|拜师|学生来访|学生求教|来学|习画)"
        ),
        "exclude": None,
    },
    "收藏鉴定": {
        "required": re.compile(
            r"(收藏|鉴定|鉴赏|鉴别|真伪|赝品|藏品|古书画|文物|"
            r"购得|购置|购入|索购|典卖|过眼|品鉴|赏鉴|请鉴|"
            r"真迹|珍品|摩挲古物|古器物|古玺印|鉴定书|辨真伪)"
        ),
        "exclude": None,
    },
    "出版编辑": {
        "required": re.compile(
            r"(刊行|刊登|付印|印行|发行|刊刻|翻印|重印|付梓|出书|成书|面世|问世|"
            r"神州国光社|商务印书馆|中华书局|文明书局|有正书局|《美术丛书》|"
            r"编纂|编辑|校订|校勘|撰稿|著述成书)"
        ),
        "exclude": None,
    },
    "家事": {
        "required": re.compile(
            r"(父亲|母亲|妻子|夫人|儿子|女儿|兄弟|姊妹|祖父|祖母|"
            r"先父|先母|先妣|先考|先室|继室|亡妻|宋若婴|宋冰若|洪夫人|"
            r"长子|次子|子女|家事|婚事|嫁娶|病故|去世|奔丧|守丧|丁忧)"
        ),
        "exclude": None,
    },
    "疾病健康": {
        # v3：增加主体过滤 —— 要求附近有 HBH 主体词
        # 实现方式：先宽泛匹配关键词，在 classify() 里再做主体检测
        "required": re.compile(
            r"(患病|生病|大病|久病|病重|病危|卧病|养病|就医|就诊|"
            r"目疾|眼病|目盲|失明|眼疾|视力模糊|手术|开刀|诊治|"
            r"抱病|抱恙|病榻|病床|病中|体弱|衰老|目力不济|"
            r"余.*病|病.*余|仆.*病|宾虹.*病|宾老.*病|谱主.*病)"
        ),
        "exclude": None,
        "require_subject": True,  # 需要检测主体
    },
    "游历": {
        "required": re.compile(
            r"(游历|游览|山水之游|游山|登山|登临|揽胜|探幽|游记|"
            r"写生之旅|游黄山|游庐山|游桂林|游蜀|游川|漫游|周游|"
            r"万里行|壮游|行旅|旅行记|途中|道中|登顶)"
        ),
        "exclude": None,
    },
    "通信往来": {
        "required": re.compile(
            r"([致寄复奉去来接]函|[致寄复奉去来接]书|手书|去信|回信|书信往来|"
            r"[致寄复奉去来]信|[致寄复奉去来][一-鿿]{2,8}[书函信]|"
            r"书曰：|函曰：|来函|接函|奉书|复书|顷诵手书|诵来函|奉诵教言)"
        ),
        "exclude": None,
    },
    "展览社集": {
        "required": re.compile(
            r"(展览|画展|书画展|陈列|参展|联展|个展|出品|入展|"
            r"雅集|社集|书画社|画社|画会|诗社|结社|"
            r"书画会|同人集|书画雅集|联展|征件|观摩会)"
        ),
        "require_hbh": True,  # v3 新增：要求有 HBH 关联词
        "exclude": None,
    },
    "诗词唱和": {  # v3 新增
        "required": re.compile(
            r"(题诗|题词|律诗|绝句|七律|五律|七绝|五绝|联诗|唱和|酬唱|"
            r"吟诗|诗稿|诗集|诗社|题画诗|诗跋|词曲|吟咏|赠诗|诗云|"
            r"诗稿印行|诗册|诗集出版)"
        ),
        "exclude": None,
    },
    "佛禅意境": {  # v3 新增（已确认388条）
        "required": re.compile(
            r"(禅画|禅意|禅境|佛法入画|以禅喻画|参禅|禅宗|居士|"
            r"佛像|罗汉|菩萨画|禅院|禅堂|禅定|静虑|空灵|无为|"
            r"虚静|寂静|心源|造化心源|天人合一|道法自然)"
        ),
        "exclude": None,
    },
}

CREATION_RULES = {
    "作画": re.compile(
        r"(作《[^》]{1,40}[图册轴卷屏幅景]》|"
        r"画《[^》]{1,40}》|绘《[^》]{1,40}》|"
        r"[作画绘]山水[画图]?|[作画]人物|[作画]花卉|[作画]花鸟|[作画]梅|"
        r"写生[山水人物花鸟]|册页[0-9零一二三四五六七八九十]{1,2}幅|"
        r"作[山水花鸟人物松竹梅菊]画)"
    ),
    "题跋": re.compile(
        r"(为.*题跋|题跋《|为.*作跋|请.*题|应.*题|题识|跋《|题画诗|题画词)"
    ),
    "著述": re.compile(
        r"(著《[^》]{1,40}》|撰《[^》]{1,40}》|"
        r"著[述文]|撰[文稿]|写稿|书稿|完稿|成稿|草稿|定稿|"
        r"作《[^》]{1,40}[篇稿文论]》|写《[^》]{1,40}[篇稿文论]》)"
    ),
    "出版": re.compile(
        r"(出版《[^》]{1,40}》|刊行《[^》]{1,40}》|印行《[^》]{1,40}》|"
        r"付印|付梓|出书|成书|面世|问世|发行|刊印)"
    ),
    "篆刻": re.compile(
        r"(篆刻|刻印|治印|奏刀|刻[图私名]印|钤印|印谱|边款|印款|古玺印)"
    ),
    "书法": re.compile(
        r"(书《[^》]{1,40}》|临[帖池]|临写|"
        r"[隶行草楷篆]书[作写]|书扇|书屏|书轴|写经|抄经|"
        r"[作书写][隶行草楷篆]书)"
    ),
}

SUBJECT_PATTERNS = {
    "山水": re.compile(r"(山水|山峰|云山|溪山|峰峦|丘壑|烟云|黄山|庐山|林壑|水墨山)"),
    "花鸟": re.compile(r"(花卉|花鸟|梅兰竹菊|梅花|兰花|竹[画图]|荷花|草虫|翎毛)"),
    "人物": re.compile(r"(人物|肖像|白描|高士|仕女|罗汉|佛像|钟馗)"),
    "篆刻": re.compile(r"(篆刻|印[章谱]|刻[印石])"),
    "书法": re.compile(r"([隶行草楷篆]书|临帖|碑帖)"),
}
TITLE_RE = re.compile(r"《([^》]{2,40})》")

def extract_titles(text):
    return [t for t in TITLE_RE.findall(text) if not re.search(
        r"(年谱|传记|日记|全集|选集|论丛|文集|词典|指南|杂志|报|刊|学报|月刊|周刊|丛书|汇编|大典|地方志|县志)", t
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

    density_year[year]["event_count"] += 1
    density_year[year]["char_count"]  += len(text)
    month_key = date[:7] if len(date) >= 7 else str(year)
    density_month[month_key]["event_count"] += 1
    density_month[month_key]["char_count"]  += len(text)

    matched_topics = []
    matched_kws    = []
    hbh_present    = bool(HBH_SUBJECT.search(text))

    for topic, rule in TOPIC_RULES_V3.items():
        if not rule["required"].search(text):
            continue
        # 主体过滤：展览社集要求有HBH关联
        if rule.get("require_hbh") and not hbh_present:
            continue
        # 主体过滤：疾病健康要求主体是HBH
        if rule.get("require_subject"):
            # 疾病词出现时，要求附近（整条文本）有HBH主体词
            if not hbh_present:
                continue
        if rule.get("exclude") and rule["exclude"].search(text):
            continue
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
            titles  = extract_titles(text)
            subj    = "其他"
            for s, sp in SUBJECT_PATTERNS.items():
                if sp.search(text):
                    subj = s
                    break
            m       = pattern.search(text)
            snippet = text[max(0,m.start()-25):min(len(text),m.end()+50)]
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

# ── 密度统计（沿用 v2 逻辑）─────────────────────────────────────────────────
all_years = sorted(density_year.keys())
early_years  = [y for y in all_years if y <= 1906]
early_avg    = sum(density_year[y]["event_count"] for y in early_years) / max(len(early_years),1)

def get_window_avg(yr, window=5):
    prev = [y for y in all_years if y < yr and y >= yr - window]
    return sum(density_year[y]["event_count"] for y in prev) / max(len(prev),1) if prev else early_avg

density_out = []
for yr in all_years:
    d   = density_year[yr]
    cnt = d["event_count"]
    chars = d["char_count"]
    if yr <= 1906:
        baseline = early_avg
        is_silent = cnt < early_avg * 0.3
    else:
        baseline = get_window_avg(yr)
        is_silent = (cnt < baseline * 0.4 and (cnt == 0 or chars / cnt < 800))
    note = ""
    if is_silent:
        if yr == 1896: note = "甲午战后动乱期，年谱空白"
        elif yr == 1903: note = "年谱确认空白年"
        elif 1915 <= yr <= 1916: note = "袁世凯帝制风波，蛰伏期"
        elif 1944 <= yr <= 1945: note = "抗战末期北平封锁"
        elif yr <= 1906: note = "早年年谱记录天然稀疏"
        else: note = "记录相对稀少"
    density_out.append({
        "year": yr, "event_count": cnt, "char_count": chars,
        "avg_chars_per_evt": chars // max(cnt,1),
        "window_baseline": round(baseline,1),
        "is_silent_period": is_silent, "note": note,
    })

monthly_out = [{"year_month": ym, "year": int(ym[:4]),
                "event_count": d["event_count"], "char_count": d["char_count"]}
               for ym, d in sorted(density_month.items())]

# ── 写输出 ────────────────────────────────────────────────────────────────────
with open("hbh_topics.json",    "w", encoding="utf-8") as f:
    json.dump(topics_out,    f, ensure_ascii=False, indent=2)
with open("hbh_creations.json", "w", encoding="utf-8") as f:
    json.dump(creations_out, f, ensure_ascii=False, indent=2)
with open("hbh_density.json",   "w", encoding="utf-8") as f:
    json.dump({"yearly": density_out, "monthly": monthly_out}, f, ensure_ascii=False, indent=2)

# ── 报告 ──────────────────────────────────────────────────────────────────────
tc = Counter(t for evt in topics_out for t in evt["topics"])
lines = [f"topics: {len(topics_out)}", f"creations: {len(creations_out)}", ""]
lines.append("── 主题分布 ──")
for t, c in tc.most_common():
    lines.append(f"  {t:10s}: {c:5d} ({round(c/len(topics_out)*100,1)}%)")
lines.append("")
cc = Counter(c["creation_type"] for c in creations_out)
lines.append("── 创作类型 ──")
for ct, c in cc.most_common(): lines.append(f"  {ct}: {c}")
lines.append("")
# 真实沉默期
lines.append("── 真实沉默期（1907后）──")
for d in density_out:
    if d["is_silent_period"] and d["year"] > 1906:
        lines.append(f"  {d['year']}: {d['event_count']}条 {d['note']}")
lines.append("")
# 主题漂移
lines.append("── 年代际主题漂移 ──")
top_topics = [t for t,_ in tc.most_common(9) if t != "其他"]
hdr = f"{'年代':6s}" + "".join(f"{t[:4]:8s}" for t in top_topics)
lines.append(hdr)
for dec in sorted(decade_topic.keys()):
    total = sum(decade_topic[dec].values())
    if total < 5: continue
    row = f"{dec}s  "
    for t in top_topics:
        c = decade_topic[dec].get(t,0)
        row += f"{c:3d}({round(c/total*100):2d}%)  "
    lines.append(row)
lines.append("")
lines.append("── 主题漂移叙述（30/60/90岁）──")
brackets = [(1895,1905,"~30岁"), (1925,1935,"~60岁"), (1950,1955,"~90岁")]
for y0, y1, label in brackets:
    pt = Counter()
    for evt in topics_out:
        if y0 <= evt["year"] <= y1:
            for t in evt["topics"]: pt[t] += 1
    lines.append(f"  {label} ({y0}-{y1}):")
    for t, c in pt.most_common(6): lines.append(f"    {t}: {c}")
lines.append("")

with open("topics_report_v3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> topics_report_v3.txt")
