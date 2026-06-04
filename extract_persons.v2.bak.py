"""
黄宾虹年谱 · 人物与社会关系抽取 v2 (复核版)
修复:
  1. 大幅补全 SEED_ALIASES（从遗漏诊断中补 80+ 真实人物）
  2. 修复 classify_interaction 的窗口 bug
  3. 扩充互动关键词列表
  4. 强化 jieba 误识别过滤
  5. 加入二阶分类：对"其他"再次尝试更宽松规则
输出: alias_map.json  hbh_persons.json  hbh_interactions.json
"""

import json
import re
from collections import defaultdict, Counter
from pathlib import Path

import jieba
import jieba.posseg as pseg

# ───────────────────────────────────────────────────────────
# 0. 路径
# ───────────────────────────────────────────────────────────
BASE          = Path(r"D:\Desktop\VAST CHALLENGE")
EVENTS_JSON   = BASE / "hbh_events_raw.json"
ALIAS_MAP_OUT = BASE / "alias_map.json"
PERSONS_OUT   = BASE / "hbh_persons.json"
INTER_OUT     = BASE / "hbh_interactions.json"

# ───────────────────────────────────────────────────────────
# 1. 预置别名表（扩充版）
#    每个条目: 标准名 → [别名列表]
# ───────────────────────────────────────────────────────────
SEED_ALIASES: dict[str, list[str]] = {
    # ──── 黄宾虹本人 ────
    "黄宾虹": [
        "黄质", "朴存", "予向", "虹庐", "宾虹", "滨虹", "濱虹", "賓虹",
        "片石", "民恐", "千慮", "千慮", "冰虹", "宾鸿", "黄宾鸿",
        "宾老", "黄先生", "宾翁", "黄老", "黄朴存", "予老",
    ],
    # ──── 家庭 ────
    "黄鞠如": ["鞠如", "黄定华"],
    "朱碧琴": ["碧琴"],
    "宋若婴": [],         # 黄夫人
    "黄映宇": ["映宇"],
    "黄映发": ["映发"],
    "黄映宝": ["映宝"],
    "黄懋赓": ["二弟赓", "黄赓", "元昌", "仲方", "仲芳"],
    "黄懋贡": ["三弟贡", "黄贡", "元清", "廉叔"],
    "黄懋赞": ["四弟赞", "黄赞", "元秀", "晋新"],

    # ──── 艺术圈 · 海派/京派 ────
    "吴昌硕": ["昌硕", "苦铁", "老缶", "缶翁", "缶道人", "仓硕", "仓石",
               "俊卿", "吳昌碩", "吴俊卿"],
    "齐白石": ["白石", "白石老人", "齐璜", "濒生", "白石翁", "齊白石"],
    "王一亭": ["一亭", "王震", "白龙山人"],
    "张大千": ["张爰", "大千居士", "季爰", "張大千"],   # 不收"大千"避免歧义
    "张善孖": ["善孖", "善子", "虎痴", "张善子"],
    "吴湖帆": ["倩庵", "吳湖帆", "吴万", "倩盦"],
    "潘天寿": ["大颐", "阿寿", "潘天壽", "潘天授", "天寿", "天授"],
    "傅雷":   ["怒安", "傅怒安"],
    "徐悲鸿": ["悲鸿", "徐寿康", "徐悲鴻"],
    "林风眠": ["凤鸣", "林鳳眠"],
    "谢稚柳": ["稚柳"],
    "唐云":   ["侠尘"],
    "李可染": ["可染"],
    "赵朴初": ["朴初"],
    "陆丹林": ["丹林"],
    "余绍宋": ["越园", "余紹宋"],
    "张宗祥": ["阆声", "張宗祥", "冷僧"],
    "钟毓龙": ["毓龙"],
    "吴一峰": ["一峰"],
    "陈半丁": ["半丁", "陈年"],
    "金城":   ["拱北", "巩北", "金北楼"],
    "陈师曾": ["衡恪", "槐堂", "朽道人"],
    "汪亚尘": ["亚尘", "亚青"],
    "刘海粟": ["海粟"],
    "高剑父": ["剑父", "高仑"],
    "高奇峰": ["奇峰"],
    "陈树人": ["树人"],   # 注意鲁迅本名也是周树人，已收为别名 "周树人"
    "俞剑华": ["剑华", "俞锷"],
    "贺天健": ["天健"],
    "郑午昌": ["午昌"],
    "张聿光": ["聿光"],
    "钱瘦铁": ["瘦铁", "钱崖", "钱叔崖"],
    "黄蔼农": ["蔼农", "黄蔼"],
    "诸闻韵": ["闻韵"],
    "诸乐三": ["乐三"],
    "马孟容": ["孟容"],
    "马公愚": ["公愚", "马冷峰"],
    "马万里": [],   # 删除"万里"别名：会误命中"万里之外"等普通词
    "马企周": ["企周"],
    # 第二批补全 - 真实人物（从全文遗漏扫描中发现）
    "谢公展": ["公展"],
    "商笙伯": ["商笙"],
    "吴衡之": ["吴衡"],
    "汪采白": ["采白"],
    "吴杏芬": [],
    "姜丹书": [],
    "张书旗": [],
    "鄢克昌": [],
    "周肇祥": [],
    "汪仲山": [],
    "刘作筹": [],
    "陈刚叔": [],
    "赖少其": [],
    "邓尔雅": [],
    "金松岑": [],
    "黄冰清": [],   # 黄宾虹门生
    "陶明霞": [],
    "虞澹涵": [],
    "汪旭云": [],
    "陈缘督": [],
    "白坚甫": [],
    "刘穗九": [],
    "丁衍镛": [],
    "邵元冲": [],
    "邵翼如": [],
    "程瑶笙": [],
    "潘兰史": [],
    "贺鸣秋": [],
    "王济远": ["济远"],
    "王师子": ["师子"],
    "王陶民": ["陶民"],
    "王远勃": ["远勃"],
    "丁悚":   ["丁悚"],
    "杨清磬": ["清磬"],
    "李秋君": ["秋君"],
    "李祖韩": ["祖韩"],
    "陈小蝶": ["小蝶", "陈定山"],
    "楼辛壶": ["辛壶", "楼邨"],
    "熊松泉": ["松泉"],
    "孙雪泥": ["雪泥"],
    "经亨颐": ["亨颐"],
    "于非闇": ["非闇", "于照"],
    "汪声远": ["声远"],
    "钱化佛": ["化佛"],
    "朱屺瞻": ["屺瞻", "起斋"],
    "吴青霞": ["青霞"],
    "倪贻德": ["贻德"],
    "汪英宾": ["英宾"],
    "吴待秋": ["待秋"],
    "符铁年": ["铁年"],
    "冯超然": ["超然", "冯迥"],
    "胡佩衡": ["佩衡"],
    "张红薇": ["红薇"],
    "江小鹣": ["小鹣"],
    "汪慎生": ["慎生"],
    "张辰伯": ["辰伯"],
    "方介堪": ["介堪"],
    "谢玉岑": ["玉岑"],
    "郑曼青": ["曼青"],
    "邱代明": ["代明"],
    "姚虞琴": ["虞琴"],
    "曾农髯": ["农髯", "曾熙"],
    "曾熙":   ["农髯"],
    "李毅士": ["毅士"],
    "宣古愚": ["古愚", "宣哲"],
    "狄平子": ["平子", "楚青", "狄葆贤"],
    "李叔同": ["叔同", "弘一"],
    "林散之": ["散之"],
    "王伯敏": [],   # 后世研究者(1924-2013)，仅用全名匹配
    "陈巨来": ["巨来"],
    "唐吉生": ["吉生"],
    "刘景晨": ["景晨"],
    "罗原觉": ["原觉"],
    "罗瘿公": ["瘿公"],
    "胡寄尘": ["寄尘"],
    "俞寄凡": ["寄凡"],
    "黄居素": ["居素"],
    "黄少牧": ["少牧"],
    "黄警吾": ["警吾"],
    "张谷雏": ["谷雏", "张虹"],
    # 蔡守 = 蔡哲夫 (同一人, 字哲夫)
    "蔡守":   ["哲夫", "蔡哲夫"],
    # 胡韫玉 = 胡朴安 (同一人, 字朴安, 号韫玉/朴庵)
    "胡韫玉": ["韫玉", "朴庵", "胡朴安", "朴安"],
    "许征白": ["征白", "徵白", "许徴白"],
    "许承尧": ["承尧", "芚公"],
    "许翰屏": ["翰屏"],
    "高燮":   ["吹万"],
    "陈去病": ["去病", "巢南"],
    "柳亚子": ["亚子", "柳弃疾"],
    "陈中凡": ["中凡"],
    "陈柱":   ["柱尊", "陈柱尊"],  # 归并：陈柱 与 陈柱尊 是同一人
    "汪律本": ["律本", "鞠友"],
    "过旭初": ["旭初"],
    "阎甘园": ["甘园"],
    "易培基": ["培基", "寅村"],
    "林思进": ["思进", "山腴", "林山腴"],

    # ──── 学术 / 出版 ────
    "邓实":   ["铁如", "野残", "野残老人", "风雨楼主", "鄧實",
               "秋枚", "邓秋枚"],
    "黄节":   ["晦闻", "黃節", "黄晦闻"],
    "叶恭绰": ["玉甫", "遐庵", "叶遐庵", "誉虎", "叶誉虎"],
    "马衡":   ["叔平"],
    "朱祖谋": ["古微", "强村", "朱古微"],
    "沈曾植": ["乙盫", "寐叟"],
    "张謇":   ["季直", "張謇"],
    "张元济": ["菊生", "張元濟"],
    "陈三立": ["散原", "伯严", "陳三立"],
    "郑孝胥": ["苏戡", "太夷", "鄭孝胥"],
    "叶楚伧": ["卞叶", "楚伧", "楚傖"],
    "沈尹默": ["君默"],
    "马一浮": ["浮翁", "湛翁"],
    "汪世清": ["世清"],
    "王中秀": ["中秀"],
    "王国维": ["静安", "伯隅", "观堂", "王靜安"],
    "夏承焘": ["承焘", "夏瞿禅", "夏老"],
    "傅增湘": ["沅叔"],
    "李瑞清": ["瑞清", "梅庵"],
    "王云五": ["云五"],
    "王伯沆": ["伯沆"],
    "顾飞":   ["默飞"],
    "朱少屏": ["少屏"],
    "宣哲":   ["古愚"],
    "史德匿": ["史德匿"],
    "陈泽霈": [],
    "张翰飞": [],

    # ──── 政治 / 社会 ────
    "康有为": ["广厦", "南海", "长素", "康南海", "康有為"],
    "梁启超": ["任公", "饮冰", "卓如", "飲冰", "梁任公"],
    "蔡元培": ["孑民", "鹤卿", "蔡孑民"],
    "陈独秀": ["仲甫", "陳獨秀"],
    "鲁迅":   ["周树人", "豫才"],   # 注：与陈树人同名"周树人"，无歧义
    "胡适":   ["适之", "胡适之", "胡適"],
    "黄炎培": ["任之"],
    "汪精卫": ["兆铭", "汪兆銘"],
    "吴铁城": ["铁城"],
    "于右任": ["髯翁", "仁庵"],
    "冯玉祥": ["焕章"],
    "郭沫若": ["鼎堂"],
    "陈叔通": ["叔通"],
    "何香凝": ["香凝"],
    "李济深": ["任潮"],
    "褚民谊": ["民谊"],

    # ──── 师友 / 早期 ────
    "倪逸甫": ["逸甫"],
    "陈春帆": ["春帆"],
    "陈崇光": ["崇光", "陈若木"],
    "陈三立": ["散原"],
    "舒国华": [],
    "汪福熙": ["福熙"],
    "汪孔祁": ["孔祁"],
    "卞孝萱": ["孝萱"],

    # ──── 出版机构（占位，便于过滤） ────
    "荣宝斋": [],
    "商务印书馆": [],
    "神州国光社": [],
    "中华书局": [],
}

# ───────────────────────────────────────────────────────────
# 后世研究者 / 年谱编纂者白名单
# 这些人在年谱中是引用源，不计入"真实互动"
# 但仍允许作为人物条目存在（标注 category=研究源）
# ───────────────────────────────────────────────────────────
SCHOLAR_SOURCES = {
    "王伯敏",   # 1924-2013, 美术史家
    "黄警吾",   # 黄宾虹堂侄, 写《黄宾虹在徽州》
    "汪世清",   # 学者, 写《黄宾虹家世》
    "王中秀",   # 年谱编纂者
    "卞孝萱",   # 1924-2009, 学者
    "石谷风",   # 1919-2019, 画家但主要作回忆
}

# ───────────────────────────────────────────────────────────
# 2. 历史人物 / 古代画家黑名单
# ───────────────────────────────────────────────────────────
HISTORICAL_FIGURES = {
    # 元四家
    "黄公望","倪瓒","吴镇","王蒙","大痴","云林","梅道人","梅花道人",
    # 明清画家
    "石涛","八大山人","石溪","弘仁","渐江","梅壑","梅壑散人",
    "文徵明","唐寅","沈周","仇英","董其昌","沈石田","董玄宰",
    "王石谷","王翚","王原祁","王时敏","王鉴","四王","石田",
    "龚贤","髡残","查士标","程邃","八大","渐师",
    "金农","郑燮","郑板桥","黄慎","李鱓","罗聘","汪士慎",
    "高凤翰","李方膺","边寿民",
    # 宋元
    "米芾","米元章","米南宫","荆浩","关仝","李成","范宽","巨然",
    "马远","夏圭","刘松年","李唐","赵昌","崔白","韩干","阎立本",
    "赵孟頫","赵子昂","李思训","顾恺之","吴道子",
    "徐熙","黄筌","王维","摩诘",
    # 文人
    "陶渊明","李白","杜甫","白居易","欧阳修","王安石","朱熹",
    "韩愈","柳宗元","范仲淹","司马光","张旭","怀素","钟繇",
    "苏东坡","苏轼","东坡","王羲之","颜真卿","柳公权",
    "范石湖","姚惜抱","姚鼐","刘熙载",
    "扬补之","王元章","补之",
    # 神话/虚构
    "黄初平","黄大仙",
    # 称呼/泛指 (jieba 误标)
    "黄氏","黄先生", "老先生","本人","门生","学子",
    "诸君","君等","诸公","诸友","诸子","友人","老兄","老弟",
    "公子","令郎","令爱","令兄","令弟","世兄","老夫子",
    "夫人","老人","女史","女士","先生","老师","主人","门人",
    # jieba 易错切分
    "为李书华","为过之翰","为容庚","为陆丹林","为顾飞","为雁迅",
    "李书华","过之翰",  # 这俩是真人，但要单独处理
    # 引用源
    "汪谱","王谱","按","存考","按语",
    # 时代/朝代
    "宋元","明清","唐宋","历代","当代","民国","清代","明代","唐代","宋代",
    "甲子","乙丑","丙寅","丁卯","戊辰","己巳","庚午","辛未",
    "壬申","癸酉","甲戌","乙亥","丙子","丁丑","戊寅","己卯",
    "庚辰","辛巳","壬午","癸未","甲申","乙酉","丙戌","丁亥",
    "戊子","己丑","庚寅","辛卯","壬辰","癸巳","甲午","乙未",
    "丙申","丁酉","戊戌","己亥","庚子","辛丑","壬寅","癸卯",
    # 普通词被 jieba 误标
    "金石","陈列","丹青","秦汉","唐人","宋人","明人","清人",
    "梅花","松竹","兰草","荷花","菊花","山水","花鸟","人物","白描",
    "桂林","柏林","北京","上海","南京","杭州","广州","苏州",
    "成都","重庆","金陵","建康","虞山","雁荡","阳朔","西湖",
    "黄山","白岳","九华","泰山","峨眉","庐山",
    "尔雅","汉书","史记","左传","春秋",
    "金石","印章","印谱","字画","书画","笔墨","水墨","设色","纸本",
    "古玺印","秦汉印","汉印","唐印",
    "墨宝","白云","友谊","士大夫","寿辰","简章","师范","名瑞麒",
    "国学","学者","老兄","民国","革命",
}

# ───────────────────────────────────────────────────────────
# 3. 互动类型关键词（大幅扩充）
#    顺序很重要：从最具体的类型开始匹配
# ───────────────────────────────────────────────────────────
INTERACTION_KEYWORDS = [
    # 通信 - 最容易识别
    ("通信", [
        "致函", "来函", "寄书", "通信", "函告", "去信", "寄函", "来书",
        "复函", "覆函", "书告", "写信", "函复", "寄信", "通函", "惠函",
        "手书", "书曰", "函云", "索函", "属书", "邮寄", "致书",
        "信曰", "复书", "覆书", "上书", "答书", "去书", "答函", "回函",
        "复信", "回信", "电询", "电告", "致电",
    ]),
    # 师生 - 拜师/受业，关键词明确
    ("师生", [
        "受业", "拜师", "执贽", "门下", "弟子", "学生", "拜于",
        "学画", "问学", "师事", "受教", "从学于", "请益", "请教",
        "门人", "及门", "亲炙", "私淑",
    ]),
    # 来访 - 物理拜访
    ("来访", [
        "来访", "造访", "拜访", "登门", "相访", "来谒", "过访",
        "来见", "来拜", "来晤", "前往访", "往访", "登门拜访",
        "枉过", "来沪访", "枉驾", "枉顾", "来归", "便道访",
        "来索画", "登庐", "登访",
    ]),
    # 同游 - 共同出行
    ("同游", [
        "同游", "偕游", "同行", "同往", "偕往", "结伴", "偕行",
        "携游", "共游", "同至", "偕至", "同赴", "携往", "携之",
        "陪同", "陪游", "相偕", "联袂", "同来", "同去",
        "偕之游", "邀游",
    ]),
    # 题跋鉴赏
    ("题跋鉴赏", [
        "题跋", "题款", "索题", "求题", "题记", "题画", "题字",
        "书题", "为.*?题", "鉴定", "鉴赏", "品题", "审定",
        "题诗", "题端", "为.*?跋", "属题", "嘱题", "命题",
        "题以", "题曰", "题字赠", "鉴定为",
    ]),
    # 合作 - 共同事业
    ("合作", [
        "合编", "共编", "合著", "共著", "同编", "联名", "共同撰",
        "共撰", "参与编", "协力", "合作", "共办", "同办",
        "发起", "创办", "成立", "组织", "组成", "联合",
        "联袂出席", "共同担任", "共同主持",
        "组织.*?画社", "组织.*?画会", "组织.*?学社",
        "聘.*?为", "聘任", "委为", "推为", "公举", "推举",
        "出任", "担任", "任院长", "任校长", "任教授",
    ]),
    # 引荐
    ("引荐", [
        "介绍", "推荐", "引荐", "托介", "托人", "代为",
        "代请", "属代", "嘱代", "属介",
    ]),
    # 收藏交易
    ("收藏交易", [
        "购得", "收购", "购藏", "得藏", "转让", "割爱",
        "卖与", "售与", "以.*?售", "购入", "易得", "易藏",
        "得其", "购入", "代购", "代鬻", "鬻于",
    ]),
    # 作画赠予 - 关键词大幅扩充
    ("作画赠予", [
        "赠画", "作画赠", "画赠", "以画赠", "赠以画", "画以赠",
        "馈赠", "赐画", "为.*?作", "为.*?写", "为.*?画",
        "为.*?绘", "为.*?书", "为.*?篆", "题赠", "书赠",
        "篆赠", "印赠", "应.*?属作", "应.*?嘱作", "应.*?之属",
        "应.*?求作", "应.*?之求", "属为", "嘱为",
        "作.*?赠", "作.*?寄", "作.*?以贻", "作.*?贻",
        "画.*?寄", "画.*?贻", "写.*?赠", "写.*?寄",
        "为.*?所作", "应.*?属", "应.*?嘱", "应.*?之嘱",
        "为.*?摹", "为.*?临",
    ]),
    # 见面会谈
    ("见面会谈", [
        "晤谈", "相谈", "相见", "会见", "晤面", "会谈", "谈及",
        "面谈", "叙谈", "叙旧", "欢聚", "见面", "聚会",
        "宴", "晏", "饮于", "饮酒", "聚饮", "雅集",
        "宴集", "雅集", "公宴", "饯", "茗谈",
        "假座", "席间", "席上",
    ]),
]

def classify_interaction(full_text: str, person: str, alias_list: list) -> str:
    """
    在全文中搜索关键词。person 周围 ±100 字优先。
    """
    # 候选呈现位置
    names_to_try = [person] + [a for a in alias_list if a]
    positions = []
    for n in names_to_try:
        if not n:
            continue
        i = 0
        while True:
            p = full_text.find(n, i)
            if p < 0:
                break
            positions.append((p, n))
            i = p + len(n)

    # 取最近的窗口
    if positions:
        # 在每个出现位置周围 ±100 字内找关键词
        windows = []
        for pos, name in positions:
            s = max(0, pos - 100)
            e = min(len(full_text), pos + len(name) + 100)
            windows.append(full_text[s:e])
        ctx = " ".join(windows)
    else:
        ctx = full_text  # 退而求其次：全文

    for itype, keywords in INTERACTION_KEYWORDS:
        for kw in keywords:
            if "." in kw or "*" in kw or "?" in kw:
                if re.search(kw, ctx):
                    return itype
            else:
                if kw in ctx:
                    return itype

    # 二阶宽松规则 - 按可信度排序
    # 委员/董事/教授/出席名单 → 合作
    if any(c in ctx for c in ["委员", "董事", "教授", "院长", "校长",
                               "主席", "理事", "评议", "顾问", "社长",
                               "主任", "聘为", "应聘", "应邀", "受聘",
                               "推为", "公举", "选为", "当选", "出席"]):
        return "合作"
    # 招饮/约饮/宴 → 见面会谈
    if any(c in ctx for c in ["招饮", "约饮", "饮于", "宴", "饯",
                               "雅集", "聚饮", "集会", "茗"]):
        return "见面会谈"
    # 通信书函
    if any(c in ctx for c in ["书", "函"]) and person in ctx:
        return "通信"
    # 赠送 + 物品
    if any(c in ctx for c in ["赠", "贻", "寄"]) and any(c in ctx for c in ["画", "书", "印", "联", "册", "扇", "卷"]):
        return "作画赠予"
    # 见面相关
    if any(c in ctx for c in ["晤", "见", "访", "聚", "宴", "宿"]):
        return "见面会谈"
    # 题跋
    if "题" in ctx and any(c in ctx for c in ["画", "书", "册", "卷", "扇"]):
        return "题跋鉴赏"
    # 同游
    if any(c in ctx for c in ["游", "登", "至", "赴", "归"]) and any(c in ctx for c in ["同", "偕", "陪", "携"]):
        return "同游"
    # 作画
    if any(c in ctx for c in ["作", "写", "画"]) and any(c in ctx for c in ["山水", "花鸟", "册", "卷", "扇", "图"]):
        return "作画赠予"
    return "其他"


# ───────────────────────────────────────────────────────────
# 4. 反向查找表
# ───────────────────────────────────────────────────────────
def build_reverse_map(alias_map: dict) -> dict:
    reverse = {}
    for std, aliases in alias_map.items():
        reverse[std] = std
        for a in aliases:
            if a:
                reverse[a] = std
    return reverse


# ───────────────────────────────────────────────────────────
# 5. 自动检测字号 (严格化版)
# ───────────────────────────────────────────────────────────
BIRTH_DEATH_RE = re.compile(
    r"([一-鿿]{2,4})（(\d{4})[—–\-~～至到~](\d{4})）"
)

_NAME_BAD_PREFIX = ("位", "即", "宧", "叟", "姓", "名", "长子", "长女",
                    "次子", "次女", "三子", "三女", "四子", "四女",
                    "五子", "五女", "六子", "六女",
                    "是", "叫", "为", "从", "随", "邀")
_NAME_BAD_CHARS = "在到和别此为段阶画作年回是叫位即宧叟姓"

def _is_valid_detected_name(name: str) -> bool:
    if len(name) < 2 or len(name) > 4:
        return False
    if any(c.isdigit() for c in name):
        return False
    if any(c in name for c in _NAME_BAD_CHARS):
        return False
    if any(name.startswith(p) for p in _NAME_BAD_PREFIX):
        return False
    return True

def auto_detect_birth_death(texts: list[str]) -> dict:
    """只接受严格格式: 名字（1850-1950），其中名字 2-4 字"""
    res = {}
    for text in texts:
        for m in BIRTH_DEATH_RE.finditer(text):
            name, b, d = m.group(1), int(m.group(2)), int(m.group(3))
            if not _is_valid_detected_name(name):
                continue
            if 1750 <= b <= 1950 and b < d < b + 110:
                if name not in res:
                    res[name] = (b, d)
    return res


# ───────────────────────────────────────────────────────────
# 6. jieba 初始化 + 启发式过滤
# ───────────────────────────────────────────────────────────
def init_jieba(alias_map: dict):
    for std, aliases in alias_map.items():
        jieba.add_word(std, freq=500, tag="nr")
        for a in aliases:
            if a:
                jieba.add_word(a, freq=300, tag="nr")
    # 显式排除一些 jieba 误识别
    for bad in ["二弟赓", "三弟贡", "四弟赞", "五子映宇", "四子映发",
                "汪谱", "王谱", "存考", "宾老", "黄先生", "宾翁",
                "为李书华", "为过之翰", "为容庚", "为陆丹林", "为顾飞",
                "为雁迅", "老夫子", "黄氏", "三井高坚"]:
        try:
            jieba.del_word(bad)
        except Exception:
            pass


def looks_like_real_person(word: str, known: set) -> bool:
    """启发式判断词是否可能是真实近现代人物"""
    if word in known:
        return True
    if len(word) < 2 or len(word) > 4:
        return False
    if word in HISTORICAL_FIGURES:
        return False
    bad_chars = "之者也而已矣此其于以为是不无有兮何若如则又或者然乎所"
    if len(word) == 2 and any(c in word for c in bad_chars):
        return False
    bad_suffix = ("公", "翁", "氏", "兄", "弟", "君", "老", "丈",
                  "卿", "侯", "伯", "甫", "夫", "妻", "妹",
                  "侄", "媳", "甥", "孙", "辈", "民", "众", "人")
    if word.endswith(bad_suffix) and len(word) == 2:
        return False
    bad_prefix = ("二", "三", "四", "五", "六", "七", "八", "九", "十",
                  "大", "小", "老", "新", "古", "今", "前", "后",
                  "诸", "群", "众", "为", "与", "和", "及", "等",
                  "全", "此", "彼", "本", "其", "回")
    if word.startswith(bad_prefix) and len(word) == 2:
        return False
    if any(c.isdigit() for c in word):
        return False
    return True


# ───────────────────────────────────────────────────────────
# 7. 在文本中搜索已知人物
# ───────────────────────────────────────────────────────────
def find_known_persons(text: str, alias_map: dict, reverse_map: dict) -> list:
    """
    返回出现的标准名（去重）。
    搜索时按长度降序，避免被短别名提前消费。
    """
    found = set()
    sorted_aliases = sorted(reverse_map.keys(), key=lambda x: -len(x))
    for alias in sorted_aliases:
        std = reverse_map[alias]
        if std == "黄宾虹":
            continue
        if alias in text:
            found.add(std)
    return list(found)


# ───────────────────────────────────────────────────────────
# 8. 上下文截取
# ───────────────────────────────────────────────────────────
def get_context_snippet(text: str, person: str, alias_list: list,
                         window: int = 80) -> str:
    """取以 person 或其别名为中心的上下文片段"""
    pos = -1
    found_name = None
    if person in text:
        pos = text.find(person)
        found_name = person
    else:
        for a in alias_list:
            if a and a in text:
                pos = text.find(a)
                found_name = a
                break
    if pos < 0:
        return text[:200].strip()
    start = max(0, pos - window)
    end   = min(len(text), pos + len(found_name) + window)
    return text[start:end].strip()


# ───────────────────────────────────────────────────────────
# 9. 历史引用过滤
# ───────────────────────────────────────────────────────────
HIST_VERBS = re.compile(
    r"(倣|仿|临|摹|师法|宗法|参法|继承|笔意|画意|笔法|风格|流派|宗|学)"
)
HBH_VERBS = re.compile(
    r"(致|寄|赠|与|和|及|访|来|晤|见|聚|宴|题|属|嘱|序|跋|为|偕|同|共)"
)

def is_real_interaction(full_text: str, person: str, alias_list: list,
                        birth_death: dict) -> bool:
    if person in HISTORICAL_FIGURES:
        return False
    # 后世研究者/年谱编纂者不计入互动
    if person in SCHOLAR_SOURCES:
        return False
    if person in birth_death:
        b, d = birth_death[person]
        if d < 1850 or b > 1970:
            return False
    ctx = get_context_snippet(full_text, person, alias_list, 50)
    # 若局部上下文全是历史风格词，且没有黄宾虹动词，认为是引用
    has_hist = bool(HIST_VERBS.search(ctx))
    has_real = bool(HBH_VERBS.search(ctx))
    if has_hist and not has_real:
        return False
    return True


# ───────────────────────────────────────────────────────────
# 10. 人物类别
# ───────────────────────────────────────────────────────────
CATEGORY_MAP = {
    "艺术": {
        # 老一辈/海派
        "吴昌硕","王一亭","齐白石","曾农髯","曾熙","李瑞清","金城",
        "陈师曾","狄平子","姚虞琴",
        # 黄宾虹同辈艺术家
        "张大千","张善孖","吴湖帆","潘天寿","谢稚柳","唐云","李可染",
        "徐悲鸿","林风眠","余绍宋","张宗祥","陈半丁","汪亚尘","刘海粟",
        "高剑父","高奇峰","陈树人","俞剑华","贺天健","郑午昌","张聿光",
        "钱瘦铁","黄蔼农","诸闻韵","诸乐三","马孟容","马公愚","马万里",
        "马企周","王济远","王师子","王陶民","王远勃","丁悚","杨清磬",
        "李秋君","李祖韩","陈小蝶","楼辛壶","熊松泉","孙雪泥","经亨颐",
        "于非闇","汪声远","钱化佛","朱屺瞻","吴青霞","倪贻德","汪英宾",
        "吴待秋","符铁年","冯超然","胡佩衡","张红薇","江小鹣","汪慎生",
        "张辰伯","方介堪","谢玉岑","郑曼青","邱代明","李毅士","宣古愚",
        "李叔同","林散之","陈巨来","唐吉生","刘景晨","罗原觉","罗瘿公",
        "陆丹林","黄居素","黄少牧","张谷雏","蔡哲夫","蔡守","赵朴初",
        "陈泽霈","张翰飞","张弦","王伯沆","俞寄凡","汪律本",
        "宣哲","李毅士","许士骐","陶冷月","傅熊湘","施翀鹏","龚熙台",
        "邓只淳","高天梅","王礼锡","张毅崛","潘达微","连声海",
        "黄警吾",  # 当作艺术晚辈
        # 补全：之前归为"其他"的艺术家
        "吴一峰","苏干英","黄般若","李尹桑","汤临泽","鲍君白","赵少昂",
        "吴咏香","冯建吴","沈泊尘","朱尊一","黄牧甫","阮性山","关春草",
        "黄咏雩","河井仙郎","竹内栖凤","古公愚","吴淑娟","丁甘仁",
        "费龙丁","钟毓龙","黄葆戉","郑文焯","费念慈","章劲宇",
        "朱金楼","张目寒","方节盫","顾佛影","王病山",
        # 第二批新增艺术家
        "谢公展","商笙伯","汪采白","吴杏芬","张书旗","鄢克昌",
        "周肇祥","汪仲山","陈刚叔","赖少其","邓尔雅","黄冰清",
        "陶明霞","虞澹涵","汪旭云","陈缘督","白坚甫",
        "丁衍镛","程瑶笙","贺鸣秋","刘作筹",
    },
    "学术": {
        "邓实","黄节","王国维","叶恭绰","马衡","朱祖谋","沈曾植",
        "张元济","傅雷","郑振铎","马一浮","沈尹默","夏承焘","傅增湘",
        "王云五","顾飞","朱少屏","胡韫玉","许征白","许承尧",
        "高燮","陈去病","柳亚子","陈中凡","陈柱","过旭初","阎甘园",
        "易培基","林思进","胡寄尘","史德匿","王中秀","汪世清","王伯敏",
        "卞孝萱","石谷风",
        # 补全：之前归"其他"的学者
        "徐积余","王秋湄","潘飞声","易大厂","顾颉刚","杨铁夫","路大荒",
        "刘既明","蒲伯英","黄萍荪","唐蔚芝","谢国桢","李伯行","王无生",
        "庞石帚","张伯英","储南强","姜可生","陈邦怀","张默君",
        "黄萍荪","陈泽霈","张翰飞","张弦","俞寄凡","汪律本",
        "雷铁崖","吴巽沂","许家栻","周叔迦","廖仲宣","罗伯希","张秉三",
        "今关天彭","严西凤","龚道耕","李宣龚","梁叔子","唐蔚芝","张祥凝",
        "李德膏","孙毓筠","徐丹甫",
        # 第二批新增学者
        "姜丹书","金松岑","吴衡之","刘穗九","邵元冲","邵翼如",
        "潘兰史","林志钧",
    },
    "政治": {
        "康有为","梁启超","蔡元培","陈独秀","鲁迅","胡适","汪精卫",
        "于右任","冯玉祥","何香凝","李济深","黄炎培","郭沫若",
        "陈叔通","郑孝胥","张謇","褚民谊","叶楚伧","陈铭枢",
        "吴铁城",
    },
    "家庭": {
        "黄鞠如","朱碧琴","宋若婴",
        "黄映宇","黄映发","黄映宝",
        "黄懋赓","黄懋贡","黄懋赞",
    },
    "出版": {
        "商务印书馆","神州国光社","中华书局","荣宝斋",
        "陈三立",  # 早期出版圈
    },
    "师友": {
        "倪逸甫","陈春帆","陈崇光","舒国华","汪福熙","汪孔祁",
    },
}

def infer_category(std: str) -> str:
    if std in SCHOLAR_SOURCES:
        return "研究源"
    for cat, names in CATEGORY_MAP.items():
        if std in names:
            return cat
    return "其他"


# ───────────────────────────────────────────────────────────
# 主流程
# ───────────────────────────────────────────────────────────
def main():
    print("加载事件数据...")
    events: list[dict] = json.loads(EVENTS_JSON.read_text(encoding="utf-8"))
    print(f"  {len(events)} 条事件")

    # ── Step A: 自动检测生卒年 (用于过滤老人物) ──
    print("Step A: 自动检测生卒年...")
    all_texts = [e["raw_text"] for e in events]
    birth_death = auto_detect_birth_death(all_texts)
    print(f"  检测到 {len(birth_death)} 个生卒年注记")

    # ── Step B: 别名表 ──
    print("Step B: 加载预置别名表...")
    alias_map = {k: list(v) for k, v in SEED_ALIASES.items()}

    # 把研究源加入别名表（无别名，仅供匹配）
    for s in SCHOLAR_SOURCES:
        if s not in alias_map:
            alias_map[s] = []

    # 将生卒年里 1850-1950 的人物作为候选标准名（若未在表中、且名字 ≥ 3 字）
    # 限制 ≥ 3 字: 避免 2 字误命中
    for name, (b, d) in birth_death.items():
        if name in ["黄宾虹", "黄质"]: continue
        if len(name) < 3: continue
        if 1850 <= b <= 1930:
            already_known = False
            for std, aliases in alias_map.items():
                if name == std or name in aliases:
                    already_known = True
                    break
            if not already_known and name not in HISTORICAL_FIGURES:
                alias_map[name] = []

    # 写 alias_map
    ALIAS_MAP_OUT.write_text(
        json.dumps(alias_map, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  alias_map.json: {len(alias_map)} 个标准人名")

    reverse_map = build_reverse_map(alias_map)
    print(f"  反向映射: {len(reverse_map)} 个别名指向标准名")

    # ── Step C: jieba 初始化 ──
    print("Step C: 初始化 jieba...")
    init_jieba(alias_map)
    known_set = set(reverse_map.keys())

    # ── Step D: 遍历事件，抽取人物 + 互动 ──
    print("Step D: 遍历事件抽取人物与互动...")

    person_stats: dict[str, dict] = defaultdict(lambda: {
        "years": [], "pages": [], "snippets": [], "last_text": ""
    })
    interactions: list[dict] = []

    for evt in events:
        if evt.get("type") == "year_header":
            continue
        year  = evt.get("year", 0)
        text  = evt.get("raw_text", "")
        evid  = evt.get("id", "")
        page  = evt.get("source_page", 0)
        date  = evt.get("date", str(year))

        # 1) 找已知人物（含别名）
        known = find_known_persons(text, alias_map, reverse_map)

        # 2) jieba nr 候选 补充：必须通过 looks_like_real_person 过滤
        for word, flag in pseg.cut(text):
            if flag == "nr" and 2 <= len(word) <= 4:
                if word in reverse_map:
                    std = reverse_map[word]
                    if std != "黄宾虹" and std not in known:
                        known.append(std)
                # 不再自动新增人物——避免污染。补全完全靠 SEED_ALIASES

        for std in known:
            aliases = alias_map.get(std, [])
            ps = person_stats[std]
            ps["years"].append(year)
            ps["pages"].append(page)
            snippet = get_context_snippet(text, std, aliases, 80)
            if snippet and snippet not in ps["snippets"]:
                ps["snippets"].append(snippet)
            ps["last_text"] = text

            if is_real_interaction(text, std, aliases, birth_death):
                itype = classify_interaction(text, std, aliases)
                interactions.append({
                    "event_id": evid,
                    "year": year,
                    "date": date,
                    "person": std,
                    "interaction_type": itype,
                    "raw_text": text[:300],
                })

    # ── Step E: 人物档案 ──
    print("Step E: 构建人物档案...")
    persons = []
    pid = 0
    for std, ps in sorted(person_stats.items(), key=lambda x: -len(x[1]["years"])):
        if not ps["years"]: continue
        pid += 1
        years_sorted = sorted(set(ps["years"]))
        first_yr = years_sorted[0]
        last_yr  = years_sorted[-1]
        span     = last_yr - first_yr
        total    = len(ps["years"])

        long_comp = span >= 40 and total >= 5

        # 断裂点
        break_note = None
        year_counter = Counter(ps["years"])
        if len(years_sorted) >= 3:
            peak_years = [y for y, c in year_counter.items() if c >= 3]
            if peak_years:
                peak_end = max(peak_years)
                if peak_end < last_yr - 5 and last_yr < 1953:
                    break_note = f"密集出现至{peak_end}年后明显减少，末次提及{last_yr}年，或因离别/逝世"
                elif last_yr < 1955 and total >= 5:
                    ctx = ps["last_text"][:120]
                    if any(kw in ctx for kw in ["逝世", "病故", "卒", "殁", "辞世", "去世"]):
                        break_note = f"末次提及{last_yr}年，文中有逝世相关表述"

        # 跨圈层
        cross_circle = False
        snippets_joined = " ".join(ps["snippets"][:10])
        art_kws = {"画", "书法", "展览", "创作", "题跋"}
        pol_kws = {"政治", "会议", "国民", "革命", "民主", "政府", "议员", "国会"}
        if any(k in snippets_joined for k in art_kws) and \
           any(k in snippets_joined for k in pol_kws):
            cross_circle = True

        rec: dict = {
            "person_id":     f"p{pid:03d}",
            "standard_name": std,
            "category":      infer_category(std),
            "first_mention": first_yr,
            "last_mention":  last_yr,
            "total_mentions": total,
            "bio_snippets":  ps["snippets"][:5],
        }
        if long_comp:    rec["long_companion"] = True
        if break_note:   rec["note"] = break_note
        if cross_circle: rec["cross_circle"] = True
        if std in SCHOLAR_SOURCES:
            rec["is_scholar_source"] = True
            # 移除"长情"标记——研究源 first_mention 不是真实结识
            rec.pop("long_companion", None)
        persons.append(rec)

    PERSONS_OUT.write_text(
        json.dumps(persons, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  hbh_persons.json: {len(persons)} 个人物")

    # ── Step F: 互动 ──
    INTER_OUT.write_text(
        json.dumps(interactions, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  hbh_interactions.json: {len(interactions)} 条互动")

    # ── Step G: 自检报告 ──
    report_lines = []
    def rp(*a): report_lines.append(" ".join(str(x) for x in a))

    rp("=" * 60)
    rp("自检报告 (v2)")
    rp("=" * 60)
    rp(f"事件总数:    {len(events)}")
    rp(f"人物总数:    {len(persons)}")
    rp(f"互动总数:    {len(interactions)}")
    rp(f"标准人名:    {len(alias_map)}")
    rp("")

    rp("── 人物 TOP 30 (按提及次数) ──")
    for p in persons[:30]:
        tag = ""
        if p.get("long_companion"): tag += "[长情]"
        if p.get("cross_circle"):   tag += "[跨圈]"
        if p.get("note"):           tag += "[断裂?]"
        rp(f"  {p['standard_name']:8s} {p['total_mentions']:4d}次  "
           f"{p['first_mention']}-{p['last_mention']}  {p['category']:6s} {tag}")

    rp("")
    rp("── 长情节点 (跨度 ≥40 年, ≥5 次) ──")
    long_list = [p for p in persons if p.get("long_companion")]
    rp(f"  共 {len(long_list)} 人")
    for p in long_list:
        rp(f"  {p['standard_name']:8s}  {p['first_mention']}-{p['last_mention']}  "
           f"{p['last_mention']-p['first_mention']}年  {p['total_mentions']}次  {p['category']}")

    rp("")
    rp("── 跨圈层人物 ──")
    cross = [p for p in persons if p.get("cross_circle")]
    rp(f"  共 {len(cross)} 人")
    for p in cross:
        rp(f"  {p['standard_name']:8s} {p['total_mentions']:4d}次  {p['category']}")

    rp("")
    rp("── 互动类型分布 ──")
    itype_counter = Counter(i["interaction_type"] for i in interactions)
    for itype, cnt in itype_counter.most_common():
        pct = cnt * 100 / len(interactions)
        rp(f"  {itype:10s}: {cnt:5d}  ({pct:.1f}%)")

    rp("")
    rp("── 类别分布 ──")
    cat_counter = Counter(p["category"] for p in persons)
    for cat, cnt in cat_counter.most_common():
        rp(f"  {cat:6s}: {cnt}")

    rp("")
    rp("── 断裂点警示 (TOP 15) ──")
    breaks = [p for p in persons if p.get("note")]
    rp(f"  共 {len(breaks)} 人")
    for p in breaks[:15]:
        rp(f"  {p['standard_name']:8s} {p['total_mentions']:3d}次  {p['note']}")

    report_path = BASE / "extract_report_v2.txt"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n自检报告写入 {report_path}")


if __name__ == "__main__":
    main()
