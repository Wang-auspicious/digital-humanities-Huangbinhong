# -*- coding: utf-8 -*-
"""聚合 hbh_*.json → life_journey.json（第一屏生命迁徙地图数据）。
   严格照 §3 schema 产出：residences / byYear / cities。
   中文直写 UTF-8，ensure_ascii=False。"""

import json, collections, sys

def L(f):
    with open(f, encoding='utf-8') as fh:
        return json.load(fh)

persons   = L('hbh_persons.json')
inter     = L('hbh_interactions.json')
locs      = L('hbh_locations.json')
resid     = L('hbh_residences.json')
creations = L('hbh_creations.json')
era       = L('era_timeline.json')
obs       = L('hbh_observations.json')

BIRTH, DEATH = 1865, 1955
YEARS = list(range(BIRTH, DEATH + 1))

# ---- helpers ----
def extract_year(date_str):
    """Parse '1865', '1894-07-25', etc. → int year."""
    try:
        return int(str(date_str)[:4])
    except:
        return None

# ---- residences (from hbh_residences.json) ----
PHASE_COLORS = ['#6E7B5B', '#9C6B4A', '#3F4A5A', '#7A5A6E']  # 歙县 上海 北平 杭州
residences_out = []
for i, r in enumerate(resid):
    residences_out.append({
        'name': r['standard_name'],
        'lat': r['lat'],
        'lng': r['lng'],
        'start': r['start_year'],
        'end': r['end_year'],
        'color': PHASE_COLORS[i % len(PHASE_COLORS)],
        'notes': r.get('notes', ''),
    })

def get_residence(year):
    """Return the residence record that covers this year, or None.
    When a year is both the end of one residence and start of another,
    prefer the NEW one (the transition year belongs to the destination)."""
    candidates = [r for r in residences_out if r['start'] <= year <= r['end']]
    if not candidates:
        return None
    # Prefer the one that STARTS in this year (transition → new home)
    starters = [r for r in candidates if r['start'] == year]
    if starters:
        return starters[0]
    return candidates[0]

# ---- cities: all unique standard_name → (lat, lng) (most common coords) ----
city_coords = collections.defaultdict(list)
for r in locs:
    key = r['standard_name']
    city_coords[key].append((r['lat'], r['lng']))

cities_out = {}
for name, coords in city_coords.items():
    # most common (lat,lng) pair
    cnt = collections.Counter(coords)
    (lat, lng), _ = cnt.most_common(1)[0]
    cities_out[name] = [lat, lng]

# Ensure residence cities are present with correct coords
for r in resid:
    nm = r['standard_name']
    if nm not in cities_out:
        cities_out[nm] = [r['lat'], r['lng']]

# ---- person total_mentions lookup ----
person_total = {p['standard_name']: p['total_mentions'] for p in persons}
person_first = {p['standard_name']: p['first_mention'] for p in persons}
person_cat   = {p['standard_name']: p['category'] for p in persons}

# ---- interactions by year ----
inter_by_year = collections.defaultdict(list)
for it in inter:
    inter_by_year[it['year']].append(it)

# ---- locations by year ----
locs_by_year = collections.defaultdict(list)
for r in locs:
    locs_by_year[r['year']].append(r)

# ---- creations by year ----
crea_by_year = collections.defaultdict(list)
for c in creations:
    crea_by_year[c['year']].append(c)

# ---- era events by year ----
era_by_year = collections.defaultdict(list)
for e in era:
    y = extract_year(e.get('date', ''))
    if y is not None and e.get('importance', 0) >= 1:
        era_by_year[y].append({
            'event': e['event'],
            'category': e.get('category', ''),
            'importance': e['importance'],
        })

# ---- radius drops by year ----
radius_by_year = {}
for r in obs.get('radius_changes', []):
    y = r.get('year')
    drop = r.get('drop_pct', 0)
    if y is not None and drop >= 60:
        radius_by_year[y] = {
            'drop_pct': drop,
            'note': r.get('note', ''),
            'type': r.get('type', ''),
        }

# ---- determine year_loc (most common location for each year) ----
year_loc = {}
for y, rs in locs_by_year.items():
    cnt = collections.Counter((r['standard_name'], r['lat'], r['lng']) for r in rs)
    (name, lat, lng), _ = cnt.most_common(1)[0]
    year_loc[y] = {'place': name, 'lat': lat, 'lng': lng}

# ---- build byYear ----
by_year_out = {}
prev_anchor = None

for y in YEARS:
    entry = {
        'anchor': None,
        'moves': [],
        'people_new': [],
        'interactions': [],
        'travels': [],
        'creations': [],
        'era': [],
        'radius_drop': 0,
    }

    # --- anchor ---
    residence = get_residence(y)
    yl = year_loc.get(y, {})

    # Birth year override: born in 金华, not 歙县
    if y == BIRTH:
        anchor = {'place': '金华', 'lat': 29.1028, 'lng': 119.6496}
    elif residence:
        anchor = {
            'place': residence['name'],
            'lat': residence['lat'],
            'lng': residence['lng'],
        }
    elif yl:
        anchor = {
            'place': yl.get('place', ''),
            'lat': yl.get('lat'),
            'lng': yl.get('lng'),
        }
    elif prev_anchor:
        anchor = dict(prev_anchor)  # carry forward
    else:
        anchor = {'place': '金华', 'lat': 29.1028, 'lng': 119.6496}

    entry['anchor'] = anchor
    prev_anchor = anchor

    # --- moves: travels away from residence city ---
    anchor_name = anchor['place']
    travel_places = set()

    # 1865: birthplace (金华) → hometown (歙县) transition
    if y == BIRTH:
        entry['moves'].append({
            'from': '金华',
            'to': '歙县',
            'fromLL': [119.6496, 29.1028],
            'toLL': [118.4152, 29.8634],
            'type': '迁徙',
        })
    if y in locs_by_year:
        for r in locs_by_year[y]:
            if r['type'] == '游历' and r['standard_name'] != anchor_name:
                travel_places.add(r['standard_name'])
                # Check if we have coords
                tc = cities_out.get(r['standard_name'], [r['lat'], r['lng']])

    # Detect residence CHANGE (e.g. 1907 歙县→上海)
    if y > BIRTH:
        prev_res = get_residence(y - 1)
        curr_res = get_residence(y)
        if prev_res and curr_res and prev_res['name'] != curr_res['name']:
            entry['moves'].append({
                'from': prev_res['name'],
                'to': curr_res['name'],
                'fromLL': [prev_res['lng'], prev_res['lat']],
                'toLL': [curr_res['lng'], curr_res['lat']],
                'type': '迁徙',
            })

    # Travel moves: from anchor to distinct travel locations
    for tp in travel_places:
        tc = cities_out.get(tp, [None, None])
        # Avoid duplicating if it's the same as a residence change
        already = any(m['to'] == tp for m in entry['moves'])
        if not already:
            entry['moves'].append({
                'from': anchor_name,
                'to': tp,
                'fromLL': [anchor['lng'], anchor['lat']],
                'toLL': [tc[1], tc[0]] if tc[0] is not None else [anchor['lng'], anchor['lat']],
                'type': '游历',
            })

    # --- people_new (first_mention == this year) ---
    for p in persons:
        if p['first_mention'] == y:
            entry['people_new'].append({
                'name': p['standard_name'],
                'cat': p['category'],
            })
    # sort by total_mentions desc
    entry['people_new'].sort(key=lambda x: person_total.get(x['name'], 0), reverse=True)

    # --- interactions (this year, top 8 by person's total_mentions) ---
    yr_inters = inter_by_year.get(y, [])
    yr_inters_sorted = sorted(yr_inters, key=lambda it: person_total.get(it['person'], 0), reverse=True)
    for it in yr_inters_sorted[:8]:
        raw = it.get('raw_text', '')
        entry['interactions'].append({
            'name': it['person'],
            'type': it['interaction_type'],
            'text': raw[:120] if raw else '',
        })

    # --- travels (location records of type 游历) ---
    if y in locs_by_year:
        for r in locs_by_year[y]:
            if r['type'] == '游历':
                entry['travels'].append({
                    'place': r['standard_name'],
                    'lat': r['lat'],
                    'lng': r['lng'],
                    'text': r.get('raw_text', '')[:120],
                })

    # --- creations ---
    for c in crea_by_year.get(y, []):
        entry['creations'].append({
            'title': c.get('title', ''),
            'type': c.get('creation_type', ''),
            'subject': c.get('subject', ''),
            'event_id': c.get('event_id', ''),
            'text': c.get('raw_text', '')[:160],
        })

    # --- era events ---
    entry['era'] = era_by_year.get(y, [])

    # --- radius drop ---
    if y in radius_by_year:
        entry['radius_drop'] = radius_by_year[y]['drop_pct']

    by_year_out[str(y)] = entry

# ---- assemble final output ----
output = {
    'residences': residences_out,
    'byYear': by_year_out,
    'cities': cities_out,
}

# ---- validation ----
errors = []
for y_str, entry in by_year_out.items():
    if not entry['anchor'] or not entry['anchor'].get('place'):
        errors.append(f"Year {y_str}: anchor missing")
    for c in entry['creations']:
        if not c.get('event_id'):
            errors.append(f"Year {y_str}: creation missing event_id: {c.get('title','?')}")

all_places = set()
for y_str, entry in by_year_out.items():
    all_places.add(entry['anchor']['place'])
    for m in entry['moves']:
        all_places.add(m['from'])
        all_places.add(m['to'])
    for t in entry['travels']:
        all_places.add(t['place'])

missing_from_cities = [p for p in all_places if p not in cities_out]
if missing_from_cities:
    errors.append(f"Places missing from cities: {missing_from_cities}")

if errors:
    print("VALIDATION ERRORS:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

# ---- write ----
with open('life_journey.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

# ---- stats ----
import os
sz = os.path.getsize('life_journey.json')
n_years = len(by_year_out)
n_cities = len(cities_out)
total_moves = sum(len(e['moves']) for e in by_year_out.values())
total_new = sum(len(e['people_new']) for e in by_year_out.values())
total_crea = sum(len(e['creations']) for e in by_year_out.values())
total_travel = sum(len(e['travels']) for e in by_year_out.values())
n_drops = sum(1 for e in by_year_out.values() if e['radius_drop'] > 0)

print(f'life_journey.json: {sz:,} bytes')
print(f'Years: {n_years}  Cities: {n_cities}')
print(f'Moves: {total_moves}  New people: {total_new}  Travels: {total_travel}')
print(f'Creations: {total_crea}  Radius drops (≥60%): {n_drops}')
print('Done.')
