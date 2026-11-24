# -*- coding: utf-8 -*-
"""支援四大類各 200 題不重複題庫、精簡 16 題 / 完整 50 題、同類隨機抽題、續測防重複與幻界 118 元素完整報告。"""
from __future__ import annotations

import json
import mimetypes
import random
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from seed_database import DB_FILE, connect

BASE_DIR = Path(__file__).resolve().parent
HTML_FILE = BASE_DIR / "index.html"
HOST = "127.0.0.1"
PORT = 8000

MBTI_SYSTEM_META = {
    "ENTJ": {
        "group": "分析家", "mbti_name": "指揮官",
        "month": "一月", "month_trait": "開創秩序",
        "plant": "梅花", "plant_desc": "歲首傲雪綻放，展現領袖風骨。",
        "archetype": "統治者", "archetype_desc": "建立秩序與掌控全局。",
        "primary_color": {"name": "金黃", "hex": "#EAB308"},
        "secondary_color": {"name": "深棕", "hex": "#5C4033"},
        "color_reason": "金色代表權威與榮耀；深棕象徵穩固結構與責任感。",
        "careers": "執行長（CEO）、管理顧問、專案總監、法官",
        "advice": "當目標推進太快時，不妨停下來聽聽夥伴的真實感受，把強大的魄力轉化為凝聚團隊的信任。",
        "dish": "黑椒爐烤牛排與焦香迷迭香",
        "vegetable": "炭烤蘆筍與紫洋蔥",
        "fruit": "血橙與熟成紅葡萄",
        "fortune": "形象運勢：氣場沉穩有威信，適合在關鍵時刻展現決斷力；貴人運偏向具備實務執行力的夥伴與前輩。",
    },
    "ESTJ": {
        "group": "守護者", "mbti_name": "總經理",
        "month": "一月", "month_trait": "開創秩序",
        "plant": "梅花", "plant_desc": "歲首傲雪綻放，講求原則與效率。",
        "archetype": "統治者", "archetype_desc": "建立秩序與高效運作。",
        "primary_color": {"name": "金黃", "hex": "#EAB308"},
        "secondary_color": {"name": "深棕", "hex": "#5C4033"},
        "color_reason": "金色代表權威；深棕象徵穩固執行力。",
        "careers": "企業高管、管理顧問、法官、營運長",
        "advice": "面對突如其來的變動時，保留一點彈性空間會讓你走得更穩，不必每件事都用同一套標準衡量。",
        "dish": "經典紅燒蹄膀與蒜苗",
        "vegetable": "高麗菜與西洋芹",
        "fruit": "青蘋果與酸甜鳳梨",
        "fortune": "形象運勢：可靠守信的專業形象深植人心；貴人多為重視規則、資源豐富的主管或制度推手。",
    },
    "ENFP": {
        "group": "外交家", "mbti_name": "競選者",
        "month": "二月", "month_trait": "浪漫生機",
        "plant": "桃花", "plant_desc": "春風吹拂，象徵熱情感染力與自由創造。",
        "archetype": "愛人者", "archetype_desc": "追求深層連結與對美的熱愛。",
        "primary_color": {"name": "洋紅", "hex": "#DB2777"},
        "secondary_color": {"name": "蜜桃橘", "hex": "#FDBA74"},
        "color_reason": "洋紅象徵濃烈情感；蜜桃色帶出浪漫依戀。",
        "careers": "創意總監、公關媒體、品牌行銷、活動策展",
        "advice": "靈感很多很美好，挑出當下最想完成的一兩件事落地實踐，你的熱情就能發揮最大光芒。",
        "dish": "香草檸檬烤雞與彩色時蔬沙拉",
        "vegetable": "甜椒與番茄",
        "fruit": "水蜜桃與草莓",
        "fortune": "形象運勢：親切鮮活、極具感染力，容易成為聚會與創意焦點；貴人常在跨界交流與新朋友中出現。",
    },
    "ESFP": {
        "group": "探險家", "mbti_name": "表演者",
        "month": "七月", "month_trait": "活在當下",
        "plant": "荔枝樹", "plant_desc": "盛夏果實飽滿，熱愛感官體驗與分享快樂。",
        "archetype": "弄臣", "archetype_desc": "用幽默感與熱情點亮全場。",
        "primary_color": {"name": "檸檬黃", "hex": "#FACC15"},
        "secondary_color": {"name": "萊姆綠", "hex": "#84CC16"},
        "color_reason": "黃色最具幽默感與感染力。",
        "careers": "美食評論家、旅遊部落客、時尚造型師、主持人",
        "advice": "享受當下的快樂之餘，也為自己留一點安靜沉澱的時間，能讓你的笑容更持久且有深度。",
        "dish": "泰式酸辣海鮮與香茅料理",
        "vegetable": "小黃瓜與玉米筍",
        "fruit": "荔枝、芒果與百香果",
        "fortune": "形象運勢：明亮自然、充滿生活溫度，能瞬間拉近距離；貴人多是樂於分享機會與體驗的同行夥伴。",
    },
    "INFP": {
        "group": "外交家", "mbti_name": "調停者",
        "month": "三月", "month_trait": "詩意理想",
        "plant": "油桐花", "plant_desc": "花開清麗，自帶文藝詩意與敏銳共情力。",
        "archetype": "創造者", "archetype_desc": "將豐富情感化為獨特故事與藝術。",
        "primary_color": {"name": "亮橘", "hex": "#F97316"},
        "secondary_color": {"name": "薰衣草紫", "hex": "#C084FC"},
        "color_reason": "亮橘代表靈感；淺紫象徵藝術氣息。",
        "careers": "作家、插畫家、心理諮商師、音樂創作人",
        "advice": "你的溫柔與理想很珍貴，試著把內心感受寫下來或分享給懂你的人，別獨自扛下所有情緒。",
        "dish": "松露野菇燉飯與迷迭香烤蔬菜",
        "vegetable": "杏鮑菇與紫甘藍",
        "fruit": "藍莓與無花果",
        "fortune": "形象運勢：溫柔細膩、富有故事感，容易讓人卸下防備；貴人多為欣賞你才華與真誠內心的知音。",
    },
    "ISFJ": {
        "group": "守護者", "mbti_name": "守衛者",
        "month": "四月", "month_trait": "內斂務實",
        "plant": "青梅", "plant_desc": "青梅內斂耐品，低調守護與踏實奉獻。",
        "archetype": "照顧者", "archetype_desc": "尋找歸屬與真誠連結。",
        "primary_color": {"name": "米色", "hex": "#D6C7B2"},
        "secondary_color": {"name": "淺灰", "hex": "#CBD5E1"},
        "color_reason": "大地裸色系代表腳踏實地與平易近人。",
        "careers": "護理師、營養師、HR、行政管理",
        "advice": "照顧別人之前，記得先問問自己累了嗎？適度說出需求，才能讓這份溫暖長久陪伴大家。",
        "dish": "梅汁蒸魚與清炒時蔬",
        "vegetable": "山藥與大白菜",
        "fruit": "青梅、水梨與白桃",
        "fortune": "形象運勢：穩重貼心、讓人安心信賴，越相處越顯珍貴；貴人常是默默支持你、重視承諾的長輩或老友。",
    },
    "ISFP": {
        "group": "探險家", "mbti_name": "探險家",
        "month": "三月", "month_trait": "隨性佛系",
        "plant": "山茶花", "plant_desc": "透過獨特審美表達自我，溫柔忠於內心。",
        "archetype": "探險家", "archetype_desc": "追求自由與真實感官體驗。",
        "primary_color": {"name": "森林綠", "hex": "#15803D"},
        "secondary_color": {"name": "土耳其藍", "hex": "#06B6D4"},
        "color_reason": "綠色代表大自然與不受拘束的靈魂。",
        "careers": "自由藝術家、獨立設計師、花藝師、攝影師",
        "advice": "跟著你的直覺與美感走，不需要急著和別人比較步調，你的獨特節奏本身就是風景。",
        "dish": "羅勒青醬義大利麵與田園沙拉",
        "vegetable": "菠菜與櫛瓜",
        "fruit": "奇異果與白葡萄",
        "fortune": "形象運勢：自在真實、審美獨到，散發低調的藝術魅力；貴人多是尊重你自由步調與創作空間的人。",
    },
    "ESTP": {
        "group": "探險家", "mbti_name": "企業家",
        "month": "五月", "month_trait": "行動守護",
        "plant": "菖蒲", "plant_desc": "菖蒲如劍，代表極強的行動力與破局思維。",
        "archetype": "英雄", "archetype_desc": "追求挑戰與戰士精神。",
        "primary_color": {"name": "正紅", "hex": "#EF4444"},
        "secondary_color": {"name": "酒紅", "hex": "#991B1B"},
        "color_reason": "正紅象徵行動力與勇氣。",
        "careers": "急診醫師、金融交易員、工程師、運動員",
        "advice": "行動力強是你的優勢，出手前花兩分鐘看清風險與後果，能讓你贏得更漂亮。",
        "dish": "辣味炙燒牛肉與墨西哥捲餅",
        "vegetable": "辣椒與紅甜椒",
        "fruit": "紅火龍果與西瓜",
        "fortune": "形象運勢：俐落果斷、敢於破局，危機時刻特別亮眼；貴人多為擅長資源整合或快狠準實戰的夥伴。",
    },
    "ISTP": {
        "group": "探險家", "mbti_name": "鑑賞家",
        "month": "五月", "month_trait": "行動守護",
        "plant": "菖蒲", "plant_desc": "反應敏捷，重視當下實戰與技術破局。",
        "archetype": "英雄", "archetype_desc": "冷靜克服挑戰的獨行戰士。",
        "primary_color": {"name": "正紅", "hex": "#EF4444"},
        "secondary_color": {"name": "酒紅", "hex": "#991B1B"},
        "color_reason": "正紅象徵果斷行動力。",
        "careers": "外科醫師、金融交易員、建築工程師",
        "advice": "你擅長解決眼前問題，偶爾也把想法簡單說出口，讓關心你的人知道你一切安好。",
        "dish": "香煎干貝與脆皮燒肉",
        "vegetable": "綠花椰菜與洋蔥",
        "fruit": "哈密瓜與芭樂",
        "fortune": "形象運勢：冷靜精準、實力派氣場十足；貴人多在實作現場、技術領域或關鍵時刻出現的幫手。",
    },
    "INFJ": {
        "group": "外交家", "mbti_name": "提倡者",
        "month": "六月", "month_trait": "精神引領",
        "plant": "荷花", "plant_desc": "出淤泥而不染，保有精神純粹與深刻洞察力。",
        "archetype": "天真者", "archetype_desc": "守護內心純淨與崇高理想。",
        "primary_color": {"name": "純白", "hex": "#F8FAFC"},
        "secondary_color": {"name": "淡粉紅", "hex": "#FBCFE8"},
        "color_reason": "白色象徵純粹與精神高潔。",
        "careers": "臨床心理師、生涯規劃師、NGO倡議者、編劇",
        "advice": "洞察力讓你看得很深，但也別忘了設定心理界線，把能量留給真正值得投入的人與事。",
        "dish": "蓮子清燉湯品與清蒸鮮蔬",
        "vegetable": "蓮藕與娃娃菜",
        "fruit": "白柚與蓮霧",
        "fortune": "形象運勢：清澈深邃、具引導與療癒氣質；貴人常是能理解你深層理念、給予精神支持的引路人。",
    },
    "ENFJ": {
        "group": "外交家", "mbti_name": "主人公",
        "month": "八月", "month_trait": "凝聚人心",
        "plant": "桂花", "plant_desc": "氣味溫潤不刺鼻，最能凝聚人心與和諧。",
        "archetype": "魔法師", "archetype_desc": "透過感召力促成團隊蛻變。",
        "primary_color": {"name": "皇家紫", "hex": "#7E22CE"},
        "secondary_color": {"name": "銀灰", "hex": "#94A3B8"},
        "color_reason": "紫色象徵靈性與直覺力。",
        "careers": "教育工作者、團隊教練、社工師、婚禮顧問",
        "advice": "你總能帶動大家往前走，但別把所有人的期待都背在肩上，允許自己有不完美的時刻。",
        "dish": "桂花蜜汁叉燒與溫潤燉菜",
        "vegetable": "南瓜與秋葵",
        "fruit": "柿子與蜜蘋果",
        "fortune": "形象運勢：溫暖有感召力，善於串聯人心；貴人多為願意與你共同成就願景的團隊夥伴。",
    },
    "ESFJ": {
        "group": "守護者", "mbti_name": "執政官",
        "month": "八月", "month_trait": "凝聚人心",
        "plant": "桂花", "plant_desc": "象徵豐收與團圓，用溫暖照護身邊每個人。",
        "archetype": "魔法師", "archetype_desc": "善於整合人際與資源。",
        "primary_color": {"name": "皇家紫", "hex": "#7E22CE"},
        "secondary_color": {"name": "銀灰", "hex": "#94A3B8"},
        "color_reason": "紫色代表溫潤的精神感召。",
        "careers": "教育工作者、客戶經理、社工師",
        "advice": "你的貼心是團隊的潤滑劑，當感到委屈或疲憊時，適度表達真實想法會讓關係更健康。",
        "dish": "家常暖心雞湯與鮮炒時蔬",
        "vegetable": "紅蘿蔔與高麗菜",
        "fruit": "荔枝與香甜葡萄",
        "fortune": "形象運勢：親切周到、人緣佳且凝聚力強；貴人常是重視情誼、樂於互相照應的生活與職場夥伴。",
    },
    "INTP": {
        "group": "分析家", "mbti_name": "邏輯學家",
        "month": "九月", "month_trait": "獨立思辨",
        "plant": "菊花", "plant_desc": "秋霜中獨自盛開，熱愛獨立思辨與真理。",
        "archetype": "智者", "archetype_desc": "追求客觀真理與底層智慧。",
        "primary_color": {"name": "海軍藍", "hex": "#1E3A8A"},
        "secondary_color": {"name": "靛藍", "hex": "#4338CA"},
        "color_reason": "深藍象徵冷靜與理性分析。",
        "careers": "演算法工程師、研究員、系統架構師、數據分析師",
        "advice": "思考很過癮，但偶爾把想法做成一個小原型或簡單結論，能幫你更快看到真實回饋。",
        "dish": "日式咖哩與酥炸天婦羅",
        "vegetable": "茄子與牛蒡",
        "fruit": "藍莓與蘋果",
        "fortune": "形象運勢：清冷睿智、思維獨特，關鍵點子常讓人驚豔；貴人多為能幫你把抽象想法落地的實務搭檔。",
    },
    "INTJ": {
        "group": "分析家", "mbti_name": "建築師",
        "month": "十月", "month_trait": "暗藏鋒芒",
        "plant": "山茶花", "plant_desc": "逆勢綻放，外表冷靜高雅，內在蘊藏強大戰略能量。",
        "archetype": "反抗者", "archetype_desc": "不盲從常規，蘊含戰略意志。",
        "primary_color": {"name": "純黑", "hex": "#18181B"},
        "secondary_color": {"name": "暗紫", "hex": "#581C87"},
        "color_reason": "黑色代表絕對獨立與拒絕妥協。",
        "careers": "投資銀行家、企業策略長、軟體架構師、律師",
        "advice": "眼光精準是你的強項，在推動藍圖時多一點耐心與溝通鋪陳，能讓更多人跟上你的節奏。",
        "dish": "黑蒜燉排骨與低溫烹調牛排",
        "vegetable": "黑木耳與菠菜",
        "fruit": "黑莓與石榴",
        "fortune": "形象運勢：沉著冷靜、戰略感強烈，自帶高辨識度氣場；貴人多為能理解長遠布局的策略夥伴。",
    },
    "ENTP": {
        "group": "分析家", "mbti_name": "辯論家",
        "month": "十一月", "month_trait": "堅毅先驅",
        "plant": "水仙", "plant_desc": "嚴冬中率先破土，象徵靈活變通與探索精神。",
        "archetype": "探險家", "archetype_desc": "永遠在尋找新出路與思維邊界。",
        "primary_color": {"name": "森林綠", "hex": "#15803D"},
        "secondary_color": {"name": "土耳其藍", "hex": "#06B6D4"},
        "color_reason": "綠色代表破土生機與遼闊視野。",
        "careers": "連續創業者、產品經理、廣告創意、趨勢分析師",
        "advice": "點子很多很有趣，挑一個最有潛力的方向走完最後一哩路，往往會帶來意想不到的突破。",
        "dish": "義式香料烤雞與創意 tapas",
        "vegetable": "芝麻葉與蘆筍",
        "fruit": "奇異果與柑橘",
        "fortune": "形象運勢：機智靈活、點子源源不絕，善於打破僵局；貴人多為擅長穩定執行與收尾的互補型夥伴。",
    },
    "ISTJ": {
        "group": "守護者", "mbti_name": "物流師",
        "month": "十二月", "month_trait": "承先啟後",
        "plant": "松柏", "plant_desc": "四季常青，展現嚴謹、可靠與傳承精神。",
        "archetype": "照顧者", "archetype_desc": "透過恪守職責成為安心後盾。",
        "primary_color": {"name": "珊瑚粉", "hex": "#FB7185"},
        "secondary_color": {"name": "暖橘", "hex": "#EA580C"},
        "color_reason": "象徵穩固的承諾與細心照護。",
        "careers": "會計師、精算師、稽核專員、供應鏈管理師",
        "advice": "你的可靠讓人非常安心，遇到超出預期的新變化時，不妨給自己一點緩衝與嘗試的空間。",
        "dish": "經典滷味拼盤與清燉牛肉湯",
        "vegetable": "白蘿蔔與花椰菜",
        "fruit": "富士蘋果與香吉士",
        "fortune": "形象運勢：穩健踏實、言出必行，是團隊的定心丸；貴人常在制度建立、長期合作與關鍵審核中助力。",
    },
}

DEFAULT_META = {
    "group": "多元人格系列", "mbti_name": "幻界元素",
    "month": "四季循環", "month_trait": "自然原力",
    "plant": "奇幻靈花", "plant_desc": "蘊含獨特的自然能量與生命氣息。",
    "archetype": "探險家", "archetype_desc": "探索未知與自我潛能。",
    "primary_color": {"name": "皇家紫", "hex": "#7E22CE"},
    "secondary_color": {"name": "銀灰", "hex": "#94A3B8"},
    "color_reason": "象徵靈性轉化與無限可能。",
    "careers": "跨領域創新者、專案顧問、自由創作者",
    "advice": "保持好奇與覺察，依照自己的步調探索，每一步都是屬於你的成長。",
    "dish": "清爽地中海拼盤",
    "vegetable": "鮮蔬沙拉與烤時蔬",
    "fruit": "綜合莓果與柑橘",
    "fortune": "形象運勢：自然獨特、充滿探索張力；貴人多在跨界交流與新體驗中相遇。",
}

RAW_ELEMENTS_118 = [
    ("001", "St", "Stellarium", "純真先驅", "ENFP", "第1-2週期", "充滿好奇心的元氣少年，總是一馬當先探索未知。"),
    ("002", "L", "Lunacrys", "清冷月神", "INFJ", "第1-2週期", "安靜優雅的銀髮少女，習慣在夜裡獨處。"),
    ("003", "G", "Glorion", "榮耀騎士", "ESTP", "第1-2週期", "性格耿直熱血、正義感爆棚的戰鬥派。"),
    ("004", "Th", "Thunderium", "暴躁雷公", "ESTJ", "第1-2週期", "說話大聲、行動雷厲風行的可靠夥伴。"),
    ("005", "P", "Phantasma", "神出鬼沒", "ENTP", "第1-2週期", "喜歡躲在角落惡作劇的幽靈系少年。"),
    ("006", "Gx", "Galaxium", "浪漫夢想家", "INFP", "第1-2週期", "腦袋裝滿整片星空的文藝青年。"),
    ("007", "A", "Aurorite", "溫柔治癒師", "ISFJ", "第1-2週期", "散發極光般柔和氣場的溫暖守護者。"),
    ("008", "Py", "Pyroflame", "熱情燃燒者", "ESFP", "第1-2週期", "對任何事都全力以赴的樂天行動派。"),
    ("009", "C", "Cryostone", "理性冰山", "INTJ", "第1-2週期", "外表冷漠、說話一針見血的邏輯控。"),
    ("010", "M", "Mistoria", "慵懶霧隱", "ISFP", "第1-2週期", "總是睡眼惺忪、喜歡泡在茶館的佛系智者。"),
    ("011", "Ce", "Celestium", "高貴天裔", "ESTJ", "第3週期", "舉止優雅、帶點微傲嬌的貴族少爺。"),
    ("012", "Mg", "Magnetara", "萬人迷磁石", "ESFP", "第3週期", "天生具備強烈吸引力的社交焦點。"),
    ("013", "B", "Blueflame", "冷靜狂熱者", "ISTP", "第3週期", "一旦觸及感興趣領域便展現驚人執著。"),
    ("014", "Am", "Amethystium", "神秘占卜師", "INFJ", "第3週期", "直覺敏銳、常能看穿謊言的占卜師。"),
    ("015", "F", "Frostwing", "自由風雪", "ISTP", "第3週期", "嚮往天空的孤高旅人，來去如風。"),
    ("016", "Sh", "Shadowium", "忠誠暗衛", "ISFJ", "第3週期", "習慣隱身身後的沉默守護者，嘴硬心軟。"),
    ("017", "S", "Solarium", "陽光領袖", "ENFJ", "第3週期", "自帶聚光燈的王者型人格，樂觀開朗。"),
    ("018", "N", "Nocturnium", "夜行紳士", "ISFP", "第3週期", "夜晚精神百倍的優雅夜貓子。"),
    ("019", "D", "Draconium", "霸道龍王", "ENTJ", "第4週期", "自尊心極強、護短又霸氣的戰鬥狂。"),
    ("020", "Ph", "Phoenixium", "不屈浴火者", "ESFP", "第4週期", "越挫越勇的樂天派，失敗也能笑著站起。"),
    ("021", "Lu", "Luminaris", "聖潔引路人", "ENFJ", "第4週期", "溫和堅定的燈塔型角色，指明方向。"),
    ("022", "V", "Voidium", "虛無極簡控", "INTP", "第4週期", "對物質毫無慾望的冷靜旁觀者。"),
    ("023", "As", "Astralux", "星軌學者", "INTP", "第4週期", "熱愛計算與觀察宇宙規律的考據狂。"),
    ("024", "O", "Oceanium", "包容海皇", "ESTP", "第4週期", "胸懷寬廣、情緒深沉如海的大叔型角色。"),
    ("025", "Tm", "Tempestium", "狂野風暴", "ESFP", "第4週期", "靈感一來如龍捲風般席捲全場的藝術家。"),
    ("026", "Tu", "Thundora", "雷鳴戰姬", "ESTP", "第4週期", "爽朗豪邁、喜歡直球對決的短髮少女。"),
    ("027", "Sd", "Stardustium", "愛哭小精靈", "INFP", "第4週期", "容易感動落淚的感性派精靈。"),
    ("028", "Lf", "Lightfall", "悲劇詩人", "INFP", "第4週期", "自帶憂鬱濾鏡、喜歡感嘆時光的青年。"),
    ("029", "Dr", "Dreamium", "白日夢家", "INFP", "第4週期", "分不清現實與夢境的迷糊浪漫主義者。"),
    ("030", "Nt", "Netherium", "深淵叛逆者", "ISFP", "第4週期", "嘴上討厭世界其實非常重義氣的少年。"),
    ("031", "Cr", "Crystalia", "完美主義者", "ISTJ", "第4週期", "追求無瑕結構與絕對透明感的工匠。"),
    ("032", "Ne", "Neonara", "派對焦點", "ESFP", "第4週期", "熱愛霓虹燈與音樂的潮流達人。"),
    ("033", "Aq", "Aquavelle", "靈動水精", "ESFJ", "第4週期", "善於察言觀色、處事圓滑的社交高手。"),
    ("034", "Cm", "Crimsonite", "赤紅決鬥者", "ESTP", "第4週期", "追求極致勝負的武癡，對強者充滿敬意。"),
    ("035", "Sk", "Skytherium", "雲端漫步者", "ESFP", "第4週期", "性格灑脫不羈、隨時準備出發旅行。"),
    ("036", "Sn", "Snowphant", "憨厚雪獸", "ISFJ", "第4週期", "體型龐大卻性格溫馴的冬日暖男。"),
    ("037", "Sp", "Sharpium", "毒舌劍客", "ESTJ", "第5週期", "說話如刀般鋒利、是非分明的劍客。"),
    ("038", "Au", "Aurumite", "奢華鑑賞家", "ISFP", "第5週期", "品味極佳、看重事物內在價值的藏家。"),
    ("039", "Az", "Azureon", "深海哲人", "INFJ", "第5週期", "能用平靜語氣化解爭吵的深沉傾聽者。"),
    ("040", "Gl", "Glacielle", "高嶺之花", "ISFJ", "第5週期", "氣質清麗脫俗、熟識後很會照顧人的冰美人。"),
    ("041", "I", "Infernium", "煉獄狂戰士", "ESTP", "第5週期", "戰鬥時忘我的熱血派，私下是居家好男人。"),
    ("042", "T", "Terravium", "大地守衛", "ISTJ", "第5週期", "腳踏實地、說一不二的團隊堅實後盾。"),
    ("043", "Sl", "Starloop", "循環強迫症", "ISTJ", "第5週期", "做事必須照固定流程走的嚴謹計畫控。"),
    ("044", "Sw", "Swiftshadow", "疾風斥候", "ESTP", "第5週期", "行動敏捷、永遠掌握第一手消息的情報販子。"),
    ("045", "Lg", "Lightfeather", "輕盈舞者", "ISFP", "第5週期", "心思細膩、跳起舞來光芒萬丈的少女。"),
    ("046", "Tw", "Twilightium", "黃昏雙面人", "ISFP", "第5週期", "白天與夜晚展現截然不同面貌的雙面人。"),
    ("047", "Mf", "Moonflare", "傲嬌月耀", "ISFP", "第5週期", "被誇獎就會瞬間臉紅害羞的反差萌少女。"),
    ("048", "Sf", "Stormflame", "爆裂先鋒", "ESTP", "第5週期", "信奉先行動再說的冒險家。"),
    ("049", "Sr", "Spiritium", "通靈少年", "INFP", "第5週期", "能聽見萬物心聲的溫柔療癒系男孩。"),
    ("050", "Fn", "Frostnova", "極寒爆破手", "ESTP", "第5週期", "平時乖巧、忍耐極限到達會瞬間爆發者。"),
    ("051", "Ss", "Shatterstar", "破碎重組者", "INTP", "第5週期", "喜歡拆解東西研究原理的機械宅。"),
    ("052", "Ds", "Dawnshine", "元氣晨曦", "ESFJ", "第5週期", "充滿正能量、最早叫大家起床的班長。"),
    ("053", "Vo", "Voltaris", "高壓發明家", "INTP", "第5週期", "滿腦子奇特實驗點子的瘋狂科學家。"),
    ("054", "Fa", "Fantasium", "童話說書人", "ENFP", "第5週期", "把日常講得像史詩冒險的魅力演說家。"),
    ("055", "E", "Emeraldium", "翡翠貴公子", "ESFJ", "第6週期", "溫文儒雅、對待生命極為溫柔的植物學家。"),
    ("056", "Si", "Silvershade", "銀幕策士", "INTJ", "第6週期", "喜歡在暗處運籌帷幄的冷靜幕後軍師。"),
    ("057", "Cf", "Scarletflame", "緋紅女王", "ENTJ", "緋焰系", "氣場強大、自信耀眼的舞台中心領袖。"),
    ("058", "Il", "Illusium", "幻術魔術師", "ENTP", "緋焰系", "用華麗戲法逗人開心的幽默紳士。"),
    ("059", "Wv", "Starwave", "星潮衝浪手", "ESFP", "緋焰系", "隨性樂觀、懂得順勢而為的行動派。"),
    ("060", "Cl", "Cloudspire", "雲端建築師", "ENFP", "緋焰系", "擁有宏大願景、喜歡構築高遠目標的理想家。"),
    ("061", "Vi", "Violetfire", "紫焰魔女", "ISFP", "緋焰系", "對禁忌知識充滿好奇的神祕學者。"),
    ("062", "Ww", "Windwhisper", "風語傾聽者", "ISFJ", "緋焰系", "擅長傾聽他人煩惱的溫柔秘密保管人。"),
    ("063", "Ca", "Celestara", "星辰歌姬", "ESFJ", "緋焰系", "歌聲能撫慰心靈、對世界充滿善意的少女。"),
    ("064", "Ec", "Eclipsium", "日蝕雙子", "ISFP", "緋焰系", "同時擁有光明與陰暗兩面的戲劇張力角色。"),
    ("065", "So", "Soulflame", "靈魂共鳴者", "ENFP", "緋焰系", "共情力極強的藝術家。"),
    ("066", "Nb", "Nebulite", "星雲孕育者", "ENFJ", "緋焰系", "充滿母性光輝與創造力的溫柔導師。"),
    ("067", "Gw", "Goldenwing", "金翼信使", "ESTJ", "緋焰系", "驕傲卻無比盡責的使命必達飛翔者。"),
    ("068", "Gc", "Glacierium", "萬年冰川", "ISTJ", "緋焰系", "記憶力驚人、記仇也記恩的沉穩巨人。"),
    ("069", "Sa", "Solarshadow", "光影行者", "ISTP", "緋焰系", "在光明與黑暗取得平衡的務實派高手。"),
    ("070", "Dc", "Dragoncrys", "龍晶收藏家", "ISFP", "緋焰系", "對珍稀寶物有執著熱愛的鑒寶師。"),
    ("071", "Pf", "Phoenixflame", "涅槃導師", "ENFJ", "緋焰系", "用溫暖話語激勵陷入低潮者的智者。"),
    ("072", "Cs", "Cosmosphere", "宏觀統籌者", "ENTJ", "第6週期", "大局觀極強、擅長協調人際與資源的指揮官。"),
    ("073", "Vf", "Verdaflame", "生命之火", "ESTP", "第6週期", "充滿野性魅力的果斷森林遊俠。"),
    ("074", "Pc", "Phantomcrys", "鏡花水月", "ENTP", "第6週期", "喜歡用謎語考驗別人的神秘貴族。"),
    ("075", "Sv", "Solvion", "破局專家", "ENTJ", "第6週期", "再混亂局面都能理出頭緒的冷靜顧問。"),
    ("076", "Tc", "Thundercrys", "蓄電修行者", "ISTP", "第6週期", "關鍵時刻一鳴驚人的寡言武道家。"),
    ("077", "Sc", "Skycascade", "飛瀑豪傑", "ESTP", "第6週期", "爽快不拘小節、喜歡暢談理想的俠客。"),
    ("078", "Mo", "Moonfrost", "月霜詩人", "INFP", "第6週期", "喜歡在雪夜裡寫詩的清冷才女。"),
    ("079", "Fr", "Starfire", "星火革命家", "ENFP", "第6週期", "眼中永遠燃燒不滅理想的熱血青年。"),
    ("080", "Mv", "Mistveil", "面紗舞姬", "ISFP", "第6週期", "舉手投足充滿神秘美感的優雅女性。"),
    ("081", "Vd", "Violetdawn", "紫霞觀察者", "INFJ", "第6週期", "在清晨靜靜思考人生的沉靜哲學少女。"),
    ("082", "Sg", "Silverglow", "微光守護者", "ISFJ", "第6週期", "不求回報、默默在背後照亮別人的前輩。"),
    ("083", "W", "Windaria", "自由吟遊詩人", "ESFP", "第6週期", "四海為家的浪子，哪裡有故事就往哪裡去。"),
    ("084", "Pr", "Pyrelis", "煉金焰師", "ESTJ", "第6週期", "對火候掌控極度嚴苛的外冷內熱大師。"),
    ("085", "Ar", "Aquaris", "深藍調停者", "ENFJ", "第6週期", "語氣溫柔卻極具說服力的外交官。"),
    ("086", "Tr", "Terralis", "隱世長老", "INFJ", "第6週期", "泰山崩於前而色不變的沉穩賢者。"),
    ("087", "Ln", "Luminucleus", "光明聖王", "ENTJ", "第7週期主族", "象徵絕對正義與秩序之光的威嚴統治者。"),
    ("088", "Dn", "Darknucleus", "暗夜帝君", "INTJ", "第7週期主族", "與 Ln 互為宿敵的深沉莫測幕後主宰。"),
    ("089", "Te", "Temporium", "時間旅人", "ISTJ", "時空系", "隨身帶著懷錶、永遠準時的紳士。"),
    ("090", "Q", "Quantara", "量子貓咪", "ISFP", "時空系", "性格薛丁格化、捉摸不定的神秘少女。"),
    ("091", "Pm", "Prismora", "稜鏡鑑賞家", "ENFJ", "時空系", "善於從不同角度看同一件事的開明智者。"),
    ("092", "Ab", "Abyssium", "深淵凝視者", "INFJ", "時空系", "承載無數秘密的孤獨孤傲守護者。"),
    ("093", "Rs", "Sanctaris", "聖域祭司", "ISFJ", "時空系", "致力保護弱小與神聖之地的溫柔祭司。"),
    ("094", "Mc", "Magicyte", "魔導優等生", "INTP", "時空系", "筆記本永遠寫滿魔法理論的學霸少女。"),
    ("095", "Ws", "Wolfstar", "孤狼獵手", "ISTP", "時空系", "對認定的夥伴絕對忠義的獨行俠。"),
    ("096", "Bo", "Starbornium", "星之驕子", "ESFP", "時空系", "天生自帶好運與天賦的開朗少年。"),
    ("097", "Hf", "Hyperflame", "超新星狂人", "ESTP", "時空系", "情感極度熾熱、毫不掩飾愛恨的豪邁戰士。"),
    ("098", "Ef", "Everfrost", "永凍守望者", "ISTJ", "時空系", "數百年如一日堅守崗位的忠誠衛士。"),
    ("099", "Fl", "Firstlight", "初光少年", "ENFP", "時空系", "象徵希望與黎明的純真孩子。"),
    ("100", "Ev", "Evernight", "永夜淑女", "ISFP", "時空系", "優雅而神秘的暗夜貴婦。"),
    ("101", "Oc", "Oraculum", "神諭先知", "INFJ", "時空系", "喜歡用雙關語讓年輕人自己悟出答案的老者。"),
    ("102", "Is", "Illusionite", "海市蜃樓", "ISFP", "時空系", "在人們最渴望時出現又消失的浪漫旅人。"),
    ("103", "Ch", "Chaotium", "混沌樂子人", "ENTP", "時空系", "哪裡無聊就去製造小混亂的搗蛋鬼。"),
    ("104", "Or", "Ordinium", "法則大法官", "ISTJ", "第7週期主族", "一絲不苟、絕對公正的秩序化身。"),
    ("105", "Vt", "Vitalium", "生命女神", "ESFJ", "第7週期主族", "充滿朝氣與慈愛的自然化身。"),
    ("106", "Su", "Soularis", "靈魂擺渡人", "INFJ", "第7週期主族", "看透生死卻依然珍視每一段記憶的引導者。"),
    ("107", "Dm", "Dimensionium", "空間魔術師", "ENTP", "第7週期主族", "思維跳脫三維限制的怪才。"),
    ("108", "Sb", "Superstringium", "萬物模仿者", "ESFP", "第7週期主族", "能完美扮演任何人的全能演員。"),
    ("109", "Nm", "Nightmarium", "夢魘編織者", "INFJ", "第7週期主族", "幫助人面對內心恐懼的另類心理師。"),
    ("110", "Dv", "Divinium", "神聖審判長", "ENTJ", "第7週期主族", "自帶神聖光環、不容許污穢的理想主義者。"),
    ("111", "U", "Universium", "星海巨人", "INFJ", "第7週期主族", "胸懷包羅萬象、帶著宏觀慈悲的神祇。"),
    ("112", "If", "Infinitium", "無限狂想家", "ENTP", "第7週期主族", "精力永遠用不完的永動機少年。"),
    ("113", "Gn", "Genesisium", "創世造物主", "ENFP", "第7週期主族", "熱愛賦予萬物生命與名字的藝術之神。"),
    ("114", "En", "Endorium", "終焉審判者", "INTJ", "第7週期主族", "負責為一切畫下乾淨俐落句點的收尾人。"),
    ("115", "Et", "Eternium", "永恆見證者", "ISTJ", "第7週期主族", "靜靜看著時代更迭卻從不干涉的紀錄者。"),
    ("116", "Sm", "Singularium", "奇點隱士", "INTJ", "第7週期主族", "一開口便是真理的極致沉默深邃智者。"),
    ("117", "Tp", "Temporalis", "時間頑童", "ENTP", "第7週期主族", "對過去與未來瞭若指掌的調皮神明。"),
    ("118", "Og", "Originarium", "本源創始神", "INFP", "第7週期主族", "一切故事的起點與歸宿之最純粹存在。"),
]

ELEMENTS_118 = []
ELEMENTS_BY_MBTI = {}
for num, sym, eng, title, mbti, period, desc in RAW_ELEMENTS_118:
    meta = MBTI_SYSTEM_META.get(mbti, DEFAULT_META)
    item = {
        "num": num, "sym": sym, "eng": eng, "title": title,
        "mbti": mbti, "period": period, "desc": desc,
        "group": meta["group"], "mbti_name": meta["mbti_name"],
        "month": meta["month"], "month_trait": meta["month_trait"],
        "plant": meta["plant"], "plant_desc": meta["plant_desc"],
        "archetype": meta["archetype"], "archetype_desc": meta["archetype_desc"],
        "primary_color": meta["primary_color"],
        "secondary_color": meta["secondary_color"],
        "color_reason": meta["color_reason"],
        "careers": meta["careers"],
        "advice": meta["advice"],
        "dish": meta["dish"],
        "vegetable": meta["vegetable"],
        "fruit": meta["fruit"],
        "fortune": meta["fortune"],
        "flavor_profile": f"菜餚：{meta['dish']}｜蔬菜：{meta['vegetable']}｜水果：{meta['fruit']}",
    }
    ELEMENTS_118.append(item)
    ELEMENTS_BY_MBTI.setdefault(mbti, []).append(item)


def _ensure_columns(conn) -> None:
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(test_sessions)").fetchall()}
    if "group_id" not in cols:
        conn.execute("ALTER TABLE test_sessions ADD COLUMN group_id INTEGER NOT NULL DEFAULT 1")
    if "mode_count" not in cols:
        conn.execute("ALTER TABLE test_sessions ADD COLUMN mode_count INTEGER NOT NULL DEFAULT 50")
    if "question_order_json" not in cols:
        conn.execute("ALTER TABLE test_sessions ADD COLUMN question_order_json TEXT NOT NULL DEFAULT '[]'")
    if "result_json" not in cols:
        conn.execute("ALTER TABLE test_sessions ADD COLUMN result_json TEXT")


def score_answers(quiz_id: str, answers_by_question: dict, conn) -> dict:
    dims = conn.execute("SELECT * FROM dimensions WHERE quiz_id = ? ORDER BY dimension_id", (quiz_id,)).fetchall()
    tally = {d["dimension_key"]: {"code_a": d["code_a"], "code_b": d["code_b"], "count_a": 0, "count_b": 0} for d in dims}

    answer_signature = 0
    for qid, option_key in answers_by_question.items():
        q_int = int(qid)
        answer_signature += q_int * (ord(option_key) - 64)
        row = conn.execute(
            """
            SELECT o.score_code, d.dimension_key
            FROM options o
            JOIN questions q ON q.question_id = o.question_id
            JOIN dimensions d ON d.dimension_id = q.dimension_id
            WHERE q.question_id = ? AND o.option_key = ?
            """,
            (q_int, option_key),
        ).fetchone()

        if row:
            d_key = row["dimension_key"]
            s_code = row["score_code"]
            if s_code == tally[d_key]["code_a"]:
                tally[d_key]["count_a"] += 1
            elif s_code == tally[d_key]["code_b"]:
                tally[d_key]["count_b"] += 1

    dimension_results = []
    mbti_letters = []
    for idx, d in enumerate(dims):
        d_key = d["dimension_key"]
        cA = tally[d_key]["count_a"]
        cB = tally[d_key]["count_b"]
        code_a = tally[d_key]["code_a"]
        code_b = tally[d_key]["code_b"]
        total = cA + cB

        if total == 0:
            pct_a, pct_b = 50, 50
        else:
            pct_a = round((cA / total) * 100)
            pct_b = 100 - pct_a

        if cA > cB:
            selected = code_a
        elif cB > cA:
            selected = code_b
        else:
            selected = code_a if ((answer_signature + idx) % 2 == 0) else code_b

        desc_row = conn.execute(
            "SELECT result_name, description FROM result_descriptions WHERE quiz_id = ? AND result_code = ?",
            (quiz_id, selected),
        ).fetchone()

        res_info = {"name": "均衡發展型", "description": "在此維度展現高度平衡的特質。"}
        if desc_row:
            res_info = {"name": desc_row["result_name"], "description": desc_row["description"]}

        dimension_results.append({
            "key": d_key,
            "name": d["dimension_name"],
            "code_a": code_a, "count_a": cA, "pct_a": pct_a,
            "code_b": code_b, "count_b": cB, "pct_b": pct_b,
            "selected": selected,
            "description": res_info,
        })
        mbti_letters.append(selected)

    mbti_code = "".join(mbti_letters) if len(mbti_letters) == 4 else "INFJ"
    candidates = ELEMENTS_BY_MBTI.get(mbti_code, ELEMENTS_118)
    assigned_element = candidates[answer_signature % len(candidates)]
    peer_elements = [
        {"num": e["num"], "sym": e["sym"], "eng": e["eng"], "title": e["title"], "desc": e["desc"]}
        for e in candidates if e["num"] != assigned_element["num"]
    ]

    return {
        "answered_count": len(answers_by_question),
        "profile_code": mbti_code,
        "dimensions": dimension_results,
        "assigned_element": assigned_element,
        "peer_elements": peer_elements,
        "notice": "本報告結合四大類題庫光譜與《幻界 118 元素圖鑑》生成。",
    }


def _select_questions_for_group(conn, group_id: int, mode_count: int, exclude_qids: set[int]) -> list[dict]:
    """嚴格在同一個 group_id 的 200 題內隨機抽題（支援精簡 16 題或完整 50 題），並優先避開前次題目。"""
    quizzes = conn.execute(
        "SELECT quiz_id, quiz_title, description FROM quizzes WHERE group_id = ? ORDER BY quiz_id",
        (group_id,),
    ).fetchall()

    all_in_group: list[dict] = []
    for q in quizzes:
        q_id = q["quiz_id"]
        rows = conn.execute(
            "SELECT question_id, question_type, question_text FROM questions WHERE quiz_id = ? ORDER BY question_id",
            (q_id,),
        ).fetchall()
        for r in rows:
            opts = conn.execute(
                "SELECT option_key, option_text FROM options WHERE question_id = ? ORDER BY option_key",
                (r["question_id"],),
            ).fetchall()
            all_in_group.append({
                "quiz_id": q_id,
                "quiz_title": q["quiz_title"],
                "question_id": r["question_id"],
                "question_type": r["question_type"],
                "question_text": r["question_text"],
                "options": [{"key": o["option_key"], "text": o["option_text"]} for o in opts],
            })

    target_count = 16 if mode_count <= 16 else 50
    unseen = [dict(item) for item in all_in_group if item["question_id"] not in exclude_qids]
    seen = [dict(item) for item in all_in_group if item["question_id"] in exclude_qids]

    random.shuffle(unseen)
    random.shuffle(seen)

    # 先從未在上一輪做過的同類題目中隨機抽，若不足再從同類剩餘題目補齊至目標題數
    ordered_pool = unseen + seen
    if target_count <= len(ordered_pool):
        chosen = ordered_pool[:target_count]
    else:
        chosen = list(ordered_pool)
        while len(chosen) < target_count and all_in_group:
            extra = [dict(x) for x in all_in_group]
            random.shuffle(extra)
            for item in extra:
                chosen.append(item)
                if len(chosen) == target_count:
                    break

    random.shuffle(chosen)
    return chosen


class UnifiedGroupQuizHandler(BaseHTTPRequestHandler):
    server_version = "MultiQuizWeb/8.0"

    def log_message(self, format, *args):
        print("[web] " + (format % args))

    def _send_json(self, payload: dict, status: int = 200):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_file(self, file_path: Path):
        if not file_path.exists():
            self.send_error(404, "File not found")
            return
        raw = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send_file(HTML_FILE)
            return

        if parsed.path == "/api/elements":
            self._send_json({"ok": True, "total": len(ELEMENTS_118), "elements": ELEMENTS_118})
            return

        if parsed.path == "/api/quizzes":
            try:
                with connect() as conn:
                    _ensure_columns(conn)
                    quizzes = conn.execute(
                        "SELECT quiz_id, group_id, quiz_title, description FROM quizzes ORDER BY group_id, quiz_id"
                    ).fetchall()
                    self._send_json({"ok": True, "quizzes": [dict(q) for q in quizzes]})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/group-start":
            params = parse_qs(parsed.query)
            group_id = int(params.get("group_id", ["1"])[0])
            mode_count = 16 if int(params.get("count", ["50"])[0]) <= 16 else 50
            exclude_raw = params.get("exclude_qids", [""])[0]
            exclude_qids = {int(x) for x in exclude_raw.split(",") if x.strip().isdigit()}

            try:
                with connect() as conn:
                    _ensure_columns(conn)
                    quizzes = conn.execute(
                        "SELECT quiz_id, quiz_title, description FROM quizzes WHERE group_id = ? ORDER BY quiz_id",
                        (group_id,),
                    ).fetchall()
                    if not quizzes:
                        self._send_json({"ok": False, "message": "找不到對應測驗類別"}, 404)
                        return

                    base_quiz_id = quizzes[0]["quiz_id"]
                    cur = conn.execute(
                        """
                        INSERT INTO test_sessions (quiz_id, group_id, mode_count, status, last_question_index, is_deleted)
                        VALUES (?, ?, ?, 'active', 0, 0)
                        """,
                        (base_quiz_id, group_id, mode_count),
                    )
                    session_id = int(cur.lastrowid)

                    questions = _select_questions_for_group(conn, group_id, mode_count, exclude_qids)
                    conn.execute(
                        "UPDATE test_sessions SET question_order_json = ? WHERE session_id = ?",
                        (json.dumps(questions, ensure_ascii=False), session_id),
                    )

                    self._send_json({
                        "ok": True,
                        "group_id": group_id,
                        "mode_count": mode_count,
                        "session_id": session_id,
                        "base_quiz_id": base_quiz_id,
                        "questions": questions,
                    })
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/sessions":
            try:
                with connect() as conn:
                    _ensure_columns(conn)
                    active_rows = conn.execute(
                        """
                        SELECT s.session_id, s.quiz_id, s.group_id, s.mode_count, s.status,
                               s.last_question_index, s.started_at, s.completed_at, s.result_json,
                               q.quiz_title
                        FROM test_sessions s
                        LEFT JOIN quizzes q ON q.quiz_id = s.quiz_id
                        WHERE s.is_deleted = 0
                        ORDER BY s.session_id DESC
                        """
                    ).fetchall()
                    deleted_rows = conn.execute(
                        """
                        SELECT s.session_id, s.quiz_id, s.group_id, s.mode_count, s.status,
                               s.last_question_index, s.started_at, s.completed_at,
                               q.quiz_title
                        FROM test_sessions s
                        LEFT JOIN quizzes q ON q.quiz_id = s.quiz_id
                        WHERE s.is_deleted = 1
                        ORDER BY s.session_id DESC
                        """
                    ).fetchall()
                    self._send_json({
                        "ok": True,
                        "sessions": [dict(r) for r in active_rows],
                        "deleted_sessions": [dict(r) for r in deleted_rows],
                    })
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/session-resume":
            params = parse_qs(parsed.query)
            sid = params.get("session_id", [""])[0]
            if not sid.isdigit():
                self._send_json({"ok": False, "message": "無效的 session_id"}, 400)
                return
            try:
                with connect() as conn:
                    _ensure_columns(conn)
                    row = conn.execute("SELECT * FROM test_sessions WHERE session_id = ?", (int(sid),)).fetchone()
                    if not row:
                        self._send_json({"ok": False, "message": "找不到紀錄"}, 404)
                        return
                    ans_rows = conn.execute(
                        """
                        SELECT a.question_id, o.option_key
                        FROM answers a
                        JOIN options o ON o.option_id = a.option_id
                        WHERE a.session_id = ?
                        """,
                        (int(sid),),
                    ).fetchall()
                    answers_map = {str(r["question_id"]): r["option_key"] for r in ans_rows}
                    q_list = json.loads(row["question_order_json"] or "[]")
                    self._send_json({
                        "ok": True,
                        "session": dict(row),
                        "questions": q_list,
                        "answers": answers_map,
                    })
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        data = json.loads(raw_body)

        if parsed.path == "/api/save-progress":
            try:
                session_id = int(data["session_id"])
                last_idx = int(data.get("last_question_index", 0))
                answers = data.get("answers", {})
                with connect() as conn:
                    _ensure_columns(conn)
                    for qid, opt_key in answers.items():
                        opt = conn.execute(
                            "SELECT option_id FROM options WHERE question_id = ? AND option_key = ?",
                            (int(qid), opt_key),
                        ).fetchone()
                        if opt:
                            conn.execute(
                                """
                                INSERT INTO answers (session_id, question_id, option_id) VALUES (?, ?, ?)
                                ON CONFLICT(session_id, question_id) DO UPDATE SET option_id = ?
                                """,
                                (session_id, int(qid), opt["option_id"], opt["option_id"]),
                            )
                    conn.execute(
                        "UPDATE test_sessions SET status = 'saved', last_question_index = ? WHERE session_id = ?",
                        (last_idx, session_id),
                    )
                self._send_json({"ok": True, "message": "已儲存作答進度"})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/submit-unified-group":
            try:
                session_id = data.get("session_id")
                base_quiz_id = data.get("base_quiz_id", "cat1_core_taste_soc")
                answers = data.get("answers", {})

                with connect() as conn:
                    _ensure_columns(conn)
                    for qid, opt_key in answers.items():
                        opt = conn.execute(
                            "SELECT option_id FROM options WHERE question_id = ? AND option_key = ?",
                            (int(qid), opt_key),
                        ).fetchone()
                        if opt and session_id:
                            conn.execute(
                                """
                                INSERT INTO answers (session_id, question_id, option_id) VALUES (?, ?, ?)
                                ON CONFLICT(session_id, question_id) DO UPDATE SET option_id = ?
                                """,
                                (int(session_id), int(qid), opt["option_id"], opt["option_id"]),
                            )

                    unified_result = score_answers(base_quiz_id, answers, conn)
                    if session_id:
                        conn.execute(
                            """
                            UPDATE test_sessions
                            SET status = 'completed', completed_at = ?, result_json = ?
                            WHERE session_id = ?
                            """,
                            (
                                datetime.now().isoformat(timespec="seconds"),
                                json.dumps(unified_result, ensure_ascii=False),
                                int(session_id),
                            ),
                        )

                self._send_json({"ok": True, "unified_result": unified_result})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/delete-session":
            try:
                session_id = int(data["session_id"])
                with connect() as conn:
                    _ensure_columns(conn)
                    conn.execute("UPDATE test_sessions SET is_deleted = 1 WHERE session_id = ?", (session_id,))
                self._send_json({"ok": True})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        if parsed.path == "/api/restore-session":
            try:
                session_id = int(data["session_id"])
                with connect() as conn:
                    _ensure_columns(conn)
                    conn.execute("UPDATE test_sessions SET is_deleted = 0 WHERE session_id = ?", (session_id,))
                self._send_json({"ok": True})
            except Exception as exc:
                self._send_json({"ok": False, "message": str(exc)}, 500)
            return

        self.send_error(404)


def main():
    if not DB_FILE.exists():
        from seed_database import init_and_seed
        init_and_seed()

    server = ThreadingHTTPServer((HOST, PORT), UnifiedGroupQuizHandler)
    print("==================================================")
    print(" 幻界 118 元素 × 四大類 800 題深度心理測驗系統已啟動！")
    print(f" 請在瀏覽器開啟：http://{HOST}:{PORT}")
    print("==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已安全停止。")


if __name__ == "__main__":
    main()
