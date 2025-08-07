from flask import Flask, request
import requests

app = Flask(__name__)

API_URL = "https://botapi.rubika.ir/v3"
BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"

users = {}
waiting_list = {"male": [], "female": [], "any": []}
chats = {}

def send_message(chat_id, text, buttons=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if buttons:
        payload["buttons"] = buttons
    try:
        requests.post(f"{API_URL}/bot{BOT_TOKEN}/sendMessage", json=payload)
    except Exception as e:
        print(f"❌ خطا در ارسال پیام: {e}")

@app.route("/", methods=["GET"])
def home():
    return "✅ ربات فعال است"

@app.route("/receiveUpdate", methods=["POST"])
def receive_update():
    data = request.json
    print("📥 پیام دریافت شد:", data)

    try:
        update = data.get("update", {})
        msg = update.get("new_message", {})
        chat_id = update.get("chat_id")
        user_id = msg.get("sender_id")
        text = msg.get("text", "").strip()

        if user_id not in users:
            users[user_id] = {"gender": None, "preferred": None, "partner": None}
            send_message(chat_id, "سلام! 😊\nبرای شروع، جنسیت خودتو مشخص کن:", buttons=[
                [{"text": "👩 دختر"}, {"text": "👨 پسر"}]
            ])
            return "OK"

        user = users[user_id]

        if user["gender"] is None:
            if text in ["👩 دختر", "دختر"]:
                user["gender"] = "female"
            elif text in ["👨 پسر", "پسر"]:
                user["gender"] = "male"
            else:
                send_message(chat_id, "لطفاً فقط از دکمه‌ها استفاده کن.")
                return "OK"
            send_message(chat_id, "عالیه! حالا انتخاب کن می‌خوای با چه کسی چت کنی:", buttons=[
                [{"text": "👩 دختر"}, {"text": "👨 پسر"}],
                [{"text": "🎲 فرقی نداره"}]
            ])
            return "OK"

        if user["preferred"] is None:
            if text in ["👩 دختر", "دختر"]:
                user["preferred"] = "female"
            elif text in ["👨 پسر", "پسر"]:
                user["preferred"] = "male"
            elif text in ["🎲 فرقی نداره", "فرقی نداره"]:
                user["preferred"] = "any"
            else:
                send_message(chat_id, "لطفاً فقط از دکمه‌ها استفاده کن.")
                return "OK"

            match_user(user_id)
            return "OK"

        # اگر در چت است، پیام را به طرف مقابل بفرست
        if user["partner"]:
            partner_id = user["partner"]
            if partner_id in users and users[partner_id]["partner"] == user_id:
                requests.post(f"{API_URL}/bot{BOT_TOKEN}/sendMessage", json={
                    "chat_id": partner_id,
                    "text": text
                })
        else:
            send_message(chat_id, "⏳ در حال جستجو برای چت با کسی هستیم... لطفاً صبور باش.")
    except Exception as e:
        print(f"❌ خطا در پردازش: {e}")
    return "OK"

def match_user(user_id):
    user = users[user_id]
    preferred = user["preferred"]

    potential_partners = []
    if preferred == "any":
        potential_partners = waiting_list["male"] + waiting_list["female"] + waiting_list["any"]
    else:
        potential_partners = waiting_list[preferred] + waiting_list["any"]

    for pid in potential_partners:
        partner = users.get(pid)
        if partner and partner["partner"] is None and (
            partner["preferred"] == user["gender"] or partner["preferred"] == "any"
        ):
            user["partner"] = pid
            partner["partner"] = user_id
            waiting_list[partner["preferred"]].remove(pid)

            send_message(user_id, "✅ یه نفر پیدا شد! می‌تونی پیام بدی.")
            send_message(pid, "✅ یه نفر پیدا شد! می‌تونی پیام بدی.")
            return

    # اگه کسی پیدا نشد، بره تو صف انتظار
    waiting_list[preferred].append(user_id)
    send_message(user_id, "🔍 کسی پیدا نشد، منتظر بمون تا یه نفر پیدا بشه...")

if __name__ == "__main__":
    app.run()
