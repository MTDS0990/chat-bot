from flask import Flask, request
import requests

app = Flask(__name__)

API_URL = "https://botapi.rubika.ir/v3"
BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"

users = {}  # ذخیره اطلاعات کاربر {chat_id: {"gender":..., "target":..., "partner":...}}

def send_message(chat_id, text, buttons=None):
    data = {"chat_id": chat_id, "text": text}
    if buttons:
        data["inline_markup"] = {
            "rows": [[{"text": btn, "command": btn}] for btn in buttons]
        }
    requests.post(f"{API_URL}/message/send", json=data)

def send_file(chat_id, file_id, file_type):
    requests.post(f"{API_URL}/message/send", json={
        "chat_id": chat_id,
        "file_inline": {"file_id": file_id, "type": file_type}
    })

def match_users():
    waiting_users = [uid for uid, info in users.items() if not info.get("partner") and info.get("target")]
    for uid in waiting_users:
        for other_uid in waiting_users:
            if uid != other_uid and not users[other_uid].get("partner"):
                if users[uid]["target"] in [users[other_uid]["gender"], "فرقی نداره"] and \
                   users[other_uid]["target"] in [users[uid]["gender"], "فرقی نداره"]:
                    users[uid]["partner"] = other_uid
                    users[other_uid]["partner"] = uid
                    send_message(uid, "✅ شما به یک کاربر وصل شدید! حالا می‌توانید چت کنید.", ["پایان چت"])
                    send_message(other_uid, "✅ شما به یک کاربر وصل شدید! حالا می‌توانید چت کنید.", ["پایان چت"])
                    return

@app.route('/')
def home():
    return 'ربات فعال است!'

@app.route('/receiveUpdate', methods=['POST'])
def receive_update():
    update = request.json.get("update", {})
    if update.get("type") == "NewMessage":
        chat_id = update["chat_id"]
        msg = update["new_message"].get("text", "")
        file_id = update["new_message"].get("file_id")
        file_type = update["new_message"].get("type")

        # ثبت کاربر در دیتابیس
        if chat_id not in users:
            users[chat_id] = {"gender": None, "target": None, "partner": None}

        # اگر در حال چت هست
        if users[chat_id].get("partner"):
            partner = users[chat_id]["partner"]
            if msg == "پایان چت":
                send_message(chat_id, "❌ چت پایان یافت.")
                send_message(partner, "❌ طرف مقابل چت را پایان داد.")
                users[chat_id]["partner"] = None
                users[partner]["partner"] = None
            else:
                if file_id and file_type in ["Image", "Voice"]:
                    send_file(partner, file_id, file_type)
                elif msg:
                    send_message(partner, msg)
            return "OK"

        # منوهای اصلی
        if msg == "/start":
            send_message(chat_id, "👋 سلام! جنسیت خود را انتخاب کنید:", ["دختر", "پسر"])
        elif msg in ["دختر", "پسر"]:
            users[chat_id]["gender"] = msg
            send_message(chat_id, "حالا روی دکمه شروع چت بزن:", ["شروع چت"])
        elif msg == "شروع چت":
            send_message(chat_id, "می‌خواهید با چه کسی چت کنید؟", ["دختر", "پسر", "فرقی نداره"])
        elif msg in ["فرقی نداره", "دختر", "پسر"]:
            users[chat_id]["target"] = msg
            send_message(chat_id, "⏳ در حال جستجوی کاربر...", [])
            match_users()
        else:
            send_message(chat_id, "لطفاً از دکمه‌ها استفاده کنید.")

    return "OK"

if __name__ == '__main__':
    app.run(host="0.0.0.0")
