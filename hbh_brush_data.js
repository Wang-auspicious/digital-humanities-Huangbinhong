/* ============================================================================
 * 第四屏「笔墨课徒」数据 —— 黄宾虹 五笔七墨语法谱
 * 全局：window.HBH_BRUSH
 *
 * 诚实约定：
 *  - def 为黄宾虹本人原话（引自《画法要旨》/画语录/尺牍），src 标出处；
 *    note 为画理白话疏解（我们的话），与原话分栏，不混同。
 *  - 每条引文均可回溯到 huangbinhong_simplified.txt 行号（srcLine），供复核。
 *  - 手绘 demo 为「教学图示」，非任何真迹的逐笔分层；sample 为真迹缩图，仅作"此法多见于此类作品"的指认。
 * ========================================================================== */
window.HBH_BRUSH = {
  intro: {
    kicker: "数字黄宾虹 · 第四章",
    title: "笔墨课徒",
    // 给草草看两眼的人一句大白话
    plain: "中国画的高下，全在一笔一墨之间。黄宾虹把这件说不清的事，拆成了十二个字——五种用笔，七种用墨。认得这十二个字，再看他那一团黑，就看得出门道了。",
    quote: "笔以立其形质，墨以分其阴阳。图画悉从笔墨而成。",
    quoteSrc: "黄宾虹《与朱砚英书》",        // huangbinhong_simplified.txt L3404
    capstone: "善画者，筑基在笔，建勋于墨，而能使笔墨变化于无穷者，在蘸水。",
    capstoneSrc: "黄宾虹 论墨"                // L2455（宾翁原话）
  },

  // —— 五笔：平 圆 留 重 变 —— 用 c1 黛青系
  // —— 七墨：浓 淡 破 泼 积 焦 宿 —— 用 accent 赭红系
  marks: [
    { key:"ping", char:"平", cat:"笔", metaphor:"如锥画沙",
      def:"一曰平，如锥画沙。",
      note:"中锋行笔，力量匀贯，不偏不漂，如锥尖画过沙地，两边匀整而中有一线。宾翁谓凡画山体，'以颜鲁公正书如锥画沙之法行之'——画山先要这一口匀劲的力。",
      src:"《画法要旨》", srcLine:5649, demo:{kind:"stroke", style:"ping"} },

    { key:"yuan", char:"圆", cat:"笔", metaphor:"如折钗股",
      def:"二曰圆，如折钗股。",
      note:"转折处圆转有力而无圭角，如金钗弯折，外圆而内劲。笔笔中锋，转而不断，是为圆。",
      src:"《画法要旨》", srcLine:5649, demo:{kind:"stroke", style:"yuan"} },

    { key:"liu", char:"留", cat:"笔", metaphor:"如屋漏痕",
      def:"三曰留，如屋漏痕。",
      note:"行处皆留，笔留得住、按得下，如雨水沿斑驳墙面渗下，时顿时行、欲行又止，积点成线，迟涩而不浮滑。",
      src:"《画法要旨》", srcLine:5649, demo:{kind:"stroke", style:"liu"} },

    { key:"zhong", char:"重", cat:"笔", metaphor:"如高山坠石",
      def:"四曰重，如高山坠石。",
      note:"用笔沉着有分量，落笔如高山坠石、力透纸背；重非粗黑，是骨力压得住纸。",
      src:"《画法要旨》", srcLine:5649, demo:{kind:"stroke", style:"zhong"} },

    { key:"bian", char:"变", cat:"笔", metaphor:"齐而不齐",
      def:"五曰变，参差离合，大小斜正，肥瘦短长，俯仰断续，齐而不齐，是为内美。",
      note:"前四笔随机应变、互参互用：参差离合、肥瘦短长，齐而不齐。宾翁以为画之'内美'正在这一'变'字——不齐之齐，才是天然。",
      src:"《画法要旨》", srcLine:5649, demo:{kind:"stroke", style:"bian"} },

    { key:"nong", char:"浓", cat:"墨", metaphor:"立形之骨",
      def:"浓墨焦墨，用于松棱石角，故尔了然。",
      note:"用墨浓黑而有光，立形之骨。东坡谓'要使其光清而不浮，精湛如小儿目睛'——浓而要黑中见光，非死黑。",
      src:"画语录", srcLine:3459, demo:{kind:"ink", style:"nong"} },

    { key:"dan", char:"淡", cat:"墨", metaphor:"积淡分远近",
      def:"淡墨积至可观处，然后用焦墨浓墨分出远近。",
      note:"淡墨打底、定远近虚实，是后续层层叠加的基。淡处最难，'实处易，虚处难'。",
      src:"画语录", srcLine:3459, demo:{kind:"ink", style:"dan"} },

    { key:"po", char:"破", cat:"墨", metaphor:"鲜而灵",
      def:"以淡墨润浓墨，则晦而钝；以浓墨破淡墨，则鲜而灵，故必先淡后浓者为得，即所谓破墨也。",
      note:"趁纸未干，以一墨破另一墨，浓淡相侵、互渗互融，水痕鲜活——破墨之妙，全在'鲜而灵'三字。",
      src:"画语录", srcLine:3459, demo:{kind:"ink", style:"po"} },

    { key:"po2", char:"泼", cat:"墨", metaphor:"云烟淋漓",
      def:"泼墨云烟，昉于董、巨，极盛于二米，为一家法。",
      note:"大块水墨泼洒而成，淋漓酣畅，写云写烟写雨意。泼而能收，方不臃肿。",
      src:"题《冷月西山独钓图》", srcLine:2292, demo:{kind:"ink", style:"po2"} },

    { key:"ji", char:"积", cat:"墨", metaphor:"层层染之",
      def:"积墨者，以墨水或浓或淡，层层染之。",
      note:"同一处，待干再加，由淡而浓、由疏而密，一遍遍叠上去，叠到十遍二十遍——'黑宾虹'那一团浑厚，正是时间与墨色一层层养出来的，不是一笔的天才。",
      src:"画语录", srcLine:3459, demo:{kind:"ink", style:"ji"} },   // 含"叠加遍数"微动画

    { key:"jiao", char:"焦", cat:"墨", metaphor:"干裂秋风",
      def:"施以破墨积墨泼墨，犹有未足，则以焦墨补其精神。",
      note:"焦墨极干极浓，干笔擦写，'干裂秋风，润含春雨'。一画将成，以焦墨补其精神、提其骨。",
      src:"画语录", srcLine:3459, demo:{kind:"ink", style:"jiao"} },

    { key:"su", char:"宿", cat:"墨", metaphor:"黑而有彩",
      def:"善用宿墨者，赋色亦古艳。",
      note:"隔宿研存之墨，渣滓渐沉、边缘渗渍，落纸黑而有'宝光'，黑里见彩。宾翁晚岁用之最熟，是其黑密厚重的关捩。",
      src:"年谱（论孟丽堂宿墨）", srcLine:2270, demo:{kind:"ink", style:"su"} }
  ],

  // 金石根：五笔半边的引子（黄宾虹先是金石家，用刻印写篆之笔去画山）
  jinshi: {
    text: "黄宾虹先是金石家，后是画家。他藏古玺汉印逾千、毕生治篆籀文字之学——那一根'如锥画沙、如折钗股'的线，正是从青铜与古印里写出来的。所谓'金石气'，是用刻字写篆的笔去画山。",
    imgs: [
      { src:"assets/thumbs/t_311_古籀篇.jpg", cap:"《古籀篇》· 文字之学" },
      { src:"assets/thumbs/t_291_东池印集.jpg", cap:"《东池印集》· 治印" },
      { src:"assets/thumbs/t_279_滨虹草堂藏古玺印铭并叙.jpg", cap:"滨虹草堂藏古玺印" }
    ]
  },

  // 每字一张真迹缩图：仅作"此法多见于此类作品"的指认，不放大、不分层
  samples: {
    ping:"assets/thumbs/t_021_山水图.jpg",
    yuan:"assets/thumbs/t_162_碧峰禅师山水图.jpg",
    liu:"assets/thumbs/t_050_嘉陵山水图.jpg",
    zhong:"assets/thumbs/t_250_苍松图.jpg",
    bian:"assets/thumbs/t_206_跋黄宾虹手迹画稿十二帧.jpg",
    nong:"assets/thumbs/t_198_晚晴山房图.jpg",
    dan:"assets/thumbs/t_118_蜀游山水册.jpg",
    po:"assets/thumbs/t_134_蜀游图.jpg",
    po2:"assets/thumbs/t_146_秋山烟树图.jpg",
    ji:"assets/thumbs/t_242_临安山色图.jpg",
    jiao:"assets/thumbs/t_198_晚晴山房图.jpg",
    su:"assets/thumbs/t_242_临安山色图.jpg"
  },

  // 进二·读画：白宾虹 → 黑宾虹 三联消长。点一个笔墨字，看它在三阶里"无→初现→盛"。
  // 诚实：三联为不同年份真迹并置；presence 为据画理的概述消长，非逐笔考据。
  evolution: {
    honest: "三联为不同年份真迹并置；下方笔墨消长为据画理的概述，非逐笔考据。",
    levelName: ["未用","初现","大盛"],   // 0 1 2
    stages: [
      { key:"bai", label:"白宾虹", sub:"早岁 · 疏淡清逸", work:"assets/works/仿倪云林图册.jpg",
        note:"师古人、宗倪黄，以笔为主，墨色清简、留白疏朗——人称'白宾虹'。" },
      { key:"shu", label:"入蜀 · 青城为枢", sub:"1933 · 六十九岁 · 蜀游", work:"assets/works/蜀游图.webp",
        note:"青城坐雨、嘉陵夜行，月移墙壁。“我从何处得粉本？雨淋墙头月移壁。”自此墨由淡转黑，积墨、宿墨、破墨大盛。",
        noteSrc:"黄宾虹《题画诗》" },   // huangbinhong_simplified.txt L1911
      { key:"hei", label:"黑宾虹", sub:"晚岁 · 浑厚华滋", work:"assets/works/晚晴山房图.jpg",
        note:"积墨十遍二十遍、焦墨醒提、宿墨生彩——黑密厚重，浑厚华滋。变的是墨，未变的是笔。" }
    ],
    // 每字三阶程度：[白, 转, 黑]  0未用 / 1初现 / 2大盛
    presence: {
      ping:[2,2,2], yuan:[2,2,2], liu:[2,2,2], zhong:[1,2,2], bian:[2,2,2],   // 笔贯穿一生
      nong:[1,2,2], dan:[2,1,1], po:[1,2,2], po2:[0,1,2], ji:[0,1,2], jiao:[0,1,2], su:[0,1,2]  // 墨由淡转黑
    }
  }
};
