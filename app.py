from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
API_URL = f"https://botapi.rubika.ir/v3/bot{TOKEN}"

users = {}       # اطلاعات کاربران
waiting = []     # لیست انتظار برای چت

def send_message(chat_id, text, buttons=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if buttons:
        data["buttons"] = buttons
    requests.post(f"{API_URL}/sendMessage", json=data)

def forward_file(file_type, chat_id, file_id):
    requests.post(f"{API_URL}/send{file_type.capitalize()}",
                  json={"chat_id": chat_id, file_type + "_id": file_id})

@app.route("/receiveUpdate", methods=["POST"])
def receive_update():
    update = request.json.get("update", {})
    if update.get("type") != "NewMessage":
        return "OK", 200

    message = update["new_message"]
    chat_id = update["chat_id"]
    sender_id = message["sender_id"]

    user = users.setdefault(sender_id, {"step": "gender"})

    partner_id = user.get("partner_id")
    text = message.get("text")
    photo_id = message.get("photo_id")
    voice_id = message.get("voice_id")

    # پایان چت
    if text == "🔚 پایان چت":
        if partner_id:
            send_message(partner_id, "❌ مخاطب از چت خارج شد.")
            users[partner_id]["partner_id"] = None
        user["partner_id"] = None
        send_message(chat_id, "✅ چت پایان یافت.")
        return "OK", 200

    # اگر در حال چت هستند، پیام، ویس یا عکس را فوروارد کن
    if partner_id:
        if text:
            send_message(partner_id, f"✉️: {text}", [["🔚 پایان چت"]])
        elif photo_id:
            forward_file("photo", partner_id, photo_id)
        elif voice_id:
            forward_file("voice", partner_id, voice_id)
        return "OK", 200

    # شروع مسیر فیلتر
    if user["step"] == "gender":
        send_message(chat_id, "🌸 جنسیت خود را انتخاب کنید:", [
            ["🙎‍♂️ پسر", "🙎‍♀️ دختر"]
        ])
        user["step"] = "set_gender"
    elif user["step"] == "set_gender":
        if text == "🙎‍♂️ پسر":
            user["gender"] = "male"
        elif text == "🙎‍♀️ دختر":
            user["gender"] = "female"
        else:
            send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.")
            return "OK", 200
        user["step"] = "partner_gender"
        send_message(chat_id, "💫 می‌خوای با چه جنسیتی چت کنی؟", [
            ["🙎‍♂️ پسر", "🙎‍♀️ دختر", "🎲 فرقی نداره"]
        ])
    elif user["step"] == "partner_gender":
        if text == "🙎‍♂️ پسر":
            user["target"] = "male"
        elif text == "🙎‍♀️ دختر":
            user["target"] = "female"
        elif text == "🎲 فرقی نداره":
            user["target"] = "any"
        else:
            send_message(chat_id, "یکی از گزینه‌ها رو انتخاب کن.")
            return "OK", 200
        user["step"] = "match"
        send_message(chat_id, "✅ برای شروع چت روی دکمه زیر بزن:", [["🚀 شروع چت"]])
    elif user["step"] == "match" and text == "🚀 شروع چت":
        for uid, u in users.items():
            if uid != sender_id and not u.get("partner_id"):
                if user["target"] == "any" or u.get("gender") == user["target"]:
                    if u["target"] == "any" or user["gender"] == u["target"]:
                        user["partner_id"] = uid
                        u["partner_id"] = sender_id
                        send_message(uid, "🎉 مخاطب پیدا شد! می‌تونی چت کنی.", [["🔚 پایان چت"]])
                        send_message(chat_id, "🎉 مخاطب پیدا شد! می‌تونی چت کنی.", [["🔚 پایان چت"]])
                        return "OK", 200
        send_message(chat_id, "⏳ منتظر بمون تا مخاطب مناسب پیدا شه.")
    else:
        send_message(chat_id, "برای شروع /start رو بزن.")

    return "OK", 200
