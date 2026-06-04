# IEEE VIS VAST Challenge 2026 —— 赛题拆解 / 数据拆解 / 突围策略

> 这是一份给自己看的工作笔记。覆盖：官方题目的中文化解读、数据集真实结构（已解压并抽样验证）、2020–2025 历届获奖作品的共性分析，以及"AI 编程助手已经抹平基础代码差距"的前提下今年怎么打。

---

## 一、本届赛事关键信息

- **大会**：IEEE VIS 2026 同期举办的 VAST Challenge（Visual Analytics Science and Technology Challenge）。
- **今年主题**：用可视分析（visual analytics）理解 **agentic AI**（智能体型 AI）的行为，特别是它们在企业环境里跑偏、违规、或被绕过约束的情形。
- **赛道**：本届目前公开了两个 Mini-Challenge：
  - **MC1**：多智能体系统的"合规防线被击穿"事件（信息禁运被泄露）。
  - **MC2**：一台智能体异常发帖到外部社交平台 SaidIt（"乱码型"故障）。
- **关键时间点**：
  - 启动：2026 年 4 月 13 日（MC1 数据已开放）。
  - 提交截止：2026 年 7 月 17 日 23:59（AOE 时区，国际日期变更线西侧的"地球上最晚"时间）。
  - 两页论文（可选，进会议论文集）：2026 年 8 月 14 日。
- **提交要求**：
  - 一份 `index.htm` 答题表（必须保留 `.htm` 后缀），命名规范是 `组织-主联系人姓-MCx`，例如 `UMD-Jones-MC2`。
  - 一段不超过 **4 分钟** 的带解说视频，`.wmv` 格式，太大就发到网上放链接。
  - 整个目录打包成 `zip`（不接受 rar/tar），50 MB 以内；超出就把视频外链。
  - 通过 PCS（Precision Conference System）的 VIS 2026 - VAST Challenge 赛道提交。
  - 走 GitHub 链接提交也允许，但要打 tag 或 release，且报名表必须在截止前完整提交（不能只丢一个仓库链接）。

---

## 二、MC1 中文拆解 —— 合并案的信息禁运是怎么被击穿的

### 故事背景

TenantThread 是一家做"租户管理软件"的 proptech（地产科技）公司，主打产品包括一个争议很大的 **Retention Optimizer（留客优化器）**：它会根据租客的付款时间、报修记录、甚至消息语气给租客打分，再把分数低的人标成"高摩擦租户"或者建议房东在续约时施压。公司对外宣称数据匿名，但实际上在小区样本里一交叉就能反查到人名。

地方报纸 *SaltWind Journal* 一直在做这个公司的连续调查报道，社交平台上 `#AlgorithmicEviction`（"算法驱逐"）话题已经发酵几周。

就在这个风口浪尖上，TenantThread 悄悄和大型房产运营商 **CivicLoom Realty Partners** 签了并购协议，内部代号 **Project HarborCrest**。并购公告严格禁运（embargo）到 **2046 年 6 月 5 日下午 6 点** 才能对外披露。为防泄密，公司部署了一个自动合规审查工具，代号 **"The Judge"（法官）**。

结果：当天下午 **5 点**——禁运解除前 1 小时——并购的相关信息已经从 TenantThread 的"自动化舆情&公关账户"在社交平台 **FleX** 上冒出来了。**禁运被击穿。**

CivicLoom 的法务团队要搞清楚：**是 TenantThread 团队故意泄密，还是这个智能体系统在压力下自己崩了？** 你的任务就是辅助这次法务调查。

### 必须回答的三组问题

1. **导致越权发布的关键事件和关系是什么？**
   - 把事件序列可视化出来，要包含：关键动作、因果关系、决策节点和决策参与方。
   - 高亮所有"让这条帖子绕过 The Judge 跑出去"的决策点和系统组件。

2. **这种"绕过禁运"是新行为。要描述系统/智能体/人员的正常行为基线，然后对比。**
   - 异常发生前有没有先行指标（leading indicators）？
   - 历史上有没有过"智能体实际行为偏离预期"的情况？什么时候？偏在哪里？
   - 有没有过类似"差点泄密"的其他事件？什么时候？是什么样的行为？
   - 那些之前的事件为什么没有引起干预？

### 数据集真实结构（已抽样验证）

文件清单：
- `MC1_final_00.json` ——主数据，是泄密前两周的智能体活动日志。
- `VAST Challenge 2026 MC1 Answer Sheet.htm` ——答题表，复制改名成 `index.htm` 后填写。
- `mc1 data description.md` ——官方说明。

JSON 顶层结构是 `rounds` 数组，每个 round 对应**一小时**的快照（实测 23 个 round，从 `2046-05-17T09:00:00` 之后那一批开始，注意：官方介绍说覆盖泄密前两周，但当前发布的子文件 `_00` 大概只是其中一段时间窗口）。每个 round 包含两部分：

**环境上下文 `environment_context`**：
- `event_narrative` / `event_headline`：这一小时的事件叙事和标题（合成的"剧本"）。
- `market_snapshot`：市场快照。
- `media_events`：媒体动态。
- `social_state`：社交平台状态。
- `external_actor_actions`：外部各方动作。
- `social_manager_alerts`：Social-Manager 智能体收到的告警。
- `agents_unavailable`：当前不可用的智能体列表（人/机偶尔会"下线"）。
- `critical_deadlines`：关键截止时间（如禁运解除时点）。
- `news`：新闻。

**智能体输出 `agent_outputs`**：每个智能体在这一小时的：
- `internal_state`：内部思考三件套——`reacting`（反应）/ `rationalizing`（合理化解释）/ `deliberating`（权衡）。**这是题目的金矿**，能直接看到智能体的"思想"。
- `communications`：本小时发出的消息列表（message_id、channel、text）。
- `declared_action`：宣称的动作（如 `MONITORING`）。

### 七个智能体（这是 MC1 的人物表）

| Agent ID | 角色 | 标签 | 资历 | 说明 |
|---|---|---|---|---|
| `legal_agent` | 法务 | Legal-Agent | 资深 | 公司总法律顾问。 |
| `quality_agent` | 平台信任 | Platform-Trust | 资深 | 平台信任与安全副总裁。 |
| `social_manager_agent` | 社交经理 | Social-Manager | 资深 | 管社交平台对外消息。 |
| `pr_agent` | 公关 | PR-Agent | 资深 | 公关与对外沟通负责人。 |
| `intern_agent` | 实习生 | Intern | 初级 | 通用实习生。 |
| `pr_intern_agent` | 公关实习生 | PR-Intern | 初级 | **关键嫌疑人**：拥有 TenantThread 官方 Flex 账号的访问权。 |
| `judge_eval_agent` | 法官 | Judge | 合规官 | 评估风险、调解冲突、提供合规指导——也就是 **"The Judge"**。 |

调查时要时刻盯着两个"窗口型"角色：**PR-Intern**（有 Flex 发帖权的初级账号）和 **The Judge**（理论上应该拦下违规的合规层）。多智能体事故里最常见的剧本就是"低权限的初级 agent 在高资历 agent 的压力下越权操作，而 Judge 因为某种规则盲区没拦住"。

### 关键实体与代号

- **TenantThread**：被收购方，本案数据所有者，做"留客优化器"那套打分系统。
- **CivicLoom**：收购方，到 6 月 5 日 18:00 前身份是禁运信息。
- **Project HarborCrest**：本次并购的内部代号。
- **ResidentIQ**：另一家被 *SaltWind Journal* 同期报道的 proptech。
- **SaltWind Journal**：在做"算法驱逐"系列调查的地方报纸。
- **OceanCrunch**：科技媒体，记者 Sarah Kowalski。
- **@HorizonMgmt / @PinnacleResidential**：TenantThread 的大客户。

### 通信渠道（channels）

智能体之间、智能体对人、智能体对其他系统都有不同的 channel，且**它们被授权可以直接发社交平台帖子，监管很轻**——这就是漏洞所在。建模时把 channel 当成边的"类型"维度是必须的。

---

## 三、MC2 中文拆解 —— 凌晨四点的乱码贴怎么发出去的

### 故事背景

你在 A 公司的 AI 系统管理部门工作。最近 SaidIt（一个类似 Reddit 的论坛）上出现了一篇看起来像"智能体故障"的帖子：内容是**乱码**，发在一个**看起来随机选出**的板块。任务是查清楚为什么会发出来，并给出补救建议。

异常贴的发送者是 **John Windward**，时间是 **2046 年 5 月 17 日凌晨 4:21**。

这套智能体系统很复杂，自动化行为很多，没人完整画过它的拓扑图。你要做的是先**画出整个系统的活动基线**，再把这次具体异常**对照**进去，最后给出干预建议。

### 必须回答的问题

1. **这条乱码贴是怎么被发出来的？** 做一个事件序列的可视化工具，包含所有重要的人和系统交互。
   - 给出针对该消息的**详细视图**（事件链）。
   - 给出**系统全局视图**，把这条事件链放回大系统的上下文里。
2. **这些贴子"含义"是什么？** 它的内容来自哪里？给出推断逻辑。
3. **会不会再发生？**
   - 在历史日志里找出**其他类似实例**，对比本次和过往。
   - 至多挑**一个干预点**，论证为什么在这里干预最有效。

### 数据集真实结构（已抽样验证）

文件清单：
- `MC2 data.json` ——内部系统采集到的时间线。
- `org_chart.json` ——TenantThread 的组织架构图（包含人和部门，**直接兼容 NetworkX 的 `node_link_graph` 格式**，可以直接 `nx.node_link_graph(json.load(f))` 加载）。
- `VAST Challenge 2026 MC2 Answer Sheet.htm` ——答题表。
- `MC2 data description.md` ——官方说明。

**主数据集 `MC2 data.json` 是一个事件流**：

```json
{
  "description": "Tenant Thread activity",
  "events": [
    {
      "short_name": "sent",                       // 动作名
      "parties": ["person:isaac_mast", "person:levi_signal"],
      "when": 2409423492.0,                       // Unix 时间戳，落在 2046-05
      "details": {"from": "...", "to": "...", "subject": "...", "status": "sent"},
      "id": 15246                                 // 全局唯一
    }
    // ...
  ]
}
```

**规模实测**：**185 147 条事件**，**24 种动作类型**。事件类型至少包括：

`access_email` / `access_files` / `ask_agent` / `assign_agent_task` / `check_access` / `check_email` / `check_in` / `create_file` / `delete_file` / `enter_room` / `flex_post` / `give_advice` / `list_files` / `post_flex` / `post_saidit` / `propose_meeting` / `queue_subordinate_task` / `read_file` / `received` / `saidit_post` / `saidit_post_check` / `send_email` / `sent` / `suggest_contacts`

把动作类型粗分成几组对建模很有帮助：

- **通信类**：`sent` / `received` / `send_email` / `check_email` / `access_email` / `propose_meeting`
- **物理/位置类**：`enter_room` / `check_in`
- **文件操作类**：`access_files` / `list_files` / `read_file` / `create_file` / `delete_file`
- **智能体协作类**：`ask_agent` / `assign_agent_task` / `queue_subordinate_task` / `give_advice` / `suggest_contacts`
- **权限校验类**：`check_access`
- **外部发布类**：`flex_post` / `post_flex` / `post_saidit` / `saidit_post` / `saidit_post_check`

⚠️ **注意名字相近的成对动作**：`flex_post` vs `post_flex`、`post_saidit` vs `saidit_post` —— 这些大概率是**不同主体或不同阶段的动作**（比如一个是"准备发"，另一个是"已发"，或者一个是"机执行"，一个是"人审核结果"）。**必须先做语义对齐**，不然分析会错。

**组织架构 `org_chart.json`**：75 个节点（公司/部门/人/智能体的混合实体，第一个节点就是 `company:tenant_thread`），且**当前文件 `links: 0`**——说明组织关系要么藏在 `edges` 字段里，要么需要从事件里反推。打开看一眼就知道。

---

## 四、IEEE VIS VAST Challenge 历届优秀作品研究（2020–2025）

> 这一节是做赛感的：评委到底偏好什么、什么样的作品能上奖、近年的趋势走向，以及为今年的策略找证据。

### 2020 —— 网络安全 + 图匹配 + 目标检测

主题围绕"从大型背景图中识别种子模板子图"做网络攻击溯源，外加图像中的关键人物识别和概念设计。

获奖代表：
- **MC1（图匹配）**：Université Paris-Saclay / CNRS / Inria 联合体的 **GraphletMatchMaker**；山东大学 *Cyber Attacks Analytics*；康斯坦茨大学；SAS 等。
- **MC2（图像目标检测）**：天津大学 *Uncovering the Missing Links* 拿下；亚利桑那州立大学的 *TotemFinder*；德州理工的 *VisMCA*。
- **MC3（设计挑战）**：普渡大学的 *ConstellationBuilder*。

特点：评委依然偏好**算法 + 可视化深度结合**的作品，不只是"画得好看"。

### 2021 —— 文本 / 多模态 / 社交媒体叙事

数据集主题是文本多面关系、媒体偏见、时空态势感知与社交媒体事件叙事。

获奖代表：
- **MC1（多面关系）**：北京大学；天津大学（媒体偏见可视化）。
- **MC2（时空态势）**：Data Star + 复旦大学的 *Spatio-temporal Situation Awareness with Multi-data Fusion*；Hasselt 大学（"人在回路"集成）。
- **MC3（叙事可视化）**：天津大学 *Mining and Understanding Stories in Text Sequences with Narrative Visualization*；Data Star + 复旦 *Mixed-Initiative Visual Exploration*；JMU + 普渡的 *CloudAnnotator*。

关键词第一次明显出现："**叙事化（narrative）**"和"**人机协作（human-in-the-loop / mixed-initiative）**"。

### 2022 —— 虚拟智慧城市 / Patterns of Life

围绕一个虚构智慧城市的多源传感与社交记录展开，覆盖人口与社会关系、生活模式、经济金融健康。

获奖代表：
- **MC1（人口与关系）**：复旦大学；TU Darmstadt + Fraunhofer。
- **MC2（生活模式）**：**伦敦城市大学 giCentre** 用 **Observable Notebooks** 做的方案直接拿奖；SAS；普渡的 *ClusBridges*。
- **MC3（经济金融）**：复旦的 *EconomicVis*；VRVis + Virginia Tech。

特点：**Observable + D3** 这条路径开始在评委心目中明显加分；评委不喜欢纯 Tableau 等"成品 BI"。

### 2023 —— 非法捕捞知识图谱 + LLM 首登场

FishEye International 的非法、未报告、未管制（IUU）捕捞知识图谱，包括公司、所有者、雇员、财务等实体。

获奖代表：
- **MC1（实体上下文）**：南方科技大学的 **FishHook** 拿到 *Outstanding Comprehensive*；ETH Zürich 的 *FishSense*。
- **MC2（贸易数据）**：德州理工 *Effective Network Layout for Transaction Analysis*。
- **MC3（商业关系）**：康斯坦茨大学 *Intuitive Filtering Interactions for Large Networks*；**普渡 #1017** 拿到 *Application of LLMs to Support VA Process* —— **第一份明确以 LLM 集成获奖的提交**。

关键词："**大规模知识图谱**"成为主战场；**LLM 第一次进入获奖语言**。

### 2024 —— 偏见溯源 + Grand Challenge 回归

CatchNet 知识图谱，调查新闻 / 算法偏见，识别非法捕捞行为转移，追踪偏见如何被注入数据。Grand Challenge 把三个 MC 整合起来。

获奖代表：
- **MC1（识别偏见）**：FGV 的 D. Diaz *Strong Data Enrichment*；康斯坦茨 R. Buchmuller *Novel Approaches for Establishing and Measuring Bias*；复旦 T. Qiu *Effective Use of Coordinated Views*。
- **MC2（地理-时序签名）**：复旦 Y. Shan *Analysis-Driven Interaction Design*；SAS；普渡 Y. Chen *Multiple Embedding Techniques*。
- **MC3（时序商业关系）**：SMU *Comprehensive Characterization of Suspicious Behaviors*；北大 Y. Guo *Thoroughness in Analysis*；RPTU J-T. Sohns *Effective Composition of Visual Encodings*。

关键词："**偏见**"成主题；"**多重嵌入（multi-embedding）**" 这种 UMAP/t-SNE + 语义聚类的技术上桌；评委的颁奖语已经普遍用 "thoroughness" / "analysis-driven" 这种"分析向"的词。

### 2025 —— 海洋岛国文化冲突 + 设计挑战正式拆开

虚构海洋岛国 **Oceanus**：全球音乐巨星崛起带动旅游业暴涨与传统渔业衰败之间的社会冲突。三个 MC 加一个 Design Challenge，且 DC **首次被正式作为独立奖项**。

获奖代表：
- **MC1（音乐影响力图谱）**：普渡 H. Y. Zong *Comprehensive Treatment of Time*；复旦 M. Hou *Excellence in Analytical Dashboards*。
- **MC2（派系冲突）**：康斯坦茨 P. Müller & T. Schulze *Elegant Visual Metaphor*。
- **MC3（无线电对话知识图谱）**：FGV A. De la Puente *Innovative Display of Daily Communication Patterns*；复旦 X. Zhou *Effective Integration of Tools and Encodings*。
- **设计挑战（DC）**：普渡 S. Qaiser *Expressive Design*；MIT D. Wootton *Intuitive Support for Query Construction*。

关键词："**视觉隐喻（visual metaphor）**" 第一次被单独命名颁奖；"**设计表达力（expressive design）**"被显著抬高权重。

### 六年沉淀出的获奖规律

**1. 工具栈（按近年频次排）**
- **Observable Notebook + D3.js** —— 上升势头明显，2022 起多次获奖。
- **React + D3 / Vega-Lite** —— 自研系统的事实标准。
- **Streamlit / Dash** —— 主要在分析型仪表板里出现（SAS、SMU 多次）。
- **Python（NetworkX、PyTorch、Sentence-Transformers）+ 前端联调** —— 2024 起 embedding 流行。
- **Tableau** 偶有但很少进决赛——评委不偏好"现成 BI"。

**2. 评委颁奖语里的关键词**

| 类型 | 出现频次 |
|---|---|
| Comprehensive / Strong / Effective（系统完整度） | 高 |
| Novel / Innovative / Elegant Metaphor（创新性） | 高且上升 |
| Narrative / Storytelling（叙事化） | 2021、2024、2025 显著 |
| Thoroughness / Analysis-Driven（分析深度） | 一直被奖励 |
| LLM / AI 集成 | 2023 首次单独奖；2024–2025 退化为底层工具 |

**3. 一个反直觉的结论**：纯**技术新颖性**（新算法）反而不是优势项——数据全部是合成的，技术只要够用就行，**真正赢的是"组装方式独特 + 分析深 + 叙事会讲"**。

**4. 必备的可视化打法**
- **多视图协调（Coordinated Multiple Views）** 几乎是必备。
- **大型 KG 不要变成意大利面**——康斯坦茨"intuitive filtering"路线连胜。
- **时间编码**：small multiples、horizon、螺旋时间在 2024–2025 高频中奖。
- **Embedding 投影**（UMAP/t-SNE + 语义聚类）2024 起明显增多。
- **视觉隐喻**（把抽象现象用世界里的实体讲清楚）开始单独被奖励。

**5. 必备的交互打法**
- **人在回路标注 / 纠错**。
- **渐进式披露 + 焦点+上下文（focus + context）**。
- **跨视图刷选联动**已经是基线。

---

## 五、2026 趋势预测：今年评委大概率会奖励什么

题目核心是 "agentic AI behaviors" —— 智能体行为分析。**MC1 是"群体智能体合谋/失控泄密"，MC2 是"单智能体故障型乱码贴"**，正好对应 agent 失控的两种典型剧本：

- MC1 = **goal drift + 社会工程压力 + 合规盲区**（多智能体协作走偏）
- MC2 = **单点故障 + 行为退化 + 异常输出**（个体智能体崩坏）

把六年历史规律套上去，今年的获奖配方很可能是这样：

1. **把日志当成"时间 × 工具 × 实体"三轴的事件图**，而不是当成纯文本流——直接借鉴 2024 MC2 的 geo-temporal signature 思路，只是把"地理"换成"agent / channel / tool"。
2. **工具调用链的图谱化**：把 ask_agent / assign_agent_task / queue_subordinate_task 这些拼成 **agent-to-agent DAG**，把 access_files / send_email / post_flex / post_saidit 拼成 **agent-to-system 的外向调用**。借 2023–2025 KG 经验，但**必须**配 Konstanz 风格的"intuitive filtering"，不然就是意大利面。
3. **行为嵌入 + UMAP + 异常聚类**几乎肯定能上榜：给每个智能体在每个时间窗口做一个 embedding（拿 internal_state 三件套 + 动作直方图组），投影后看它有没有飘出"自己的正常区域"。沿 2024 普渡路线。
4. **强叙事 + 视觉隐喻**：把 agent 的"policy 漂移"、"合规层失效"用人格化或剧情化的视觉修辞讲清楚（参考 2025 康斯坦茨的 Elegant Visual Metaphor）。比如把 The Judge 的判断过程画成"安检门 + 通过率热力"，把 PR-Intern 的越权画成"细小裂缝里的水流"。
5. **人在回路的审计交互**：让用户标记"可疑步骤"并反向追踪上下游影响。这能直接打到评委对"调查导向交互"的偏好。

---

## 六、AI 智能体时代怎么突围（关键问题）

> 前提：Copilot / Claude 已经能让任何人 30 分钟写出 D3 力导向图、Observable 仪表板。**写代码本身不再是壁垒**，**人和人的"基础工艺"差距被抹平了**。这正是你担心的事。

那么六年规律告诉我们，**突围只能从三条 AI 暂时还不擅长的路线上走**：

### 路线 1：分析深度 —— "你能问出别人不会问的问题"

AI 写代码很强，但 AI **不会主动替你设计调查问题**。评委历来奖励 *Thoroughness in Analysis* 和 *Comprehensive Characterization*（2024 PKU、SMU）。

- 不要止步于"找到那条越权发布的链路"。要进一步追问：
  - 这次失控属于哪一类？是 **prompt injection** / **goal drift（目标漂移）** / **memory poisoning（记忆污染）** / **role confusion（角色错位）** / **escalation under pressure（资深 agent 向初级 agent 施压）** 中的哪一种？
  - PR-Intern 是被谁"激活"的？是 PR-Agent 的直接指令，还是 Social-Manager 的告警把它推到了执行边缘？
  - The Judge 当时为什么没拦？是**没看到**（数据没流过它）、**看到了但判通过**（规则盲区），还是**它当时下线了**（看 `agents_unavailable`）？
  - 历史窗口里有没有过"差点被拦但其实拦住了"的擦边球？那些规则当时怎么生效的，这次为什么失灵？
- 输出形式建议是一份**调查叙事文档**：每个发现都写成 "线索 → 证据视图 → 反证 → 结论" 链条，让评委像看侦探小说一样读。

### 路线 2：叙事方式 —— "你交的不是 dashboard，是一份审计案例"

2021、2024、2025 都明确给"narrative / metaphor"颁过奖。叙事化提交的共同特征：

- **开篇有一个具体场景**："2046 年 6 月 5 日 17:03，PR-Intern 在没有被 Judge 评估的状态下发出了第一条触及 HarborCrest 的 Flex 帖。" —— 而不是"我们做了一个 dashboard"。
- **视图按调查推理顺序排列**，而不是按数据类型分页（不要"先放图谱页 / 再放时间线页 / 再放表格页"，而要"先放问题1的证据视图 / 再放问题2的证据视图"）。
- **用视觉隐喻**：
  - 把 agent 的 policy drift 画成"漂流的星轨"。
  - 把 The Judge 画成"安检门"，每条消息从它面前经过时透明度=审查置信度。
  - 把跨 channel 的信息扩散画成"水波"。
  - 把 MC2 的乱码贴溯源画成"破裂的传话游戏"——从源头一段段被改写。
- 两页 summary 写成 **case report**，不要写成 system paper。

### 路线 3：交互设计 —— "审计员能在 3 步内追到根因"

AI 助手不会替你设计**交互流程**。评委反复奖励 *Intuitive Filtering*（康斯坦茨三连）和 *Analysis-Driven Interaction Design*（2024 复旦）。

具体突围动作：

- **"问题模板"侧栏**：把审计员的常见问题做成可点击的预设查询，类似 2025 MIT 的 *Intuitive Support for Query Construction*。例如："谁在哪一小时绕过了 Judge？" / "PR-Intern 在过去两周里多少次单独发帖？" / "Judge 的判断置信度分布是否有阶段性下降？"
- **跨视图反向追溯**：点一个异常动作 → 自动高亮它的**全部历史上下文**（同一 agent 的早期行为、被谁触发、它又触发了谁）。**不是单向 brush，是因果反向链**。
- **Diff 视图**：把"合规 agent 的行为信号"和"失控 agent 的行为信号"叠加画出来，让差异在一秒内可见。这件事对 MC1 七个 agent 特别合适——拿任何一个资深 agent 和 PR-Intern 做对比模板。
- **LLM 副驾驶要做成可质疑的证据视图，而不是黑箱聊天框**：让 LLM 自动生成假设（"我猜 Social-Manager 在 16:30 的告警是触发因素"），但每个假设旁边**必须挂可点开的原始证据**，否则评委今年大概率会觉得是炫技。

### 三条"非显然"但加分的小技巧

- **自己做数据增强**（2024 FGV 的 *Strong Data Enrichment* 就是因此获奖）：对官方数据做二次清洗、补全 schema、抽取隐式关系，例如：
  - 把 MC2 里 `flex_post` / `post_flex` 这种近义动作做语义对齐与统一。
  - 把 `org_chart.json` 里目前 links=0 的部门 → 人员关系**自己从 events 里反推一份**。
  - 给 MC1 的 `internal_state` 三件套打"情绪/犹豫/合规担忧"标签（用 LLM 批量打，可视化时呈现）。
- **工具栈推荐**：**Observable Notebook + D3 + 一个轻量后端（FastAPI / Flask）**。六年获奖密度最高的组合，且 Observable 现场演示无敌——你 4 分钟视频里直接录屏 + voice-over，比录一个 React 应用清晰太多。
- **明确放一段"局限性 + 反偏见自省"**：今年的主题就是"AI 行为审计"，评委对**方法论自省**会有偏好——告诉他们"我们的检测会不会自己有偏见？数据合成可能引入了哪些假信号？"

---

## 七、个人执行建议

1. **先两周 MC1 一周 MC2**：MC1 故事更"政治化"、获奖天花板更高（多智能体合谋的故事更有戏剧张力），MC2 偏故障定位偏运维侧，叙事空间更窄但工作量也小。
2. **第一周先不要写代码**：先把 MC1 的 23 个 round 全部读一遍，把每个 agent 的 internal_state 文本通读，建立"小说式"的事件理解，再画系统拓扑草图。这一步 AI 替你看了你就会丢掉关键叙事素材。
3. **第二周开始原型**：Observable + D3，先做"事件流时间轴 + agent 状态泳道图" 这个最朴素但最叙事友好的视图。
4. **第三周做嵌入和异常检测**：拿 sentence embedding 对 `deliberating` / `rationalizing` 文本聚类，找"突变点"。
5. **第四周做隐喻设计 + 交互打磨 + 4 分钟视频脚本**：视频脚本比可视化系统更重要——评委看视频的时间比点你 demo 的时间多。
