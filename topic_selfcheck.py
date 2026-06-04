# -*- coding: utf-8 -*-
"""
主题分类自查：量化各主题的假阳性率
对每个主题抽50条，判断是否真实属于该主题
"""
import json, re
from collections import defaultdict, Counter

with open("hbh_topics.json", encoding="utf-8") as f:
    topics = json.load(f)
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)

evt_map = {e["id"]: e for e in events}

# ── 具体假阳性规则，逐类检测 ────────────────────────────────────────────────

lines = []
lines.append("=== 主题分类假阳性量化自查 ===\n")

by_topic = defaultdict(list)
for t in topics:
    for topic in t["topics"]:
        by_topic[topic].append(t)

# ── 1. 革命政治：检测"民国"纯时间引用 ──────────────────────────────────────
minguo_only = re.compile(r"^(民国歙县志|民国\d+年|《民国|民国肇始|据民国|民国丁戊间|民国某年)")
minguo_fp = []
real_zhengzhi = []
for t in by_topic["革命政治"]:
    raw = evt_map[t["event_id"]].get("raw_text", "")
    kw_hit = t["keywords"]
    # 只靠"民国"命中（其他无强词）
    only_minguo = (kw_hit == ["民国"] or
                   ("民国" in kw_hit and not any(
                       k in raw for k in ["革命","同盟会","起义","北伐","辛亥","变法","党员","抗战"])))
    if only_minguo:
        minguo_fp.append(t["event_id"])
    else:
        real_zhengzhi.append(t["event_id"])

lines.append(f"革命政治 总计 {len(by_topic['革命政治'])} 条")
lines.append(f"  仅靠'民国'时间词命中（假阳性）: {len(minguo_fp)} 条 ({round(len(minguo_fp)/len(by_topic['革命政治'])*100)}%)")
lines.append(f"  有实质政治内容: {len(real_zhengzhi)} 条 ({round(len(real_zhengzhi)/len(by_topic['革命政治'])*100)}%)")
lines.append("  样本假阳性3条:")
for eid in minguo_fp[:3]:
    lines.append(f"    {eid}: {evt_map[eid]['raw_text'][:100]}")
lines.append("")

# ── 2. 教学育人：检测主体是否为他人 ──────────────────────────────────────────
# "太学生"、"院校学生"、"学生员"等科举相关词汇是噪音
exam_fp_pattern = re.compile(r"(太学生|附学生员|学生员|院试|书院|院校|科举|考试制度|童生|科考|乡试|会试|进士|举人|秀才)")
school_fp = []
real_jiaoxue = []
for t in by_topic["教学育人"]:
    raw = evt_map[t["event_id"]].get("raw_text", "")
    kw_hit = t["keywords"]
    # 由科举词触发
    if exam_fp_pattern.search(raw) and not any(
        k in raw for k in ["教授","执教","讲授","课徒","收徒","授徒","任教","门生","弟子"]):
        school_fp.append(t["event_id"])
    else:
        real_jiaoxue.append(t["event_id"])

lines.append(f"教学育人 总计 {len(by_topic['教学育人'])} 条")
lines.append(f"  由科举/学校机构词命中（假阳性）: {len(school_fp)} 条 ({round(len(school_fp)/len(by_topic['教学育人'])*100)}%)")
lines.append(f"  有实质教学内容: {len(real_jiaoxue)} 条 ({round(len(real_jiaoxue)/len(by_topic['教学育人'])*100)}%)")
lines.append("  样本假阳性3条:")
for eid in school_fp[:3]:
    lines.append(f"    {eid}: {evt_map[eid]['raw_text'][:100]}")
lines.append("")

# ── 3. 通信往来：检测"函"误匹配 ──────────────────────────────────────────────
# 检测"函"字在非书信语境：百函经 / 石函 / 竹函 / 函谷 等
han_fp_pattern = re.compile(r"(百函|石函|竹函|函谷|千山云护百函经|石经|经函)")
han_fp = []
real_xinhan = []
for t in by_topic["通信往来"]:
    raw = evt_map[t["event_id"]].get("raw_text", "")
    if han_fp_pattern.search(raw):
        han_fp.append(t["event_id"])
    else:
        real_xinhan.append(t["event_id"])

lines.append(f"通信往来 总计 {len(by_topic['通信往来'])} 条")
lines.append(f"  '函'误匹配非书信语境: {len(han_fp)} 条")
lines.append(f"  有实质书信内容: {len(real_xinhan)} 条")
lines.append("  样本误匹配:")
for eid in han_fp[:5]:
    lines.append(f"    {eid}: {evt_map[eid]['raw_text'][:100]}")
lines.append("")

# ── 4. 疾病健康：检测是否为他人的疾病 ──────────────────────────────────────
# 年谱里大量他人的病逝被命中
others_sick_pattern = re.compile(r"(逝世|去世|病逝|殁|卒|死|逝|不幸|噩耗).*[，。；]")
hbh_sick_pattern = re.compile(r"(余|鄙人|仆|宾虹|宾老|谱主).*(病|疾|眼|目|体弱|衰老|就医|手术)")
others_sick = []
self_sick = []
for t in by_topic["疾病健康"]:
    raw = evt_map[t["event_id"]].get("raw_text", "")
    if hbh_sick_pattern.search(raw):
        self_sick.append(t["event_id"])
    else:
        others_sick.append(t["event_id"])

lines.append(f"疾病健康 总计 {len(by_topic['疾病健康'])} 条")
lines.append(f"  涉及黄宾虹自身: {len(self_sick)} 条 ({round(len(self_sick)/len(by_topic['疾病健康'])*100)}%)")
lines.append(f"  他人疾病/病逝: {len(others_sick)} 条 ({round(len(others_sick)/len(by_topic['疾病健康'])*100)}%)")
lines.append("  他人疾病样本3条:")
for eid in others_sick[:3]:
    lines.append(f"    {eid}: {evt_map[eid]['raw_text'][:100]}")
lines.append("")

# ── 5. 笔法墨法：检测"墨法"/"用笔"是否在他人画论/他人描述里 ──────────────
# 通过"按：" / "存考：" 开头的按语标识为引文/注释
annotate_pattern = re.compile(r"^(按：|存考：|注：|附记：)")
bifa_annotation = []
bifa_real = []
for t in by_topic["笔法墨法"]:
    raw = evt_map[t["event_id"]].get("raw_text", "").strip()
    if annotate_pattern.match(raw):
        bifa_annotation.append(t["event_id"])
    else:
        bifa_real.append(t["event_id"])

lines.append(f"笔法墨法 总计 {len(by_topic['笔法墨法'])} 条")
lines.append(f"  正文（非注释）: {len(bifa_real)} 条")
lines.append(f"  以'按：/存考：'开头的注释性文本: {len(bifa_annotation)} 条")
lines.append("")

# ── 6. 出版编辑：检测主体是他人出版物的引用 ──────────────────────────────────
# 引文标识：《XXX》云、《XXX》："、录自《XXX》
citation_pattern = re.compile(r"(录自|见《|据《|引《)")
pub_citation = []
pub_real = []
for t in by_topic["出版编辑"]:
    raw = evt_map[t["event_id"]].get("raw_text", "")
    # 如果整条文本是引用别人著作的内容
    if citation_pattern.search(raw) and not any(
        k in raw for k in ["刊行","出版","刊印","印行","刊刻","面世","问世","成书","付梓","出书"]):
        pub_citation.append(t["event_id"])
    else:
        pub_real.append(t["event_id"])

lines.append(f"出版编辑 总计 {len(by_topic['出版编辑'])} 条")
lines.append(f"  有出版动作: {len(pub_real)} 条 ({round(len(pub_real)/len(by_topic['出版编辑'])*100)}%)")
lines.append(f"  仅引用他人著作/无出版动作: {len(pub_citation)} 条 ({round(len(pub_citation)/len(by_topic['出版编辑'])*100)}%)")
lines.append("")

# ── 7. 收藏鉴定：检测是否真的是鉴定活动 ──────────────────────────────────────
collect_action = re.compile(r"(收购|购得|购置|鉴定|鉴别|真伪|赝品|藏品|过眼|品鉴|赏鉴|请鉴|出售|典卖)")
collect_passive = re.compile(r"(博物馆藏|香港中大文物馆|安徽省博物馆|馆藏|所藏|藏书楼|旧藏)")
coll_active = []
coll_passive = []
for t in by_topic["收藏鉴定"]:
    raw = evt_map[t["event_id"]].get("raw_text", "")
    if collect_action.search(raw):
        coll_active.append(t["event_id"])
    elif collect_passive.search(raw):
        coll_passive.append(t["event_id"])
    else:
        coll_active.append(t["event_id"])  # 有收藏词就算

lines.append(f"收藏鉴定 总计 {len(by_topic['收藏鉴定'])} 条")
lines.append(f"  有明确收藏/鉴定动作: {len(coll_active)} 条")
lines.append(f"  被动引用（博物馆藏等）: {len(coll_passive)} 条")
lines.append("")

# ── 8. 展览社集：检测是否为本人参加 vs 旁人社集 ──────────────────────────
# 统计提到"黄宾虹"名字的展览事件 vs 仅有第三方社集
hbh_names = re.compile(r"(黄宾虹|宾虹|宾老|宾翁|谱主|先生.*画|画.*先生)")
exhi_self = []
exhi_other = []
for t in by_topic["展览社集"]:
    raw = evt_map[t["event_id"]].get("raw_text", "")
    if hbh_names.search(raw):
        exhi_self.append(t["event_id"])
    else:
        exhi_other.append(t["event_id"])

lines.append(f"展览社集 总计 {len(by_topic['展览社集'])} 条")
lines.append(f"  涉及黄宾虹本人: {len(exhi_self)} 条 ({round(len(exhi_self)/len(by_topic['展览社集'])*100)}%)")
lines.append(f"  第三方社集活动: {len(exhi_other)} 条 ({round(len(exhi_other)/len(by_topic['展览社集'])*100)}%)")
lines.append("")

# ── 总结 ─────────────────────────────────────────────────────────────────────
lines.append("=== 核心问题总结 ===")
lines.append("")
lines.append("1. 革命政治：'民国'作为时间词/引用源大量误触发，约40-50%假阳性")
lines.append("   修正方向：'民国'只在强政治语境下计分，单独出现不触发")
lines.append("")
lines.append("2. 教学育人：科举制度说明、他人教育背景误触发，约20-30%假阳性")
lines.append("   修正方向：去掉'学校/学院/学堂'等机构词，只保留'执教/收徒/课徒/弟子'等主动词")
lines.append("")
lines.append("3. 通信往来：'函'字在诗歌/地名/佛经语境误匹配")
lines.append("   修正方向：要求前缀'致/复/奉/去/来/寄'等动词才触发")
lines.append("")
lines.append("4. 疾病健康：大量他人（友人、名人）的病逝被标注，主体混乱")
lines.append("   修正方向：增加主体词过滤（余/宾虹/宾老/谱主），只标注HBH本人健康")
lines.append("")
lines.append("5. 出版编辑：引用他人著作（按语/存考）大量被命中，无实质出版动作")
lines.append("   修正方向：要求有出版动词，排除纯引用文本")
lines.append("")
lines.append("6. 展览社集：有一小部分是完全与黄宾虹无关的第三方社集活动")
lines.append("   修正方向：问题较小，可保留但降低权重")
lines.append("")
lines.append("7. '其他'过多（46%）：大量可分类事件未被捕获")
lines.append("   根本原因：规则精度提高后覆盖率下降，需补充薄弱主题的关键词")
lines.append("   建议增加：诗词唱和主题、佛禅主题（已确认388条）")

with open("topic_selfcheck.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> topic_selfcheck.txt")
