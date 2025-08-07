from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
API_URL = f"https://botapi.rubika.ir/v3/bot{BOT_TOKEN}"

users = {}
chats = {}

@app.route('/')
def home():
    return "ربات چت ناشناس فعال است!"

@app.route('/receiveUpdate', methods=['POST'])
def receive_update():
    data = request.json
    print("📥 پیام دریافت شد:", data)

    try:
        update = data.get("update", {})
        msg = update.get("new_message")
        chat_id = update.get("chat_id")
        sender_id = msg["sender_id"]
        text = msg.get("text", "")
        file_inline = msg.get("file_inline")

        if sender_id not in users:
            users[sender_id] = {"state": "ask_gender"}
            return send_message(chat_id, "🌸 به چت ناشناس خوش اومدی!\n\nلطفاً جنسیت خودت رو مشخص کن:", [
                ["👦 پسر", "👧 دختر"]
            ])

        user = users[sender_id]
        state = user["state"]

        if state == "ask_gender":
            if text in ["👦 پسر", "👧 دختر"]:
                user["gender"] = "male" if text == "👦 پسر" else "female"
                user["state"] = "choose_target"
                return send_message(chat_id, "میخوای با چه کسی چت کنی؟", [
                    ["👦 پسر", "👧 دختر"],
                    ["🆗 فرقی نداره"]
                ])
            else:
                return send_message(chat_id, "لطفاً جنسیت خودتو با دکمه مشخص کن.")

        elif state == "choose_target":
            if text in ["👦 پسر", "👧 دختر", "🆗 فرقی نداره"]:
                user["target"] = text
                user["state"] = "waiting"
                return try_connect(sender_id, chat_id)
            else:
                return send_message(chat_id, "یکی از گزینه‌ها رو انتخاب کن.")

        elif state == "chatting":
            partner_id = chats.get(sender_id)
            if text == "❌ پایان چت":
                end_chat(sender_id, partner_id)
                return send_message(chat_id, "✅ چت پایان یافت.")
            else:
                forward_message(partner_id, text, file_inline)
                return "", 200

        elif state == "waiting":
            return send_message(chat_id, "⏳ منتظر اتصال به کاربر دیگر هستی...")

    except Exception as e:
        print("❌ خطا در پردازش:", e)

    return "", 200

def try_connect(user_id, chat_id):
    gender = users[user_id]["gender"]
    target = users[user_id]["target"]
    
    for uid, info in users.items():
        if uid != user_id and info["state"] == "waiting":
            if target == "🆗 فرقی نداره" or \
               (target == "👦 پسر" and info["gender"] == "male") or \
               (target == "👧 دختر" and info["gender"] == "female"):
                if info["target"] == "🆗 فرقی نداره" or \
                   (info["target"] == "👦 پسر" and gender == "male") or \
                   (info["target"] == "👧 دختر" and gender == "female"):
                    
                    users[user_id]["state"] = "chatting"
                    users[uid]["state"] = "chatting"
                    chats[user_id] = uid
                    chats[uid] = user_id
                    send_message(chat_id, "🎉 به یک کاربر وصل شدی!\nبرای پایان چت دکمه زیر رو بزن.", [["❌ پایان چت"]])
                    send_message(get_chat_id(uid), "🎉 به یک کاربر وصل شدی!\nبرای پایان چت دکمه زیر رو بزن.", [["❌ پایان چت"]])
                    return "", 200
    return send_message(chat_id, "⏳ منتظر اتصال به کاربر دیگر هستی...")

def end_chat(user1, user2):
    for uid in [user1, user2]:
        if uid in users:
            users[uid]["state"] = "ask_gender"
            users[uid].pop("target", None)
            chats.pop(uid, None)
            send_message(get_chat_id(uid), "❌ چت به پایان رسید. برای شروع دوباره /start رو بزن.")

def forward_message(to_id, text, file_inline=None):
    chat_id = get_chat_id(to_id)
    payload = {
        "chat_id": chat_id,
        "text": text or "",
    }
    if file_inline:
        payload["file_inline"] = file_inline
    requests.post(f"{API_URL}/sendMessage", json=payload)

def send_message(chat_id, text, buttons=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if buttons:
        payload["btn_list"] = [{"row": [{"text": b} for b in row]} for row in buttons]
    requests.post(f"{API_URL}/sendMessage", json=payload)

def get_chat_id(user_id):
    for cid, info in users.items():
        if cid == user_id:
            return user_id  # چون chat_id با user_id یکیه در پیام جدید

# پورت سازگار با Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
