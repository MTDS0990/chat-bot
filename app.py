from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "BJAJB0ZFKNCMRUTVFQBFNGNYVYQKAXCWYPHWLGELMBVZRBLYAMMVQBHKFCTIOQGF"
SEND_URL = f"https://messengerg2c37.iranl.ms/bot{TOKEN}/sendMessage"

@app.route('/')
def home():
    return "🤖 ربات روشنه و کار می‌کنه!"

@app.route('/receiveUpdate', methods=['POST'])
def receive_update():
    try:
        data = request.get_json()
        print("📥 پیام دریافت شد:", data)

        update = data.get("update", {})
        if update.get("type") == "NewMessage":
            chat_id = update.get("chat_id")
            new_message = update.get("new_message", {})
            text = new_message.get("text", "")
            sender_id = new_message.get("sender_id", "")

            print("✉️ پیام از:", sender_id, "| متن:", text)

            response = requests.post(SEND_URL, json={
                "chat_id": chat_id,
                "text": f"سلام {sender_id}، پیامتو گرفتم ✅"
            })

            print("✅ پاسخ فرستاده شد:", response.text)
        else:
            print("⚠️ نوع آپدیت پشتیبانی نمی‌شود:", update.get("type"))

    except Exception as e:
        print("❌ خطا در پردازش:", str(e))

    return "OK"

if __name__ == '__main__':
    app.run(debug=True)
