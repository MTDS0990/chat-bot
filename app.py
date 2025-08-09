from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_URL = "https://botapi.rubika.ir/v3"
BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"

# ذخیره اطلاعات کاربران در حافظه
users = {}
chats = {}

def send_message(chat_id, text, buttons=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if buttons:
        data["inline_markup"] = {"rows": [[{"text": btn, "command": btn}] for btn in buttons]}
    requests.post(f"{API_URL}/message/send?token={BOT_TOKEN}", json=data)

def forward_file(chat_id, file_id):
    requests.post(f"{API_URL}/message/forward?token={BOT_TOKEN}", json={
        "chat_id": chat_id,
        "file_inline": file_id
    })

@app.route("/", methods=["GET"])
def home():
    return "ربات فعال است ✅"

@app.route("/receiveUpdate", methods=["POST"])
def receive_update():
    update = request.json.get("update", {})
    print("📥 پیام جدید:", update)

    if update.get("type") == "NewMessage":
        chat_id = update["chat_id"]
        message = update["new_message"]

        text = message.get("text", "")
        file_inline = message.get("file_inline")

        # اگر فایل (عکس/ویس) باشد
        if file_inline:
            if chat_id in chats:
                forward_file(chats[chat_id], file_inline)
            return jsonify({"status": "OK"})

        # مرحله شروع
        if text == "/start":
            users[chat_id] = {"step": "choose_gender"}
            send_message(chat_id, "🌸 سلام! لطفا جنسیت خود را انتخاب کنید:", ["👩 دختر", "👨 پسر"])
            return jsonify({"status": "OK"})

        # انتخاب جنسیت کاربر
        if users.get(chat_id, {}).get("step") == "choose_gender" and text in ["👩 دختر", "👨 پسر"]:
            users[chat_id]["gender"] = text
            users[chat_id]["step"] = "choose_target"
            send_message(chat_id, "با چه کسی دوست داری چت کنی؟", ["👩 دختر", "👨 پسر", "❌ فرقی نداره"])
            return jsonify({"status": "OK"})

        # انتخاب جنسیت طرف مقابل
        if users.get(chat_id, {}).get("step") == "choose_target" and text in ["👩 دختر", "👨 پسر", "❌ فرقی نداره"]:
            users[chat_id]["target"] = text
            users[chat_id]["step"] = "waiting"
            send_message(chat_id, "🔍 در حال جستجوی یک هم‌صحبت مناسب...", ["❌ پایان چت"])
            match_users()
            return jsonify({"status": "OK"})

        # پایان چت
        if text == "❌ پایان چت":
            end_chat(chat_id)
            return jsonify({"status": "OK"})

        # ارسال پیام بین دو نفر
        if chat_id in chats:
            partner = chats[chat_id]
            send_message(partner, text)
            return jsonify({"status": "OK"})

    return jsonify({"status": "INVALID_INPUT"})

def match_users():
    waiting_users = [uid for uid, info in users.items() if info.get("step") == "waiting"]
    while len(waiting_users) >= 2:
        u1 = waiting_users.pop(0)
        u2 = waiting_users.pop(0)
        chats[u1] = u2
        chats[u2] = u1
        users[u1]["step"] = "chatting"
        users[u2]["step"] = "chatting"
        send_message(u1, "✅ شما به یک کاربر وصل شدید! شروع کنید...")
        send_message(u2, "✅ شما به یک کاربر وصل شدید! شروع کنید...")

def end_chat(chat_id):
    if chat_id in chats:
        partner = chats.pop(chat_id)
        chats.pop(partner, None)
        users[chat_id]["step"] = "choose_gender"
        users[partner]["step"] = "choose_gender"
        send_message(chat_id, "❌ چت پایان یافت. دوباره شروع کنید:", ["👩 دختر", "👨 پسر"])
        send_message(partner, "❌ چت پایان یافت. دوباره شروع کنید:", ["👩 دختر", "👨 پسر"])

if __name__ == "__main__":
    app.run(host="0.0.0.0")
