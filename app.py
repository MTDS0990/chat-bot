from flask import Flask, request
import requests

app = Flask(__name__)

API_URL = "https://botapi.rubika.ir/v3"
BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"

users = {}
waiting_users = []

def send_message(chat_id, text, buttons=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }
    if buttons:
        data["buttons"] = buttons

    requests.post(f"{API_URL}/sendMessage", json=data)

def forward_file(chat_id, file_inline):
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "file_inline": file_inline
    })

@app.route('/')
def home():
    return 'ربات فعال است.'

@app.route('/receiveUpdate', methods=['POST'])
def receive_update():
    data = request.json
    print("📥 پیام دریافت شد:", data)

    update = data.get("update")
    if not update:
        return 'NO UPDATE'

    if update["type"] == "NewMessage":
        chat_id = update["chat_id"]
        message = update["new_message"]

        user_id = message["sender_id"]
        text = message.get("text")
        file_inline = message.get("file_inline")

        user = users.get(user_id, {
            "chat_id": chat_id,
            "state": "awaiting_gender"
        })
        users[user_id] = user

        # مراحل تنظیمات جنسیت
        if user["state"] == "awaiting_gender":
            send_message(chat_id, "جنسیت خود را انتخاب کنید:", buttons=[
                [{"text": "👦 پسر"}, {"text": "👧 دختر"}]
            ])
            user["state"] = "selecting_gender"

        elif user["state"] == "selecting_gender":
            if "پسر" in text:
                user["gender"] = "male"
            elif "دختر" in text:
                user["gender"] = "female"
            else:
                send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.")
                return 'OK'

            send_message(chat_id, "مایلی با چه جنسیتی گفتگو کنی؟", buttons=[
                [{"text": "👧 دختر"}, {"text": "👦 پسر"}, {"text": "👌 فرقی نداره"}]
            ])
            user["state"] = "selecting_target"

        elif user["state"] == "selecting_target":
            if "پسر" in text:
                user["target_gender"] = "male"
            elif "دختر" in text:
                user["target_gender"] = "female"
            elif "فرقی" in text:
                user["target_gender"] = "any"
            else:
                send_message(chat_id, "لطفاً یکی از گزینه‌ها را انتخاب کنید.")
                return 'OK'

            # شروع جستجو
            match_user = None
            for other_id, other in users.items():
                if other_id == user_id:
                    continue
                if other.get("state") != "chatting":
                    if other.get("target_gender") in [user["gender"], "any"] and \
                       user["target_gender"] in [other.get("gender"), "any"]:
                        match_user = other_id
                        break

            if match_user:
                user["state"] = "chatting"
                user["partner"] = match_user

                partner = users[match_user]
                partner["state"] = "chatting"
                partner["partner"] = user_id

                send_message(chat_id, "✅ شما به یک نفر متصل شدید.", buttons=[[{"text": "❌ پایان چت"}]])
                send_message(partner["chat_id"], "✅ شما به یک نفر متصل شدید.", buttons=[[{"text": "❌ پایان چت"}]])
            else:
                send_message(chat_id, "🔎 در حال جستجو برای یافتن شریک گفت‌وگو...")
                user["state"] = "waiting"
                waiting_users.append(user_id)

        elif user["state"] == "chatting":
            if text == "❌ پایان چت":
                partner_id = user.get("partner")
                if partner_id and partner_id in users:
                    partner = users[partner_id]
                    send_message(partner["chat_id"], "❌ چت توسط طرف مقابل پایان یافت.")
                    partner["state"] = "selecting_target"
                    partner.pop("partner", None)

                user["state"] = "selecting_target"
                user.pop("partner", None)
                send_message(chat_id, "✅ چت پایان یافت.")
                return 'OK'

            partner_id = user.get("partner")
            if partner_id and partner_id in users:
                partner = users[partner_id]
                if text:
                    send_message(partner["chat_id"], text)
                elif file_inline:
                    forward_file(partner["chat_id"], file_inline)

    return 'OK'

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
