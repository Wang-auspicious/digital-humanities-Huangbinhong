# 第三屏《实景山水》游踪线动效 — 设计 spec

日期：2026-06-05
范围：`HBH.html` 单屏 `#hbh-atlas`（实景山水）
目标：把静止的山水底图"加点动的"，用一条**按年代游历顺序**在群山间游走的动态线，把这些山「串起来」。

## 背景

`#hbh-atlas` = 一张水墨底图 `山水底图.png`，上挂地名签（名山/胜水），引线连到地图锚点；
点签 → 右侧展开该地存世画作。整屏完全静止，老师要求加动态。

灵魂是"以步履丈量山川"——黄宾虹登黄山、入青城、溯嘉陵、渡漓江，是一条真实行旅路线。
第一屏《生命舆图》已有"朱砂线标出迁居·走过后留痕"的语言，本屏游踪线与之跨屏呼应。

## 用户拍板的四个决定

1. **方向**：游踪路线流动（非氛围微动）。
2. **顺序**：按年代游历顺序——用每个锚点 `yearText` 首年排序。
3. **标记与留痕**：朱砂游踪点 + 自绘墨线留痕（线走过后常驻）。
4. **播放**：进屏自动走一遍 + 角落「重游」重播控件。
5. **凌乱处理**：领头亮、身后渐隐 + 平滑曲线（认可）。

## 数据

取 `DATA.labels` 中 `sub ∈ {名山, 胜水}` 且有 `yearText` 的锚点，共 18 个：
黄山1899 · 惠山1909 · 新安1909 · 泰山1912 · 嘉陵江1925 · 池州青玉峡1927 · 八桂1928 ·
漓江1928 · 金华山1930 · 桂林1931 · 雁山1931 · 蜀游1933 · 青城山1933 · 九华山1936 ·
横槎江1936 · 武夷九曲1947 · 临安1951 · 南岳1953。
（`名胜斋馆` 类无 yearText、非地理实景，不进路线，仍可点击。）

锚点屏上坐标 = 与现有引线圆点同一算法：`MAP_LABEL_POS[key]` 存在则取 `[pos[0], pos[2]]`（0–100 SVG 空间，与底图 viewBox 一致），否则回退 `d.anchor`。18 个均有 `MAP_LABEL_POS`。

## 视觉

- **朱砂赭游线**，细、平滑（Catmull-Rom→三次贝塞尔，张力 ~0.85 收敛防过冲），贴 feTurbulence 墨纹滤镜做毛笔涩感。
- **留痕（trail）**：低透明朱砂线，走过即常驻；用 `stroke-dasharray=L / stroke-dashoffset=L−cur` 逐段揭示。
- **领头亮（head）**：一段短而亮的发光段（长 ~6% L）始终贴在游踪点身后，dasharray 短窗 + 负 dashoffset 定位 `[cur−HEAD, cur]`；与暗 trail 形成"领头亮、身后渐隐"对比。
- **朱砂游踪点**：HTML 元素，按 `getPointAtLength(cur)` 的 (x,y) 定位为 `left:x% top:y%`（底图 viewBox 0–100 + preserveAspectRatio=none，% 与用户坐标一一对应）。带辉光。
- **随动小题**：点旁一行衬线小字（如「1933 · 青城坐雨」），随经过的锚点更新——把装饰线升级为叙事线。
- **逐山点亮**：游踪点经过某锚点 → 该地名签 `pulse`（短暂放大/发光）一下。

## 交互 / 播放

- `HBH.init.atlas` 首次（进屏）末尾自动起播一遍 → 画满定住，head/点淡出，trail 常驻。
- 角落「重游」按钮重置重播。
- **每次进屏重播**：`showPage` 路由里，非首次进入 atlas 时调用 `HBH._atlasReplay()`（首次由 init 自播，避免双触发）。
- **不干扰看画**：游线层 `pointer-events:none`，在地名签之下（线在底图之上、签之下；点/小题在最上但 pointer-events:none）。
- **面板开时暂停压暗**：右侧画卷 `#paperPanel.show` 或 `#imageViewer.show` 时，冻结进度并给游线层加 `.dimmed`；关闭后续播。

## 实现路子（选 A）

A. **SVG path + `stroke-dashoffset` 自绘 + `getPointAtLength` 驱动 + rAF 单一进度 t**。
复用现成：`#hairlines` 同款 SVG 叠层、`bInk` 同款 feTurbulence、label pulse 走 CSS。
离线、无库、可精确触发逐山事件、留痕、易重播。
（B Canvas 毛笔=过重；C 纯 CSS offset-path=逐山触发仍需 JS，控制力差。）

## 落点

- markup：`.mapBox` 内加 `<svg id="journeyLayer">`（底图之上、引线之下）+ `#journeyDot` `#journeyTip` `#journeyReplay`（mapBox 末尾、最上层）。
- CSS：`#hbh-atlas` 段前新增独立 `<style>` 块（scoped `#hbh-atlas .journey*`）。
- JS：`HBH.init.atlas` 内 `DATA.labels.forEach` 渲染签之后追加 `setupJourney()` IIFE；并在该 forEach 里给每个 `d` 存 `d._el`。
- router：`showPage` 加非首次 atlas → replay 分支。

## 风格红线（沿用 [[feedback-hbh-deck-style]]）

矿物水墨色 / 朱砂赭 accent / 衬线 / 无英文 / 纯手绘 SVG 无库 / 不遮挡主体 / 引线连对点 / 人文笔触。

## 迭代 1（2026-06-05 当日用户反馈）

1. **朱砂 → 水墨**：trail/head/dot 全改墨色（黑/深墨），去掉红色辉光，head 用墨色描边 + feTurbulence 涩感。
2. **放慢**：从单段 9.5s 缓动改为 **delta-time 匀速推进** `TRAVEL_MS≈16.5s`。
3. **要地停顿 + 黑色浮注**：定 6 处「要地」(`MEANINGFUL`：黄山/嘉陵江/青城山/漓江/武夷九曲/南岳)，游踪点到达即**停顿 `PAUSE_MS≈1.6s`** 并浮出**黑色 ≤10 字注**（`.journeyNote`，贴线、纸色光晕、衬线），常驻直至隐去或重播。取代原「随动小题」单 tip。
4. **左下角隐显按钮** `#journeyToggle`：切 `.mapBox.journey-hidden` 隐去轨迹+浮注+控件，动画冻结，**沉浸式自己探索**地图与画作。

## 自检

Chrome headless 截关键帧（起播中段/走满/面板开暂停），核验：线不乱、不遮 titleBlock、点击看画不受影响、风格统一。备份 `HBH.html.bak_journey_*`。
