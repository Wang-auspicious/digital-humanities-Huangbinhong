# -*- coding: utf-8 -*-
"""
把两个独立整页应用合并成单个自包含 HBH.html，零功能冲突、可继续加页面。

策略：
  · CSS —— 每页所有规则作用域化到 #hbh-<page>（消除 7 处同名类冲突 + :root/body/* + 关键帧改名）
  · JS  —— 每页内联脚本包进惰性初始化闭包（IIFE），消除全局名冲突；首次显示该页才执行（保证测量到真实尺寸）
  · 布局 —— 各页保持原汁原味 100vh（fixed inset:0），顶部自动隐藏切换条悬浮其上，不挤占/裁剪任何页面 UI
  · 跨页查询修正 —— atlas 的 document.querySelector('.rail') 限定到本页（map 也有 .rail）

用法：python build_hbh.py  → 生成 HBH.html
"""
import re

PAGES = [
    {"key": "map",   "title": "生命舆图", "file": "digital_hbh_map_story.html"},
    {"key": "atlas", "title": "实景山水", "file": "digital_hbh_shanshui_atlas.html"},
]
DEFAULT = "map"


# ── 提取 ──────────────────────────────────────────────────────────────────────
def extract(path):
    s = open(path, encoding="utf-8").read()
    styles = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", s, re.S))
    bm = re.search(r"<body[^>]*>(.*)</body>", s, re.S)
    body = bm.group(1) if bm else s
    # 外部脚本可能在 <head> 或 <body>，扫描整篇
    ext = re.findall(r'<script[^>]*\bsrc="([^"]+)"[^>]*>\s*</script>', s)
    inline = [m.group(2) for m in re.finditer(r"<script([^>]*)>(.*?)</script>", body, re.S)
              if "src=" not in m.group(1)]
    body_nos = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.S)
    return styles, body_nos, "\n".join(inline), ext


# ── CSS 作用域化 ──────────────────────────────────────────────────────────────
def scope_css(css, root):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    kf = {}
    rid = "#" + root

    def split_sel(sel):
        parts, depth, cur = [], 0, ""
        for ch in sel:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append(cur); cur = ""
            else:
                cur += ch
        if cur.strip():
            parts.append(cur)
        return [p.strip() for p in parts if p.strip()]

    def scope_one(s):
        s = s.strip()
        if s == "*":
            return rid + " *"
        if s in (":root", "html", "body"):
            return rid
        m = re.match(r"^(?:html|body|:root)\b\s*(.+)$", s)
        if m:
            return rid + " " + m.group(1)
        return rid + " " + s

    def handle(sel, body):
        low = sel.lower()
        if "keyframes" in low and low.lstrip().startswith("@"):
            m = re.match(r"(@[-a-z]*keyframes)\s+([A-Za-z0-9_-]+)", sel, re.I)
            if m:
                new = root.replace("-", "_") + "_" + m.group(2)
                kf[m.group(2)] = new
                return f"{m.group(1)} {new}{{{body}}}"
            return f"{sel}{{{body}}}"
        if low.startswith(("@media", "@supports", "@container")):
            return f"{sel}{{{walk(body)}}}"
        if low.startswith("@"):
            return f"{sel}{{{body}}}"
        scoped = ",".join(scope_one(p) for p in split_sel(sel))
        return f"{scoped}{{{body}}}"

    def walk(s):
        res, i, n, prelude = [], 0, len(s), ""
        while i < n:
            c = s[i]
            if c == "{":
                depth, j = 1, i + 1
                while j < n and depth > 0:
                    if s[j] == "{":
                        depth += 1
                    elif s[j] == "}":
                        depth -= 1
                    j += 1
                res.append(handle(prelude.strip(), s[i + 1:j - 1]))
                prelude = ""
                i = j
            elif c == "}":
                i += 1
            else:
                prelude += c
                i += 1
        return "".join(res)

    out = walk(css)
    for old, new in kf.items():
        out = re.sub(r"(animation(?:-name)?\s*:[^;{}]*?)\b" + re.escape(old) + r"\b",
                     lambda mm: mm.group(1) + new, out)
    return out


# ── 脚本跨页查询修正 ──────────────────────────────────────────────────────────
def fix_scripts(js, root):
    if root == "hbh-atlas":
        js = js.replace("document.querySelector('.rail')",
                        "document.querySelector('#hbh-atlas .rail')")
    if root == "hbh-map":
        js = js.replace("document.querySelectorAll('.city-pulse')",
                        "document.querySelectorAll('#hbh-map .city-pulse')")
        js = js.replace("document.querySelectorAll('.eraSeg')",
                        "document.querySelectorAll('#hbh-map .eraSeg')")
    return js


# ── 组装 ──────────────────────────────────────────────────────────────────────
def build():
    styles, sections, inits, ext_all = [], [], [], []
    for p in PAGES:
        root = "hbh-" + p["key"]
        css, body, js, ext = extract(p["file"])
        styles.append(f"/* ===== {p['file']} → #{root} ===== */\n" + scope_css(css, root))
        sections.append(
            f'<section id="{root}" class="hbh-page" data-page="{p["key"]}">\n{body}\n</section>')
        js = fix_scripts(js, root)
        inits.append(
            f"  HBH.init.{p['key']} = function(){{\n/* ---- {p['file']} ---- */\n{js}\n  }};")
        for e in ext:
            if e not in ext_all:
                ext_all.append(e)

    ext_tags = "\n".join(f'<script src="{e}"></script>' for e in ext_all)
    style_all = "\n\n".join(styles)
    section_all = "\n\n".join(sections)
    init_all = "\n\n".join(inits)
    nav_btns = "\n".join(
        f'    <button class="hbh-tab" data-go="{p["key"]}">{p["title"]}</button>'
        for p in PAGES)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>数字黄宾虹 · HBH</title>
<style>
  /* —— 全局基座 —— */
  html, body {{ margin:0; width:100%; height:100%; overflow:hidden; background:#e6cfaa; }}
  .hbh-page, .hbh-page * {{ box-sizing:border-box; }}
  /* 每页都是独立的全视口应用，互不干扰；隐藏的页 display:none */
  .hbh-page {{ position:fixed; inset:0; display:none; }}
  .hbh-page.active {{ display:block; }}

  /* —— 顶部自动隐藏切换条（悬浮，不挤占页面布局）—— */
  #hbh-nav {{
    position:fixed; top:0; left:50%; transform:translateX(-50%) translateY(-130%);
    z-index:99999; display:flex; align-items:center; gap:6px;
    padding:7px 10px; margin-top:8px; border-radius:999px;
    background:rgba(30,22,14,.82); box-shadow:0 8px 28px rgba(20,12,4,.38);
    backdrop-filter:blur(6px); opacity:0; transition:transform .32s ease, opacity .32s ease;
    font-family:"Noto Serif SC","Songti SC",serif;
  }}
  #hbh-nav.show {{ transform:translateX(-50%) translateY(0); opacity:1; }}
  #hbh-nav .brand {{ color:#e9cf9a; font-size:12px; letter-spacing:.18em; padding:0 6px 0 4px; }}
  .hbh-tab {{
    border:1px solid rgba(233,207,154,.32); background:transparent; color:#e7d6b2;
    font:13px/1 "Noto Serif SC","Songti SC",serif; letter-spacing:.12em;
    padding:6px 13px; border-radius:999px; cursor:pointer; transition:all .16s ease;
  }}
  .hbh-tab:hover {{ border-color:rgba(233,207,154,.7); color:#fff3d6; }}
  .hbh-tab.active {{ background:#b86d4f; border-color:#b86d4f; color:#fff6e6; }}
  /* 顶部感应热区：鼠标移到最上方即唤出导航 */
  #hbh-hot {{ position:fixed; top:0; left:0; right:0; height:64px; z-index:99998; }}

{style_all}
</style>
</head>
<body>

<!-- ============ 顶部自动隐藏导航（鼠标移到屏幕最上方唤出）============ -->
<div id="hbh-hot"></div>
<nav id="hbh-nav">
    <span class="brand">数字黄宾虹</span>
{nav_btns}
</nav>

<!-- ============ map_story 所需的本地数据脚本（全局，先于初始化加载）============ -->
{ext_tags}

<!-- ============ 各页面（原文件 DOM，CSS 已作用域隔离）============ -->
{section_all}

<!-- ============ 路由 + 惰性初始化 ============ -->
<script>
window.HBH = window.HBH || {{ init:{{}}, started:{{}} }};

{init_all}

(function(){{
  var nav = document.getElementById('hbh-nav');
  var hot = document.getElementById('hbh-hot');
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.hbh-tab'));

  function showPage(key){{
    document.querySelectorAll('.hbh-page').forEach(function(s){{
      s.classList.toggle('active', s.dataset.page === key);
    }});
    tabs.forEach(function(t){{ t.classList.toggle('active', t.dataset.go === key); }});
    if (!HBH.started[key]) {{            // 首次显示才初始化 —— 保证脚本测量到真实尺寸
      HBH.started[key] = true;
      try {{ HBH.init[key](); }} catch(e) {{ console.error('[HBH] init '+key+' 失败:', e); }}
    }}
    try {{ history.replaceState(null, '', '#'+key); }} catch(e) {{}}
  }}
  window.HBH.show = showPage;
  tabs.forEach(function(t){{ t.addEventListener('click', function(){{ showPage(t.dataset.go); }}); }});

  // —— 自动隐藏：移到顶部唤出，离开 2s 后收起 ——
  var hideTimer;
  function reveal(){{ nav.classList.add('show'); clearTimeout(hideTimer);
    hideTimer = setTimeout(function(){{ nav.classList.remove('show'); }}, 2200); }}
  hot.addEventListener('mousemove', reveal);
  nav.addEventListener('mousemove', function(){{ nav.classList.add('show'); clearTimeout(hideTimer); }});
  nav.addEventListener('mouseleave', reveal);
  document.addEventListener('keydown', function(e){{ if(e.key==='Tab' && e.altKey){{
    e.preventDefault(); var i=tabs.findIndex(function(t){{return t.classList.contains('active');}});
    showPage(tabs[(i+1)%tabs.length].dataset.go); reveal();
  }}}});

  // —— 默认页 ——
  var initial = (location.hash||'').replace('#','');
  if (!HBH.init[initial]) initial = '{DEFAULT}';
  showPage(initial);
  reveal();   // 进场提示一次
}})();

/* ───────────────────────────────────────────────────────────────────────────
   如何新增一个页面（保持零冲突）：
   1) 写好独立的整页 newpage.html（自带 <style>/<script>，可正常单独打开）；
   2) 在 build_hbh.py 的 PAGES 列表追加 {{key:'xxx', title:'菜单名', file:'newpage.html'}}；
   3) 重新运行  python build_hbh.py  → 自动作用域化 CSS、闭包化 JS、并入本文件。
   （手工加亦可：仿照上面 #hbh-xxx 的 <style> 作用域、<section> 与 HBH.init.xxx 三处即可。）
   ─────────────────────────────────────────────────────────────────────────── */
</script>
</body>
</html>
"""
    open("HBH.html", "w", encoding="utf-8").write(html)
    print("已生成 HBH.html，大小 %.0f KB，页面：%s" % (
        len(html) / 1024, "、".join(p["title"] for p in PAGES)))


if __name__ == "__main__":
    build()
