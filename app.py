from flask import Flask, request
import requests

app = Flask(__name__)

API_URL = "https://botapi.rubika.ir/v3"
BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"

# ذخیره اطلاعات کاربران
users = {}
pairs = {}

def send_message(chat_id, text, btn=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if btn:
        data["inline_markup"] = {"rows": [[{"text": b, "command": b}] for b in btn]}
    return requests.post(f"{API_URL}/message/send", json=data)

def forward_message(from_chat, to_chat, message):
    file_id = message.get("file_inline", {}).get("file_id")
    text = message.get("text")
    if file_id:
        requests.post(f"{API_URL}/message/send", json={
            "chat_id": to_chat,
            "file_inline": {"file_id": file_id}
        })
    elif text:
        send_message(to_chat, text)

@app.route('/')
def home():
    return "ربات فعال است!"

@app.route('/receiveUpdate', methods=['POST'])
def receive_update():
    update = request.json.get("update")
    if not update:
        return "OK"

    if update["type"] == "NewMessage":
        chat_id = update["chat_id"]
        message = update["new_message"]
        text = message.get("text", "")

        # اگه تو چت ناشناس هست
        if chat_id in pairs:
            forward_message(chat_id, pairs[chat_id], message)
            return "OK"

        # شروع
        if text == "/start":
            users[chat_id] = {"gender": None, "target_gender": None}
            send_message(chat_id, "سلام! جنسیت خودت رو انتخاب کن:", ["👩 دختر", "👨 پسر"])
        
        elif text in ["👩 دختر", "👨 پسر"]:
            users[chat_id]["gender"] = text
            send_message(chat_id, "حالا روی «شروع چت» بزن:", ["🚀 شروع چت"])

        elif text == "🚀 شروع چت":
            send_message(chat_id, "میخوای با چه کسی چت کنی؟", ["👩 دختر", "👨 پسر", "🤝 فرقی نداره"])

        elif text in ["👩 دختر", "👨 پسر", "🤝 فرقی نداره"]:
            users[chat_id]["target_gender"] = text
            match_user(chat_id)

        elif text == "❌ پایان چت":
            if chat_id in pairs:
                partner = pairs.pop(chat_id)
                pairs.pop(partner, None)
                send_message(chat_id, "چت پایان یافت.")
                send_message(partner, "طرف مقابل چت رو پایان داد.")
            else:
                send_message(chat_id, "شما در حال حاضر در چت نیستید.")

        else:
            send_message(chat_id, "برای شروع، /start رو بزن.")

    return "OK"

def match_user(chat_id):
    gender = users[chat_id]["gender"]
    target_gender = users[chat_id]["target_gender"]

    for uid, info in users.items():
        if uid != chat_id and uid not in pairs and info["gender"] and info["target_gender"]:
            if target_gender == "🤝 فرقی نداره" or info["gender"] == target_gender:
                if info["target_gender"] == "🤝 فرقی نداره" or gender == info["target_gender"]:
                    pairs[chat_id] = uid
                    pairs[uid] = chat_id
                    send_message(chat_id, "✅ به یک نفر متصل شدید! می‌توانید چت را شروع کنید.", ["❌ پایان چت"])
                    send_message(uid, "✅ به یک نفر متصل شدید! می‌توانید چت را شروع کنید.", ["❌ پایان چت"])
                    return

    send_message(chat_id, "⏳ منتظر بمانید تا کسی با شرایط شما پیدا شود.")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
