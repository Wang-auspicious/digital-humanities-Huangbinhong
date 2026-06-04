import json
import math
import os
import random
import re
from pathlib import Path

import openpyxl


ROOT = Path(".")
XLSX = ROOT / "待查.xlsx"
IMAGE_ROOT = ROOT / "作品图"
OUT = ROOT / "digital_hbh_shanshui_atlas.html"


def rel(p: Path) -> str:
    return p.as_posix()


def trim_text(s, n=96):
    s = re.sub(r"\s+", "", str(s or ""))
    return s[:n] + ("…" if len(s) > n else "")


def build_file_map():
    files = {}
    for dp, _, fs in os.walk(IMAGE_ROOT):
        for f in fs:
            files[f] = rel(Path(dp) / f)
    return files


def place_key(title: str) -> str:
    title = str(title or "")
    pairs = [
        ("黄山", ["黄山", "文殊台"]),
        ("泰山", ["泰岱", "泰岳"]),
        ("惠山", ["惠山", "惠麓"]),
        ("西泠", ["西泠"]),
        ("新安", ["新安"]),
        ("广雅书院", ["广雅书院"]),
        ("宝铁研斋", ["宝铁研斋"]),
        ("冲雪访碑", ["冲雪访碑"]),
        ("分湖", ["分湖"]),
        ("近游", ["近游"]),
        ("校碑", ["校碑", "仿碑"]),
        ("杨华", ["杨华"]),
        ("木孙楼", ["木孙楼"]),
        ("庆寿", ["庆寿"]),
        ("冷香阁", ["冷香阁"]),
        ("嘉陵江", ["嘉陵"]),
        ("红树室", ["红树室"]),
        ("篝镫纺读", ["篝镫纺读"]),
        ("勘书", ["勘书"]),
        ("练滨草堂", ["练滨"]),
        ("池州青玉峡", ["池州", "青玉峡"]),
        ("八桂", ["八桂"]),
        ("漓江", ["漓江"]),
        ("畏斋", ["畏斋"]),
        ("澹远楼", ["澹远楼"]),
        ("风轩水槛", ["风轩水槛"]),
        ("豫园", ["豫园"]),
        ("金华山", ["金华山", "金华洞"]),
        ("石雨草堂", ["石雨草堂"]),
        ("桂林", ["桂林"]),
        ("雁山", ["雁山"]),
        ("病榻慰亲", ["病榻慰亲"]),
        ("湖荷忆昨", ["湖荷忆昨"]),
        ("听帆楼", ["听帆"]),
        ("翦淞阁", ["翦淞阁"]),
        ("霜柑阁", ["霜柑阁"]),
        ("青城山", ["青城"]),
        ("蜀游", ["蜀游", "蜀中"]),
        ("江行", ["江行"]),
        ("老人峰", ["老人峰"]),
        ("九龙潭", ["九龙潭"]),
        ("归云楼", ["归云楼"]),
        ("陈柱尊山屋", ["陈柱尊", "尊山屋", "北流"]),
        ("九华山", ["九华"]),
        ("横槎江", ["横槎"]),
        ("寒月行窝", ["寒月行窝"]),
        ("城南草堂", ["城南草堂"]),
        ("柏园", ["柏园"]),
        ("碧峰禅师", ["碧峰禅师"]),
        ("宋故行宫", ["宋故行宫"]),
        ("东涯老屋", ["东涯老屋"]),
        ("焦山", ["焦山"]),
        ("双树居", ["双树居"]),
        ("松籁阁", ["松籁阁"]),
        ("山居清话", ["山居清话"]),
        ("碧山草堂", ["碧山草堂"]),
        ("燕郊", ["燕郊"]),
        ("晚晴山房", ["晚晴山房"]),
        ("闲闲山庄", ["闲闲山庄"]),
        ("怀旧楼", ["怀旧楼"]),
        ("江淮", ["江淮"]),
        ("读书楼", ["读书楼"]),
        ("海印盦", ["海印盦"]),
        ("挹翠阁", ["挹翠阁"]),
        ("武夷九曲", ["武彝", "武夷"]),
        ("尘甸晴初", ["尘甸"]),
        ("竹北栘", ["竹北栘"]),
        ("虞山", ["虞山"]),
        ("玄亭", ["玄亭"]),
        ("补学轩", ["补学轩"]),
        ("剑池", ["剑池"]),
        ("临安", ["临安"]),
        ("南岳", ["南岳"]),
    ]
    for key, needles in pairs:
        if any(n in title for n in needles):
            return key
    key = re.sub(r"(山水|图卷|图册|册|卷|图|大意|风景|纪游|诗意|山色|雅集|读画销夏)$", "", title)
    return key[:6] or title


def comment_for(row, key):
    title = row["作品名"]
    year = row["年份"]
    sub = row.get("子类") or ""
    if key == "黄山":
        return "石骨层层，早年游踪到晚年追忆都归在这里。"
    if key in {"桂林", "漓江", "八桂"}:
        return "南方水势开阔，峰影轻，笔墨也随之放缓。"
    if key in {"嘉陵江", "蜀游", "青城山"}:
        return "入蜀前后的山水，险峻里带行旅的湿气。"
    if key in {"泰山", "九华山", "南岳", "武夷九曲", "雁山"}:
        return "名山不只取形势，重在把古意压进皴线。"
    if key in {"西泠", "豫园", "焦山", "剑池", "虞山"}:
        return "名胜连着题跋与交游，景物后面有人在场。"
    if "斋" in key or "楼" in key or "阁" in key or "草堂" in key or "轩" in key or "园" in key or "居" in key:
        return "斋馆图多为友人而作，山水收束成可居可读的一角。"
    if sub == "胜水":
        return "水路带出行迹，留白处像江面，也像回望。"
    if sub == "名山":
        return "山名在画题里很实，落到笔下却更近胸中丘壑。"
    return "实景入画，并不照录风景，而是借地名存一段往还。"


REGION_BASE = {
    "黄山": (31, 24),
    "泰山": (55, 12),
    "惠山": (16, 25),
    "西泠": (18, 43),
    "新安": (22, 35),
    "分湖": (16, 61),
    "嘉陵江": (63, 34),
    "青城山": (71, 30),
    "蜀游": (72, 43),
    "桂林": (80, 73),
    "漓江": (73, 67),
    "八桂": (88, 78),
    "九华山": (50, 61),
    "南岳": (87, 82),
    "武夷九曲": (63, 77),
    "雁山": (79, 23),
    "金华山": (14, 15),
    "池州青玉峡": (46, 53),
    "焦山": (83, 43),
    "剑池": (88, 53),
    "虞山": (84, 61),
    "临安": (54, 72),
}

DEFAULT_POOLS = {
    "名山": [(24, 18), (38, 16), (56, 22), (74, 19), (86, 33), (32, 75), (61, 80), (88, 79)],
    "胜水": [(15, 58), (38, 51), (59, 46), (69, 57), (82, 69), (52, 75), (30, 68)],
    "名胜斋馆": [
        (11, 39), (22, 47), (31, 58), (44, 37), (52, 31), (64, 52), (75, 39), (87, 48),
        (16, 71), (33, 80), (45, 68), (58, 63), (72, 78), (88, 65), (23, 28), (68, 24),
    ],
}


def anchor_for(key, sub, idx):
    if key in REGION_BASE:
        x, y = REGION_BASE[key]
    else:
        pool = DEFAULT_POOLS.get(sub) or DEFAULT_POOLS["名胜斋馆"]
        x, y = pool[idx % len(pool)]
    # deterministic looseness, not a grid
    rnd = random.Random(hash(key) & 0xFFFFFFFF)
    x += rnd.uniform(-3.8, 3.8)
    y += rnd.uniform(-3.0, 3.0)
    return max(4, min(96, x)), max(5, min(94, y))


def label_for(anchor, idx):
    ax, ay = anchor
    # Place text on nearby quieter paper; stagger direction by index.
    rnd = random.Random(idx * 9173 + 41)
    dx = rnd.choice([-10, -8, 7, 9, 12])
    dy = rnd.choice([-8, -5, 6, 9])
    if ay < 18:
        dy = abs(dy) + 3
    if ay > 82:
        dy = -abs(dy) - 2
    if ax < 14:
        dx = abs(dx) + 3
    if ax > 88:
        dx = -abs(dx) - 3
    return max(2.0, min(96.0, ax + dx)), max(4.0, min(92.0, ay + dy))


def main():
    file_map = build_file_map()
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb.active
    headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]

    all_with_images = []
    real_rows = []
    for r in range(2, ws.max_row + 1):
        row = dict(zip(headers, [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]))
        if row.get("查到图") != "是":
            continue
        imgs = []
        for name in str(row.get("匹配图片") or "").split(";"):
            name = name.strip()
            if name and name in file_map:
                imgs.append({"name": name, "src": file_map[name]})
        if not imgs:
            continue
        item = {
            "title": str(row["作品名"]),
            "year": int(row["年份"]) if row.get("年份") else None,
            "category": row.get("大类") or "",
            "sub": row.get("子类") or "",
            "event": row.get("event_id") or "",
            "raw": trim_text(row.get("原文片段"), 130),
            "images": imgs,
        }
        all_with_images.append(item)
        if row.get("大类") == "实景山水":
            row["images"] = imgs
            real_rows.append(row)

    groups = {}
    for row in real_rows:
        key = place_key(row["作品名"])
        groups.setdefault(key, {"key": key, "sub": row.get("子类") or "", "works": []})
        groups[key]["works"].append(
            {
                "title": str(row["作品名"]),
                "year": int(row["年份"]) if row.get("年份") else None,
                "sub": row.get("子类") or "",
                "raw": trim_text(row.get("原文片段"), 140),
                "note": comment_for(row, key),
                "images": row["images"],
            }
        )

    labels = []
    for idx, (key, group) in enumerate(sorted(groups.items(), key=lambda kv: (min(w["year"] for w in kv[1]["works"] if w["year"]), kv[0]))):
        sub = group["sub"]
        anchor = anchor_for(key, sub, idx)
        lab = label_for(anchor, idx)
        works = sorted(group["works"], key=lambda w: (w["year"] or 9999, w["title"]))
        years = [w["year"] for w in works if w["year"]]
        labels.append(
            {
                "key": key,
                "sub": sub,
                "count": len(works),
                "yearText": str(years[0]) if len(set(years)) == 1 else f"{years[0]}–{years[-1]}",
                "anchor": [round(anchor[0], 2), round(anchor[1], 2)],
                "label": [round(lab[0], 2), round(lab[1], 2)],
                "note": comment_for({"作品名": works[0]["title"], "年份": years[0] if years else "", "子类": sub}, key),
                "works": works,
            }
        )

    gallery = []
    for item in all_with_images:
        gallery.append(
            {
                "title": item["title"],
                "year": item["year"],
                "category": item["category"],
                "sub": item["sub"],
                "src": item["images"][0]["src"],
            }
        )

    data = {
        "labels": labels,
        "gallery": gallery,
        "stats": {
            "realWorks": len(real_rows),
            "realLabels": len(labels),
            "allWorks": len(all_with_images),
        },
    }

    html = render_html(data)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} | labels={len(labels)} realWorks={len(real_rows)} gallery={len(gallery)}")


def render_html(data):
    data_json = json.dumps(data, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>数字黄宾虹｜实景山水</title>
<style>
  :root {{
    --paper:#e6cfaa;
    --paper2:#ead8b9;
    --ink:#251f18;
    --muted:rgba(37,31,24,.48);
    --line:rgba(60,45,32,.32);
    --red:#b86d4f;
    --cyan:#1b9ca1;
    --map-ratio:1.333333;
    --rail-min:338px;
    --map-w:min(calc(100vh * var(--map-ratio)), calc(100vw - var(--rail-min)));
  }}
  * {{ box-sizing:border-box; }}
  html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:var(--paper); }}
  body {{
    color:var(--ink);
    font-family: "Noto Serif SC","Songti SC","SimSun",Georgia,serif;
    background:
      radial-gradient(circle at 18% 12%, rgba(255,250,232,.36), transparent 28%),
      linear-gradient(90deg, var(--paper2) 0, var(--paper) 78%, #e2c69b 100%);
  }}
  .page {{ position:relative; width:100vw; height:100vh; display:flex; align-items:stretch; }}
  .mapPane {{ position:relative; flex:0 0 var(--map-w); width:var(--map-w); height:100vh; overflow:hidden; }}
  .mapBox {{ position:absolute; left:0; top:0; width:100%; height:100%; }}
  .baseMap {{ position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; object-position:left top; user-select:none; pointer-events:none; }}
  .veil {{ position:absolute; inset:0; pointer-events:none; background:linear-gradient(90deg, transparent 91%, rgba(230,207,170,.20)); mix-blend-mode:multiply; }}
  .hairlines {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; overflow:visible; }}
  .hairlines path {{ fill:none; stroke:var(--line); stroke-width:.085; vector-effect:non-scaling-stroke; shape-rendering:crispEdges; }}
  .hairlines .dot {{ fill:rgba(159,86,57,.45); stroke:rgba(255,248,226,.75); stroke-width:.16; vector-effect:non-scaling-stroke; }}
  .labels {{ position:absolute; inset:0; }}
  .label {{
    position:absolute;
    transform:translate(-50%,-50%);
    display:flex;
    align-items:flex-start;
    gap:3px;
    cursor:default;
    color:rgba(38,31,24,.74);
    filter: drop-shadow(0 1px 0 rgba(238,222,188,.55));
    transition:opacity .16s ease, color .16s ease, transform .16s ease;
  }}
  .label:hover {{ z-index:20; color:rgba(28,22,17,.96); transform:translate(-50%,-50%) scale(1.045); }}
  .label .seal {{
    width:8px; height:8px;
    border:1px solid rgba(176,91,62,.45);
    color:rgba(176,91,62,.70);
    font:6px/6px "Times New Roman",serif;
    display:grid; place-items:center;
    margin-top:1px;
  }}
  .label .name {{
    writing-mode:vertical-rl;
    letter-spacing:.12em;
    font-size:9px;
    line-height:1.05;
    white-space:nowrap;
    border:1px solid rgba(120,82,54,.28);
    border-radius:9px;
    padding:3px 2px;
    background:rgba(236,220,188,.28);
  }}
  .label .meta {{
    writing-mode:vertical-rl;
    letter-spacing:.10em;
    font-size:7.4px;
    line-height:1.18;
    max-height:98px;
    white-space:normal;
    opacity:.78;
  }}
  .label .count {{ color:rgba(165,78,52,.78); font-size:7px; }}
  .titleBlock {{
    position:absolute; left:26px; top:22px; z-index:5;
    display:grid; grid-template-columns:auto 1fr; gap:10px;
    pointer-events:none;
  }}
  .titleSeal {{
    width:42px; height:54px;
    border:2px solid rgba(176,91,62,.42);
    color:rgba(176,91,62,.66);
    display:grid; place-items:center;
    writing-mode:vertical-rl;
    letter-spacing:.16em;
    font-size:18px;
    line-height:1;
  }}
  .intro {{ padding-top:3px; max-width:210px; }}
  .intro h1 {{ margin:0 0 7px; font-size:13px; font-weight:500; letter-spacing:.16em; }}
  .intro p {{ margin:0; font-size:8px; line-height:1.75; color:rgba(38,31,24,.54); letter-spacing:.08em; }}
  .bottomIndex {{
    position:absolute; left:28px; right:26px; bottom:18px; height:38px;
    display:flex; gap:4px; align-items:end; opacity:.48; pointer-events:none;
  }}
  .tick {{ flex:1; border-left:1px solid rgba(158,96,65,.24); height:12px; position:relative; }}
  .tick span {{ position:absolute; bottom:-13px; left:-5px; font-size:6.5px; color:rgba(117,76,52,.55); }}
  .rail {{
    flex:1 1 auto;
    height:100vh;
    min-width:var(--rail-min);
    padding:22px 22px 22px 18px;
    overflow:hidden;
    background:
      linear-gradient(90deg, rgba(230,207,170,.80), rgba(230,207,170,.96) 28%, rgba(226,198,155,.95)),
      radial-gradient(circle at 70% 25%, rgba(255,248,222,.34), transparent 32%);
    border-left:1px solid rgba(122,82,48,.10);
  }}
  .railHead {{
    height:42px;
    display:flex; align-items:flex-start; justify-content:space-between; gap:12px;
    margin-bottom:10px;
    color:rgba(43,35,27,.62);
  }}
  .railHead .smallTitle {{ font-size:10px; letter-spacing:.18em; }}
  .railHead .stat {{ font-size:7px; line-height:1.55; text-align:right; letter-spacing:.07em; }}
  .thumbGrid {{
    width:100%; height:calc(100vh - 74px);
    display:grid;
    grid-template-columns:repeat(12, 1fr);
    grid-auto-rows:14px;
    gap:5px;
    grid-auto-flow:dense;
    align-content:start;
    overflow:hidden;
  }}
  .thumb {{
    position:relative;
    background:#d8bd8e;
    border:1px solid rgba(95,63,39,.18);
    overflow:hidden;
    opacity:.88;
    transition:opacity .14s ease, transform .14s ease, box-shadow .14s ease;
  }}
  .thumb img {{ width:100%; height:100%; object-fit:cover; display:block; filter:saturate(.82) contrast(.96); }}
  .thumb:hover {{ opacity:1; transform:scale(1.04); z-index:8; box-shadow:0 8px 22px rgba(63,42,25,.20); }}
  .thumb.rect {{ grid-column:span 4; grid-row:span 2; }}
  .thumb.long {{ grid-column:span 6; grid-row:span 2; }}
  .thumb.tall {{ grid-column:span 3; grid-row:span 3; }}
  .thumb.sq {{ grid-column:span 3; grid-row:span 3; }}
  .thumb.round {{ grid-column:span 3; grid-row:span 3; border-radius:50%; }}
  .thumb.round img {{ border-radius:50%; }}
  .popover {{
    position:absolute;
    z-index:50;
    width:min(360px, 31vw);
    max-height:min(610px, 78vh);
    padding:12px 12px 13px;
    background:rgba(237,220,187,.95);
    border:1px solid rgba(91,59,36,.22);
    box-shadow:0 18px 55px rgba(59,37,20,.25);
    backdrop-filter:blur(2px);
    opacity:0;
    transform:translateY(4px);
    pointer-events:none;
    transition:opacity .12s ease, transform .12s ease;
  }}
  .popover.show {{ opacity:1; transform:translateY(0); }}
  .popTop {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; border-bottom:1px solid rgba(112,72,44,.18); padding-bottom:8px; margin-bottom:9px; }}
  .popTitle {{ font-size:15px; letter-spacing:.09em; font-weight:500; }}
  .popSub {{ margin-top:4px; font-size:8px; letter-spacing:.09em; color:rgba(43,35,27,.55); }}
  .popNote {{ font-size:10px; line-height:1.85; color:rgba(38,31,24,.76); margin:0 0 10px; }}
  .workList {{ display:flex; flex-direction:column; gap:9px; overflow:auto; max-height:430px; padding-right:4px; overscroll-behavior:contain; }}
  .work {{ display:grid; grid-template-columns:78px 1fr; gap:9px; align-items:start; }}
  .workImgs {{ width:78px; display:grid; grid-template-columns:repeat(2, 1fr); gap:3px; }}
  .workImgs img {{ width:100%; aspect-ratio:1/1; object-fit:cover; background:#d5bd91; border:1px solid rgba(93,61,36,.15); }}
  .workInfo b {{ display:block; font-size:10px; font-weight:500; letter-spacing:.05em; margin-bottom:3px; }}
  .workInfo .raw {{ font-size:8px; line-height:1.55; color:rgba(38,31,24,.56); }}
  .hoverHint {{
    position:absolute; right:18px; bottom:13px; font-size:7px; letter-spacing:.1em;
    color:rgba(43,35,27,.44);
  }}
  @media (max-width:1100px) {{
    :root {{ --rail-min:300px; }}
    .label .meta {{ display:none; }}
    .popover {{ width:360px; max-width:calc(100vw - 28px); }}
    .thumbGrid {{ grid-template-columns:repeat(8, 1fr); }}
  }}
</style>
</head>
<body>
<div class="page">
  <section class="mapPane" id="mapPane">
    <div class="mapBox" id="mapBox">
      <img class="baseMap" src="山水底图.png" alt="山水底图" />
      <svg class="hairlines" viewBox="0 0 100 100" preserveAspectRatio="none" id="hairlines"></svg>
      <div class="labels" id="labels"></div>
      <div class="veil"></div>
      <div class="titleBlock">
        <div class="titleSeal">宾虹</div>
        <div class="intro">
          <h1>实景山水索引</h1>
          <p>据《黄宾虹年谱》与待查图表整理。名山、胜水、斋馆各归其位；移入小签，可看同一地名下留存图像。</p>
        </div>
      </div>
      <div class="bottomIndex" id="bottomIndex"></div>
    </div>
  </section>
  <aside class="rail">
    <div class="railHead">
      <div class="smallTitle">图像旁列</div>
      <div class="stat" id="stat"></div>
    </div>
    <div class="thumbGrid" id="thumbGrid"></div>
  </aside>
  <div class="popover" id="popover"></div>
  <div class="hoverHint">移入左侧小签展开作品；右侧为已查图像缩列</div>
</div>
<script>
const DATA = {data_json};

function enc(src) {{ return encodeURI(src).replace(/#/g, '%23'); }}

const labelsEl = document.getElementById('labels');
const linesEl = document.getElementById('hairlines');
const pop = document.getElementById('popover');
const mapPane = document.getElementById('mapPane');

function makePath(ax, ay, lx, ly) {{
  const midX = lx;
  return `M ${{ax}} ${{ay}} H ${{midX}} V ${{ly}}`;
}}

DATA.labels.forEach((d, i) => {{
  const [ax, ay] = d.anchor, [lx, ly] = d.label;
  const p = document.createElementNS('http://www.w3.org/2000/svg','path');
  p.setAttribute('d', makePath(ax, ay, lx, ly));
  linesEl.appendChild(p);
  const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
  c.setAttribute('class','dot');
  c.setAttribute('cx', ax); c.setAttribute('cy', ay); c.setAttribute('r', .42);
  linesEl.appendChild(c);

  const el = document.createElement('div');
  el.className = 'label';
  el.style.left = lx + '%';
  el.style.top = ly + '%';
  const count = d.count > 1 ? `<span class="count">/${{d.count}}</span>` : '';
  el.innerHTML = `<span class="seal">${{String(i+1).padStart(2,'0')}}</span><span class="name">${{d.key}}${{count}}</span><span class="meta">${{d.yearText}}｜${{d.note}}</span>`;
  el.addEventListener('mouseenter', () => showPop(d, el));
  el.addEventListener('mousemove', () => showPop(d, el));
  el.addEventListener('mouseleave', hidePopSoon);
  labelsEl.appendChild(el);
}});

let hideTimer = 0;
pop.addEventListener('mouseenter', () => clearTimeout(hideTimer));
pop.addEventListener('mouseleave', hidePopSoon);

function hidePopSoon() {{
  clearTimeout(hideTimer);
  hideTimer = setTimeout(() => pop.classList.remove('show'), 170);
}}

function showPop(d, el) {{
  clearTimeout(hideTimer);
  const works = d.works.slice().sort((a,b)=>(a.year||0)-(b.year||0));
  const coverCount = works.reduce((n,w)=>n + w.images.length, 0);
  pop.innerHTML = `
    <div class="popTop">
      <div>
        <div class="popTitle">${{d.key}}</div>
        <div class="popSub">${{d.yearText}}｜${{d.sub || '实景山水'}}｜${{works.length}}件作品 / ${{coverCount}}帧图像</div>
      </div>
    </div>
    <p class="popNote">${{d.note}}</p>
    <div class="workList">
      ${{works.map(w => `
        <div class="work">
          <div class="workImgs">
            ${{w.images.slice(0,4).map(img => `<img src="${{enc(img.src)}}" title="${{img.name}}">`).join('')}}
          </div>
          <div class="workInfo">
            <b>${{w.year || ''}}｜${{w.title}}</b>
            <div class="raw">${{w.raw || w.note}}</div>
          </div>
        </div>
      `).join('')}}
    </div>`;
  const er = el.getBoundingClientRect();
  const pr = pop.getBoundingClientRect();
  let left = er.right + 14;
  let top = er.top - 10;
  if (left + 370 > window.innerWidth) left = er.left - 374;
  if (left < 12) left = Math.min(window.innerWidth - 374, er.right + 14);
  if (top + Math.min(610, window.innerHeight * .78) > window.innerHeight - 14) top = window.innerHeight - Math.min(610, window.innerHeight * .78) - 14;
  if (top < 12) top = 12;
  pop.style.left = left + 'px';
  pop.style.top = top + 'px';
  pop.classList.add('show');
}}

const grid = document.getElementById('thumbGrid');
const shapes = ['rect','sq','round','long','rect','sq','tall','rect','round','sq'];
DATA.gallery.forEach((g, i) => {{
  const a = document.createElement('div');
  a.className = 'thumb ' + shapes[i % shapes.length];
  a.title = `${{g.year || ''}} ${{g.title}}｜${{g.category}}`;
  a.innerHTML = `<img loading="lazy" src="${{enc(g.src)}}" alt="${{g.title}}">`;
  grid.appendChild(a);
}});

document.getElementById('stat').innerHTML =
  `实景山水 ${{DATA.stats.realWorks}} 件<br>左侧地名小签 ${{DATA.stats.realLabels}} 处<br>已查图像作品 ${{DATA.stats.allWorks}} 件`;

const bi = document.getElementById('bottomIndex');
for (let y = 1899; y <= 1953; y += 3) {{
  const t = document.createElement('div');
  t.className = 'tick';
  if ((y - 1899) % 9 === 0) t.innerHTML = `<span>${{y}}</span>`;
  bi.appendChild(t);
}}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
