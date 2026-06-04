"""
黄宾虹年谱数字化处理脚本 v2
数据源: paras_with_pages.txt (Word COM 精确页码)
输出:   huangbinhong_simplified.txt + hbh_events_raw.json
"""

import json
import re
from collections import Counter
from pathlib import Path

from opencc import OpenCC

SRC       = Path(r"D:\Desktop\VAST CHALLENGE\paras_with_pages.txt")
OUT_DIR   = Path(r"D:\Desktop\VAST CHALLENGE")
TXT_OUT   = OUT_DIR / "huangbinhong_simplified.txt"
JSON_OUT  = OUT_DIR / "hbh_events_raw.json"


# ─────────────────────────────────────────────────────
# Step 1: 读取 paras_with_pages.txt → [(page, text), ...]
# ─────────────────────────────────────────────────────

def load_paras(src: Path) -> list[tuple[int, str]]:
    results = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        tab = line.index("\t")
        try:
            page = int(line[:tab])
        except ValueError:
            continue
        text = line[tab + 1:].strip()
        if text:
            results.append((page, text))
    return results


# ─────────────────────────────────────────────────────
# Step 2: 繁→简 + 生成 simplified.txt
# ─────────────────────────────────────────────────────

def build_simplified_txt(paras: list[tuple[int, str]], cc: OpenCC):
    lines = []
    simp_paras = []
    prev_page = None

    for page, text in paras:
        if page != prev_page:
            lines.append(f"[P_{page}]")
            prev_page = page
        simp = cc.convert(text)
        lines.append(simp)
        simp_paras.append((page, simp))

    return "\n".join(lines), simp_paras


# ─────────────────────────────────────────────────────
# Step 3: 结构化切分 → events
# ─────────────────────────────────────────────────────

YEAR_HEADER_RE = re.compile(r"公元\s*(\d{3,4})\s*年")

CN_NUM = r"[一二三四五六七八九十百千零○〇\d]+"
DATE_START_RE = re.compile(rf"^({CN_NUM}月{CN_NUM}日|{CN_NUM}月)")

CN_DIGIT = {
    "零": 0, "〇": 0, "○": 0,
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    "十一": 11, "十二": 12,
}

def cn_to_int(s: str) -> int | None:
    s = s.strip()
    if re.fullmatch(r"\d+", s):
        return int(s)
    if s in CN_DIGIT:
        return CN_DIGIT[s]
    if s.startswith("十") and len(s) <= 3:
        rest = s[1:]
        return 10 + (CN_DIGIT.get(rest, 0) if rest else 0)
    if s.endswith("十") and len(s) == 2:
        return CN_DIGIT.get(s[0], 1) * 10
    return None


def parse_date(year: int, raw: str) -> str:
    m = re.match(rf"({CN_NUM})月(?:({CN_NUM})日)?", raw)
    if not m:
        return str(year)
    month = cn_to_int(m.group(1))
    if month is None or not (1 <= month <= 12):
        return str(year)
    if m.group(2):
        day = cn_to_int(m.group(2))
        if day and 1 <= day <= 31:
            return f"{year:04d}-{month:02d}-{day:02d}"
    return f"{year:04d}-{month:02d}"


def parse_events(simp_paras: list[tuple[int, str]]) -> list[dict]:
    events = []
    evt_id = 0
    current_year = None
    CHRONICLE_START = 1865

    for page, text in simp_paras:
        hdr = YEAR_HEADER_RE.search(text)
        if hdr:
            current_year = int(hdr.group(1))
            if current_year >= CHRONICLE_START:
                evt_id += 1
                events.append({
                    "id": f"evt_{evt_id:05d}",
                    "year": current_year,
                    "date": str(current_year),
                    "type": "year_header",
                    "raw_text": text,
                    "source_page": page,
                })
            continue

        if current_year is None or current_year < CHRONICLE_START:
            continue

        date_str = str(current_year)
        dm = DATE_START_RE.match(text)
        if dm:
            date_str = parse_date(current_year, dm.group(0))

        evt_id += 1
        events.append({
            "id": f"evt_{evt_id:05d}",
            "year": current_year,
            "date": date_str,
            "raw_text": text,
            "source_page": page,
        })

    return events


# ─────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────

def main():
    print("Step 1/3: 加载段落 + 页码...")
    paras = load_paras(SRC)
    pages = [p for p, _ in paras]
    print(f"  {len(paras)} 段落，页码范围 {min(pages)}–{max(pages)}")

    print("Step 2/3: 繁→简 + 生成 simplified.txt...")
    cc = OpenCC("t2s")
    full_text, simp_paras = build_simplified_txt(paras, cc)
    TXT_OUT.write_text(full_text, encoding="utf-8")
    print(f"  写入 {TXT_OUT}  ({TXT_OUT.stat().st_size:,} bytes)")

    print("Step 3/3: 结构化切分 → events JSON...")
    events = parse_events(simp_paras)
    JSON_OUT.write_text(
        json.dumps(events, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  {len(events)} 条事件，写入 {JSON_OUT}  ({JSON_OUT.stat().st_size:,} bytes)")

    # ── 质量抽查 ──
    print("\n── 前5条事件 ──")
    for e in events[:5]:
        print(json.dumps(e, ensure_ascii=False))

    print("\n── 末5条事件 ──")
    for e in events[-5:]:
        print(json.dumps(e, ensure_ascii=False))

    print("\n── 年份分布（全部）──")
    year_counts = Counter(e["year"] for e in events)
    for yr in sorted(year_counts):
        print(f"  {yr}: {year_counts[yr]} 条")

    # 日期字段统计
    dated = sum(1 for e in events if re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", e["date"]))
    print(f"\n── 日期精度：{dated}/{len(events)} 条有具体月份或日期 ──")


if __name__ == "__main__":
    main()
