# -*- coding: utf-8 -*-
"""從壓縮檔或解壓後的「題庫」資料夾讀取四大類各 200 題（共 800 題），建立 SQLite 資料庫。"""
from __future__ import annotations

import re
import sqlite3
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "personality_test.db"
ZIP_FILE = BASE_DIR / "題庫.zip"
BANK_DIR = BASE_DIR / "題庫"

CATEGORIES_META = [
    (
        "cat1_core_taste_soc",
        1,
        "第一類：核心行為風格 × 特質視角 × 口味與社交偏好",
        "涵蓋日常行為慣性、人格特質視角、飲食口味偏好與社交互動節奏（題庫 200 題，不混跨類別）。",
    ),
    (
        "cat2_career_focus_creat",
        2,
        "第二類：探索職涯興趣 × 專注模式與創造動能",
        "聚焦職涯方向探索、專注與任務切換模式、靈感發想與創造動能（題庫 200 題，不混跨類別）。",
    ),
    (
        "cat3_emot_intim_comm",
        3,
        "第三類：解析情緒覺察 × 親密表達與溝通社交互動",
        "深入解析情緒辨識與覺察、親密關係與情感表達、日常溝通與人際互動模式（題庫 200 題，不混跨類別）。",
    ),
    (
        "cat4_resil_crisis_lead",
        4,
        "第四類：抗壓復原力 × 危機應變與決策領導節奏",
        "涵蓋高壓復原與回血策略、突發危機應變、決策取捨與團隊領導節奏（題庫 200 題，不混跨類別）。",
    ),
]

DOCX_NAME_BY_GROUP = {
    1: "第一類.docx",
    2: "第二類.docx",
    3: "第三類.docx",
    4: "第四類.docx",
}


def _extract_paragraphs_from_docx_bytes(docx_bytes: bytes) -> list[str]:
    import io

    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as dz:
        xml_content = dz.read("word/document.xml")
    tree = ET.fromstring(xml_content)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paras: list[str] = []
    for p in tree.findall(".//w:p", ns):
        texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
        line = "".join(texts).strip()
        if line:
            paras.append(line)
    return paras


def _load_raw_paragraphs(group_id: int) -> list[str]:
    fname = DOCX_NAME_BY_GROUP[group_id]
    direct_path = BANK_DIR / fname
    if direct_path.exists():
        return _extract_paragraphs_from_docx_bytes(direct_path.read_bytes())

    if ZIP_FILE.exists():
        with zipfile.ZipFile(ZIP_FILE, "r") as zf:
            for member in zf.namelist():
                if member.endswith(f"/{fname}") or member == fname:
                    return _extract_paragraphs_from_docx_bytes(zf.read(member))

    raise FileNotFoundError(f"找不到第 {group_id} 類題庫檔案（{fname}），請確認「題庫」資料夾或「題庫.zip」存在。")


def _infer_score_code(dim_key: str, opt_idx: int, total_opts: int) -> str:
    """依題目維度與選項位置對應 E/I、S/N、T/F、J/P 得分代碼，確保各維度具備雙向光譜鑑別度。"""
    pair_map = {
        "DIM_1": ("E", "I"),
        "DIM_2": ("S", "N"),
        "DIM_3": ("T", "F"),
        "DIM_4": ("J", "P"),
    }
    code_a, code_b = pair_map.get(dim_key, ("E", "I"))
    if total_opts == 2:
        return code_a if opt_idx == 0 else code_b
    if total_opts == 3:
        if opt_idx == 0:
            return code_a
        if opt_idx == 1:
            return code_b
        return code_a if dim_key in ("DIM_1", "DIM_3") else code_b
    # 4 選 1：A/C 偏 code_a，B/D 偏 code_b
    return code_a if opt_idx in (0, 2) else code_b


def parse_group_questions_from_bank(group_id: int) -> list[tuple[str, str, str, list[tuple[str, str]]]]:
    paras = _load_raw_paragraphs(group_id)
    code_re = re.compile(r"^(C[1-4]-\d{3})-(2O|3O|4O)-([A-Z0-9_]+)$")
    opt_re = re.compile(r"^([A-D])\.\s*(.+)$")

    parsed_items: list[dict] = []
    cur: dict | None = None
    i = 0
    while i < len(paras):
        line = paras[i]
        normalized_line = line.replace("C4-0108-4O-LEAD -> C4-108-4O-LEAD", "C4-108-4O-LEAD")
        m = code_re.match(normalized_line)
        if m:
            if cur:
                parsed_items.append(cur)
            q_code, q_opt_cnt, q_tag = m.groups()
            q_type = {"2O": "2選1", "3O": "3選1", "4O": "4選1"}[q_opt_cnt]
            q_text = paras[i + 1] if i + 1 < len(paras) else ""
            opts: list[tuple[str, str]] = []
            seen_keys: set[str] = set()
            j = i + 2
            while j < len(paras):
                cand = paras[j].replace("C4-0108-4O-LEAD -> C4-108-4O-LEAD", "C4-108-4O-LEAD")
                if code_re.match(cand) or cand.startswith(("第", "題型分佈", "去重檢核狀態")):
                    break
                om = opt_re.match(cand)
                if om:
                    okey = om.group(1)
                    otext = om.group(2).strip()
                    if okey not in seen_keys:
                        seen_keys.add(okey)
                        opts.append((okey, otext))
                j += 1
            cur = {
                "code": q_code,
                "type": q_type,
                "tag": q_tag,
                "text": q_text,
                "opts": opts,
            }
            i = j
        else:
            i += 1
    if cur:
        parsed_items.append(cur)

    # 依題號排序並確保每類恰好 200 題不重複
    parsed_items.sort(key=lambda x: x["code"])
    unique_by_code: dict[str, dict] = {}
    for item in parsed_items:
        if item["code"] not in unique_by_code:
            unique_by_code[item["code"]] = item
    ordered = list(unique_by_code.values())[:200]

    dim_cycle = ["DIM_1", "DIM_2", "DIM_3", "DIM_4"]
    output: list[tuple[str, str, str, list[tuple[str, str]]]] = []
    for idx, q in enumerate(ordered):
        dim_key = dim_cycle[idx % 4]
        raw_opts = [text for _, text in q["opts"]]
        scored_opts = [
            (opt_text, _infer_score_code(dim_key, o_idx, len(raw_opts)))
            for o_idx, opt_text in enumerate(raw_opts)
        ]
        display_text = f"[{q['code']}・{q['tag']}] {q['text']}"
        output.append((dim_key, q["type"], display_text, scored_opts))

    if len(output) != 200:
        raise ValueError(f"第 {group_id} 類題庫解析數量為 {len(output)} 題，預期為 200 題。")

    return output


def generate_quiz_data(quiz_id: str, group_id: int):
    dimensions = [
        {"key": "DIM_1", "name": "能量維度 (外向 E / 內向 I)", "code_a": "E", "code_b": "I", "description": "E：外向互動充電；I：內向獨處沉澱。"},
        {"key": "DIM_2", "name": "認知與感官維度 (實感 S / 直覺 N)", "code_a": "S", "code_b": "N", "description": "S：重視具體細節與實務；N：重視抽象概念、靈感與跳躍聯想。"},
        {"key": "DIM_3", "name": "決策維度 (思考 T / 情感 F)", "code_a": "T", "code_b": "F", "description": "T：邏輯客觀與效率；F：同理共情與和諧。"},
        {"key": "DIM_4", "name": "生活與執行節奏維度 (判斷 J / 感知 P)", "code_a": "J", "code_b": "P", "description": "J：結構計畫與秩序；P：彈性應變與靈活節奏。"},
    ]

    questions = parse_group_questions_from_bank(group_id)

    results = [
        ("E", "外向共振者 (Extraversion)", "善於從外部互動、交流與感官體驗中汲取能量與行動力。"),
        ("I", "內省深潛者 (Introversion)", "擁有豐富的精神內核，擅長在安靜與獨立思考中沉澱。"),
        ("S", "務實構築者 (Sensing)", "腳踏實地、觀察入微，擅長掌握具體細節、口味與穩定執行。"),
        ("N", "星軌遠見者 (Intuition)", "想像力馳騁於未來與宏觀規律，善於捕捉靈感與關聯。"),
        ("T", "理性裁決者 (Thinking)", "以冷靜客觀的邏輯剖析問題，堅守原則與效率。"),
        ("F", "共情治癒者 (Feeling)", "具備細膩的同理心與溫度，重視人際和諧與情感連結。"),
        ("J", "秩序領航者 (Judging)", "擅長規劃藍圖與掌控節奏，重視秩序與明確方向。"),
        ("P", "自由探索者 (Perceiving)", "擁抱變化與無限可能，在靈活應變中展現彈性。"),
    ]
    return dimensions, questions, results


SCHEMA = """
CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id TEXT PRIMARY KEY,
    group_id INTEGER NOT NULL DEFAULT 1,
    quiz_title TEXT NOT NULL,
    description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dimensions (
    dimension_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,
    dimension_key TEXT NOT NULL,
    dimension_name TEXT NOT NULL,
    code_a TEXT NOT NULL,
    code_b TEXT NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id),
    UNIQUE(quiz_id, dimension_key)
);
CREATE TABLE IF NOT EXISTS questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,
    dimension_id INTEGER NOT NULL,
    question_type TEXT NOT NULL DEFAULT '4選1',
    question_text TEXT NOT NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id),
    FOREIGN KEY (dimension_id) REFERENCES dimensions(dimension_id)
);
CREATE TABLE IF NOT EXISTS options (
    option_id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    option_key TEXT NOT NULL CHECK(option_key IN ('A','B','C','D')),
    option_text TEXT NOT NULL,
    score_code TEXT NOT NULL,
    UNIQUE(question_id, option_key),
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
);
CREATE TABLE IF NOT EXISTS test_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,
    group_id INTEGER NOT NULL DEFAULT 1,
    mode_count INTEGER NOT NULL DEFAULT 200,
    status TEXT NOT NULL DEFAULT 'active',
    last_question_index INTEGER NOT NULL DEFAULT 0,
    question_order_json TEXT NOT NULL DEFAULT '[]',
    result_json TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
);
CREATE TABLE IF NOT EXISTS answers (
    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,
    UNIQUE(session_id, question_id),
    FOREIGN KEY (session_id) REFERENCES test_sessions(session_id),
    FOREIGN KEY (question_id) REFERENCES questions(question_id),
    FOREIGN KEY (option_id) REFERENCES options(option_id)
);
CREATE TABLE IF NOT EXISTS result_descriptions (
    quiz_id TEXT NOT NULL,
    result_code TEXT NOT NULL,
    result_name TEXT NOT NULL,
    description TEXT NOT NULL,
    PRIMARY KEY(quiz_id, result_code),
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_and_seed() -> None:
    with connect() as conn:
        conn.execute("DROP TABLE IF EXISTS answers")
        conn.execute("DROP TABLE IF EXISTS test_sessions")
        conn.execute("DROP TABLE IF EXISTS options")
        conn.execute("DROP TABLE IF EXISTS questions")
        conn.execute("DROP TABLE IF EXISTS result_descriptions")
        conn.execute("DROP TABLE IF EXISTS dimensions")
        conn.execute("DROP TABLE IF EXISTS quizzes")
        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM answers")
        conn.execute("DELETE FROM test_sessions")
        conn.execute("DELETE FROM options")
        conn.execute("DELETE FROM questions")
        conn.execute("DELETE FROM result_descriptions")
        conn.execute("DELETE FROM dimensions")
        conn.execute("DELETE FROM quizzes")

        total_q = 0
        for q_id, g_id, q_title, q_desc in CATEGORIES_META:
            conn.execute(
                "INSERT INTO quizzes (quiz_id, group_id, quiz_title, description) VALUES (?, ?, ?, ?)",
                (q_id, g_id, q_title, q_desc),
            )
            dimensions, questions, results = generate_quiz_data(q_id, g_id)

            dim_map = {}
            for dim in dimensions:
                cur = conn.execute(
                    "INSERT INTO dimensions(quiz_id, dimension_key, dimension_name, code_a, code_b, description) VALUES (?,?,?,?,?,?)",
                    (q_id, dim["key"], dim["name"], dim["code_a"], dim["code_b"], dim["description"]),
                )
                dim_map[dim["key"]] = cur.lastrowid

            for dim_key, q_type, q_text, opts in questions:
                cur_q = conn.execute(
                    "INSERT INTO questions(quiz_id, dimension_id, question_type, question_text) VALUES (?, ?, ?, ?)",
                    (q_id, dim_map[dim_key], q_type, q_text),
                )
                q_db_id = cur_q.lastrowid
                total_q += 1
                for opt_key, (opt_text, s_code) in zip("ABCD", opts):
                    conn.execute(
                        "INSERT INTO options(question_id, option_key, option_text, score_code) VALUES (?, ?, ?, ?)",
                        (q_db_id, opt_key, opt_text, s_code),
                    )

            for r_code, r_name, r_desc in results:
                conn.execute(
                    "INSERT INTO result_descriptions VALUES (?, ?, ?, ?)",
                    (q_id, r_code, r_name, r_desc),
                )

    print(f"資料庫初始化完成！四大類各 200 題、總計 {total_q} 題不重複題目：{DB_FILE}")


if __name__ == "__main__":
    init_and_seed()
