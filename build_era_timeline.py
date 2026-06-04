# -*- coding: utf-8 -*-
"""
生成 era_timeline.json
覆盖黄宾虹生卒 1865-1955 年的中国近代史大事
来源：人教版历史 / 学术通识史料，不依赖年谱内容
"""
import json, os
os.chdir(r"D:\Desktop\VAST CHALLENGE")

ERA_EVENTS = [
    # ── 晚清（1865-1911）──────────────────────────────────────────
    {"date":"1865",      "event":"太平天国运动结束（1864年7月天京失守，余部1865年覆灭）",     "category":"战争",    "importance":1},
    {"date":"1868",      "event":"洋务运动进入全面展开阶段（江南制造局、轮船招商局等）",     "category":"社会",    "importance":2},
    {"date":"1872",      "event":"第一批留美幼童派遣（容闳主持，中国近代留学开端）",          "category":"文化",    "importance":2},
    {"date":"1875",      "event":"光绪帝即位，慈禧太后二度垂帘听政",                         "category":"政治",    "importance":2},
    {"date":"1882",      "event":"壬午兵变（朝鲜），清廷强化对朝鲜宗藩控制",                  "category":"政治",    "importance":3},
    {"date":"1884",      "event":"中法战争（1883-1885），清廷被迫签《中法新约》",             "category":"战争",    "importance":1},
    {"date":"1888",      "event":"颐和园重建竣工，挪用海军经费引发政争",                      "category":"政治",    "importance":3},
    {"date":"1894-07-25","event":"甲午战争爆发（丰岛海战），中日正式宣战",                    "category":"战争",    "importance":1},
    {"date":"1895-04-17","event":"马关条约签订，割台湾、辽东，赔款两亿两",                    "category":"政治",    "importance":1},
    {"date":"1895",      "event":"公车上书（康有为主导），维新变法思潮兴起",                   "category":"政治",    "importance":1},
    {"date":"1898-06-11","event":"戊戌变法开始（百日维新），光绪帝颁布系列新政诏令",          "category":"政治",    "importance":1},
    {"date":"1898-09-21","event":"戊戌政变，慈禧重掌权，谭嗣同等六君子被杀",                  "category":"政治",    "importance":1},
    {"date":"1900-06",   "event":"义和团运动高峰，八国联军入侵北京",                          "category":"战争",    "importance":1},
    {"date":"1901-09-07","event":"辛丑条约签订，赔款四亿五千万两，清廷权威跌至谷底",          "category":"政治",    "importance":1},
    {"date":"1904-02",   "event":"日俄战争在中国东北爆发，清廷宣布局外中立",                  "category":"战争",    "importance":1},
    {"date":"1905-09-02","event":"废除科举制度，延续千年的选官体系终结",                      "category":"文化",    "importance":1},
    {"date":"1905",      "event":"中国同盟会成立（东京），孙中山提出三民主义",                "category":"政治",    "importance":1},
    {"date":"1906",      "event":"清廷宣布预备立宪，派五大臣出洋考察",                        "category":"政治",    "importance":2},
    {"date":"1908-11-14","event":"光绪帝崩，溥仪即位，隆裕太后垂帘",                         "category":"政治",    "importance":1},
    {"date":"1908-11-15","event":"慈禧太后去世，清廷进入最后三年",                            "category":"政治",    "importance":1},
    {"date":"1911-10-10","event":"武昌起义爆发，辛亥革命开始",                                "category":"政治",    "importance":1},

    # ── 民国初年（1912-1927）────────────────────────────────────────
    {"date":"1912-01-01","event":"中华民国成立，孙中山就任临时大总统（南京）",                "category":"政治",    "importance":1},
    {"date":"1912-02-12","event":"清帝逊位，溥仪退位，清朝灭亡",                              "category":"政治",    "importance":1},
    {"date":"1912-03",   "event":"袁世凯就任临时大总统，中华民国首都迁北京",                  "category":"政治",    "importance":1},
    {"date":"1913",      "event":"宋教仁被刺，二次革命失败，袁世凯独裁强化",                  "category":"政治",    "importance":2},
    {"date":"1915-01-18","event":"日本提出《二十一条》，企图独占中国",                        "category":"政治",    "importance":1},
    {"date":"1915-09",   "event":"《新青年》创刊（陈独秀），新文化运动标志性起点",             "category":"文化",    "importance":1},
    {"date":"1915-12",   "event":"袁世凯宣布称帝（洪宪帝制），各地护国运动兴起",             "category":"政治",    "importance":1},
    {"date":"1916-06-06","event":"袁世凯病死，黎元洪继任，府院之争开始",                     "category":"政治",    "importance":1},
    {"date":"1917",      "event":"张勋复辟（12日），旋即失败，共和再次恢复",                  "category":"政治",    "importance":2},
    {"date":"1917",      "event":"俄国十月革命，马克思主义开始向中国传播",                    "category":"社会",    "importance":1},
    {"date":"1919-05-04","event":"五四运动爆发，学生游行抗议巴黎和会，新文化运动高潮",        "category":"文化",    "importance":1},
    {"date":"1919",      "event":"白话文运动兴盛，胡适《文学改良刍议》广泛传播",              "category":"文化",    "importance":2},
    {"date":"1921-07",   "event":"中国共产党成立（上海一大）",                                "category":"政治",    "importance":1},
    {"date":"1923",      "event":"孙中山改组国民党，实行联俄联共扶助农工政策",                "category":"政治",    "importance":2},
    {"date":"1924",      "event":"黄埔军校创立，国共合作北伐准备",                            "category":"政治",    "importance":2},
    {"date":"1925-03-12","event":"孙中山逝世（北京），国民革命运动失去领袖",                  "category":"政治",    "importance":1},
    {"date":"1925-05-30","event":"五卅惨案（上海），反帝爱国运动高涨",                        "category":"社会",    "importance":1},
    {"date":"1926-07",   "event":"国民革命军北伐开始",                                        "category":"战争",    "importance":1},
    {"date":"1927-04-12","event":"四一二政变，蒋介石清党，国共第一次合作破裂",                "category":"政治",    "importance":1},
    {"date":"1927-04",   "event":"南京国民政府成立，北伐继续",                                "category":"政治",    "importance":1},

    # ── 南京国民政府时期（1927-1937）────────────────────────────────
    {"date":"1928",      "event":"北伐完成，国民政府名义上统一全国，定都南京",                "category":"政治",    "importance":1},
    {"date":"1928",      "event":"张作霖被炸死（皇姑屯事件），日本关东军制造事端",           "category":"战争",    "importance":2},
    {"date":"1929",      "event":"世界经济大萧条开始，波及中国",                              "category":"社会",    "importance":2},
    {"date":"1931-09-18","event":"九一八事变，日本占领东三省，伪满洲国成立",                  "category":"战争",    "importance":1},
    {"date":"1932-01-28","event":"一·二八事变（上海），淞沪抗战",                             "category":"战争",    "importance":1},
    {"date":"1934-10",   "event":"中央红军开始长征（两万五千里）",                            "category":"战争",    "importance":1},
    {"date":"1935-12-09","event":"一二·九运动，北平学生抗日救亡运动",                        "category":"社会",    "importance":2},
    {"date":"1936-12-12","event":"西安事变（张学良、杨虎城兵谏蒋介石），促成国共第二次合作",  "category":"政治",    "importance":1},

    # ── 抗日战争（1937-1945）────────────────────────────────────────
    {"date":"1937-07-07","event":"七七事变（卢沟桥），全面抗战爆发",                          "category":"战争",    "importance":1},
    {"date":"1937-08-13","event":"八一三淞沪会战，日军大举进攻上海",                          "category":"战争",    "importance":1},
    {"date":"1937-12-13","event":"南京沦陷，南京大屠杀（30余万人遇难）",                      "category":"战争",    "importance":1},
    {"date":"1938-10",   "event":"武汉沦陷，国民政府迁重庆，抗战进入相持阶段",               "category":"战争",    "importance":1},
    {"date":"1940-03",   "event":"汪伪政权成立（南京），汉奸政府开始运作",                   "category":"政治",    "importance":2},
    {"date":"1941-12-07","event":"珍珠港事件，美国对日宣战，二战太平洋战场扩大",             "category":"战争",    "importance":1},
    {"date":"1942",      "event":"延安文艺座谈会，毛泽东《在延安文艺座谈会上的讲话》",        "category":"文化",    "importance":1},
    {"date":"1943",      "event":"中美英签署《开罗宣言》，战后领土安排明确",                  "category":"政治",    "importance":2},
    {"date":"1944",      "event":"豫湘桂大溃败，国军损失惨重，美国对华政策转变",              "category":"战争",    "importance":2},
    {"date":"1945-08-15","event":"日本宣布无条件投降，抗战胜利",                              "category":"战争",    "importance":1},
    {"date":"1945-09-02","event":"日本正式签署投降书，第二次世界大战结束",                    "category":"战争",    "importance":1},

    # ── 国共内战（1945-1949）──────────────────────────────────────
    {"date":"1945-08",   "event":"重庆谈判（毛泽东赴渝），国共双十协定签订",                 "category":"政治",    "importance":1},
    {"date":"1946-06",   "event":"国共内战全面爆发",                                          "category":"战争",    "importance":1},
    {"date":"1947",      "event":"国共内战：国军攻占延安，但战局逐渐逆转",                    "category":"战争",    "importance":2},
    {"date":"1948",      "event":"三大战役开始（辽沈、淮海、平津），解放军全面攻势",          "category":"战争",    "importance":1},
    {"date":"1949-01-31","event":"北平和平解放",                                              "category":"政治",    "importance":1},
    {"date":"1949-04-23","event":"南京解放，国民政府覆灭",                                    "category":"政治",    "importance":1},
    {"date":"1949-10-01","event":"中华人民共和国成立（天安门城楼），毛泽东宣告",              "category":"政治",    "importance":1},

    # ── 新中国初期（1949-1955）──────────────────────────────────────
    {"date":"1950-06-25","event":"朝鲜战争爆发，中国志愿军入朝作战（10月）",                  "category":"战争",    "importance":1},
    {"date":"1950",      "event":"土地改革法颁布，全国土地改革运动展开",                      "category":"社会",    "importance":1},
    {"date":"1951",      "event":"思想改造运动（知识分子），镇压反革命运动",                   "category":"社会",    "importance":2},
    {"date":"1952",      "event":"三反五反运动，文化艺术界全面改造",                          "category":"社会",    "importance":2},
    {"date":"1953-07-27","event":"朝鲜战争停战协定签订",                                      "category":"战争",    "importance":1},
    {"date":"1953",      "event":"第一个五年计划开始，社会主义改造全面推进",                   "category":"社会",    "importance":1},
    {"date":"1954",      "event":"第一届全国人民代表大会召开，《中华人民共和国宪法》颁布",    "category":"政治",    "importance":1},
    {"date":"1955-03-25","event":"黄宾虹在杭州逝世，享年九十二岁",                            "category":"文化",    "importance":1},

    # ── 文化艺术专项 ────────────────────────────────────────────────
    {"date":"1902",      "event":"中国近代美术教育起步：南京两江师范学堂设图画手工科",        "category":"文化",    "importance":2},
    {"date":"1912",      "event":"民国成立后，北京大学等新式学堂蓬勃发展",                    "category":"文化",    "importance":2},
    {"date":"1912",      "event":"国学保存会、神州国光社推动金石学、国画复兴",                "category":"文化",    "importance":2},
    {"date":"1919",      "event":"徐悲鸿赴法留学，西画东渐加速",                              "category":"文化",    "importance":3},
    {"date":"1927",      "event":"上海美专（刘海粟）、杭州国立艺专（林风眠）先后发展成熟",   "category":"文化",    "importance":2},
    {"date":"1929",      "event":"全国第一届美术展览会在上海举行",                            "category":"文化",    "importance":2},
    {"date":"1937",      "event":"抗战爆发，大批文化人随政府内迁，文化重心西移",              "category":"文化",    "importance":2},
    {"date":"1942",      "event":"延安文艺整风，确立革命文艺方向",                            "category":"文化",    "importance":1},
    {"date":"1949",      "event":"全国文艺工作者代表大会，确立社会主义文艺路线",              "category":"文化",    "importance":1},
    {"date":"1953",      "event":"中国美协成立，国画改革讨论（传统vs革新）",                  "category":"文化",    "importance":2},
]

# 去重并排序
seen = set()
timeline = []
for e in ERA_EVENTS:
    key = e["date"] + e["event"][:10]
    if key not in seen:
        seen.add(key)
        timeline.append(e)

timeline.sort(key=lambda x: x["date"])

with open("era_timeline.json", "w", encoding="utf-8") as f:
    json.dump(timeline, f, ensure_ascii=False, indent=2)

print(f"era_timeline.json: {len(timeline)} 条事件")

# 统计
from collections import Counter
cats = Counter(e["category"] for e in timeline)
imp  = Counter(e["importance"] for e in timeline)
lines = [f"era_timeline.json: {len(timeline)} 条"]
lines.append("分类分布: " + str(dict(cats)))
lines.append("重要度分布: " + str(dict(imp)))
lines.append("")
lines.append("── 重要度1（最高）事件列表 ──")
for e in timeline:
    if e["importance"]==1:
        lines.append(f"  {e['date']:12s} [{e['category']}] {e['event']}")

with open("era_timeline_diag.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done -> era_timeline_diag.txt")
