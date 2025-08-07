from flask import Flask, request
import requests
import os

app = Flask(__name__)
TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
API_URL = "https://botapi.rubika.ir/v3"

users = {}  # user_id -> {"gender": str, "looking_for": str, "partner": user_id or None}

# صفحه اصلی
@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است ✅"

# دریافت آپدیت‌ها
@app.route("/receiveUpdate", methods=["POST"])
def receive_update():
    data = request.get_json()
    print("📥 پیام دریافت شد:", data)

    update = data.get("update", {})
    if update.get("type") == "NewMessage":
        message = update.get("new_message", {})
        user_id = message.get("sender_id")
        chat_id = update.get("chat_id")
        text = message.get("text", "")
        file_inline = message.get("file_inline", None)

        # اگر فایل (عکس، ویس) ارسال شده
        if file_inline and users.get(user_id, {}).get("partner"):
            forward_file(users[user_id]["partner"], file_inline)
            return "ok"

        # اگر پیام متنی است
        if text:
            handle_text(user_id, chat_id, text)

    return "ok"

# هندل پیام متنی
def handle_text(user_id, chat_id, text):
    user = users.get(user_id)

    if text == "/start":
        users[user_id] = {"gender": None, "looking_for": None, "partner": None}
        send_message(chat_id, "سلام! 👋\nلطفاً جنسیت خود را انتخاب کنید:", [
            {"text": "👦 پسر", "command": "gender_boy"},
            {"text": "👧 دختر", "command": "gender_girl"}
        ])
        return

    if text == "🔚 پایان چت":
        end_chat(user_id)
        return

    if user:
        if not user["gender"]:
            if text == "👦 پسر":
                users[user_id]["gender"] = "boy"
            elif text == "👧 دختر":
                users[user_id]["gender"] = "girl"
            else:
                send_message(chat_id, "لطفاً فقط با دکمه انتخاب کن.")
                return
            send_message(chat_id, "مایلی با چه کسی چت کنی؟", [
                {"text": "👧 دختر", "command": "looking_girl"},
                {"text": "👦 پسر", "command": "looking_boy"},
                {"text": "🔁 فرقی نداره", "command": "looking_any"}
            ])
            return

        if not user["looking_for"]:
            if text == "👧 دختر":
                users[user_id]["looking_for"] = "girl"
            elif text == "👦 پسر":
                users[user_id]["looking_for"] = "boy"
            elif text == "🔁 فرقی نداره":
                users[user_id]["looking_for"] = "any"
            else:
                send_message(chat_id, "لطفاً فقط با دکمه انتخاب کن.")
                return
            match_user(user_id)
            return

        # اگر چت فعال است
        if user["partner"]:
            partner_id = user["partner"]
            send_message(partner_id, text)
        else:
            send_message(chat_id, "⏳ در حال پیدا کردن مخاطب مناسب... لطفاً صبور باشید.")
    else:
        send_message(chat_id, "لطفاً /start را ارسال کنید.")

# تطبیق کاربران
def match_user(user_id):
    for other_id, other in users.items():
        if other_id != user_id and not other["partner"]:
            if (
                (users[user_id]["looking_for"] == "any" or users[user_id]["looking_for"] == other["gender"])
                and
                (other["looking_for"] == "any" or other["looking_for"] == users[user_id]["gender"])
            ):
                users[user_id]["partner"] = other_id
                users[other_id]["partner"] = user_id
                send_message(user_id, "🎉 یک نفر برای چت پیدا شد!\nبرای پایان چت، دکمه زیر را بزنید:", [
                    {"text": "🔚 پایان چت", "command": "end"}
                ])
                send_message(other_id, "🎉 یک نفر برای چت پیدا شد!\nبرای پایان چت، دکمه زیر را بزنید:", [
                    {"text": "🔚 پایان چت", "command": "end"}
                ])
                return
    send_message(user_id, "⏳ در حال جست‌وجو برای مخاطب...")

# پایان چت
def end_chat(user_id):
    user = users.get(user_id)
    if user and user["partner"]:
        partner_id = user["partner"]
        users[user_id]["partner"] = None
        users[partner_id]["partner"] = None
        send_message(user_id, "❌ چت پایان یافت.")
        send_message(partner_id, "❌ طرف مقابل چت را ترک کرد.")
    else:
        send_message(user_id, "شما در حال حاضر با کسی در حال چت نیستید.")

# ارسال پیام متنی با دکمه
def send_message(chat_id, text, buttons=None):
    payload = {"chat_id": chat_id, "text": text}
    if buttons:
        payload["buttons"] = [[{"text": b["text"], "command": b["command"]}] for b in buttons]
    try:
        requests.post(f"{API_URL}/sendMessage", json=payload)
    except Exception as e:
        print("❌ خطا در ارسال پیام:", e)

# فوروارد عکس یا ویس
def forward_file(chat_id, file_inline):
    payload = {"chat_id": chat_id, "file_inline": file_inline}
    try:
        requests.post(f"{API_URL}/sendFile", json=payload)
    except Exception as e:
        print("❌ خطا در ارسال فایل:", e)

# اجرای برنامه
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
