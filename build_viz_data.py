# -*- coding: utf-8 -*-
"""聚合所有 hbh_*.json -> 单个 hbh_data.js (window.HBH=...) 供前端内嵌读取。"""
import json, collections

def L(f): return json.load(open(f, encoding='utf-8'))

persons   = L('hbh_persons.json')
inter     = L('hbh_interactions.json')
locs      = L('hbh_locations.json')
resid     = L('hbh_residences.json')
topics    = L('hbh_topics.json')
creations = L('hbh_creations.json')
density   = L('hbh_density.json')
era       = L('era_timeline.json')
obs       = L('hbh_observations.json')
src       = L('hbh_source_layer.json')
kg        = L('hbh_knowledge_graph.json')

BIRTH, DEATH = 1865, 1955
YEARS = list(range(BIRTH, DEATH + 1))

# ---- source type map ----
src_by_evt = {s['event_id']: s['source_type'] for s in src}
SRC_CODE = {'HBH自撰': 'self', '他人记述': 'other', '编者按语': 'editor', '引用文献': 'cite'}

# ---- representative yearly location (most frequent place) ----
loc_by_year = collections.defaultdict(list)
for r in locs:
    loc_by_year[r['year']].append(r)
year_loc = {}
for y, rs in loc_by_year.items():
    cnt = collections.Counter((r['standard_name'], r['lat'], r['lng']) for r in rs)
    (name, lat, lng), _ = cnt.most_common(1)[0]
    year_loc[y] = {'place': name, 'lat': lat, 'lng': lng}

# ---- residence phases with life-tones ----
PHASE_COLORS = ['#6E7B5B', '#9C6B4A', '#3F4A5A', '#7A5A6E']  # 歙县 上海 北平 杭州
resid_out = []
for i, r in enumerate(resid):
    resid_out.append({
        'name': r['standard_name'], 'start': r['start_year'], 'end': r['end_year'],
        'lat': r['lat'], 'lng': r['lng'], 'notes': r.get('notes', ''),
        'color': PHASE_COLORS[i % len(PHASE_COLORS)]
    })
def phase_of(y):
    for i, r in enumerate(resid):
        if r['start_year'] <= y <= r['end_year']:
            return i
    return len(resid) - 1

# ---- yearly aggregate ----
yearly_density = {d['year']: d for d in density['yearly']}
crea_by_year = collections.Counter(c['year'] for c in creations)
inter_by_year = collections.Counter(i['year'] for i in inter)
years_out = []
for y in YEARS:
    d = yearly_density.get(y, {})
    yl = year_loc.get(y, {})
    years_out.append({
        'y': y,
        'events': d.get('event_count', 0),
        'chars': d.get('char_count', 0),
        'silent': bool(d.get('is_silent_period', False)),
        'crea': crea_by_year.get(y, 0),
        'inter': inter_by_year.get(y, 0),
        'lat': yl.get('lat'), 'lng': yl.get('lng'), 'place': yl.get('place', ''),
        'phase': phase_of(y),
    })

# ---- monthly matrix from density.monthly ----
months_out = []
for m in density['monthly']:
    ym = m.get('year_month') or m.get('ym') or ''
    yr = m.get('year'); mo = m.get('month')
    if yr is None and isinstance(ym, str) and '-' in ym:
        parts = ym.split('-'); yr = int(parts[0]); mo = int(parts[1])
    months_out.append({'y': yr, 'm': mo, 'c': m.get('event_count', 0)})

# ---- radius drops (significant) ----
radius = [{'year': r.get('year'), 'drop': r.get('drop_pct', 0), 'note': r.get('note', '')}
          for r in obs.get('radius_changes', []) if r.get('drop_pct', 0) >= 60]

# ---- topic stream by year (top topics) ----
TOPIC_KEEP = ['笔法墨法','金石考据','收藏鉴定','通信往来','展览社集','出版编辑',
              '教学育人','家事','游历','诗词唱和','革命政治','佛禅意境','疾病健康']
topic_year = {t: collections.Counter() for t in TOPIC_KEEP}
for e in topics:
    for t in e.get('topics', []):
        if t in topic_year:
            topic_year[t][e['year']] += 1
topic_stream = {t: [topic_year[t].get(y, 0) for y in YEARS] for t in TOPIC_KEEP}

# ---- events (trimmed) for live text ribbon ----
events_out = []
for e in topics:
    txt = e.get('raw_text', '').strip().replace('\n', '')
    events_out.append({
        'y': e['year'], 'd': e.get('date', ''),
        't': e.get('topics', [])[:3],
        's': SRC_CODE.get(src_by_evt.get(e['event_id'], ''), 'other'),
        'x': txt[:140],
    })

# ---- persons + interaction strands ----
TYPE_CODE = {'通信':'L','作画赠予':'G','合作':'C','题跋鉴赏':'A','见面会谈':'M',
             '师生':'T','同游':'Y','引荐':'I','来访':'V','收藏交易':'S','其他':'O'}
acts_by_person = collections.defaultdict(list)
for it in inter:
    acts_by_person[it['person']].append((it['year'], TYPE_CODE.get(it['interaction_type'], 'O')))
persons_out = []
for p in persons:
    nm = p['standard_name']
    acts = sorted(set(acts_by_person.get(nm, [])))
    persons_out.append({
        'name': nm, 'cat': p['category'],
        'first': p['first_mention'], 'last': p['last_mention'],
        'total': p['total_mentions'],
        'acts': [[a[0], a[1]] for a in acts],
    })
persons_out.sort(key=lambda x: (x['first'], -x['total']))

# ---- thread people: top recurring, with yearly interaction counts ----
must_include = ['傅雷','齐白石','张大千','黄节','谭嗣同','黄宾虹']  # narrative anchors (HBH excluded later)
inter_py = collections.defaultdict(lambda: collections.Counter())
for it in inter:
    inter_py[it['person']][it['year']] += 1
# rank: by total mentions, then ensure must_include present
ranked = sorted(persons, key=lambda p: -p['total_mentions'])
chosen, seen = [], set()
for nm in must_include:
    pp = next((p for p in persons if p['standard_name'] == nm), None)
    if pp and nm not in seen:
        chosen.append(pp); seen.add(nm)
for p in ranked:
    if len(chosen) >= 20: break
    if p['standard_name'] in seen: continue
    if p['category'] in ('研究源',): continue
    chosen.append(p); seen.add(p['standard_name'])
thread_people = []
for p in chosen:
    nm = p['standard_name']
    yc = inter_py.get(nm, {})
    thread_people.append({
        'name': nm, 'cat': p['category'],
        'first': p['first_mention'], 'last': p['last_mention'],
        'total': p['total_mentions'],
        'yc': {str(y): c for y, c in sorted(yc.items())},
    })
thread_people.sort(key=lambda x: x['first'])

# ---- 傅雷 dialogue raw texts ----
fulei = [{'y': it['year'], 'type': it['interaction_type'], 'x': it['raw_text'][:260]}
         for it in inter if it['person'] == '傅雷']
fulei.sort(key=lambda r: r['y'])

# ---- concepts (五笔七墨 + 核心画论) ----
cpt_nodes = {c['id']: c for c in kg['nodes']['concepts']}
cpt_edges = [e for e in kg['edges'] if e['type'] == 'MENTIONS_CONCEPT']
cpt_count = collections.Counter(e['target'] for e in cpt_edges)
cpt_years = collections.defaultdict(list)
for e in cpt_edges:
    if e.get('year'):
        cpt_years[e['target']].append(e['year'])
concepts_out = []
for cid, node in cpt_nodes.items():
    yrs = sorted(cpt_years.get(cid, []))
    concepts_out.append({
        'name': node['name'], 'group': node.get('group', ''),
        'subtype': node.get('subtype', ''),
        'count': cpt_count.get(cid, 0),
        'years': yrs,
    })
concepts_out.sort(key=lambda c: -c['count'])

# ---- creations 1951-1955 (dark/light climax) ----
crea_climax = []
for c in creations:
    if 1948 <= c['year'] <= 1955:
        crea_climax.append({'y': c['year'], 'type': c['creation_type'],
                            'title': c['title'], 'x': c.get('raw_text', '')[:160]})

# ---- category counts ----
cat_counts = collections.Counter(p['category'] for p in persons)

DATA = {
    'meta': {'name': '黄宾虹', 'birth': BIRTH, 'death': DEATH,
             'persons': len(persons), 'interactions': len(inter),
             'events': len(topics), 'creations': len(creations),
             'concepts': len(cpt_nodes)},
    'years': years_out,
    'months': months_out,
    'residences': resid_out,
    'era': era,
    'radius': radius,
    'topicStream': topic_stream,
    'topicOrder': TOPIC_KEEP,
    'events': events_out,
    'persons': persons_out,
    'threadPeople': thread_people,
    'catCounts': dict(cat_counts),
    'fulei': fulei,
    'concepts': concepts_out,
    'creaClimax': crea_climax,
    'typeNames': {v: k for k, v in TYPE_CODE.items()},
    'srcNames': {'self': '黄宾虹自撰', 'other': '他人记述', 'editor': '编者按语', 'cite': '引用文献'},
}

with open('hbh_data.js', 'w', encoding='utf-8') as f:
    f.write('window.HBH = ')
    json.dump(DATA, f, ensure_ascii=False, separators=(',', ':'))
    f.write(';')

import os
print('hbh_data.js bytes:', os.path.getsize('hbh_data.js'))
print('years', len(years_out), 'months', len(months_out), 'persons', len(persons_out),
      'events', len(events_out), 'concepts', len(concepts_out), 'fulei', len(fulei),
      'climax', len(crea_climax), 'radius', len(radius))
