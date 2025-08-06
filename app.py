from flask import Flask, request
import requests

app = Flask(__name__)

# توکن ربات روبیکا
BOT_TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"

# آدرس API روبیکا
API_URL = f"https://messengerg2c37.iranl.ms/bot{BOT_TOKEN}/sendMessage"

@app.route('/', methods=['GET'])
def index():
    return "ربات روشن است ✅"

@app.route('/receiveUpdate', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📥 پیام دریافت شد:", data)

    try:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')

        # پاسخ پیش‌فرض
        if text == "/start":
            reply = "سلام! به ربات چت ناشناس طاها خوش اومدی 🤖\nپیامتو بفرست تا با یه نفر ناشناس چت کنی..."
        else:
            reply = "✅ پیام شما دریافت شد. (البته هنوز جفت‌سازی فعال نشده!)"

        # ارسال پاسخ
        payload = {
            "chat_id": chat_id,
            "text": reply
        }
        requests.post(API_URL, json=payload)

    except Exception as e:
        print("❌ خطا در پردازش:", e)

    return '', 200
