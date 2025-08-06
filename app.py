from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
BASE_API = f"https://botapi.rubika.ir/v3/{TOKEN}"

SEND_URL = BASE_API + "/sendMessage"

@app.route('/', methods=['GET'])
def home():
    return "🤖 ربات آماده‌ است!"

@app.route('/receiveUpdate', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📥 پیام دریافت شد:", data)

    # ساختار body می‌تواند شامل "inline_message" یا "update"
    if "update" in data and data["update"].get("type") == "NewMessage":
        chat_id = data["update"].get("chat_id")
        msg = data["update"].get("new_message", {})
        text = msg.get("text", "")
        sender_id = msg.get("sender_id", "")

        print(f"✉️ پیام از {sender_id}: {text}")

        # پاسخ:
        if text == "/start":
            reply = "سلام! به چت ناشناس خوش اومدی 💬"
        else:
            reply = f"تو گفتی: {text}"

        resp = requests.post(SEND_URL, json={"chat_id": chat_id, "text": reply})
        print("✅ پاسخ ارسال شد:", resp.text)

    elif "inline_message" in data:
        im = data["inline_message"]
        chat_id = im.get("chat_id")
        text = im.get("text", "")
        print(f"📲 پیام دکمه‌ای: {text}")

        requests.post(SEND_URL, json={
            "chat_id": chat_id,
            "text": f"فشردی: {text}"
        })

    else:
        print("⚠️ پیام ناشناس یا نوع پشتیبانی‌نشده")

    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(request.environ.get("PORT", 5000)))
