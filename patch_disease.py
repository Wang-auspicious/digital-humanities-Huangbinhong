# -*- coding: utf-8 -*-
"""
用人工复核结果更新 hbh_topics.json 中的疾病健康标注
保留 29 条真实 HBH 健康记录，其余改回"其他"或移除疾病标签
"""
import json, os
os.chdir(r"D:\Desktop\VAST CHALLENGE")

# 人工确认保留的事件 ID（29条 + 边界2条 = 31条）
KEEP_DISEASE = {
    "evt_00196",  # 1886 结婚时大病
    "evt_01785",  # 1928 过港因病
    "evt_02830",  # 1934 臂酸痛
    "evt_02966",  # 1934 HBH夫人胃疾
    "evt_03658",  # 1939 就诊来平
    "evt_03733",  # 1940 目疾手术（蔡守信）
    "evt_03768",  # 1940 衰老目力减
    "evt_03795",  # 1941 内障手术（致段拭）
    "evt_03796",  # 1941 手术住院费（致顾飞）
    "evt_04038",  # 1944 患湿就诊自题
    "evt_04209",  # 1946 衰老困难
    "evt_04725",  # 1951 眼疾石谷风记
    "evt_04774",  # 1951 眼疾急剧恶化
    "evt_04799",  # 1952 目疾（白蕉信）
    "evt_04801",  # 1952 目疾（HBH自书）
    "evt_04826",  # 1952 目疾甚剧（朱砚英）
    "evt_04838",  # 1952 失视觉仍作画
    "evt_04880",  # 1953 久病目（夏承焘）
    "evt_04892",  # 1953 眼疾记录
    "evt_04911",  # 1953 白内障手术后
    "evt_04938",  # 1954 就医陆信
    "evt_04940",  # 1954 手术重见光明
    "evt_04944",  # 1954 手术后体力限制
    "evt_04948",  # 1954 李济深信目疾已疗
    "evt_04981",  # 1954 双目近盲仍画
    "evt_05070",  # 1955 病势加重住院
    "evt_05076",  # 1955 胃病甚剧
    "evt_05078",  # 1955 胃癌逝世
    "evt_05079",  # 1955 讣告
    "evt_05082",  # 1955 结语
}

with open("hbh_topics.json", encoding="utf-8") as f:
    topics = json.load(f)

removed = 0
for t in topics:
    if "疾病健康" in t["topics"] and t["event_id"] not in KEEP_DISEASE:
        t["topics"] = [x for x in t["topics"] if x != "疾病健康"]
        if not t["topics"]:
            t["topics"] = ["其他"]
        removed += 1

with open("hbh_topics.json", "w", encoding="utf-8") as f:
    json.dump(topics, f, ensure_ascii=False, indent=2)

# 验证
after = sum(1 for t in topics if "疾病健康" in t["topics"])
print(f"删除 {removed} 条误分类 | 保留 {after} 条真实疾病记录")

# 打印保留的明细
print("\n保留的疾病健康事件：")
with open("hbh_events_raw.json", encoding="utf-8") as f:
    events = json.load(f)
evt_map = {e["id"]: e for e in events}

kept = [t for t in topics if "疾病健康" in t["topics"]]
kept.sort(key=lambda x: x["year"])
lines = [f"疾病健康 最终保留 {len(kept)} 条\n"]
for t in kept:
    raw = evt_map[t["event_id"]].get("raw_text","")
    lines.append(f"[{t['year']}] {t['event_id']}: {raw[:120]}")

with open("disease_final.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> disease_final.txt")
