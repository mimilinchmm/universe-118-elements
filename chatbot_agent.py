# -*- coding: utf-8 -*-
"""幻界元素心理測驗聊天機器人後端：支援 16 題/50 題需求判斷、專屬測驗按鈕與自由聊天。"""
from __future__ import annotations

import json
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8001

LINKS = [
    {"label": "外部 200 題人格測驗參考", "url": "https://m.psyctest.cn/q/Vm5baaG6/"},
    {"label": "外部注意力/特質測驗參考", "url": "https://app.raadstest.com/tw/autism/raadsr"},
]


def decide_quiz_plan(msg: str) -> tuple[int, int, str]:
    """依使用者需求回傳 (group_id, question_count, mode_desc)。"""
    short_hints = ["精簡", "稍微", "隨便", "簡單", "快速", "練習", "15", "16", "十五", "十六", "先看看", "大概"]
    full_hints = ["完整", "50", "五十", "深度", "詳細", "仔細", "全部"]

    if any(k in msg for k in short_hints):
        q_count = 16
        mode_desc = "精簡版（16 題）"
    elif any(k in msg for k in full_hints):
        q_count = 50
        mode_desc = "完整版（50 題）"
    else:
        q_count = 50
        mode_desc = "完整版（50 題）"

    if any(k in msg for k in ["第二類", "職涯", "職業", "工作", "學習", "專注", "創意", "創作", "靈感"]):
        group_id = 2
    elif any(k in msg for k in ["第三類", "情緒", "覺察", "親密", "情感", "愛情", "溝通", "互動", "社交"]):
        group_id = 3
    elif any(k in msg for k in ["第四類", "抗壓", "復原", "壓力", "危機", "應變", "決策", "領導", "管理"]):
        group_id = 4
    else:
        group_id = 1

    return group_id, q_count, mode_desc


def generate_chat_reply(message: str) -> dict:
    msg = message.strip()
    if not msg:
        return {
            "reply": (
                "你可以跟我自由聊天，也可以告訴我你的測驗需求（例如：「我想做精簡版 16 題」或「我想做完整版 50 題」）。"
            ),
            "recommended_group": None,
            "question_count": None,
            "button_text": None,
            "links": LINKS,
        }

    test_triggers = [
        "測驗", "題目", "人格", "特質", "性格", "口味", "社交",
        "職涯", "工作", "專注", "創意", "情緒", "親密", "溝通",
        "抗壓", "壓力", "危機", "決策", "領導", "精簡", "完整",
        "16", "50", "十六", "五十", "元素", "本命", "第一類", "第二類", "第三類", "第四類"
    ]

    if any(k in msg for k in test_triggers):
        group_id, q_count, mode_desc = decide_quiz_plan(msg)
        group_names = {
            1: "第一類：核心行為風格 × 特質視角 × 口味與社交偏好",
            2: "第二類：探索職涯興趣 × 專注模式與創造動能",
            3: "第三類：解析情緒覺察 × 親密表達與溝通社交互動",
            4: "第四類：抗壓復原力 × 危機應變與決策領導節奏",
        }
        return {
            "reply": (
                f"依照你的需求，我為你準備了**「{mode_desc}」**，對應**「{group_names[group_id]}」**（每次作答皆在同類 200 題內隨機抽題，並自動避開前一次題目）。\n"
                "點擊下方按鈕即可直接開始，你也可以在聊天框切換精簡版或完整版："
            ),
            "recommended_group": group_id,
            "question_count": q_count,
            "button_text": f"✨ 開始 {mode_desc}測驗",
            "links": LINKS,
        }

    free_chat_replies = [
        f"聽起來你提到「{msg}」！不管你想聊聊今天的心情、生活小事，還是想分享最近的想法，我都在這裡陪你聊。",
        f"關於「{msg}」，我很樂意聽你多說一點！你現在比較想輕鬆聊聊，還是想順便測測看自己的幻界 118 元素本命呢？",
        f"「{msg}」聽起來很有意思呢！你可以自在地和我聊天，如果想開始測驗，只要說「精簡版 16 題」或「完整版 50 題」就能立刻開測。",
    ]
    return {
        "reply": random.choice(free_chat_replies),
        "recommended_group": None,
        "question_count": None,
        "button_text": None,
        "links": LINKS,
    }


class ChatBotHandler(BaseHTTPRequestHandler):
    server_version = "ChatBotAgent/5.0"

    def log_message(self, format, *args):
        print("[chat_bot] " + (format % args))

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

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/api/chat"):
            self._send_json({"ok": True, "message": "🤖 幻界元素聊天機器人 API 運行中！"})
            return
        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                res_data = generate_chat_reply(data.get("message", ""))
                self._send_json({"ok": True, **res_data})
            except Exception as exc:
                self._send_json({"ok": False, "reply": f"系統發生錯誤: {str(exc)}"}, 500)
            return
        self.send_error(404)


def main():
    server = ThreadingHTTPServer((HOST, PORT), ChatBotHandler)
    print("==================================================")
    print(" 🤖 幻界元素諮詢聊天機器人後端已啟動！")
    print(f" 聊天 API 位址：http://{HOST}:{PORT}/api/chat")
    print("==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n聊天機器人伺服器已安全停止。")


if __name__ == "__main__":
    main()
