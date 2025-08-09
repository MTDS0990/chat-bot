from flask import Flask, request
import requests

app = Flask(__name__)

API_URL = "https://botapi.rubika.ir/v3"
BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"

# ذخیره وضعیت کاربران
users = {}  # chat_id -> {gender, target_gender, partner_id}

def send_message(chat_id, text, btn=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if btn:
        payload["inline_markup"] = {
            "rows": [[{"text": b, "command": b}] for b in btn]
        }
    res = requests.post(f"{API_URL}/message/send", json=payload)
    print("📤", res.text)

def forward_file(file_id, to_chat):
    payload = {
        "chat_id": to_chat,
        "file_inline": file_id
    }
    requests.post(f"{API_URL}/message/send", json=payload)

@app.route("/")
def home():
    return "ربات فعال است!"

@app.route("/receiveUpdate", methods=["POST"])
def receive_update():
    update = request.json.get("update")
    print("📥", update)

    if update.get("type") == "NewMessage":
        chat_id = update.get("chat_id")
        msg_data = update.get("new_message", {})
        text = msg_data.get("text", "")
        file_id = msg_data.get("file_inline", "")

        # اگر کاربر شریک چت دارد، پیام یا فایل را فوروارد کن
        if chat_id in users and users[chat_id].get("partner_id"):
            partner = users[chat_id]["partner_id"]
            if file_id:
                forward_file(file_id, partner)
            elif text:
                send_message(partner, text)
            return "OK"

        # مرحله 1: استارت
        if text == "/start":
            users[chat_id] = {"gender": None, "target_gender": None, "partner_id": None}
            send_message(chat_id, "سلام! لطفا جنسیت خود را انتخاب کنید:", ["👩 دختر", "👨 پسر"])
            return "OK"

        # مرحله 2: انتخاب جنسیت کاربر
        if text in ["👩 دختر", "👨 پسر"]:
            users[chat_id]["gender"] = text
            send_message(chat_id, "میخوای چت رو شروع کنیم؟", ["🚀 شروع چت"])
            return "OK"

        # مرحله 3: انتخاب جنسیت طرف مقابل
        if text == "🚀 شروع چت":
            send_message(chat_id, "دوست داری با چه کسی چت کنی؟", ["👩 دختر", "👨 پسر", "🎯 فرقی نداره"])
            return "OK"

        if text in ["👩 دختر", "👨 پسر", "🎯 فرقی نداره"] and users[chat_id].get("gender"):
            users[chat_id]["target_gender"] = text
            # جستجوی کاربر مناسب
            for uid, info in users.items():
                if uid != chat_id and info["partner_id"] is None:
                    if info["gender"] == text or text == "🎯 فرقی نداره" or info["target_gender"] == "🎯 فرقی نداره":
                        users[chat_id]["partner_id"] = uid
                        users[uid]["partner_id"] = chat_id
                        send_message(chat_id, "✅ به یک نفر وصل شدید! می‌توانید چت کنید.", ["❌ پایان چت"])
                        send_message(uid, "✅ به یک نفر وصل شدید! می‌توانید چت کنید.", ["❌ پایان چت"])
                        return "OK"
            send_message(chat_id, "⏳ در حال جستجوی یک نفر...")
            return "OK"

        # پایان چت
        if text == "❌ پایان چت":
            partner = users[chat_id].get("partner_id")
            if partner:
                send_message(partner, "❌ طرف مقابل چت را پایان داد.", ["🚀 شروع چت"])
                users[partner]["partner_id"] = None
            users[chat_id]["partner_id"] = None
            send_message(chat_id, "چت پایان یافت.", ["🚀 شروع چت"])
            return "OK"

    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0")
