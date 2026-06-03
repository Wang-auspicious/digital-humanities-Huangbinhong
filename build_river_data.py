"""
build_river_data.py v2 — 按《黄宾虹交友圈·河流图设计规范》重构
输出 6 层 ThemeRiver 数据 + 气泡卡片数据 → hbh_river_data.js
"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, 'hbh_interactions.json'), 'r', encoding='utf-8') as f:
    interactions = json.load(f)
with open(os.path.join(BASE, 'hbh_persons.json'), 'r', encoding='utf-8') as f:
    persons = json.load(f)

# ── 6 层映射（设计规范 §2）─────────────────────────────────────
# 原 7 圈层 → 6 流带层（自上而下，明→暗）
LAYER_MAP = {
    '艺术': '书画同道',
    '学术': '金石考古',
    '师友': '诗文师友',
    '家庭': '诗文师友',   # 家庭并入诗文师友
    '出版': '出版传媒',
    '政治': '政商护持',
    '其他': '教育弟子',   # 其他归入教育/晚辈
}
LAYER_ORDER = ['书画同道', '金石考古', '诗文师友', '出版传媒', '教育弟子', '政商护持']
LAYER_COLORS = {
    '书画同道': '#EBD9D3',
    '金石考古': '#E3B7A8',
    '诗文师友': '#C8736A',
    '出版传媒': '#9CA89A',
    '教育弟子': '#8C9AA6',
    '政商护持': '#6E6E86',
}

person_cat = {p['standard_name']: p.get('category', '其他') for p in persons}
person_meta = {p['standard_name']: p for p in persons}

# ── 1. 年度 × 6 层统计 ──
years_dict = {}
for it in interactions:
    y = str(it['year'])
    cat = person_cat.get(it['person'], '其他')
    layer = LAYER_MAP.get(cat, '教育弟子')
    if y not in years_dict:
        years_dict[y] = {'total': 0, 'active': set(), 'layers': {l: 0 for l in LAYER_ORDER}}
    years_dict[y]['total'] += 1
    years_dict[y]['active'].add(it['person'])
    years_dict[y]['layers'][layer] += 1

years_list = []
for yr in range(1865, 1956):
    sy = str(yr)
    d = years_dict.get(sy, {'total': 0, 'active': set(), 'layers': {l: 0 for l in LAYER_ORDER}})
    years_list.append({
        'year': yr,
        'total': d['total'],
        'active': len(d['active']) if isinstance(d['active'], set) else d['active'],
        'layers': d['layers'],
    })

# ── 2. ThemeRiver 堆叠数据 ──
# 为每层生成平滑曲线所需的数据点（91年 × 6层）
# stackOffsetWiggle: 以中轴浮动，上下交替堆叠
# 简化：baseline 居中，每层厚度 = sqrt(count) 做面积映射
peak_total = max(y['total'] for y in years_list)  # 661
theme_river = {'years': [], 'layers': []}
for yr_data in years_list:
    theme_river['years'].append({
        'year': yr_data['year'],
        'total': yr_data['total'],
    })
for li, layer_name in enumerate(LAYER_ORDER):
    values = [yr_data['layers'][layer_name] for yr_data in years_list]
    theme_river['layers'].append({
        'name': layer_name,
        'color': LAYER_COLORS[layer_name],
        'index': li,
        'values': values,
    })

# ── 3. 按人聚合（供卡片选取 + 趋势查询）─────────────────────
person_ints = {}  # name -> [{year, type}]
for it in interactions:
    nm = it['person']
    if nm not in person_ints:
        person_ints[nm] = []
    person_ints[nm].append({'year': it['year'], 'type': it['interaction_type']})

streams = []
for nm, ints_list in person_ints.items():
    years_set = sorted(set(i['year'] for i in ints_list))
    meta = person_meta.get(nm, {})
    type_counts = {}
    for i in ints_list:
        t = i['type']; type_counts[t] = type_counts.get(t, 0) + 1
    primary_type = max(type_counts, key=type_counts.get) if type_counts else '其他'

    by_year = {}
    for i in ints_list:
        y = i['year']
        if y not in by_year:
            by_year[y] = {'total': 0, 'types': {}}
        by_year[y]['total'] += 1
        by_year[y]['types'][i['type']] = by_year[y]['types'].get(i['type'], 0) + 1

    streams.append({
        'person': nm,
        'cat': meta.get('category', '其他'),
        'layer': LAYER_MAP.get(meta.get('category', '其他'), '教育弟子'),
        'first': meta.get('first_mention', years_set[0] if years_set else 1865),
        'last': meta.get('last_mention', years_set[-1] if years_set else 1955),
        'total': len(ints_list),
        'primaryType': primary_type,
        'typeCounts': type_counts,
        'years': years_set,
        'peakYear': max(by_year, key=lambda k: by_year[k]['total']) if by_year else None,
        'byYear': {str(k): v for k, v in by_year.items()},
    })
streams.sort(key=lambda s: s['total'], reverse=True)

# ── 4. 气泡卡片（~20 人，按设计规范 §4.4）─────────────────
# 选互动的 top 人物 + 历史关键人物，跨各层
KEY_PEOPLE = {
    '邓实': '出版传媒', '黄节': '出版传媒', '柳亚子': '诗文师友', '陈去病': '诗文师友',
    '齐白石': '书画同道', '张大千': '书画同道', '傅雷': '诗文师友', '潘天寿': '教育弟子',
    '蔡守': '金石考古', '许承尧': '诗文师友', '王一亭': '书画同道', '叶恭绰': '政商护持',
    '张善孖': '书画同道', '俞剑华': '教育弟子', '王伯敏': '教育弟子', '李可染': '教育弟子',
    '夏承焘': '诗文师友', '陆丹林': '出版传媒', '徐悲鸿': '书画同道', '陈师曾': '书画同道',
    '黄鞠如': '诗文师友', '倪逸甫': '教育弟子',
}

cards = []
for nm, layer in KEY_PEOPLE.items():
    s = next((x for x in streams if x['person'] == nm), None)
    if not s:
        # 尝试从 persons 直接取
        p = person_meta.get(nm, {})
        s = {
            'person': nm, 'layer': layer,
            'first': p.get('first_mention', 0), 'last': p.get('last_mention', 0),
            'total': p.get('total_mentions', 0), 'primaryType': '其他',
            'typeCounts': {}, 'years': [], 'peakYear': None,
        }
    cards.append({
        'person': nm,
        'layer': layer,
        'first': s['first'], 'last': s['last'],
        'total': s['total'],
        'primaryType': s.get('primaryType', '其他'),
        'peakYear': s.get('peakYear') or ((s['first'] + s['last']) // 2 if s['first'] and s['last'] else 1920),
        'years': s.get('years', []),
    })
cards.sort(key=lambda c: c['first'])

# ── 5. 叙事锚点 ──
anchors = [
    {'year': 1907, 'label': '迁居海上', 'desc': '赴上海，入神州国光社，交游圈开始快速扩张'},
    {'year': 1928, 'label': '海上鼎盛', 'desc': '南行广州香港桂林，艺术学术交游达洪峰'},
    {'year': 1937, 'label': '困居北平', 'desc': '抗战爆发，老友凋零，闭门治学作画'},
]

# ── 6. 时代分段（底部色带） ──
eras = [
    {'start': 1865, 'end': 1907, 'label': '徽州·金华', 'desc': '早岁乡居、研习新安画派'},
    {'start': 1907, 'end': 1937, 'label': '上海', 'desc': '编辑、鬻画、海上鼎盛三十年'},
    {'start': 1937, 'end': 1948, 'label': '北平', 'desc': '困居治学十一年'},
    {'start': 1948, 'end': 1955, 'label': '杭州', 'desc': '西湖栖霞岭晚境'},
]

# ── 输出 ──
out_path = os.path.join(BASE, 'hbh_river_data.js')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('window.HBH_RIVER = ')
    json.dump({
        'years': years_list,
        'themeRiver': theme_river,
        'streams': streams,
        'cards': cards,
        'anchors': anchors,
        'eras': eras,
        'layers': [{'name': l, 'color': LAYER_COLORS[l]} for l in LAYER_ORDER],
        'yearRange': [1865, 1955],
    }, f, ensure_ascii=False, separators=(',', ':'))
    f.write(';\n')

print(f'Done: {out_path}')
print(f'   Years: {len(years_list)} (1865-1955)')
print(f'   ThemeRiver layers: {len(LAYER_ORDER)}')
print(f'   Streams: {len(streams)} persons')
print(f'   Cards: {len(cards)}')
print(f'   Size: {os.path.getsize(out_path)/1024:.1f} KB')
