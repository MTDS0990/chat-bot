from flask import Flask, request
import requests
import random
import os

app = Flask(__name__)

API_URL = "https://botapi.rubika.ir/v3"
TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
headers = {
    "Content-Type": "application/json",
    "auth": TOKEN
}

users = {}
waiting_users = []

@app.route('/')
def home():
    return 'ربات آنلاین است ✅'

@app.route('/receiveUpdate', methods=['POST'])
def receive_update():
    data = request.get_json()

    if not data or 'message' not in data:
        return 'no message'

    msg = data['message']
    user_id = msg['from']

    # اگر کاربر جدید است، ثبتش کن
    if user_id not in users:
        users[user_id] = {"status": "none", "gender": None, "partner": None}
        send_keyboard(user_id, "سلام! جنسیتتو انتخاب کن:", [["پسر 👦", "دختر 👧"]])
        return "ok"

    user = users[user_id]
    msg_type = msg.get("type")

    # انتخاب جنسیت
    if user["gender"] is None:
        if msg.get("text") in ["پسر 👦", "دختر 👧"]:
            user["gender"] = msg["text"]
            send_keyboard(user_id, "میخوای با کی چت کنی؟", [["پسر 👦", "دختر 👧", "هر دو 👥"]])
        else:
            send_message(user_id, "لطفاً جنسیتتو انتخاب کن.")
        return "ok"

    # انتخاب ترجیح چت
    if user["status"] == "none":
        if msg.get("text") in ["پسر 👦", "دختر 👧", "هر دو 👥"]:
            user["status"] = "waiting"
            user["preferred"] = msg["text"]
            waiting_users.append(user_id)
            send_message(user_id, "منتظر پیدا شدن چت هستی...")
            match_users()
        else:
            send_message(user_id, "لطفاً یکی از گزینه‌ها رو انتخاب کن.")
        return "ok"

    # اگر در حال چت هستن
    if user["partner"]:
        if msg.get("text") == "❌ پایان چت":
            end_chat(user_id)
            return "ok"

        forward_to_partner(user_id, msg)
        return "ok"

    send_message(user_id, "منتظر پیدا شدن چت هستی...")

    return "ok"

def send_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "type": "text"
    }
    requests.post(f"{API_URL}/sendMessage", headers=headers, json=payload)

def send_keyboard(chat_id, text, keyboard):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "type": "text",
        "inline_keyboard_markup": {
            "rows": [[{"text": btn, "type": "text", "command": btn} for btn in row] for row in keyboard]
        }
    }
    requests.post(f"{API_URL}/sendMessage", headers=headers, json=payload)

def forward_to_partner(user_id, msg):
    partner_id = users[user_id]["partner"]
    new_msg = {
        "chat_id": partner_id,
        "type": msg["type"]
    }

    if msg["type"] == "text":
        new_msg["text"] = msg["text"]
    elif msg["type"] == "file":
        new_msg["file_inline"] = msg["file_inline"]
    else:
        send_message(user_id, "این نوع پیام پشتیبانی نمی‌شود.")
        return

    requests.post(f"{API_URL}/sendMessage", headers=headers, json=new_msg)

def match_users():
    global waiting_users
    matched = []

    for uid in waiting_users:
        if users[uid]["partner"]:
            continue

        for other_id in waiting_users:
            if uid == other_id or users[other_id]["partner"]:
                continue

            # بررسی تطابق ترجیحات
            if users[uid]["preferred"] in [users[other_id]["gender"], "هر دو 👥"] and \
               users[other_id]["preferred"] in [users[uid]["gender"], "هر دو 👥"]:
                users[uid]["partner"] = other_id
                users[other_id]["partner"] = uid
                users[uid]["status"] = "chatting"
                users[other_id]["status"] = "chatting"
                matched.extend([uid, other_id])

                send_keyboard(uid, "شما به چت متصل شدی ✅", [["❌ پایان چت"]])
                send_keyboard(other_id, "شما به چت متصل شدی ✅", [["❌ پایان چت"]])
                break

    # حذف matched ها از لیست انتظار
    waiting_users = [u for u in waiting_users if u not in matched]

def end_chat(user_id):
    partner = users[user_id].get("partner")
    if partner:
        send_message(partner, "طرف مقابل چت را ترک کرد ❌")
        users[partner]["partner"] = None
        users[partner]["status"] = "waiting"
        waiting_users.append(partner)

    users[user_id]["partner"] = None
    users[user_id]["status"] = "waiting"
    waiting_users.append(user_id)

    send_message(user_id, "چت پایان یافت ❌")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
