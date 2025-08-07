from flask import Flask, request
import requests

app = Flask(__name__)

# 🔐 توکن واقعی شما از @anon_chat_bot
TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
API_URL = f"https://messengerg2c37.iranl.ms/bot{TOKEN}/"

users = {}  # user_id: {"gender": "پسر/دختر", "target": "پسر/دختر/فرقی نداره", "partner": None}

@app.route("/")
def home():
    return "ربات فعال است!"

@app.route("/receiveUpdate", methods=["POST"])
def receive_update():
    try:
        data = request.json
        message = data["update"]["new_message"]
        user_id = message["sender_id"]
        text = message.get("text", "")

        if user_id not in users:
            users[user_id] = {"gender": None, "target": None, "partner": None}

        user = users[user_id]

        if text == "/start":
            send_message(user_id, "سلام! برای شروع، جنسیت خودت رو انتخاب کن:", [
                {"text": "دختر 👧", "callback_data": "gender:دختر"},
                {"text": "پسر 👦", "callback_data": "gender:پسر"}
            ])

        elif text == "/end":
            partner = user["partner"]
            if partner:
                send_message(partner, "❗️طرف مقابل چت رو ترک کرد.")
                users[partner]["partner"] = None
            users[user_id]["partner"] = None
            send_message(user_id, "چت تموم شد. برای شروع دوباره /start رو بزن.")

        elif user["partner"]:
            # ارسال پیام به طرف مقابل
            send_message(user["partner"], text)

    except Exception as e:
        print("❌ خطا در پردازش:", e)
    return ""

@app.route("/receiveCallback", methods=["POST"])
def receive_callback():
    try:
        data = request.json
        callback = data["update"]["callback_query"]
        user_id = callback["sender"]["user_id"]
        data_text = callback["data"]

        if user_id not in users:
            users[user_id] = {"gender": None, "target": None, "partner": None}

        user = users[user_id]

        if data_text.startswith("gender:"):
            gender = data_text.split(":")[1]
            user["gender"] = gender
            send_message(user_id, "میخوای با چه جنسیتی چت کنی؟", [
                {"text": "پسر 👦", "callback_data": "target:پسر"},
                {"text": "دختر 👧", "callback_data": "target:دختر"},
                {"text": "فرقی نداره 🙃", "callback_data": "target:فرقی نداره"}
            ])

        elif data_text.startswith("target:"):
            target = data_text.split(":")[1]
            user["target"] = target
            find_partner(user_id)

    except Exception as e:
        print("❌ خطا در کال‌بک:", e)
    return ""

def find_partner(user_id):
    user = users[user_id]
    for uid, u in users.items():
        if uid != user_id and not u["partner"]:
            if u["gender"] and u["target"] and user["gender"] and user["target"]:
                match = (
                    (user["target"] == u["gender"] or user["target"] == "فرقی نداره") and
                    (u["target"] == user["gender"] or u["target"] == "فرقی نداره")
                )
                if match:
                    user["partner"] = uid
                    u["partner"] = user_id
                    send_message(user_id, "🎉 یه نفر پیدا شد! شروع کن به چت 🗨")
                    send_message(uid, "🎉 یه نفر پیدا شد! شروع کن به چت 🗨")
                    return
    send_message(user_id, "⏳ در حال جستجو برای فرد مناسب...")

def send_message(chat_id, text, buttons=None):
    data = {
        "chat_id": chat_id,
        "text": text,
    }
    if buttons:
        data["reply_markup"] = {
            "inline_keyboard": [[button] for button in buttons]
        }
    requests.post(API_URL + "sendMessage", json=data)
